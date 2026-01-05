"""Integration tests for tool result compression with coordinator."""

import pytest
from unittest.mock import Mock, patch
from bson import ObjectId


class TestCoordinatorCompression:
    """Test that coordinator applies compression based on optimizations."""

    def test_coordinator_compresses_when_toggle_on(self, coordinator_instance):
        """Verify coordinator compresses results when compress_results=True."""
        # Create mock tool use and LLM responses
        tool_use = Mock()
        tool_use.type = "tool_use"
        tool_use.name = "get_tasks"
        tool_use.id = "toolu_test"
        tool_use.input = {}

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Here are your tasks"

        # First response: tool use
        mock_response_1 = Mock()
        mock_response_1.stop_reason = "tool_use"
        mock_response_1.content = [tool_use]

        # Second response: final answer
        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        # Create large task list (>10 tasks to trigger compression)
        large_task_list = {
            "success": True,
            "tasks": [
                {
                    "_id": str(ObjectId()),
                    "title": f"Task {i}",
                    "status": "todo" if i < 20 else "done",
                    "project_name": "Test Project",
                    "description": "Long description here..."  # Should be stripped
                }
                for i in range(50)
            ]
        }

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response_1, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_list:
                mock_list.return_value = large_task_list

                # Enable compression
                optimizations = {"compress_results": True}

                response = coordinator_instance.process(
                    "What are my tasks?",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1,
                    optimizations=optimizations
                )

                # Verify tool was called
                assert mock_list.called

                # Verify LLM received compressed result
                # Check the second LLM call (after tool execution)
                second_call_args = mock_llm.call_args_list[1]
                messages = second_call_args[1]['messages']

                # Find the tool result message
                tool_result_msg = None
                for msg in messages:
                    if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                        for content in msg["content"]:
                            if isinstance(content, dict) and content.get("type") == "tool_result":
                                tool_result_msg = content
                                break

                assert tool_result_msg is not None, "Should have tool result in messages"

                # Parse the tool result content
                import json
                result_content = json.loads(tool_result_msg["content"])

                # Verify compression was applied
                assert "total_count" in result_content, "Should have compressed format"
                assert result_content["total_count"] == 50
                assert "summary" in result_content
                assert "top_5" in result_content
                assert len(result_content["top_5"]) == 5

    def test_coordinator_no_compression_when_toggle_off(self, coordinator_instance):
        """Verify coordinator returns full results when compress_results=False."""
        # Create mock tool use and LLM responses
        tool_use = Mock()
        tool_use.type = "tool_use"
        tool_use.name = "get_tasks"
        tool_use.id = "toolu_test"
        tool_use.input = {}

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Here are your tasks"

        mock_response_1 = Mock()
        mock_response_1.stop_reason = "tool_use"
        mock_response_1.content = [tool_use]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        # Create large task list
        large_task_list = {
            "success": True,
            "tasks": [
                {"_id": str(ObjectId()), "title": f"Task {i}", "status": "todo"}
                for i in range(50)
            ]
        }

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response_1, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_list:
                mock_list.return_value = large_task_list

                # Disable compression
                optimizations = {"compress_results": False}

                response = coordinator_instance.process(
                    "What are my tasks?",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1,
                    optimizations=optimizations
                )

                # Verify tool was called
                assert mock_list.called

                # Verify LLM received full result (not compressed)
                second_call_args = mock_llm.call_args_list[1]
                messages = second_call_args[1]['messages']

                # Find the tool result message
                tool_result_msg = None
                for msg in messages:
                    if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                        for content in msg["content"]:
                            if isinstance(content, dict) and content.get("type") == "tool_result":
                                tool_result_msg = content
                                break

                assert tool_result_msg is not None

                # Parse the tool result content
                import json
                result_content = json.loads(tool_result_msg["content"])

                # Verify NO compression (full result)
                assert "tasks" in result_content, "Should have full tasks array"
                assert len(result_content["tasks"]) == 50, "Should have all 50 tasks"
                assert "total_count" not in result_content, "Should not have compression format"

    def test_coordinator_default_compression_on(self, coordinator_instance):
        """Verify compression is ON by default (when optimizations not provided)."""
        tool_use = Mock()
        tool_use.type = "tool_use"
        tool_use.name = "get_tasks"
        tool_use.id = "toolu_test"
        tool_use.input = {}

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Here are your tasks"

        mock_response_1 = Mock()
        mock_response_1.stop_reason = "tool_use"
        mock_response_1.content = [tool_use]

        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        large_task_list = {
            "success": True,
            "tasks": [
                {"_id": str(ObjectId()), "title": f"Task {i}", "status": "todo"}
                for i in range(50)
            ]
        }

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response_1, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_list:
                mock_list.return_value = large_task_list

                # Don't provide optimizations (test default behavior)
                response = coordinator_instance.process(
                    "What are my tasks?",
                    conversation_history=[],
                    input_type="text",
                    turn_number=1
                    # No optimizations parameter
                )

                # Verify compression was applied by default
                second_call_args = mock_llm.call_args_list[1]
                messages = second_call_args[1]['messages']

                tool_result_msg = None
                for msg in messages:
                    if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                        for content in msg["content"]:
                            if isinstance(content, dict) and content.get("type") == "tool_result":
                                tool_result_msg = content
                                break

                import json
                result_content = json.loads(tool_result_msg["content"])

                # Default should be compressed (toggle default is True in UI)
                assert "total_count" in result_content, "Default should compress"


