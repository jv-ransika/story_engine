# Multi‑Agent Storyworld Simulator (Story Engine)

Multi‑Agent Storyworld Simulator is an ongoing project that simulates episodic, character‑driven narratives using orchestrated LLM agents, state‑graph workflows, per‑character memory, and SQLite checkpointing for resumable execution.

## Highlights

- **Multi‑agent orchestration**: 6+ specialized agents working in coordinated workflows (Start Agent, Scene Creator, Moment Runner, Scene Validator, Goal Validator, and Per-Character Agents).
- **Autonomous characters**: Each character has independent agents with personality-driven decision-making and emergent behavior.
- **Stateful simulation**: Scenes, moments, per‑character short/long term memory units (115-250 events), and intelligent goal validation.
- **Persistent narratives**: SQLite checkpointing enables pause/resume from any exact moment without data loss.
- **Designed for**: Reproducible, goal‑directed episodic story generation with emergent multi-agent interactions.

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

**Start Agent** (`start_agent.py`) - Story Initialization
- Initializes the story world with user-provided narrative context
- Generates initial character profiles with goals, personality traits, strengths, and weaknesses
- Creates story-relevant entities and objects
- Defines the starting scene description and main narrative goal
- Output: Characters, entities, opening scene, and main objective ready for episodic simulation

**Environment Agent Workflow** (`agents/env_agent.py`) - Multi-Agent Orchestration
A sophisticated LangGraph state-graph containing 5 specialized agent nodes that work in coordinated cycles:

1. **Scene Creator Agent**
   - Dynamically generates new scenes based on narrative progress, character availability, and entities
   - Considers previous scenes and story trajectory
   - Determines which characters will participate in the upcoming scene
   - Output: Scene description with character assignments

2. **Moment Runner Agent**
   - Orchestrates individual character interactions within each scene
   - Sequences character turns and dialogue moments
   - Invokes Character Agents for each participating character
   - Collects and aggregates character responses (dialogue, actions, memory updates)
   - Output: Completed moment with all character interactions recorded

3. **Scene Validator Agent**
   - Evaluates whether the current scene has achieved its narrative purpose
   - Determines if scene objectives are met or if more moments are needed
   - Decides scene completion status
   - Conditional logic: If scene incomplete → loops back to Moment Runner; if complete → proceeds to Goal Validator
   - Output: `is_scene_complete` flag

4. **Goal Validator Agent**
   - Assesses progress toward the main story objective
   - Evaluates if the central narrative goal has been achieved
   - If goal not achieved → triggers Scene Creator for the next scene
   - If goal achieved → ends the narrative workflow
   - Tracks goal achievement status across episodes
   - Output: `is_main_goal_achieved` flag

5. **Character Agents** (`agents/character_agent.py`) - Per-Character Autonomous Behavior
   - Invoked by Moment Runner for each character participating in a moment
   - Generate character-specific dialogue and actions based on:
     - Character personality traits, strengths, and weaknesses
     - Current short-term and long-term goals
     - Memory of past events (115-250 memory units per character)
     - Scene context and other characters present
   - Maintain independent memory systems:
     - Short-term memory: Recent events (dynamically sized based on memory_factor)
     - Long-term memory: Important events and learnings
   - Determine which other characters listen to each interaction
   - Update personal goals based on scene developments
   - Output: Dialogue, action, memory updates, and listener assignments

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
[Start Agent] → Characters, Entities, Scene, Goal
    ↓
[Environment Agent Workflow - LangGraph State Graph]
    ├→ [Scene Creator Agent] → Generate Next Scene
    │    ↓
    ├→ [Moment Runner Agent] → Execute Moment
    │    ├→ [Character Agent 1] → Dialogue, Action, Memory
    │    ├→ [Character Agent 2] → Dialogue, Action, Memory
    │    └→ [Character Agent N] → Dialogue, Action, Memory
    │    ↓
    ├→ [Scene Validator Agent] → Is Scene Complete?
    │    ├─ NO → Loop back to Moment Runner
    │    └─ YES → Proceed
    │    ↓
    └→ [Goal Validator Agent] → Is Main Goal Achieved?
         ├─ NO → Loop back to Scene Creator
         └─ YES → End Workflow
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

