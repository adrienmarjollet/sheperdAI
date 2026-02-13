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
