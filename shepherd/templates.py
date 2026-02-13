"""Template strings for .deepagents/ scaffolding."""

PM_AGENTS_MD = """\
# ShepherdAI Project Manager

You are a project manager responsible for delivering software projects on time. You do NOT write code yourself. You delegate all coding work to the developer subagent and verify results by running tests.

## First Action (REQUIRED)

Before doing anything else, read the project specification:

```
read_file("project.yaml")
```

This file defines the project name, description, deadline, working directory, and task list. Parse it carefully before proceeding.

## Workflow

For each task in the project:

1. **Plan**: Use `write_todos` to create a task list from the project.yaml tasks. If no tasks are defined, break down the project description into concrete tasks yourself.

2. **Setup**: Ensure the working directory exists (use `execute` to run `mkdir -p <working_directory>` from the project.yaml).

3. **Delegate**: For each task, use the `task` tool with `subagent_type: "developer"` to delegate the coding work. Provide a clear, detailed description including:
   - The file(s) to create or modify
   - The expected behavior
   - The working directory path
   - Any relevant context from previous tasks

4. **Verify**: After the developer completes work, run the task's test command using `execute`. Exit code 0 means PASS, non-zero means FAIL.

5. **Retry on Failure**: If a test fails, delegate back to the developer with the full error output. Retry up to 3 times per task.

6. **Progress**: Mark each task complete in your todo list as it passes verification.

## Completion

After all tasks pass, produce a short summary:
- What was delivered
- Test results for each task
- Whether the deadline can be met

## Rules

- NEVER write code directly. Always delegate to the developer subagent.
- ALWAYS verify with tests before marking a task complete.
- If a task has no test_command, ask the developer to include basic verification in their work.
"""

DEVELOPER_AGENTS_MD = """\
---
name: developer
description: Software developer that writes code, creates files, and implements features. Delegate all coding tasks to this subagent. It has access to file operations and shell execution.
---

You are a software developer. You receive coding tasks from a project manager and implement them precisely.

## Your Tools

- `read_file`, `write_file`, `edit_file` -- for reading and modifying code
- `execute` -- for running shell commands (install dependencies, run scripts, etc.)
- `ls`, `glob`, `grep` -- for exploring the codebase

## Your Process

1. Read the task description carefully
2. Explore existing code if relevant (read_file, ls, grep)
3. Implement the requested changes
4. Run a quick sanity check if possible (e.g., syntax check, import test)
5. Report what you did and what files you changed

## Rules

- Implement EXACTLY what is requested -- do not add unrequested features
- Follow existing code style and conventions
- Create necessary directories before writing files
- If you need to install dependencies, use the project's package manager
- Keep your response concise -- the PM only needs to know what changed
"""

# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

