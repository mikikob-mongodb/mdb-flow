"""Coordinator Agent that routes requests to appropriate sub-agents."""

import json
from typing import List, Dict, Any, Optional

from shared.llm import llm_service
from shared.logger import get_logger
from agents.worklog import worklog_agent
from agents.retrieval import retrieval_agent

logger = get_logger("coordinator")


class CoordinatorAgent:
    """Coordinator agent that routes user requests to specialized agents."""

    def __init__(self):
        self.llm = llm_service
        self.worklog_agent = worklog_agent
        self.retrieval_agent = retrieval_agent

    def parse_voice_input(self, transcript: str) -> dict:
        """
        Parse unstructured voice input to extract structured task/project updates.

        Args:
            transcript: Raw voice transcript from user

        Returns:
            dict with extracted structure:
                - task_references: list of informal task mentions
                - project_references: list of informal project mentions
                - completions: list of tasks mentioned as done
                - progress_updates: list of work in progress updates
                - deferrals: list of items pushed to later (with when/reason)
                - new_items: list of new tasks suggested (with source if mentioned)
                - context_updates: list of context to add to tasks/projects
                - notes_to_add: list of specific notes to add
                - decisions: list of decisions made
                - cleaned_summary: 1-2 sentence clean summary
        """
        system_prompt = """You are a voice input parser for a TODO app. Parse rambling, stream-of-consciousness speech into structured updates.

Extract the following from the transcript:

1. **task_references**: Informal task mentions like "the auth thing", "that login bug", "the API stuff"
   Format: [{"mention": "the auth thing", "likely_task": "authentication feature"}]

2. **project_references**: Informal project mentions like "the mobile app", "that client project"
   Format: [{"mention": "the mobile app", "likely_project": "Mobile App Rewrite"}]

3. **completions**: Tasks mentioned as done/finished/completed
   Format: [{"what": "authentication system", "confidence": "high"}]

4. **progress_updates**: Work in progress, partially done
   Format: [{"what": "API endpoints", "status": "halfway done", "details": "finished GET and POST"}]

5. **deferrals**: Items pushed to later
   Format: [{"what": "testing", "when": "next week", "reason": "waiting for staging environment"}]

6. **new_items**: New tasks mentioned
   Format: [{"task": "add password reset flow", "source": "mentioned by Sarah in standup"}]

7. **context_updates**: Context to add to existing tasks/projects
   Format: [{"target": "API project", "context": "using FastAPI framework, deployment on AWS"}]

8. **notes_to_add**: Specific notes to capture
   Format: [{"note": "Remember to update documentation after auth is done"}]

9. **decisions**: Decisions made
   Format: [{"decision": "Going with OAuth instead of custom auth", "reasoning": "more secure"}]

10. **cleaned_summary**: A clean 1-2 sentence summary of what was said

Return ONLY valid JSON with this structure:
{
  "task_references": [],
  "project_references": [],
  "completions": [],
  "progress_updates": [],
  "deferrals": [],
  "new_items": [],
  "context_updates": [],
  "notes_to_add": [],
  "decisions": [],
  "cleaned_summary": ""
}

Be generous in interpretation - capture the intent even if vague. Return empty arrays for sections with no matches."""

        # Get parsed structure from Claude
        logger.info(f"Parsing voice transcript: '{transcript[:100]}...'")
        try:
            response = self.llm.generate(
                messages=[{"role": "user", "content": f"Parse this voice transcript:\n\n{transcript}"}],
                system=system_prompt,
                max_tokens=2000,
                temperature=0.0
            )

            logger.debug(f"Raw LLM response:\n{response}")
            print(f"[COORDINATOR] Raw LLM response:\n{response}")

            # Clean up response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()

            # Parse JSON response
            parsed = json.loads(cleaned_response)

            # Ensure all expected keys exist
            default_structure = {
                "task_references": [],
                "project_references": [],
                "completions": [],
                "progress_updates": [],
                "deferrals": [],
                "new_items": [],
                "context_updates": [],
                "notes_to_add": [],
                "decisions": [],
                "cleaned_summary": ""
            }

            # Merge with defaults
            for key in default_structure:
                if key not in parsed:
                    parsed[key] = default_structure[key]

            logger.info(f"Successfully parsed voice input:")
            logger.info(f"  - Completions: {len(parsed.get('completions', []))}")
            logger.info(f"  - Progress updates: {len(parsed.get('progress_updates', []))}")
            logger.info(f"  - Notes: {len(parsed.get('notes_to_add', []))}")
            logger.info(f"  - New items: {len(parsed.get('new_items', []))}")
            logger.debug(f"Full parsed structure: {json.dumps(parsed, indent=2)}")

            return parsed

        except Exception as e:
            logger.error(f"Error parsing voice input: {e}", exc_info=True)
            print(f"[COORDINATOR] Error parsing voice input: {e}")
            # Return empty structure on error
            return {
                "task_references": [],
                "project_references": [],
                "completions": [],
                "progress_updates": [],
                "deferrals": [],
                "new_items": [],
                "context_updates": [],
                "notes_to_add": [],
                "decisions": [],
                "cleaned_summary": ""
            }

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

    def _process_voice_input(self, transcript: str) -> str:
        """
        Process voice input: search for tasks → show options → ask for confirmation.

        Simple flow:
        1. Parse voice to understand intent (completion, progress, note, etc.)
        2. Search for matching tasks
        3. Show top results and ask user to confirm
        4. User responds with number or name to execute

        Args:
            transcript: Voice transcript

        Returns:
            Search results and confirmation request
        """
        logger.info("=" * 80)
        logger.info("=== VOICE PROCESSING START ===")
        logger.info(f"Transcript: '{transcript}'")
        print(f"[COORDINATOR] Processing voice input: {transcript[:100]}...")

        # Parse the voice input to extract structured data
        parsed = self.parse_voice_input(transcript)

        logger.debug(f"Task references found: {parsed['task_references']}")
        logger.debug(f"Completions found: {parsed['completions']}")
        logger.debug(f"Progress updates found: {parsed['progress_updates']}")
        logger.debug(f"Notes found: {parsed['notes_to_add']}")

        # Determine the action type from parsed data
        action_type = None
        action_description = None

        if parsed["completions"]:
            action_type = "complete"
            action_description = "completed"
        elif parsed["progress_updates"]:
            action_type = "progress"
            action_description = "working on"
        elif parsed["notes_to_add"]:
            action_type = "note"
            action_description = "add a note to"
        elif parsed["deferrals"]:
            action_type = "defer"
            action_description = "deferred"

        # If we found task references, do semantic search and show options
        if parsed["task_references"] and action_type:
            # Take the first task reference
            ref = parsed["task_references"][0]
            mention = ref.get("mention", "")

            logger.info(f"Searching for tasks matching: '{mention}'")

            # Do semantic search (without threshold filtering)
            search_results = self.retrieval_agent._search_semantic(
                query=mention,
                collections=["tasks"],
                limit=5
            )

            if search_results.get("success") and search_results.get("results"):
                tasks = search_results["results"]
                logger.info(f"Found {len(tasks)} potential matches")

                # Build confirmation message
                response_parts = []
                response_parts.append(f"I heard you say you {action_description} something.")
                response_parts.append(f"\nWhich task did you mean?\n")

                for i, task in enumerate(tasks[:5], 1):
                    status_icon = {"todo": "○", "in_progress": "◐", "done": "✓"}.get(task.get('status'), "○")
                    project_info = f" ({task.get('project_name', '')})" if task.get('project_name') else ""
                    response_parts.append(f"{i}. {status_icon} {task['title']}{project_info}")

                response_parts.append(f"\n**Please mention the task name** to confirm and I'll mark it as {action_description}.")

                return "\n".join(response_parts)
            else:
                return f"I couldn't find any tasks matching '{mention}'. Can you be more specific?"

        # Handle new items
        if parsed["new_items"]:
            response_parts = []
            response_parts.append("I heard you mention creating new tasks:\n")
            for i, item in enumerate(parsed["new_items"], 1):
                source_info = f" (source: {item['source']})" if item.get("source") else ""
                response_parts.append(f"{i}. {item['task']}{source_info}")

            response_parts.append("\nShould I create these tasks? Reply 'yes' to confirm or provide more details.")
            return "\n".join(response_parts)

        # Handle general notes without a task reference
        if parsed["notes_to_add"] and not parsed["task_references"]:
            notes_text = "\n".join([f"- {note['note']}" for note in parsed["notes_to_add"]])
            return f"I captured these notes:\n\n{notes_text}\n\nWhich task or project should I add them to?"

        # Fallback: no clear action detected
        return f"I heard: \"{parsed['cleaned_summary']}\"\n\nCould you clarify what you'd like me to do? For example:\n- 'I finished [task name]'\n- 'I'm working on [task name]'\n- 'Add a note to [task name]: [your note]'"

    def process(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, input_type: str = "text") -> str:
        """
        Process a user message by routing to the appropriate agent.

        Args:
            user_message: User's message
            conversation_history: Optional conversation history
            input_type: Type of input ("text" or "voice")

        Returns:
            Agent's response
        """
        # Debug logging
        logger.info("=" * 80)
        logger.info("=== NEW REQUEST ===")
        logger.info(f"Input type: {input_type}")
        logger.info(f"User message: {user_message[:200]}...")
        logger.info(f"History length: {len(conversation_history) if conversation_history else 0}")

        print(f"[COORDINATOR] User message: {user_message}")
        print(f"[COORDINATOR] Input type: {input_type}")

        # Handle voice input differently
        if input_type == "voice":
            logger.info("Routing to voice processing pipeline")
            result = self._process_voice_input(user_message)
            logger.info("Voice processing complete")
            return result

        # For text input, use normal routing
        # Determine intent
        logger.debug("Determining intent for text input...")
        intent = self._determine_intent(user_message, conversation_history)
        logger.info(f"Intent determined: {intent.upper()}")

        print(f"[COORDINATOR] Routing to: {intent.upper()} agent")

        # Route to appropriate agent
        if intent == "retrieval":
            logger.info("Routing to RETRIEVAL agent")
            result = self.retrieval_agent.process(user_message, conversation_history)
        else:
            logger.info("Routing to WORKLOG agent")
            result = self.worklog_agent.process(user_message, conversation_history)

        logger.info("Request processing complete")
        logger.info("=" * 80)
        return result


# Global coordinator instance
coordinator = CoordinatorAgent()
