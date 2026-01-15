# Procedural Memory System Design

## Overview

Procedural memory enables the system to learn and automate multi-step workflows based on patterns of user behavior. Unlike episodic memory (what happened) or semantic memory (learned facts), procedural memory encodes **how to do things** - repeatable sequences of actions.

## Core Concept

**Pattern**: A user says "Create a task for X, then start working on it"

**Without Procedural Memory**:
- User: "Create a task for API docs, then start it"
- System: Creates task ✓
- User: "Now start that task" ← requires second interaction

**With Procedural Memory**:
- User: "Create a task for API docs, then start it"
- System: Detects workflow pattern → Creates task → Extracts task_id → Starts task ✓
- Single interaction, automatic chaining

## Architecture

### 1. Workflow Pattern Structure

```python
{
    # Metadata
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Human-readable workflow name",
    "description": "What this workflow does",

    # Trigger Detection
    "trigger_pattern": r"regex pattern to match user input",

    # Workflow Definition
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "tool_name",
                "extract_from_user": ["param1", "param2"],
                "capture_result": "variable_name",
                "description": "What this step does"
            },
            {
                "step": 2,
                "action": "another_tool",
                "use_captured": {"param": "step_1.variable_name"},
                "wait_for_user": True  # Optional: pause for confirmation
            }
        ],
        "success_criteria": "When is this workflow successful?"
    },

    # Examples & Metrics
    "examples": ["Example user input 1", "Example 2"],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime,
    "last_used": None
}
```

### 2. Execution Flow

```
User Input
    ↓
Natural Language Detection (Tier 2)
    ↓
Workflow Pattern Matching (memory/manager.py)
    ↓
Inject matched workflow into system prompt
    ↓
LLM executes steps sequentially
    ↓
Tool calls with data passing between steps
    ↓
Update workflow metrics (times_used, success_rate)
```

### 3. Data Flow Between Steps

**Capturing Results**:
```python
{
    "step": 1,
    "action": "create_task",
    "capture_result": "task_id"  # Store result for later steps
}
```

**Using Captured Data**:
```python
{
    "step": 2,
    "action": "start_task",
    "use_captured": {"task_id": "step_1.task_id"}  # Reference previous result
}
```

**Extracting from User Input**:
```python
{
    "step": 1,
    "action": "create_task",
    "extract_from_user": ["title", "assignee", "priority"]
}
```

## Design Patterns

### Pattern 1: Simple Chaining
**Use Case**: Create → Immediate Action
**Complexity**: Low
**Example**: Create task → Start task

```python
Steps:
1. create_task(params from user) → capture task_id
2. start_task(task_id from step 1)
```

### Pattern 2: Search + Action
**Use Case**: Find → Confirm → Act
**Complexity**: Medium
**Example**: Find task → User selects → Complete it

```python
Steps:
1. search_tasks(query from user) → capture matches
2. confirm_selection(wait for user) → capture selected_id
3. complete_task(selected_id from step 2)
```

### Pattern 3: Batch Operations
**Use Case**: Find Multiple → Act on Each
**Complexity**: Medium-High
**Example**: Find all blocked tasks → Escalate all

```python
Steps:
1. get_tasks(blocked=true) → capture task_list
2. confirm_batch(wait for user) → capture confirmed_ids
3. FOR EACH: update_task(id, priority=high)
4. FOR EACH: add_note(id, "Escalated")
```

### Pattern 4: Conditional Logic
**Use Case**: Check State → Act Differently
**Complexity**: High
**Example**: Check workload → Assign to least busy

```python
Steps:
1. get_tasks(active) → capture all_tasks
2. calculate_workload(all_tasks) → capture stats
3. create_task(assignee=stats.least_busy_person)
```

### Pattern 5: Cross-Entity Workflows
**Use Case**: Multiple Entity Types
**Complexity**: High
**Example**: Create project → Create tasks → Assign team

```python
Steps:
1. create_project(params) → capture project_id
2. create_task(project_id, title="Task 1") → capture task_id_1
3. create_task(project_id, title="Task 2") → capture task_id_2
4. update_task(task_id_1, assignee=person_1)
5. update_task(task_id_2, assignee=person_2)
```

## Workflow Discovery & Learning

### Method 1: Pre-defined Templates (Current)
- Expert-designed workflows stored in seed data
- Covers common patterns proactively
- Example: All workflows in `workflow_patterns.py`

### Method 2: User-Defined Rules (Implemented)
- User teaches: "When I say X, do Y"
- System extracts and stores as semantic memory rule
- Example: "When I say 'done', complete the current task"

### Method 3: Automatic Pattern Detection (Future)
- Analyze episodic memory for repeated sequences
- Identify: User does A → then B → then C frequently
- Propose: "I noticed you often X. Want me to automate this?"

### Method 4: Import from Templates (Future)
- Library of workflow templates
- Users browse and install workflows
- Customize parameters for their team

## Trigger Pattern Design

### Principles
1. **Specific enough** to avoid false positives
2. **General enough** to match natural variations
3. **Use word boundaries** (`\b`) to avoid partial matches
4. **Capture multi-step indicators**: "then", "and then", "after that"

### Examples

**Good Trigger**:
```python
r"create.*task.*(?:then|and)\s+start"
```
Matches:
- ✓ "Create a task for X, then start it"
- ✓ "Create task and start working on it"
- ✗ "Create a task" (no chaining indicator)

**Too Broad**:
```python
r"create.*task"
```
Problem: Matches ALL task creation, including single-step

**Too Narrow**:
```python
r"create a task for .* and then start it"
```
Problem: Misses "Create task X, then start" (missing "a", "for")

### Trigger Priority

