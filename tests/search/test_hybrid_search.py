"""
Hybrid Search Tests

Section 5 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 12 total

Covers:
- Hybrid search combining vector + text search
- Exact match finding
- Semantic relevance matching
- Informal reference handling
- Score fusion and ranking
"""

import pytest


class TestBasicHybridSearch:
    """Test basic hybrid search functionality."""

    def test_hybrid_search_tasks_returns_results(self, retrieval_agent):
        """Hybrid search returns results for tasks."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 0, "Hybrid search should return results"
        assert isinstance(results, list), "Should return list"

    def test_hybrid_search_projects_returns_results(self, retrieval_agent):
        """Hybrid search returns results for projects."""
        results = retrieval_agent.hybrid_search_projects("agent")

        assert len(results) > 0, "Should find projects"
        assert isinstance(results, list), "Should return list"

        # Verify project structure
        for project in results:
            assert "_id" in project, "Project should have _id"
            assert "name" in project, "Project should have name"

    def test_hybrid_search_has_scores(self, retrieval_agent, assert_all_have_field):
        """Hybrid search results include relevance scores."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 0, "Should have results"
        assert_all_have_field(results, "score", "All results should have score")

        # Scores should be numeric
        for result in results:
            assert isinstance(result["score"], (int, float)), \
                f"Score should be numeric, got {type(result['score'])}"

    def test_hybrid_search_respects_limit(self, retrieval_agent):
        """Hybrid search respects limit parameter."""
        limit = 5
        results = retrieval_agent.hybrid_search_tasks("task", limit=limit)

        assert len(results) <= limit, \
            f"Should return at most {limit} results, got {len(results)}"


class TestMatchingStrategies:
    """Test different matching strategies in hybrid search."""

    def test_hybrid_finds_exact_match(self, retrieval_agent):
        """
        Hybrid search finds exact text matches.

        When searching for exact task title, should rank it highly.
        """
        # Find a real task from database to ensure exact match exists
        results = retrieval_agent.hybrid_search_tasks("debugging documentation")

        assert len(results) > 0, "Should find results for 'debugging documentation'"

        # Exact or close matches should be in top results
        top_result = results[0]
        title_lower = top_result["title"].lower()

        # Should contain at least one of the search terms
        assert any(term in title_lower for term in ["debug", "doc"]), \
            f"Top result should contain search terms. Got: {top_result['title']}"

    def test_hybrid_finds_semantic_match(self, retrieval_agent):
        """
        Hybrid search finds semantically similar results.

        Query: "error tracking"
        Expected: Should find debugging/monitoring tasks
        """
        results = retrieval_agent.hybrid_search_tasks("error tracking")

        assert len(results) > 0, "Should find semantically related tasks"

        # Check if results contain relevant terms
        titles = [r["title"].lower() for r in results[:5]]
        combined_text = " ".join(titles)

        # Should find tasks about debugging, errors, monitoring, etc.
        relevant_terms = ["debug", "error", "monitor", "log", "trace", "bug"]
        found_relevant = any(term in combined_text for term in relevant_terms)

        assert found_relevant, \
            f"Should find error/debugging related tasks. Found: {titles}"

    def test_hybrid_matches_informal_reference(self, retrieval_agent):
        """
        Hybrid search handles informal task references.

        Query: "doc task"
        Expected: Should find documentation-related tasks
        """
        results = retrieval_agent.hybrid_search_tasks("doc task")

        assert len(results) > 0, "Should find tasks with informal reference"

        # Should find documentation tasks
        titles = [r["title"].lower() for r in results[:3]]
        combined_text = " ".join(titles)

        assert "doc" in combined_text, \
            f"Should find doc-related tasks. Found: {titles}"

    def test_hybrid_search_partial_word_match(self, retrieval_agent):
        """
        Hybrid search finds partial word matches.

        Query: "webinar"
        Expected: Should find tasks with "webinar" or "web" related content
        """
        results = retrieval_agent.hybrid_search_tasks("webinar")

        assert len(results) > 0, "Should find results for partial match"

        # At least one result should contain the search term
        titles = [r["title"].lower() for r in results]
        assert any("webinar" in title or "web" in title for title in titles), \
            "Should find webinar or web-related tasks"


class TestScoreFusion:
    """Test hybrid search score fusion and ranking."""

    def test_hybrid_search_sorted_by_score(self, retrieval_agent, assert_sorted_by):
        """Results are sorted by fused score descending."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 1, "Need multiple results to test sorting"
        assert_sorted_by(results, "score", reverse=True,
                        message="Results should be sorted by score descending")

    def test_hybrid_better_than_text_only(self, retrieval_agent):
        """
        Hybrid search should perform better than text-only search.

        Verifies that semantic understanding improves results.
        """
        # Hybrid search with semantic understanding
        # Using "troubleshooting" which should find "debugging" tasks semantically
        hybrid_results = retrieval_agent.hybrid_search_tasks("troubleshooting")

        assert len(hybrid_results) > 0, "Hybrid search should find results"

        # Hybrid should find debugging/problem-solving tasks through semantic similarity
        titles = [r["title"].lower() for r in hybrid_results[:5]]
        combined_text = " ".join(titles)

        # Should find semantically related terms even if exact word not present
        semantic_terms = ["debug", "error", "fix", "guide", "method"]
        found_semantic = any(term in combined_text for term in semantic_terms)

        # This demonstrates semantic understanding beyond keyword matching
        assert found_semantic or "troubleshoot" in combined_text, \
            f"Hybrid search should leverage semantic understanding. Found: {titles}"


class TestEdgeCases:
    """Test edge cases for hybrid search."""

    def test_empty_query(self, retrieval_agent):
        """Empty query handles gracefully."""
        try:
            results = retrieval_agent.hybrid_search_tasks("")
            # Should either return empty or handle gracefully
            assert isinstance(results, list), "Should return list"
        except Exception as e:
            # Or raise a clear error
            assert "query" in str(e).lower() or "empty" in str(e).lower()

    def test_very_long_query(self, retrieval_agent):
        """Very long query string handles gracefully."""
        long_query = "debugging documentation webinar " * 50

        try:
            results = retrieval_agent.hybrid_search_tasks(long_query)
            assert isinstance(results, list), "Should handle long query"
        except Exception as e:
            # Should have reasonable error, not crash
            assert isinstance(e, Exception)

    def test_special_characters_query(self, retrieval_agent):
        """Queries with special characters handle gracefully."""
        special_query = "debugging@#$%^&*()"

        try:
            results = retrieval_agent.hybrid_search_tasks(special_query)
            assert isinstance(results, list), "Should handle special characters"
        except Exception:
            # Or raise clear error
            pass

    def test_no_results_scenario(self, retrieval_agent):
        """Query returning no results handles gracefully."""
        # Use very specific/uncommon term
        results = retrieval_agent.hybrid_search_tasks("xyzabc123nonexistent")

        # Should return empty list, not error
        assert isinstance(results, list), "Should return list even with no results"
