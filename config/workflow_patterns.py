"""Procedural memory patterns for multi-step workflows."""

from datetime import datetime, timedelta

# Multi-step workflow patterns stored as procedural memory
WORKFLOW_PATTERNS = [
    {
        "memory_type": "procedural",
        "rule_type": "workflow",
        "name": "Create Task and Start Workflow",
        "description": "Pattern for creating a task and immediately starting work on it",
        "trigger_pattern": r"create.*task.*(?:then|and)\s+start",
        "workflow": {
            "steps": [
                {
                    "step": 1,
                    "action": "create_task",
                    "extract_from_user": ["title", "project_name", "priority", "assignee", "due_date"],
                    "capture_result": "task_id"
                },
                {
                    "step": 2,
                    "action": "start_task",
                    "use_captured": {"task_id": "step_1.task_id"},
                    "description": "Mark the newly created task as in_progress"
                }
            ],
            "success_criteria": "Both tools return success=true"
        },
        "examples": [
            "Create a task for API docs, assign to Sarah, due tomorrow, then start it",
            "Create high priority task for testing and start working on it"
        ],
        "times_used": 0,
        "success_rate": 1.0,
        "created_at": datetime.utcnow(),
        "last_used": None
    },
    {
        "memory_type": "procedural",
        "rule_type": "workflow",
        "name": "Query and Complete Workflow",
        "description": "Pattern for finding tasks and completing the first/selected one",
        "trigger_pattern": r"(show|what\'s|list).*(?:then|and)\s+(complete|mark.*done|finish)",
        "workflow": {
            "steps": [
                {
                    "step": 1,
                    "action": "search_tasks",
                    "extract_from_user": ["query"],
                    "capture_result": "tasks"
                },
                {
                    "step": 2,
                    "action": "confirm_selection",
                    "description": "Ask user to confirm which task to complete",
                    "wait_for_user": True
                },
                {
                    "step": 3,
                    "action": "complete_task",
                    "use_captured": {"task_id": "step_2.selected_task_id"}
                }
            ],
            "success_criteria": "Task status changes to done"
        },
        "examples": [
            "Show me what's overdue, then complete the first one",
            "What's blocked? Mark the top one as done"
        ],
        "times_used": 0,
        "success_rate": 1.0,
        "created_at": datetime.utcnow(),
        "last_used": None
    },
    {
        "memory_type": "procedural",
        "rule_type": "workflow",
        "name": "Batch Create Tasks Workflow",
        "description": "Pattern for creating multiple tasks in sequence",
        "trigger_pattern": r"create.*tasks?.*and|create.*multiple.*task",
        "workflow": {
            "steps": [
                {
                    "step": 1,
                    "action": "create_task",
                    "extract_from_user": ["title_1", "project_name"],
                    "capture_result": "task_id_1"
                },
                {
                    "step": 2,
                    "action": "create_task",
                    "extract_from_user": ["title_2", "project_name"],
                    "capture_result": "task_id_2"
                },
                {
                    "step": 3,
                    "action": "create_task",
                    "extract_from_user": ["title_3", "project_name"],
                    "capture_result": "task_id_3",
                    "optional": True
                }
            ],
            "success_criteria": "All create_task calls return success"
        },
        "examples": [
            "Create tasks for research, design, and implementation",
            "Add tasks for frontend and backend work"
        ],
        "times_used": 0,
        "success_rate": 1.0,
        "created_at": datetime.utcnow(),
        "last_used": None
    },
    {
        "memory_type": "procedural",
        "rule_type": "workflow",
        "name": "Search Add Note Workflow",
        "description": "Pattern for finding a task and adding a note to it",
        "trigger_pattern": r"add.*note.*to|note.*on.*task",
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
                    "description": "Ask which task if multiple matches",
                    "wait_for_user": True
                },
                {
                    "step": 3,
                    "action": "add_note_to_task",
                    "use_captured": {
                        "task_id": "step_2.selected_task_id",
                        "note": "user_input.note_content"
                    }
                }
            ],
            "success_criteria": "Note appears in task's notes array"
        },
        "examples": [
            "Add a note to the migration task: completed phase 1",
            "Note on API docs task: reviewed by Sarah"
        ],
        "times_used": 0,
        "success_rate": 1.0,
        "created_at": datetime.utcnow(),
        "last_used": None
    }
]
