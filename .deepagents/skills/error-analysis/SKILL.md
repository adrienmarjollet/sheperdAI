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
