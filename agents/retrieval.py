"""Retrieval Agent for semantic and temporal search operations."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from bson import ObjectId

from shared.llm import llm_service
from shared.embeddings import embed_query as embedding_embed_query
from shared.db import (
    get_collection,
    get_project as db_get_project,
    TASKS_COLLECTION,
    PROJECTS_COLLECTION,
)
from shared.models import Task, Project


class RetrievalAgent:
    """Agent for handling search and retrieval operations using Claude."""

    def __init__(self):
        self.llm = llm_service
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define all available tools for the agent."""
        return [
            {
                "name": "embed_query",
                "description": "Generate embedding vector for a query text using Voyage AI",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Query text to embed"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "search_semantic",
                "description": "Perform semantic vector search across tasks and/or projects",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "collections": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["tasks", "projects"]
                            },
                            "description": "Collections to search (default: both tasks and projects)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_by_date",
                "description": "Search for activity on a specific date",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date to search: 'yesterday', 'today', or 'YYYY-MM-DD' format"
                        },
                        "include_incomplete": {
                            "type": "boolean",
                            "description": "Include tasks that were worked on but not completed (default: false)",
                            "default": False
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "search_incomplete",
                "description": "Find tasks with activity since a date but status not done",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "since_date": {
                            "type": "string",
                            "description": "Start date: 'yesterday', 'today', or 'YYYY-MM-DD' format"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Optional project ID to filter by"
                        }
                    },
                    "required": ["since_date"]
                }
            },
            {
                "name": "search_progress",
                "description": "Get progress summary for a project including tasks and activity",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (MongoDB ObjectId as string)"
                        },
                        "since_date": {
                            "type": "string",
                            "description": "Optional: Show activity since this date ('yesterday', 'today', or 'YYYY-MM-DD')"
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
            if tool_name == "embed_query":
                return self._embed_query(**tool_input)
            elif tool_name == "search_semantic":
                return self._search_semantic(**tool_input)
            elif tool_name == "search_by_date":
                return self._search_by_date(**tool_input)
            elif tool_name == "search_incomplete":
                return self._search_incomplete(**tool_input)
            elif tool_name == "search_progress":
                return self._search_progress(**tool_input)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse a date string into a datetime object.

        Args:
            date_str: Date string ('yesterday', 'today', or 'YYYY-MM-DD')

        Returns:
            datetime object
        """
        date_str_lower = date_str.lower()
        now = datetime.utcnow()

        if date_str_lower == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str_lower == "yesterday":
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Parse YYYY-MM-DD format
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use 'yesterday', 'today', or 'YYYY-MM-DD'")

    def _embed_query(self, text: str) -> Dict[str, Any]:
        """Generate embedding vector for a query text."""
        embedding = embedding_embed_query(text)

        return {
            "success": True,
            "text": text,
            "embedding_dimensions": len(embedding),
            "embedding": embedding
        }

    def _search_semantic(
        self,
        query: str,
        collections: Optional[List[Literal["tasks", "projects"]]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Perform semantic vector search across collections.

        Args:
            query: Search query text
            collections: Collections to search (default: ["tasks", "projects"])
            limit: Maximum results per collection

        Returns:
            Search results with similarity scores
        """
        if collections is None:
            collections = ["tasks", "projects"]

        # Generate query embedding
        query_embedding = embedding_embed_query(query)

        results = {
            "success": True,
            "query": query,
            "results": []
        }

        # Search tasks
        if "tasks" in collections:
            tasks_collection = get_collection(TASKS_COLLECTION)

            # MongoDB Atlas Vector Search aggregation
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "task_embedding_index",  # Atlas search index name
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,  # Scan more candidates for better results
                        "limit": limit
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "title": 1,
                        "status": 1,
                        "priority": 1,
                        "context": 1,
                        "project_id": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]

            try:
                task_results = list(tasks_collection.aggregate(pipeline))
                for task in task_results:
                    task["_id"] = str(task["_id"])
                    task["project_id"] = str(task["project_id"]) if task.get("project_id") else None
                    task["type"] = "task"
                results["results"].extend(task_results)
            except Exception as e:
                results["tasks_error"] = f"Vector search failed: {str(e)}. Ensure vector search index is created."

        # Search projects
        if "projects" in collections:
            projects_collection = get_collection(PROJECTS_COLLECTION)

            # MongoDB Atlas Vector Search aggregation
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "project_embedding_index",  # Atlas search index name
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "description": 1,
                        "status": 1,
                        "context": 1,
                        "created_at": 1,
                        "last_activity": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]

            try:
                project_results = list(projects_collection.aggregate(pipeline))
                for project in project_results:
                    project["_id"] = str(project["_id"])
                    project["type"] = "project"
                results["results"].extend(project_results)
            except Exception as e:
                results["projects_error"] = f"Vector search failed: {str(e)}. Ensure vector search index is created."

        # Sort all results by score (descending)
        if "score" in results["results"][0] if results["results"] else {}:
            results["results"].sort(key=lambda x: x.get("score", 0), reverse=True)

        results["count"] = len(results["results"])
        return results

    def _search_by_date(
        self,
        date: str,
        include_incomplete: bool = False
    ) -> Dict[str, Any]:
        """
        Search for activity on a specific date.

        Args:
            date: Date string ('yesterday', 'today', or 'YYYY-MM-DD')
            include_incomplete: Include tasks worked on but not completed

        Returns:
            Chronological activity for the date
        """
        # Parse date
        target_date = self._parse_date(date)
        next_day = target_date + timedelta(days=1)

        results = {
            "success": True,
            "date": date,
            "parsed_date": target_date.isoformat(),
            "tasks": [],
            "projects": []
        }

        # Search tasks with activity on this date
        tasks_collection = get_collection(TASKS_COLLECTION)

        # Build match condition
        match_condition = {
            "activity_log.timestamp": {
                "$gte": target_date,
                "$lt": next_day
            }
        }

        if not include_incomplete:
            # Only include tasks that were completed on this date
            match_condition["completed_at"] = {
                "$gte": target_date,
                "$lt": next_day
            }

        pipeline = [
            {"$match": match_condition},
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "status": 1,
                    "priority": 1,
                    "project_id": 1,
                    "created_at": 1,
                    "completed_at": 1,
                    "activity_log": {
                        "$filter": {
                            "input": "$activity_log",
                            "as": "log",
                            "cond": {
                                "$and": [
                                    {"$gte": ["$$log.timestamp", target_date]},
                                    {"$lt": ["$$log.timestamp", next_day]}
                                ]
                            }
                        }
                    }
                }
            },
            {"$sort": {"activity_log.timestamp": 1}}
        ]

        task_results = list(tasks_collection.aggregate(pipeline))
        for task in task_results:
            task["_id"] = str(task["_id"])
            task["project_id"] = str(task["project_id"]) if task.get("project_id") else None
        results["tasks"] = task_results

        # Search projects with activity on this date
        projects_collection = get_collection(PROJECTS_COLLECTION)

        pipeline = [
            {
                "$match": {
                    "activity_log.timestamp": {
                        "$gte": target_date,
                        "$lt": next_day
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "description": 1,
                    "status": 1,
                    "activity_log": {
                        "$filter": {
                            "input": "$activity_log",
                            "as": "log",
                            "cond": {
                                "$and": [
                                    {"$gte": ["$$log.timestamp", target_date]},
                                    {"$lt": ["$$log.timestamp", next_day]}
                                ]
                            }
                        }
                    }
                }
            },
            {"$sort": {"activity_log.timestamp": 1}}
        ]

        project_results = list(projects_collection.aggregate(pipeline))
        for project in project_results:
            project["_id"] = str(project["_id"])
        results["projects"] = project_results

        results["task_count"] = len(task_results)
        results["project_count"] = len(project_results)

        return results

    def _search_incomplete(
        self,
        since_date: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find tasks with activity since a date but status not done.

        Args:
            since_date: Start date string
            project_id: Optional project ID filter

        Returns:
            Incomplete tasks with recent activity
        """
        # Parse date
        start_date = self._parse_date(since_date)

        tasks_collection = get_collection(TASKS_COLLECTION)

        # Build match condition
        match_condition = {
            "status": {"$ne": "done"},
            "activity_log.timestamp": {"$gte": start_date}
        }

        if project_id:
            match_condition["project_id"] = ObjectId(project_id)

        pipeline = [
            {"$match": match_condition},
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "status": 1,
                    "priority": 1,
                    "context": 1,
                    "project_id": 1,
                    "created_at": 1,
                    "last_worked_on": 1,
                    "recent_activity": {
                        "$filter": {
                            "input": "$activity_log",
                            "as": "log",
                            "cond": {"$gte": ["$$log.timestamp", start_date]}
                        }
                    }
                }
            },
            {"$sort": {"last_worked_on": -1}}
        ]

        task_results = list(tasks_collection.aggregate(pipeline))
        for task in task_results:
            task["_id"] = str(task["_id"])
            task["project_id"] = str(task["project_id"]) if task.get("project_id") else None

        return {
            "success": True,
            "since_date": since_date,
            "parsed_date": start_date.isoformat(),
            "project_id": project_id,
            "count": len(task_results),
            "tasks": task_results
        }

    def _search_progress(
        self,
        project_id: str,
        since_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get progress summary for a project.

        Args:
            project_id: Project ID
            since_date: Optional date to filter activity

        Returns:
            Progress summary with stats and activity
        """
        project_oid = ObjectId(project_id)

        # Get project
        project = db_get_project(project_oid)
        if not project:
            return {"success": False, "error": "Project not found"}

        # Get all tasks for project
        tasks_collection = get_collection(TASKS_COLLECTION)

        # Calculate task statistics
        pipeline = [
            {"$match": {"project_id": project_oid}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_counts = list(tasks_collection.aggregate(pipeline))
        stats = {
            "total": 0,
            "todo": 0,
            "in_progress": 0,
            "done": 0
        }

        for item in status_counts:
            status = item["_id"]
            count = item["count"]
            stats[status] = count
            stats["total"] += count

        # Calculate completion percentage
        stats["completion_percentage"] = (
            (stats["done"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )

        # Get recent activity
        activity_filter = {}
        if since_date:
            start_date = self._parse_date(since_date)
            activity_filter = {"activity_log.timestamp": {"$gte": start_date}}

        # Get tasks with recent activity
        match_condition = {"project_id": project_oid}
        if since_date:
            match_condition.update(activity_filter)

        recent_tasks_pipeline = [
            {"$match": match_condition},
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "status": 1,
                    "last_worked_on": 1,
                    "activity_log": 1 if not since_date else {
                        "$filter": {
                            "input": "$activity_log",
                            "as": "log",
                            "cond": {"$gte": ["$$log.timestamp", start_date]}
                        }
                    }
                }
            },
            {"$sort": {"last_worked_on": -1}},
            {"$limit": 20}
        ]

        recent_tasks = list(tasks_collection.aggregate(recent_tasks_pipeline))
        for task in recent_tasks:
            task["_id"] = str(task["_id"])

        # Build result
        result = {
            "success": True,
            "project_id": project_id,
            "project": {
                "_id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "context": project.context,
                "methods": project.methods,
                "decisions": project.decisions
            },
            "statistics": stats,
            "recent_tasks": recent_tasks,
            "recent_activity_count": sum(len(task.get("activity_log", [])) for task in recent_tasks)
        }

        if since_date:
            result["since_date"] = since_date

        return result

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
        system_prompt = """You are a helpful search and retrieval assistant.
You have access to tools for semantic search, date-based search, and progress tracking.
Use the appropriate tools to help users find tasks, projects, and track progress.

When searching:
- Use semantic search for finding tasks/projects by meaning or content
- Use date-based search for activity on specific dates
- Use incomplete search for finding stalled or unfinished work
- Use progress search for project status and statistics

Always use the tools to perform actual searches - don't just describe what you would do.
Provide clear, organized summaries of search results."""

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
retrieval_agent = RetrievalAgent()
