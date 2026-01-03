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
        """Verify vector search index on tasks exists."""
        # Note: Vector search indexes are managed separately in Atlas
        # This test verifies the embedding field exists on documents
        task = tasks_collection.find_one({"embedding": {"$exists": True}})
        assert task is not None, "Tasks should have embedding field for vector search"
        assert "embedding" in task, "Task should have embedding field"

    def test_vector_index_projects(self, projects_collection):
        """Verify vector search index on projects exists."""
        project = projects_collection.find_one({"embedding": {"$exists": True}})
        assert project is not None, "Projects should have embedding field for vector search"
        assert "embedding" in project, "Project should have embedding field"

    def test_tasks_have_embeddings(self, tasks_collection):
        """Verify tasks have embedding field with correct dimensions."""
        task = tasks_collection.find_one({"embedding": {"$exists": True}})
        assert task is not None, "At least one task should have embeddings"
        
        embedding = task["embedding"]
        assert len(embedding) == 1024, \
            f"Voyage embeddings should be 1024 dimensions, got {len(embedding)}"
        
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "Embedding values should be numeric"


class TestSampleData:
    """Test that sample data exists in collections."""

    def test_tasks_have_data(self, tasks_collection):
        """Verify tasks collection has documents."""
        count = tasks_collection.count_documents({})
        assert count >= 40, f"Tasks collection should have at least 40 documents, got {count}"

    def test_projects_have_data(self, projects_collection):
        """Verify projects collection has documents."""
        count = projects_collection.count_documents({})
        assert count >= 10, f"Projects collection should have at least 10 documents, got {count}"
