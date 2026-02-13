"""Scaffold .deepagents/ directory from project.yaml for use with the DeepAgents CLI."""

import argparse
import os
from pathlib import Path

import yaml

from shepherd.templates import (
    CLAUDE_CODE_SKILL_MD,
    CODE_REVIEW_SKILL_MD,
    DEBUGGING_SKILL_MD,
    DEPENDENCY_MANAGEMENT_SKILL_MD,
    DEVELOPER_AGENTS_MD,
    ENVIRONMENT_SETUP_SKILL_MD,
    ERROR_ANALYSIS_SKILL_MD,
    GIT_WORKFLOW_SKILL_MD,
    PM_AGENTS_MD,
    PROGRESS_REPORTING_SKILL_MD,
    TASK_DECOMPOSITION_SKILL_MD,
    TEST_RUNNER_SKILL_MD,
)


def init(project_file: str = "project.yaml") -> None:
    """Scaffold .deepagents/ directory from a project.yaml file.

    Creates the directory structure and configuration files needed to run
    the ShepherdAI PM agent via ``deepagents --agent shepherd``.

    Args:
        project_file: Path to the project YAML file.
    """
    # Validate project.yaml
    with open(project_file) as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict) or "name" not in config:
        raise SystemExit(f"Error: {project_file} must contain at least a 'name' field.")

    project_root = Path.cwd()
    deepagents_dir = project_root / ".deepagents"

    # Create directory structure
    files = {
        deepagents_dir / "AGENTS.md": PM_AGENTS_MD,
        deepagents_dir / "agents" / "developer" / "AGENTS.md": DEVELOPER_AGENTS_MD,
        deepagents_dir / "skills" / "claude-code" / "SKILL.md": CLAUDE_CODE_SKILL_MD,
        deepagents_dir / "skills" / "test-runner" / "SKILL.md": TEST_RUNNER_SKILL_MD,
        deepagents_dir / "skills" / "task-decomposition" / "SKILL.md": TASK_DECOMPOSITION_SKILL_MD,
        deepagents_dir / "skills" / "code-review" / "SKILL.md": CODE_REVIEW_SKILL_MD,
        deepagents_dir / "skills" / "debugging" / "SKILL.md": DEBUGGING_SKILL_MD,
        deepagents_dir / "skills" / "environment-setup" / "SKILL.md": ENVIRONMENT_SETUP_SKILL_MD,
        deepagents_dir / "skills" / "dependency-management" / "SKILL.md": DEPENDENCY_MANAGEMENT_SKILL_MD,
        deepagents_dir / "skills" / "git-workflow" / "SKILL.md": GIT_WORKFLOW_SKILL_MD,
        deepagents_dir / "skills" / "progress-reporting" / "SKILL.md": PROGRESS_REPORTING_SKILL_MD,
        deepagents_dir / "skills" / "error-analysis" / "SKILL.md": ERROR_ANALYSIS_SKILL_MD,
    }

    created = []
    skipped = []

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            skipped.append(path.relative_to(project_root))
        else:
            path.write_text(content)
            created.append(path.relative_to(project_root))

    # Create working directory
    working_dir = config.get("working_directory", "./workspace")
    os.makedirs(working_dir, exist_ok=True)

    # Summary
    print(f"Initialized ShepherdAI for project '{config['name']}'")
    if created:
        for p in created:
            print(f"  created: {p}")
    if skipped:
        for p in skipped:
            print(f"  skipped (exists): {p}")
    print()
    print("Run:  deepagents --agent shepherd")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold .deepagents/ for the ShepherdAI PM agent"
    )
    parser.add_argument(
        "project_file",
        nargs="?",
        default="project.yaml",
        help="Path to project.yaml (default: project.yaml)",
    )
    args = parser.parse_args()
    init(args.project_file)


if __name__ == "__main__":
    main()
