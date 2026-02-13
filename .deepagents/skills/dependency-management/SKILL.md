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
