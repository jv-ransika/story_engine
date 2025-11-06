# Multi‑Agent Storyworld Simulator (Story Engine)

Multi‑Agent Storyworld Simulator is an ongoing project that simulates episodic, character‑driven narratives using orchestrated LLM agents, state‑graph workflows, per‑character memory, and SQLite checkpointing for resumable execution.

## Highlights

- Multi‑agent architecture: autonomous character agents, an environment orchestrator, and a story initializer.
- Stateful simulation: scenes, moments, per‑character short/long term memory units, and goal checks.
- Checkpointing: saves and resumes story state using SQLite so long-running narratives can be paused and resumed.
- Designed for reproducible, goal‑directed episodic story generation and emergent interactions between agents.

## Tech stack

- Python 3.10+
- Pydantic (data models and validation)
- LangGraph (state/workflow orchestration)
- Google Generative API (optional, pluggable LLM backends)
- SQLite (checkpointing via `langgraph.checkpoint.sqlite.SqliteSaver`)

## Installation (recommended)

1. Create a virtual environment and activate it (zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies. If you have a `requirements.txt` add it; otherwise install core libs manually:

```bash
# Example (adjust versions as needed)
pip install pydantic langgraph google-generative-api
```

Note: package names and availability depend on your environment and preferred LLM provider. Replace `google-generative-api` with your LLM client of choice.

## Usage

Run the main driver which initializes or resumes a story:

```zsh
# Set the thread id used for checkpointing (example):
export THREAD_ID="story-1"

python3 main.py

# The script will prompt: "Do you want to restart the story? (y/n):"
# Enter 'y' to start a fresh story (runs start agent + env agent).
# Enter 'n' to resume from the checkpoint stored in env_agent_checkpoint.db.
```

How it works (brief): `main.py` uses `start_agent_app` to produce initial characters, entities, a starting scene description and a main goal. The environment workflow (`env_agent_workflow`) is compiled with a `SqliteSaver` checkpointer and invoked to run the episodic simulation. The code reads `thread_id` from environment (via `utils.get_env.get_env_variable`) to namespace checkpoints.

## Files of interest

- `main.py` — driver and examples for starting/resuming story runs
- `agents/start_agent.py` — story initialization agent
- `agents/env_agent.py` — environment orchestrator / workflow
- `agents/character_agent.py` — per-character behavior and memory handling
- `pydantic_bp/core.py` — Pydantic models for Character, Scene, Moment, MemoryUnit
- `utils/get_env.py`, `utils/model.py` — environment helpers and LLM clients

