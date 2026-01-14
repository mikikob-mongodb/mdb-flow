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

### 3.5 Create Task with New Fields

**Purpose:** Test that the Worklog Agent can create tasks with enrichment fields (assignee, due_date, blockers).

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.10 | "Create a task to review security docs, assign to Mike Chen, due next Friday" | create_task with assignee + due_date | Creates task with assignee and due date | □ |
| 3.11 | "Add a high priority task to fix login bug, assign to Sarah, due tomorrow" | create_task with priority + assignee + due_date | Creates with all fields | □ |
| 3.12 | "Create a task for API documentation, assign to Mike, due in 5 days" | create_task with assignee + relative due date | Parses "in 5 days" correctly | □ |
| 3.13 | "Create a task to migrate database, assign to Mike, due in 2 weeks, blocker: waiting on security approval" | create_task with all fields | Creates with assignee, due date, and initial blocker | □ |

**Verification:**
```
□ Debug panel shows: create_task tool call
□ Tool parameters include assignee, due_date, blockers
□ Natural language dates parsed correctly ("next Friday" → ISO date)
□ Relative dates parsed ("in 5 days" → correct future date)
□ Task appears in database with all fields
□ UI shows 👤 assignee badge, 📅 due date, 🚧 blocker indicator
□ Episodic memory records task creation
```

### 3.6 Add Blockers

**Purpose:** Test the Worklog Agent's ability to add and remove blockers from tasks.

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.13 | "Add a blocker to the migration task: waiting on security approval" | search → add_blocker | Adds blocker to task | □ |
| 3.14 | "Block the API task because we need the schema finalized" | search → add_blocker | Adds blocker to task | □ |
| 3.15 | "Remove the blocker from the migration task" | search → remove_blocker | Removes blocker | □ |

**Verification:**
```
□ Debug panel shows: add_blocker or remove_blocker tool call
□ Tool first searches for task by title
□ Blocker text added to blockers array in database
□ UI shows 🚧 indicator on task header
□ Expanded task shows blocker in red error box
□ Activity log records blocker addition/removal
□ Embedding regenerated (includes blocker text for search)
```

### 3.7 Add Stakeholders & Project Updates

**Purpose:** Test adding stakeholders and status updates to projects.

| ID | Query | Expected Flow | Expected Behavior | Pass |
|----|-------|---------------|-------------------|------|
| 3.16 | "Add Mike Chen as a stakeholder to Project Alpha" | search → add_stakeholder | Adds stakeholder to project | □ |
| 3.17 | "Add Sarah to the AgentOps project stakeholders" | search → add_stakeholder | Adds stakeholder | □ |
| 3.18 | "Add a project update to Alpha: completed architecture review" | search → add_project_update | Adds update with timestamp | □ |
| 3.19 | "Update Project Alpha: Phase 1 timeline approved" | search → add_project_update | Adds update to project | □ |

**Verification:**
```
□ Debug panel shows: add_stakeholder or add_project_update tool call
□ Tool searches for project by name first
□ Stakeholder added to stakeholders array
□ Project update includes automatic timestamp + content
□ UI shows stakeholders list: "👥 Stakeholders: Mike Chen, Sarah"
□ UI shows 📝 Recent Updates section with last 2 updates
□ Activity log records changes
□ Embedding regenerated (includes new text for semantic search)
```

### 3.8 Disambiguation Flow

When multiple tasks match:

| ID | Query | Expected Flow | Pass |
|----|-------|---------------|------|
| 3.20 | "Complete the doc task" | Shows numbered options | □ |
| 3.21 | Reply: "2" | Selects second option | □ |
| 3.22 | Reply: "the AgentOps one" | Selects by description | □ |

### 3.9 Cancellation Flow

| ID | Query | Expected Behavior | Pass |
|----|-------|-------------------|------|
| 3.23 | "Complete X" → "no" | Cancels gracefully | □ |
| 3.24 | "Complete X" → "cancel" | Cancels gracefully | □ |
| 3.25 | "Complete X" → "nevermind" | Cancels gracefully | □ |

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
| Create Task (Basic) | 2 | __ | __ |
| Create Task (New Fields) | 4 | __ | __ |
| Add Blockers | 3 | __ | __ |
| Stakeholders & Updates | 4 | __ | __ |
| Disambiguation | 3 | __ | __ |
| Cancellation | 3 | __ | __ |
| **Total** | **26** | __ | __ |

---

*Text Actions Testing Guide v2.0*
