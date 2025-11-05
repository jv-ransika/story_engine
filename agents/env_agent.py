import json
from typing import List, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from pydantic_bp.core import Character, Entity, Scene, Moment
from utils.model import lite_llm
from agents.character_agent import character_app


class EnvAgentState(TypedDict):
    description: str
    main_goal: str
    is_main_goal_achieved: bool = False
    characters: List[Character]
    entities: List[Entity]
    scenes: List[Scene] = []
    next_character_index: int = 0

    next_scene_no: int = 1
    next_scene: str = ""
    is_scene_complete: bool = False
    current_scene: Scene = None

    next_moment_no: int = 1
    current_moment: Moment = None



class SceneModel(BaseModel):
    characters_indexes: List[int] = Field(description="0 based indexes of characters present in the scene, in the order they will appear.")
    description: str = Field(description="Description of the scene like where it is happening, time of the day, mood, etc.")


def get_next_character(state: EnvAgentState) -> Character:
    if state["next_character_index"] >= len(state["characters"]):
        state["next_character_index"] = 0

    character = state["characters"][state["next_character_index"]]
    return character

def scene_creator(state: EnvAgentState) -> EnvAgentState:
    '''
    Creates a new scene based on the current state.
    '''

    print(f"Creating scene number {state['next_scene_no']}...")
    
    system_mssage = f"""
        You are a scene creator agent. Your task is to create a new scene with the help of available characters and entities to complete the scenario.
        The main goal is: {state['main_goal']}

    """

    scene_creator_llm = lite_llm.with_structured_output(SceneModel)

    characters_data = []
    for character in state["characters"]:
        characters_data.append({
            "name": character.name,
            "role": character.role,
            "longtime_goals": character.longtime_goals,
            "personality": character.personality,
            "strengths": character.strengths,
            "weaknesses": character.weaknesses,
        })

    entities_data = [entity.model_dump() for entity in state["entities"]]

    scenes_data = []
    for scene in state["scenes"]:
        scene_data = {
            "no": scene.no,
            "description": scene.description,
            "moments": []
        }
        for moment in scene.moments:
            moment_data = {
                "no": moment.no,
                "situations": []
            }
            for situation in moment.situations:
                situation_data = {
                    "who_said": situation.who_said.name,
                    "who_listens": [char.name for char in situation.who_listens],
                    "dialogue": situation.dialogue,
                    "action": situation.action
                }
                moment_data["situations"].append(situation_data)
            scene_data["moments"].append(moment_data)
        scenes_data.append(scene_data)

    response = scene_creator_llm.invoke([
        SystemMessage(content=system_mssage),
        HumanMessage(content=f'''
        Here are the available characters:
        {json.dumps(characters_data, indent=2)}
        Here are the available entities:
        {json.dumps(entities_data, indent=2)}
        The scenes that have happened so far:
        {json.dumps(scenes_data, indent=2)}
        Reference to the new scene is {state['next_scene']}
        ''')
    ])

    print(f"Scene created successfully..")

    return {
        "current_scene": Scene(
                no=state["next_scene_no"],
                description=response.description,
                characters=[state["characters"][i] for i in response.characters_indexes],
                moments=[]
        ),
        "is_scene_complete": False,
        "next_moment_no": 1,
    }


def moment_runner(state: EnvAgentState) -> EnvAgentState:
    '''
    Creates a new moments within the current scene.
    '''
    print(f"Creating moment number {state['next_moment_no']} in scene {state['next_scene_no']}...")

    for character in state["current_scene"].characters:
        character_state = {
            "scene": state["current_scene"],
            "current_character": character,
        }
        character_response = character_app.invoke(character_state)
        new_memory_unit = character_response["new_memory_unit"]
        
        # Append the new memory unit to the current moment
        if state["current_moment"] is None :
            # Create a new moment if it doesn't exist
            state["current_moment"] = Moment(
                no=state["next_moment_no"],
                situations=[]
            )
            state["current_scene"].moments.append(state["current_moment"])

        state["current_moment"].situations.append(new_memory_unit)

    print(f"Moment created successfully..")

    return {
        "next_moment_no": state["next_moment_no"] + 1
    }


