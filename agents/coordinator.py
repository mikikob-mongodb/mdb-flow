"""Coordinator Agent that routes requests to appropriate sub-agents."""

import json
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
        try:
            response = self.llm.generate(
                messages=[{"role": "user", "content": f"Parse this voice transcript:\n\n{transcript}"}],
                system=system_prompt,
                max_tokens=2000,
                temperature=0.0
            )

            # Parse JSON response
            parsed = json.loads(response.strip())

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

            return parsed

        except Exception as e:
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
        Process voice input with special handling for stream-of-consciousness updates.

        Args:
            transcript: Voice transcript

        Returns:
            Summary of what was captured and actions taken
        """
        print(f"[COORDINATOR] Processing voice input: {transcript[:100]}...")

        # Parse the voice input to extract structured data
        parsed = self.parse_voice_input(transcript)

        # Build a summary of actions
        actions_taken = []
        clarifications_needed = []
        new_items_pending = []

        # 1. Process task references (completions, progress updates, deferrals)
        if parsed["task_references"]:
            for ref in parsed["task_references"]:
                # Try to fuzzy match the task
                match_result = self.retrieval_agent.fuzzy_match_task(
                    reference=ref.get("mention", ""),
                    threshold=0.7
                )

                if match_result.get("match"):
                    # Found a clear match
                    task = match_result["match"]
                    task_id = task["_id"]

                    # Check if this task was mentioned in completions
                    for completion in parsed["completions"]:
                        if ref["mention"].lower() in completion["what"].lower():
                            # Mark as completed
                            result = self.worklog_agent.apply_voice_update(
                                task_id=task_id,
                                updates={"status": "done"},
                                voice_log_entry={
                                    "summary": parsed["cleaned_summary"],
                                    "raw_transcript": transcript,
                                    "extracted": parsed
                                }
                            )
                            actions_taken.append(f"✓ Marked '{task['title']}' as done")

                    # Check for progress updates
                    for progress in parsed["progress_updates"]:
                        if ref["mention"].lower() in progress["what"].lower():
                            # Add progress note
                            note = f"{progress['status']}: {progress.get('details', '')}"
                            result = self.worklog_agent.apply_voice_update(
                                task_id=task_id,
                                updates={"notes_to_add": [note]},
                                voice_log_entry={
                                    "summary": parsed["cleaned_summary"],
                                    "raw_transcript": transcript,
                                    "extracted": parsed
                                }
                            )
                            actions_taken.append(f"📝 Added progress update to '{task['title']}'")

                    # Check for deferrals
                    for deferral in parsed["deferrals"]:
                        if ref["mention"].lower() in deferral["what"].lower():
                            # Add deferral note
                            note = f"Deferred to {deferral['when']}: {deferral.get('reason', '')}"
                            result = self.worklog_agent.apply_voice_update(
                                task_id=task_id,
                                updates={"notes_to_add": [note]},
                                voice_log_entry={
                                    "summary": parsed["cleaned_summary"],
                                    "raw_transcript": transcript,
                                    "extracted": parsed
                                }
                            )
                            actions_taken.append(f"⏸️ Deferred '{task['title']}' to {deferral['when']}")

                elif match_result.get("alternatives"):
                    # Ambiguous - ask for clarification
                    alt_titles = [alt["title"] for alt in match_result["alternatives"][:3]]
                    clarifications_needed.append(
                        f"❓ Which task did you mean by '{ref['mention']}'?\n  - " + "\n  - ".join(alt_titles)
                    )

        # 2. Process project references with context updates
        if parsed["project_references"]:
            for ref in parsed["project_references"]:
                # Try to fuzzy match the project
                match_result = self.retrieval_agent.fuzzy_match_project(
                    reference=ref.get("mention", ""),
                    threshold=0.7
                )

                if match_result.get("match"):
                    project = match_result["match"]
                    project_id = project["_id"]

                    # Check for context updates
                    for context_update in parsed["context_updates"]:
                        if ref["mention"].lower() in context_update["target"].lower():
                            # Add context to project
                            result = self.worklog_agent.apply_voice_update(
                                project_id=project_id,
                                updates={"context": context_update["context"]},
                                voice_log_entry={
                                    "summary": parsed["cleaned_summary"],
                                    "raw_transcript": transcript,
                                    "extracted": parsed
                                }
                            )
                            actions_taken.append(f"📋 Updated context for '{project['name']}'")

        # 3. Handle decisions
        if parsed["decisions"]:
            # Try to infer which project these decisions belong to
            for decision in parsed["decisions"]:
                decision_text = f"{decision['decision']}"
                if decision.get("reasoning"):
                    decision_text += f" - Reasoning: {decision['reasoning']}"

                # For now, just add to notes
                actions_taken.append(f"💡 Captured decision: {decision['decision']}")

        # 4. Handle general notes
        if parsed["notes_to_add"]:
            for note in parsed["notes_to_add"]:
                actions_taken.append(f"📝 Noted: {note['note']}")

        # 5. Handle new items - ask for confirmation
        if parsed["new_items"]:
            for item in parsed["new_items"]:
                source_info = f" (from: {item['source']})" if item.get("source") else ""
                new_items_pending.append(
                    f"Should I create a task: '{item['task']}'{source_info}?"
                )

        # Build response
        response_parts = []

        if parsed["cleaned_summary"]:
            response_parts.append(f"**Voice Update Received:** {parsed['cleaned_summary']}\n")

        if actions_taken:
            response_parts.append("**Actions taken:**")
            response_parts.extend(actions_taken)
            response_parts.append("")

        if clarifications_needed:
            response_parts.append("**Need clarification:**")
            response_parts.extend(clarifications_needed)
            response_parts.append("")

        if new_items_pending:
            response_parts.append("**New items mentioned:**")
            response_parts.extend(new_items_pending)
            response_parts.append("")

        if not actions_taken and not clarifications_needed and not new_items_pending:
            response_parts.append("I captured your update but didn't find any specific actions to take. Could you clarify what you'd like me to do?")

        return "\n".join(response_parts)

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
        print(f"[COORDINATOR] User message: {user_message}")
        print(f"[COORDINATOR] Input type: {input_type}")

        # Handle voice input differently
        if input_type == "voice":
            return self._process_voice_input(user_message)

        # For text input, use normal routing
        # Determine intent
        intent = self._determine_intent(user_message, conversation_history)

        print(f"[COORDINATOR] Routing to: {intent.upper()} agent")

        # Route to appropriate agent
        if intent == "retrieval":
            return self.retrieval_agent.process(user_message, conversation_history)
        else:
            return self.worklog_agent.process(user_message, conversation_history)


# Global coordinator instance
coordinator = CoordinatorAgent()
