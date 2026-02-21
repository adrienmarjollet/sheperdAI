# ShepherdAI

An autonomous Project Manager agent that orchestrates software development using **Claude Code** as the runtime for both PM and developer roles — with strict context separation between them.

No framework dependency. No LangChain. No DeepAgents. Just `claude -p` invocations, filesystem state, and shell scripts.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  CRON / SCHEDULER                                        │
│  Triggers PM cycle every N hours                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  SHEPHERD PM SESSION  (claude -p with PM identity)       │
│                                                          │
│  Reads:  .shepherd/ state files (handoff, portfolio...)   │
│  Writes: .shepherd/ state files only                     │
│  NEVER writes implementation code                        │
│                                                          │
│  Spawns isolated developer sessions:                     │
│  ┌──────────────────────────────────────────────────┐    │
│  │  DEVELOPER SESSION  (claude -p with dev identity) │    │
│  │  Reads:  delegation brief + working directory     │    │
│  │  Writes: working directory only                   │    │
│  │  NEVER modifies .shepherd/ state                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  After developer exits: PM verifies with test commands   │
└──────────────────────────────────────────────────────────┘
```

**Key insight**: Each `claude -p` call is a separate process with its own context window. The PM never sees implementation code. The developer never sees the roadmap. The filesystem mediates all communication through delegation briefs.

## Quick Start

### 1. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Clone and set up

```bash
git clone <repo-url> && cd sheperdAI
pip install pyyaml
```

### 3. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Define your project

Create or edit `project.yaml`:

```yaml
name: "My Web App"
description: "A Flask API with /health and /greet/<name> endpoints"
working_directory: "./workspace"
deadline: "2026-03-01"

tasks:
  - name: "Initialize Flask project"
    description: "Create app.py with a Flask app and a /health endpoint"
    test_command: "cd workspace && python -c \"from app import app; print('ok')\""

  - name: "Add greeting endpoint"
    description: "Add GET /greet/<name> returning JSON greeting"
    test_command: "cd workspace && python -m pytest test_app.py -v"
```

### 5. Load the project

```bash
bash .shepherd/scripts/load-project.sh project.yaml
```

This parses `project.yaml` and creates the `.shepherd/projects/<name>/` state files (status, decisions, risks).

### 6. Run a PM cycle

```bash
bash .shepherd/scripts/shepherd-cycle.sh
```

The PM reads state, decides what to work on, writes delegation briefs, spawns developers, verifies results, and updates state — all autonomously.

### 7. Set up cron for full autonomy (optional)

```bash
crontab -e
# Run every 6 hours:
0 */6 * * * cd /path/to/sheperdAI && bash .shepherd/scripts/shepherd-cycle.sh >> .shepherd/journal/cron.log 2>&1
```

## How It Works

### The Cycle

1. **Read State** — PM reads `.shepherd/handoff.md` (what happened last cycle) and project status files
2. **Assess** — Which tasks are DONE, PENDING, BLOCKED? What should we work on next?
3. **Decide** — Prioritize tasks, log decisions with reasoning in `decisions.md`
4. **Delegate** — Write a delegation brief and spawn a developer session (`claude -p`)
5. **Verify** — Run the acceptance test commands after the developer exits
6. **Handle Results** — PASS → mark done. FAIL → retry (up to 3x) or mark BLOCKED
7. **Handoff** — Write `handoff.md` so the next cycle knows where things stand

### Context Separation

| | PM Session | Developer Session |
|---|---|---|
| **Identity** | Project Manager | Software Developer |
| **Sees** | .shepherd/ state files | Delegation brief + working directory |
| **Doesn't see** | Source code, implementation details | Roadmap, other projects, deadlines |
| **Can write** | .shepherd/ files only | Working directory only |
| **Can't write** | Implementation code | .shepherd/ state files |
| **Lifecycle** | Long-running cycle | Born, implements, exits |
| **Continuity** | Via filesystem (handoff.md) | None (stateless per task) |

### Delegation Briefs

The brief is the **contract** between PM and developer. It contains:
- Task description and requirements
- Working directory
- Acceptance criteria (test commands)
- Constraints (what NOT to do)
- Context from previous attempts (for retries)

The developer appends a `## Results` section with status, files changed, and test outcomes.

## Project Structure

```
sheperdAI/
├── .shepherd/                    # All PM state and orchestration
│   ├── CYCLE.md                  # PM operating protocol (10 steps)
│   ├── handoff.md                # Cycle-to-cycle continuity
│   ├── portfolio.md              # All projects overview
│   ├── prompts/
│   │   ├── pm-system.md          # PM identity and rules
│   │   └── developer-system.md   # Developer identity and rules
│   ├── scripts/
│   │   ├── shepherd-cycle.sh     # Entry point: launches PM cycle
│   │   ├── spawn-developer.sh    # Spawns isolated developer session
│   │   └── load-project.sh       # Loads project.yaml into state files
│   ├── templates/
│   │   └── delegation-brief.md   # Template for delegation briefs
│   ├── delegations/
│   │   ├── active/               # Currently delegated tasks
│   │   ├── completed/            # Successfully verified tasks
│   │   └── failed/               # Tasks that failed after 3 retries
│   ├── projects/<name>/
│   │   ├── spec.md               # Original project spec
│   │   ├── status.md             # Task-by-task progress table
│   │   ├── decisions.md          # Strategic decisions with reasoning
│   │   └── risks.md              # Risk register
│   ├── journal/                  # Daily journal entries
│   └── reviews/                  # Weekly retrospectives
├── project.yaml                  # Project specification (input)
├── CLAUDE.md                     # Claude Code configuration
└── workspace/                    # Where code gets written
```

## Project YAML Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Project name |
| `description` | string | yes | What the project should do |
| `working_directory` | string | no | Where code is written (default `./workspace`) |
| `deadline` | string | no | Target date, `YYYY-MM-DD` |
| `tasks` | list | no | Pre-defined task list |

### Task fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Short, human-readable task name |
| `description` | string | yes | Full description with acceptance criteria |
| `test_command` | string | no | Shell command to verify the task (exit 0 = pass) |

If `tasks` is omitted, the PM agent auto-generates a task breakdown from the project `description`.

## Human Oversight

You are the board of directors. Review the agent's work by checking:

```bash
# What happened recently
git log --oneline .shepherd/

# What decisions were made and why
cat .shepherd/projects/*/decisions.md

# Current state of all projects
cat .shepherd/portfolio.md

# What the agent plans to do next
cat .shepherd/handoff.md
```

To steer the agent, edit `.shepherd/handoff.md` or project state files directly. The next cycle will pick up your changes.

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Python 3.10+ (for project loading script)
- `pyyaml` Python package
- `ANTHROPIC_API_KEY` environment variable
