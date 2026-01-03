"""Test fixtures for mdb-flow test suite."""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from shared.models import Task, Project


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    task = Task(
        title="Create debugging methodologies doc",
        context="Document debugging best practices for the team",
        priority="high",
        status="in_progress"
    )
    task._id = ObjectId()
    task.embedding = [0.1] * 1024  # Mock embedding vector
    return task


@pytest.fixture
def sample_completed_task() -> Task:
    """Create a completed task for testing."""
    task = Task(
        title="Set up development environment",
        context="Install dependencies and configure settings",
        priority="medium",
        status="done"
    )
    task._id = ObjectId()
    task.completed_at = datetime.utcnow()
    task.embedding = [0.2] * 1024
    return task


@pytest.fixture
def sample_project() -> Project:
    """Create a sample project for testing."""
    project = Project(
        name="Voice Agent Architecture",
        description="Design and implement voice-based agent system",
        status="active"
    )
    project._id = ObjectId()
    project.embedding = [0.3] * 1024
    return project


@pytest.fixture
def sample_project_agentops() -> Project:
    """Create AgentOps sample project for testing."""
    project = Project(
        name="AgentOps Integration",
        description="Integrate AgentOps monitoring into the system",
        status="active"
    )
    project._id = ObjectId()
    project.embedding = [0.4] * 1024
    return project


@pytest.fixture
def mock_tasks_collection(sample_task, sample_completed_task):
    """Mock MongoDB tasks collection."""
    mock_collection = MagicMock()

    # Mock find operations
    def mock_find(query=None):
        mock_cursor = MagicMock()
        tasks = [sample_task, sample_completed_task]

        # Filter by status if specified
        if query and "status" in query:
            tasks = [t for t in tasks if t.status == query["status"]]

        # Filter by project_id if specified
        if query and "project_id" in query:
            tasks = [t for t in tasks if t.project_id == query.get("project_id")]

        mock_cursor.__iter__ = Mock(return_value=iter([t.model_dump() for t in tasks]))
        mock_cursor.sort = Mock(return_value=mock_cursor)
        return mock_cursor

    mock_collection.find = mock_find
    mock_collection.find_one = Mock(return_value=sample_task.model_dump())
    mock_collection.insert_one = Mock(return_value=Mock(inserted_id=ObjectId()))
    mock_collection.update_one = Mock(return_value=Mock(modified_count=1))

    return mock_collection


@pytest.fixture
def mock_projects_collection(sample_project, sample_project_agentops):
    """Mock MongoDB projects collection."""
    mock_collection = MagicMock()

    def mock_find(query=None):
        mock_cursor = MagicMock()
        projects = [sample_project, sample_project_agentops]

        if query and "status" in query:
            projects = [p for p in projects if p.status == query["status"]]

        mock_cursor.__iter__ = Mock(return_value=iter([p.model_dump() for p in projects]))
        mock_cursor.sort = Mock(return_value=mock_cursor)
        return mock_cursor

    mock_collection.find = mock_find
    mock_collection.find_one = Mock(return_value=sample_project.model_dump())
    mock_collection.insert_one = Mock(return_value=Mock(inserted_id=ObjectId()))
    mock_collection.update_one = Mock(return_value=Mock(modified_count=1))

    return mock_collection


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Here are your tasks:\n- Create debugging methodologies doc\n- Set up development environment"
    mock_llm.chat.return_value = "Task created successfully."
    return mock_llm


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    def mock_embed(*args, **kwargs):
        return [0.1] * 1024  # Return 1024-dim vector
    return mock_embed


@pytest.fixture
def mock_whisper_client():
    """Mock OpenAI Whisper client for audio transcription."""
    mock_client = MagicMock()
    mock_transcriptions = MagicMock()
    mock_transcriptions.create.return_value = "I finished the debugging documentation"
    mock_client.audio.transcriptions = mock_transcriptions
    return mock_client


@pytest.fixture
def coordinator_with_mocks(mock_llm_service, monkeypatch):
    """Create coordinator with mocked dependencies."""
    # Mock the database collections
    from agents import coordinator as coordinator_module

    # Create a fresh coordinator instance for testing
    from shared.llm import LLMService

    # Patch the LLM service
    monkeypatch.setattr(coordinator_module.coordinator, "llm", mock_llm_service)

    return coordinator_module.coordinator


# ============================================================================
# Slash Command Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def coordinator_instance():
    """Initialize coordinator once for all slash command tests."""
    from agents.coordinator import coordinator
    return coordinator


@pytest.fixture(scope="session")
def executor(coordinator_instance):
    """Initialize SlashCommandExecutor once for all tests."""
    from ui.slash_commands import SlashCommandExecutor
    return SlashCommandExecutor(coordinator_instance)


@pytest.fixture
def execute_command(executor):
    """Factory fixture to execute slash commands and return results."""
    from ui.slash_commands import parse_slash_command

    def _execute(command_str: str):
        """Execute a slash command and return the result."""
        parsed = parse_slash_command(command_str)
        if not parsed:
            return {"success": False, "error": f"Failed to parse command: {command_str}"}

        try:
            result = executor.execute(parsed)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    return _execute


@pytest.fixture
def validate_table_columns():
    """Fixture to validate table columns for different result types."""
    def _validate(result, expected_columns):
        """
        Validate that result data has expected columns/fields.

        Args:
            result: The command execution result
            expected_columns: List of required column names/fields

        Returns:
            bool: True if all columns present and valid
        """
        if not result.get("success"):
            return False

        data = result.get("result", {})

        # For list results, check first item has all fields
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            return all(col in first_item or first_item.get(col) is not None
                      for col in expected_columns)

        # For dict results (like project detail), check the structure
        if isinstance(data, dict):
            if data.get("type") == "project_detail":
                return all(col in data for col in expected_columns)
            # For single results, check fields
            return all(col in data for col in expected_columns)

        return False

    return _validate


@pytest.fixture
def validate_count_range():
    """Fixture to validate result count is within expected range."""
    def _validate(result, min_count=None, max_count=None, exact_count=None):
        """
        Validate result count is within expected range.

        Args:
            result: The command execution result
            min_count: Minimum expected count (inclusive)
            max_count: Maximum expected count (inclusive)
            exact_count: Exact expected count

        Returns:
            bool: True if count is valid
        """
        if not result.get("success"):
            return False

        data = result.get("result", {})

        # Get count from result
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = data.get("total_tasks", data.get("count", 0))
        else:
            return False

        if exact_count is not None:
            return count == exact_count

        if min_count is not None and count < min_count:
            return False

        if max_count is not None and count > max_count:
            return False

        return True

    return _validate
