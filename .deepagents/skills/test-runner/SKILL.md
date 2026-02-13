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
