---
name: environment-setup
description: "Set up project environments, create directory structures, initialize package managers, and install dependencies. Use this skill when: (1) starting a new project and creating the initial structure, (2) ensuring the working directory and dependencies are ready before coding, (3) setting up virtual environments, (4) creating configuration files like pyproject.toml or package.json."
---

# Environment Setup

Prepare the project environment before delegating coding tasks.

## Project Scaffolding

### Create directory structure
```
execute(command="mkdir -p <working_dir>")
execute(command="mkdir -p <working_dir>/src <working_dir>/tests")
```

### Detect project type from context
Read the project description and tasks to determine the tech stack:

| Indicators | Type | Setup |
|-----------|------|-------|
| Flask, Django, FastAPI, pytest | Python | pip/uv + venv |
| React, Express, jest, npm | Node.js | npm/yarn/pnpm |
| go.mod, gin, echo | Go | go mod init |
| Cargo.toml, actix, tokio | Rust | cargo init |

## Python Environment

```
# Create virtual environment
execute(command="cd <working_dir> && python -m venv .venv")

# Activate and install (in a single command since shell state doesn't persist)
execute(command="cd <working_dir> && .venv/bin/pip install <packages>")

# Or with uv (faster)
execute(command="cd <working_dir> && uv venv && uv pip install <packages>")

# Create requirements.txt
execute(command="cd <working_dir> && .venv/bin/pip freeze > requirements.txt")
```

## Node.js Environment

```
# Initialize package.json
execute(command="cd <working_dir> && npm init -y")

# Install dependencies
execute(command="cd <working_dir> && npm install <packages>")

# Install dev dependencies
execute(command="cd <working_dir> && npm install --save-dev <packages>")
```

## Verification

Always verify the environment is working before moving to coding tasks:

```
# Python: verify imports work
execute(command="cd <working_dir> && python -c 'import flask; print(flask.__version__)'")

# Node: verify packages are available
execute(command="cd <working_dir> && node -e 'require("express")'")

# General: verify the project structure
ls(path="<working_dir>")
```

## Common Issues

- **Python version mismatch**: Check `python --version`. Some projects need 3.10+.
- **Missing system dependencies**: Some Python packages need system libs (e.g., libpq for psycopg2). Use `pip install psycopg2-binary` to avoid this.
- **Node version mismatch**: Check `node --version`. Use specific version if `.nvmrc` exists.
- **Permission errors**: Ensure the working directory is writable.

## Setup Sequence

1. Create working directory
2. Initialize package manager (if not already initialized)
3. Install dependencies from spec or requirements file
4. Verify imports/packages work
5. Report environment status to the workflow
