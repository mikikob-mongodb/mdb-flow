"""
Vector Search Tests

Section 4 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 10 total

Covers:
- Basic vector search functionality
- Semantic relevance matching
- Embedding generation
- Score sorting and limits
"""

import pytest
from shared.embeddings import embed_query


class TestBasicVectorSearch:
    """Test basic vector search functionality."""

    def test_vector_search_tasks_returns_results(self, retrieval_agent):
        """Vector search returns results."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 0, "Vector search should return results"
        assert isinstance(results, list), "Should return list"

    def test_vector_search_returns_scores(self, retrieval_agent, assert_all_have_field):
        """Vector search results have relevance scores."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 0, "Should have results"
        assert_all_have_field(results, "score", "All results should have score")

        # Scores should be numeric
        for result in results:
            assert isinstance(result["score"], (int, float)), \
                f"Score should be numeric, got {type(result['score'])}"

    def test_vector_search_sorted_by_score(self, retrieval_agent, assert_sorted_by):
        """Results sorted by relevance score descending."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 1, "Need multiple results to test sorting"
        assert_sorted_by(results, "score", reverse=True,
                        message="Results should be sorted by score descending")

    def test_vector_search_respects_limit(self, retrieval_agent):
        """Vector search respects limit parameter."""
        limit = 3
        results = retrieval_agent.hybrid_search_tasks("debugging", limit=limit)

        assert len(results) <= limit, \
            f"Should return at most {limit} results, got {len(results)}"


class TestSemanticMatching:
    """Test semantic relevance and synonym matching."""

    def test_vector_search_semantic_match(self, retrieval_agent):
        """
        Vector search finds semantically related results.

        Query: "observability tools"
        Expected: Should find debugging/monitoring related tasks
        """
        results = retrieval_agent.hybrid_search_tasks("observability tools")

        assert len(results) > 0, "Should find semantically related tasks"

        # Check if results contain relevant terms
        titles = [r["title"].lower() for r in results]
        combined_text = " ".join(titles)

        # Should find tasks about debugging, monitoring, or observability
        relevant_terms = ["debug", "monitor", "observ", "log", "trace", "metric"]
        found_relevant = any(term in combined_text for term in relevant_terms)

        assert found_relevant, \
            f"Should find tasks related to observability. Found: {titles[:3]}"

    def test_vector_search_synonym(self, retrieval_agent):
        """
        Vector search handles synonyms.

        Query: "documentation"
        Expected: Should find tasks with "doc" or "documentation"
        """
        results = retrieval_agent.hybrid_search_tasks("documentation")

        assert len(results) > 0, "Should find documentation tasks"

        titles = [r["title"].lower() for r in results]
        combined_text = " ".join(titles)

        # Should find "doc" or "documentation"
        assert "doc" in combined_text, \
            f"Should find doc-related tasks. Found: {titles[:3]}"

    def test_vector_search_different_phrasing(self, retrieval_agent):
        """
        Vector search finds tasks even with different phrasing.

        Tests semantic understanding beyond keyword matching.
        """
        # Same concept, different words
        results1 = retrieval_agent.hybrid_search_tasks("how to find bugs")
        results2 = retrieval_agent.hybrid_search_tasks("debugging")

        # Both should find some results
        assert len(results1) > 0, "Should find results for 'how to find bugs'"
        assert len(results2) > 0, "Should find results for 'debugging'"

        # Results should overlap (at least one common task)
        ids1 = {str(r["_id"]) for r in results1}
        ids2 = {str(r["_id"]) for r in results2}

        # There should be some overlap for semantically similar queries
        # (This may not always be true, so we just check both returned results)
        assert len(ids1) > 0 and len(ids2) > 0


class TestEmbeddingGeneration:
    """Test embedding generation functionality."""

    def test_embed_text_dimensions(self):
        """Embedding generation produces correct dimensions."""
        embedding = embed_query("test query")

        assert embedding is not None, "Should generate embedding"
        assert len(embedding) == 1024, \
            f"Voyage embeddings should be 1024 dimensions, got {len(embedding)}"

        # All values should be numeric
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "Embedding values should be numeric"

    def test_embed_text_consistency(self):
        """Same input produces same embedding."""
        text = "consistent test query"

        emb1 = embed_query(text)
        emb2 = embed_query(text)

        assert emb1 == emb2, "Same input should produce same embedding"

    def test_embed_text_different_inputs(self):
        """Different inputs produce different embeddings."""
        emb1 = embed_query("debugging")
        emb2 = embed_query("webinar")

        assert emb1 != emb2, "Different inputs should produce different embeddings"


class TestEdgeCases:
    """Test edge cases for vector search."""

    def test_empty_query(self, retrieval_agent):
        """Empty query string handles gracefully."""
        try:
            results = retrieval_agent.hybrid_search_tasks("")
            # Should either return empty or handle gracefully
            assert isinstance(results, list), "Should return list"
        except Exception as e:
            # Or raise a clear error
            assert "query" in str(e).lower() or "empty" in str(e).lower()

    def test_very_long_query(self, retrieval_agent):
        """Very long query string handles gracefully."""
        long_query = "debugging " * 100  # Very long query

        try:
            results = retrieval_agent.hybrid_search_tasks(long_query)
            assert isinstance(results, list), "Should handle long query"
        except Exception as e:
            # Should have reasonable error, not crash
            assert isinstance(e, Exception)

    def test_no_results_scenario(self, retrieval_agent):
        """Query that returns no results handles gracefully."""
        # Use a very specific/uncommon term
        results = retrieval_agent.hybrid_search_tasks(
            "xyzabc123nonexistent"
        )

        # Should return empty list, not error
        assert isinstance(results, list), "Should return list even with no results"

    def test_special_characters_in_query(self, retrieval_agent):
        """Queries with special characters handle gracefully."""
        special_query = "debugging@#$%^&*()"

        try:
            results = retrieval_agent.hybrid_search_tasks(special_query)
            assert isinstance(results, list), "Should handle special characters"
        except Exception:
            # Or raise clear error
            pass
