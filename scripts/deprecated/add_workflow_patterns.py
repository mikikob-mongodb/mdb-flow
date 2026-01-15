"""
Add additional workflow patterns to procedural memory.

This script adds high-priority workflow patterns from the pattern catalog:
- Reassign Task
- Create Project with Standard Tasks
- Clone Project Structure
- Handoff All Tasks
- Escalate Blocked Tasks
"""

from shared.db import get_db
from shared.embeddings import embed_query
from datetime import datetime

DEMO_USER_ID = "demo-user"


def get_new_workflows():
    """Define new workflow patterns to add."""
    return [
        # Pattern #5: Reassign Task
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "workflow",
            "name": "Reassign Task Workflow",
            "description": "Find a task and reassign it to a different team member",
            "trigger_pattern": r"reassign.*task|change.*assignee.*to|give.*task to",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "search_tasks",
                        "extract_from_user": ["title"],
                        "capture_result": "tasks",
                        "description": "Search for the task to reassign"
                    },
                    {
                        "step": 2,
                        "action": "update_task",
                        "use_captured": {"task_id": "step_1.task_id"},
                        "extract_from_user": ["assignee"],
                        "description": "Update task with new assignee"
                    }
                ],
                "success_criteria": "Task assignee updated successfully"
            },
            "examples": [
                "Reassign the migration task to Mike",
                "Change the assignee of API docs to Sarah",
                "Give the testing task to Alex"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None
        },

        # Pattern #11: Create Project with Standard Tasks
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "workflow",
            "name": "Create Project with Standard Tasks",
            "description": "Create a new project and populate it with standard task templates (Requirements, Design, Implementation, Testing, Deployment)",
            "trigger_pattern": r"create project.*with (?:standard )?tasks|new project.*standard|initialize project",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "create_project",
                        "extract_from_user": ["project_name", "description"],
                        "capture_result": "project_id",
                        "description": "Create the new project"
                    },
                    {
                        "step": 2,
                        "action": "create_task",
                        "use_captured": {"project_id": "step_1.project_id"},
                        "parameters": {"title": "Requirements", "priority": "high"},
                        "description": "Create Requirements task"
                    },
                    {
                        "step": 3,
                        "action": "create_task",
                        "use_captured": {"project_id": "step_1.project_id"},
                        "parameters": {"title": "Design", "priority": "medium"},
                        "description": "Create Design task"
                    },
                    {
                        "step": 4,
                        "action": "create_task",
                        "use_captured": {"project_id": "step_1.project_id"},
                        "parameters": {"title": "Implementation", "priority": "medium"},
                        "description": "Create Implementation task"
                    },
                    {
                        "step": 5,
                        "action": "create_task",
                        "use_captured": {"project_id": "step_1.project_id"},
                        "parameters": {"title": "Testing", "priority": "medium"},
                        "description": "Create Testing task"
                    },
                    {
                        "step": 6,
                        "action": "create_task",
                        "use_captured": {"project_id": "step_1.project_id"},
                        "parameters": {"title": "Deployment", "priority": "low"},
                        "description": "Create Deployment task"
                    }
                ],
                "success_criteria": "Project created with 5 standard tasks"
            },
            "examples": [
                "Create a new project called Website Redesign with standard tasks",
                "Initialize project Mobile App with standard workflow",
                "New project for API Refactor with tasks"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None
        },

        # Pattern #13: Clone Project Structure
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "workflow",
            "name": "Clone Project Structure",
            "description": "Copy an existing project's task structure to a new project with a different name",
            "trigger_pattern": r"clone project|copy project structure|duplicate project",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "search_projects",
                        "extract_from_user": ["source_project_name"],
                        "capture_result": "source_project_id",
                        "description": "Find the source project to clone"
                    },
                    {
                        "step": 2,
                        "action": "get_tasks",
                        "use_captured": {"project_id": "step_1.source_project_id"},
                        "capture_result": "source_tasks",
                        "description": "Get all tasks from source project"
                    },
                    {
                        "step": 3,
                        "action": "create_project",
                        "extract_from_user": ["new_project_name"],
                        "capture_result": "new_project_id",
                        "description": "Create the new project"
                    }
                    # Note: Steps 4+ would need loop construct to copy all tasks
                    # For now, this workflow will need custom handling
                ],
                "success_criteria": "New project created with cloned task structure"
            },
            "examples": [
                "Clone the Q4 Sprint project structure for Q1",
                "Copy the Website Redesign project to Mobile App Redesign",
                "Duplicate the API Project structure"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None
        },

        # Pattern #16: Handoff All Tasks
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "workflow",
            "name": "Handoff All Tasks Workflow",
            "description": "Transfer all tasks from one team member to another with handoff notes",
            "trigger_pattern": r"reassign all.*tasks from|handoff.*tasks|transfer (?:all )?(?:work|tasks) from",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "get_tasks",
                        "extract_from_user": ["from_assignee"],
                        "capture_result": "task_list",
                        "description": "Get all tasks assigned to the source person"
                    }
                    # Note: Steps 2+ would need loop construct for batch updates
                    # This workflow will need custom batch handling
                ],
                "success_criteria": "All tasks transferred with handoff notes"
            },
            "examples": [
                "Reassign all of Mike's tasks to Sarah",
                "Handoff Alex's work to the team",
                "Transfer all tasks from John to Mary"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None
        },

        # Pattern #6: Escalate Blocked Tasks
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "workflow",
            "name": "Escalate Blocked Tasks",
            "description": "Find blocked tasks, increase priority to high, and add escalation notes",
            "trigger_pattern": r"escalate.*blocked|priority.*blocked|urgent.*blocked",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "get_tasks",
                        "extract_from_user": ["project_name"],
                        "parameters": {"blocked": True},
                        "capture_result": "blocked_tasks",
                        "description": "Get all blocked tasks for the project"
                    }
                    # Note: Steps 2+ would need loop for batch priority updates
                    # This workflow will need custom batch handling
                ],
                "success_criteria": "All blocked tasks escalated to high priority"
            },
            "examples": [
                "Escalate all blocked tasks for Project Alpha",
                "Make blocked tasks high priority",
                "Urgent: escalate blocked work items"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None
        }
    ]


