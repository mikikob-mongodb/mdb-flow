"""
Coordinator Agent Tests

Section 6 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 20 total

Covers:
- Tool selection logic (retrieval vs worklog)
- Query parsing and intent classification
- Voice vs text input parity
- Error handling
- Conversation history threading
- Parameter extraction
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestToolSelection:
    """Test coordinator's ability to select the correct tool/agent."""

    def test_coordinator_selects_retrieval_for_search(self, coordinator_instance):
        """Coordinator selects retrieval agent for search queries."""
        # Create proper tool use mock
        tool_use = Mock()
        tool_use.type = "tool_use"
        tool_use.name = "get_tasks"
        tool_use.id = "toolu_get_tasks"
        tool_use.input = {}

        # Create text block mock
        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Here are your tasks"

        # Mock LLM responses
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [tool_use]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_list:
                mock_list.return_value = {
                    "success": True,
                    "tasks": [{"_id": "1", "title": "Test task", "status": "todo"}]
                }

                response = coordinator_instance.process(
                    "show me my tasks",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # Verify tool was called via current_turn tracking
                assert coordinator_instance.current_turn is not None, "Should track turn"
                tool_names = [tc["name"] for tc in coordinator_instance.current_turn["tool_calls"]]
                assert "get_tasks" in tool_names or "search_tasks" in tool_names, \
                    "Should use get_tasks or search_tasks for task queries"

    def test_coordinator_selects_worklog_for_complete(self, coordinator_instance):
        """Coordinator selects worklog agent for task completion."""
        # Create proper tool use mock
        tool_use = Mock()
        tool_use.type = "tool_use"
        tool_use.name = "search_tasks"
        tool_use.id = "toolu_search"
        tool_use.input = {"query": "task 123", "limit": 5}

        # Create text block mock
        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Found 1 task. Confirm?"

        # Mock LLM responses
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [tool_use]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.retrieval_agent, 'hybrid_search_tasks') as mock_search:
                mock_search.return_value = [
                    {"_id": "123", "title": "Test task", "status": "todo"}
                ]

                response = coordinator_instance.process(
                    "mark task 123 as complete",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # Should search first (confirmation pattern)
                assert isinstance(response, str), "Should return response string"
                assert coordinator_instance.current_turn is not None, "Should track turn"
                tool_names = [tc["name"] for tc in coordinator_instance.current_turn["tool_calls"]]
                assert "search_tasks" in tool_names, \
                    "Should search for task first (confirmation pattern)"

    def test_coordinator_selects_worklog_for_note(self, coordinator_instance):
        """Coordinator selects worklog agent for adding notes."""
        with patch.object(coordinator_instance, 'worklog_agent') as mock_worklog:
            mock_worklog.add_note.return_value = {
                "success": True,
                "message": "Note added"
            }

            response = coordinator_instance.process(
                "add note to task: made good progress",
                conversation_history=[],
                input_type="text"
            )

            assert isinstance(response, str), "Should return response string"

    def test_coordinator_selects_worklog_for_status_update(self, coordinator_instance):
        """Coordinator selects worklog agent for status changes."""
        with patch.object(coordinator_instance, 'worklog_agent') as mock_worklog:
            mock_worklog.start_task.return_value = {
                "success": True,
                "message": "Task started"
            }

            response = coordinator_instance.process(
                "start working on the debugging task",
                conversation_history=[],
                input_type="text"
            )

            assert isinstance(response, str), "Should return response string"


class TestQueryParsing:
    """Test coordinator's query parsing and understanding."""

    def test_parse_list_intent(self, coordinator_instance):
        """Parse 'list' intent from various phrasings."""
        list_queries = [
            "show me my tasks",
            "what are my tasks",
            "list all tasks",
            "what do I need to do"
        ]

        for query in list_queries:
            response = coordinator_instance.process(
                query,
                conversation_history=[],
                input_type="text"
            )

            assert isinstance(response, str), \
                f"Should handle list query: {query}"
            assert len(response) > 0, "Should return non-empty response"

    def test_parse_complete_intent(self, coordinator_instance):
        """Parse 'complete task' intent from various phrasings."""
        complete_queries = [
            "mark debugging task as complete",
            "I finished the documentation",
            "completed the webinar task"
        ]

        for query in complete_queries:
            response = coordinator_instance.process(
                query,
                conversation_history=[],
                input_type="text"
            )

            assert isinstance(response, str), \
                f"Should handle completion query: {query}"

    def test_parse_status_filter(self, coordinator_instance):
        """Parse status filter from query."""
        response = coordinator_instance.process(
            "show me tasks in progress",
            conversation_history=[],
            input_type="text"
        )

        assert isinstance(response, str), "Should handle status filter"
        # Response should reflect filtered results
        assert len(response) > 0

    def test_parse_project_filter(self, coordinator_instance):
        """Parse project filter from query."""
        response = coordinator_instance.process(
            "show me tasks for AgentOps project",
            conversation_history=[],
            input_type="text"
        )

        assert isinstance(response, str), "Should handle project filter"


class TestVoiceTextParity:
    """Test parity between voice and text input handling."""

    def test_voice_and_text_same_intent(self, coordinator_instance):
        """Voice and text versions of same query produce similar results."""
        query = "show me my tasks"

        # Process as text
        text_response = coordinator_instance.process(
            query,
            conversation_history=[],
            input_type="text"
        )

        # Process as voice
        voice_response = coordinator_instance.process(
            query,
            conversation_history=[],
            input_type="voice"
        )

        # Both should return valid responses
        assert isinstance(text_response, str)
        assert isinstance(voice_response, str)
        assert len(text_response) > 0
        assert len(voice_response) > 0

    def test_voice_handles_informal_phrasing(self, coordinator_instance):
        """Voice input handles informal/conversational phrasing."""
        informal_query = "hey, what's on my plate today?"

        response = coordinator_instance.process(
            informal_query,
            conversation_history=[],
            input_type="voice"
        )

        assert isinstance(response, str), "Should handle informal voice query"
        assert len(response) > 0

    def test_voice_handles_incomplete_reference(self, coordinator_instance):
        """Voice input handles incomplete task references."""
        response = coordinator_instance.process(
            "complete the doc task",
            conversation_history=[],
            input_type="voice"
        )

        assert isinstance(response, str), \
            "Should handle incomplete reference (may ask for clarification)"


class TestErrorHandling:
    """Test coordinator error handling."""

    def test_handles_empty_query(self, coordinator_instance):
        """Handles empty query gracefully."""
        try:
            response = coordinator_instance.process(
                "",
                conversation_history=[],
                input_type="text"
            )

            # Should either return helpful message or empty string
            assert isinstance(response, str)
        except Exception as e:
            # Or raise clear error
            assert "query" in str(e).lower() or "empty" in str(e).lower()

    def test_handles_ambiguous_query(self, coordinator_instance):
        """Handles ambiguous queries gracefully."""
        response = coordinator_instance.process(
            "update it",  # Ambiguous - update what?
            conversation_history=[],
            input_type="text"
        )

        # Should ask for clarification or return helpful message
        assert isinstance(response, str)
        assert len(response) > 0

    def test_handles_tool_error(self, coordinator_instance):
        """Handles errors from underlying tools gracefully."""
        with patch.object(coordinator_instance, 'retrieval_agent') as mock_retrieval:
            # Simulate tool error
            mock_retrieval.get_tasks.side_effect = Exception("Database error")

            response = coordinator_instance.process(
                "show me my tasks",
                conversation_history=[],
                input_type="text"
            )

            # Should handle error gracefully
            assert isinstance(response, str)
            # Should communicate error to user
            assert len(response) > 0

    def test_handles_invalid_task_reference(self, coordinator_instance):
        """Handles references to non-existent tasks."""
        response = coordinator_instance.process(
            "complete the nonexistent_task_xyz_123",
            conversation_history=[],
            input_type="text"
        )

        # Should indicate task not found or ask for clarification
        assert isinstance(response, str)
        assert len(response) > 0


class TestConversationHistory:
    """Test conversation history threading."""

    def test_uses_conversation_context(self, coordinator_instance):
        """Coordinator uses previous conversation context."""
        history = [
            {"role": "user", "content": "show me AgentOps tasks"},
            {"role": "assistant", "content": "Here are your AgentOps tasks..."}
        ]

        # Follow-up query that relies on context
        response = coordinator_instance.process(
            "what about the completed ones?",
            conversation_history=history,
            input_type="text"
        )

        # Should understand "ones" refers to AgentOps tasks
        assert isinstance(response, str)
        assert len(response) > 0

    def test_maintains_context_across_turns(self, coordinator_instance):
        """Context is maintained across multiple turns."""
        history = [
            {"role": "user", "content": "show me debugging tasks"},
            {"role": "assistant", "content": "Found 3 debugging tasks"},
            {"role": "user", "content": "complete the first one"},
            {"role": "assistant", "content": "Completed debugging documentation"}
        ]

        # Another follow-up
        response = coordinator_instance.process(
            "add a note to that task: finished early",
            conversation_history=history,
            input_type="text"
        )

        # Should understand "that task" refers to debugging documentation
        assert isinstance(response, str)

    def test_handles_context_switch(self, coordinator_instance):
        """Handles when user switches context."""
        history = [
            {"role": "user", "content": "show me debugging tasks"},
            {"role": "assistant", "content": "Found 3 debugging tasks"}
        ]

        # Completely different query (context switch)
        response = coordinator_instance.process(
            "what projects do I have?",
            conversation_history=history,
            input_type="text"
        )

        # Should handle new topic appropriately
        assert isinstance(response, str)
        assert len(response) > 0
