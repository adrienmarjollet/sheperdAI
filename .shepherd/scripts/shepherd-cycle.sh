#!/usr/bin/env bash
# shepherd-cycle.sh — Launches a PM oversight cycle
#
# Usage: bash .shepherd/scripts/shepherd-cycle.sh [--max-turns N]
#
# This is the entry point for each autonomous PM cycle.
# It launches Claude Code with the PM identity and the CYCLE.md protocol.
# The PM reads state, makes decisions, delegates to developers, and updates state.
#
# Typically triggered by cron or a scheduler:
#   0 */6 * * * cd /path/to/repo && bash .shepherd/scripts/shepherd-cycle.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHEPHERD_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$SHEPHERD_DIR")"

MAX_TURNS="${1:-50}"

# ---------------------------------------------------------------------------
# Load PM system prompt
# ---------------------------------------------------------------------------
PM_PROMPT_FILE="$SHEPHERD_DIR/prompts/pm-system.md"

if [ ! -f "$PM_PROMPT_FILE" ]; then
    echo "ERROR: PM system prompt not found: $PM_PROMPT_FILE"
    exit 1
fi

PM_SYSTEM_PROMPT=$(cat "$PM_PROMPT_FILE")

# ---------------------------------------------------------------------------
# Build the cycle prompt
# ---------------------------------------------------------------------------
CYCLE_PROMPT="Run a Shepherd PM oversight cycle.

Follow the protocol in .shepherd/CYCLE.md exactly:

1. Read .shepherd/handoff.md to understand current state
2. Read .shepherd/portfolio.md for project overview
3. Read each active project's status.md
4. Assess priorities and decide what to work on
5. Write delegation briefs for tasks to delegate
6. Spawn developers: bash .shepherd/scripts/spawn-developer.sh <brief-path>
7. Verify results by running acceptance test commands
8. Update all state files (status.md, portfolio.md, decisions.md)
9. Write handoff.md for the next cycle
10. Write a journal entry in .shepherd/journal/

If no projects are loaded yet, check if project.yaml exists and run:
  bash .shepherd/scripts/load-project.sh project.yaml

Be methodical. Be thorough. Log your reasoning."

# ---------------------------------------------------------------------------
# Run the PM cycle
# ---------------------------------------------------------------------------
echo "=========================================="
echo "SHEPHERD PM: Starting oversight cycle"
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Max turns: $MAX_TURNS"
echo "=========================================="

cd "$REPO_ROOT"

claude -p \
    --dangerously-skip-permissions \
    --max-turns "$MAX_TURNS" \
    --system-prompt "$PM_SYSTEM_PROMPT" \
    "$CYCLE_PROMPT"

EXIT_CODE=$?

echo "=========================================="
echo "SHEPHERD PM: Cycle complete"
echo "Exit code: $EXIT_CODE"
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

exit $EXIT_CODE
