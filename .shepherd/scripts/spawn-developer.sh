#!/usr/bin/env bash
# spawn-developer.sh — Spawns an isolated Claude Code developer session
#
# Usage: bash .shepherd/scripts/spawn-developer.sh <brief-path>
#
# This script:
# 1. Reads the developer system prompt
# 2. Launches a separate Claude Code session with developer identity
# 3. The developer reads the brief, implements the task, appends results
# 4. Exits when done — the PM then verifies the results
#
# IMPORTANT: The developer session is a completely separate process.
# It has NO access to the PM's context window.
# It can ONLY see: the brief file + the project working directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHEPHERD_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$SHEPHERD_DIR")"

# ---------------------------------------------------------------------------
# Validate arguments
# ---------------------------------------------------------------------------
if [ $# -lt 1 ]; then
    echo "ERROR: Missing brief path."
    echo "Usage: bash .shepherd/scripts/spawn-developer.sh <brief-path>"
    exit 1
fi

BRIEF_PATH="$1"

if [ ! -f "$BRIEF_PATH" ]; then
    echo "ERROR: Brief file not found: $BRIEF_PATH"
    exit 1
fi

# ---------------------------------------------------------------------------
# Load developer system prompt
# ---------------------------------------------------------------------------
DEVELOPER_PROMPT_FILE="$SHEPHERD_DIR/prompts/developer-system.md"

if [ ! -f "$DEVELOPER_PROMPT_FILE" ]; then
    echo "ERROR: Developer system prompt not found: $DEVELOPER_PROMPT_FILE"
    exit 1
fi

DEVELOPER_SYSTEM_PROMPT=$(cat "$DEVELOPER_PROMPT_FILE")

# ---------------------------------------------------------------------------
# Build the task prompt
# ---------------------------------------------------------------------------
TASK_PROMPT="Read the delegation brief at '${BRIEF_PATH}' and execute the task described in it.

Follow the developer protocol:
1. Read the brief completely
2. Explore the working directory specified in the brief
3. Implement all requirements
4. Run the acceptance test commands
5. Append a ## Results section to the brief file with status, files changed, test results, and notes

Important rules:
- Do NOT modify any file under .shepherd/ except appending Results to your brief
- Do NOT modify files outside the working directory specified in the brief
- Implement EXACTLY what the brief asks — nothing more, nothing less
- Run ALL acceptance test commands and report their exit codes"

# ---------------------------------------------------------------------------
# Spawn the developer session
# ---------------------------------------------------------------------------
echo "=========================================="
echo "SHEPHERD: Spawning developer session"
echo "Brief: $BRIEF_PATH"
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

cd "$REPO_ROOT"

# Launch Claude Code in non-interactive mode with developer identity
# --dangerously-skip-permissions: allows autonomous operation
# --max-turns: prevents runaway sessions
# --system-prompt: enforces developer identity
claude -p \
    --dangerously-skip-permissions \
    --max-turns 30 \
    --system-prompt "$DEVELOPER_SYSTEM_PROMPT" \
    "$TASK_PROMPT"

EXIT_CODE=$?

echo "=========================================="
echo "SHEPHERD: Developer session exited"
echo "Exit code: $EXIT_CODE"
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

exit $EXIT_CODE
