# Procedural Memory Workflow Patterns

This document catalogs potential procedural memory patterns for multi-step workflows. These patterns automate complex, repetitive task sequences.

## Current Implemented Patterns

1. **Create Task and Start Workflow** - Create task → Start task
2. **Query and Complete Workflow** - Search → Confirm → Complete
3. **Batch Create Tasks Workflow** - Create multiple tasks sequentially
4. **Search Add Note Workflow** - Search → Confirm → Add note

---

## Category: Task Management Workflows

### 5. Reassign Task Workflow
**Trigger**: `reassign.*task|change.*assignee.*to`
**Pattern**: Find task → Confirm → Update assignee
**Example**: "Reassign the migration task to Mike"
```
Steps:
1. search_tasks(query from user)
2. confirm_selection (if multiple matches)
3. update_task(task_id, assignee=new_assignee)
```

### 6. Escalate Blocked Task Workflow
**Trigger**: `escalate.*blocked|priority.*blocked`
**Pattern**: Find blocked task → Update priority to high → Add escalation note
**Example**: "Escalate all blocked tasks for Project Alpha"
```
Steps:
1. get_tasks(status=in_progress, project=from_user)
2. filter for tasks with blockers
3. For each: update_task(priority=high)
4. For each: add_note_to_task("Escalated due to blockers")
```

### 7. Create Task with Dependencies Workflow
**Trigger**: `create.*task.*depends on|create.*task.*blocked by`
**Pattern**: Create task → Set blockers
**Example**: "Create a task for deployment, blocked by testing task"
```
Steps:
1. search_tasks(query=blocker_reference) - find blocking task
2. create_task(title, project, blockers=[blocker_task_id])
```

### 8. Bulk Status Update Workflow
**Trigger**: `mark all.*as|complete all.*tasks`
**Pattern**: Query tasks → Confirm → Update status for all
**Example**: "Mark all testing tasks as done"
```
Steps:
1. search_tasks(query)
2. Show list, confirm
3. For each: complete_task(task_id)
```

### 9. Split Task into Subtasks Workflow
**Trigger**: `break down.*task|create subtasks for`
**Pattern**: Find parent task → Create multiple related tasks → Link via notes
**Example**: "Break down the API implementation task into 3 subtasks"
```
Steps:
1. search_tasks(parent_reference)
2. confirm_selection
3. create_task(title=subtask_1, project, context="Parent: {parent_title}")
4. create_task(title=subtask_2, project, context="Parent: {parent_title}")
5. create_task(title=subtask_3, project, context="Parent: {parent_title}")
6. add_note_to_task(parent_id, "Split into 3 subtasks: {ids}")
```

### 10. Unblock Task Workflow
**Trigger**: `unblock.*task|remove blocker from`
**Pattern**: Find task → Update to remove blockers → Add resolution note
**Example**: "Unblock the deployment task"
```
Steps:
1. search_tasks(query)
2. confirm_selection
3. update_task(task_id, blockers=[])
4. add_note_to_task(task_id, "Blockers resolved")
```

---

## Category: Project Workflows

### 11. Create Project with Standard Tasks Workflow
**Trigger**: `create project.*with tasks|new project.*standard|initialize project`
**Pattern**: Create project → Create standard task set → Assign team
**Example**: "Create a new project called Website Redesign with standard tasks"
```
Steps:
1. create_project(name, description)
2. create_task(title="Requirements", project_id, priority=high)
3. create_task(title="Design", project_id, priority=medium)
4. create_task(title="Implementation", project_id, priority=medium)
5. create_task(title="Testing", project_id, priority=medium)
6. create_task(title="Deployment", project_id, priority=low)
```

### 12. Archive Completed Project Workflow
**Trigger**: `archive.*project|close.*project|mark project.*done`
**Pattern**: Find project → Mark all tasks done → Update project status
**Example**: "Archive the Q4 Marketing project"
```
Steps:
1. get_projects(name=from_user)
2. confirm_selection
3. get_tasks(project_id)
4. For each incomplete task: complete_task(task_id)
5. update_project(project_id, status=completed)
```

### 13. Clone Project Structure Workflow
**Trigger**: `clone project|copy project structure|duplicate project`
**Pattern**: Find source project → Create new project → Copy task structure
**Example**: "Clone the Q4 Sprint project structure for Q1"
```
Steps:
1. get_projects(name=source_project)
2. confirm_selection
3. get_tasks(project_id=source_id)
4. create_project(name=new_name, description)
5. For each task: create_task(title, new_project_id, priority, assignee=None)
```

### 14. Project Health Check Workflow
**Trigger**: `project health|check project status|project report`
**Pattern**: Get project → Get tasks → Analyze metrics → Generate report
**Example**: "Give me a health check on Project Alpha"
```
Steps:
1. get_projects(name=from_user)
2. get_tasks(project_id)
3. Calculate: overdue_count, blocked_count, completion_rate
4. Return formatted report with recommendations
```

---

## Category: Team/Assignment Workflows

