from agents.start_agent import start_agent_app
from agents.env_agent import env_agent_app


def run_start_agent(input_text: str):
    initial_state = {
        "input_text": input_text,
        "characters": [],
        "entities": [],
        "start_scene_description": "",
        "main_goal": ""
    }
    output_state = start_agent_app.invoke(initial_state)

    initial_state["characters"] = output_state["characters"]
    initial_state["entities"] = output_state["entities"]
    initial_state["start_scene_description"] = output_state["start_scene_description"]
    initial_state["main_goal"] = output_state["main_goal"]

    return initial_state


def run_without_checkpoint_env_agent(state):
    output_state = env_agent_app.invoke(
        state,
        config={
            "recursion_limit": 50
        }
    )
    return output_state


if __name__ == "__main__":
    input_text = "In a distant future, humanity has colonized Mars. Amidst political turmoil and environmental challenges, a group of explorers embarks on a mission to uncover ancient Martian artifacts that could hold the key to humanity's survival."
    output = run_start_agent(input_text)
    print(output)

    output = run_without_checkpoint_env_agent({
        "main_goal": output["main_goal"],
        "is_main_goal_achieved": False,
        "characters": output["characters"],
        "entities": output["entities"],
        "scenes": [],
        "next_character_index": 0,
        "next_scene_no": 1,
        "next_scene": output["start_scene_description"],
        "is_scene_complete": False,
        "current_scene": None,
        "next_moment_no": 1,
        "current_moment": None
    })