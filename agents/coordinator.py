"""Coordinator Agent that routes requests to appropriate sub-agents."""

from typing import List, Dict, Any, Optional

from shared.llm import llm_service
from agents.worklog import worklog_agent
from agents.retrieval import retrieval_agent


class CoordinatorAgent:
    """Coordinator agent that routes user requests to specialized agents."""

    def __init__(self):
        self.llm = llm_service
        self.worklog_agent = worklog_agent
        self.retrieval_agent = retrieval_agent

    def _determine_intent(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Determine the user's intent to route to the appropriate agent.

        Args:
            user_message: User's message
            conversation_history: Optional conversation history

        Returns:
            Intent: "worklog" or "retrieval"
        """
        # Build messages for intent classification
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        # System prompt for intent classification
        system_prompt = """You are a routing agent that determines user intent.
Analyze the user's message and classify it into one of two categories:

1. WORKLOG - User wants to create, update, manage, or LIST tasks/projects:
   - Creating new tasks or projects
   - Updating task status, priority, or details
   - Adding notes, context, decisions, or methods
   - Completing tasks
   - Listing/showing ALL tasks or projects (e.g., "What tasks do I have?", "Show me all projects")
   - Getting details about a specific task or project
   - General task/project management and listing operations

2. RETRIEVAL - User wants to SEARCH, FILTER, or ANALYZE with specific criteria:
   - Searching for tasks/projects by semantic meaning or keywords
   - Finding tasks related to a specific topic or concept
   - Filtering by date ranges ("what did I work on yesterday?")
   - Finding incomplete or stalled tasks
   - Getting project statistics and progress analytics
   - Complex queries with specific search criteria

IMPORTANT: Simple "list all" or "show me" queries should be WORKLOG, not RETRIEVAL.
Only use RETRIEVAL when the user needs semantic search, filtering, or analytics.

Respond with ONLY one word: either "worklog" or "retrieval" based on the primary intent."""

        # Get intent from Claude
        response = self.llm.generate(
            messages=messages,
            system=system_prompt,
            max_tokens=10,
            temperature=0.0
        )

        # Parse response
        intent = response.strip().lower()
        if "retrieval" in intent:
            return "retrieval"
        else:
            return "worklog"  # Default to worklog

    def process(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Process a user message by routing to the appropriate agent.

        Args:
            user_message: User's message
            conversation_history: Optional conversation history

        Returns:
            Agent's response
        """
        # Determine intent
        intent = self._determine_intent(user_message, conversation_history)

        # Debug logging
        print(f"[COORDINATOR] User message: {user_message}")
        print(f"[COORDINATOR] Routing to: {intent.upper()} agent")

        # Route to appropriate agent
        if intent == "retrieval":
            return self.retrieval_agent.process(user_message, conversation_history)
        else:
            return self.worklog_agent.process(user_message, conversation_history)


# Global coordinator instance
coordinator = CoordinatorAgent()
