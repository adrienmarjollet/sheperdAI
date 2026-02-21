# Shepherd AI — Claude Code Configuration

## Project Overview
Shepherd is an autonomous project management system that uses Claude Code for both
PM orchestration and developer execution, with strict separation between the two roles.

## Architecture
- **PM sessions** (`claude -p` with PM identity): Read state, make decisions, delegate, verify
- **Developer sessions** (`claude -p` with developer identity): Implement tasks from briefs, report results
- **Filesystem** (`.shepherd/`): The interface between PM and developer. Source of truth for all state.
- **No framework dependency**: Uses raw Claude Code CLI (`claude -p`) instead of DeepAgents

## Key Directories
- `.shepherd/` — All PM state, protocols, briefs, and scripts
- `.shepherd/prompts/` — System prompts for PM and developer identities
- `.shepherd/scripts/` — Shell scripts for spawning sessions and loading projects
- `.shepherd/delegations/` — Task briefs (active, completed, failed)
- `.shepherd/projects/` — Per-project state (status, decisions, risks)
- `project.yaml` — Project specification (input)

## How to Run
```bash
# Load a project
bash .shepherd/scripts/load-project.sh project.yaml

# Run a PM cycle (manually)
bash .shepherd/scripts/shepherd-cycle.sh

# Set up cron (every 6 hours)
crontab -e
# 0 */6 * * * cd /path/to/sheperdAI && bash .shepherd/scripts/shepherd-cycle.sh >> .shepherd/journal/cron.log 2>&1
```

## Rules
- The PM NEVER writes implementation code
- The developer NEVER modifies `.shepherd/` state files (except appending Results to its brief)
- All decisions are logged with reasoning in `projects/<name>/decisions.md`
- All tasks must pass acceptance tests before being marked DONE
- Maximum 3 retries per task before marking BLOCKED