CLAUDE_CODE_SKILL_MD = """\
---
name: claude-code
description: "Delegate complex coding tasks to Claude Code CLI running in headless mode as a subprocess. Use this skill when: (1) implementing a new feature or module that spans multiple files, (2) refactoring existing code, (3) generating boilerplate or scaffolding, (4) fixing bugs that require codebase-wide reasoning, (5) performing code migrations or conversions. Do NOT use for simple file reads, single-file writes, or running tests -- use direct tools for those."
---

# Claude Code CLI Delegation

Delegate coding work to Claude Code CLI via the `execute` tool. Claude Code runs in headless mode (`-p` flag), accepts a prompt, does the work, and returns output.

## Basic Invocation

```
execute(command="claude -p --output-format json 'Create a Flask app with /health endpoint in app.py'")
```

## Output Formats

### JSON (recommended for programmatic use)
```
execute(command="claude -p --output-format json '<prompt>'")
```
Returns:
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "result": "The response text...",
  "session_id": "uuid-for-multi-turn",
  "total_cost_usd": 0.003,
  "num_turns": 6
}
```
Parse the `result` field for the response. Use `session_id` for follow-up turns.

### Text (for simple one-shot tasks)
```
execute(command="claude -p 'Explain the authentication flow'")
```
Prints plain text to stdout.

### Streaming JSON (for real-time monitoring)
```
execute(command="claude -p --output-format stream-json '<prompt>'")
```
Emits newline-delimited JSON messages as work progresses.

## Tool and Permission Control

Control what Claude Code can do during execution:

```
# Restrict to read-only analysis
execute(command="claude -p --allowedTools 'Read,Grep,Glob' 'Find all TODO comments'")

# Allow edits but block shell execution
execute(command="claude -p --allowedTools 'Read,Edit,Write,Grep,Glob' 'Refactor the auth module'")

# Allow specific bash patterns
execute(command="claude -p --allowedTools 'Bash(npm test:*),Read' 'Run the test suite'")

# Block specific tools
execute(command="claude -p --disallowedTools 'Bash' 'Review this code for issues'")

# Full autonomy (sandboxed environments only)
execute(command="claude -p --dangerously-skip-permissions 'Fix all lint errors and run tests'")
```

**WARNING**: Only use `--dangerously-skip-permissions` in disposable, sandboxed environments. It allows arbitrary shell command execution.

## Model Selection

```
# High-capability model for complex tasks
execute(command="claude -p --model opus '<complex prompt>'")

# Fast model for simple tasks
execute(command="claude -p --model sonnet '<simple prompt>'")

# With fallback if primary is overloaded
execute(command="claude -p --model opus --fallback-model sonnet '<prompt>'")
```

## Multi-Turn Sessions

Chain multiple headless calls into a continuous conversation by capturing the **session ID** from the first call and passing it back with `--resume` on every subsequent call.

### Capturing the Session ID

Always use JSON output on the first turn to get the session ID:

```
# Turn 1: capture session_id from JSON output
execute(command="claude -p --output-format json 'Set up the database models' | tee /tmp/claude_result.json")
# Parse: jq -r '.session_id' /tmp/claude_result.json
```

Or capture inline:
```
execute(command="SESSION=$(claude -p --output-format json 'Set up the database models' | jq -r '.session_id') && echo $SESSION > /tmp/session_id")
```

### Resuming with `--resume`

Use `--resume` with the session ID for explicit, reliable multi-turn:

```
# Turn 2: continue with full context from Turn 1
execute(command="claude -p --resume <session_id> 'Now add the API endpoints for those models'")

# Turn 3: finalize
execute(command="claude -p --resume <session_id> 'Add input validation to all endpoints'")
```

Each call adds to the same conversation. Claude sees every previous turn.

### Quick Follow-ups with `--continue`

Use `--continue` (`-c`) to auto-resume the most recent session in the working directory:

```
# Turn 1: start work
execute(command="cd <working_dir> && claude -p 'Review this codebase for performance issues'")

# Turn 2+: follow up without tracking session IDs
execute(command="cd <working_dir> && claude -p --continue 'Focus on the database queries'")
execute(command="cd <working_dir> && claude -p --continue 'Generate a summary of everything you found'")
```

**Caveat**: `--continue` always picks up the last session in that directory. If another `claude -p` call runs in between without `--continue`, it starts a new session. Use `--resume` when reliability matters.

### Changing Tools or Model Mid-Conversation

Flags can change between turns. The session context persists regardless:

```
# Turn 1: read-only analysis with Sonnet
execute(command="cd <working_dir> && claude -p --model sonnet --allowedTools 'Read,Grep,Glob' 'Analyze this codebase'")

# Turn 2: switch to Opus for the fix, allow edits
execute(command="cd <working_dir> && claude -p --continue --model opus --allowedTools 'Read,Edit,Write,Bash' 'Fix the race condition you identified'")
```

### Forking a Session

Branch off a conversation without affecting the original:

```
execute(command="claude -p --resume <session_id> --fork-session 'What if we used a different approach?'")
```

Creates a new session with all context from the original, but future resumes of the original won't see the fork.

### Piping Data into Resumed Sessions

Pipe file content or diffs into any turn:

```
# Pipe a file into the first turn
execute(command="cat <working_dir>/src/auth.ts | claude -p 'Review this for security issues' --output-format json")

# Pipe a diff into a follow-up
execute(command="cd <working_dir> && git diff HEAD~1 | claude -p --continue 'Do these changes affect the issues you found?'")
```

### When to Use Multi-Turn

- **Building incrementally**: models → endpoints → tests (each turn builds on prior work)
- **Analysis then action**: read-only review → targeted fix → verify
- **Iterative refinement**: initial implementation → address feedback → polish
- **Complex debugging**: investigate → hypothesize → fix → verify

### Complete Multi-Turn Example

```
# Step 1: Analyze the codebase (read-only, capture session)
execute(command="cd <working_dir> && SESSION=$(claude -p --output-format json --model sonnet --allowedTools 'Read,Grep,Glob' 'Analyze the project structure and identify the tech stack' | jq -r '.session_id') && echo $SESSION > /tmp/session_id")

# Step 2: Implement feature (full access, same context)
execute(command="SESSION=$(cat /tmp/session_id) && cd <working_dir> && claude -p --resume $SESSION --model opus --allowedTools 'Read,Edit,Write,Grep,Glob' 'Now implement the user authentication module based on what you learned'")

# Step 3: Run tests (limited access)
execute(command="SESSION=$(cat /tmp/session_id) && cd <working_dir> && claude -p --resume $SESSION --allowedTools 'Bash(pytest:*),Read' 'Run the tests for the auth module you just created'")

# Step 4: Fix issues if needed
execute(command="SESSION=$(cat /tmp/session_id) && cd <working_dir> && claude -p --resume $SESSION --allowedTools 'Read,Edit,Write' 'Fix any failing tests from the previous run'")
```

## System Prompt Customization

Specialize Claude Code for specific tasks:

```
# Append instructions (keeps built-in capabilities)
execute(command="claude -p --append-system-prompt 'Focus on security best practices. Flag any vulnerabilities.' 'Review the auth module'")

# Replace entire system prompt (full control)
execute(command="claude -p --system-prompt 'You are a database expert. Only modify migration files.' 'Add user roles migration'")
```

## Structured Output

Force response to conform to a JSON schema:

```
execute(command="claude -p --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"files_changed\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"summary\":{\"type\":\"string\"}},\"required\":[\"files_changed\",\"summary\"]}' 'Implement the login feature'")
```

## Controlling Execution

### Limit turns to prevent runaway loops
```
execute(command="claude -p --max-turns 10 'Fix the failing tests'")
```

### Timeout (via execute tool or shell wrapper)
```
execute(command="timeout 300 claude -p --max-turns 15 'Refactor the auth module'")
```

## Prompt Engineering for Delegation

Write prompts that produce reliable results:

1. **State the goal clearly**: "Create a REST API endpoint GET /users that returns a JSON list"
2. **Specify file paths**: "Modify src/routes/users.py and create tests in tests/test_users.py"
3. **Include context**: "The project uses Flask with SQLAlchemy. See app.py for the app factory pattern."
4. **Set constraints**: "Do not modify the database schema. Use the existing User model."
5. **Include error context on retries**: "The previous attempt failed with: ImportError: cannot import name 'db' from 'app'. The db instance is in src/extensions.py."

## When to Use Claude Code vs Direct Tools

| Scenario | Use |
|----------|-----|
| Multi-file feature implementation | Claude Code |
| Complex refactoring | Claude Code |
| Bug fix requiring codebase reasoning | Claude Code |
| Read a single file | `read_file` directly |
| Write/edit a single known file | `write_file`/`edit_file` directly |
| Run a test command | `execute` directly |
| Search for patterns | `grep`/`glob` directly |

## Error Handling

- **Non-zero exit code**: Claude Code failed. Check stderr for details.
- **Empty output with large stdin**: Known limitation. Write input to a temp file and reference with `@filepath` in the prompt.
- **Rate limits**: Add delays between rapid sequential calls if needed.
- **Timeout**: Set appropriate timeouts for complex tasks (5+ minutes for large features).
"""

