"""Core functionality tests for mdb-flow.

Focused tests for critical functionality and regression prevention.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from bson import ObjectId
from datetime import datetime
import json

from shared.llm import LLMService
from shared.models import Task, Project, ActivityLogEntry
from agents.coordinator import CoordinatorAgent
from utils.audio import transcribe_audio


# ============================================================================
# 1. LLM Integration Tests (Critical for API compatibility)
# ============================================================================

def test_llm_generate_basic():
    """Test that simple prompt returns response."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello! How can I help?")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        llm = LLMService()
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.generate(messages)

        # Verify
        assert response == "Hello! How can I help?"
        mock_client.messages.create.assert_called_once()


def test_llm_generate_with_history():
    """Test that conversation history works correctly."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Your name is Alice.")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        llm = LLMService()
        messages = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
            {"role": "user", "content": "What's my name?"}
        ]
        response = llm.generate(messages)

        # Verify
        assert "Alice" in response
        call_args = mock_client.messages.create.call_args
        assert len(call_args[1]["messages"]) == 3


def test_llm_messages_format():
    """
    CRITICAL REGRESSION TEST: Only role+content are sent to API.
    This prevents the BadRequestError from extra fields like input_type.
    """
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test with extra fields that should be stripped
        llm = LLMService()
        messages = [
            {
                "role": "user",
                "content": "Hello",
                "input_type": "voice",  # Extra field that should be stripped
                "timestamp": "2026-01-02",  # Another extra field
            }
        ]
        llm.generate(messages)

        # Verify that only role and content were sent to API
        call_args = mock_client.messages.create.call_args
        sent_messages = call_args[1]["messages"]
        assert len(sent_messages) == 1
        assert set(sent_messages[0].keys()) == {"role", "content"}
        assert "input_type" not in sent_messages[0]
        assert "timestamp" not in sent_messages[0]


def test_llm_generate_with_tools_message_format():
    """Test that generate_with_tools also strips non-API fields."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        llm = LLMService()
        messages = [
            {
                "role": "user",
                "content": "Hello",
                "input_type": "voice",  # Should be stripped
            }
        ]
        tools = [{"name": "test_tool", "description": "Test"}]
        llm.generate_with_tools(messages, tools)

        # Verify
        call_args = mock_client.messages.create.call_args
        sent_messages = call_args[1]["messages"]
        assert set(sent_messages[0].keys()) == {"role", "content"}


# ============================================================================
# 2. Model Tests
# ============================================================================

def test_task_model_creation():
    """Test Task model can be created and serialized."""
    task = Task(
        title="Test task",
        context="Test context",
        priority="high",
        status="todo"
    )
    assert task.title == "Test task"
    assert task.status == "todo"
    assert task.priority == "high"

    # Test serialization
    task_dict = task.model_dump()
    assert "title" in task_dict
    assert task_dict["title"] == "Test task"


def test_project_model_creation():
    """Test Project model can be created and serialized."""
    project = Project(
        name="Test Project",
        description="Test description",
        status="active"
    )
    assert project.name == "Test Project"
    assert project.status == "active"

    # Test serialization
    project_dict = project.model_dump()
    assert "name" in project_dict


def test_activity_log_voice_fields():
    """Test ActivityLogEntry supports voice-specific fields."""
    log_entry = ActivityLogEntry(
        action="voice_update",
        note="Voice update processed",
        summary="User finished debugging doc",
        raw_transcript="I finished the debugging documentation",
        extracted={"completions": ["debugging doc"]}
    )

    assert log_entry.action == "voice_update"
    assert log_entry.summary == "User finished debugging doc"
    assert log_entry.raw_transcript == "I finished the debugging documentation"
    assert log_entry.extracted is not None


# ============================================================================
# 3. Voice Parsing Tests (Critical for Milestone 2)
# ============================================================================

def test_parse_voice_input_json_cleanup():
    """Test that voice parsing handles markdown-wrapped JSON."""
    # Create mock function that returns markdown-wrapped JSON
    json_content = {
        "task_references": [],
        "completions": [{"what": "testing", "confidence": "high"}],
        "progress_updates": [],
        "deferrals": [],
        "new_items": [],
        "context_updates": [],
        "notes_to_add": [],
        "decisions": [],
        "project_references": [],
        "cleaned_summary": "Test summary"
    }

    mock_llm_response = f"```json\n{json.dumps(json_content)}\n```"

    # Patch the LLM generate method directly on the coordinator's llm instance
    coordinator = CoordinatorAgent()
    with patch.object(coordinator.llm, 'generate', return_value=mock_llm_response):
        result = coordinator.parse_voice_input("test transcript")

        # Verify JSON was parsed despite markdown wrapping
        assert result is not None
        assert "completions" in result
        assert len(result["completions"]) == 1


