from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from pydantic_bp.core import Character, CharacterMemoryUnit, Scene
from utils.model import lite_llm


class CharacterAgentState(BaseModel):
    scene: Scene
    current_character: Character
    new_memory_unit: Optional[CharacterMemoryUnit] = Field(default=None)



def character_agent(state: CharacterAgentState) -> CharacterAgentState:
    sysmet_prompt = state.current_character.system_message()

    class CharacterResponse(BaseModel):
        dialogue: str = Field(..., description="Your dialogue in this scene.")
        action: str = Field(..., description="Your action in this scene.")
        who_listens: List[int] = Field(..., description="List of characters indexes who are listening to you in this moment. 0 based indexes as per the scene characters list.")
        shortterm_goals: List[str] = Field(description="Your updated shortterm goals after this moment. add or remove goals as necessary.")
        longterm_memory: List[str] = Field(description="Any new facts or events to be added to your longterm memory. Just add very importantce events. dont repeat existing memories. othervise leave it empty. and alse memory_factor affects how much you remember. If memory_factor is low, you may forget some details. even important ones.")

    character_llm = lite_llm.with_structured_output(CharacterResponse)

    response = character_llm.invoke([
        SystemMessage(content=sysmet_prompt),
        HumanMessage(content=f"""
                     Scene Description: {str(state.scene)}\n , available characters to interact with: {list(state.scene.characters)}
                     What do you do in this moment?
        """)
    ])



    new_memory_unit = CharacterMemoryUnit(
        who_said=state.current_character.name,
        who_listens=[state.scene.characters[i].name for i in response.who_listens],
        dialogue=response.dialogue,
        action=response.action
    )
    
    state.current_character.shorttime_goals = response.shortterm_goals
    state.current_character.longterm_memory.extend(response.longterm_memory)

    #this character also in below list
    # state.current_character.update_shortterm_memory(new_memory_unit)

    # Change this to update only relevant characters
    for character in state.scene.characters:
        character.update_shortterm_memory(new_memory_unit)

    return {
        "new_memory_unit": new_memory_unit
    }


character_workflow = StateGraph(CharacterAgentState)
character_workflow.add_node("character_agent", character_agent)

character_workflow.set_entry_point("character_agent")
character_workflow.add_edge("character_agent", END)

character_app = character_workflow.compile()