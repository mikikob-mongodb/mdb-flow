"""Streamlit Chat UI for Flow Companion."""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

# Import the coordinator agent
from agents.coordinator import coordinator
from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION
from shared.models import Task, Project
from utils.audio import transcribe_audio


# Slash command parsing and execution
def parse_slash_command(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse slash commands, return None if not a command."""
    if not user_input.startswith("/"):
        return None

    parts = user_input[1:].split()
    if not parts:
        return None

    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Parse key:value arguments
    kwargs = {}
    positional = []
    for arg in args:
        if ":" in arg:
            key, value = arg.split(":", 1)
            kwargs[key] = value
        else:
            positional.append(arg)

    return {
        "command": command,
        "subcommand": positional[0] if positional else None,
        "args": positional[1:] if len(positional) > 1 else [],
        "kwargs": kwargs,
        "raw": user_input
    }


class SlashCommandExecutor:
    """Execute slash commands directly against MongoDB, bypassing LLM."""

    def __init__(self, coordinator_instance):
        self.coordinator = coordinator_instance
        self.retrieval = coordinator_instance.retrieval_agent
        self.worklog = coordinator_instance.worklog_agent

    def execute(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command and return result with timing."""
        start = time.time()

        cmd = parsed_command["command"]
        sub = parsed_command.get("subcommand")
        args = parsed_command.get("args", [])
        kwargs = parsed_command.get("kwargs", {})

        # Check for 'raw' flag
        show_raw = sub == "raw" or "raw" in args or kwargs.get("raw") is not None
        if show_raw:
            # Remove 'raw' from subcommand/args if present
            if sub == "raw":
                sub = None
            if "raw" in args:
                args = [a for a in args if a != "raw"]

        try:
            if cmd == "tasks":
                result = self._handle_tasks(sub, args, kwargs)
            elif cmd == "projects":
                result = self._handle_projects(sub, args, kwargs)
            elif cmd == "search":
                result = self._handle_search(sub, args, kwargs)
            elif cmd == "bench":
                result = self._handle_bench(sub, args, kwargs)
            elif cmd == "help":
                result = self._handle_help(sub)
            else:
                result = {"error": f"Unknown command: /{cmd}"}

            duration_ms = int((time.time() - start) * 1000)
            return {
                "success": "error" not in result,
                "command": parsed_command["raw"],
                "duration_ms": duration_ms,
                "result": result,
                "show_raw": show_raw
            }
        except Exception as e:
            return {
                "success": False,
                "command": parsed_command["raw"],
                "duration_ms": int((time.time() - start) * 1000),
                "error": str(e),
                "show_raw": show_raw
            }

    def _handle_tasks(self, sub, args, kwargs):
        """Handle /tasks commands with project name resolution."""
        from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION
        from bson import ObjectId
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"=== /tasks command ===")
        logger.info(f"sub: {sub}, args: {args}, kwargs: {kwargs}")

        # Handle search subcommand FIRST
        if sub == "search" and args:
            query = " ".join(args)
            logger.info(f"Searching tasks for: {query}")
            limit = int(kwargs.get("limit", 10))
            results = self.retrieval.hybrid_search_tasks(query, limit)
            logger.info(f"Search returned {len(results)} tasks")
            # Enrich with project names
            return self._enrich_tasks_with_project_names(results)

        # Handle completed:timeframe pattern
        if kwargs.get("completed"):
            timeframe = kwargs["completed"]
            logger.info(f"Getting tasks completed {timeframe}")
            return self._get_tasks_by_activity_type("completed", timeframe)

        # Handle temporal subcommands
        if sub == "today":
            logger.info("Getting tasks with activity today")
            return self._get_temporal_tasks("today")
        elif sub == "yesterday":
            logger.info("Getting tasks with activity yesterday")
            return self._get_temporal_tasks("yesterday")
        elif sub == "week":
            logger.info("Getting tasks with activity this week")
            return self._get_temporal_tasks("week")
        elif sub == "stale":
            logger.info("Getting stale tasks (in_progress > 7 days)")
            return self._get_stale_tasks()
        else:
            # Regular task list with filters and $lookup for project names
            # Build match query from kwargs
            match_query = {}

            # Status filter
            if kwargs.get("status"):
                match_query["status"] = kwargs["status"]
                logger.info(f"Filtering by status: {kwargs['status']}")

            # Priority filter
            if kwargs.get("priority"):
                match_query["priority"] = kwargs["priority"]
                logger.info(f"Filtering by priority: {kwargs['priority']}")

            # Project filter - need to resolve project name to project_id
            if kwargs.get("project"):
                project_name = kwargs["project"]
                logger.info(f"Looking up project: {project_name}")

                projects_collection = get_collection(PROJECTS_COLLECTION)
                project_doc = projects_collection.find_one(
                    {"name": {"$regex": project_name, "$options": "i"}},
                    {"_id": 1}
                )

                if project_doc:
                    match_query["project_id"] = project_doc["_id"]
                    logger.info(f"Found project_id: {project_doc['_id']}")
                else:
                    logger.warning(f"Project '{project_name}' not found")
                    return {"error": f"Project '{project_name}' not found"}

            logger.info(f"MongoDB match query: {match_query}")

            # Build aggregation pipeline with $lookup to get project names
            pipeline = []

            # Add match filter if any filters provided
            if match_query:
                pipeline.append({"$match": match_query})

            # Join with projects collection
            pipeline.extend([
                {
                    "$lookup": {
                        "from": "projects",
                        "localField": "project_id",
                        "foreignField": "_id",
                        "as": "project"
                    }
                },
                {
                    "$addFields": {
                        "project_name": {"$arrayElemAt": ["$project.name", 0]}
                    }
                },
                {
                    "$project": {
                        "embedding": 0,
                        "project": 0  # Remove joined array, keep just project_name
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$limit": 50}
            ])

            tasks_collection = get_collection(TASKS_COLLECTION)
            tasks = list(tasks_collection.aggregate(pipeline))

            logger.info(f"Query returned {len(tasks)} tasks")

            # Convert ObjectIds to strings for JSON serialization
            for task in tasks:
                if task.get("_id"):
                    task["_id"] = str(task["_id"])
                if task.get("project_id"):
                    task["project_id"] = str(task["project_id"])

            return tasks

        # For time-based queries, enrich with project names
        return self._enrich_tasks_with_project_names(tasks)

    def _get_temporal_tasks(self, timeframe):
        """Get tasks with activity in a specific timeframe."""
        from shared.db import get_collection, TASKS_COLLECTION
        import logging

        logger = logging.getLogger(__name__)
        now = datetime.utcnow()

        if timeframe == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif timeframe == "yesterday":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "week":
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        else:
            start = now - timedelta(days=7)
            end = now

        logger.info(f"Temporal query: {timeframe}, Start: {start}, End: {end}")

        # Query tasks with activity in the time range
        query = {
            "activity_log": {
                "$elemMatch": {
                    "timestamp": {"$gte": start, "$lte": end}
                }
            }
        }

        logger.info(f"MongoDB query: {query}")

        tasks_collection = get_collection(TASKS_COLLECTION)
        tasks = list(tasks_collection.aggregate([
            {"$match": query},
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "project_id",
                    "foreignField": "_id",
                    "as": "project"
                }
            },
            {
                "$addFields": {
                    "project_name": {"$arrayElemAt": ["$project.name", 0]}
                }
            },
            {
                "$project": {
                    "embedding": 0,
                    "project": 0
                }
            },
            {"$sort": {"created_at": -1}},
            {"$limit": 50}
        ]))

        logger.info(f"Query returned {len(tasks)} tasks")

        # Convert ObjectIds to strings
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        return tasks

    def _get_tasks_by_activity_type(self, activity_type, timeframe):
        """Get tasks by activity type (completed, started, etc.) in a timeframe."""
        from shared.db import get_collection, TASKS_COLLECTION
        import logging

        logger = logging.getLogger(__name__)
        now = datetime.utcnow()

        if timeframe == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "yesterday":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "this_week":
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now - timedelta(days=7)  # Default to last 7 days

        logger.info(f"Getting tasks by activity: {activity_type} {timeframe}, Start: {start}")

        query = {
            "activity_log": {
                "$elemMatch": {
                    "action": activity_type,
                    "timestamp": {"$gte": start}
                }
            }
        }

        logger.info(f"MongoDB query: {query}")

        tasks_collection = get_collection(TASKS_COLLECTION)
        tasks = list(tasks_collection.aggregate([
            {"$match": query},
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "project_id",
                    "foreignField": "_id",
                    "as": "project"
                }
            },
            {
                "$addFields": {
                    "project_name": {"$arrayElemAt": ["$project.name", 0]}
                }
            },
            {
                "$project": {
                    "embedding": 0,
                    "project": 0
                }
            },
            {"$sort": {"created_at": -1}},
            {"$limit": 50}
        ]))

        logger.info(f"Query returned {len(tasks)} tasks")

        # Convert ObjectIds to strings
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        return tasks

    def _get_stale_tasks(self):
        """Get stale tasks (in_progress for more than 7 days)."""
        from shared.db import get_collection, TASKS_COLLECTION
        import logging

        logger = logging.getLogger(__name__)
        now = datetime.utcnow()
        stale_threshold = now - timedelta(days=7)

        logger.info(f"Getting stale tasks (in_progress before {stale_threshold})")

        query = {
            "status": "in_progress",
            "updated_at": {"$lt": stale_threshold}
        }

        logger.info(f"MongoDB query: {query}")

        tasks_collection = get_collection(TASKS_COLLECTION)
        tasks = list(tasks_collection.aggregate([
            {"$match": query},
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "project_id",
                    "foreignField": "_id",
                    "as": "project"
                }
            },
            {
                "$addFields": {
                    "project_name": {"$arrayElemAt": ["$project.name", 0]}
                }
            },
            {
                "$project": {
                    "embedding": 0,
                    "project": 0
                }
            },
            {"$sort": {"updated_at": 1}},
            {"$limit": 50}
        ]))

        logger.info(f"Query returned {len(tasks)} stale tasks")

        # Convert ObjectIds to strings
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        return tasks

    def _enrich_tasks_with_project_names(self, tasks):
        """Enrich tasks with project names by looking up project_id."""
        if not tasks:
            return tasks

        from shared.db import get_collection, PROJECTS_COLLECTION

        # Build project lookup dict
        project_ids = [task.get("project_id") for task in tasks if task.get("project_id")]
        if not project_ids:
            # No projects to lookup, just add "-" for all tasks
            for task in tasks:
                task["project_name"] = "-"
            return tasks

        # Convert string IDs to ObjectIds if needed
        from bson import ObjectId
        object_ids = []
        for pid in project_ids:
            if isinstance(pid, str):
                try:
                    object_ids.append(ObjectId(pid))
                except:
                    object_ids.append(pid)
            else:
                object_ids.append(pid)

        # Fetch projects
        projects_collection = get_collection(PROJECTS_COLLECTION)
        projects = list(projects_collection.find(
            {"_id": {"$in": object_ids}},
            {"_id": 1, "name": 1}
        ))

        # Create lookup dict (support both ObjectId and string keys)
        project_lookup = {}
        for p in projects:
            project_lookup[str(p["_id"])] = p["name"]
            project_lookup[p["_id"]] = p["name"]

        # Enrich tasks with project names
        for task in tasks:
            pid = task.get("project_id")
            if pid:
                task["project_name"] = project_lookup.get(str(pid)) or project_lookup.get(pid) or "-"
            else:
                task["project_name"] = "-"

        return tasks

    def _handle_projects(self, sub, args, kwargs):
        """Handle /projects commands with task counts."""
        from shared.db import get_collection, PROJECTS_COLLECTION
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"=== /projects command ===")
        logger.info(f"sub: {sub}, args: {args}, kwargs: {kwargs}")

        # Handle search subcommand
        if sub == "search" and args:
            query = " ".join(args)
            logger.info(f"Searching projects for: {query}")
            limit = int(kwargs.get("limit", 5))

            # Use hybrid search
            results = self.retrieval.hybrid_search_projects(query, limit)
            logger.info(f"Search returned {len(results)} projects")

            # Enrich with task counts
            return self._enrich_projects_with_task_counts(results)

        # Handle /projects <name> - Get specific project with its tasks
        if sub and not args:
            project_name = sub
            logger.info(f"Getting specific project: {project_name}")
            return self._get_project_detail(project_name)

        # Regular project list with task counts via aggregation
        # Build aggregation pipeline with $lookup to get task counts
        pipeline = [
            {
                "$lookup": {
                    "from": "tasks",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "tasks"
                }
            },
            {
                "$addFields": {
                    "todo_count": {
                        "$size": {
                            "$filter": {
                                "input": "$tasks",
                                "cond": {"$eq": ["$$this.status", "todo"]}
                            }
                        }
                    },
                    "in_progress_count": {
                        "$size": {
                            "$filter": {
                                "input": "$tasks",
                                "cond": {"$eq": ["$$this.status", "in_progress"]}
                            }
                        }
                    },
                    "done_count": {
                        "$size": {
                            "$filter": {
                                "input": "$tasks",
                                "cond": {"$eq": ["$$this.status", "done"]}
                            }
                        }
                    },
                    "total_tasks": {"$size": "$tasks"}
                }
            },
            {
                "$project": {
                    "name": 1,
                    "description": 1,
                    "status": 1,
                    "todo_count": 1,
                    "in_progress_count": 1,
                    "done_count": 1,
                    "total_tasks": 1,
                    "created_at": 1
                }
            },
            {"$sort": {"created_at": -1}},
            {"$limit": 50}
        ]

        projects_collection = get_collection(PROJECTS_COLLECTION)
        projects = list(projects_collection.aggregate(pipeline))

        logger.info(f"Query returned {len(projects)} projects")

        # Convert ObjectIds to strings for JSON serialization
        for project in projects:
            if project.get("_id"):
                project["_id"] = str(project["_id"])

        return projects

    def _enrich_projects_with_task_counts(self, projects):
        """Enrich projects with task counts by looking up tasks."""
        if not projects:
            return projects

        from shared.db import get_collection, TASKS_COLLECTION
        from bson import ObjectId

        # Build project ID list
        project_ids = []
        for project in projects:
            pid = project.get("_id")
            if isinstance(pid, str):
                try:
                    project_ids.append(ObjectId(pid))
                except:
                    project_ids.append(pid)
            elif pid:
                project_ids.append(pid)

        if not project_ids:
            # No projects to enrich
            for project in projects:
                project["todo_count"] = 0
                project["in_progress_count"] = 0
                project["done_count"] = 0
                project["total_tasks"] = 0
            return projects

        # Fetch all tasks for these projects
        tasks_collection = get_collection(TASKS_COLLECTION)
        tasks = list(tasks_collection.find(
            {"project_id": {"$in": project_ids}},
            {"project_id": 1, "status": 1}
        ))

        # Count tasks by project and status
        task_counts = {}
        for task in tasks:
            pid = str(task.get("project_id"))
            if pid not in task_counts:
                task_counts[pid] = {"todo": 0, "in_progress": 0, "done": 0}

            status = task.get("status", "todo")
            if status in task_counts[pid]:
                task_counts[pid][status] += 1

        # Enrich projects with counts
        for project in projects:
            pid = str(project.get("_id"))
            counts = task_counts.get(pid, {"todo": 0, "in_progress": 0, "done": 0})

            project["todo_count"] = counts["todo"]
            project["in_progress_count"] = counts["in_progress"]
            project["done_count"] = counts["done"]
            project["total_tasks"] = sum(counts.values())

        return projects

    def _get_project_detail(self, project_name):
        """Get a single project with its tasks."""
        from shared.db import get_collection, PROJECTS_COLLECTION, TASKS_COLLECTION
        from bson import ObjectId
        import logging

        logger = logging.getLogger(__name__)

        # Find the project (case-insensitive exact match first)
        projects_collection = get_collection(PROJECTS_COLLECTION)
        project = projects_collection.find_one(
            {"name": {"$regex": f"^{project_name}$", "$options": "i"}},
            {"embedding": 0}
        )

        if not project:
            # Try partial match
            logger.info(f"Exact match not found, trying partial match")
            project = projects_collection.find_one(
                {"name": {"$regex": project_name, "$options": "i"}},
                {"embedding": 0}
            )

        if not project:
            logger.warning(f"Project '{project_name}' not found")
            return {"error": f"Project '{project_name}' not found"}

        logger.info(f"Found project: {project.get('name')}")

        # Get tasks for this project with project_name field
        tasks_collection = get_collection(TASKS_COLLECTION)
        tasks = list(tasks_collection.aggregate([
            {"$match": {"project_id": project["_id"]}},
            {
                "$addFields": {
                    "project_name": project.get("name")
                }
            },
            {
                "$project": {
                    "embedding": 0
                }
            },
            {"$sort": {"status": 1, "created_at": -1}},
            {"$limit": 100}
        ]))

        logger.info(f"Found {len(tasks)} tasks for project")

        # Convert ObjectIds to strings
        project["_id"] = str(project["_id"])
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        # Count tasks by status
        todo_count = len([t for t in tasks if t.get("status") == "todo"])
        in_progress_count = len([t for t in tasks if t.get("status") == "in_progress"])
        done_count = len([t for t in tasks if t.get("status") == "done"])

        return {
            "type": "project_detail",
            "project": project,
            "tasks": tasks,
            "task_count": len(tasks),
            "todo_count": todo_count,
            "in_progress_count": in_progress_count,
            "done_count": done_count
        }

    def _handle_search(self, sub, args, kwargs):
        """Handle /search commands."""
        if not args:
            return {"error": "Usage: /search <query>"}

        query = " ".join(args)
        limit = int(kwargs.get("limit", 5))

        if sub == "tasks" or sub is None:
            results = self.retrieval.hybrid_search_tasks(query, limit)
            # Enrich with project names
            return self._enrich_tasks_with_project_names(results)
        elif sub == "projects":
            return self.retrieval.hybrid_search_projects(query, limit)
        else:
            return {"error": f"Unknown search type: {sub}"}

    def _handle_bench(self, sub, args, kwargs):
        """Handle /bench commands - run performance benchmarks."""
        runs = int(kwargs.get("runs", 10))

        if sub == "get":
            return self._benchmark(lambda: self.worklog._list_tasks(limit=50), runs, "get_tasks")
        elif sub == "search":
            query = " ".join(args) if args else "debugging"
            return self._benchmark(lambda: self.retrieval.hybrid_search_tasks(query, 5), runs, f"search_tasks({query})")
        elif sub == "all":
            return {
                "get_tasks": self._benchmark(lambda: self.worklog._list_tasks(limit=50), runs, "get_tasks"),
                "get_projects": self._benchmark(lambda: self.worklog._list_projects(limit=50), runs, "get_projects"),
                "search_tasks": self._benchmark(lambda: self.retrieval.hybrid_search_tasks("debugging", 5), runs, "search_tasks"),
            }
        else:
            return {"error": "Usage: /bench <get|search|all> [runs:N]"}

    def _benchmark(self, fn, runs, name):
        """Run a function multiple times and return timing statistics."""
        times = []
        for _ in range(runs):
            start = time.time()
            fn()
            times.append((time.time() - start) * 1000)

        times.sort()
        return {
            "operation": name,
            "runs": runs,
            "avg_ms": round(sum(times) / len(times), 1),
            "min_ms": round(min(times), 1),
            "max_ms": round(max(times), 1),
            "p50_ms": round(times[len(times) // 2], 1),
            "p95_ms": round(times[int(len(times) * 0.95)], 1) if runs >= 10 else None,
            "p99_ms": round(times[int(len(times) * 0.99)], 1) if runs >= 100 else None
        }

    def _handle_help(self, sub):
        """Show help for slash commands."""
        return {
            "help_text": """**Flow Companion Slash Commands**

**TASK QUERIES**
• `/tasks` - List all tasks (table format)
• `/tasks status:<status>` - Filter by status (todo, in_progress, done)
• `/tasks priority:<level>` - Filter by priority (low, medium, high)
• `/tasks project:<name>` - Filter by project name (case-insensitive)
• `/tasks status:in_progress priority:high` - Multiple filters (combined with AND)
• `/tasks search <query>` - Hybrid search for tasks (semantic + text)
• `/tasks today` - Tasks with activity today
• `/tasks yesterday` - Tasks with activity yesterday
• `/tasks week` - Tasks with activity this week
• `/tasks stale` - In-progress tasks older than 7 days
• `/tasks completed:today` - Tasks completed today
• `/tasks completed:this_week` - Tasks completed this week

**PROJECT QUERIES**
• `/projects` - List all projects with task counts
• `/projects <name>` - Show specific project with all its tasks
• `/projects search <query>` - Search projects by name/description

**SEARCH**
• `/search <query>` - Hybrid search for tasks (semantic + text)
• `/search projects <query>` - Search projects
• `/search limit:10 bug` - Limit results (default: 5)

**BENCHMARKS**
• `/bench get` - Benchmark get_tasks operation
• `/bench search <query>` - Benchmark search with specific query
• `/bench all` - Benchmark all operations
• `/bench get runs:100` - Custom number of runs (default: 10)

**UTILITIES**
• `/help` - Show this help
• `<command> raw` - Show JSON output instead of table (e.g., `/tasks raw`)

**Examples:**
• `/tasks project:AgentOps` - All tasks in AgentOps project
• `/tasks project:AgentOps status:todo` - Todo tasks in AgentOps
• `/tasks priority:high status:in_progress` - High priority tasks in progress
• `/tasks search debugging` - Search for tasks about debugging
• `/tasks completed:today` - Tasks completed today
• `/projects AgentOps` - Show AgentOps project with all its tasks
• `/projects search memory` - Search for projects about memory

**Note:** Slash commands bypass the LLM and execute directly against MongoDB for instant results (<100ms typical)."""
        }


# Page configuration
st.set_page_config(
    page_title="Flow Companion",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "coordinator" not in st.session_state:
        st.session_state.coordinator = coordinator

    if "slash_executor" not in st.session_state:
        st.session_state.slash_executor = SlashCommandExecutor(coordinator)

    if "last_audio_bytes" not in st.session_state:
        st.session_state.last_audio_bytes = None

    if "last_debug_info" not in st.session_state:
        st.session_state.last_debug_info = []

    if "debug_history" not in st.session_state:
        st.session_state.debug_history = []


def get_all_projects_with_tasks() -> List[Dict[str, Any]]:
    """
    Get all projects with their associated tasks.

    Returns:
        List of projects with tasks
    """
    projects_collection = get_collection(PROJECTS_COLLECTION)
    tasks_collection = get_collection(TASKS_COLLECTION)

    # Get all active projects
    projects_cursor = projects_collection.find(
        {"status": "active"}
    ).sort("last_activity", -1)

    projects_with_tasks = []

    for project_doc in projects_cursor:
        project = Project(**project_doc)

        # Get tasks for this project
        tasks_cursor = tasks_collection.find(
            {"project_id": project.id}
        ).sort([("status", 1), ("created_at", -1)])

        tasks = [Task(**task_doc) for task_doc in tasks_cursor]

        projects_with_tasks.append({
            "project": project,
            "tasks": tasks
        })

    # Also get tasks without a project
    orphan_tasks_cursor = tasks_collection.find(
        {"project_id": None}
    ).sort([("status", 1), ("created_at", -1)])

    orphan_tasks = [Task(**task_doc) for task_doc in orphan_tasks_cursor]

    if orphan_tasks:
        projects_with_tasks.append({
            "project": None,
            "tasks": orphan_tasks
        })

    return projects_with_tasks


def get_status_icon(status: str) -> str:
    """Get icon for task status."""
    icons = {
        "todo": "○",
        "in_progress": "◐",
        "done": "✓"
    }
    return icons.get(status, "○")


def get_priority_badge(priority: str) -> str:
    """Get colored badge for priority."""
    if priority == "high":
        return "🔴"
    elif priority == "medium":
        return "🟡"
    elif priority == "low":
        return "🟢"
    return ""


def render_task_list():
    """Render the task list in the sidebar."""
    st.sidebar.title("📋 Tasks & Projects")

    # Get all projects with tasks
    projects_with_tasks = get_all_projects_with_tasks()

    if not projects_with_tasks:
        st.sidebar.info("No projects or tasks yet. Start by creating one in the chat!")
        return

    # Render each project and its tasks
    for item in projects_with_tasks:
        project = item["project"]
        tasks = item["tasks"]

        # Project header
        if project:
            st.sidebar.markdown(f"### 📁 {project.name}")
            if project.description:
                st.sidebar.caption(project.description)
        else:
            st.sidebar.markdown("### 📝 Unassigned Tasks")

        # Render tasks
        if tasks:
            for task in tasks:
                status_icon = get_status_icon(task.status)
                priority_badge = get_priority_badge(task.priority) if task.priority else ""

                # Task display
                task_text = f"{status_icon} {priority_badge} {task.title}".strip()

                # Use expander for task details
                with st.sidebar.expander(task_text, expanded=False):
                    st.caption(f"**Status:** {task.status}")
                    if task.priority:
                        st.caption(f"**Priority:** {task.priority}")
                    if task.context:
                        st.caption(f"**Context:** {task.context}")
                    if task.notes:
                        st.caption(f"**Notes:** {len(task.notes)}")
                    st.caption(f"**Created:** {task.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if task.last_worked_on:
                        st.caption(f"**Last worked:** {task.last_worked_on.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.sidebar.caption("_No tasks in this project_")

        st.sidebar.divider()

    # Add refresh button
    if st.sidebar.button("🔄 Refresh Tasks", use_container_width=True):
        st.rerun()


def format_tasks_table(tasks, show_raw=False):
    """Format tasks as a markdown table."""
    if not tasks:
        return "No tasks found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Header
    lines = ["| # | Title | Status | Priority | Project | Last Activity |"]
    lines.append("|---|-------|--------|----------|---------|---------------|")

    for i, task in enumerate(tasks, 1):
        title = task.get("title", "Untitled")[:40]
        if len(task.get("title", "")) > 40:
            title += "..."

        status = task.get("status", "-")
        priority = task.get("priority") or "-"
        project = task.get("project_name") or "-"

        # Get last activity timestamp
        activity_log = task.get("activity_log", [])
        if activity_log:
            last = activity_log[-1].get("timestamp")
            if last:
                # Handle both datetime objects and strings
                if hasattr(last, 'strftime'):
                    last_activity = last.strftime("%b %d")
                else:
                    # Parse string if needed
                    last_activity = str(last)[:10]
            else:
                last_activity = "-"
        else:
            last_activity = "-"

        lines.append(f"| {i} | {title} | {status} | {priority} | {project} | {last_activity} |")

    return "\n".join(lines)


def format_projects_table(projects, show_raw=False):
    """Format projects as a markdown table."""
    if not projects:
        return "No projects found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Check if these are search results (have score field)
    is_search_results = len(projects) > 0 and "score" in projects[0]

    if is_search_results:
        # Header for search results
        lines = ["| # | Name | Score | Description | Todo | In Progress | Done | Total |"]
        lines.append("|---|------|-------|-------------|------|-------------|------|-------|")

        for i, project in enumerate(projects, 1):
            name = project.get("name", "Untitled")[:25]
            if len(project.get("name", "")) > 25:
                name += "..."

            score = project.get("score", "-")
            if isinstance(score, float):
                score = f"{score:.2f}"

            description = project.get("description", "")[:30]
            if len(project.get("description", "")) > 30:
                description += "..."
            if not description:
                description = "-"

            # Get task counts
            tasks_todo = project.get("todo_count", 0)
            tasks_in_progress = project.get("in_progress_count", 0)
            tasks_done = project.get("done_count", 0)
            tasks_total = project.get("total_tasks", 0)

            lines.append(f"| {i} | {name} | {score} | {description} | {tasks_todo} | {tasks_in_progress} | {tasks_done} | {tasks_total} |")
    else:
        # Header for regular list
        lines = ["| # | Name | Description | Todo | In Progress | Done | Total |"]
        lines.append("|---|------|-------------|------|-------------|------|-------|")

        for i, project in enumerate(projects, 1):
            name = project.get("name", "Untitled")[:30]
            if len(project.get("name", "")) > 30:
                name += "..."

            description = project.get("description", "")[:40]
            if len(project.get("description", "")) > 40:
                description += "..."
            if not description:
                description = "-"

            # Get task counts from aggregation
            tasks_todo = project.get("todo_count", 0)
            tasks_in_progress = project.get("in_progress_count", 0)
            tasks_done = project.get("done_count", 0)
            tasks_total = project.get("total_tasks", 0)

            lines.append(f"| {i} | {name} | {description} | {tasks_todo} | {tasks_in_progress} | {tasks_done} | {tasks_total} |")

    return "\n".join(lines)


def format_benchmark_table(bench_data, show_raw=False):
    """Format benchmark results as a markdown table."""
    if show_raw:
        return None  # Signal to show JSON instead

    # Single benchmark result
    if "operation" in bench_data:
        lines = ["| Operation | Runs | Avg | Min | Max | P50 | P95 | Status |"]
        lines.append("|-----------|------|-----|-----|-----|-----|-----|--------|")

        p95 = f"{bench_data['p95_ms']}ms" if bench_data.get('p95_ms') else "-"
        runs = bench_data.get('runs', '-')
        lines.append(
            f"| {bench_data['operation']} | {runs} | {bench_data['avg_ms']}ms | {bench_data['min_ms']}ms | "
            f"{bench_data['max_ms']}ms | {bench_data['p50_ms']}ms | {p95} | ✓ |"
        )
        return "\n".join(lines)

    # Multiple benchmark results
    lines = ["| Operation | Runs | Avg | Min | Max | P50 | P95 | Status |"]
    lines.append("|-----------|------|-----|-----|-----|-----|-----|--------|")

    for name, bench in bench_data.items():
        if isinstance(bench, dict) and "operation" in bench:
            p95 = f"{bench['p95_ms']}ms" if bench.get('p95_ms') else "-"
            runs = bench.get('runs', '-')
            lines.append(
                f"| {bench['operation']} | {runs} | {bench['avg_ms']}ms | {bench['min_ms']}ms | "
                f"{bench['max_ms']}ms | {bench['p50_ms']}ms | {p95} | ✓ |"
            )

    return "\n".join(lines)


def format_search_results_table(results, show_raw=False):
    """Format search results as a markdown table."""
    if not results:
        return "No results found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Header
    lines = ["| # | Title | Score | Status | Project | Priority |"]
    lines.append("|---|-------|-------|--------|---------|----------|")

    for i, item in enumerate(results, 1):
        title = item.get("title", "Untitled")[:50]
        if len(item.get("title", "")) > 50:
            title += "..."

        # Score from hybrid search
        score = item.get("score", "-")
        if isinstance(score, float):
            score = f"{score:.2f}"

        status = item.get("status", "-")
        project = item.get("project_name") or "-"
        priority = item.get("priority") or "-"

        lines.append(f"| {i} | {title} | {score} | {status} | {project} | {priority} |")

    return "\n".join(lines)


def render_command_result(result: Dict[str, Any]):
    """Render the result of a slash command execution."""
    if not result.get("success"):
        # Show error
        st.error(f"❌ Command failed: {result.get('error', 'Unknown error')}")
        return

    # Show success banner with timing
    duration = result.get("duration_ms", 0)
    st.success(f"✓ Executed in {duration}ms")

    data = result.get("result", {})
    show_raw = result.get("show_raw", False)

    # Handle different result types
    if isinstance(data, dict) and "error" in data:
        st.error(data["error"])
    elif isinstance(data, dict) and data.get("type") == "project_detail":
        # Project detail view with tasks
        project = data.get("project", {})
        tasks = data.get("tasks", [])

        st.markdown(f"**Project:** {project.get('name', 'Untitled')}")
        if project.get("description"):
            st.markdown(f"*{project.get('description')}*")

        st.markdown(f"**Status:** {data.get('todo_count', 0)} todo • {data.get('in_progress_count', 0)} in progress • {data.get('done_count', 0)} done")
        st.markdown("")

        if tasks:
            st.markdown(f"**Tasks ({len(tasks)}):**")
            table = format_tasks_table(tasks, show_raw)
            if table:
                st.markdown(table)
            else:
                st.json(tasks)
        else:
            st.info("No tasks in this project")
    elif "help_text" in data:
        # Help output - new format
        st.markdown(data["help_text"])
    elif "commands" in data:
        # Help output - legacy format
        st.markdown("**Available Commands:**")
        for cmd in data["commands"]:
            st.markdown(f"**`{cmd['command']}`** - {cmd['description']}")
            if cmd.get("examples"):
                st.caption(f"Examples: {', '.join(f'`{ex}`' for ex in cmd['examples'])}")
        if data.get("note"):
            st.info(data["note"])
    elif isinstance(data, dict) and any(k in data for k in ["operation", "runs", "avg_ms"]):
        # Single benchmark result - format as table
        table = format_benchmark_table(data, show_raw)
        if table:
            st.markdown(table)
        else:
            st.json(data)
    elif isinstance(data, dict) and all(isinstance(v, dict) and "operation" in v for v in data.values()):
        # Multiple benchmark results - format as table
        table = format_benchmark_table(data, show_raw)
        if table:
            st.markdown(table)
        else:
            st.json(data)
    elif isinstance(data, list):
        # List of tasks, projects, or search results
        if len(data) == 0:
            st.info("No results found")
        else:
            # Determine type and format appropriately
            first_item = data[0]

            # Check if it's a search result (has score field)
            if isinstance(first_item, dict) and "score" in first_item:
                table = format_search_results_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} result(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            # Check if it's a task
            elif isinstance(first_item, dict) and "title" in first_item and "status" in first_item:
                table = format_tasks_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} task(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            # Check if it's a project
            elif isinstance(first_item, dict) and "name" in first_item:
                table = format_projects_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} project(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            else:
                # Unknown type - show as JSON
                st.json(data)
    else:
        # Generic result - show as JSON
        st.json(data)


def render_debug_panel():
    """Render the debug panel showing all tool calls grouped by conversation turn."""
    st.markdown("### 🔍 Agent Debug")
    st.caption("Complete trace of all tool calls")

    debug_history = st.session_state.get("debug_history", [])

    if not debug_history:
        st.info("No tool calls yet. Send a message to see the agent's work.")
        return

    # Summary stats at the top
    total_turns = len(debug_history)
    total_calls = sum(len(turn["tool_calls"]) for turn in debug_history)
    total_time = sum(turn["total_duration_ms"] for turn in debug_history)
    st.caption(f"**{total_turns} turns** • **{total_calls} tool calls** • **{total_time}ms total**")

    # Latency breakdown legend
    with st.expander("⏱️ Latency Legend", expanded=False):
        st.markdown("""
        **Component breakdown:**
        - 🔵 **LLM Thinking**: Claude deciding actions and generating responses (typically 500-3000ms)
        - 🟢 **MongoDB Query**: Database read/write operations (typically 50-150ms)
        - 🟡 **Embedding Generation**: Voyage AI API for semantic vectors (typically 200-400ms)
        - ⚪ **Processing**: Python overhead and serialization (typically <50ms)

        *MongoDB is fast! Most latency comes from LLM thinking and external API calls.*
        """)

    # Clear button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.debug_history = []
        st.rerun()

    st.divider()

    # Show turns in chronological order (oldest first, newest last)
    for turn in debug_history:
        # Expand the most recent turn (last in the list)
        is_most_recent = (turn == debug_history[-1])

        # Create expander label with LLM vs Tool breakdown
        user_input_preview = turn["user_input"][:50]
        if len(turn["user_input"]) > 50:
            user_input_preview += "..."

        # Calculate time breakdown
        total_time = turn['total_duration_ms']
        llm_time = turn.get('llm_time_ms', 0)
        tool_time = sum(tc["duration_ms"] for tc in turn["tool_calls"]) if turn["tool_calls"] else 0

        # Calculate percentages (avoid division by zero)
        if total_time > 0:
            llm_pct = int((llm_time / total_time) * 100)
            tool_pct = int((tool_time / total_time) * 100)
        else:
            llm_pct = 0
            tool_pct = 0

        # Build label with breakdown
        expander_label = f"**Turn {turn['turn']}**: {user_input_preview} ({total_time}ms)\n"
        expander_label += f"        🔵 LLM: {llm_time}ms ({llm_pct}%)"

        if tool_time > 0:
            expander_label += f" • 🛠️ Tools: {tool_time}ms ({tool_pct}%)"

        with st.expander(expander_label, expanded=is_most_recent):
            # Show timestamp
            st.caption(f"🕐 {turn['timestamp']}")

            # Show full user input if it was truncated
            if len(turn["user_input"]) > 50:
                st.caption(f"*Full input: {turn['user_input']}*")

            st.markdown("---")

            # Show each tool call
            for i, call in enumerate(turn["tool_calls"], 1):
                st.markdown(f"**Call {i}:** `{call['name']}`")

                # Two-column layout: details on left, timing/status on right
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Input parameters (collapsible)
                    if call["input"]:
                        with st.expander("Input", expanded=False):
                            st.json(call["input"])
                    else:
                        st.caption("*No input*")

                    # Output summary
                    st.caption(f"**Output:** {call['output']}")

                    # Show latency breakdown if available
                    if call.get("breakdown"):
                        breakdown = call["breakdown"]

                        # Calculate total time for percentages
                        total_breakdown_time = sum(breakdown.values())

                        # Determine MongoDB operation type based on tool name
                        tool_name = call["name"]
                        mongodb_op_type_map = {
                            "get_tasks": "find query",
                            "get_projects": "find query",
                            "search_tasks": "$rankFusion hybrid",
                            "search_projects": "$rankFusion hybrid",
                            "get_tasks_by_time": "temporal query ($elemMatch)",
                            "complete_task": "update",
                            "start_task": "update",
                            "add_note_to_task": "update"
                        }
                        mongodb_op_type = mongodb_op_type_map.get(tool_name, "query")

                        # Check if get_tasks/get_projects has filters for more specific labeling
                        if tool_name in ["get_tasks", "get_projects"] and call.get("input"):
                            has_filters = any(v for v in call["input"].values() if v)
                            if has_filters:
                                mongodb_op_type = "filtered find"
                            else:
                                mongodb_op_type = "simple find"

                        # Create detailed component mapping
                        component_info = {
                            "embedding_generation": {"emoji": "🟡", "label": "Embedding (Voyage)"},
                            "mongodb_query": {"emoji": "🟢", "label": f"MongoDB ({mongodb_op_type})"},
                            "processing": {"emoji": "⚪", "label": "Processing (Python)"}
                        }

                        # Build breakdown with percentages
                        st.caption("**Breakdown:**")
                        for component, ms in breakdown.items():
                            info = component_info.get(component, {"emoji": "⚪", "label": component.replace("_", " ").title()})
                            emoji = info["emoji"]
                            label = info["label"]

                            # Calculate percentage
                            if total_breakdown_time > 0:
                                pct = int((ms / total_breakdown_time) * 100)
                            else:
                                pct = 0

                            st.caption(f"{emoji} {label}: {ms}ms ({pct}%)")

                with col2:
                    # Duration
                    st.caption(f"⏱️ {call['duration_ms']}ms")

                    # Success/Error indicator
                    if call["success"]:
                        st.success("✓")
                    else:
                        error_msg = call.get("error", "Failed")
                        st.error(f"✗")
                        if error_msg:
                            st.caption(f"*{error_msg}*")

                # Show arrow between calls (except after last call)
                if i < len(turn["tool_calls"]):
                    st.markdown("↓")
                    st.markdown("")  # Add spacing

            # Show LLM calls (Claude thinking/responding)
            if turn.get("llm_calls"):
                # Add separator if there were tool calls
                if turn["tool_calls"]:
                    st.markdown("---")

                st.markdown("**🔵 LLM Thinking**")

                # Group LLM calls by purpose
                llm_time = turn.get("llm_time_ms", 0)
                num_calls = len(turn["llm_calls"])

                # Two-column layout
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Show breakdown of LLM calls
                    for llm_call in turn["llm_calls"]:
                        purpose = llm_call["purpose"].replace("_", " ").title()
                        duration = llm_call["duration_ms"]
                        st.caption(f"• {purpose}: {duration}ms")

                with col2:
                    st.caption(f"⏱️ {llm_time}ms")
                    st.caption(f"({num_calls} call{'s' if num_calls > 1 else ''})")


def render_chat():
    """Render the chat interface."""
    # Add custom CSS for full-height debug panel
    st.markdown("""
    <style>
    [data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 0;
        height: calc(100vh - 100px);
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create two columns: chat (main) and debug panel (sidebar on right)
    chat_col, debug_col = st.columns([2.5, 1.5])

    with chat_col:
        st.title("💬 Flow Companion")
        st.caption("Your AI-powered task and project management assistant")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Handle different message types
                if message.get("is_command_result"):
                    # Slash command result - render with special formatting
                    render_command_result(message["content"])
                elif message.get("is_slash_command"):
                    # Slash command input - show with terminal style
                    st.markdown(f"⚡ `{message['content']}`")
                    st.caption("*Direct (no LLM)*")
                elif message.get("input_type") == "voice":
                    # Voice input
                    st.markdown(f"🎤 {message['content']}")
                else:
                    # Normal text message
                    st.markdown(message["content"])

        # Chat input
        prompt = st.chat_input("Ask me anything about your tasks or projects...")

        # Voice input
        audio_bytes = st.audio_input("🎤 Or record a voice update")

    with debug_col:
        render_debug_panel()

    # Handle text input
    if prompt:
        # Check if this is a slash command
        parsed_command = parse_slash_command(prompt)

        if parsed_command:
            # Slash command - execute directly without LLM
            # Add command to history
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "input_type": "command",
                "is_slash_command": True
            })

            # Display command with terminal style
            with st.chat_message("user"):
                st.markdown(f"⚡ `{prompt}`")
                st.caption("*Direct (no LLM)*")

            # Execute command and show result
            with st.chat_message("assistant"):
                with st.spinner("Executing..."):
                    result = st.session_state.slash_executor.execute(parsed_command)

                    # Render the result
                    render_command_result(result)

                    # Store result in history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result,
                        "is_command_result": True
                    })

            # Rerun to update the display
            st.rerun()

        else:
            # Normal text input - process through LLM
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "input_type": "text"
            })

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Prepare conversation history for the coordinator
                    history = st.session_state.messages[:-1]  # Exclude the current message

                    # Calculate turn number
                    turn_number = len(st.session_state.debug_history) + 1

                    # Process message through coordinator
                    response = st.session_state.coordinator.process(
                        prompt, history, input_type="text", turn_number=turn_number
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            # Rerun to update the display (including task list)
            st.rerun()

    # Handle audio input
    elif audio_bytes:
        # Get bytes from the audio file
        audio_data = audio_bytes.getvalue()

        # Check if this is the same audio we just processed (prevent duplicates)
        if audio_data == st.session_state.last_audio_bytes:
            # Skip - already processed this audio
            return

        # Store this audio as the last processed
        st.session_state.last_audio_bytes = audio_data

        # Show transcribing spinner
        with st.spinner("🎤 Transcribing..."):
            transcript = transcribe_audio(audio_data)

        if transcript:
            # Add user message to history with voice flag
            st.session_state.messages.append({
                "role": "user",
                "content": transcript,
                "input_type": "voice"
            })

            # Display user message with microphone icon
            with st.chat_message("user"):
                st.markdown(f"🎤 {transcript}")

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Prepare conversation history for the coordinator
                    history = st.session_state.messages[:-1]  # Exclude the current message

                    # Calculate turn number
                    turn_number = len(st.session_state.debug_history) + 1

                    # Process message through coordinator with voice flag
                    response = st.session_state.coordinator.process(
                        transcript, history, input_type="voice", turn_number=turn_number
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            # Rerun to update the display (including task list)
            st.rerun()
        else:
            st.error("Failed to transcribe audio. Please try again.")


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Create layout: sidebar for tasks, main area for chat
    render_task_list()
    render_chat()

    # Add footer
    st.markdown("---")
    st.caption("Flow Companion Milestone 2 - Voice Input with Claude & Voyage AI")


if __name__ == "__main__":
    main()
