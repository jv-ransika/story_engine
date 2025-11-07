from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class CharacterMemoryUnit(BaseModel):
    who_said: str
    who_listens: List[str]
    dialogue: str
    action: str

class Moment(BaseModel):
    no: int
    situations: List[CharacterMemoryUnit]

class Character(BaseModel):
    name: str
    role: str
    longtime_goals: List[str]
    shorttime_goals: List[str] = Field(default_factory=list)
    personality: List[str]
    strengths: List[str]
    weaknesses: List[str]
    memory_factor: float = 0.5
    max_shortterm_memory: Optional[int] = None

    shortterm_memory: List[CharacterMemoryUnit]
    longterm_memory: List[str]

    @model_validator(mode='after')
    def set_post_init(self):
        if self.max_shortterm_memory is None:
            self.max_shortterm_memory = 15 + int(self.memory_factor * 100)
        
        return self

    def system_message(self) -> str:
        return (f"You are {self.name}, a {self.role} in the story. "
                f"Your longtime goals are: {', '.join(self.longtime_goals)}. "
                f"Your shorttime goals are: {', '.join(self.shorttime_goals)}. "
                f"Your memory factor is: {self.memory_factor}. (Means how well you remember past events, from 0 to 1). "
                f"your personality traits are: {', '.join(self.personality)}. "
                f"Your strengths are: {', '.join(self.strengths)}. "
                f"Your weaknesses are: {', '.join(self.weaknesses)}.")
    
    def update_shortterm_memory(self, event: str):
        if len(self.shortterm_memory) >= self.max_shortterm_memory:
            self.shortterm_memory.pop(0)

        self.shortterm_memory.append(event)


class Scene(BaseModel):
    no: int
    characters: List[Character]
    description: str
    moments: List[Moment]


class Entity(BaseModel):
    name: str
    description: str