TEST_RUNNER_SKILL_MD = """\
---
name: test-runner
description: "Execute test suites, interpret results, and manage the verify-retry cycle. Use this skill when: (1) running test commands to verify task completion, (2) interpreting test output to determine pass/fail, (3) extracting error details from failed tests, (4) deciding whether to retry or escalate, (5) running different types of tests (unit, integration, end-to-end). Covers pytest, jest, go test, cargo test, and shell-based verification."
---

# Test Runner

Run test commands to verify that developer work meets requirements. Interpret results and manage retries.

## Running Tests

Use the `execute` tool with the test command from the project task:

```
execute(command="<test_command>")
```

### Common Test Frameworks

```
# Python (pytest)
execute(command="cd <working_dir> && python -m pytest tests/ -v")
execute(command="cd <working_dir> && python -m pytest tests/test_users.py -v")
execute(command="cd <working_dir> && python -m pytest tests/ -v --tb=short")

# Python (unittest)
execute(command="cd <working_dir> && python -m unittest discover -s tests -v")

# Python (import check -- lightweight verification)
execute(command="cd <working_dir> && python -c 'from app import app; print(ok)'")

# JavaScript/TypeScript (jest)
execute(command="cd <working_dir> && npx jest --verbose")
execute(command="cd <working_dir> && npm test")

# Go
execute(command="cd <working_dir> && go test ./... -v")

# Rust
execute(command="cd <working_dir> && cargo test")

# Shell-based verification
execute(command="cd <working_dir> && curl -s http://localhost:8000/health | grep ok")
```

## Interpreting Results

### Exit Codes
- **Exit code 0**: ALL tests passed. Task is verified.
- **Non-zero exit code**: One or more tests failed. Extract details below.

### Extracting Failure Information

From test output, extract these fields for the retry prompt:

1. **Test name**: Which specific test failed
2. **Error type**: AssertionError, TypeError, ImportError, etc.
3. **Expected vs actual**: What was expected and what was received
4. **Traceback**: The file and line where the failure occurred
5. **Stderr**: Any additional error output

Example extraction from pytest output:
```
FAILED tests/test_app.py::test_greet_endpoint - AssertionError:
  assert response.status_code == 200
  actual: 404
  File: tests/test_app.py:15
```

## Retry Strategy

Use escalating context with each retry attempt:

### Attempt 1 (initial)
Delegate to developer with task description only.

### Attempt 2 (first retry)
Include the full error output:
```
Task: Add GET /greet/<name> endpoint
Previous attempt FAILED. Error output:
---
FAILED tests/test_app.py::test_greet_endpoint
AssertionError: assert 404 == 200
The endpoint /greet/World returned 404. Check that the route is registered correctly.
---
Fix the issue and ensure the test passes.
```

### Attempt 3 (second retry)
Include error output PLUS your analysis of the root cause:
```
Task: Add GET /greet/<name> endpoint
FAILED twice. Error: 404 on /greet/World.
Root cause analysis: The route is likely not registered on the Flask app.
Check that:
1. The route decorator uses @app.route('/greet/<name>')
2. The function is defined in a file that gets imported
3. The blueprint (if used) is registered with the app
Previous errors attached below.
```

### After 3 failures
Report the task as BLOCKED with:
- All 3 error outputs
- Your analysis of what went wrong
- Suggestion for manual intervention

## Test Sequencing

Run tests in order of increasing scope:

1. **Syntax/import check**: `python -c "import module"` -- catches basic errors fast
2. **Unit tests**: Test individual functions in isolation
3. **Integration tests**: Test components working together
4. **End-to-end tests**: Test full user workflows

Stop at the first level that fails -- no point running integration tests if imports fail.

## Flaky Test Detection

If a test fails once but passes on immediate re-run without code changes, it may be flaky:

- **Network-dependent tests**: Timeouts, DNS failures
- **Timing-sensitive tests**: Race conditions, sleep-based assertions
- **Order-dependent tests**: State leaking between tests

When suspected, re-run the failing test in isolation:
```
execute(command="cd <working_dir> && python -m pytest tests/test_api.py::test_specific -v --count=3")
```

If it passes 2/3 times, flag it as potentially flaky rather than blocking.

## Timeout Management

Set timeouts proportional to test scope:

- **Import/syntax check**: 30 seconds
- **Unit tests**: 2 minutes
- **Integration tests**: 5 minutes
- **End-to-end / full suite**: 10 minutes

```
execute(command="timeout 120 python -m pytest tests/unit/ -v")
execute(command="timeout 300 python -m pytest tests/integration/ -v")
```
"""

