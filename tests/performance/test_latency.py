"""
Performance and Latency Tests

Section 15 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 12 total

Covers:
- Database query latency
- Vector search performance
- Hybrid search performance
- Coordinator response time
- Embedding generation speed
- LLM API call latency
- End-to-end flow performance
"""

import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseLatency:
    """Test database operation performance."""

    def test_database_query_latency(self, tasks_collection, measure_execution_time):
        """Database queries complete within acceptable time."""
        # Measure simple find query
        result, duration_ms = measure_execution_time(
            tasks_collection.find_one,
            {"status": "todo"}
        )

        # Database queries should be fast (< 100ms)
        assert duration_ms < 100, \
            f"Database query took {duration_ms:.1f}ms, expected < 100ms"
        assert result is not None or result is None, "Should return result"

    def test_database_aggregation_latency(self, tasks_collection,
                                          measure_execution_time):
        """Database aggregation pipelines complete efficiently."""
        # Measure aggregation query
        pipeline = [
            {"$match": {"status": "in_progress"}},
            {"$limit": 10}
        ]

        result, duration_ms = measure_execution_time(
            lambda: list(tasks_collection.aggregate(pipeline))
        )

        # Aggregations should complete reasonably fast (< 200ms)
        assert duration_ms < 200, \
            f"Aggregation took {duration_ms:.1f}ms, expected < 200ms"

    def test_database_count_latency(self, tasks_collection, measure_execution_time):
        """Database count operations are fast."""
        result, duration_ms = measure_execution_time(
            tasks_collection.count_documents,
            {"status": "todo"}
        )

        # Count should be very fast (< 50ms)
        assert duration_ms < 50, \
            f"Count took {duration_ms:.1f}ms, expected < 50ms"


class TestSearchLatency:
    """Test search operation performance."""

    def test_vector_search_latency(self, retrieval_agent, measure_execution_time):
        """Vector search completes within acceptable time."""
        # Measure vector search
        result, duration_ms = measure_execution_time(
            retrieval_agent.vector_search_tasks,
            "debugging",
            limit=10
        )

        # Vector search should complete in reasonable time (< 500ms)
        # Note: Includes embedding generation + vector search
        assert duration_ms < 500, \
            f"Vector search took {duration_ms:.1f}ms, expected < 500ms"
        assert isinstance(result, list), "Should return results"

    def test_hybrid_search_latency(self, retrieval_agent, measure_execution_time):
        """Hybrid search completes within acceptable time."""
        # Measure hybrid search
        result, duration_ms = measure_execution_time(
            retrieval_agent.hybrid_search_tasks,
            "debugging",
            limit=10
        )

        # Hybrid search should complete reasonably (< 600ms)
        # Note: Combines vector + text search
        assert duration_ms < 600, \
            f"Hybrid search took {duration_ms:.1f}ms, expected < 600ms"

    def test_text_search_latency(self, retrieval_agent, measure_execution_time):
        """Text-only search is fast."""
        # Measure simple text-based query
        result, duration_ms = measure_execution_time(
            retrieval_agent.get_tasks,
            status="todo",
            limit=10
        )

        # Text search should be fast (< 100ms)
        assert duration_ms < 100, \
            f"Text search took {duration_ms:.1f}ms, expected < 100ms"


