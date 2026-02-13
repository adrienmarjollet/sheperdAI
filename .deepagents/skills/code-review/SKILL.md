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
