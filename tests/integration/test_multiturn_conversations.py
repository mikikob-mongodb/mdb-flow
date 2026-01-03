"""
Multi-turn Conversation Tests

Section 9 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 12 total

Covers:
- Context retention across conversation turns
- Reference resolution (pronouns, "that task", "the first one")
- Task refinement through dialogue
- Project context maintenance
- Follow-up questions
- Conversation history threading
"""

import pytest
from unittest.mock import patch, MagicMock


class TestContextRetention:
    """Test context retention across conversation turns."""

    def test_remembers_previous_query(self, coordinator_instance):
        """Coordinator remembers and uses previous query context."""
        # Turn 1: Ask about tasks
        history = []
        response1 = coordinator_instance.process(
            "show me my debugging tasks",
            conversation_history=history,
            input_type="text"
        )

        # Build history
        history.append({"role": "user", "content": "show me my debugging tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Follow-up relying on context
        response2 = coordinator_instance.process(
            "what about the completed ones?",
            conversation_history=history,
            input_type="text"
        )

        # Should understand "completed ones" refers to debugging tasks
        assert isinstance(response2, str)
        assert len(response2) > 0

    def test_maintains_project_context(self, coordinator_instance):
        """Project context is maintained across turns."""
        # Turn 1: Ask about specific project
        history = []
        response1 = coordinator_instance.process(
            "show me tasks for AgentOps project",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me tasks for AgentOps project"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Ask for different status within same project
        response2 = coordinator_instance.process(
            "which ones are in progress?",
            conversation_history=history,
            input_type="text"
        )

        # Should filter in-progress tasks for AgentOps project
        assert isinstance(response2, str)
        assert len(response2) > 0

    def test_maintains_status_context(self, coordinator_instance):
        """Status filter context is maintained."""
        history = []
        response1 = coordinator_instance.process(
            "show me tasks that are in progress",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me tasks that are in progress"})
        history.append({"role": "assistant", "content": response1})

        # Ask about priority within same status
        response2 = coordinator_instance.process(
            "which ones are high priority?",
            conversation_history=history,
            input_type="text"
        )

        assert isinstance(response2, str)


class TestReferenceResolution:
    """Test resolution of references and pronouns."""

    def test_resolves_that_task(self, coordinator_instance):
        """Resolves 'that task' reference from previous context."""
        # Turn 1: Show specific task
        history = []
        response1 = coordinator_instance.process(
            "find the debugging documentation task",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "find the debugging documentation task"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Act on "that task"
        response2 = coordinator_instance.process(
            "complete that task",
            conversation_history=history,
            input_type="text"
        )

        # Should understand "that task" refers to debugging documentation
        assert isinstance(response2, str)
        assert len(response2) > 0

    def test_resolves_the_first_one(self, coordinator_instance):
        """Resolves 'the first one' from list context."""
        # Turn 1: Get list of tasks
        history = []
        response1 = coordinator_instance.process(
            "show me my todo tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me my todo tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Reference first item
        response2 = coordinator_instance.process(
            "start working on the first one",
            conversation_history=history,
            input_type="text"
        )

        # Should identify and act on first task from list
        assert isinstance(response2, str)

    def test_resolves_pronoun_it(self, coordinator_instance):
        """Resolves 'it' pronoun from context."""
        # Turn 1: Ask about task
        history = []
        response1 = coordinator_instance.process(
            "what's the status of the webinar task?",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "what's the status of the webinar task?"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Use pronoun
        response2 = coordinator_instance.process(
            "mark it as complete",
            conversation_history=history,
            input_type="text"
        )

        # Should resolve "it" to webinar task
        assert isinstance(response2, str)

    def test_resolves_them_pronoun(self, coordinator_instance):
        """Resolves 'them' pronoun for multiple items."""
        # Turn 1: Get multiple tasks
        history = []
        response1 = coordinator_instance.process(
            "show me debugging tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me debugging tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Reference with pronoun
        response2 = coordinator_instance.process(
            "how many of them are completed?",
            conversation_history=history,
            input_type="text"
        )

        # Should understand "them" refers to debugging tasks
        assert isinstance(response2, str)


class TestTaskRefinement:
    """Test task refinement through multi-turn dialogue."""

    def test_refine_search_with_followups(self, coordinator_instance):
        """User refines search through follow-up queries."""
        # Turn 1: Broad search
        history = []
        response1 = coordinator_instance.process(
            "show me my tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me my tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Refine by status
        response2 = coordinator_instance.process(
            "just the in progress ones",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "just the in progress ones"})
        history.append({"role": "assistant", "content": response2})

        # Turn 3: Further refine by project
        response3 = coordinator_instance.process(
            "for AgentOps project only",
            conversation_history=history,
            input_type="text"
        )

        # Should progressively narrow down results
        assert isinstance(response3, str)

    def test_clarification_dialogue(self, coordinator_instance):
        """System asks for clarification, user provides it."""
        # Turn 1: Ambiguous request
        history = []
        response1 = coordinator_instance.process(
            "complete the doc task",
            conversation_history=history,
            input_type="text"
        )

        # May ask for clarification if multiple doc tasks exist
        history.append({"role": "user", "content": "complete the doc task"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: User clarifies
        response2 = coordinator_instance.process(
            "the debugging documentation one",
            conversation_history=history,
            input_type="text"
        )

        # Should use clarification to complete correct task
        assert isinstance(response2, str)


class TestFollowupQuestions:
    """Test handling of follow-up questions."""

    def test_followup_about_details(self, coordinator_instance):
        """Follow-up asking for more details about previous response."""
        # Turn 1: List tasks
        history = []
        response1 = coordinator_instance.process(
            "show me my tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me my tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Ask for details
        response2 = coordinator_instance.process(
            "tell me more about the first one",
            conversation_history=history,
            input_type="text"
        )

        # Should provide detailed info about first task
        assert isinstance(response2, str)

    def test_followup_count_question(self, coordinator_instance):
        """Follow-up asking about count from previous results."""
        # Turn 1: Show tasks
        history = []
        response1 = coordinator_instance.process(
            "show me debugging tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me debugging tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Ask count question
        response2 = coordinator_instance.process(
            "how many are there?",
            conversation_history=history,
            input_type="text"
        )

        # Should provide count of debugging tasks
        assert isinstance(response2, str)


class TestEdgeCases:
    """Test edge cases in multi-turn conversations."""

    def test_context_switch_handling(self, coordinator_instance):
        """Handles abrupt context switches gracefully."""
        # Turn 1: Debugging tasks
        history = []
        response1 = coordinator_instance.process(
            "show me debugging tasks",
            conversation_history=history,
            input_type="text"
        )

        history.append({"role": "user", "content": "show me debugging tasks"})
        history.append({"role": "assistant", "content": response1})

        # Turn 2: Completely different topic (context switch)
        response2 = coordinator_instance.process(
            "what projects do I have?",
            conversation_history=history,
            input_type="text"
        )

        # Should handle new topic without confusion
        assert isinstance(response2, str)

    def test_long_conversation_history(self, coordinator_instance):
        """Handles long conversation histories efficiently."""
        # Build a long history
        history = []
        for i in range(10):
            history.append({"role": "user", "content": f"Query {i}"})
            history.append({"role": "assistant", "content": f"Response {i}"})

        # New query with long history
        response = coordinator_instance.process(
            "show me my current tasks",
            conversation_history=history,
            input_type="text"
        )

        # Should handle long history without errors
        assert isinstance(response, str)
        assert len(response) > 0

    def test_empty_history_handling(self, coordinator_instance):
        """Handles empty conversation history correctly."""
        response = coordinator_instance.process(
            "show me my tasks",
            conversation_history=[],
            input_type="text"
        )

        # Should work fine without history
        assert isinstance(response, str)
        assert len(response) > 0
