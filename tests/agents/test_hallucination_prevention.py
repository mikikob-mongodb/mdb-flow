"""
Hallucination Prevention Regression Tests

Critical tests to prevent the LLM from hallucinating actions instead of using tools.

Bug History:
- Jan 4, 2026: LLM was responding "I found 1 task matching..." without calling search_tasks
- LLM was hallucinating that it performed actions when it never called the tools
- System prompt was updated to explicitly forbid hallucination

These tests ensure:
1. LLM ALWAYS calls tools when needed
2. LLM NEVER responds with "I found X" without calling search
3. LLM NEVER claims to perform actions without calling the tool
4. Search → Confirm → Execute flow is always followed
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from bson import ObjectId


def create_tool_use_mock(tool_name, tool_input, tool_id="toolu_test"):
    """Helper to create properly configured tool use mock."""
    mock = Mock()
    mock.type = "tool_use"
    mock.name = tool_name
    mock.id = tool_id
    mock.input = tool_input
    return mock


def create_text_mock(text):
    """Helper to create properly configured text block mock."""
    mock = Mock()
    mock.type = "text"
    mock.text = text
    return mock


class TestToolUseEnforcement:
    """Verify LLM always uses tools and never responds without them."""

    def test_always_calls_search_for_task_queries(self, coordinator_instance):
        """Verify LLM calls search_tasks for any task search query."""
        # Mock LLM responses using helpers
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("search_tasks", {"query": "debugging task", "limit": 5}, "toolu_search")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("I found 1 task matching...")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.retrieval_agent, 'hybrid_search_tasks') as mock_search:
                mock_search.return_value = [{
                    "_id": str(ObjectId()),
                    "title": "Debugging",
                    "status": "todo"
                }]

                response = coordinator_instance.process(
                    "Find the debugging task",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # CRITICAL: LLM must call search_tasks
                assert mock_search.called, "HALLUCINATION DETECTED: LLM did not call search_tasks"

                # Verify tool was called via coordinator
                tool_names = [tc["name"] for tc in coordinator_instance.current_turn["tool_calls"]]
                assert "search_tasks" in tool_names, "search_tasks must be in tool calls"

    def test_never_responds_without_tool_for_list_query(self, coordinator_instance):
        """Verify LLM calls get_tasks for 'list tasks' queries, never responds from memory."""
        # Mock LLM responses using helpers
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("get_tasks", {}, "toolu_get")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("Here are your tasks:")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_list:
                mock_list.return_value = {
                    "success": True,
                    "tasks": [{"title": "Task 1"}]
                }

                response = coordinator_instance.process(
                    "What tasks do I have?",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # CRITICAL: Must call get_tasks, not respond from memory
                assert mock_list.called, "HALLUCINATION: LLM did not call get_tasks"

                # Verify first LLM response was tool_use, not end_turn
                assert mock_response.stop_reason == "tool_use", "First LLM call should be tool_use"

    def test_never_claims_action_without_calling_tool(self, coordinator_instance):
        """Verify LLM never says 'I completed X' without calling complete_task."""
        # Mock LLM responses using helpers
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("search_tasks", {"query": "debugging task", "limit": 5}, "toolu_search")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("Found 1 task. Is this the one you want to complete?")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.retrieval_agent, 'hybrid_search_tasks') as mock_search:
                mock_search.return_value = [{
                    "_id": str(ObjectId()),
                    "title": "Debugging",
                    "status": "todo"
                }]

                response = coordinator_instance.process(
                    "Mark debugging task as done",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # First turn: should search and ask for confirmation
                assert mock_search.called, "Should search first"
                assert "confirm" in response.lower() or "is this" in response.lower(), \
                    "Should ask for confirmation, not claim to complete"

                # Verify LLM did NOT call complete_task yet
                tool_names = [tc["name"] for tc in coordinator_instance.current_turn["tool_calls"]]
                assert "complete_task" not in tool_names, \
                    "HALLUCINATION: Should not call complete_task without confirmation"


class TestSearchConfirmExecuteFlow:
    """Verify the search → confirm → execute pattern for actions."""

    def test_action_requires_search_first(self, coordinator_instance):
        """Verify actions always search first, never execute directly."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("search_tasks", {"query": "note task", "limit": 5}, "toolu_search")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("Is this the task?")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.retrieval_agent, 'hybrid_search_tasks') as mock_search:
                mock_search.return_value = [{"_id": str(ObjectId()), "title": "Add notes"}]

                response = coordinator_instance.process(
                    "Add a note to the task - Fixed bug",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                )

                # CRITICAL: First tool must be search, not add_note
                first_tool = coordinator_instance.current_turn["tool_calls"][0]
                assert first_tool["name"] == "search_tasks", \
                    "First tool must be search_tasks, not direct action"

    def test_confirmation_turn_then_executes(self, coordinator_instance):
        """Verify after user confirms, LLM executes the action."""
        # Turn 2: User confirms "yes"
        task_id = str(ObjectId())
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("complete_task", {"task_id": task_id}, "toolu_complete")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("✓ Marked task as complete")]

        # Conversation history shows previous search
        history = [
            {"role": "user", "content": "Mark debugging task as done"},
            {"role": "assistant", "content": "Found 1 task. Is this the one?"}
        ]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_complete_task') as mock_complete:
                mock_complete.return_value = {"success": True, "task": {"status": "done"}}

                response = coordinator_instance.process(
                    "Yes",
                    conversation_history=history,
                    input_type="text",
                    turn_number=2
                )

                # Now LLM should execute the action
                assert mock_complete.called, "Should complete task after confirmation"
                tool_names = [tc["name"] for tc in coordinator_instance.current_turn["tool_calls"]]
                assert "complete_task" in tool_names, "Should call complete_task after 'yes'"


