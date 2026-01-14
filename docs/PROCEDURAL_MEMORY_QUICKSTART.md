# Procedural Memory Quick Start Guide

## What is Procedural Memory?

Procedural memory enables the system to **automate multi-step workflows** by recognizing patterns in user requests.

**Example**: Instead of saying "Create a task" → "Now start that task" (2 interactions), users can say "Create a task and start it" (1 interaction, automatic chaining).

## Documentation Structure

### 📚 [PROCEDURAL_MEMORY_DESIGN.md](./PROCEDURAL_MEMORY_DESIGN.md)
**Read this first** - Core concepts, architecture, and design philosophy
- How the system works
- Pattern matching and execution
- Data flow between steps
- Best practices

### 💡 [PROCEDURAL_MEMORY_PATTERNS.md](./PROCEDURAL_MEMORY_PATTERNS.md)
**Ideation reference** - 32+ workflow pattern ideas organized by category
- Task Management (10 patterns)
- Project Workflows (4 patterns)
- Team/Assignment (4 patterns)
- Reporting/Analytics (4 patterns)
- Maintenance/Cleanup (3 patterns)
- Template/Initialization (4 patterns)
- Conditional/Smart (3 patterns)

### 🛠️ [SAMPLE_WORKFLOW_IMPLEMENTATIONS.md](./SAMPLE_WORKFLOW_IMPLEMENTATIONS.md)
**Implementation guide** - Ready-to-use workflow definitions
- Level 1: Simple Chaining (Reassign Task)
- Level 2: Search + Action (Weekly Report)
- Level 3: Batch Operations (Escalate Blocked, Handoff Tasks)
- Level 4: Conditional Logic (Smart Assignment)
- Level 5: Cross-Entity (Project Setup, Sprint Setup)
- Advanced: Dependency Resolution

## Current Implementation Status

### ✅ Implemented (4 workflows)
1. **Create Task and Start** - `create.*task.*then.*start`
2. **Query and Complete** - `show.*then.*complete`
3. **Batch Create Tasks** - `create.*tasks.*and`
4. **Search Add Note** - `add.*note.*to`

### 🔄 High Priority (Next 5 to implement)
1. **Reassign Task** - Simple, high-value (Level 1)
2. **Weekly Status Report** - Demo-friendly reporting (Level 2)
3. **Create Project with Tasks** - Cross-entity showcase (Level 5)
4. **Escalate Blocked Tasks** - Smart automation (Level 3)
5. **Handoff All Tasks** - Team management (Level 3)

## Quick Pattern Examples

### Simple: Create → Action
```
User: "Create high priority task for API docs, assign to Mike, then start it"

Workflow:
1. create_task(title, priority, assignee) → task_id
2. start_task(task_id)
```

### Search → Confirm → Action
```
User: "Find the deployment task and add a note about production issues"

Workflow:
1. search_tasks("deployment") → matches
2. confirm_selection() → selected_id
3. add_note_to_task(selected_id, note)
```

### Batch Operations
```
User: "Escalate all blocked tasks"

Workflow:
1. get_tasks(blocked=true) → task_list
2. confirm_batch() → confirmed_ids
3. FOR EACH: update_task(id, priority=high)
4. FOR EACH: add_note(id, "Escalated")
```

### Cross-Entity
```
User: "Create a new project called Mobile App with standard tasks"

Workflow:
1. create_project(name) → project_id
2. create_task("Requirements", project_id)
3. create_task("Design", project_id)
4. create_task("Implementation", project_id)
5. create_task("Testing", project_id)
```

## How to Add a New Workflow

### Step 1: Define the Pattern
```python
{
    "name": "Your Workflow Name",
    "description": "What it does",
    "trigger_pattern": r"regex pattern",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "tool_name",
                "extract_from_user": ["param1"],
                "capture_result": "var_name"
            },
            {
                "step": 2,
                "action": "another_tool",
                "use_captured": {"param": "step_1.var_name"}
            }
        ]
    },
    "examples": ["User input example 1", "Example 2"]
}
```

### Step 2: Add to Seed Data
```python
# scripts/demo/seed_demo_data.py
def get_procedural_memory_data():
    return [
        # ... existing workflows
        your_new_workflow
    ]
```

### Step 3: Reseed Database
```bash
python scripts/demo/seed_demo_data.py
```

### Step 4: Test
```
User: [Say something matching your trigger pattern]
System: Should detect and execute workflow
```

## Pattern Categories by Use Case