When multiple patterns could match:
1. **Most specific** pattern wins
2. **Longer regex** takes precedence
3. **Multi-step** before single-step
4. Check `trigger_pattern` in order of workflow complexity

## User Confirmation Points

### When to Require Confirmation

**Always confirm**:
- Batch operations affecting multiple items
- Destructive actions (delete, complete, archive)
- When ambiguity exists (multiple search results)

**Skip confirmation**:
- Single item creation
- Read-only operations (reports, searches)
- User explicitly said "auto" or "automatically"

### Confirmation UX

```python
{
    "step": 2,
    "action": "confirm_selection",
    "wait_for_user": True,
    "description": "Ask user to select which task if multiple matches"
}
```

LLM should generate:
```
I found 3 tasks matching "API":
1. API Documentation (In Progress) - Project Alpha
2. API Testing (Todo) - Project Beta
3. API Deployment (Blocked) - Project Alpha

Which one did you want to complete? (Reply with the number or name)
```

## Error Handling

### Step Failure Scenarios

**Scenario 1: Tool Call Fails**
```python
Step 2: create_task → Error: "Project not found"
```
Recovery:
- Stop workflow execution
- Report error to user
- Don't execute subsequent steps
- Don't update success metrics

**Scenario 2: Missing Data**
```python
Step 3 needs: task_id from step 1
But step 1 failed to capture it
```
Recovery:
- Detect missing dependency
- Ask user for missing parameter
- Or abort workflow gracefully

**Scenario 3: User Cancels**
```python
Step 2: confirm_selection → User says "cancel"
```
Recovery:
- Stop workflow
- Report: "Workflow cancelled"
- Mark as incomplete (don't count against success_rate)

## Metrics & Learning

### Workflow Metrics

```python
{
    "times_used": 42,           # How many times triggered
    "success_rate": 0.95,       # Successful completions / attempts
    "created_at": datetime,     # When added to system
    "last_used": datetime,      # Most recent execution
    "avg_duration_ms": 2500     # Average execution time (future)
}
```

### Success Criteria

Define what "success" means for each workflow:
- **Simple**: "Tool returns success=true"
- **Complex**: "Final task status changed to expected state"
- **Multi-entity**: "Project and all tasks created successfully"

### Optimization

Based on metrics:
1. **High use, low success** → Improve workflow or split into simpler steps
2. **Low use, high complexity** → Consider removing
3. **High use, high success** → Good candidate for featured workflows
4. **Similar patterns** → Merge into single workflow with parameters

## Extending the System

### Adding a New Workflow

**Step 1**: Design the workflow
```python
# Identify the pattern
User says: "Create project with tasks for research, design, development"

# Break into steps
1. create_project(name from user)
2. create_task(title="Research", project_id)
3. create_task(title="Design", project_id)
4. create_task(title="Development", project_id)
```

**Step 2**: Write the pattern definition
```python
{
    "name": "Create Project with Custom Tasks",
    "trigger_pattern": r"create project.*with tasks for",
    "workflow": {
        "steps": [...] # Define steps
    }
}
```

**Step 3**: Add to seed data
```python
# scripts/demo/seed_demo_data.py
def get_procedural_memory_data():
    return [
        # ... existing workflows
        new_workflow_pattern
    ]
```

**Step 4**: Test the trigger
```bash
User: "Create project called Mobile App with tasks for research, design, development"
System: Should detect pattern and execute workflow
```

**Step 5**: Monitor metrics
- Check `times_used` after deployments
- Monitor `success_rate`
- Refine based on failures

### Creating Workflow Categories

Organize workflows by purpose:

**Task Management**: create, update, complete, reassign
**Project Setup**: initialize, clone, archive
**Team Coordination**: distribute work, handoffs, capacity
**Reporting**: status reports, analytics, summaries
**Maintenance**: cleanup, escalation, stale detection

## Best Practices

### DO:
✓ Use clear, descriptive names
✓ Include multiple example triggers
✓ Define explicit success criteria
✓ Add user confirmations for destructive actions
✓ Test with natural language variations
✓ Update metrics after each use

### DON'T:
✗ Create workflows for single operations (use direct tools)
✗ Use overly complex regex (keep readable)
✗ Skip confirmation on batch operations
✗ Hard-code values (extract from user or use parameters)
✗ Create duplicate workflows (merge similar patterns)

## Future Enhancements

### 1. Workflow Composition
Allow workflows to call other workflows:
```python
{
    "step": 3,
    "action": "execute_workflow",
    "workflow_name": "Escalate Blocked Tasks"
}
```

### 2. Conditional Steps
Enable if/else logic:
```python
{
    "step": 2,
    "condition": "if step_1.task_count > 10",
    "then": "compress_and_summarize",
    "else": "show_all_tasks"
}
```

### 3. Loop Constructs
Iterate over collections:
```python
{
    "step": 3,
    "action": "for_each",
    "collection": "step_1.tasks",
    "do": {
        "action": "update_task",
        "parameters": {"priority": "high"}
    }
}
```

### 4. Parameterized Workflows
User customizes template:
```python
workflow = create_workflow_from_template(
    template="Project Setup",
    params={
        "task_count": 5,
        "default_assignee": "team_lead",
        "sprint_duration": 2
    }
)
```

### 5. Workflow Marketplace
Share and discover workflows:
- Community-contributed patterns
- Import/export workflow definitions
- Vote on usefulness
- Clone and customize

## Conclusion

Procedural memory transforms the system from a reactive tool into a proactive assistant that learns common workflows and automates them. The key is finding the right patterns that are:

1. **Frequent** - Users do them often enough to warrant automation
2. **Multi-step** - Complex enough that automation adds value
3. **Consistent** - Pattern is stable across users/contexts
4. **Detectable** - Natural language trigger is recognizable

Start simple, measure usage, and expand based on real user patterns.
