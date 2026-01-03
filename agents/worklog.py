"""Worklog Agent for task and project management operations."""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from bson import ObjectId

from shared.llm import llm_service
from shared.logger import get_logger
from shared.embeddings import embed_document
from shared.db import (
    create_task as db_create_task,
    update_task as db_update_task,
    add_task_note,
    get_task as db_get_task,
    create_project as db_create_project,
    update_project as db_update_project,
    add_project_note,
    add_project_method,
    add_project_decision,
    get_project as db_get_project,
    get_collection,
    TASKS_COLLECTION,
    PROJECTS_COLLECTION,
)
from shared.models import Task, Project

logger = get_logger("worklog")


class WorklogAgent:
    """Agent for handling task and project management operations using Claude."""

    def __init__(self):
        self.llm = llm_service
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define all available tools for the agent."""
        return [
            {
                "name": "create_task",
                "description": "Create a new task with optional context, notes, priority, and status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the task"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Optional project ID (MongoDB ObjectId as string)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Rich context about the task"
                        },
                        "notes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional array of notes"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Task priority"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done"],
                            "description": "Task status (defaults to 'todo')"
                        }
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "update_task",
                "description": "Update an existing task's fields",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID (MongoDB ObjectId as string)"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done"],
                            "description": "New status"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "New priority"
                        },
                        "context": {
                            "type": "string",
                            "description": "New or additional context"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "New project ID"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID (MongoDB ObjectId as string)"
                        },
                        "completion_note": {
                            "type": "string",
                            "description": "Optional note about task completion"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "create_project",
                "description": "Create a new project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Project description"
                        },
                        "context": {
                            "type": "string",
                            "description": "Rich context about the project"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "update_project",
                "description": "Update an existing project's fields",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (MongoDB ObjectId as string)"
                        },
                        "name": {
                            "type": "string",
                            "description": "New name"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description"
                        },
                        "context": {
                            "type": "string",
                            "description": "New or additional context"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["active", "archived"],
                            "description": "Project status"
                        }
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "add_note",
                "description": "Add a note to a task or project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_type": {
                            "type": "string",
                            "enum": ["task", "project"],
                            "description": "Type of target (task or project)"
                        },
                        "target_id": {
                            "type": "string",
                            "description": "Target ID (MongoDB ObjectId as string)"
                        },
                        "note": {
                            "type": "string",
                            "description": "Note content to add"
                        }
                    },
                    "required": ["target_type", "target_id", "note"]
                }
            },
            {
                "name": "add_context",
                "description": "Add or update context for a task or project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_type": {
                            "type": "string",
                            "enum": ["task", "project"],
                            "description": "Type of target (task or project)"
                        },
                        "target_id": {
                            "type": "string",
                            "description": "Target ID (MongoDB ObjectId as string)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context to add or update"
                        }
                    },
                    "required": ["target_type", "target_id", "context"]
                }
            },
            {
                "name": "add_decision",
                "description": "Add a decision to a project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (MongoDB ObjectId as string)"
                        },
                        "decision": {
                            "type": "string",
                            "description": "Decision to record"
                        }
                    },
                    "required": ["project_id", "decision"]
                }
            },
            {
                "name": "add_method",
                "description": "Add a technology/method/approach to a project",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (MongoDB ObjectId as string)"
                        },
                        "method": {
                            "type": "string",
                            "description": "Technology, method, or approach to add"
                        }
                    },
                    "required": ["project_id", "method"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List tasks with optional filters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Filter by project ID"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done"],
                            "description": "Filter by status"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (default: 20)",
                            "default": 20
                        }
                    }
                }
            },
            {
                "name": "list_projects",
                "description": "List projects with optional filters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["active", "archived"],
                            "description": "Filter by status"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of projects to return (default: 20)",
                            "default": 20
                        }
                    }
                }
            },
            {
                "name": "get_task",
                "description": "Get a single task by ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID (MongoDB ObjectId as string)"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_project",
                "description": "Get a single project by ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (MongoDB ObjectId as string)"
                        }
                    },
                    "required": ["project_id"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Dictionary with the tool execution result
        """
        try:
            if tool_name == "create_task":
                return self._create_task(**tool_input)
            elif tool_name == "update_task":
                return self._update_task(**tool_input)
            elif tool_name == "complete_task":
                return self._complete_task(**tool_input)
            elif tool_name == "create_project":
                return self._create_project(**tool_input)
            elif tool_name == "update_project":
                return self._update_project(**tool_input)
            elif tool_name == "add_note":
                return self._add_note(**tool_input)
            elif tool_name == "add_context":
                return self._add_context(**tool_input)
            elif tool_name == "add_decision":
                return self._add_decision(**tool_input)
            elif tool_name == "add_method":
                return self._add_method(**tool_input)
            elif tool_name == "list_tasks":
                return self._list_tasks(**tool_input)
            elif tool_name == "list_projects":
                return self._list_projects(**tool_input)
            elif tool_name == "get_task":
                return self._get_task(**tool_input)
            elif tool_name == "get_project":
                return self._get_project(**tool_input)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _create_task(
        self,
        title: str,
        project_id: Optional[str] = None,
        context: str = "",
        notes: Optional[List[str]] = None,
        priority: Optional[Literal["low", "medium", "high"]] = None,
        status: Literal["todo", "in_progress", "done"] = "todo"
    ) -> Dict[str, Any]:
        """Create a new task."""
        # Create task model
        task = Task(
            title=title,
            project_id=ObjectId(project_id) if project_id else None,
            context=context,
            notes=notes or [],
            priority=priority,
            status=status
        )

        # Generate embedding from title + context
        embedding_text = f"{title}\n{context}".strip()
        task.embedding = embed_document(embedding_text)

        # Create in database
        task_id = db_create_task(task, action_note=f"Task created: {title}")

        # Return created task
        created_task = db_get_task(task_id)
        return {
            "success": True,
            "task_id": str(task_id),
            "task": self._task_to_dict(created_task)
        }

    def _update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        status: Optional[Literal["todo", "in_progress", "done"]] = None,
        priority: Optional[Literal["low", "medium", "high"]] = None,
        context: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing task."""
        task_oid = ObjectId(task_id)
        current_task = db_get_task(task_oid)

        if not current_task:
            return {"success": False, "error": "Task not found"}

        updates = {}
        changes = []

        if title is not None:
            updates["title"] = title
            changes.append(f"title changed to '{title}'")

        if status is not None:
            updates["status"] = status
            changes.append(f"status changed to '{status}'")

        if priority is not None:
            updates["priority"] = priority
            changes.append(f"priority changed to '{priority}'")

        if context is not None:
            updates["context"] = context
            changes.append("context updated")

        if project_id is not None:
            updates["project_id"] = ObjectId(project_id)
            changes.append(f"moved to project {project_id}")

        # Re-generate embedding if title or context changed
        if title is not None or context is not None:
            new_title = title if title is not None else current_task.title
            new_context = context if context is not None else current_task.context
            embedding_text = f"{new_title}\n{new_context}".strip()
            updates["embedding"] = embed_document(embedding_text)

        # Update in database
        action_note = "; ".join(changes) if changes else "Task updated"
        success = db_update_task(task_oid, updates, "updated", action_note)

        # Return updated task
        updated_task = db_get_task(task_oid)
        return {
            "success": success,
            "task": self._task_to_dict(updated_task)
        }

    def _complete_task(
        self,
        task_id: str,
        completion_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a task as completed."""
        task_oid = ObjectId(task_id)

        updates = {
            "status": "done",
            "completed_at": datetime.utcnow()
        }

        action_note = completion_note if completion_note else "Task completed"
        success = db_update_task(task_oid, updates, "completed", action_note)

        updated_task = db_get_task(task_oid)
        return {
            "success": success,
            "task": self._task_to_dict(updated_task)
        }

    def _create_project(
        self,
        name: str,
        description: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """Create a new project."""
        # Create project model
        project = Project(
            name=name,
            description=description,
            context=context
        )

        # Generate embedding from name + description
        embedding_text = f"{name}\n{description}".strip()
        project.embedding = embed_document(embedding_text)

        # Create in database
        project_id = db_create_project(project, action_note=f"Project created: {name}")

        # Return created project
        created_project = db_get_project(project_id)
        return {
            "success": True,
            "project_id": str(project_id),
            "project": self._project_to_dict(created_project)
        }

    def _update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        context: Optional[str] = None,
        status: Optional[Literal["active", "archived"]] = None
    ) -> Dict[str, Any]:
        """Update an existing project."""
        project_oid = ObjectId(project_id)
        current_project = db_get_project(project_oid)

        if not current_project:
            return {"success": False, "error": "Project not found"}

        updates = {}
        changes = []

        if name is not None:
            updates["name"] = name
            changes.append(f"name changed to '{name}'")

        if description is not None:
            updates["description"] = description
            changes.append("description updated")

        if context is not None:
            updates["context"] = context
            changes.append("context updated")

        if status is not None:
            updates["status"] = status
            changes.append(f"status changed to '{status}'")

        # Re-generate embedding if name or description changed
        if name is not None or description is not None:
            new_name = name if name is not None else current_project.name
            new_desc = description if description is not None else current_project.description
            embedding_text = f"{new_name}\n{new_desc}".strip()
            updates["embedding"] = embed_document(embedding_text)

        # Update in database
        action_note = "; ".join(changes) if changes else "Project updated"
        success = db_update_project(project_oid, updates, "updated", action_note)

        # Return updated project
        updated_project = db_get_project(project_oid)
        return {
            "success": success,
            "project": self._project_to_dict(updated_project)
        }

    def _add_note(
        self,
        target_type: Literal["task", "project"],
        target_id: str,
        note: str
    ) -> Dict[str, Any]:
        """Add a note to a task or project."""
        target_oid = ObjectId(target_id)

        if target_type == "task":
            success = add_task_note(target_oid, note)
        else:  # project
            success = add_project_note(target_oid, note)

        return {
            "success": success,
            "message": f"Note added to {target_type}"
        }

    def _add_context(
        self,
        target_type: Literal["task", "project"],
        target_id: str,
        context: str
    ) -> Dict[str, Any]:
        """Add or update context for a task or project."""
        target_oid = ObjectId(target_id)

        if target_type == "task":
            # Get current task to regenerate embedding
            current_task = db_get_task(target_oid)
            if not current_task:
                return {"success": False, "error": "Task not found"}

            embedding_text = f"{current_task.title}\n{context}".strip()
            embedding = embed_document(embedding_text)

            success = db_update_task(
                target_oid,
                {"context": context, "embedding": embedding},
                "context_added",
                "Context updated"
            )
        else:  # project
            # Get current project to regenerate embedding
            current_project = db_get_project(target_oid)
            if not current_project:
                return {"success": False, "error": "Project not found"}

            embedding_text = f"{current_project.name}\n{current_project.description}".strip()
            embedding = embed_document(embedding_text)

            success = db_update_project(
                target_oid,
                {"context": context, "embedding": embedding},
                "context_added",
                "Context updated"
            )

        return {
            "success": success,
            "message": f"Context updated for {target_type}"
        }

    def _add_decision(self, project_id: str, decision: str) -> Dict[str, Any]:
        """Add a decision to a project."""
        project_oid = ObjectId(project_id)
        success = add_project_decision(project_oid, decision)

        return {
            "success": success,
            "message": "Decision added to project"
        }

    def _add_method(self, project_id: str, method: str) -> Dict[str, Any]:
        """Add a method/technology to a project."""
        project_oid = ObjectId(project_id)
        success = add_project_method(project_oid, method)

        return {
            "success": success,
            "message": "Method added to project"
        }

    def _list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[Literal["todo", "in_progress", "done"]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List tasks with optional filters."""
        collection = get_collection(TASKS_COLLECTION)

        # Build query
        query = {}
        if project_id:
            query["project_id"] = ObjectId(project_id)
        if status:
            query["status"] = status

        # Execute query - exclude embedding field for performance
        cursor = collection.find(query, {"embedding": 0}).sort("created_at", -1).limit(limit)
        tasks = [Task(**doc) for doc in cursor]

        return {
            "success": True,
            "count": len(tasks),
            "tasks": [self._task_to_dict(task) for task in tasks]
        }

    def _list_projects(
        self,
        status: Optional[Literal["active", "archived"]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List projects with optional filters."""
        collection = get_collection(PROJECTS_COLLECTION)

        # Build query
        query = {}
        if status:
            query["status"] = status

        # Execute query - exclude embedding field for performance
        cursor = collection.find(query, {"embedding": 0}).sort("created_at", -1).limit(limit)
        projects = [Project(**doc) for doc in cursor]

        return {
            "success": True,
            "count": len(projects),
            "projects": [self._project_to_dict(project) for project in projects]
        }

    def _get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a single task by ID."""
        task_oid = ObjectId(task_id)
        task = db_get_task(task_oid)

        if not task:
            return {"success": False, "error": "Task not found"}

        return {
            "success": True,
            "task": self._task_to_dict(task)
        }

    def _get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a single project by ID."""
        project_oid = ObjectId(project_id)
        project = db_get_project(project_oid)

        if not project:
            return {"success": False, "error": "Project not found"}

        return {
            "success": True,
            "project": self._project_to_dict(project)
        }

    def apply_voice_update(
        self,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        updates: Optional[Dict[str, Any]] = None,
        voice_log_entry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply batch updates from parsed voice input to a task or project.

        Args:
            task_id: Optional task ID to update
            project_id: Optional project ID to update
            updates: dict with fields to update:
                - status: new status
                - notes_to_add: list of notes to add
                - context: context to add/update
            voice_log_entry: dict with:
                - summary: cleaned summary
                - raw_transcript: original speech
                - extracted: parsed voice structure

        Returns:
            dict with success status and updated entity
        """
        logger.info(f"apply_voice_update: task_id={task_id}, project_id={project_id}")
        logger.debug(f"Updates: {updates}")
        logger.debug(f"Voice log summary: {voice_log_entry.get('summary', 'N/A')}")

        if not task_id and not project_id:
            logger.warning("apply_voice_update called without task_id or project_id")
            return {"success": False, "error": "Must provide either task_id or project_id"}

        updates = updates or {}
        voice_log_entry = voice_log_entry or {}

        # Process task update
        if task_id:
            logger.info(f"Applying voice update to task {task_id}")
            task_oid = ObjectId(task_id)
            current_task = db_get_task(task_oid)

            if not current_task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found"}

            # Build update dict
            update_fields = {}
            changes = []

            # Update status if provided
            if "status" in updates:
                logger.info(f"Updating task status: {current_task.status} → {updates['status']}")
                update_fields["status"] = updates["status"]
                changes.append(f"status changed to '{updates['status']}'")
                if updates["status"] == "done":
                    update_fields["completed_at"] = datetime.utcnow()

            # Add context if provided
            if "context" in updates:
                # Append to existing context
                new_context = current_task.context
                if new_context:
                    new_context += f"\n\n{updates['context']}"
                else:
                    new_context = updates["context"]
                update_fields["context"] = new_context
                changes.append("context updated")

                # Regenerate embedding
                embedding_text = f"{current_task.title}\n{new_context}".strip()
                update_fields["embedding"] = embed_document(embedding_text)

            # Create voice activity log entry
            from shared.models import ActivityLogEntry
            log_entry = ActivityLogEntry(
                action="voice_update",
                note=voice_log_entry.get("summary", "Voice update"),
                summary=voice_log_entry.get("summary"),
                raw_transcript=voice_log_entry.get("raw_transcript"),
                extracted=voice_log_entry.get("extracted")
            )

            # Add to activity log
            if "activity_log" not in update_fields:
                update_fields["activity_log"] = current_task.activity_log
            update_fields["activity_log"].append(log_entry)

            # Apply updates
            action_note = "; ".join(changes) if changes else "Voice update applied"
            db_update_task(task_oid, update_fields, "voice_update", action_note)

            # Add notes separately if provided
            if "notes_to_add" in updates:
                for note in updates["notes_to_add"]:
                    add_task_note(task_oid, note)

            # Return updated task
            updated_task = db_get_task(task_oid)
            return {
                "success": True,
                "task": self._task_to_dict(updated_task)
            }

        # Process project update
        else:  # project_id
            project_oid = ObjectId(project_id)
            current_project = db_get_project(project_oid)

            if not current_project:
                return {"success": False, "error": "Project not found"}

            # Build update dict
            update_fields = {}
            changes = []

            # Update status if provided
            if "status" in updates:
                update_fields["status"] = updates["status"]
                changes.append(f"status changed to '{updates['status']}'")

            # Add context if provided
            if "context" in updates:
                # Append to existing context
                new_context = current_project.context
                if new_context:
                    new_context += f"\n\n{updates['context']}"
                else:
                    new_context = updates["context"]
                update_fields["context"] = new_context
                changes.append("context updated")

                # Regenerate embedding
                embedding_text = f"{current_project.name}\n{current_project.description}".strip()
                update_fields["embedding"] = embed_document(embedding_text)

            # Create voice activity log entry
            from shared.models import ActivityLogEntry
            log_entry = ActivityLogEntry(
                action="voice_update",
                note=voice_log_entry.get("summary", "Voice update"),
                summary=voice_log_entry.get("summary"),
                raw_transcript=voice_log_entry.get("raw_transcript"),
                extracted=voice_log_entry.get("extracted")
            )

            # Add to activity log
            if "activity_log" not in update_fields:
                update_fields["activity_log"] = current_project.activity_log
            update_fields["activity_log"].append(log_entry)

            # Apply updates
            action_note = "; ".join(changes) if changes else "Voice update applied"
            db_update_project(project_oid, update_fields, "voice_update", action_note)

            # Add notes separately if provided
            if "notes_to_add" in updates:
                for note in updates["notes_to_add"]:
                    add_project_note(project_oid, note)

            # Return updated project
            updated_project = db_get_project(project_oid)
            return {
                "success": True,
                "project": self._project_to_dict(updated_project)
            }

    def create_task_from_voice(
        self,
        title: str,
        project_id: Optional[str] = None,
        source: Optional[str] = None,
        context: str = "",
        from_transcript: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a task that was mentioned in voice input.

        Args:
            title: Task title
            project_id: Optional project ID
            source: Source attribution (e.g., "mentioned by Sarah in standup")
            context: Task context
            from_transcript: Original transcript snippet

        Returns:
            dict with success status and created task
        """
        # Build context with source attribution
        full_context = context
        if source:
            attribution = f"Source: {source}"
            full_context = f"{attribution}\n\n{context}" if context else attribution

        # Create task model
        task = Task(
            title=title,
            project_id=ObjectId(project_id) if project_id else None,
            context=full_context,
            status="todo"
        )

        # Generate embedding
        embedding_text = f"{title}\n{full_context}".strip()
        task.embedding = embed_document(embedding_text)

        # Add voice creation log entry
        from shared.models import ActivityLogEntry
        log_entry = ActivityLogEntry(
            action="created_from_voice",
            note=f"Task created from voice input{': ' + source if source else ''}",
            summary=f"Created: {title}",
            raw_transcript=from_transcript
        )
        task.activity_log.append(log_entry)

        # Create in database
        action_note = f"Task created from voice: {title}"
        if source:
            action_note += f" (source: {source})"
        task_id = db_create_task(task, action_note=action_note)

        # Return created task
        created_task = db_get_task(task_id)
        return {
            "success": True,
            "task_id": str(task_id),
            "task": self._task_to_dict(created_task)
        }

    def _task_to_dict(self, task: Optional[Task]) -> Optional[Dict[str, Any]]:
        """Convert Task model to dictionary for JSON serialization."""
        if not task:
            return None

        task_dict = task.model_dump(exclude={"embedding"})  # Exclude large embedding
        task_dict["_id"] = str(task.id) if task.id else None
        task_dict["project_id"] = str(task.project_id) if task.project_id else None
        return task_dict

    def _project_to_dict(self, project: Optional[Project]) -> Optional[Dict[str, Any]]:
        """Convert Project model to dictionary for JSON serialization."""
        if not project:
            return None

        project_dict = project.model_dump(exclude={"embedding"})  # Exclude large embedding
        project_dict["_id"] = str(project.id) if project.id else None
        return project_dict

    def process(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Process a user message and execute appropriate tools.

        Args:
            user_message: User's natural language request
            conversation_history: Optional conversation history

        Returns:
            Agent's response
        """
        # Build messages
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        # System prompt for the agent
        system_prompt = """You are a helpful task and project management assistant.
You have access to tools for creating, updating, and managing tasks and projects.
Use the appropriate tools to help users manage their work.

When users ask about their tasks or projects:
- ALWAYS use the list_tasks or list_projects tools to check what exists
- Don't assume the database is empty - always check first
- Report the actual results from the tools

When creating or updating tasks/projects:
- Extract relevant information from the user's message
- Ask for clarification if needed before using tools
- Provide clear confirmation of actions taken
- Be proactive in suggesting task organization

Always use the tools to perform actual operations - don't just describe what you would do."""

        # Tool use loop
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call Claude with tools
            response = self.llm.generate_with_tools(
                messages=messages,
                tools=self.tools,
                system=system_prompt,
                max_tokens=4096
            )

            # Check if we're done (no tool use)
            if response.stop_reason == "end_turn":
                # Extract text response
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                return text_content

            # Process tool uses
            if response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute tools and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        # Execute tool
                        result = self.execute_tool(tool_name, tool_input)

                        # Debug logging
                        print(f"[DEBUG] Tool: {tool_name}, Input: {tool_input}")
                        print(f"[DEBUG] Result count: {result.get('count', 'N/A')}, Success: {result.get('success', 'N/A')}")

                        # Add result
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": str(result)
                        })

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

        return "Maximum iterations reached. Please try again with a simpler request."


# Global agent instance
worklog_agent = WorklogAgent()
