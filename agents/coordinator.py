"""Coordinator Agent that routes requests to appropriate sub-agents."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from shared.llm import llm_service
from shared.logger import get_logger
from agents.worklog import worklog_agent
from agents.retrieval import retrieval_agent

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
    }
]

SYSTEM_PROMPT = """You are a task management assistant. Help users manage their tasks and projects using the available tools.

**Important guidelines:**

1. When user references a task informally (e.g., "the debugging doc", "checkpointer task"):
   - First use search_tasks to find matches
   - If 1 clear match: use its _id to proceed with the action
   - If multiple matches: show the options with numbers and ask which one they mean

2. For task actions (complete, start, add note):
   - You MUST have the task_id from a search_tasks result first
   - Never guess or make up task IDs

3. **CRITICAL - Format responses with proper markdown:**

   When displaying task lists, use this format:

   ## ◐ In Progress (X tasks)
   1. **Task name** (Priority) - Project Name
   2. **Task name** (Priority) - Project Name

   ## ○ To Do (X tasks)
   1. **Task name** (Priority) - Project Name

   ## ✓ Done (X tasks)
   1. **Task name** (Priority) - Project Name

   - Always use markdown headers (##) to group by status
   - Use numbered lists with bold task names
   - Include priority (High/Medium/Low) in parentheses
   - Show project name after dash
   - Use status icons: ○ (todo), ◐ (in_progress), ✓ (done)

   For single task operations, confirm briefly:
   - "✓ Marked **Task name** as complete."
   - "Started working on **Task name**."

4. Be concise but readable:
   - Use headers, bullet points, and numbered lists
   - Keep responses scannable with proper spacing
   - Don't explain what you're doing step-by-step
   - Use natural, conversational language

5. Voice input handling:
   - Voice and text are processed identically
   - User might say "I finished the debugging doc" - search first, then complete
   - For ambiguous references, always ask for clarification"""


class CoordinatorAgent:
    """Coordinator agent that routes user requests to specialized agents using tool use."""

    def __init__(self):
        self.llm = llm_service
        self.worklog_agent = worklog_agent
        self.retrieval_agent = retrieval_agent
        self.last_debug_info = []  # Store debug info from last request

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

            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                error_msg = f"Unknown tool: {tool_name}"

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            error_msg = str(e)
            result = {"success": False, "error": str(e)}

        finally:
            # Always calculate duration, even on error
            duration_ms = int((time.time() - start_time) * 1000)

            # Create output summary
            output_summary = ""
            if result:
                if result.get("success"):
                    if "tasks" in result:
                        output_summary = f"{result['count']} tasks returned"
                    elif "projects" in result:
                        output_summary = f"{result['count']} projects returned"
                    elif "result" in result:
                        output_summary = str(result["result"])[:200]
                    else:
                        output_summary = "Success"
                else:
                    output_summary = f"Error: {result.get('error', 'Unknown')}"

            # Build debug info (don't include full result to avoid serialization issues)
            debug_info = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "duration_ms": duration_ms,
                "output_summary": output_summary,
                "success": result.get("success", False) if result else False,
                "error": error_msg
            }

            return result, debug_info

    def process(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, input_type: str = "text") -> str:
        """
        Process a user message using Claude's native tool use.

        Voice and text inputs are processed identically - Claude decides which tools to call.

        Args:
            user_message: User's message (voice transcript or text)
            conversation_history: Optional conversation history
            input_type: Type of input ("text" or "voice") - for logging only

        Returns:
            Agent's response
        """
        logger.info("=" * 80)
        logger.info("=== NEW REQUEST ===")
        logger.info(f"Input type: {input_type}")
        logger.info(f"User message: {user_message[:200]}...")
        logger.info(f"History length: {len(conversation_history) if conversation_history else 0}")

        # Reset debug info
        self.last_debug_info = []

        # Build messages - SAME PATH FOR VOICE AND TEXT
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        # Use Claude's native tool use
        logger.info("Calling Claude with tool use enabled")
        response = self.llm.generate_with_tools(
            messages=messages,
            tools=COORDINATOR_TOOLS,
            system=SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.3
        )

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

                    # Add tool result (convert ObjectIds to strings first)
                    serializable_result = convert_objectids_to_str(result)
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

            # Get next response from Claude
            logger.info("Sending tool results back to Claude")
            response = self.llm.generate_with_tools(
                messages=messages,
                tools=COORDINATOR_TOOLS,
                system=SYSTEM_PROMPT,
                max_tokens=4096,
                temperature=0.3
            )

        # Extract final text response
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_text += content_block.text

        logger.info("Request processing complete")
        logger.info("=" * 80)

        return final_text.strip()


# Global coordinator instance
coordinator = CoordinatorAgent()
