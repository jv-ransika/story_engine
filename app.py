import gradio as gr
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.start_agent import start_agent_app
from agents.env_agent import env_agent_workflow
from utils.get_env import get_env_variable


env_agent_app = None


def initialize_app():
    global env_agent_app
    with SqliteSaver.from_conn_string("env_agent_checkpoint.db") as memory:
        env_agent_app = env_agent_workflow.compile(checkpointer=memory)


def check_story_exists() -> bool:
    """Checks if a saved state exists for the given thread_id."""
    config = {"configurable": {"thread_id": get_env_variable("THREAD_ID")}}
    try:
        env_agent_app.get_state(config)
        return True
    except Exception:
        return False


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
            "thread_id": get_env_variable("THREAD_ID")
        }
    }

    if resume and check_story_exists():
        output_state = env_agent_app.invoke(None, config=config)
        return output_state
    
    output_state = env_agent_app.invoke(state, config=config)
    return output_state


def generate_new_story(prompt: str, progress=gr.Progress()):
    """Generate a new story from scratch"""
    try:
        progress(0, desc="Running start agent...")
        output = run_start_agent(prompt)
        
        progress(0.3, desc="Starting story generation...")
        story_state = {
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
        }
        
        progress(0.5, desc="Generating story...")
        result = run_env_agent(story_state, resume=False)
        
        return format_story_output(result)
    except Exception as e:
        return f"Error generating story: {str(e)}"


def resume_story(progress=gr.Progress()):
    """Resume an existing story from checkpoint"""
    try:
        if not check_story_exists():
            return "No existing story found. Please generate a new story first."
        
        progress(0, desc="Resuming story...")
        result = run_env_agent(None, resume=True)
        
        return format_story_output(result)
    except Exception as e:
        return f"Error resuming story: {str(e)}"


def format_story_output(state):
    """Format the state output into readable text"""
    output = []
    
    if "main_goal" in state:
        output.append(f"**Main Goal:** {state['main_goal']}\n")
    
    if "characters" in state and state["characters"]:
        output.append("**Characters:**")
        for char in state["characters"]:
            output.append(f"- {char.name} ({char.role})")
        output.append("")
    
    if "entities" in state and state["entities"]:
        output.append("**Entities:**")
        for entity in state["entities"]:
            output.append(f"- {entity.name}: {entity.description}")
        output.append("")
    
    if "scenes" in state and state["scenes"]:
        output.append("**Story Scenes:**")
        for scene in state["scenes"]:
            output.append(f"\n**Scene {scene.no}:** {scene.description}")
            if scene.moments:
                for moment in scene.moments:
                    output.append(f"\n  *Moment {moment.no}:*")
                    for situation in moment.situations:
                        output.append(f"    {situation.who_said}: {situation.dialogue}")
                        if situation.action:
                            output.append(f"    *Action: {situation.action}*")
    
    output.append(f"\n**Goal Achieved:** {state.get('is_main_goal_achieved', False)}")
    
    return "\n".join(output)


def main():
    initialize_app()
    
    with gr.Blocks(title="Story Engine", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎭 Story Engine")
        gr.Markdown("Generate AI-powered interactive stories with dynamic characters and environments.")
        
        with gr.Tabs():
            with gr.Tab("Generate New Story"):
                with gr.Column():
                    prompt_input = gr.Textbox(
                        label="Story Prompt",
                        placeholder="Describe your story scenario...",
                        lines=4,
                        value="In a distant future, humanity has colonized Mars. Amidst political turmoil and environmental challenges, a group of explorers embarks on a mission to uncover ancient Martian artifacts that could hold the key to humanity's survival."
                    )
                    generate_btn = gr.Button("Generate Story", size="lg", variant="primary")
                    
                    output = gr.Markdown(label="Story Output")
                    
                    generate_btn.click(
                        fn=generate_new_story,
                        inputs=[prompt_input],
                        outputs=[output]
                    )
            
            with gr.Tab("Resume Story"):
                with gr.Column():
                    gr.Markdown("Resume your previously started story from where you left off.")
                    resume_btn = gr.Button("Resume Story", size="lg", variant="primary")
                    
                    output_resume = gr.Markdown(label="Story Output")
                    
                    resume_btn.click(
                        fn=resume_story,
                        outputs=[output_resume]
                    )
    
    return demo


if __name__ == "__main__":
    demo = main()
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False)
