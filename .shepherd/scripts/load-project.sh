#!/usr/bin/env bash
# load-project.sh — Loads a project.yaml into .shepherd/ state files
#
# Usage: bash .shepherd/scripts/load-project.sh <project-yaml-path>
#
# This script parses project.yaml and creates the corresponding
# .shepherd/projects/<name>/ directory with status.md, spec.md, etc.
# It also updates portfolio.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHEPHERD_DIR="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 1 ]; then
    echo "ERROR: Missing project yaml path."
    echo "Usage: bash .shepherd/scripts/load-project.sh <project.yaml>"
    exit 1
fi

PROJECT_FILE="$1"

if [ ! -f "$PROJECT_FILE" ]; then
    echo "ERROR: Project file not found: $PROJECT_FILE"
    exit 1
fi

# ---------------------------------------------------------------------------
# Parse project.yaml using Python — write all state files directly from Python
# This avoids bash/JSON escaping issues entirely.
# ---------------------------------------------------------------------------
REPO_ROOT="$(dirname "$SHEPHERD_DIR")"

python3 << PYEOF
import yaml
import os
import sys

shepherd_dir = "$SHEPHERD_DIR"
repo_root = "$REPO_ROOT"
project_file = "$PROJECT_FILE"

with open(project_file) as f:
    data = yaml.safe_load(f)

# Normalize project name for directory
name = data.get('name', 'unnamed').lower().replace(' ', '-')
display_name = data.get('name', 'Unnamed')
description = data.get('description', 'No description')
working_dir = data.get('working_directory', './workspace')
deadline = str(data.get('deadline', 'None'))
tasks = data.get('tasks', [])

project_dir = os.path.join(shepherd_dir, 'projects', name)
os.makedirs(project_dir, exist_ok=True)

print(f"Loading project: {display_name}")
print(f"Directory: {project_dir}")

# --- spec.md ---
with open(project_file) as f:
    raw_yaml = f.read()

with open(os.path.join(project_dir, 'spec.md'), 'w') as f:
    f.write(f"# Project Spec: {display_name}\n\n")
    f.write(f"**Description**: {description}\n")
    f.write(f"**Working Directory**: {working_dir}\n")
    f.write(f"**Deadline**: {deadline}\n\n")
    f.write(f"## Source\nLoaded from: {project_file}\n\n")
    f.write(f"## Raw YAML\n\`\`\`yaml\n{raw_yaml}\`\`\`\n")
print("  Created: spec.md")

# --- status.md ---
with open(os.path.join(project_dir, 'status.md'), 'w') as f:
    f.write(f"# Project Status: {display_name}\n\n")
    f.write(f"**Working Directory**: {working_dir}\n")
    f.write(f"**Deadline**: {deadline}\n\n")
    f.write("## Tasks\n\n")
    f.write("| # | Task | Status | Test Command | Retries | Notes |\n")
    f.write("|---|------|--------|--------------|---------|-------|\n")
    for i, task in enumerate(tasks, 1):
        task_name = task.get('name', f'Task {i}')
        test_cmd = task.get('test_command', 'N/A').replace('|', '\\|')
        f.write(f"| {i} | {task_name} | PENDING | \`{test_cmd}\` | 0 | |\n")
    f.write("\n<!--\nStatus values: PENDING, IN_PROGRESS, DONE, BLOCKED, SKIPPED\n")
    f.write("Update this table as tasks progress.\n-->\n")
print("  Created: status.md")

# --- decisions.md ---
with open(os.path.join(project_dir, 'decisions.md'), 'w') as f:
    f.write(f"# Decisions Log: {display_name}\n\n")
    f.write("<!-- Log all strategic decisions here with reasoning. -->\n")
    f.write("<!-- Format: -->\n")
    f.write("<!-- ## [DATE] Decision Title -->\n")
    f.write("<!-- **Decision**: What was decided -->\n")
    f.write("<!-- **Alternatives**: What else was considered -->\n")
    f.write("<!-- **Reasoning**: Why this choice -->\n\n")
    f.write("(No decisions yet.)\n")
print("  Created: decisions.md")

# --- risks.md ---
with open(os.path.join(project_dir, 'risks.md'), 'w') as f:
    f.write(f"# Risk Register: {display_name}\n\n")
    f.write("<!-- Track known risks, their likelihood, impact, and mitigation. -->\n\n")
    f.write("| Risk | Likelihood | Impact | Mitigation | Status |\n")
    f.write("|------|-----------|--------|------------|--------|\n")
    f.write("| (none identified yet) | | | | |\n\n")
    f.write("<!--\nLikelihood: LOW, MEDIUM, HIGH\nImpact: LOW, MEDIUM, HIGH\n")
    f.write("Status: OPEN, MITIGATED, MATERIALIZED, CLOSED\n-->\n")
print("  Created: risks.md")

# --- Update portfolio.md ---
portfolio_path = os.path.join(shepherd_dir, 'portfolio.md')
with open(portfolio_path, 'r') as f:
    portfolio = f.read()

if f"| {display_name} |" in portfolio:
    print("  Portfolio: already listed (skipping)")
else:
    # Remove placeholder
    portfolio = portfolio.replace("| (no projects loaded yet) | | | | | | |\n", "")
    # Insert project line before the comment
    new_line = f"| {display_name} | ACTIVE | HIGH | 0 | {len(tasks)} | {deadline} | Loaded from {project_file} |\n"
    portfolio = portfolio.replace("<!--\n", new_line + "<!--\n", 1)
    with open(portfolio_path, 'w') as f:
        f.write(portfolio)
    print("  Portfolio: updated")

# --- Create working directory ---
workspace = os.path.join(repo_root, working_dir)
if not os.path.isdir(workspace):
    os.makedirs(workspace, exist_ok=True)
    print(f"  Workspace: created {working_dir}")
else:
    print("  Workspace: already exists")

print()
print(f"Project '{display_name}' loaded successfully.")
print(f"Tasks: {len(tasks)}")
print("Run 'bash .shepherd/scripts/shepherd-cycle.sh' to start the PM.")
PYEOF