### For Demo Purposes (Impressive + Clear)
1. **Create Project with Tasks** - Shows cross-entity coordination
2. **Weekly Report** - Shows data aggregation
3. **Smart Task Assignment** - Shows intelligent automation
4. **Sprint Setup** - Shows template instantiation
5. **Escalate Blocked** - Shows batch operations

### For Developer Productivity
1. **Reassign Task** - Common, simple, useful
2. **Handoff All Tasks** - Team transitions
3. **Unblock Task** - Dependency management
4. **Split into Subtasks** - Task breakdown
5. **Bug Triage** - Issue management

### For Team Management
1. **Distribute Work** - Load balancing
2. **Check Team Capacity** - Workload analysis
3. **Escalate Overdue** - Automatic escalation
4. **Handoff Tasks** - Team transitions

### For Reporting
1. **Weekly Status** - Progress tracking
2. **Personal Productivity** - Individual metrics
3. **Blocker Analysis** - Problem identification
4. **Project Health Check** - Project metrics

## Complexity Ladder

### Level 1: Start Here
- **Reassign Task** (1 entity, 2 steps)
- **Create + Start** (already implemented)

### Level 2: Build Confidence
- **Weekly Report** (read-only, multi-source)
- **Search + Action** (already implemented)

### Level 3: Add Power
- **Batch Operations** (affect multiple items)
- **Escalate Blocked** (smart filtering)

### Level 4: Advanced Logic
- **Conditional Assignment** (if/else logic)
- **Workload Balancing** (calculations)

### Level 5: Full Orchestration
- **Project Setup** (cross-entity, 5+ steps)
- **Sprint Initialization** (complex structure)
- **Dependency Resolution** (recursive logic)

## Testing Checklist

When implementing a new workflow:

- [ ] Trigger pattern matches intended queries
- [ ] Trigger pattern doesn't false-positive on unrelated queries
- [ ] All steps execute in correct order
- [ ] Data flows correctly between steps
- [ ] User confirmations appear when needed
- [ ] Success criteria is met
- [ ] Error handling works (missing params, failed tools)
- [ ] Metrics update (times_used, success_rate)
- [ ] Natural language variations work

## Metrics to Track

After deployment, monitor:

**High Value Workflows**:
- `times_used` > 10 per week
- `success_rate` > 0.90
- `avg_duration` < 5 seconds

**Problematic Workflows**:
- `times_used` = 0 (never triggered → remove or fix trigger)
- `success_rate` < 0.70 (often fails → simplify or fix)
- User complaints about false triggers → refine regex

## Common Pitfalls

### ❌ Pattern too broad
```python
r"create task"  # Matches ALL task creation
```
**Fix**: Require multi-step indicator
```python
r"create.*task.*(?:then|and)\s+start"
```

### ❌ Missing data extraction
```python
# Step 2 needs assignee but didn't extract it
{
    "step": 2,
    "action": "update_task",
    "use_captured": {"task_id": "step_1.id"}
    # Missing: extract_from_user: ["assignee"]
}
```

### ❌ No user confirmation on batch
```python
# Dangerous: No confirmation before updating 50 tasks
{
    "step": 2,
    "action": "batch_update_tasks"
    # Missing: wait_for_user: True
}
```

### ❌ Single-step workflow
```python
# Just use direct tool call instead
{
    "workflow": {
        "steps": [
            {"action": "create_task"}  # Only 1 step!
        ]
    }
}
```

## Resources

- **Current Implementation**: `config/workflow_patterns.py`
- **Seed Script**: `scripts/demo/seed_demo_data.py`
- **Memory Manager**: `memory/manager.py` (retrieval methods)
- **Coordinator**: `agents/coordinator.py` (execution logic)

## Next Steps

1. **Review**: Read [PROCEDURAL_MEMORY_DESIGN.md](./PROCEDURAL_MEMORY_DESIGN.md) for architecture
2. **Explore**: Browse [PROCEDURAL_MEMORY_PATTERNS.md](./PROCEDURAL_MEMORY_PATTERNS.md) for ideas
3. **Implement**: Use [SAMPLE_WORKFLOW_IMPLEMENTATIONS.md](./SAMPLE_WORKFLOW_IMPLEMENTATIONS.md) as templates
4. **Test**: Add workflows to seed data and test with real queries
5. **Measure**: Monitor metrics and refine based on usage

## Key Insight

**Good procedural memory = Frequent + Multi-step + Detectable**

If users do it often, it has multiple steps, and we can recognize the pattern, automate it!
