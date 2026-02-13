---
name: task-decomposition
description: "Break down project specifications into ordered, actionable, testable tasks. Use this skill when: (1) project.yaml has no predefined tasks and you must generate them, (2) a task description is vague and needs refinement, (3) you need to identify dependencies between tasks, (4) you need to order tasks for optimal implementation, (5) planning the initial todo list with write_todos."
---

# Task Decomposition

Break a project specification into concrete, ordered, testable implementation tasks.

## Input Sources

### From project.yaml (pre-defined tasks)
```yaml
tasks:
  - name: "Initialize Flask project"
    description: "Create app.py with Flask app and /health endpoint"
    test_command: "python -c 'from app import app; print(ok)'"
```
Use these directly. Refine descriptions if they are too vague.

### From project description (no predefined tasks)
When `tasks` is empty or absent, decompose the `description` field into tasks.

## Decomposition Process

### Step 1: Identify deliverables
Read the project description and list every concrete output:
- Files to create
- Endpoints to implement
- Features to build
- Tests to write

### Step 2: Order by dependency
Arrange deliverables so each task builds on prior work:
1. **Foundation first**: Project scaffolding, config files, entry points
2. **Core models/data**: Database models, data structures, schemas
3. **Business logic**: Core functions, services, algorithms
4. **API/interface layer**: Endpoints, CLI commands, UI components
5. **Integration**: Connecting components, middleware, routing
6. **Tests**: Test files for each component
7. **Polish**: Error handling, logging, documentation

### Step 3: Make tasks atomic
Each task should:
- **Do one thing**: "Create User model" not "Create User model and API endpoints"
- **Be testable**: Include a `test_command` or verification step
- **Be self-contained**: The developer can complete it without guessing
- **Have clear output**: Specify exact files and behaviors

### Step 4: Write the todo list
```
write_todos(todos=[
  {"task": "Initialize project structure", "status": "pending"},
  {"task": "Create database models", "status": "pending"},
  {"task": "Implement API endpoints", "status": "pending"},
  {"task": "Add authentication", "status": "pending"},
  {"task": "Write test suite", "status": "pending"}
])
```

## Task Description Template

For each task delegated to the developer, include:

```
TASK: <concise name>
WORKING DIRECTORY: <path>
OBJECTIVE: <what to build>
FILES TO CREATE/MODIFY:
  - <path/to/file.py>: <what this file should contain>
DEPENDENCIES: <what must exist before this task>
ACCEPTANCE CRITERIA:
  - <specific testable condition>
  - <specific testable condition>
CONTEXT: <relevant info from prior tasks>
```

## Handling Vague Descriptions

When a project description is vague (e.g., "Build a web app"):

1. Infer scope from the project name and description
2. Choose the simplest viable tech stack
3. Start with a minimal working version
4. Create tasks that deliver incrementally (each task produces a runnable state)

## Task Sizing Guidelines

- **Too small**: "Add import statement" -- merge into parent task
- **Right size**: "Create Flask app with /health endpoint and tests" -- clear, completable in one delegation
- **Too large**: "Build the entire backend" -- split into model, endpoint, and test tasks

Aim for 3-10 tasks per project. Fewer means tasks are too broad; more means unnecessary granularity.

## Dependency Detection

Common dependency patterns:
- Tests depend on the code they test
- API endpoints depend on models/schemas
- Authentication depends on user models
- Frontend depends on API endpoints
- Integration tests depend on all components

Never delegate a task before its dependencies are complete and verified.
