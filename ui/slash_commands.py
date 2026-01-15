"""Slash command parsing and execution for Flow Companion."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time
import logging


# Help text for commands
HELP_TEXT = {
    "main": """
Available commands:
  /tasks [flags]     - List tasks
  /projects [name]   - List projects
  /search [mode] [target] <query> - Search
  /do <action> <task> - Perform action
  /help [command]    - Show help

Use /help <command> for details.
""",
    "tasks": """
/tasks [flags]
  status:todo|in_progress|done  - Filter by status
  priority:high|medium|low      - Filter by priority
  project:<name>                - Filter by project
  assignee:<name>               - Filter by assignee
  due:today|week|next-week      - Filter by due date
  blocked                       - Show only blocked tasks
  overdue                       - Show only overdue tasks
  limit:<n>                     - Limit results

Examples:
  /tasks
  /tasks status:in_progress
  /tasks assignee:Mike
  /tasks blocked
  /tasks overdue
  /tasks due:week assignee:Sarah
  /tasks priority:high project:AgentOps
""",
    "search": """
/search [mode] [target] <query>
  mode: vector | text | hybrid (default)
  target: tasks (default) | projects

Examples:
  /search debugging           (hybrid search tasks)
  /search vector debugging    (semantic search)
  /search text debugging      (keyword search)
  /search projects memory     (search projects)
""",
    "do": """
/do <action> "<task>"
  complete  - Mark task as done
  start     - Mark task as in_progress
  stop      - Mark task as todo
  note      - Add note (requires second arg)

Examples:
  /do complete "debugging doc"
  /do start "checkpointer"
  /do note "voice agent" "WebSocket working"
""",
    "projects": """
/projects [name|flags]
  [name] - Get specific project with tasks
  stakeholder:<name>  - Filter by stakeholder
  status:active|planned|completed|archived  - Filter by status
  (no args) - List all projects

