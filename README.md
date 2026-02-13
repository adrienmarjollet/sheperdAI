# ShepherdAI

A Project Manager AI agent that orchestrates software development. ShepherdAI reads a project specification from a YAML file, breaks it into tasks, delegates coding to a developer subagent, and verifies results through automated tests — all via the [DeepAgents](https://github.com/langchain-ai/deepagents) CLI.

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url> && cd shepherdAI

uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
git submodule update --init --recursive
uv pip install -e deepagents/libs/deepagents
uv pip install -e deepagents/libs/cli
```

### 2. Set your API key

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=...          # optional, for web search
```

### 3. Define your project

Create (or edit) `project.yaml`:

```yaml
name: "My Web App"
description: "A Flask API with /health and /greet/<name> endpoints"
working_directory: "./workspace"
deadline: "2026-03-01"

tasks:
  - name: "Initialize Flask project"
    description: "Create app.py with a Flask app and a /health endpoint returning {\"status\": \"ok\"}"
    test_command: "cd workspace && python -c \"from app import app; print('ok')\""

  - name: "Add greeting endpoint"
    description: "Add GET /greet/<name> returning {\"message\": \"Hello, <name>!\"}"
    test_command: "cd workspace && python -m pytest test_app.py -v"
```

### 4. Scaffold the agent configuration

```bash
python -m shepherd.init project.yaml
```

This generates the `.deepagents/` directory with agent instructions and skills. Existing files are never overwritten.

### 5. Run the PM agent

```bash
deepagents --agent shepherd
```

The agent reads `project.yaml`, plans the work, delegates each task to a developer subagent, runs the test commands, and retries failures up to 3 times.

## CLI Usage

### Interactive mode (default)

```bash
deepagents --agent shepherd
```

Opens a TUI where you can chat with the PM agent, approve actions, and steer the project.

### Non-interactive mode

```bash
deepagents --agent shepherd -n "Begin working on the project"
```

Sends a single instruction and lets the agent run to completion without prompts.

### Resume a previous session

```bash
deepagents --agent shepherd -r
```

Picks up where the last session left off, preserving full conversation history and task state.

## Project YAML Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Project name |
| `description` | string | yes | What the project should do |
| `working_directory` | string | no | Where code is written (default `./workspace`) |
| `deadline` | string | no | Target date, `YYYY-MM-DD` |
| `tasks` | list | no | Pre-defined task list (see below) |

### Task fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Short, human-readable task name |
| `description` | string | yes | Full description with acceptance criteria |
| `test_command` | string | no | Shell command to verify the task (exit code 0 = pass) |

If `tasks` is omitted, the PM agent auto-generates a task breakdown from the project `description`.

## How It Works

```
project.yaml
     │
     ▼
┌──────────────┐   task() tool   ┌──────────────────┐
│  PM Agent    │ ──────────────▶ │ Developer Agent   │
│              │                 │                   │
│  • reads     │                 │  • writes code    │
│    project   │  ◀──────────── │  • runs commands  │
│  • plans     │   result        │  • reports back   │
│  • verifies  │                 └──────────────────┘
│  • retries   │
└──────────────┘
```

1. **Plan** — The PM reads `project.yaml` and creates a todo list (or uses the pre-defined tasks).
2. **Delegate** — Each task is handed to the developer subagent via the `task()` tool. The PM never writes code itself.
3. **Verify** — After the developer finishes, the PM runs the `test_command`. Exit code 0 means pass.
4. **Retry** — If a test fails, the PM sends the error output back to the developer for another attempt (up to 3 retries). After 3 failures the task is marked BLOCKED.
5. **Report** — Once all tasks pass (or are blocked), the PM generates a summary.

## Project Structure

```
shepherdAI/
├── .deepagents/                  # Agent & skill configuration (generated)
│   ├── AGENTS.md                 # PM agent instructions
│   ├── agents/
│   │   └── developer/
│   │       └── AGENTS.md         # Developer subagent instructions
│   └── skills/                   # 11 skill definitions
│       ├── claude-code/          # Claude Code CLI delegation
│       ├── test-runner/          # Test execution & result parsing
│       ├── task-decomposition/   # Breaking projects into tasks
│       ├── code-review/          # Code review before testing
│       ├── debugging/            # Systematic failure diagnosis
│       ├── environment-setup/    # Project environment preparation
│       ├── dependency-management/# Package installation & conflicts
│       ├── git-workflow/         # Version control management
│       ├── progress-reporting/   # Status tracking & summaries
│       └── error-analysis/       # Error parsing & retry prompts
├── deepagents/                   # Git submodule (DeepAgents framework)
├── shepherd/                     # Scaffolding module
│   ├── __init__.py
│   ├── init.py                   # Generates .deepagents/ from templates
│   └── templates.py              # All template strings
├── project.yaml                  # Your project definition
├── requirements.txt              # Python dependencies
└── .env.example                  # API key template
```

## Scaffolding New Projects

To use ShepherdAI in a different directory or for a new project:

1. Write a `project.yaml` describing your project.
2. Run the scaffolder:

```bash
python -m shepherd.init path/to/project.yaml
```

This creates the full `.deepagents/` tree from built-in templates. Files that already exist are skipped, so you can safely re-run it after adding new skills upstream.

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- An `ANTHROPIC_API_KEY` (or another LLM provider key supported by DeepAgents)