class TestSystemPromptEnforcement:
    """Verify system prompt directives are being followed."""

    def test_llm_receives_all_tools(self, coordinator_instance):
        """Verify all 20 tools are passed to LLM."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [create_text_mock("Response")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.return_value = mock_response

            coordinator_instance.process(
                "Test query",
                conversation_history=[],
                input_type="text",
                turn_number=1
            )

            # Verify tools parameter in LLM call
            call_args = mock_llm.call_args
            tools_passed = call_args[1].get('tools', [])

            assert len(tools_passed) == 20, f"Should pass 20 tools to LLM, got {len(tools_passed)}"

            # Verify key tools are present
            tool_names = [t['name'] for t in tools_passed]
            assert "search_tasks" in tool_names, "search_tasks must be in tools"
            assert "create_task" in tool_names, "create_task must be in tools"
            assert "complete_task" in tool_names, "complete_task must be in tools"

    def test_system_prompt_includes_tool_enforcement(self, coordinator_instance):
        """Verify system prompt includes hallucination prevention directives."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [create_text_mock("Response")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.return_value = mock_response

            coordinator_instance.process(
                "Test query",
                conversation_history=[],
                input_type="text",
                turn_number=1
            )

            # Verify system parameter in LLM call
            call_args = mock_llm.call_args
            system_prompt = call_args[1].get('system', '')

            # Check for critical hallucination prevention phrases
            assert "ALWAYS USE TOOLS" in system_prompt, \
                "System prompt must include 'ALWAYS USE TOOLS' directive"
            assert "NEVER" in system_prompt and "without" in system_prompt, \
                "System prompt must forbid responding without tools"
            assert "HALLUCINATING" in system_prompt or "LYING" in system_prompt, \
                "System prompt must warn against hallucination"


class TestVoiceInputHallucinationPrevention:
    """Verify hallucination prevention works for voice input too."""

    def test_voice_input_also_requires_tools(self, coordinator_instance):
        """Verify voice input has same tool use requirements as text."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [create_tool_use_mock("search_tasks", {"query": "voice task", "limit": 5}, "toolu_voice")]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [create_text_mock("Found tasks")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response, mock_response_2]

            with patch.object(coordinator_instance.retrieval_agent, 'hybrid_search_tasks') as mock_search:
                mock_search.return_value = [{"_id": str(ObjectId()), "title": "Voice task"}]

                response = coordinator_instance.process(
                    "Find the voice task",
                    conversation_history=[],
                    input_type="voice",  # Voice input
                    turn_number=1
                )

                # Voice input must also use tools
                assert mock_search.called, "Voice input must also call search_tasks"


class TestNoToolUseDetection:
    """Tests that detect when LLM fails to use tools (regression detection)."""

    def test_detects_text_only_response_for_search(self, coordinator_instance, caplog):
        """Detect if LLM responds with text instead of calling search."""
        # This is the HALLUCINATION scenario we're preventing
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"  # BAD: Should be "tool_use"
        mock_response.content = [create_text_mock("I found 1 task matching 'debugging':")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.return_value = mock_response

            response = coordinator_instance.process(
                "Find debugging task",
                conversation_history=[],
                input_type="text",
                turn_number=1
            )

            # Verify that hallucination was detected and logged
            tool_calls = coordinator_instance.current_turn.get("tool_calls", [])
            assert len(tool_calls) == 0, "No tools should be called when LLM hallucinates"

            # Verify warning was logged
            assert "NO TOOLS CALLED" in caplog.text, \
                "System should log warning when LLM responds without calling tools"

    def test_detects_action_claim_without_tool(self, coordinator_instance, caplog):
        """Detect if LLM claims to complete action without calling tool."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"  # BAD: Should call complete_task first
        mock_response.content = [create_text_mock("✓ Marked task as complete")]

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.return_value = mock_response

            response = coordinator_instance.process(
                "Mark task 123 as done",
                conversation_history=[],
                input_type="text",
                turn_number=1
            )

            # Verify that hallucination was detected
            tool_calls = coordinator_instance.current_turn.get("tool_calls", [])
            assert len(tool_calls) == 0, "No tools should be called when LLM hallucinates"

            # Verify warning was logged
            assert "NO TOOLS CALLED" in caplog.text, \
                "System should log warning when LLM claims action without calling tools"

            # LLM responded with completion claim
            assert "✓" in response or "complete" in response.lower(), \
                "LLM hallucinated a completion response"
