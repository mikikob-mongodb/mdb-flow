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

1. WORKLOG - User wants to create, update, or manage tasks/projects:
   - Creating new tasks or projects
   - Updating task status, priority, or details
   - Adding notes, context, decisions, or methods
   - Completing tasks
   - General task/project management operations

2. RETRIEVAL - User wants to search, find, or analyze existing data:
   - Searching for tasks or projects
   - Finding tasks by semantic similarity
   - Checking what was done on a specific date
   - Finding incomplete tasks
   - Checking project progress or statistics
   - Any query about existing data

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

        # Route to appropriate agent
        if intent == "retrieval":
            return self.retrieval_agent.process(user_message, conversation_history)
        else:
            return self.worklog_agent.process(user_message, conversation_history)


# Global coordinator instance
coordinator = CoordinatorAgent()