class TestCompressionWithMultipleTools:
    """Test compression works with multiple tool calls in one turn."""

    def test_compression_applies_to_all_tools(self, coordinator_instance):
        """Verify compression applies to each tool result independently."""
        # Mock LLM to call both get_tasks and get_projects
        get_tasks_tool = Mock()
        get_tasks_tool.type = "tool_use"
        get_tasks_tool.name = "get_tasks"
        get_tasks_tool.id = "toolu_tasks"
        get_tasks_tool.input = {}

        get_projects_tool = Mock()
        get_projects_tool.type = "tool_use"
        get_projects_tool.name = "get_projects"
        get_projects_tool.id = "toolu_projects"
        get_projects_tool.input = {}

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Here's your overview"

        # First response: call both tools
        mock_response_1 = Mock()
        mock_response_1.stop_reason = "tool_use"
        mock_response_1.content = [get_tasks_tool, get_projects_tool]

        # Second response: final answer
        mock_response_2 = Mock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [text_block]

        # Large results for both
        large_task_list = {
            "tasks": [{"_id": str(ObjectId()), "title": f"Task {i}", "status": "todo"} for i in range(50)]
        }
        large_project_list = {
            "projects": [{"_id": str(ObjectId()), "name": f"Project {i}", "task_count": 10} for i in range(12)]
        }

        with patch.object(coordinator_instance.llm, 'generate_with_tools') as mock_llm:
            mock_llm.side_effect = [mock_response_1, mock_response_2]

            with patch.object(coordinator_instance.worklog_agent, '_list_tasks') as mock_tasks:
                with patch.object(coordinator_instance.worklog_agent, '_list_projects') as mock_projects:
                    mock_tasks.return_value = large_task_list
                    mock_projects.return_value = large_project_list

                    optimizations = {"compress_results": True}

                    response = coordinator_instance.process(
                        "Show me everything",
                        conversation_history=[],
                        input_type="text",
                        turn_number=1,
                        optimizations=optimizations
                    )

                    # Both tools should be compressed
                    second_call_args = mock_llm.call_args_list[1]
                    messages = second_call_args[1]['messages']

                    # Find tool results
                    tool_results = []
                    for msg in messages:
                        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                            for content in msg["content"]:
                                if isinstance(content, dict) and content.get("type") == "tool_result":
                                    tool_results.append(content)

                    assert len(tool_results) == 2, "Should have 2 tool results"

                    # Both should be compressed
                    import json
                    for result in tool_results:
                        parsed = json.loads(result["content"])
                        # Check for compression markers
                        assert "total_count" in parsed or "matches" in parsed, \
                            "Each result should be compressed"
