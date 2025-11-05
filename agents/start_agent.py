from pydantic import BaseModel, Field
from typing import List, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from pydantic_bp.core import Character, Entity
from utils.model import lite_llm


class startAgentState(BaseModel):
    input_text: str
    characters: List[Character] = []
    entities: List[Entity] = []
    start_scene_description: str = ""
    main_goal: str = ""

class CharacterDict(TypedDict):
    name: str = Field(depescription="Name of the character")
    role: str = Field(depescription="Role of the character in the story")
    longtime_goals: List[str] = Field(depescription="Long term goals of the character")
    memory_factor: float = Field(depescription="Memory retention factor of the character. 0 to 1, where 1 means full memory retention, default is 0.5 for normal person")
    personality: List[str] = Field(depescription="Personality traits of the character")
    strengths: List[str] = Field(depescription="Strengths of the character")
    weaknesses: List[str] = Field(depescription="Weaknesses of the character")

class EntityDict(TypedDict):
    name: str = Field(depescription="Name of the entity")
    description: str = Field(depescription="Description of the entity")

class StartAgentOutput(TypedDict):
    characters: List[CharacterDict]
    entities: List[EntityDict]
    start_scene_description: str = Field(depescription="Description of the starting scene")
    main_goal: str = Field(depescription="Main goal of the story, successfully occurrence of crime")


def start_agent(state: startAgentState) -> StartAgentOutput:

    print("Starting Start Agent...")

    system_prompt = """You are an agent that analyzes the input text to identify key characters and entities, and generate a compelling starting scene description for a story based on the provided input.
    characters = []
    entities = []
    start_scene_description = ""
    main_goal = ""
    """

    start_agent_llm = lite_llm.with_structured_output(StartAgentOutput)

    res = start_agent_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage('''
                     Analyze the following input text to identify key characters and entities, and generate a compelling starting scene description for a story.
                     Input Text: {input_text}
                     '''.format(input_text=state.input_text)
                     )
    ])

    characters = []
    for character in res["characters"]:
        characters.append(
            Character(
                name=character["name"],
                role=character["role"],
                longtime_goals=character["longtime_goals"],
                personality=character["personality"],
                strengths=character["strengths"],
                weaknesses=character["weaknesses"],
                shortterm_memory=[],
                longterm_memory=[],
                memory_factor=character.get("memory_factor", 0.5)
            )
        )

    entities = []
    for entity in res["entities"]:
        entities.append(
            Entity(
                name=entity["name"],
                description=entity["description"]
            )
        )       
    

    print("Start Agent completed.")

    return {
        "characters": characters,
        "entities": entities,
        "start_scene_description": res["start_scene_description"],
        "main_goal": res["main_goal"]
    }

start_agent_workflow = StateGraph(startAgentState)
start_agent_workflow.add_node("start_agent", start_agent)

start_agent_workflow.set_entry_point("start_agent")
start_agent_workflow.add_edge("start_agent", END)

start_agent_app = start_agent_workflow.compile()