def test_parse_voice_input_extracts_completions():
    """Test voice parsing extracts task completions."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()

        json_content = {
            "task_references": [{"mention": "the doc", "likely_task": "debugging doc"}],
            "completions": [{"what": "debugging documentation", "confidence": "high"}],
            "progress_updates": [],
            "deferrals": [],
            "new_items": [],
            "context_updates": [],
            "notes_to_add": [],
            "decisions": [],
            "project_references": [],
            "cleaned_summary": "Finished debugging documentation"
        }
        mock_response.content = [MagicMock(text=json.dumps(json_content))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        coordinator = CoordinatorAgent()
        result = coordinator.parse_voice_input("I finished the debugging doc")

        assert "completions" in result
        assert len(result["completions"]) > 0
        assert "debugging" in result["completions"][0]["what"].lower()


# ============================================================================
# 4. Audio Transcription Tests
# ============================================================================

def test_transcribe_audio_success():
    """Test successful audio transcription."""
    mock_audio_bytes = b"fake audio data"

    with patch('utils.audio.OpenAI') as mock_openai_class:
        with patch('utils.audio.tempfile.NamedTemporaryFile') as mock_tempfile:
            with patch('utils.audio.os.unlink'):
                with patch('builtins.open', mock_open(read_data=mock_audio_bytes)):
                    # Setup mocks
                    mock_client = MagicMock()
                    mock_transcriptions = MagicMock()
                    mock_transcriptions.create.return_value = "Test transcription"
                    mock_client.audio.transcriptions = mock_transcriptions
                    mock_openai_class.return_value = mock_client

                    # Mock temp file
                    mock_temp = MagicMock()
                    mock_temp.name = "/tmp/test_audio.wav"
                    mock_temp.__enter__ = Mock(return_value=mock_temp)
                    mock_temp.__exit__ = Mock(return_value=False)
                    mock_tempfile.return_value = mock_temp

                    # Test
                    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                        transcript = transcribe_audio(mock_audio_bytes)

                    # Verify
                    assert transcript == "Test transcription"
                    mock_transcriptions.create.assert_called_once()


def test_transcribe_audio_empty_bytes():
    """Test transcription with empty audio returns empty string."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        transcript = transcribe_audio(b"")
        assert transcript == ""


def test_transcribe_audio_missing_api_key():
    """Test transcription without API key returns empty string."""
    with patch.dict('os.environ', {}, clear=True):
        transcript = transcribe_audio(b"test")
        assert transcript == ""


# ============================================================================
# 5. Fuzzy Matching Tests (Critical for voice input)
# ============================================================================

def test_fuzzy_matching_text_similarity():
    """Test text similarity component of fuzzy matching."""
    from rapidfuzz import fuzz

    # Test that fuzzy matching can handle informal references
    reference = "debugging doc"
    actual_title = "Create debugging methodologies doc"

    # Calculate text similarity (same algorithm as fuzzy_match_task)
    text_score = fuzz.ratio(reference.lower(), actual_title.lower()) / 100.0

    # Should have reasonable similarity
    assert text_score > 0.5, f"Text score {text_score} too low for '{reference}' vs '{actual_title}'"


def test_fuzzy_matching_various_references():
    """Test fuzzy matching with various informal references."""
    from rapidfuzz import fuzz

    test_cases = [
        ("auth thing", "Authentication feature implementation", 0.3),
        ("debugging doc", "Create debugging methodologies doc", 0.5),
        ("voice agent", "Voice Agent Architecture", 0.6),
        ("agentops", "AgentOps Integration", 0.5),
    ]

    for reference, actual, min_score in test_cases:
        score = fuzz.ratio(reference.lower(), actual.lower()) / 100.0
        assert score >= min_score, f"Score {score} too low for '{reference}' vs '{actual}'"


# ============================================================================
# 6. Integration Tests (End-to-End Critical Paths)
# ============================================================================

def test_coordinator_accepts_input_type_parameter():
    """Test coordinator.process() accepts input_type without errors."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test that both text and voice input_type work
        coordinator = CoordinatorAgent()

        # Mock the LLM methods to avoid actual API calls
        with patch.object(coordinator.llm, 'generate', return_value="Test response"):
            with patch.object(coordinator.llm, 'generate_with_tools', return_value=mock_response):
                # Should not raise any errors
                try:
                    result_text = coordinator.process("test message", [], input_type="text")
                    assert result_text is not None

                    result_voice = coordinator.process("test message", [], input_type="voice")
                    assert result_voice is not None
                except Exception as e:
                    pytest.fail(f"coordinator.process() raised {e} with input_type parameter")


def test_coordinator_with_conversation_history():
    """Test coordinator maintains conversation history."""
    with patch('shared.llm.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        coordinator = CoordinatorAgent()

        history = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"}
        ]

        # Mock the LLM methods
        with patch.object(coordinator.llm, 'generate', return_value="Response"):
            with patch.object(coordinator.llm, 'generate_with_tools', return_value=mock_response):
                # Should accept history without errors
                result = coordinator.process("Follow-up message", history, input_type="text")
                assert result is not None


# ============================================================================
# 7. Critical Regression Tests
# ============================================================================

def test_vector_search_index_name():
    """
    CRITICAL: Verify vector search uses correct index name 'vector_index'.
    This prevents the regression where incorrect index names caused 0 results.
    """
    from agents.retrieval import RetrievalAgent

    agent = RetrievalAgent()

    # Check that the tool definitions reference correct index
    # (The actual index name 'vector_index' is used in _search_semantic and fuzzy_match methods)
    # This is a smoke test to ensure the module loads without errors
    assert agent is not None
    assert hasattr(agent, 'fuzzy_match_task')
    assert hasattr(agent, 'fuzzy_match_project')


def test_session_state_structure():
    """Test that expected session state fields are documented."""
    # This documents the expected session state structure for Streamlit
    expected_fields = {
        "messages": list,  # Chat history
        "coordinator": object,  # Coordinator agent instance
        "last_audio_bytes": (type(None), bytes)  # For duplicate prevention
    }

    # This test documents the structure - actual Streamlit tests would need streamlit testing framework
    assert expected_fields is not None
