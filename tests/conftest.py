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
