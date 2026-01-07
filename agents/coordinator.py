"""Coordinator Agent that routes requests to appropriate sub-agents."""

import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from bson import ObjectId

from shared.llm import llm_service
from shared.logger import get_logger
from agents.worklog import worklog_agent
from agents.retrieval import retrieval_agent
from utils.context_engineering import compress_tool_result
from config.prompts import get_system_prompt, get_prompt_stats

logger = get_logger("coordinator")


def convert_objectids_to_str(obj):
    """Recursively convert ObjectId and datetime instances to strings for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_objectids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectids_to_str(item) for item in obj]
    else:
        return obj

# Tool definitions for Claude
COORDINATOR_TOOLS = [
    {
        "name": "get_tasks",
        "description": "Get all tasks, optionally filtered by status or project. Use this when user asks 'what are my tasks' or 'show me all tasks'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "done"],
                    "description": "Filter by task status"
                },
                "project_name": {
                    "type": "string",
                    "description": "Filter by project name"
                }
            }
        }
    },
    {
        "name": "search_tasks",
        "description": "Search for tasks using hybrid search (vector + text). Use for informal references like 'the debugging doc', 'checkpointer task', or 'voice agent app'. Returns top matching tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The informal task reference or search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as done/completed. Requires task_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "start_task",
        "description": "Mark a task as in_progress (currently working on it). Requires task_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "add_note_to_task",
        "description": "Add a note/context to a task. Requires task_id and note text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                },
                "note": {
                    "type": "string",
                    "description": "The note text to add"
                }
            },
            "required": ["task_id", "note"]
        }
    },
    {
        "name": "get_projects",
        "description": "List all projects with their status and task counts.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_projects",
        "description": "Search for projects by name using hybrid search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The project name or search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_tasks_by_time",
        "description": "Get tasks based on when activity happened. Use for temporal questions like 'what did I do today', 'tasks from this week', 'what did I complete yesterday'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["today", "yesterday", "this_week", "last_week", "this_month"],
                    "description": "Relative time period to query"
                },
                "activity_type": {
                    "type": "string",
                    "enum": ["created", "started", "completed", "note_added", "updated"],
                    "description": "Type of activity to filter by (optional)"
                },
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "done"],
                    "description": "Current status filter (optional)"
                }
            },
            "required": ["timeframe"]
        }
    },
    {
        "name": "create_task",
        "description": "Create a new task in a project. Requires project name - no orphan tasks allowed. Use when user says 'create a task', 'add a task', 'make a new task', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "project_name": {
                    "type": "string",
                    "description": "Project to add task to (required - look up by name using search_projects if needed)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Task priority (default: medium)"
                },
                "context": {
                    "type": "string",
                    "description": "Optional context/description for the task"
                }
            },
            "required": ["title", "project_name"]
        }
    },
    {
        "name": "update_task",
        "description": "Update an existing task's title, priority, context, status, or move it to a different project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                },
                "title": {
                    "type": "string",
                    "description": "New task title"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "New priority"
                },
                "context": {
                    "type": "string",
                    "description": "New or additional context"
                },
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "done"],
                    "description": "New status"
                },
                "project_name": {
                    "type": "string",
                    "description": "Move task to this project (will look up by name)"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "stop_task",
        "description": "Stop working on a task and mark it as todo. Use when user says 'I stopped working on X' or 'pause X'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "create_project",
        "description": "Create a new project. Use when user says 'create a project', 'make a new project', 'start a project called X'.",
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
        "description": "Update an existing project's name, description, context, or status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
                },
                "name": {
                    "type": "string",
                    "description": "New project name"
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
        "name": "add_note_to_project",
        "description": "Add a note to a project. Use for general notes, updates, or observations about the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
                },
                "note": {
                    "type": "string",
                    "description": "The note text to add"
                }
            },
            "required": ["project_id", "note"]
        }
    },
    {
        "name": "add_context_to_task",
        "description": "Add or update rich context for a task. Context is different from notes - it's the main descriptive content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                },
                "context": {
                    "type": "string",
                    "description": "Context to add or update"
                }
            },
            "required": ["task_id", "context"]
        }
    },
    {
        "name": "add_context_to_project",
        "description": "Add or update rich context for a project. Context is different from notes - it's the main descriptive content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
                },
                "context": {
                    "type": "string",
                    "description": "Context to add or update"
                }
            },
            "required": ["project_id", "context"]
        }
    },
    {
        "name": "add_decision_to_project",
        "description": "Record an important decision made about the project. Use for architectural decisions, technology choices, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
                },
                "decision": {
                    "type": "string",
                    "description": "The decision to record"
                }
            },
            "required": ["project_id", "decision"]
        }
    },
    {
        "name": "add_method_to_project",
        "description": "Add a technology, method, or approach being used in the project. Use for tracking tech stack, methodologies, frameworks, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
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
        "name": "get_task",
        "description": "Get details of a single task by ID. Use when you have the task_id and need full details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the task"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "get_project",
        "description": "Get details of a single project by ID. Use when you have the project_id and need full details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "MongoDB ObjectId of the project"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_action_history",
        "description": "Get history of past actions from long-term memory. Use for questions like 'what did I do last week', 'what have I been working on', 'what tasks did I complete'. Only available when long-term memory is enabled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "description": "Time range to query",
                    "enum": ["today", "yesterday", "this_week", "last_week", "this_month"]
                },
                "action_type": {
                    "type": "string",
                    "description": "Filter by action type",
                    "enum": ["completed", "started", "created", "noted", "all"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10
                }
            },
            "required": ["time_range"]
        }
    }
]

# System prompts are now defined in config/prompts.py
# Use get_system_prompt(streamlined=True/False) to retrieve them


class CoordinatorAgent:
    """Coordinator agent that routes user requests to specialized agents using tool use."""

    def __init__(self, memory_manager=None):
        self.llm = llm_service
        self.worklog_agent = worklog_agent
        self.retrieval_agent = retrieval_agent
        self.memory = memory_manager  # Memory manager for long-term action history
        self.last_debug_info = []  # Store debug info from last request (deprecated - use current_turn)
        self.current_turn = None  # Current conversation turn with all tool calls

    def _summarize_output(self, result: Any) -> str:
        """
        Create a brief summary of tool output for debug display.

        Args:
            result: The tool result to summarize

        Returns:
            Brief string summary
        """
        if result is None:
            return "None"
        elif isinstance(result, dict):
            if "tasks" in result:
                return f"{result.get('count', 0)} tasks returned"
            elif "projects" in result:
                return f"{result.get('count', 0)} projects returned"
            elif "success" in result:
                if result["success"]:
                    return "Success"
                else:
                    return f"Error: {result.get('error', 'Unknown')}"
            else:
                # Truncate dict representation
                return str(result)[:200]
        elif isinstance(result, list):
            return f"{len(result)} items returned"
        else:
            return str(result)[:200]

    def _record_to_long_term(
        self,
        action: str,
        content: dict,
        user_id: str = "default"
    ):
        """Record significant actions to long-term memory.

        Args:
            action: Action type (e.g., "completed", "started", "created", "noted")
            content: Action content dict
            user_id: User identifier
        """
        if not self.memory:
            return

        self.memory.write_long_term(
            user_id=user_id,
            memory_type="action",
            content={
                "action": action,
                **content,
                "timestamp": datetime.utcnow().isoformat()
            },
            tags=[f"action:{action}"]
        )

    def _get_available_tools(self) -> List[Dict]:
        """Get tools available based on current settings.

        Returns:
            List of tool definitions
        """
        # Start with all base tools except get_action_history
        tools = [t for t in COORDINATOR_TOOLS if t["name"] != "get_action_history"]

        # Only include history tool if long-term memory is enabled
        if self.optimizations.get("long_term_memory") and self.memory:
            # Find the history tool definition
            history_tool = next((t for t in COORDINATOR_TOOLS if t["name"] == "get_action_history"), None)
            if history_tool:
                tools.append(history_tool)

        return tools

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a tool and return the result with debug info.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            Tuple of (tool_result, debug_info)
        """
        import time

        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

        start_time = time.time()
        error_msg = None
        result = None

        try:
            if tool_name == "get_tasks":
                # Get all tasks with optional filtering - DIRECT DATABASE CALL
                status = tool_input.get("status")
                project_name = tool_input.get("project_name")

                # Call worklog agent's direct method (bypasses LLM)
                result = self.worklog_agent._list_tasks(
                    status=status,
                    limit=50
                )

            elif tool_name == "search_tasks":
                # Hybrid search for tasks
                query = tool_input["query"]
                limit = tool_input.get("limit", 5)

                tasks = self.retrieval_agent.hybrid_search_tasks(query, limit)

                # Convert ObjectId to string for JSON serialization
                for task in tasks:
                    if "_id" in task:
                        task["_id"] = str(task["_id"])
                    if "project_id" in task and task["project_id"]:
                        task["project_id"] = str(task["project_id"])

                result = {
                    "success": True,
                    "tasks": tasks,
                    "count": len(tasks)
                }

            elif tool_name == "complete_task":
                # Mark task as done - DIRECT DATABASE CALL
                task_id = tool_input["task_id"]
                result = self.worklog_agent._complete_task(task_id)

            elif tool_name == "start_task":
                # Mark task as in_progress - DIRECT DATABASE CALL
                task_id = tool_input["task_id"]
                result = self.worklog_agent._update_task(task_id, status="in_progress")

            elif tool_name == "add_note_to_task":
                # Add note to task - DIRECT DATABASE CALL
                task_id = tool_input["task_id"]
                note = tool_input["note"]
                result = self.worklog_agent._add_note("task", task_id, note)

            elif tool_name == "get_projects":
                # Get all projects - DIRECT DATABASE CALL
                result = self.worklog_agent._list_projects(limit=50)

            elif tool_name == "search_projects":
                # Hybrid search for projects
                query = tool_input["query"]
                limit = tool_input.get("limit", 5)

                projects = self.retrieval_agent.hybrid_search_projects(query, limit)

                # Convert ObjectId to string for JSON serialization
                for project in projects:
                    if "_id" in project:
                        project["_id"] = str(project["_id"])

                result = {
                    "success": True,
                    "projects": projects,
                    "count": len(projects)
                }

            elif tool_name == "get_tasks_by_time":
                # Temporal query for tasks based on activity timestamps
                from datetime import timedelta

                timeframe = tool_input["timeframe"]
                activity_type = tool_input.get("activity_type")
                status = tool_input.get("status")

                # Convert timeframe to dates
                now = datetime.now()
                since = None
                until = None

                if timeframe == "today":
                    since = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif timeframe == "yesterday":
                    since = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    until = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif timeframe == "this_week":
                    # Start of week (Monday)
                    since = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                elif timeframe == "last_week":
                    # Start of last week
                    since = (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
                    # End of last week
                    until = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                elif timeframe == "this_month":
                    since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                # Query tasks by activity
                tasks = self.retrieval_agent.get_tasks_by_activity(
                    since=since,
                    until=until,
                    activity_type=activity_type,
                    status=status
                )

                # Convert ObjectId to string for JSON serialization
                for task in tasks:
                    if "_id" in task:
                        task["_id"] = str(task["_id"])
                    if "project_id" in task and task["project_id"]:
                        task["project_id"] = str(task["project_id"])

                result = {
                    "success": True,
                    "tasks": tasks,
                    "count": len(tasks),
                    "timeframe": timeframe,
                    "activity_type": activity_type
                }

            elif tool_name == "create_task":
                # Create a new task - look up project by name first
                title = tool_input["title"]
                project_name = tool_input["project_name"]
                priority = tool_input.get("priority", "medium")
                context = tool_input.get("context", "")

                # Look up project by name
                projects = self.retrieval_agent.hybrid_search_projects(project_name, limit=1)

                if not projects:
                    result = {
                        "success": False,
                        "error": f"Project not found: '{project_name}'. Use search_projects or get_projects to see available projects."
                    }
                else:
                    project_id = projects[0]["_id"]

                    # Create task via worklog agent
                    result = self.worklog_agent._create_task(
                        title=title,
                        project_id=str(project_id),
                        priority=priority,
                        context=context
                    )

            elif tool_name == "update_task":
                # Update task fields
                task_id = tool_input["task_id"]
                title = tool_input.get("title")
                priority = tool_input.get("priority")
                context = tool_input.get("context")
                status = tool_input.get("status")
                project_name = tool_input.get("project_name")

                # Look up project if moving to different project
                project_id = None
                if project_name:
                    projects = self.retrieval_agent.hybrid_search_projects(project_name, limit=1)
                    if projects:
                        project_id = str(projects[0]["_id"])
                    else:
                        result = {
                            "success": False,
                            "error": f"Project not found: '{project_name}'"
                        }

                if project_name and not project_id:
                    pass  # Error already set above
                else:
                    result = self.worklog_agent._update_task(
                        task_id=task_id,
                        title=title,
                        priority=priority,
                        context=context,
                        status=status,
                        project_id=project_id
                    )

            elif tool_name == "stop_task":
                # Mark task as todo (stopped)
                task_id = tool_input["task_id"]
                result = self.worklog_agent._update_task(task_id, status="todo")

            elif tool_name == "create_project":
                # Create a new project
                name = tool_input["name"]
                description = tool_input.get("description", "")
                context = tool_input.get("context", "")
                result = self.worklog_agent._create_project(
                    name=name,
                    description=description,
                    context=context
                )

            elif tool_name == "update_project":
                # Update project fields
                project_id = tool_input["project_id"]
                name = tool_input.get("name")
                description = tool_input.get("description")
                context = tool_input.get("context")
                status = tool_input.get("status")
                result = self.worklog_agent._update_project(
                    project_id=project_id,
                    name=name,
                    description=description,
                    context=context,
                    status=status
                )

            elif tool_name == "add_note_to_project":
                # Add note to project
                project_id = tool_input["project_id"]
                note = tool_input["note"]
                result = self.worklog_agent._add_note("project", project_id, note)

            elif tool_name == "add_context_to_task":
                # Add context to task
                task_id = tool_input["task_id"]
                context = tool_input["context"]
                result = self.worklog_agent._add_context("task", task_id, context)

            elif tool_name == "add_context_to_project":
                # Add context to project
                project_id = tool_input["project_id"]
                context = tool_input["context"]
                result = self.worklog_agent._add_context("project", project_id, context)

            elif tool_name == "add_decision_to_project":
                # Add decision to project
                project_id = tool_input["project_id"]
                decision = tool_input["decision"]
                result = self.worklog_agent._add_decision(project_id, decision)

            elif tool_name == "add_method_to_project":
                # Add method/technology to project
                project_id = tool_input["project_id"]
                method = tool_input["method"]
                result = self.worklog_agent._add_method(project_id, method)

            elif tool_name == "get_task":
                # Get single task by ID
                task_id = tool_input["task_id"]
                result = self.worklog_agent._get_task(task_id)

            elif tool_name == "get_project":
                # Get single project by ID
                project_id = tool_input["project_id"]
                result = self.worklog_agent._get_project(project_id)

            elif tool_name == "get_action_history":
                # Query long-term memory for action history
                from datetime import timedelta

                time_range = tool_input["time_range"]
                action_type = tool_input.get("action_type", "all")
                limit = tool_input.get("limit", 10)

                # Calculate date range
                now = datetime.utcnow()
                date_ranges = {
                    "today": now - timedelta(days=1),
                    "yesterday": now - timedelta(days=2),
                    "this_week": now - timedelta(days=7),
                    "last_week": now - timedelta(days=14),
                    "this_month": now - timedelta(days=30)
                }

                start_date = date_ranges.get(time_range, now - timedelta(days=7))

                # Query long-term memory
                if not self.memory:
                    result = {
                        "success": False,
                        "error": "Long-term memory not enabled"
                    }
                else:
                    memories = self.memory.read_long_term(
                        user_id="default",
                        memory_type="action",
                        limit=limit * 2  # Get more to filter
                    )

                    # Filter by date and action type
                    actions = []
                    for mem in memories:
                        created_at = mem.get("created_at")
                        if created_at and created_at >= start_date:
                            content = mem.get("content", {})
                            action = content.get("action")

                            # Filter by action type
                            if action_type == "all" or action == action_type:
                                actions.append({
                                    "action": action,
                                    "task": content.get("task", {}).get("title", "Unknown"),
                                    "project": content.get("project"),
                                    "timestamp": content.get("timestamp"),
                                    "note": content.get("note", "")[:100] if content.get("note") else None
                                })

                            if len(actions) >= limit:
                                break

                    result = {
                        "success": True,
                        "time_range": time_range,
                        "count": len(actions),
                        "actions": actions
                    }

            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                error_msg = f"Unknown tool: {tool_name}"

            # Record significant actions to long-term memory if enabled
            if self.optimizations.get("long_term_memory") and result and result.get("success"):
                # Record task completions
                if tool_name == "complete_task" and result.get("task"):
                    self._record_to_long_term(
                        action="completed",
                        content={
                            "task": {
                                "id": result["task"].get("_id"),
                                "title": result["task"].get("title")
                            },
                            "project": result.get("project_name")
                        }
                    )

                # Record task starts
                elif tool_name == "start_task" and result.get("task"):
                    self._record_to_long_term(
                        action="started",
                        content={
                            "task": {
                                "id": result["task"].get("_id"),
                                "title": result["task"].get("title")
                            },
                            "project": result.get("project_name")
                        }
                    )

                # Record task creations
                elif tool_name == "create_task" and result.get("task"):
                    self._record_to_long_term(
                        action="created",
                        content={
                            "task": {
                                "id": result["task"].get("_id"),
                                "title": result["task"].get("title")
                            },
                            "project": result.get("project_name")
                        }
                    )

                # Record notes added
                elif tool_name == "add_note_to_task":
                    self._record_to_long_term(
                        action="noted",
                        content={
                            "task": {
                                "id": tool_input.get("task_id")
                            },
                            "note": tool_input.get("note", "")[:100]  # Truncate
                        }
                    )

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            error_msg = str(e)
            result = {"success": False, "error": str(e)}

        finally:
            # Always calculate duration, even on error
            duration_ms = int((time.time() - start_time) * 1000)

            # Use new summarize method for consistent output summary
            output_summary = self._summarize_output(result)

            # Capture latency breakdown from agents
            breakdown = {}

            # Check if retrieval agent has timings
            if hasattr(self.retrieval_agent, 'last_query_timings') and self.retrieval_agent.last_query_timings:
                breakdown.update(self.retrieval_agent.last_query_timings)
                self.retrieval_agent.last_query_timings = {}  # Reset

            # Check if worklog agent has timings
            if hasattr(self.worklog_agent, 'last_query_timings') and self.worklog_agent.last_query_timings:
                breakdown.update(self.worklog_agent.last_query_timings)
                self.worklog_agent.last_query_timings = {}  # Reset

            # Calculate processing overhead (Python, serialization, etc.)
            if breakdown:
                known_time = sum(breakdown.values())
                processing_overhead = max(0, duration_ms - known_time)
                if processing_overhead > 0:
                    breakdown["processing"] = processing_overhead

            # Build debug info (don't include full result to avoid serialization issues)
            debug_info = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "duration_ms": duration_ms,
                "output_summary": output_summary,
                "success": result.get("success", False) if result else False,
                "error": error_msg
            }

            # Also append to current turn if we're tracking it
            if self.current_turn is not None:
                self.current_turn["tool_calls"].append({
                    "name": tool_name,
                    "input": tool_input,
                    "output": output_summary,
                    "duration_ms": duration_ms,
                    "breakdown": breakdown if breakdown else None,  # Include latency breakdown
                    "success": result.get("success", False) if result else False,
                    "error": error_msg
                })

            return result, debug_info

    def process(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, input_type: str = "text", turn_number: int = 1, optimizations: Optional[Dict[str, bool]] = None, return_debug: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Process a user message using Claude's native tool use.

        Voice and text inputs are processed identically - Claude decides which tools to call.

        Args:
            user_message: User's message (voice transcript or text)
            conversation_history: Optional conversation history
            input_type: Type of input ("text" or "voice") - for logging only
            turn_number: The turn number for this request (for debug tracking)
            optimizations: Optional dict of optimization toggles (compress_results, streamlined_prompt, prompt_caching)
            return_debug: If True, return dict with response and debug info instead of just response string

        Returns:
            If return_debug=False: Agent's response string (default, backwards compatible)
            If return_debug=True: Dict with {"response": str, "debug": {...}}
        """
        # Store optimizations for use throughout the process
        self.optimizations = optimizations or {}

        # Get system prompt based on streamlined toggle
        streamlined = self.optimizations.get("streamlined_prompt", True)
        system_prompt = get_system_prompt(streamlined)
        prompt_stats = get_prompt_stats(streamlined)

        # Get prompt caching setting
        cache_prompts = self.optimizations.get("prompt_caching", True)

        logger.info("=" * 80)
        logger.info("=== NEW REQUEST ===")
        logger.info(f"Input type: {input_type}")
        logger.info(f"User message: {user_message[:200]}...")
        logger.info(f"History length: {len(conversation_history) if conversation_history else 0}")
        logger.info(f"📊 Prompt: {prompt_stats['type']} ({prompt_stats['word_count']} words, ~{int(prompt_stats['estimated_tokens'])} tokens)")
        logger.info(f"📊 Caching: {'enabled' if cache_prompts else 'disabled'}")

        # Create new turn for debug tracking
        self.current_turn = {
            "turn": turn_number,
            "user_input": user_message[:100] + "..." if len(user_message) > 100 else user_message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tool_calls": [],
            "llm_calls": [],  # Track LLM thinking time
            "total_duration_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cache_hit": False,
            "tools_called": []
        }

        # Reset old debug info (kept for backwards compatibility)
        self.last_debug_info = []

        # Build messages - SAME PATH FOR VOICE AND TEXT
        # CRITICAL: Serialize conversation history to ensure datetime/ObjectId objects are converted to strings
        # Otherwise the Anthropic API will fail with "Object of type datetime is not JSON serializable"
        messages = convert_objectids_to_str(conversation_history.copy()) if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        # Get available tools based on settings
        available_tools = self._get_available_tools()

        # Use Claude's native tool use - TIME THIS CALL
        import time
        logger.info("=" * 80)
        logger.info("=== INITIAL LLM CALL (DECIDE ACTION) ===")
        logger.info(f"📊 Turn {turn_number}")
        logger.info(f"📊 Sending {len(available_tools)} tools to LLM")
        logger.info(f"📊 Tool names: {', '.join([t['name'] for t in available_tools])}")
        logger.info(f"📊 Messages count: {len(messages)}")
        logger.info(f"📊 Last message roles: {[m.get('role') for m in messages[-5:]]}")
        logger.info(f"📊 Last message preview: {str(messages[-1].get('content', ''))[:150]}...")
        logger.info(f"📊 System prompt length: {len(system_prompt)} chars")
        logger.info("=" * 80)

        llm_start = time.time()
        response = self.llm.generate_with_tools(
            messages=messages,
            tools=available_tools,
            system=system_prompt,
            max_tokens=4096,
            temperature=0.3,
            cache_prompts=cache_prompts
        )
        llm_duration = int((time.time() - llm_start) * 1000)

        # Capture token usage
        if hasattr(response, 'usage'):
            self.current_turn["tokens_in"] += getattr(response.usage, 'input_tokens', 0)
            self.current_turn["tokens_out"] += getattr(response.usage, 'output_tokens', 0)
            cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
            if cache_read > 0:
                self.current_turn["cache_hit"] = True

        # DEBUG: Check response
        logger.info("=" * 80)
        logger.info("=== INITIAL LLM RESPONSE ===")
        logger.info(f"📊 Stop reason: {response.stop_reason}")
        logger.info(f"📊 Content blocks: {len(response.content)}")
        logger.info(f"📊 Content types: {[b.type for b in response.content]}")

        tool_use_blocks = [b for b in response.content if hasattr(b, 'type') and b.type == 'tool_use']
        logger.info(f"📊 Tool use blocks: {len(tool_use_blocks)}")

        if tool_use_blocks:
            logger.info(f"📊 ✅ Tools called: {[b.name for b in tool_use_blocks]}")
        else:
            # Log why no tool was called - check the text response
            text_blocks = [b.text for b in response.content if hasattr(b, 'text')]
            if text_blocks:
                logger.warning(f"📊 ❌ NO TOOLS CALLED - LLM responded with text only")
                logger.warning(f"📊 Text response: {text_blocks[0][:300]}...")
            logger.warning(f"📊 ⚠️  CRITICAL: LLM should call tools but didn't!")
        logger.info("=" * 80)

        # Track the initial LLM call
        self.current_turn["llm_calls"].append({
            "purpose": "decide_action",
            "duration_ms": llm_duration
        })
        logger.info(f"LLM decide_action took {llm_duration}ms")

        # Handle tool calls in a loop until Claude is done
        max_iterations = 10
        iteration = 0

        while response.stop_reason == "tool_use" and iteration < max_iterations:
            iteration += 1
            logger.info(f"Tool use iteration {iteration}")

            # Extract tool calls from response
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    logger.info(f"Tool call: {tool_name}")
                    logger.debug(f"Tool input: {tool_input}")

                    # Execute the tool and get result + debug info
                    result, debug_info = self._execute_tool(tool_name, tool_input)

                    # Add iteration number to debug info
                    debug_info["iteration"] = iteration
                    debug_info["index"] = len(self.last_debug_info) + 1

                    # Store debug info
                    self.last_debug_info.append(debug_info)

                    # Apply compression if enabled (before serialization)
                    compress = self.optimizations.get("compress_results", True)
                    compressed_result = compress_tool_result(tool_name, result, compress=compress)

                    # Add tool result (convert ObjectIds to strings first)
                    serializable_result = convert_objectids_to_str(compressed_result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(serializable_result)
                    })

            # Add assistant message with tool use
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Add tool results
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Get next response from Claude - TIME THIS CALL
            logger.info("=" * 80)
            logger.info(f"=== FOLLOW-UP LLM CALL (ITERATION {iteration}) ===")
            logger.info(f"📊 Sending tool results back to LLM")
            logger.info(f"📊 Sending {len(available_tools)} tools to LLM")
            logger.info(f"📊 Messages count: {len(messages)}")
            logger.info(f"📊 Last message roles: {[m.get('role') for m in messages[-5:]]}")
            logger.info(f"📊 Tool results count: {len(tool_results)}")
            logger.info("=" * 80)

            llm_start = time.time()
            response = self.llm.generate_with_tools(
                messages=messages,
                tools=available_tools,
                system=system_prompt,
                max_tokens=4096,
                temperature=0.3,
                cache_prompts=cache_prompts
            )
            llm_duration = int((time.time() - llm_start) * 1000)

            # Capture token usage
            if hasattr(response, 'usage'):
                self.current_turn["tokens_in"] += getattr(response.usage, 'input_tokens', 0)
                self.current_turn["tokens_out"] += getattr(response.usage, 'output_tokens', 0)
                cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
                if cache_read > 0:
                    self.current_turn["cache_hit"] = True

            logger.info("=" * 80)
            logger.info(f"=== FOLLOW-UP LLM RESPONSE (ITERATION {iteration}) ===")
            logger.info(f"📊 Stop reason: {response.stop_reason}")
            logger.info(f"📊 Content blocks: {len(response.content)}")
            logger.info(f"📊 Content types: {[b.type for b in response.content]}")
            logger.info("=" * 80)

            # Track this LLM call
            self.current_turn["llm_calls"].append({
                "purpose": "format_response",
                "duration_ms": llm_duration
            })
            logger.info(f"LLM format_response took {llm_duration}ms")

        # Extract final text response
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_text += content_block.text

        # Calculate total duration for this turn (LLM + tools)
        if self.current_turn is not None:
            # Sum tool time
            tool_time = sum(tc["duration_ms"] for tc in self.current_turn["tool_calls"])

            # Sum LLM time
            llm_time = sum(lc["duration_ms"] for lc in self.current_turn["llm_calls"])

            # Total = LLM + tools
            self.current_turn["llm_time_ms"] = llm_time
            self.current_turn["total_duration_ms"] = tool_time + llm_time

            logger.info(f"Turn complete: LLM={llm_time}ms, Tools={tool_time}ms, Total={self.current_turn['total_duration_ms']}ms")

        logger.info("Request processing complete")
        logger.info("=" * 80)

        # Return debug info if requested (for evals), otherwise just the response text
        if return_debug:
            # Aggregate timing breakdown across all tool calls
            embedding_time = 0
            mongodb_time = 0
            processing_time = 0

            for tool_call in self.current_turn.get("tool_calls", []):
                breakdown = tool_call.get("breakdown")
                if breakdown:
                    embedding_time += breakdown.get("embedding_generation", 0)
                    mongodb_time += breakdown.get("mongodb_query", 0)
                    processing_time += breakdown.get("processing", 0)

            return {
                "response": final_text.strip(),
                "debug": {
                    "tokens_in": self.current_turn.get("tokens_in", 0),
                    "tokens_out": self.current_turn.get("tokens_out", 0),
                    "llm_time_ms": self.current_turn.get("llm_time_ms", 0),
                    "tool_time_ms": sum(tc["duration_ms"] for tc in self.current_turn.get("tool_calls", [])),
                    "cache_hit": self.current_turn.get("cache_hit", False),
                    "tools_called": [tc["name"] for tc in self.current_turn.get("tool_calls", [])],
                    "embedding_time_ms": embedding_time,
                    "mongodb_time_ms": mongodb_time,
                    "processing_time_ms": processing_time
                }
            }
        else:
            return final_text.strip()


# Global coordinator instance with memory manager
try:
    from memory import MemoryManager
    from shared.db import MongoDB
    from shared.embeddings import embed_query

    # Create memory manager with embedding function
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Use embed_query function for embeddings
    memory_manager = MemoryManager(
        db=db,
        embedding_fn=embed_query
    )

    coordinator = CoordinatorAgent(memory_manager=memory_manager)
    logger.info("✅ Coordinator initialized with memory manager")
except Exception as e:
    logger.warning(f"⚠️  Failed to initialize memory manager: {e}")
    logger.warning("Coordinator running without memory support")
    coordinator = CoordinatorAgent(memory_manager=None)
