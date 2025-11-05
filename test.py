from pydantic_bp.core import Character, CharacterMemoryUnit, Moment, Scene

character = Character(
    name="Alice",
    role="Protagonist",
    longtime_goals=["Save the world", "Find true love"],
    personality=["Brave", "Curious"],
    strengths=["Intelligence", "Agility"],
    weaknesses=["Impulsiveness"],
    shortterm_memory=[],
    longterm_memory=[]
)

print(character.system_message())

breakpoint()