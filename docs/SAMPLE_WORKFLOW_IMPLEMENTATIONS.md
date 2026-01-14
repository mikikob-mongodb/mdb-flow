# Sample Procedural Memory Workflow Implementations

These are ready-to-implement workflow patterns organized by complexity level.

## Level 1: Simple Chaining

### Reassign Task Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Reassign Task Workflow",
    "description": "Find a task and reassign it to a different person",
    "trigger_pattern": r"reassign.*task|change.*assignee.*to|give.*task to",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "search_tasks",
                "extract_from_user": ["task_reference"],
                "capture_result": "tasks"
            },
            {
                "step": 2,
                "action": "confirm_selection",
                "description": "Confirm which task if multiple matches",
                "wait_for_user": True
            },
            {
                "step": 3,
                "action": "update_task",
                "use_captured": {"task_id": "step_2.selected_task_id"},
                "extract_from_user": ["assignee"],
                "description": "Update the assignee field"
            }
        ],
        "success_criteria": "Task assignee updated successfully"
    },
    "examples": [
        "Reassign the API documentation task to Mike",
        "Give the deployment task to Sarah",
        "Change assignee of testing task to Alex"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Level 2: Search + Action

### Weekly Status Report Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Weekly Status Report Workflow",
    "description": "Generate a weekly status report showing completed and in-progress work",
    "trigger_pattern": r"weekly report|what did (?:we|i) do this week|week(?:ly)? (?:status|summary)",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "get_tasks_by_time",
                "parameters": {
                    "timeframe": "this_week",
                    "activity_type": "completed"
                },
                "capture_result": "completed_tasks"
            },
            {
                "step": 2,
                "action": "get_tasks",
                "parameters": {
                    "status": "in_progress"
                },
                "capture_result": "in_progress_tasks"
            },
            {
                "step": 3,
                "action": "get_tasks",
                "parameters": {
                    "blocked": True
                },
                "capture_result": "blocked_tasks"
            },
            {
                "step": 4,
                "action": "format_report",
                "description": "Format results into structured report",
                "use_captured": {
                    "completed": "step_1.completed_tasks",
                    "in_progress": "step_2.in_progress_tasks",
                    "blocked": "step_3.blocked_tasks"
                }
            }
        ],
        "success_criteria": "Report includes completed, in-progress, and blocked counts"
    },
    "examples": [
        "Give me a weekly status report",
        "What did we do this week?",
        "Show me the week in review"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Level 3: Batch Operations

### Escalate Blocked Tasks Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Escalate Blocked Tasks Workflow",
    "description": "Find all blocked tasks and escalate priority with notes",
    "trigger_pattern": r"escalate.*blocked|priority.*blocked|flag blocked tasks",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "get_tasks",
                "parameters": {
                    "blocked": True,
                    "status": "in_progress"
                },
                "capture_result": "blocked_tasks"
            },
            {
                "step": 2,
                "action": "confirm_batch_action",
                "description": "Show list and confirm escalation",
                "wait_for_user": True,
                "use_captured": {"tasks": "step_1.blocked_tasks"}
            },
            {
                "step": 3,
                "action": "batch_update_tasks",
                "description": "Update priority for all blocked tasks",
                "use_captured": {"task_ids": "step_2.confirmed_task_ids"},
                "parameters": {
                    "priority": "high"
                }
            },
            {
                "step": 4,
                "action": "batch_add_notes",
                "description": "Add escalation note to all tasks",
                "use_captured": {"task_ids": "step_2.confirmed_task_ids"},
                "parameters": {
                    "note": "Escalated due to blockers"
                }
            }
        ],
        "success_criteria": "All blocked tasks marked high priority with notes"
    },
    "examples": [
        "Escalate all blocked tasks",
        "Flag blocked tasks as high priority",
        "Escalate blocked work for Project Alpha"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

### Handoff All Tasks Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Handoff All Tasks Workflow",
    "description": "Transfer all tasks from one person to another with handoff notes",
    "trigger_pattern": r"(?:reassign|transfer|handoff) all.*tasks? from|give all.*tasks? to",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "get_tasks",
                "extract_from_user": ["from_assignee"],
                "capture_result": "tasks_to_transfer"
            },
            {
                "step": 2,
                "action": "confirm_batch_action",
                "description": "Confirm transfer of all tasks",
                "wait_for_user": True,
                "use_captured": {"tasks": "step_1.tasks_to_transfer"}
            },
            {
                "step": 3,
                "action": "batch_update_tasks",
                "use_captured": {"task_ids": "step_2.confirmed_task_ids"},
                "extract_from_user": ["to_assignee"],
                "description": "Update assignee for all tasks"
            },
            {
                "step": 4,
                "action": "batch_add_notes",
                "use_captured": {
                    "task_ids": "step_2.confirmed_task_ids",
                    "from_person": "step_1.from_assignee",
                    "to_person": "step_3.to_assignee"
                },
                "parameters": {
                    "note": "Handed off from {from_person} to {to_person}"
                }
            }
        ],
        "success_criteria": "All tasks reassigned with handoff notes"
    },
    "examples": [
        "Reassign all of Mike's tasks to Sarah",
        "Transfer all tasks from Alex to the team lead",
        "Handoff all my tasks to Mike"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Level 4: Conditional Logic

### Smart Task Assignment Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Smart Task Assignment Workflow",
    "description": "Create task and auto-assign to team member with lowest workload",
    "trigger_pattern": r"create.*task.*auto.?assign|assign.*smartly|assign to (?:least busy|whoever has capacity)",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "get_tasks",
                "parameters": {
                    "status": ["in_progress", "todo"]
                },
                "capture_result": "all_active_tasks"
            },
            {
                "step": 2,
                "action": "calculate_workload",
                "description": "Count tasks per assignee to find least busy",
                "use_captured": {"tasks": "step_1.all_active_tasks"},
                "capture_result": "workload_stats"
            },
            {
                "step": 3,
                "action": "create_task",
                "extract_from_user": ["title", "project_name", "priority", "due_date"],
                "use_captured": {
                    "assignee": "step_2.least_busy_person"
                },
                "capture_result": "task_id"
            },
            {
                "step": 4,
                "action": "add_note_to_task",
                "use_captured": {
                    "task_id": "step_3.task_id",
                    "assignee": "step_2.least_busy_person",
                    "workload": "step_2.workload_stats"
                },
                "parameters": {
                    "note": "Auto-assigned to {assignee} (current workload: {workload} tasks)"
                }
            }
        ],
        "success_criteria": "Task created and assigned to person with lowest workload"
    },
    "examples": [
        "Create high priority bug fix task and auto-assign to whoever has capacity",
        "Add task for code review, assign smartly",
        "Create task and assign to least busy team member"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Level 5: Cross-Entity Workflows

### Create Project with Standard Tasks Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Create Project with Standard Tasks Workflow",
    "description": "Initialize new project with standard task structure",
    "trigger_pattern": r"create (?:new )?project.*with (?:standard )?tasks|initialize (?:new )?project|new project setup",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "create_project",
                "extract_from_user": ["name", "description"],
                "capture_result": "project_id"
            },
            {
                "step": 2,
                "action": "create_task",
                "parameters": {
                    "title": "Requirements Gathering",
                    "priority": "high"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "task_id_1"
            },
            {
                "step": 3,
                "action": "create_task",
                "parameters": {
                    "title": "Design & Planning",
                    "priority": "high"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "task_id_2"
            },
            {
                "step": 4,
                "action": "create_task",
                "parameters": {
                    "title": "Implementation",
                    "priority": "medium"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "task_id_3"
            },
            {
                "step": 5,
                "action": "create_task",
                "parameters": {
                    "title": "Testing & QA",
                    "priority": "medium"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "task_id_4"
            },
            {
                "step": 6,
                "action": "create_task",
                "parameters": {
                    "title": "Deployment & Launch",
                    "priority": "low"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "task_id_5"
            }
        ],
        "success_criteria": "Project created with 5 standard tasks"
    },
    "examples": [
        "Create a new project called Website Redesign with standard tasks",
        "Initialize project for Mobile App with default structure",
        "Set up new project API Integration with tasks"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

### Sprint Setup Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Sprint Setup Workflow",
    "description": "Initialize a new sprint with standard structure and ceremonies",
    "trigger_pattern": r"(?:create|setup|initialize) (?:new )?sprint|new sprint|start sprint",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "create_project",
                "extract_from_user": ["sprint_name", "start_date", "duration_weeks"],
                "parameters": {
                    "status": "active"
                },
                "capture_result": "project_id"
            },
            {
                "step": 2,
                "action": "create_task",
                "parameters": {
                    "title": "Sprint Planning",
                    "priority": "high"
                },
                "use_captured": {
                    "project_id": "step_1.project_id",
                    "due_date": "step_1.start_date"
                },
                "capture_result": "planning_task_id"
            },
            {
                "step": 3,
                "action": "create_task",
                "parameters": {
                    "title": "Daily Standups",
                    "priority": "medium",
                    "context": "Daily sync meetings throughout sprint"
                },
                "use_captured": {"project_id": "step_1.project_id"},
                "capture_result": "standup_task_id"
            },
            {
                "step": 4,
                "action": "create_task",
                "parameters": {
                    "title": "Sprint Review",
                    "priority": "high"
                },
                "use_captured": {
                    "project_id": "step_1.project_id",
                    "due_date": "step_1.end_date"
                },
                "capture_result": "review_task_id"
            },
            {
                "step": 5,
                "action": "create_task",
                "parameters": {
                    "title": "Sprint Retrospective",
                    "priority": "high"
                },
                "use_captured": {
                    "project_id": "step_1.project_id",
                    "due_date": "step_1.end_date"
                },
                "capture_result": "retro_task_id"
            }
        ],
        "success_criteria": "Sprint project created with planning, standups, review, and retro tasks"
    },
    "examples": [
        "Set up a new 2-week sprint starting Monday",
        "Initialize Sprint 12 starting January 15th",
        "Create new sprint for Q1"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Advanced: Dependency Chain Resolution

### Dependency Resolution Workflow
```python
{
    "memory_type": "procedural",
    "rule_type": "workflow",
    "name": "Dependency Resolution Workflow",
    "description": "Resolve all blocking dependencies for a task",
    "trigger_pattern": r"resolve (?:dependencies|blockers) for|unblock.*by completing|clear blockers",
    "workflow": {
        "steps": [
            {
                "step": 1,
                "action": "search_tasks",
                "extract_from_user": ["task_reference"],
                "capture_result": "target_task"
            },
            {
                "step": 2,
                "action": "get_task_details",
                "use_captured": {"task_id": "step_1.target_task.id"},
                "description": "Get full task details including blockers",
                "capture_result": "task_details"
            },
            {
                "step": 3,
                "action": "search_blocker_tasks",
                "use_captured": {"blockers": "step_2.task_details.blockers"},
                "description": "Find task objects for each blocker",
                "capture_result": "blocker_tasks"
            },
            {
                "step": 4,
                "action": "confirm_batch_action",
                "description": "Show blocker tasks and confirm completion",
                "wait_for_user": True,
                "use_captured": {"tasks": "step_3.blocker_tasks"}
            },
            {
                "step": 5,
                "action": "batch_complete_tasks",
                "use_captured": {"task_ids": "step_4.confirmed_task_ids"},
                "description": "Complete all blocking tasks"
            },
            {
                "step": 6,
                "action": "update_task",
                "use_captured": {"task_id": "step_1.target_task.id"},
                "parameters": {
                    "blockers": []
                },
                "description": "Clear blockers from target task"
            },
            {
                "step": 7,
                "action": "add_note_to_task",
                "use_captured": {
                    "task_id": "step_1.target_task.id",
                    "completed_count": "step_5.completed_count"
                },
                "parameters": {
                    "note": "Resolved {completed_count} blocking dependencies"
                }
            }
        ],
        "success_criteria": "All blockers completed and removed from task"
    },
    "examples": [
        "Resolve all dependencies blocking the deployment task",
        "Clear blockers for API integration by completing them",
        "Unblock the release task"
    ],
    "times_used": 0,
    "success_rate": 1.0,
    "created_at": datetime.utcnow(),
    "last_used": None
}
```

## Implementation Notes

### Required Tool Enhancements

Some workflows require new tool actions:
- `batch_update_tasks` - Update multiple tasks at once
- `batch_add_notes` - Add notes to multiple tasks
- `batch_complete_tasks` - Complete multiple tasks
- `calculate_workload` - Analyze task distribution
- `format_report` - Structure data into report format
- `get_task_details` - Get full task object with all fields
- `search_blocker_tasks` - Find tasks matching blocker references

### Workflow Execution Engine

The coordinator needs to:
1. **Pattern matching** - Detect workflow triggers in user input
2. **Context extraction** - Pull parameters from natural language
3. **Sequential execution** - Run steps in order, passing data between steps
4. **User confirmations** - Pause for user input when `wait_for_user: True`
5. **Error recovery** - Handle failures at any step
6. **Progress tracking** - Update `times_used` and `success_rate` metrics

### Demo-Friendly Workflows

Best for live demonstrations:
1. **Create Project with Standard Tasks** - Shows cross-entity coordination
2. **Weekly Status Report** - Shows data aggregation
3. **Reassign Task** - Simple, clear, useful
4. **Escalate Blocked Tasks** - Shows smart automation
5. **Sprint Setup** - Shows template instantiation