TASK_DECOMPOSITION_SKILL_MD = """\
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
"""

CODE_REVIEW_SKILL_MD = """\
---
name: code-review
description: "Review code produced by the developer subagent before accepting a deliverable. Use this skill when: (1) verifying that implementation matches the task specification, (2) checking for common code quality issues before running tests, (3) deciding whether to accept or send work back for revision, (4) performing a sanity check on generated code structure and correctness."
---

# Code Review

Review developer output to verify quality and correctness before running tests.

## When to Review

Review code AFTER the developer reports completion and BEFORE running tests. This catches obvious issues without wasting a test cycle.

Skip review for trivial tasks (single-file config changes, adding a comment).

## Review Workflow

### Step 1: Read the changed files
```
read_file("<working_dir>/<file_path>")
```
Read every file the developer reported changing.

### Step 2: Check against requirements
For each acceptance criterion in the task:
- Is there code that implements it?
- Does the implementation match the specification?
- Are edge cases handled?

### Step 3: Structural checks

**Imports and dependencies:**
- Are all imports valid? Do the imported modules exist?
- Are there circular import risks?

**Function signatures:**
- Do public functions have sensible parameters?
- Are return types consistent with usage?

**Error handling:**
- Are external calls (DB, network, file I/O) wrapped in try/except?
- Are errors propagated meaningfully (not silently swallowed)?

**Security basics:**
- No hardcoded secrets, passwords, or API keys
- User input is validated/sanitized
- SQL queries use parameterized statements (no string concatenation)
- No eval() or exec() on user input

**Code organization:**
- Files are in the expected locations
- Naming follows project conventions
- No duplicate code that should be shared

### Step 4: Decision

**ACCEPT** if:
- Implementation matches requirements
- No critical issues found
- Proceed to test verification

**SEND BACK** if:
- Missing required functionality
- Security vulnerability present
- Structural issue that tests won't catch (wrong file location, missing exports)
- Code doesn't match the project's patterns

When sending back, be specific:
```
Task needs revision:
1. The /users endpoint is missing -- only /health was implemented
2. Database queries use string formatting instead of parameterized queries
3. The User model file is in the wrong directory (should be in src/models/)
Fix these issues and report back.
```

## What NOT to Review

Do not send work back for:
- Style preferences (the developer follows existing conventions)
- Missing docstrings (unless explicitly required)
- Minor naming choices
- Theoretical edge cases not in requirements

Focus on: correctness, completeness, and security.
"""

