---
name: git-workflow
description: "Manage version control with git: initialize repositories, stage changes, commit with meaningful messages, and check status. Use this skill when: (1) initializing a git repo for a new project, (2) committing completed work after verification, (3) checking what files have changed, (4) creating branches for feature isolation."
---

# Git Workflow

Manage version control for the project using git via the `execute` tool.

## Initialize Repository

```
execute(command="cd <working_dir> && git init")
execute(command="cd <working_dir> && git add -A && git commit -m 'Initial project scaffold'")
```

Only initialize once, at the start of the project after the initial scaffolding is verified.

## Check Status

```
# See what changed
execute(command="cd <working_dir> && git status")

# See specific changes
execute(command="cd <working_dir> && git diff")

# See staged changes
execute(command="cd <working_dir> && git diff --cached")
```

## Commit After Verified Tasks

Commit ONLY after a task passes test verification:

```
# Stage specific files
execute(command="cd <working_dir> && git add src/models/user.py tests/test_user.py")

# Commit with descriptive message
execute(command="cd <working_dir> && git commit -m 'Add User model with name and email fields'")
```

### Commit Message Format

Follow conventional commits:
```
<type>: <short description>

Types:
  feat:     new feature
  fix:      bug fix
  refactor: code change that neither fixes a bug nor adds a feature
  test:     adding or updating tests
  chore:    build process, dependencies, config
  docs:     documentation
```

Examples:
```
feat: add GET /users endpoint with pagination
fix: resolve circular import between models and routes
test: add integration tests for authentication flow
chore: add Flask and SQLAlchemy to requirements.txt
```

## Branching (Optional)

For larger projects with multiple parallel features:

```
# Create feature branch
execute(command="cd <working_dir> && git checkout -b feature/user-auth")

# After feature is complete, merge back
execute(command="cd <working_dir> && git checkout main && git merge feature/user-auth")
```

For most single-developer ShepherdAI projects, committing directly to main is sufficient.

## When to Commit

- **After each verified task**: Provides rollback points
- **After environment setup**: Captures the initial scaffolding
- **Before risky changes**: Create a savepoint

Do NOT commit:
- Unverified code (tests haven't passed)
- Temporary debug files
- Environment-specific files (.env, .venv, node_modules)

## .gitignore

Ensure a .gitignore exists early. Delegate its creation to the developer:

```
Common entries:
  Python: __pycache__/, *.pyc, .venv/, *.egg-info/
  Node:   node_modules/, dist/, .env
  General: .DS_Store, *.log, .idea/, .vscode/
```