Examples:
  /projects                      (list all)
  /projects AgentOps             (specific project)
  /projects stakeholder:Mike     (Mike's projects)
  /projects status:active        (active projects only)
  /projects search memory        (search projects)
"""
}


def detect_natural_language_query(user_input: str) -> Optional[str]:
    """
    Detect natural language queries that map to slash commands.

    Returns the equivalent slash command string, or None if no match.
    """
    import re

    query_lower = user_input.lower().strip()

    # Skip if input already starts with / (it's already a slash command)
    if query_lower.startswith('/'):
        return None

    # Skip multi-step queries - these should go to the LLM (Tier 4)
    # Examples: "Show me what's overdue, then complete the first one"
    #           "Find blocked tasks and add a note to each"
    #           "List high priority, then start the top one"
    multi_step_indicators = [
        r'\bthen\b',
        r'\band then\b',
        r'\bafter that\b',
        r'\bnext\b.*\b(complete|start|mark|add|create|update)',
        r',\s*then\b',
        r'\bfirst\s+(complete|start|mark)',
        r'\btop\s+one\s+(complete|start|mark)',
    ]
    if any(re.search(pattern, query_lower) for pattern in multi_step_indicators):
        return None  # Let LLM handle multi-step workflows

    # Check for complex filter conditions early - skip pattern matching if present
    # These should go to LLM agent (Tier 3) which can use search_tasks with filters
    complex_filter_indicators = [
        r'\b(high|medium|low)[- ]priority\b',  # priority filters
        r'\bthat (are|is)\b.*\b(in[- ]progress|todo|done|blocked|overdue)\b',  # "tasks that are X" structure
        r'\bwith\b.*\b(priority|status)\b',    # "with priority/status"
        r'\band\b.*\b(priority|status|blocked|overdue)\b',  # multiple conditions
    ]
    has_complex_filters = any(re.search(pattern, query_lower) for pattern in complex_filter_indicators)
    if has_complex_filters:
        return None  # Let LLM handle complex filtered queries

    # Skip web search queries - these should route to MCP for external search tools
    # Examples: "Search the web for X", "Search online for Y", "Web search Z"
    web_search_indicators = [
        r'\bsearch\s+(the\s+)?(web|internet|online)\b',
        r'\b(web|internet|online)\s+search\b',
        r'\b(google|bing|research)\s+(for|about)?\b',
    ]
    is_web_search = any(re.search(pattern, query_lower) for pattern in web_search_indicators)
    if is_web_search:
        return None  # Let coordinator route to MCP for web search

    # NOTE: Action patterns like "I finished X", "Start X", "Complete X" are NOT converted here.
    # They should go to the Worklog Agent (Tier 4) which does search → confirm → execute workflow.
    # Tier 2 detection only handles queries, not actions that modify data.

    # "What's next?" / "What should I work on?"
    if re.search(r'\b(what\'?s next|what should i (?:work on|do)|what\'?s my next task)\b', query_lower):
        return "/tasks status:todo priority:high"

    # Due date queries (BEFORE temporal queries to avoid conflict) - require query prefix
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(due today)(\s+tasks?)?\b', query_lower):
        return "/tasks due:today"

    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(due (?:this )?week)(\s+tasks?)?\b', query_lower):
        return "/tasks due:week"

    # Temporal queries - check for time-based filters
    # "Show me completed tasks from this week"
    if re.search(r'\b(completed|finished|done)\b.*\b(this week|today|yesterday)\b', query_lower):
        if 'this week' in query_lower:
            return "/completed this_week"
        elif 'today' in query_lower:
            return "/completed today"
        elif 'yesterday' in query_lower:
            return "/completed yesterday"

    # "What did I work on this week/today?"
    if re.search(r'\b(this week|today|yesterday)\b', query_lower) and not re.search(r'\b(completed|done|finished|due)\b', query_lower):
        if 'this week' in query_lower:
            return "/tasks this_week"
        elif 'today' in query_lower:
            return "/tasks today"
        elif 'yesterday' in query_lower:
            return "/tasks yesterday"

    # COMPOUND QUERIES - Assignee + Status (MUST come before simple assignee patterns)
    # "Show me Mike's tasks that are in progress"
    # "What's Sarah's work that is done"
    # "List Mike's tasks that are todo"
    compound_assignee_status = re.search(
        r'\b(?:show me|what[\'s\s]+|list|get)\s+(\w+)[\'s]+\s+(?:tasks?|work)\s+(?:that (?:are|is)|which (?:are|is))\s+(in progress|in-progress|ongoing|done|completed|finished|todo|to do|pending)',
        query_lower
    )
    if compound_assignee_status:
        assignee = compound_assignee_status.group(1).capitalize()
        status_raw = compound_assignee_status.group(2)
        # Normalize status
        if status_raw in ['in progress', 'in-progress', 'ongoing']:
            status = 'in_progress'
        elif status_raw in ['done', 'completed', 'finished']:
            status = 'done'
        elif status_raw in ['todo', 'to do', 'pending']:
            status = 'todo'
        else:
            status = status_raw
        return f"/tasks assignee:{assignee} status:{status}"

    # Assignee task queries - "Show me Mike's tasks" / "What's Mike working on?" (BEFORE status checks)
    assignee_match = re.search(r'\b(?:show me|what[\'s\s]+|list|get)\s+(\w+)[\'s]+\s+(?:tasks?|work)\b', query_lower)
    if assignee_match:
        assignee = assignee_match.group(1).capitalize()
        return f"/tasks assignee:{assignee}"

    # Assignee work queries - "What's Mike working on?" / "What is Sarah doing?"
    assignee_work_match = re.search(r'\b(?:what[\'s\s]+|what is)\s+(\w+)\s+(?:working on|doing)\b', query_lower)
    if assignee_work_match:
        assignee = assignee_work_match.group(1).capitalize()
        return f"/tasks assignee:{assignee}"

    # Status queries (non-temporal) - require query prefix
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(in progress|in-progress|ongoing|current)(\s+tasks?)?\b', query_lower):
        return "/tasks status:in_progress"

    # Status queries - MUST have query prefix to avoid matching action statements like "I finished X"
    # Queries: "What's done?", "Show me finished tasks", "List completed"
    # Actions (should NOT match): "I finished X", "Mark X as done", "Complete the task"
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(done|completed|finished)(\s+tasks?)?\b', query_lower):
        return "/tasks status:done"

    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(todo|to do|pending|upcoming)(\s+tasks?)?\b', query_lower):
        return "/tasks status:todo"

    # Priority queries - require query prefix
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(high priority|urgent|important)(\s+tasks?)?\b', query_lower):
        return "/tasks priority:high status:todo,in_progress"

    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(medium priority|normal)(\s+tasks?)?\b', query_lower):
        return "/tasks priority:medium"

    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(low priority)(\s+tasks?)?\b', query_lower):
        return "/tasks priority:low"

    # Blocked tasks queries - require query prefix
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(blocked|blocking)(\s+tasks?)?\b', query_lower):
        return "/tasks blocked"

    # Overdue tasks queries - require query prefix
    if re.search(r'\b(what[\'s\s]+|show\s+me\s+|show\s+|list\s+)(overdue|past due|late)(\s+tasks?)?\b', query_lower):
        return "/tasks overdue"

    # Stakeholder project queries - "Show me Mike's projects" / "What projects is Mike involved in?"
    stakeholder_match = re.search(r'\b(?:show me|what|list|get)\s+(?:projects?\s+)?(?:is\s+)?(\w+)(?:[\'s]+\s+projects?|\s+(?:is\s+)?involved in)\b', query_lower)
    if stakeholder_match:
        stakeholder = stakeholder_match.group(1).capitalize()
        return f"/projects stakeholder:{stakeholder}"

    # Project detail queries
    # Extract project name from queries like "Show me the AgentOps project"
    project_detail_match = re.search(r'(?:show me|get|display|view)\s+(?:the\s+)?(.+?)\s+project\b', user_input, re.IGNORECASE)
    if project_detail_match:
        project_name = project_detail_match.group(1).strip()
        # Only match if project name starts with capital (likely a proper noun)
        if project_name and project_name[0].isupper():
            return f"/projects {project_name}"

    # Project-specific task queries
    # Extract project name from queries like "What's in the Voice Agent project?"
    project_match = re.search(r'\b(?:in|for|on)\s+(?:the\s+)?([A-Z][A-Za-z\s]+?)\s+(?:project|tasks?)\b', user_input)
    if project_match:
        project_name = project_match.group(1).strip()
        return f"/tasks project:{project_name}"

    # List all projects queries
    if re.search(r'\b(show me|list|view|see)\s+(the\s+)?(all\s+)?projects?\b', query_lower):
        # "Show me the project" or "See all projects"
        return "/projects"

    if re.search(r'^(see all|show all|list all)$', query_lower):
        # Generic "see all" / "show all" - assume projects context
        return "/projects"

    # General "what's going on" queries
    if re.search(r'\b(what[\'s\s]+going on|what[\'s\s]+happening|status update|current status)\b', query_lower):
        return "/tasks"

    # Search queries with "tasks" keyword
    if re.search(r'\b(find|search for|look for|show me).*\b(tasks?|work)\b', query_lower):
        # Extract search term
        search_match = re.search(r'\b(?:find|search for|look for|show me)\s+(?:tasks?\s+)?(?:about\s+)?(.+?)(?:\s+tasks?)?$', query_lower)
        if search_match:
            search_term = search_match.group(1).strip()
            # Remove common trailing words
            search_term = re.sub(r'\s+(tasks?|work)$', '', search_term)
            return f"/search {search_term}"

    # Search queries WITHOUT "tasks" keyword - "Look for X" / "Find X"
    # Must come after more specific patterns
    # Only matches if searching for task-related content (not web search)
    if re.search(r'\b(look for|find)\s+\w', query_lower):
        search_match = re.search(r'\b(?:look for|find)\s+(.+)$', query_lower)
        if search_match:
            search_term = search_match.group(1).strip()
            # Don't match if it's trying to find a project
            if not re.search(r'\bprojects?\b', search_term):
                return f"/search {search_term}"

    # NOTE: "search for X" is intentionally NOT included above
    # Ambiguous queries like "search for AI agents" should go to coordinator
    # which routes to MCP for web search. For MongoDB search, use:
    #   - "find X" or "look for X" (matches above)
    #   - "search tasks for X" (matches pattern at line 269)

    # "What tasks are X?" queries - search for that attribute
    what_tasks_match = re.search(r'what tasks are\s+(.+?)\??$', query_lower)
    if what_tasks_match:
        search_term = what_tasks_match.group(1).strip()
        return f"/search {search_term}"

    return None


def parse_slash_command(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse slash commands, return None if not a command."""
    import re

    if not user_input.startswith("/"):
        return None

    # Remove leading slash and split into command and rest
    content = user_input[1:].strip()
    if not content:
        return None

    # Extract command (first word)
    command_match = re.match(r'^(\w+)\s*(.*)', content)
    if not command_match:
        return None

    command = command_match.group(1).lower()
    rest = command_match.group(2).strip()

    # Parse key:value arguments (supports spaces in values until next key:value)
    kwargs = {}
    positional = []

    if rest:
        # Find all key:value patterns using regex
        # Match pattern: word:(anything until next word: or end)
        remaining = rest
        while remaining:
            # Try to match key:value pattern
            kv_match = re.match(r'(\w+):((?:[^\s]|\s(?!\w+:))+)', remaining)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                kwargs[key] = value
                remaining = remaining[kv_match.end():].strip()
            else:
                # No more key:value pairs, rest are positional args
                positional.extend(remaining.split())
                break

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
            elif cmd == "do":
                result = self._handle_do(sub, args, kwargs)
            elif cmd == "help":
                result = self._handle_help(sub, args, kwargs)
            else:
                result = {"error": f"Unknown command: /{cmd}. Use /help for available commands."}

            duration_ms = int((time.time() - start) * 1000)
            return {
                "success": "error" not in result,
                "command": parsed_command["raw"],
                "duration_ms": duration_ms,
                "result": result,
                "show_raw": show_raw
            }
        except Exception as e:
            import traceback
            self.logger.error(f"Command execution error: {e}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "command": parsed_command["raw"],
                "duration_ms": int((time.time() - start) * 1000),
                "error": str(e),
                "traceback": traceback.format_exc(),
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
            limit = int(kwargs.get("limit", 50))
            self.logger.info(f"Getting tasks completed {timeframe}")
            return self._get_tasks_by_activity_type("completed", timeframe, limit)

        # Handle temporal subcommands
        limit = int(kwargs.get("limit", 50))
        if sub == "today":
            self.logger.info("Getting tasks with activity today")
            return self._get_temporal_tasks("today", limit)
        elif sub == "yesterday":
            self.logger.info("Getting tasks with activity yesterday")
            return self._get_temporal_tasks("yesterday", limit)
        elif sub == "week":
            self.logger.info("Getting tasks with activity this week")
            return self._get_temporal_tasks("week", limit)
        elif sub == "stale":
            self.logger.info("Getting stale tasks (in_progress > 7 days)")
            return self._get_stale_tasks(limit)
        else:
            # Regular task list with filters and $lookup for project names
            # Build match query from kwargs
            match_query = {"is_test": {"$ne": True}}  # Always exclude test data

            # Status filter (supports comma-separated values like "todo,in_progress")
            if kwargs.get("status"):
                status_value = kwargs["status"]
                if "," in status_value:
                    # Multiple statuses - use $in operator
                    status_list = [s.strip() for s in status_value.split(",")]
                    match_query["status"] = {"$in": status_list}
                    self.logger.info(f"Filtering by status (multiple): {status_list}")
                else:
                    # Single status
                    match_query["status"] = status_value
                    self.logger.info(f"Filtering by status: {status_value}")

            # Priority filter
            if kwargs.get("priority"):
                match_query["priority"] = kwargs["priority"]
                self.logger.info(f"Filtering by priority: {kwargs['priority']}")

            # Assignee filter (case-insensitive partial match)
            if kwargs.get("assignee"):
                match_query["assignee"] = {"$regex": kwargs["assignee"], "$options": "i"}
                self.logger.info(f"Filtering by assignee: {kwargs['assignee']}")

            # Blocked filter - tasks with blockers
            if kwargs.get("blocked") or sub == "blocked":
                match_query["blockers"] = {"$exists": True, "$ne": []}
                self.logger.info("Filtering for blocked tasks")

            # Overdue filter - tasks past due date and not done
            if kwargs.get("overdue") or sub == "overdue":
                now = datetime.utcnow()
                match_query["due_date"] = {"$lt": now}
                match_query["status"] = {"$ne": "done"}
                self.logger.info("Filtering for overdue tasks")

            # Due date filters
            if kwargs.get("due"):
                due_filter = kwargs["due"]
                now = datetime.utcnow()

                if due_filter == "today":
                    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                    match_query["due_date"] = {"$gte": start_of_day, "$lte": end_of_day}
                    self.logger.info("Filtering for tasks due today")
                elif due_filter == "this-week" or due_filter == "week":
                    end_of_week = now + timedelta(days=(7 - now.weekday()))
                    match_query["due_date"] = {"$gte": now, "$lte": end_of_week}
                    self.logger.info("Filtering for tasks due this week")
                elif due_filter == "next-week":
                    start_of_next_week = now + timedelta(days=(7 - now.weekday() + 1))
                    end_of_next_week = start_of_next_week + timedelta(days=7)
                    match_query["due_date"] = {"$gte": start_of_next_week, "$lte": end_of_next_week}
                    self.logger.info("Filtering for tasks due next week")

            # Project filter - need to resolve project name to project_id
            if kwargs.get("project"):
                project_name = kwargs["project"]
                self.logger.info(f"Looking up project: {project_name}")

                projects_collection = get_collection(PROJECTS_COLLECTION)
                project_doc = projects_collection.find_one(
                    {
                        "name": {"$regex": project_name, "$options": "i"},
                        "is_test": {"$ne": True}  # Exclude test projects
                    },
                    {"_id": 1}
                )

                if project_doc:
                    match_query["project_id"] = project_doc["_id"]
                    self.logger.info(f"Found project_id: {project_doc['_id']}")
                else:
                    # Project not found - use a non-existent ID to return empty results gracefully
                    from bson import ObjectId
                    match_query["project_id"] = ObjectId("000000000000000000000000")
                    self.logger.warning(f"Project '{project_name}' not found, returning empty results")

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
                        "as": "project_doc"
                    }
                },
                {
                    "$addFields": {
                        "project_name": {"$arrayElemAt": ["$project_doc.name", 0]}
                    }
                },
                {
                    "$project": {
                        "embedding": 0,
                        "project_doc": 0  # Remove joined array, keep just project_name
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$limit": int(kwargs.get("limit", 50))}
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

    def _get_temporal_tasks(self, timeframe, limit=50):
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
                    "as": "project_doc"
                }
            },
            {
                "$addFields": {
                    "project_name": {"$arrayElemAt": ["$project_doc.name", 0]}
                }
            },
            {
                "$project": {
                    "embedding": 0,
                    "project_doc": 0
                }
            },
            {"$sort": {"created_at": -1}},
            {"$limit": limit}
        ]))

        self.logger.info(f"Query returned {len(tasks)} tasks")

        # Convert ObjectIds to strings
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        return tasks

    def _get_tasks_by_activity_type(self, activity_type, timeframe, limit=50):
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
            {"$limit": limit}
        ]))

        self.logger.info(f"Query returned {len(tasks)} tasks")

        # Convert ObjectIds to strings
        for task in tasks:
            if task.get("_id"):
                task["_id"] = str(task["_id"])
            if task.get("project_id"):
                task["project_id"] = str(task["project_id"])

        return tasks

    def _get_stale_tasks(self, limit=50):
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
                    "as": "project_doc"
                }
            },
            {
                "$addFields": {
                    "project_name": {"$arrayElemAt": ["$project_doc.name", 0]}
                }
            },
            {
                "$project": {
                    "embedding": 0,
                    "project_doc": 0
                }
            },
            {"$sort": {"updated_at": 1}},
            {"$limit": limit}
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
        self.logger.info(f"sub: '{sub}' (type: {type(sub).__name__})")
        self.logger.info(f"args: {args} (len: {len(args)})")
        self.logger.info(f"kwargs: {kwargs}")
        self.logger.info(f"Condition checks:")
        self.logger.info(f"  - sub == 'search': {sub == 'search'}")
        self.logger.info(f"  - sub is not None: {sub is not None}")
        self.logger.info(f"  - bool(sub): {bool(sub)}")
        self.logger.info(f"  - sub != 'search': {sub != 'search'}")

        # Handle search subcommand
        if sub == "search" and args:
            self.logger.info(f">>> BRANCH: Search subcommand")
            query = " ".join(args)
            self.logger.info(f"Searching projects for: {query}")
            limit = int(kwargs.get("limit", 5))

            # Use hybrid search
            results = self.retrieval.hybrid_search_projects(query, limit)
            self.logger.info(f"Search returned {len(results)} projects")

            # Enrich with task counts
            return self._enrich_projects_with_task_counts(results)

        # Handle /projects <name> - Get specific project with its tasks
        # Support multi-word project names: /projects Voice Agent
        if sub and sub != "search":
            self.logger.info(f">>> BRANCH: Get specific project")
            # Reconstruct project name from sub + args
            project_name = f"{sub} {' '.join(args)}" if args else sub
            # Strip quote characters that might be from escaping: /projects "Voice Agent"
            project_name = project_name.strip('"').strip("'")
            self.logger.info(f"Getting specific project: {project_name}")
            return self._get_project_detail(project_name)

        # Regular project list with task counts via aggregation
        self.logger.info(f">>> BRANCH: List all projects")

        # Build match query from kwargs
        match_query = {"is_test": {"$ne": True}}  # Always exclude test data

        # Stakeholder filter (case-insensitive partial match on array elements)
        if kwargs.get("stakeholder"):
            match_query["stakeholders"] = {"$regex": kwargs["stakeholder"], "$options": "i"}
            self.logger.info(f"Filtering by stakeholder: {kwargs['stakeholder']}")

        # Status filter
        if kwargs.get("status"):
            match_query["status"] = kwargs["status"]
            self.logger.info(f"Filtering by status: {kwargs['status']}")

        # Build aggregation pipeline with $lookup to get task counts
        pipeline = [
            # Filter out test projects
            {"$match": match_query},
            {
                "$lookup": {
                    "from": "tasks",
                    "let": {"project_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$project_id", "$$project_id"]},
                                "is_test": {"$ne": True}  # Filter test tasks
                            }
                        }
                    ],
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
            {"$limit": int(kwargs.get("limit", 50))}
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
            {
                "project_id": {"$in": project_ids},
                "is_test": {"$ne": True}  # Exclude test tasks
            },
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
            {
                "name": {"$regex": f"^{project_name}$", "$options": "i"},
                "is_test": {"$ne": True}  # Exclude test projects
            },
            {"embedding": 0}
        )

        if not project:
            # Try partial match
            self.logger.info(f"Exact match not found, trying partial match")
            project = projects_collection.find_one(
                {
                    "name": {"$regex": project_name, "$options": "i"},
                    "is_test": {"$ne": True}  # Exclude test projects
                },
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
        """
        Handle /search commands with optional mode and target.

        Formats:
            /search <query>                    → hybrid search tasks (default)
            /search tasks <query>              → hybrid search tasks
            /search projects <query>           → hybrid search projects
            /search vector <query>             → vector-only search tasks
            /search text <query>               → text-only search tasks
            /search vector tasks <query>       → vector-only search tasks
            /search text projects <query>      → text-only search projects
        """
        # Handle empty args FIRST before any parsing
        if (not sub or not sub.strip()) and (not args or len(args) == 0):
            return {
                "error": "Usage: /search [vector|text|hybrid] [tasks|projects] <query>\n\nExamples:\n  /search debugging\n  /search vector debugging\n  /search projects memory",
                "success": False
            }

        # Combine sub and args for easier parsing
        all_parts = [sub] if sub and sub.strip() else []
        all_parts.extend(args if args else [])

        mode = "hybrid"  # Default mode
        target = "tasks"  # Default target
        query_parts = []

        i = 0
        # Check for mode (must be first if present)
        if i < len(all_parts) and all_parts[i] in ["vector", "text", "hybrid"]:
            mode = all_parts[i]
            i += 1

        # Check for target (only if it's exactly "tasks" or "projects")
        if i < len(all_parts) and all_parts[i] in ["tasks", "projects"]:
            target = all_parts[i]
            i += 1

        # Rest is the query
        query_parts = all_parts[i:]
        query = " ".join(query_parts)

        if not query or not query.strip():
            return {
                "error": f"Missing search query. Usage: /search [{mode}] [{target}] <query>\n\nExample: /search {mode} {target} debugging",
                "success": False
            }

        limit = int(kwargs.get("limit", 5))

        # Build method name: {mode}_search_{target}
        method_name = f"{mode}_search_{target}"
        search_method = getattr(self.retrieval, method_name, None)

        if not search_method:
            return {"error": f"Search method not implemented: {mode} search for {target}"}

        # Execute search
        self.logger.info(f"Executing {method_name}('{query}', limit={limit})")
        results = search_method(query, limit)

        # Enrich tasks with project names if searching tasks
        if target == "tasks" and results:
            results = self._enrich_tasks_with_project_names(results)

        self.logger.info(f"Search completed: mode={mode}, target={target}, query='{query}', results={len(results)}")

        # Return results with metadata for debug panel
        return {
            "results": results,
            "count": len(results),
            "mode": mode,
            "target": target,
            "query": query
        }

    def _handle_do(self, sub, args, kwargs):
        """Handle /do commands - task actions."""
        from shared.db import update_task, add_task_note, create_task, get_task
        from shared.models import Task
        from bson import ObjectId

        self.logger.info(f"=== /do command ===")
        self.logger.info(f"sub: {sub}, args: {args}, kwargs: {kwargs}")

        # Handle empty args FIRST
        if not sub or not sub.strip():
            return {
                "error": "Usage: /do <action> <task>\n\nActions:\n  complete - Mark task done\n  start - Mark task in progress\n  stop - Mark task as todo\n  note - Add note to task\n\nExamples:\n  /do complete \"debugging doc\"\n  /do start \"checkpointer\"",
                "success": False
            }

        action = sub.lower()

        # Validate action
        valid_actions = ["complete", "start", "stop", "note", "create"]
        if action not in valid_actions:
            return {
                "error": f"Unknown action: {action}. Use: {', '.join(valid_actions)}",
                "success": False
            }

        # Handle create action (doesn't need task lookup)
        if action == "create":
            if not args:
                return {"error": "Usage: /do create -t <title> [-p <project>] [--priority <level>]"}

            # Parse flags for create command
            import shlex

            # Reconstruct the original command string for proper quote handling
            create_args_str = " ".join(args)
            self.logger.info(f"Parsing create command: {create_args_str}")

            try:
                # Parse shell-style arguments
                parsed_args = shlex.split(create_args_str)
            except ValueError as e:
                return {"error": f"Invalid syntax: {e}"}

            # Check if any flags are present
            has_flags = any(arg.startswith("-") for arg in parsed_args)

            # Extract flags
            title = None
            project_name = None
            priority = kwargs.get("priority", "medium")  # Also check kwargs for backward compat

            if has_flags:
                # Parse flag-based syntax: -t "title" -p project --priority high
                i = 0
                while i < len(parsed_args):
                    arg = parsed_args[i]

                    if arg in ["-t", "--title"]:
                        if i + 1 < len(parsed_args):
                            title = parsed_args[i + 1]
                            i += 2
                        else:
                            return {"error": f"Flag {arg} requires a value"}
                    elif arg in ["-p", "--project"]:
                        if i + 1 < len(parsed_args):
                            project_name = parsed_args[i + 1]
                            i += 2
                        else:
                            return {"error": f"Flag {arg} requires a value"}
                    elif arg == "--priority":
                        if i + 1 < len(parsed_args):
                            priority = parsed_args[i + 1]
                            i += 2
                        else:
                            return {"error": "Flag --priority requires a value"}
                    else:
                        # Skip unrecognized args
                        i += 1
            else:
                # Backward compatibility: no flags means entire string is title
                title = " ".join(parsed_args)

            # Also check kwargs for backward compatibility with colon syntax
            if not project_name and kwargs.get("project"):
                project_name = kwargs["project"]

            if not title:
                return {"error": "Title is required. Use: /do create -t \"Task title\" or /do create Title here"}

            self.logger.info(f"Creating task: title='{title}', project='{project_name}', priority='{priority}'")

            # Build task object
            task_data = {
                "title": title,
                "description": "",
                "status": "todo",
                "priority": priority,
                "project_id": None
            }

            # Resolve project if provided
            if project_name:
                from shared.db import get_collection, PROJECTS_COLLECTION
                projects_collection = get_collection(PROJECTS_COLLECTION)
                project_doc = projects_collection.find_one(
                    {
                        "name": {"$regex": project_name, "$options": "i"},
                        "is_test": {"$ne": True}  # Exclude test projects
                    },
                    {"_id": 1, "name": 1}
                )
                if not project_doc:
                    # Project validation - MUST exist
                    return {"error": f"Project not found: '{project_name}'. Use /projects to see available projects."}

                task_data["project_id"] = project_doc["_id"]
                self.logger.info(f"Assigned to project: {project_doc['name']}")

            # Create task
            task = Task(**task_data)
            task_id = create_task(task, action_note=f"Created via /do command")

            # Fetch created task
            created_task = get_task(task_id)
            return {
                "action": "create",
                "task": {
                    "_id": str(created_task.id),
                    "title": created_task.title,
                    "status": created_task.status,
                    "priority": created_task.priority
                },
                "message": f"✅ Created task: {created_task.title}"
            }

        # For other actions, we need to find the task first
        if not args or len(args) == 0:
            return {
                "error": f"Usage: /do {action} <task_name>\n\nExample: /do {action} \"task name\"",
                "success": False
            }

        # Extract task reference and optional note (for 'note' action)
        task_reference = " ".join(args)
        note_text = None

        # For note action, extract note from quotes or kwargs
        if action == "note":
            # Look for quoted text
            import re
            quoted = re.search(r'"([^"]+)"', task_reference)
            if quoted:
                note_text = quoted.group(1)
                task_reference = task_reference.replace(quoted.group(0), "").strip()
            elif "note" in kwargs:
                note_text = kwargs["note"]

            if not note_text:
                return {"error": "Usage: /do note <task> \"<note_text>\""}

        self.logger.info(f"Looking up task: {task_reference}")

        # Use fuzzy matching to find the task
        match_result = self.retrieval.fuzzy_match_task(task_reference, threshold=0.6)

        task = None
        if not match_result or "match" not in match_result:
            # Try hybrid search as fallback
            self.logger.info("Fuzzy match failed, trying hybrid search")
            search_results = self.retrieval.hybrid_search_tasks(task_reference, limit=1)
            if not search_results:
                return {"error": f"Task not found: {task_reference}"}
            task = search_results[0]
        else:
            task = match_result["match"]

        # Verify task was found
        if not task or not task.get("_id"):
            return {"error": f"Task not found: {task_reference}"}

        task_id = task["_id"] if isinstance(task["_id"], ObjectId) else ObjectId(task["_id"])
        task_title = task.get("title", "Unknown")

        self.logger.info(f"Found task: {task_title} (ID: {task_id})")

        # Perform the action
        if action == "complete":
            success = update_task(task_id, {"status": "done"}, "Completed via /do command")
            if success:
                return {
                    "action": "complete",
                    "task": {"_id": str(task_id), "title": task_title, "status": "done"},
                    "message": f"✅ Completed: {task_title}"
                }
            else:
                return {"error": "Failed to update task"}

        elif action == "start":
            success = update_task(task_id, {"status": "in_progress"}, "Started via /do command")
            if success:
                return {
                    "action": "start",
                    "task": {"_id": str(task_id), "title": task_title, "status": "in_progress"},
                    "message": f"▶️ Started: {task_title}"
                }
            else:
                return {"error": "Failed to update task"}

        elif action == "stop":
            success = update_task(task_id, {"status": "todo"}, "Stopped via /do command")
            if success:
                return {
                    "action": "stop",
                    "task": {"_id": str(task_id), "title": task_title, "status": "todo"},
                    "message": f"⏸️ Stopped: {task_title}"
                }
            else:
                return {"error": "Failed to update task"}

        elif action == "note":
            success = add_task_note(task_id, note_text)
            if success:
                return {
                    "action": "note",
                    "task": {"_id": str(task_id), "title": task_title},
                    "note": note_text,
                    "message": f"📝 Added note to: {task_title}"
                }
            else:
                return {"error": "Failed to add note"}

        else:
            return {"error": f"Unknown action: {action}. Valid actions: complete, start, stop, note, create"}

    def _handle_help(self, sub, args, kwargs):
        """Handle /help commands - show command documentation."""
        # Get topic from sub or first arg
        topic = sub if sub else ("main" if not args else args[0])
        topic = topic.lower() if topic else "main"

        self.logger.info(f"=== /help command ===")
        self.logger.info(f"topic: {topic}")

        # Get help text for topic, default to main if not found
        help_text = HELP_TEXT.get(topic, HELP_TEXT["main"])

        if topic not in HELP_TEXT and topic != "main":
            # Unknown topic, show main help with a hint
            return {
                "help": f"Unknown help topic: '{topic}'\n{HELP_TEXT['main']}",
                "success": True
            }

        return {
            "help": help_text,
            "success": True
        }