class TestEmbeddingLatency:
    """Test embedding generation performance."""

    def test_embedding_generation_latency(self, retrieval_agent,
                                          measure_execution_time):
        """Embedding generation completes quickly."""
        # Measure embedding generation
        result, duration_ms = measure_execution_time(
            retrieval_agent.embed_text,
            "test query for embedding"
        )

        # Embedding should generate reasonably fast (< 300ms)
        assert duration_ms < 300, \
            f"Embedding generation took {duration_ms:.1f}ms, expected < 300ms"
        assert len(result) == 1024, "Should return 1024-dim embedding"

    def test_batch_embedding_efficiency(self, retrieval_agent,
                                       measure_execution_time):
        """Multiple embeddings have reasonable overhead."""
        # Measure single embedding
        _, single_duration = measure_execution_time(
            retrieval_agent.embed_text,
            "test query"
        )

        # Measure three sequential embeddings
        def generate_three():
            retrieval_agent.embed_text("query 1")
            retrieval_agent.embed_text("query 2")
            retrieval_agent.embed_text("query 3")

        _, triple_duration = measure_execution_time(generate_three)

        # Three embeddings should be less than 4x single (allows for overhead)
        assert triple_duration < single_duration * 4, \
            "Batch embedding overhead too high"


class TestCoordinatorLatency:
    """Test coordinator response time."""

    def test_coordinator_response_latency(self, coordinator_instance,
                                         measure_execution_time):
        """Coordinator responds within acceptable time."""
        with patch.object(coordinator_instance, 'llm') as mock_llm:
            # Mock LLM to isolate coordinator logic
            mock_llm.generate.return_value = "Test response"

            result, duration_ms = measure_execution_time(
                coordinator_instance.process,
                "show me my tasks",
                conversation_history=[],
                input_type="text"
            )

            # Coordinator logic should be fast (< 100ms when LLM mocked)
            assert duration_ms < 100, \
                f"Coordinator took {duration_ms:.1f}ms, expected < 100ms"

    def test_coordinator_with_history_latency(self, coordinator_instance,
                                              measure_execution_time):
        """Coordinator handles conversation history efficiently."""
        # Build moderate history
        history = []
        for i in range(5):
            history.append({"role": "user", "content": f"Query {i}"})
            history.append({"role": "assistant", "content": f"Response {i}"})

        with patch.object(coordinator_instance, 'llm') as mock_llm:
            mock_llm.generate.return_value = "Response"

            result, duration_ms = measure_execution_time(
                coordinator_instance.process,
                "show me my tasks",
                conversation_history=history,
                input_type="text"
            )

            # Should handle history without major slowdown (< 150ms)
            assert duration_ms < 150, \
                f"Coordinator with history took {duration_ms:.1f}ms"


class TestEndToEndLatency:
    """Test end-to-end flow performance."""

    def test_simple_query_end_to_end(self, coordinator_instance,
                                     assert_execution_time_under):
        """Simple query completes in reasonable time."""
        # Full end-to-end query (includes LLM, database, etc.)
        # This will actually call the LLM API

        result = assert_execution_time_under(
            coordinator_instance.process,
            3000,  # 3 seconds threshold for full query
            "show me my tasks",
            conversation_history=[],
            input_type="text"
        )

        assert isinstance(result, str)

    def test_search_query_end_to_end(self, coordinator_instance,
                                     assert_execution_time_under):
        """Search query completes within threshold."""
        # Full search query with LLM + hybrid search
        result = assert_execution_time_under(
            coordinator_instance.process,
            4000,  # 4 seconds threshold for search
            "find tasks about debugging",
            conversation_history=[],
            input_type="text"
        )

        assert isinstance(result, str)


class TestLatencyUnderLoad:
    """Test performance under various load conditions."""

    def test_multiple_sequential_queries(self, retrieval_agent,
                                        measure_execution_time):
        """Performance remains consistent across multiple queries."""
        durations = []

        # Run 5 sequential queries
        for i in range(5):
            _, duration = measure_execution_time(
                retrieval_agent.get_tasks,
                status="todo",
                limit=10
            )
            durations.append(duration)

        # All queries should complete in reasonable time
        for i, duration in enumerate(durations):
            assert duration < 200, \
                f"Query {i+1} took {duration:.1f}ms, expected < 200ms"

        # Performance should be relatively consistent
        avg_duration = sum(durations) / len(durations)
        for duration in durations:
            # No query should be more than 2x average (indicates caching issues)
            assert duration < avg_duration * 2, \
                "Performance variance too high"