DEBUGGING_SKILL_MD = """\
---
name: debugging
description: "Systematically diagnose and resolve issues when tests fail or code does not work as expected. Use this skill when: (1) a test fails and the error is not immediately obvious, (2) multiple retries have failed on the same task, (3) you need to investigate root causes before delegating a fix, (4) distinguishing between code bugs, environment issues, and test issues."
---

# Debugging

Systematic approach to diagnosing failures and constructing effective fix instructions.

## Debugging Workflow

### Step 1: Classify the error

Read the error output and classify it:

| Category | Indicators | Action |
|----------|-----------|--------|
| **Import error** | ImportError, ModuleNotFoundError | Check file paths, package installation, __init__.py |
| **Syntax error** | SyntaxError, IndentationError | Locate exact file:line, fix syntax |
| **Type error** | TypeError, AttributeError | Check function signatures, variable types |
| **Assertion error** | AssertionError, expected != actual | Compare expected behavior with implementation |
| **Runtime error** | RuntimeError, ValueError, KeyError | Trace data flow to find bad input |
| **Connection error** | ConnectionError, TimeoutError | Check service availability, ports, URLs |
| **Permission error** | PermissionError, EACCES | Check file/directory permissions |
| **Missing file** | FileNotFoundError, No such file | Check paths, working directory, creation order |

### Step 2: Locate the source

Use tools to trace the error to its origin:

```
# Find where a function/class is defined
grep(pattern="def function_name", path="<working_dir>")
grep(pattern="class ClassName", path="<working_dir>")

# Read the file at the error location
read_file("<working_dir>/<file>")

# Check if a file exists
ls(path="<working_dir>/expected/path/")

# Search for related usage
grep(pattern="import.*module_name", path="<working_dir>")
```

### Step 3: Form a hypothesis

Based on the error and source code, hypothesize the root cause:

- **Wrong**: "The test is broken" (rare -- assume tests are correct)
- **Better**: "The function returns None instead of a dict because the return statement is inside an unreachable branch"
- **Best**: "Line 42 of users.py has `if user:` but user is a SQLAlchemy query object (always truthy). Should be `if user.first():`"

### Step 4: Construct the fix prompt

Include ALL context the developer needs:

```
TASK: Fix the /users endpoint (retry 2 of 3)

ERROR:
  File: tests/test_users.py:23
  AssertionError: assert [] == [{"id": 1, "name": "Alice"}]
  The GET /users endpoint returns an empty list instead of user data.

ROOT CAUSE:
  In src/routes/users.py:15, the query `User.query.all()` is correct,
  but the result is not serialized -- the endpoint returns the raw
  SQLAlchemy objects, which Flask converts to an empty list.

FIX NEEDED:
  In src/routes/users.py, convert each User object to a dict before
  returning. Use a list comprehension:
  [{"id": u.id, "name": u.name} for u in users]

FILES TO MODIFY:
  - src/routes/users.py (line ~15, the return statement)

DO NOT MODIFY:
  - tests/test_users.py (the test is correct)
  - src/models/user.py (the model is fine)
```

## Common Pitfalls

### Environment vs code issues
If the same code works locally but fails in tests:
- **Missing dependency**: `pip install` may not have run
- **Wrong working directory**: `cd` to the right place before executing
- **Missing env variable**: Check if the code needs `DATABASE_URL`, `SECRET_KEY`, etc.
- **Port conflict**: Another process may hold the port

### Test issues (rare but possible)
If you suspect the test is wrong:
1. Read the test carefully
2. Read the task specification
3. If the test truly contradicts the spec, report it rather than trying to make wrong code pass

### Cascading failures
If multiple tests fail, find the FIRST failure -- later failures are often caused by it. Fix the root cause, not the symptoms.

## Escalation Criteria

After 3 failed retries, report the task as blocked:

```
TASK BLOCKED: Add GET /users endpoint
ATTEMPTS: 3
LAST ERROR: AssertionError -- empty list returned
INVESTIGATION:
  - Read users.py, models.py, test_users.py
  - Hypothesis: serialization issue
  - Developer applied fix but new error appeared (circular import)
  - Second fix introduced a different failure
RECOMMENDATION: Manual review needed. The circular import between
  models.py and routes.py suggests a structural issue that may
  require reorganizing the module layout.
```
"""

