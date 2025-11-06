from langgraph.checkpoint.sqlite import SqliteSaver

from agents.start_agent import start_agent_app
from agents.env_agent import env_agent_workflow
from utils.get_env import get_env_variable


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


def run_env_agent(state, resume: bool):
    config = {
            "recursion_limit": 50,
            "configurable": {
                "thread_id": get_env_variable("thread_id")
            }
        }

    if resume and check_story_exists(env_agent_app):
        print("Env Agent resuming from existing checkpoint...")
        output_state = env_agent_app.invoke(None, config=config)
        return output_state
    
    print("Env Agent starting fresh execution...")
    output_state = env_agent_app.invoke(
        state,
        config=config
    )
    return output_state

def check_story_exists(app) -> bool:
    """Checks if a saved state exists for the given thread_id."""
    config = {"configurable": {"thread_id": get_env_variable("thread_id")}}
    try:
        # get_state() will raise an exception if no state is found
        app.get_state(config)
        return True
    except Exception:
        return False



if __name__ == "__main__":
    input_text = "In a distant future, humanity has colonized Mars. Amidst political turmoil and environmental challenges, a group of explorers embarks on a mission to uncover ancient Martian artifacts that could hold the key to humanity's survival."

    need_restart = input("Do you want to restart the story? (y/n): ")

    with SqliteSaver.from_conn_string("env_agent_checkpoint.db") as memory:
        env_agent_app = env_agent_workflow.compile(checkpointer=memory)

        if need_restart.lower() == 'y':
            print("Starting new story...")
            output = run_start_agent(input_text)
            print(output)

            output = run_env_agent({
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
            }, resume=False)
        else:
            print("Resuming story from checkpoint...")
            output = run_env_agent(None, resume=True)