### 15. Distribute Work Round-Robin Workflow
**Trigger**: `distribute.*tasks|assign tasks to team|balance workload`
**Pattern**: Get unassigned tasks → Assign to team members in rotation
**Example**: "Distribute all unassigned tasks to Sarah, Mike, and Alex"
```
Steps:
1. get_tasks(status=todo, assignee=None)
2. Extract team members from query
3. For each task: update_task(task_id, assignee=next_in_rotation)
```

### 16. Handoff All Tasks Workflow
**Trigger**: `reassign all.*tasks from|handoff.*tasks|transfer work from`
**Pattern**: Get all tasks for person A → Reassign to person B → Add handoff notes
**Example**: "Reassign all of Mike's tasks to Sarah"
```
Steps:
1. get_tasks(assignee=from_person)
2. confirm (show list)
3. For each: update_task(task_id, assignee=to_person)
4. For each: add_note_to_task(task_id, "Handed off from {from} to {to}")
```

### 17. Check Team Capacity Workflow
**Trigger**: `team capacity|who has bandwidth|workload report`
**Pattern**: Get tasks by assignee → Calculate metrics → Suggest rebalancing
**Example**: "Show me team capacity and who needs more work"
```
Steps:
1. get_tasks(status=in_progress OR todo)
2. Group by assignee
3. Calculate: task_count, high_priority_count per person
4. Return capacity report with suggestions
```

### 18. Escalate Overdue to Manager Workflow
**Trigger**: `escalate overdue|notify manager about overdue`
**Pattern**: Get overdue tasks → Update assignee to manager → Add escalation note
**Example**: "Escalate all overdue tasks to the project manager"
```
Steps:
1. get_tasks(overdue=true)
2. confirm
3. For each: update_task(assignee=manager_name, priority=high)
4. For each: add_note_to_task("Escalated - overdue")
```

---

## Category: Reporting/Analytics Workflows

### 19. Weekly Status Report Workflow
**Trigger**: `weekly report|what did we do this week|week in review`
**Pattern**: Get completed + in-progress tasks from this week → Format report
**Example**: "Give me a weekly status report"
```
Steps:
1. get_tasks_by_time(timeframe=this_week, activity_type=completed)
2. get_tasks_by_time(timeframe=this_week, activity_type=started)
3. get_tasks(status=in_progress)
4. Format report: "✓ Completed: X tasks, ◐ In Progress: Y tasks"
```

### 20. Personal Productivity Report Workflow
**Trigger**: `my productivity|what did i complete|my stats`
**Pattern**: Get user's tasks by status → Calculate completion rate → Show insights
**Example**: "Show me my productivity stats for this week"
```
Steps:
1. get_tasks_by_time(assignee=user, timeframe=this_week, activity_type=completed)
2. get_tasks(assignee=user, status=in_progress)
3. get_tasks(assignee=user, status=todo)
4. Calculate: completion_rate, avg_time_to_complete
5. Return formatted report
```

### 21. Blocker Analysis Workflow
**Trigger**: `blocker report|what's blocking us|analyze blockers`
**Pattern**: Get all blocked tasks → Group by blocker → Identify patterns
**Example**: "Analyze what's blocking our team"
```
Steps:
1. get_tasks(blocked=true)
2. Extract blocker text from all tasks
3. Group by common blocker patterns
4. Return report: "Top blockers: {list}, Affected tasks: {count}"
```

### 22. Sprint Velocity Report Workflow
**Trigger**: `sprint velocity|completion rate|how fast are we`
**Pattern**: Get completed tasks last 2 weeks → Calculate daily average → Project completion
**Example**: "What's our sprint velocity?"
```
Steps:
1. get_tasks_by_time(timeframe=last_two_weeks, activity_type=completed)
2. Calculate: tasks_per_day average
3. get_tasks(status=todo)
4. Project: "At current velocity, {X} days to complete backlog"
```

---

## Category: Maintenance/Cleanup Workflows

### 23. Clean Up Stale Tasks Workflow
**Trigger**: `clean up stale|find old tasks|archive inactive`
**Pattern**: Find tasks in-progress > 30 days → Confirm → Add review note
**Example**: "Clean up tasks that have been in progress for over a month"
```
Steps:
1. get_tasks(status=in_progress)
2. Filter: started_at > 30 days ago
3. confirm (show list)
4. For each: add_note_to_task("Flagged for review - stale")
```

### 24. Update Due Dates in Bulk Workflow
**Trigger**: `extend deadline|push due dates|delay.*tasks`
**Pattern**: Find tasks with due dates → Update by offset → Add note
**Example**: "Extend all tasks due this week by 7 days"
```
Steps:
1. get_tasks(due=this_week)
2. confirm
3. For each: update_task(due_date=current + 7 days)
4. For each: add_note_to_task("Deadline extended by 7 days")
```

### 25. Auto-Archive Completed Tasks Workflow
**Trigger**: `archive completed|clean up done tasks`
**Pattern**: Find tasks completed > 30 days → Confirm → Mark archived
**Example**: "Archive all tasks completed over 30 days ago"
```
Steps:
1. get_tasks(status=done)
2. Filter: completed_at > 30 days ago
3. confirm
4. For each: update_task(archived=true)
```

---

## Category: Template/Initialization Workflows