def scene_validator(state: EnvAgentState) -> EnvAgentState:
    '''
    Validates the created scene if it finishes its purpose.
    '''
    print("Validating scene completion...")

    class SceneValidationModel(BaseModel):
        is_scene_complete: bool = Field(description="Whether the scene is complete or not.")
    

    system_prompt = f"""
        You are a scene validator agent. Your task is to evaluate whether the current scene has achieved its purpose in progressing towards the main goal.
        The main goal is: {state['main_goal']}
        Provide your response in the specified structured format.
    """

    scene_validator_llm = lite_llm.with_structured_output(SceneValidationModel)

    current_scene = state["current_scene"]
    current_scene_data = {
        "description": current_scene.description,
        "moments": []
    }

    # Manually serialize moments and situations

    for moment in current_scene.moments:
        moment_data = {
            "no": moment.no,
            "situations": []
        }
        for situation in moment.situations:
            situation_data = {
                "who_said": situation.who_said.name,
                "who_listens": [char.name for char in situation.who_listens],
                "dialogue": situation.dialogue,
                "action": situation.action
            }
            moment_data["situations"].append(situation_data)
        current_scene_data["moments"].append(moment_data)


    response = scene_validator_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f'''
        Here is the current scene:
        {json.dumps(current_scene_data, indent=2)}
        Based on the above scene, determine if the scene is complete in achieving its purpose.
        The purpose of the scene is {state['next_scene']}
        If scene purpose must be fully achieved, mark it as complete.
        Even scene purpose is achieved if characters not yet complete their actions or conversations, mark it as incomplete.
        and if scene being large unnecessarily and characters are just make silly actions, terminate scene by marking it as complete.
        ''')
    ])

    state["is_scene_complete"] = response.is_scene_complete

    if response.is_scene_complete:
        print("Scene is complete.")
        return {
            "scenes": state["scenes"] + [state["current_scene"]],
            "next_scene_no": state["next_scene_no"] + 1,
            "current_scene": None,
            "current_moment": None,
            "next_moment_no": 1,
            "is_scene_complete": True
        }

    print("Scene is not yet complete.")
    return {
        "is_scene_complete": response.is_scene_complete
    }


def final_goal_validator(state: EnvAgentState) -> EnvAgentState:
    print("Validating final goal achievement...")
    
    class GoalModel(BaseModel):
        is_main_goal_achieved: bool = Field(description="Whether the main goal has been achieved or not.")
        next_scene: SceneModel = Field(description="The next scene to be created to progress towards the main goal. if main goal is achieved, leave this empty.")


    system_prompt = f"""
        You are a goal validator agent. Your task is to evaluate whether the main goal has been achieved based on scenes happened so far.
        The main goal is: {state['main_goal']}
        If the main goal is not achieved, you need to suggest the next scene to be created to progress towards the main goal.
        Provide your response in the specified structured format.
    """

    goal_validator_llm = lite_llm.with_structured_output(GoalModel)

    scenes_data = []

    for scene in state["scenes"]:
        scene_data = {
            "no": scene.no,
            "description": scene.description,
            "moments": []
        }
        for moment in scene.moments:
            moment_data = {
                "no": moment.no,
                "situations": []
            }
            for situation in moment.situations:
                situation_data = {
                    "who_said": situation.who_said.name,
                    "who_listens": [char.name for char in situation.who_listens],
                    "dialogue": situation.dialogue,
                    "action": situation.action
                }
                moment_data["situations"].append(situation_data)
            scene_data["moments"].append(moment_data)
        scenes_data.append(scene_data)

    characters_data = []
    for character in state["characters"]:
        characters_data.append({
            "name": character.name,
            "role": character.role,
            "longtime_goals": character.longtime_goals,
            "personality": character.personality,
            "strengths": character.strengths,
            "weaknesses": character.weaknesses,
        })

    entities_data = [entity.model_dump() for entity in state["entities"]]

    response = goal_validator_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f'''
        Here are the scenes that have happened so far:
        {json.dumps(scenes_data, indent=2)}
        Based on the above scenes, determine if the main goal has been achieved. If not, suggest the next scene to be created.
        Characters available:
        {json.dumps(characters_data, indent=2)}
        Entities available:
        {json.dumps(entities_data, indent=2)}
        ''')
    ])

    if response.is_main_goal_achieved:
        print("Main goal has been achieved!")
    else:
        print("Main goal not yet achieved. Next scene to create:")

    
    return{
        "is_main_goal_achieved": response.is_main_goal_achieved,
        "next_scene": response.next_scene
    }


env_agent_workflow = StateGraph(EnvAgentState)
env_agent_workflow.add_node("scene_creation", scene_creator)
env_agent_workflow.add_node("moment_runner", moment_runner)
env_agent_workflow.add_node("final_goal_validation", final_goal_validator)
env_agent_workflow.add_node("scene_validation", scene_validator)


env_agent_workflow.set_entry_point("scene_creation")
env_agent_workflow.add_edge("scene_creation", "moment_runner")
env_agent_workflow.add_edge("moment_runner", "scene_validation")

env_agent_workflow.add_conditional_edges(
    "scene_validation",
    lambda state: state["is_scene_complete"],
    {
        True: "final_goal_validation",
        False: "moment_runner"
    }
)

env_agent_workflow.add_conditional_edges(
    "final_goal_validation",
    lambda state: state["is_main_goal_achieved"],
    {
        True: END,
        False: "scene_creation"
    }
)

env_agent_app = env_agent_workflow.compile()
