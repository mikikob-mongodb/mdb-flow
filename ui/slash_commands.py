"""Slash command parsing and execution for Flow Companion."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time
import logging


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
        self.logger = logging.getLogger(__name__)

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

        self.logger.info(f"=== /tasks command ===")
        self.logger.info(f"sub: {sub}, args: {args}, kwargs: {kwargs}")

        # Handle search subcommand FIRST
        if sub == "search" and args:
            query = " ".join(args)
            self.logger.info(f"Searching tasks for: {query}")
            limit = int(kwargs.get("limit", 10))
            results = self.retrieval.hybrid_search_tasks(query, limit)
            self.logger.info(f"Search returned {len(results)} tasks")
            # Enrich with project names
            return self._enrich_tasks_with_project_names(results)

        # Handle completed:timeframe pattern
        if kwargs.get("completed"):
            timeframe = kwargs["completed"]
            self.logger.info(f"Getting tasks completed {timeframe}")
            return self._get_tasks_by_activity_type("completed", timeframe)

        # Handle temporal subcommands
        if sub == "today":
            self.logger.info("Getting tasks with activity today")
            return self._get_temporal_tasks("today")
        elif sub == "yesterday":
            self.logger.info("Getting tasks with activity yesterday")
            return self._get_temporal_tasks("yesterday")
        elif sub == "week":
            self.logger.info("Getting tasks with activity this week")
            return self._get_temporal_tasks("week")
        elif sub == "stale":
            self.logger.info("Getting stale tasks (in_progress > 7 days)")
            return self._get_stale_tasks()
        else:
            # Regular task list with filters and $lookup for project names
            # Build match query from kwargs
            match_query = {}

            # Status filter
            if kwargs.get("status"):
                match_query["status"] = kwargs["status"]
                self.logger.info(f"Filtering by status: {kwargs['status']}")

            # Priority filter
            if kwargs.get("priority"):
                match_query["priority"] = kwargs["priority"]
                self.logger.info(f"Filtering by priority: {kwargs['priority']}")

            # Project filter - need to resolve project name to project_id
            if kwargs.get("project"):
                project_name = kwargs["project"]
                self.logger.info(f"Looking up project: {project_name}")

                projects_collection = get_collection(PROJECTS_COLLECTION)
                project_doc = projects_collection.find_one(
                    {"name": {"$regex": project_name, "$options": "i"}},
                    {"_id": 1}
                )

                if project_doc:
                    match_query["project_id"] = project_doc["_id"]
                    self.logger.info(f"Found project_id: {project_doc['_id']}")
                else:
                    self.logger.warning(f"Project '{project_name}' not found")
                    return {"error": f"Project '{project_name}' not found"}

            self.logger.info(f"MongoDB match query: {match_query}")

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

            self.logger.info(f"Query returned {len(tasks)} tasks")

            # Convert ObjectIds to strings for JSON serialization
            for task in tasks:
                if task.get("_id"):
                    task["_id"] = str(task["_id"])
                if task.get("project_id"):
                    task["project_id"] = str(task["project_id"])

            return tasks

    def _get_temporal_tasks(self, timeframe):
        """Get tasks with activity in a specific timeframe."""
        from shared.db import get_collection, TASKS_COLLECTION

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

        self.logger.info(f"Temporal query: {timeframe}, Start: {start}, End: {end}")

        # Query tasks with activity in the time range
        query = {
            "activity_log": {
                "$elemMatch": {
                    "timestamp": {"$gte": start, "$lte": end}
                }
            }
        }

        self.logger.info(f"MongoDB query: {query}")

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

        self.logger.info(f"Query returned {len(tasks)} tasks")

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

        self.logger.info(f"Getting tasks by activity: {activity_type} {timeframe}, Start: {start}")

        query = {
            "activity_log": {
                "$elemMatch": {
                    "action": activity_type,
                    "timestamp": {"$gte": start}
                }
            }
        }

        self.logger.info(f"MongoDB query: {query}")

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

        self.logger.info(f"Query returned {len(tasks)} tasks")

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

        now = datetime.utcnow()
        stale_threshold = now - timedelta(days=7)

        self.logger.info(f"Getting stale tasks (in_progress before {stale_threshold})")

        query = {
            "status": "in_progress",
            "updated_at": {"$lt": stale_threshold}
        }

        self.logger.info(f"MongoDB query: {query}")

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

        self.logger.info(f"Query returned {len(tasks)} stale tasks")

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
        from bson import ObjectId

        # Build project lookup dict
        project_ids = [task.get("project_id") for task in tasks if task.get("project_id")]
        if not project_ids:
            # No projects to lookup, just add "-" for all tasks
            for task in tasks:
                task["project_name"] = "-"
            return tasks

        # Convert string IDs to ObjectIds if needed
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

        self.logger.info(f"=== /projects command ===")
        self.logger.info(f"sub: {sub}, args: {args}, kwargs: {kwargs}")

        # Handle search subcommand
        if sub == "search" and args:
            query = " ".join(args)
            self.logger.info(f"Searching projects for: {query}")
            limit = int(kwargs.get("limit", 5))

            # Use hybrid search
            results = self.retrieval.hybrid_search_projects(query, limit)
            self.logger.info(f"Search returned {len(results)} projects")

            # Enrich with task counts
            return self._enrich_projects_with_task_counts(results)

        # Handle /projects <name> - Get specific project with its tasks
        if sub and not args:
            project_name = sub
            self.logger.info(f"Getting specific project: {project_name}")
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

        self.logger.info(f"Query returned {len(projects)} projects")

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

        # Find the project (case-insensitive exact match first)
        projects_collection = get_collection(PROJECTS_COLLECTION)
        project = projects_collection.find_one(
            {"name": {"$regex": f"^{project_name}$", "$options": "i"}},
            {"embedding": 0}
        )

        if not project:
            # Try partial match
            self.logger.info(f"Exact match not found, trying partial match")
            project = projects_collection.find_one(
                {"name": {"$regex": project_name, "$options": "i"}},
                {"embedding": 0}
            )

        if not project:
            self.logger.warning(f"Project '{project_name}' not found")
            return {"error": f"Project '{project_name}' not found"}

        self.logger.info(f"Found project: {project.get('name')}")

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

        self.logger.info(f"Found {len(tasks)} tasks for project")

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
