# 03 - Text Actions (LLM)

**Time:** 15 minutes  
**Priority:** P0 - Core functionality

---

## Overview

Actions modify data and typically require the flow:
1. Search → find matching task(s)
2. Confirm → show match, ask for confirmation
3. Execute → perform the action

**Key Point:** Agent should search before acting, never guess.

---

## Test Cases

### 3.1 Complete Task

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.1 | "I finished the debugging doc" | search → confirm → complete | Finds task, asks confirmation, completes | □ |
| 3.2 | "Mark the checkpointer task as done" | search → confirm → complete | Finds task, completes it | □ |
| 3.3 | "Complete the voice agent task" | search → confirm → complete | Finds and completes | □ |

**Verification:**
```
□ Say completion phrase
□ Agent should search for task
□ Agent shows match and asks for confirmation
□ Confirm with "yes" or "that's the one"
□ Verify task status changes to "done"
□ Check debug panel shows tool sequence
□ Check Episodic Memory records the action
```

### 3.2 Start Task

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.4 | "I'm starting work on the checkpointer" | search → confirm → start | Changes status to in_progress | □ |
| 3.5 | "Begin the documentation task" | search → confirm → start | Changes status to in_progress | □ |

### 3.3 Add Note

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.6 | "Add a note to voice agent: WebSocket working" | search → add_note | Adds note to task | □ |
| 3.7 | "Note on debugging task: found the bug" | search → add_note | Adds note to task | □ |

### 3.4 Create Task

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.8 | "Create a task: Review PR #123" | create_task | Creates new task | □ |
| 3.9 | "Add a new task for testing in AgentOps" | create_task(project=AgentOps) | Creates task in project | □ |

### 3.5 Disambiguation Flow

When multiple tasks match:

| ID | Query | Expected Flow | Pass |
|----|-------|---------------|------|
| 3.10 | "Complete the doc task" | Shows numbered options | □ |
| 3.11 | Reply: "2" | Selects second option | □ |
| 3.12 | Reply: "the AgentOps one" | Selects by description | □ |

### 3.6 Cancellation Flow

| ID | Query | Expected Behavior | Pass |
|----|-------|-------------------|------|
| 3.13 | "Complete X" → "no" | Cancels gracefully | □ |
| 3.14 | "Complete X" → "cancel" | Cancels gracefully | □ |
| 3.15 | "Complete X" → "nevermind" | Cancels gracefully | □ |

---

## Action Verification Checklist

```
□ Agent searches before acting (doesn't guess)
□ Agent asks for confirmation on destructive actions
□ Agent handles "no" / "cancel" gracefully
□ Multiple matches show numbered options
□ Can select by number ("2") or description ("the second one")
□ Activity log updated on task after action
□ Episodic Memory records the action
□ Shared Memory passes context between agents (if enabled)
```

---

## Memory Integration Points

Actions should integrate with memory:

| Memory Type | Expected Behavior |
|-------------|-------------------|
| Working Memory | Current project context filters searches |
| Episodic Memory | Action is recorded with timestamp |
| Semantic Memory | Preferences applied (e.g., default project) |
| Procedural Memory | Rules executed (e.g., "when I say done, complete") |
| Shared Memory | Retrieval → Worklog handoff visible |

See [06-memory-engineering.md](06-memory-engineering.md) for detailed memory tests.

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Complete Task | 3 | __ | __ |
| Start Task | 2 | __ | __ |
| Add Note | 2 | __ | __ |
| Create Task | 2 | __ | __ |
| Disambiguation | 3 | __ | __ |
| Cancellation | 3 | __ | __ |
| **Total** | **15** | __ | __ |

---

*Text Actions Testing Guide v2.0*