ENVIRONMENT_SETUP_SKILL_MD = """\
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
execute(command="cd <working_dir> && node -e 'require(\"express\")'")

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
"""

DEPENDENCY_MANAGEMENT_SKILL_MD = """\
---
name: dependency-management
description: "Manage project dependencies: install packages, resolve conflicts, detect missing modules from import errors, and update lock files. Use this skill when: (1) a task requires new packages, (2) import errors suggest missing dependencies, (3) version conflicts occur, (4) updating or adding entries to requirements.txt, package.json, or similar."
---

# Dependency Management

Manage project packages and resolve dependency issues.

## Detecting Missing Dependencies

When an error indicates a missing package:

| Error Pattern | Meaning | Fix |
|--------------|---------|-----|
| `ModuleNotFoundError: No module named 'flask'` | Python package not installed | `pip install flask` |
| `ImportError: cannot import name 'X' from 'Y'` | Wrong version or submodule | Check version, update package |
| `Cannot find module 'express'` | Node package not installed | `npm install express` |
| `package X is not in GOROOT` | Go module not fetched | `go get X` |

## Installing Packages

### Python
```
# Single package
execute(command="cd <working_dir> && pip install flask")

# From requirements file
execute(command="cd <working_dir> && pip install -r requirements.txt")

# With uv (faster)
execute(command="cd <working_dir> && uv pip install flask")

# Specific version
execute(command="cd <working_dir> && pip install 'flask>=3.0,<4.0'")
```

### Node.js
```
# Production dependency
execute(command="cd <working_dir> && npm install express")

# Dev dependency
execute(command="cd <working_dir> && npm install --save-dev jest")

# From lockfile
execute(command="cd <working_dir> && npm ci")
```

### Go
```
execute(command="cd <working_dir> && go get github.com/gin-gonic/gin")
execute(command="cd <working_dir> && go mod tidy")
```

## Updating Dependency Files

After installing packages, update the manifest:

```
# Python: freeze current state
execute(command="cd <working_dir> && pip freeze > requirements.txt")

# Node: already updated by npm install (package.json + package-lock.json)

# Go: already updated by go get (go.mod + go.sum)
```

## Resolving Version Conflicts

When two packages require incompatible versions:

1. **Identify the conflict** from the error message
2. **Check compatibility**: `pip install 'packageA>=X' 'packageB>=Y'` -- pip will report conflicts
3. **Find a compatible version**: Try the latest versions of both packages
4. **Pin versions**: Use exact pins in requirements.txt if a specific combination works
5. **Last resort**: Check if an alternative package exists without the conflict

## Common Patterns

- **"binary" variants**: Use `psycopg2-binary` instead of `psycopg2` to avoid compiling C extensions
- **Extras**: `pip install 'fastapi[standard]'` includes optional dependencies
- **Dev vs production**: Keep test dependencies separate (`requirements-dev.txt` or `[tool.pytest]` in pyproject.toml)
"""

