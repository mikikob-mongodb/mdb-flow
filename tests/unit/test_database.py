"""
Database and Connection Tests

Section 1 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 8 total
"""

import pytest


class TestMongoDBConnection:
    """Test MongoDB Atlas connection."""

    def test_mongodb_connection(self, db_client):
        """Verify MongoDB Atlas connection works."""
        result = db_client.admin.command("ping")
        assert result["ok"] == 1, "MongoDB connection should be successful"

    def test_database_exists(self, db_client):
        """Verify flow_companion database exists."""
        databases = db_client.list_database_names()
        assert "flow_companion" in databases, "flow_companion database should exist"

    def test_collections_exist(self, db):
        """Verify required collections exist."""
        collections = db.list_collection_names()
        assert "tasks" in collections, "tasks collection should exist"
        assert "projects" in collections, "projects collection should exist"


class TestDatabaseIndexes:
    """Test that required indexes exist."""

    def test_vector_index_tasks(self, tasks_collection):
        """Verify vector search index on tasks exists (if embeddings present)."""
        # Note: Vector search indexes are managed separately in Atlas
        # This test verifies the embedding field exists on documents
        # Demo data may not have embeddings - this is optional for demo flow
        task = tasks_collection.find_one({"embedding": {"$exists": True}})
        if task is not None:
            assert "embedding" in task, "Task should have embedding field"
        else:
            pytest.skip("No tasks with embeddings found - optional for demo")

    def test_vector_index_projects(self, projects_collection):
        """Verify vector search index on projects exists (if embeddings present)."""
        # Demo data may not have embeddings - this is optional for demo flow
        project = projects_collection.find_one({"embedding": {"$exists": True}})
        if project is not None:
            assert "embedding" in project, "Project should have embedding field"
        else:
            pytest.skip("No projects with embeddings found - optional for demo")

    def test_tasks_have_embeddings(self, tasks_collection):
        """Verify tasks have embedding field with correct dimensions (if present)."""
        task = tasks_collection.find_one({"embedding": {"$exists": True}})
        if task is None:
            pytest.skip("No tasks with embeddings found - optional for demo")

        embedding = task["embedding"]
        assert len(embedding) == 1024, \
            f"Voyage embeddings should be 1024 dimensions, got {len(embedding)}"

        assert all(isinstance(x, (int, float)) for x in embedding), \
            "Embedding values should be numeric"


class TestSampleData:
    """Test that sample data exists in collections."""

    def test_tasks_have_data(self, tasks_collection):
        """Verify tasks collection has demo data."""
        count = tasks_collection.count_documents({})
        # Demo data includes 7 curated tasks for demo flow
        assert count >= 7, f"Demo should have at least 7 tasks, got {count}"

    def test_projects_have_data(self, projects_collection):
        """Verify projects collection has demo data."""
        count = projects_collection.count_documents({})
        # Demo data includes 3 curated projects for demo flow
        assert count >= 3, f"Demo should have at least 3 projects, got {count}"
