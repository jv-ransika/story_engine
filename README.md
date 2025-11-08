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

## Project Architecture

### Directory Structure

```
story_engine/
├── agents/                    # Multi-agent orchestration modules
│   ├── start_agent.py        # Story initialization agent - generates initial world state
│   ├── env_agent.py          # Environment orchestrator - manages scene flow and interactions
│   └── character_agent.py    # Character behavior agent - handles per-character dialogue, actions, and memory
├── pydantic_bp/              # Data models and blueprints
│   └── core.py               # Pydantic models: Character, Scene, Moment, CharacterMemoryUnit, Entity
├── utils/                    # Utility modules
│   ├── get_env.py            # Environment variable loading
│   └── model.py              # LLM client initialization
├── graph_outputs/            # Visualization outputs (workflows/state graphs)
├── main.py                   # Main entry point for CLI-based story execution
├── app.py                    # Gradio web interface for story generation
├── interface.py              # Alternative interface layer
├── test.py                   # Testing and debugging scripts
└── env_agent_checkpoint.db   # SQLite checkpoint database for state persistence
```

### Core Components

#### 1. **Agents** (`agents/`)

**StartAgent** (`start_agent.py`)
- Initializes the story world with user-provided context
- Generates initial characters with goals, personality traits, strengths, and weaknesses
- Creates entities relevant to the story
- Defines the starting scene and main narrative goal
- Output: `startAgentState` containing characters, entities, scene description, and main goal

**EnvAgent** (`agents/env_agent.py`)
- Orchestrates the episodic simulation workflow
- Manages scene generation and progression
- Sequences character interactions within moments
- Tracks narrative progress toward the main goal
- Handles state transitions between scenes and moments
- State: `EnvAgentState` with characters, scenes, current moment, and goal achievement status

**CharacterAgent** (`agents/character_agent.py`)
- Handles individual character behavior within a scene
- Generates character dialogue and actions via LLM
- Manages short-term and long-term memory updates
- Determines which characters listen to each interaction
- Updates character goals based on story events
- State: `CharacterAgentState` with scene, character, and memory updates

#### 2. **Data Models** (`pydantic_bp/core.py`)

- **Character**: Name, role, goals (long/short-term), personality, strengths, weaknesses, memory factor, memory units
- **Scene**: Collection of moments where characters interact
- **Moment**: Individual interactions between characters (dialogue, actions, listeners)
- **CharacterMemoryUnit**: Records of what was said, who listened, and what action was taken
- **Entity**: Story-relevant objects or concepts that characters interact with

#### 3. **Utilities** (`utils/`)

- **get_env.py**: Loads environment variables (e.g., `THREAD_ID` for checkpointing)
- **model.py**: Initializes LLM client (Google Generative API or custom backends)

#### 4. **Interfaces**

- **main.py**: CLI-based driver for starting/resuming stories with checkpoint management
- **app.py**: Gradio web UI for interactive story generation with persistent state
- **test.py**: Testing and debugging utilities

### Data Flow

```
User Input
    ↓
[StartAgent] → Characters, Entities, Scene, Goal
    ↓
[EnvAgent Workflow] → Scene Manager
    ↓
    ├→ [Scene Generator] → Next Scene
    ↓
    ├→ [Character Sequencer] → Next Character
    ↓
    └→ [CharacterAgent] → Dialogue, Action, Memory Updates
    ↓
[Memory & Checkpoint] → SQLite (env_agent_checkpoint.db)
    ↓
Narrative Output → CLI / Gradio UI
```

### State Persistence

- **Checkpointing**: Uses `langgraph.checkpoint.sqlite.SqliteSaver`
- **Thread ID**: Namespaces checkpoints for multiple story runs
- **Resumable**: Stories can be paused and resumed from any checkpoint
- **Database**: `env_agent_checkpoint.db` stores all workflow state

## Files of interest

- `main.py` — driver and examples for starting/resuming story runs
- `app.py` — Gradio web interface for interactive story generation
- `agents/start_agent.py` — story initialization agent
- `agents/env_agent.py` — environment orchestrator / workflow
- `agents/character_agent.py` — per-character behavior and memory handling
- `pydantic_bp/core.py` — Pydantic models for Character, Scene, Moment, MemoryUnit, Entity
- `utils/get_env.py`, `utils/model.py` — environment helpers and LLM clients

