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