### 26. New Sprint Setup Workflow
**Trigger**: `new sprint|initialize sprint|create sprint`
**Pattern**: Create sprint project → Create task categories → Set dates
**Example**: "Set up a new 2-week sprint starting Monday"
```
Steps:
1. create_project(name="Sprint {date}", status=active)
2. create_task(title="Sprint Planning", project_id, priority=high, due=monday)
3. create_task(title="Daily Standups", project_id)
4. create_task(title="Sprint Review", project_id, due=friday_week2)
5. create_task(title="Sprint Retro", project_id, due=friday_week2)
```

### 27. Bug Triage Workflow
**Trigger**: `create bug|new bug|report bug`
**Pattern**: Create bug task → Set priority high → Assign to triage → Add to bugs project
**Example**: "Report a bug: login page doesn't load"
```
Steps:
1. get_projects(name="Bugs") OR create_project(name="Bugs")
2. create_task(title=bug_description, project_id, priority=high, assignee=triage_lead)
3. add_note_to_task(task_id, "Needs triage and investigation")
```

### 28. Onboarding Task Setup Workflow
**Trigger**: `onboard new member|new team member tasks`
**Pattern**: Create onboarding project → Create standard onboarding tasks → Assign to manager
**Example**: "Set up onboarding tasks for new engineer Alex"
```
Steps:
1. create_project(name="Onboarding - {name}")
2. create_task(title="Complete orientation", project_id, assignee=name, due=day_1)
3. create_task(title="Set up development environment", project_id, assignee=name, due=day_2)
4. create_task(title="Review codebase", project_id, assignee=name, due=week_1)
5. create_task(title="First PR review", project_id, assignee=manager, due=week_2)
```

### 29. Release Checklist Workflow
**Trigger**: `prepare release|release checklist|deploy.*checklist`
**Pattern**: Create release project → Create release tasks in order → Set dependencies
**Example**: "Set up release checklist for v2.0"
```
Steps:
1. create_project(name="Release v{version}")
2. create_task(title="Code freeze", project_id, priority=high)
3. create_task(title="Run test suite", project_id, priority=high)
4. create_task(title="Security audit", project_id, priority=high)
5. create_task(title="Deploy to staging", project_id, blockers=["testing"])
6. create_task(title="Deploy to production", project_id, blockers=["staging"])
```

---

## Category: Conditional/Smart Workflows

### 30. Smart Task Assignment Based on Workload
**Trigger**: `assign task smartly|auto-assign|assign to least busy`
**Pattern**: Create task → Check team workload → Assign to person with least tasks
**Example**: "Create a high priority task for bug fix and assign to whoever has capacity"
```
Steps:
1. get_tasks(status=in_progress OR todo)
2. Group by assignee, count tasks
3. Identify person with lowest task count
4. create_task(title, project, assignee=lowest_workload_person)
```

### 31. Conditional Priority Escalation Workflow
**Trigger**: `check priorities|escalate if needed`
**Pattern**: Get tasks → Check age + status → Auto-escalate old in-progress tasks
**Example**: "Escalate any tasks that have been in progress for over 2 weeks"
```
Steps:
1. get_tasks(status=in_progress)
2. Filter: started_at > 14 days ago AND priority != high
3. For each: update_task(priority=high)
4. For each: add_note_to_task("Auto-escalated - in progress > 2 weeks")
```

### 32. Dependency Chain Resolution Workflow
**Trigger**: `resolve dependencies|unblock chain|clear blockers`
**Pattern**: Find task → Check blockers → Complete blockers → Update original task
**Example**: "Resolve all dependencies blocking the deployment task"
```
Steps:
1. search_tasks(main_task_reference)
2. get_task_details(task_id) - retrieve blockers
3. For each blocker: search_tasks(blocker_name)
4. For each blocker_task: confirm_selection, complete_task(blocker_task_id)
5. update_task(main_task_id, blockers=[])
```

---

## Pattern Design Guidelines

When designing procedural memory patterns:

1. **Multi-step requirement**: Must have 2+ distinct operations
2. **Repeatable**: Pattern should apply to multiple scenarios
3. **Clear trigger**: Natural language pattern that users would actually say
4. **Capture dependencies**: Each step should capture results for next steps
5. **Confirmation points**: Include user confirmation for destructive operations
6. **Error handling**: Consider what happens if intermediate steps fail

## Pattern Complexity Levels

- **Level 1**: Simple chaining (Create → Update)
- **Level 2**: Search + Action (Find → Confirm → Act)
- **Level 3**: Batch operations (Find multiple → Act on each)
- **Level 4**: Conditional logic (Check state → Act differently)
- **Level 5**: Cross-entity workflows (Project + Tasks + Assignments)

## Implementation Priority

Recommended implementation order:
1. ✅ Create + Start (implemented)
2. ✅ Search + Complete (implemented)
3. ✅ Batch Create (implemented)
4. 🔄 Reassign Task (high value, simple)
5. 🔄 Create Project with Tasks (demo-friendly)
6. 🔄 Weekly Report (reporting showcase)
7. 🔄 Distribute Work (team management)
8. 🔄 Escalate Blocked (smart automation)