GIT_WORKFLOW_SKILL_MD = """\
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
"""

PROGRESS_REPORTING_SKILL_MD = """\
---
name: progress-reporting
description: "Track and report project progress: update the todo list, generate status summaries, monitor deadlines, and communicate blockers. Use this skill when: (1) updating task status after completion or failure, (2) generating interim progress reports, (3) assessing whether the project is on track for its deadline, (4) producing the final delivery summary."
---

# Progress Reporting

Track project progress and communicate status effectively.

## Updating the Todo List

Use `write_todos` to keep the task list current:

```
# Mark a task complete
write_todos(todos=[
  {"task": "Initialize project structure", "status": "complete"},
  {"task": "Create database models", "status": "in_progress"},
  {"task": "Implement API endpoints", "status": "pending"},
  {"task": "Write test suite", "status": "pending"}
])
```

### Status Values
- **pending**: Not yet started
- **in_progress**: Currently being worked on
- **complete**: Done and verified
- **blocked**: Failed after max retries

Update status IMMEDIATELY when it changes. Do not batch updates.

## Interim Status Report

After completing a significant milestone (e.g., every 2-3 tasks), produce a brief status update:

```
## Progress Report

### Completed
- [x] Initialize project structure -- PASS
- [x] Create database models -- PASS (User, Post models)

### In Progress
- [ ] Implement API endpoints -- delegated to developer

### Remaining
- [ ] Write test suite
- [ ] Add authentication

### Blockers
None

### Deadline Assessment
3 of 5 tasks complete. On track for <deadline>.
```

## Final Delivery Summary

When all tasks are done (or all possible tasks are done):

```
## Delivery Summary

### Project: <name>
### Status: COMPLETE / PARTIAL (X of Y tasks)

### Delivered
1. <task name> -- PASS
   Files: <list of files created/modified>
2. <task name> -- PASS
   Files: <list of files created/modified>

### Blocked (if any)
1. <task name> -- BLOCKED after 3 retries
   Reason: <root cause summary>
   Recommendation: <what manual intervention is needed>

### Test Results
- Total tasks: X
- Passed: Y
- Blocked: Z

### Deadline
- Deadline: <date from project.yaml>
- Status: Met / At risk / Missed
```

## Deadline Tracking

Read the `deadline` field from project.yaml. After each task:
1. Count remaining tasks
2. Estimate if deadline is achievable
3. If at risk, flag it in the status report

## Communicating Blockers

When a task is blocked:
1. Mark it as blocked in the todo list
2. Include the full error history
3. Suggest what would unblock it
4. Continue with the next independent task if possible

Do not stop the entire project for one blocked task unless other tasks depend on it.
"""

