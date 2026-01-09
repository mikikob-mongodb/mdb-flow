"""Tests for Tool Discovery Store"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from bson import ObjectId

from memory.tool_discoveries import ToolDiscoveryStore


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    collection = MagicMock()
    db.__getitem__.return_value = collection
    return db


@pytest.fixture
def mock_embedding_fn():
    """Mock embedding function that returns a fixed vector"""
    def embed(text):
        # Return a 1024-dim vector (simplified for testing)
        return [0.1] * 1024
    return embed


@pytest.fixture
def store(mock_db, mock_embedding_fn):
    """Create a ToolDiscoveryStore with mocked dependencies"""
    return ToolDiscoveryStore(mock_db, embedding_fn=mock_embedding_fn)


class TestToolDiscoveryStore:
    """Test suite for ToolDiscoveryStore"""

    def test_init_creates_indexes(self, mock_db, mock_embedding_fn):
        """Test that initialization creates required indexes"""
        collection = mock_db["tool_discoveries"]

        store = ToolDiscoveryStore(mock_db, mock_embedding_fn)

        # Verify create_index was called multiple times
        assert collection.create_index.call_count >= 5

    def test_log_discovery_success(self, store, mock_db):
        """Test logging a successful discovery"""
        collection = mock_db["tool_discoveries"]
        collection.insert_one.return_value.inserted_id = ObjectId()

        discovery_id = store.log_discovery(
            user_request="What's the latest AI news?",
            intent="web_search",
            solution={
                "mcp_server": "tavily",
                "tool_used": "tavily-search",
                "arguments": {"query": "AI news", "max_results": 5}
            },
            result_preview="Recent AI developments include...",
            success=True,
            execution_time_ms=850,
            user_id="user-123"
        )

        # Verify insert_one was called
        assert collection.insert_one.called

        # Verify the document structure
        call_args = collection.insert_one.call_args[0][0]
        assert call_args["user_request"] == "What's the latest AI news?"
        assert call_args["intent"] == "web_search"
        assert call_args["solution"]["mcp_server"] == "tavily"
        assert call_args["solution"]["tool_used"] == "tavily-search"
        assert call_args["success"] is True
        assert call_args["execution_time_ms"] == 850
        assert call_args["times_used"] == 1
        assert call_args["promoted_to_static"] is False
        assert call_args["user_id"] == "user-123"
        assert "request_embedding" in call_args
        assert len(call_args["request_embedding"]) == 1024

    def test_log_discovery_without_embedding(self, mock_db):
        """Test logging discovery when embedding function is None"""
        store = ToolDiscoveryStore(mock_db, embedding_fn=None)
        collection = mock_db["tool_discoveries"]
        collection.insert_one.return_value.inserted_id = ObjectId()

        discovery_id = store.log_discovery(
            user_request="Search for AI news",
            intent="web_search",
            solution={
                "mcp_server": "tavily",
                "tool_used": "tavily-search",
                "arguments": {}
            },
            result_preview="Results...",
            success=True,
            execution_time_ms=500
        )

        # Verify embedding is None
        call_args = collection.insert_one.call_args[0][0]
        assert call_args["request_embedding"] is None

    def test_log_discovery_truncates_preview(self, store, mock_db):
        """Test that result preview is truncated to 500 chars"""
        collection = mock_db["tool_discoveries"]
        collection.insert_one.return_value.inserted_id = ObjectId()

        long_preview = "x" * 1000

        store.log_discovery(
            user_request="Test",
            intent="test",
            solution={
                "mcp_server": "test",
                "tool_used": "test",
                "arguments": {}
            },
            result_preview=long_preview,
            success=True,
            execution_time_ms=100
        )

        call_args = collection.insert_one.call_args[0][0]
        assert len(call_args["result_preview"]) == 500

    def test_log_discovery_invalid_solution(self, store):
        """Test that invalid solution format raises ValueError"""
        with pytest.raises(ValueError, match="Solution must contain"):
            store.log_discovery(
                user_request="Test",
                intent="test",
                solution={"mcp_server": "test"},  # Missing required fields
                result_preview="test",
                success=True,
                execution_time_ms=100
            )

    def test_find_similar_discovery_vector_search(self, store, mock_db):
        """Test finding similar discovery via vector search"""
        collection = mock_db["tool_discoveries"]

        # Mock aggregation result with similarity score
        mock_discovery = {
            "_id": ObjectId(),
            "user_request": "Latest AI news",
            "intent": "web_search",
            "solution": {
                "mcp_server": "tavily",
                "tool_used": "tavily-search",
                "arguments": {"query": "AI news"}
            },
            "times_used": 5,
            "similarity_score": 0.92
        }
        collection.aggregate.return_value = [mock_discovery]

        result = store.find_similar_discovery(
            user_request="Show me recent AI developments",
            similarity_threshold=0.85
        )

        # Verify aggregate was called with vector search pipeline
        assert collection.aggregate.called
        pipeline = collection.aggregate.call_args[0][0]
        assert pipeline[0]["$vectorSearch"]["path"] == "request_embedding"

        # Verify result
        assert result is not None
        assert result["solution"]["mcp_server"] == "tavily"

        # Verify times_used was incremented
        assert collection.update_one.called
        update_call = collection.update_one.call_args[0]
        assert "$inc" in update_call[1]
        assert update_call[1]["$inc"]["times_used"] == 1

    def test_find_similar_discovery_no_match(self, store, mock_db):
        """Test when no similar discovery is found"""
        collection = mock_db["tool_discoveries"]
        collection.aggregate.return_value = []
        collection.find_one.return_value = None  # No exact match either

        result = store.find_similar_discovery(
            user_request="Completely unrelated query",
            similarity_threshold=0.85
        )

        assert result is None

    def test_find_similar_discovery_exact_match_fallback(self, store, mock_db):
        """Test fallback to exact match when vector search fails"""
        collection = mock_db["tool_discoveries"]

        # Make aggregate fail
        collection.aggregate.side_effect = Exception("Vector search not available")

        # Mock exact match
        mock_discovery = {
            "_id": ObjectId(),
            "user_request": "Search AI news",
            "solution": {"mcp_server": "tavily", "tool_used": "tavily-search", "arguments": {}},
            "times_used": 3
        }
        collection.find_one.return_value = mock_discovery

        result = store.find_similar_discovery(
            user_request="Search AI news",
            similarity_threshold=0.85
        )

        # Verify fallback to find_one
        assert collection.find_one.called
        assert result is not None
        assert result["times_used"] == 4  # Incremented

    def test_get_popular_discoveries(self, store, mock_db):
        """Test retrieving popular discoveries"""
        collection = mock_db["tool_discoveries"]

        mock_discoveries = [
            {"_id": ObjectId(), "times_used": 10, "promoted_to_static": False},
            {"_id": ObjectId(), "times_used": 8, "promoted_to_static": False},
            {"_id": ObjectId(), "times_used": 5, "promoted_to_static": False}
        ]

        # Mock find chain
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_discoveries
        collection.find.return_value = mock_cursor

        results = store.get_popular_discoveries(
            min_uses=2,
            limit=20,
            exclude_promoted=True
        )

        # Verify query
        query_call = collection.find.call_args[0][0]
        assert query_call["times_used"] == {"$gte": 2}
        assert query_call["promoted_to_static"] is False

        # Verify sort and limit
        assert mock_cursor.sort.called
        assert mock_cursor.limit.called

        assert len(results) == 3
        assert results[0]["times_used"] == 10

    def test_mark_as_promoted(self, store, mock_db):
        """Test marking discovery as promoted"""
        collection = mock_db["tool_discoveries"]
        collection.update_one.return_value.modified_count = 1

        discovery_id = str(ObjectId())
        success = store.mark_as_promoted(
            discovery_id,
            notes="Promoted to static web_search tool"
        )

        assert success is True

        # Verify update
        update_call = collection.update_one.call_args[0]
        assert update_call[1]["$set"]["promoted_to_static"] is True
        assert update_call[1]["$set"]["developer_notes"] == "Promoted to static web_search tool"

    def test_mark_as_promoted_not_found(self, store, mock_db):
        """Test marking non-existent discovery"""
        collection = mock_db["tool_discoveries"]
        collection.update_one.return_value.modified_count = 0

        success = store.mark_as_promoted(str(ObjectId()))

        assert success is False

    def test_add_developer_notes(self, store, mock_db):
        """Test adding developer notes"""
        collection = mock_db["tool_discoveries"]
        collection.update_one.return_value.modified_count = 1

        discovery_id = str(ObjectId())
        success = store.add_developer_notes(
            discovery_id,
            "This pattern is very popular, consider static tool"
        )

        assert success is True

        # Verify update
        update_call = collection.update_one.call_args[0]
        assert "developer_notes" in update_call[1]["$set"]

    def test_get_stats(self, store, mock_db):
        """Test getting discovery statistics"""
        collection = mock_db["tool_discoveries"]

        # Mock count_documents
        collection.count_documents.side_effect = [100, 85, 15, 5]  # total, success, fail, promoted

        # Mock aggregation for avg_uses
        collection.aggregate.side_effect = [
            [{"_id": None, "avg_uses": 3.5}],  # avg_uses
            [{"_id": "tavily", "count": 50}],  # most_used_server
            [{"_id": "tavily-search", "count": 45}]  # most_used_tool
        ]

        stats = store.get_stats()

        assert stats["total_discoveries"] == 100
        assert stats["successful"] == 85
        assert stats["failed"] == 15
        assert stats["promoted"] == 5
        assert stats["avg_uses"] == 3.5
        assert stats["most_used_server"] == "tavily"
        assert stats["most_used_tool"] == "tavily-search"

    def test_get_discoveries_by_server(self, store, mock_db):
        """Test getting discoveries for specific server"""
        collection = mock_db["tool_discoveries"]

        mock_discoveries = [
            {"_id": ObjectId(), "solution": {"mcp_server": "tavily"}, "times_used": 10}
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_discoveries
        collection.find.return_value = mock_cursor

        results = store.get_discoveries_by_server("tavily", limit=10)

        # Verify query
        query_call = collection.find.call_args[0][0]
        assert query_call["solution.mcp_server"] == "tavily"

        assert len(results) == 1

    def test_get_discoveries_by_intent(self, store, mock_db):
        """Test getting discoveries by intent"""
        collection = mock_db["tool_discoveries"]

        mock_discoveries = [
            {"_id": ObjectId(), "intent": "web_search", "times_used": 15}
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_discoveries
        collection.find.return_value = mock_cursor

        results = store.get_discoveries_by_intent("web_search", limit=10)

        # Verify query
        query_call = collection.find.call_args[0][0]
        assert query_call["intent"] == "web_search"

        assert len(results) == 1

    def test_delete_discovery(self, store, mock_db):
        """Test deleting a discovery"""
        collection = mock_db["tool_discoveries"]
        collection.delete_one.return_value.deleted_count = 1

        discovery_id = str(ObjectId())
        success = store.delete_discovery(discovery_id)

        assert success is True
        assert collection.delete_one.called

    def test_delete_discovery_not_found(self, store, mock_db):
        """Test deleting non-existent discovery"""
        collection = mock_db["tool_discoveries"]
        collection.delete_one.return_value.deleted_count = 0

        success = store.delete_discovery(str(ObjectId()))

        assert success is False