def main():
    db = get_db()

    # Get new workflows
    workflows = get_new_workflows()

    print(f"\n{'='*60}")
    print(f"ADDING {len(workflows)} NEW WORKFLOW PATTERNS")
    print(f"{'='*60}\n")

    added_count = 0

    for workflow in workflows:
        workflow_name = workflow["name"]

        # Check if workflow already exists
        existing = db.memory_procedural.find_one({
            "user_id": workflow["user_id"],
            "name": workflow_name
        })

        if existing:
            print(f"⏭️  Skipping: '{workflow_name}' (already exists)")
            continue

        # Generate embedding for semantic search
        # Combine name, description, and examples for better embeddings
        embedding_text = f"{workflow['name']}. {workflow['description']}. Examples: {', '.join(workflow['examples'])}"
        workflow["embedding"] = embed_query(embedding_text)

        # Insert workflow
        result = db.memory_procedural.insert_one(workflow)
        print(f"✓ Added: '{workflow_name}'")
        print(f"  Trigger: {workflow['trigger_pattern']}")
        print(f"  Steps: {len(workflow['workflow']['steps'])}")
        print()
        added_count += 1

    print(f"{'='*60}")
    print(f"✅ Added {added_count} new workflow patterns")
    print(f"{'='*60}\n")

    # Show final count
    total_workflows = db.memory_procedural.count_documents({"user_id": DEMO_USER_ID})
    print(f"Total workflows in memory_procedural: {total_workflows}\n")


if __name__ == "__main__":
    main()