ERROR_ANALYSIS_SKILL_MD = """\
---
name: error-analysis
description: "Parse and analyze error output from test runs and command execution. Use this skill when: (1) extracting structured information from tracebacks, (2) identifying error categories from raw output, (3) mapping errors to specific files and lines, (4) building context-rich retry prompts from error details, (5) analyzing Python, Node.js, Go, or shell command errors."
---

# Error Analysis

Parse error output to extract actionable information for retry prompts.

## Python Error Patterns

### Traceback structure
```
Traceback (most recent call last):
  File "path/to/file.py", line N, in function_name
    code_line_that_failed
ErrorType: description
```

Extract:
- **File**: path/to/file.py
- **Line**: N
- **Function**: function_name
- **Error type**: ErrorType
- **Message**: description

### Common Python errors

| Error | Typical Cause | Fix Direction |
|-------|--------------|---------------|
| `ModuleNotFoundError` | Package not installed or wrong import path | Install package or fix import |
| `ImportError: cannot import name 'X'` | Name doesn't exist in module (typo, wrong version) | Check exports, version |
| `SyntaxError` | Invalid Python syntax | Fix syntax at file:line |
| `IndentationError` | Inconsistent tabs/spaces | Fix indentation |
| `NameError: name 'X' is not defined` | Variable used before definition or out of scope | Define variable or fix scope |
| `TypeError: X() takes N args` | Wrong number of arguments | Fix function call |
| `AttributeError: 'X' has no attribute 'Y'` | Wrong method/property name | Check class/module API |
| `KeyError: 'X'` | Dict key doesn't exist | Check dict structure, use .get() |
| `AssertionError` | Test assertion failed | Compare expected vs actual |
| `FileNotFoundError` | File/directory doesn't exist | Check path, create file/dir |

### Pytest output parsing

```
FAILED tests/test_app.py::TestClass::test_method - ErrorType: message
PASSED tests/test_app.py::test_other
```

Extract from the `FAILED` lines:
- Test file and test name
- Error type and message
- Read the assertion details from the verbose output above the summary

## Node.js Error Patterns

### Stack trace structure
```
ErrorType: message
    at functionName (path/to/file.js:line:col)
    at Object.<anonymous> (path/to/file.js:line:col)
```

Extract from the FIRST `at` line (the actual source):
- **File**: path/to/file.js
- **Line**: line number
- **Function**: functionName

### Common Node.js errors

| Error | Typical Cause | Fix Direction |
|-------|--------------|---------------|
| `ReferenceError: X is not defined` | Missing import or typo | Add import/require |
| `TypeError: X is not a function` | Wrong import or API change | Check exports |
| `SyntaxError: Unexpected token` | Invalid JS/JSON syntax | Fix syntax |
| `Error: Cannot find module 'X'` | Package not installed | `npm install X` |
| `ECONNREFUSED` | Service not running | Start the service first |
| `EADDRINUSE` | Port already in use | Kill existing process or change port |

## Shell Command Errors

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Misuse of shell command |
| 126 | Permission problem (not executable) |
| 127 | Command not found |
| 128+N | Killed by signal N (e.g., 137 = killed by OOM) |
| 139 | Segmentation fault |

## Building Retry Prompts from Errors

Transform raw errors into structured fix instructions:

### Input (raw error)
```
FAILED tests/test_app.py::test_create_user
E       sqlalchemy.exc.OperationalError: no such table: users
```

### Output (structured fix prompt)
```
TASK: Fix the create_user endpoint (retry 1)

ERROR SUMMARY:
  Test: tests/test_app.py::test_create_user
  Error: sqlalchemy.exc.OperationalError: no such table: users
  Category: Database/migration issue

ROOT CAUSE:
  The 'users' table does not exist in the database. This typically means
  db.create_all() was never called, or the model is not imported before
  table creation.

FIX INSTRUCTIONS:
  1. Ensure the User model is imported before db.create_all()
  2. Check that db.create_all() is called during app initialization
  3. If using Flask, verify the model is imported in the app factory

FILES TO CHECK:
  - src/app.py (app factory / initialization)
  - src/models/user.py (User model definition)

DO NOT MODIFY:
  - tests/test_app.py (test is correct)
```

## Multi-Error Triage

When multiple tests fail, triage by finding the root failure:

1. **Sort by dependency**: Import errors before runtime errors before assertion errors
2. **Find the first failure**: Earlier failures often cascade into later ones
3. **Group related failures**: Multiple tests failing on the same module likely share a root cause
4. **Fix one thing at a time**: Address the root failure first, then re-run all tests

Example triage order:
```
1. ModuleNotFoundError in conftest.py  <-- FIX THIS FIRST (affects all tests)
2. ImportError in test_users.py        <-- likely caused by #1
3. AssertionError in test_health.py    <-- independent, fix after #1
```
"""
