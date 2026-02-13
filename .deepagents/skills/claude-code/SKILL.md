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
execute(command="claude -p --output-format json --json-schema '{"type":"object","properties":{"files_changed":{"type":"array","items":{"type":"string"}},"summary":{"type":"string"}},"required":["files_changed","summary"]}' 'Implement the login feature'")
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
