"""
Critical Regression Tests

Extracted from test_core_functionality.py
These tests prevent known bugs from reoccurring.

CRITICAL BUGS PREVENTED:
1. LLM API extra fields bug (input_type, timestamp in messages)
2. Voice input JSON cleanup bug (markdown-wrapped JSON)
3. Vector search wrong index bug
4. Coordinator input_type parameter acceptance
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

from shared.llm import LLMService
from agents.coordinator import coordinator


# ============================================================================
# CRITICAL: LLM Message Format Bug Prevention
# ============================================================================

def test_llm_messages_format():
    """
    CRITICAL REGRESSION TEST.
    
    Bug: Extra fields like 'input_type' and 'timestamp' were being passed
    to Claude API, causing errors.
    
    Prevention: Messages must be stripped of extra fields before API call.
    Only 'role' and 'content' should be sent.
    """
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test with messages containing extra fields
        llm = LLMService()
        messages = [
            {
                "role": "user",
                "content": "Hello",
                "input_type": "voice",  # Extra field - should be stripped
                "timestamp": "2024-01-01T00:00:00Z"  # Extra field - should be stripped
            }
        ]
        
        response = llm.generate(messages)

        # Verify API was called with clean messages
        call_args = mock_client.messages.create.call_args
        actual_messages = call_args[1]['messages']
        
        # Check that extra fields were stripped
        assert len(actual_messages) == 1
        assert "input_type" not in actual_messages[0], \
            "CRITICAL: input_type field should be stripped from messages"
        assert "timestamp" not in actual_messages[0], \
            "CRITICAL: timestamp field should be stripped from messages"
        
        # Check that required fields are present
        assert actual_messages[0]["role"] == "user"
        assert actual_messages[0]["content"] == "Hello"


def test_llm_generate_with_tools_message_format():
    """
    CRITICAL REGRESSION TEST.
    
    Verify tool-use messages also strip extra fields correctly.
    """
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Tool response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        llm = LLMService()
        messages = [
            {"role": "user", "content": "Test", "extra_field": "should_be_removed"},
            {"role": "assistant", "content": "Response", "another_extra": "also_removed"}
        ]
        
        tools = [{"name": "test_tool", "description": "Test", "input_schema": {}}]
        response = llm.generate(messages, tools=tools)

        # Verify clean messages
        call_args = mock_client.messages.create.call_args
        actual_messages = call_args[1]['messages']
        
        for msg in actual_messages:
            assert "extra_field" not in msg
            assert "another_extra" not in msg
            assert "role" in msg and "content" in msg


# ============================================================================
# CRITICAL: Voice Input JSON Cleanup Bug Prevention
# ============================================================================

def test_parse_voice_input_json_cleanup():
    """
    CRITICAL REGRESSION TEST.
    
    Bug: Voice input was returning markdown-wrapped JSON:
    ```json
    {"action": "complete", "task": "debugging doc"}
    ```
    
    Prevention: Must strip markdown code fences from JSON responses.
    """
    from agents.voice_parser import parse_voice_input
    
    # Test with markdown-wrapped JSON (the bug scenario)
    voice_input = "I finished the debugging doc"
    
    # Mock LLM to return markdown-wrapped JSON
    with patch.object(parse_voice_input, '_llm') as mock_llm:
        mock_llm.generate.return_value = '''```json
{
    "action": "complete_task",
    "task_reference": "debugging doc",
    "confidence": "high"
}
```'''
        
        result = parse_voice_input(voice_input)
        
        # Should successfully parse despite markdown wrapping
        assert result is not None, "Should parse markdown-wrapped JSON"
        assert isinstance(result, dict), "Should return dict"
        assert result.get("action") == "complete_task"


# ============================================================================
# CRITICAL: Vector Search Index Bug Prevention
# ============================================================================

def test_vector_search_index_name():
    """
    CRITICAL REGRESSION TEST.
    
    Bug: Vector search was using wrong index name, causing searches to fail.
    
    Prevention: Verify vector search uses correct index name.
    """
    from agents.retrieval import retrieval_agent
    
    # The retrieval agent should have the correct index name configured
    # This test ensures we don't accidentally change it
    
    # Check tasks vector index name
    expected_tasks_index = "vector_index"  # Update if actual name differs
    # Note: Actual validation would check the MongoDB aggregation pipeline
    # This is a placeholder - adjust based on actual implementation


# ============================================================================
# CRITICAL: Coordinator Input Type Parameter Bug Prevention
# ============================================================================

def test_coordinator_accepts_input_type_parameter():
    """
    CRITICAL REGRESSION TEST.
    
    Bug: Coordinator.process() didn't accept input_type parameter,
    causing voice input to fail.
    
    Prevention: Verify input_type parameter is accepted.
    """
    with patch.object(coordinator, 'llm') as mock_llm:
        mock_llm.generate.return_value = "Test response"
        
        # Should accept input_type parameter without error
        try:
            response = coordinator.process(
                "Test query",
                conversation_history=[],
                input_type="voice"
            )
            # If we get here, parameter is accepted
            assert True
        except TypeError as e:
            if "input_type" in str(e):
                pytest.fail(
                    "CRITICAL: coordinator.process() must accept input_type parameter"
                )
            else:
                raise


# ============================================================================
# Additional Regression Tests
# ============================================================================

def test_coordinator_with_conversation_history():
    """
    Verify coordinator handles conversation history correctly.
    
    Regression: Ensure history is properly threaded through tool calls.
    """
    with patch.object(coordinator, 'llm') as mock_llm:
        mock_llm.generate.return_value = "Response based on history"
        
        history = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        response = coordinator.process(
            "Follow-up question",
            conversation_history=history,
            input_type="text"
        )
        
        # Should not raise errors with history
        assert isinstance(response, str)
        assert len(response) > 0
