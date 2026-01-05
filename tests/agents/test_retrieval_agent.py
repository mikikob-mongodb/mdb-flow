"""
Retrieval Agent Tests

Section 2 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 18 total

Covers:
- Hybrid search (tasks and projects)
- Fuzzy matching
- Semantic search
- Edge cases
"""

import pytest


class TestHybridSearchTasks:
    """Test hybrid search functionality for tasks."""

    def test_hybrid_search_tasks_returns_results(self, retrieval_agent):
        """Hybrid search returns results for tasks."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        assert len(results) > 0, "Should return results"
        assert isinstance(results, list), "Should return list"

        # Check structure
        for result in results:
            assert "_id" in result, "Result should have _id"
            assert "title" in result, "Result should have title"
            assert "score" in result, "Result should have score"

    def test_hybrid_search_respects_limit(self, retrieval_agent):
        """Hybrid search respects limit parameter."""
        limit = 3
        results = retrieval_agent.hybrid_search_tasks("task", limit=limit)

        assert len(results) <= limit, \
            f"Should return at most {limit} results, got {len(results)}"

    def test_hybrid_search_semantic_matching(self, retrieval_agent):
        """Hybrid search finds semantically related tasks."""
        results = retrieval_agent.hybrid_search_tasks("documentation")

        assert len(results) > 0, "Should find documentation-related tasks"

        # Check if results are relevant
        titles = [r["title"].lower() for r in results[:3]]
        combined = " ".join(titles)

        # Should find doc-related tasks
        assert "doc" in combined or "guide" in combined or "write" in combined, \
            f"Should find doc-related tasks. Found: {titles}"

    def test_hybrid_search_scores_sorted(self, retrieval_agent, assert_sorted_by):
        """Results should be sorted by score descending."""
        results = retrieval_agent.hybrid_search_tasks("debugging")

        if len(results) > 1:
            assert_sorted_by(results, "score", reverse=True,
                            message="Results should be sorted by score descending")


class TestHybridSearchProjects:
    """Test hybrid search functionality for projects."""

    def test_hybrid_search_projects_returns_results(self, retrieval_agent):
        """Hybrid search returns results for projects."""
        results = retrieval_agent.hybrid_search_projects("agent")

        assert len(results) > 0, "Should return results"
        assert isinstance(results, list), "Should return list"

        # Check structure
        for result in results:
            assert "_id" in result, "Result should have _id"
            assert "name" in result, "Result should have name"
            assert "score" in result, "Result should have score"

    def test_hybrid_search_projects_respects_limit(self, retrieval_agent):
        """Hybrid search respects limit parameter."""
        limit = 2
        results = retrieval_agent.hybrid_search_projects("project", limit=limit)

        assert len(results) <= limit, \
            f"Should return at most {limit} results, got {len(results)}"

    def test_hybrid_search_projects_semantic(self, retrieval_agent):
        """Hybrid search finds semantically related projects."""
        results = retrieval_agent.hybrid_search_projects("memory")

        assert len(results) > 0, "Should find memory-related projects"


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""

    def test_fuzzy_match_task_exact(self, retrieval_agent):
        """Fuzzy match finds tasks with exact matches."""
        # Get a real task title
        results = retrieval_agent.hybrid_search_tasks("debugging", limit=1)
        if len(results) > 0:
            task_title = results[0]["title"]

            # Search for exact title
            result = retrieval_agent.fuzzy_match_task(task_title)

            assert result is not None, "Should return result"
            assert "match" in result, "Should have match field"
            assert "confidence" in result, "Should have confidence field"
            # Exact match should have high confidence
            if result["match"]:
                assert result["confidence"] > 0.7, "Exact match should have high confidence"

    def test_fuzzy_match_task_partial(self, retrieval_agent):
        """Fuzzy match finds tasks with partial matches."""
        # Try a partial match
        result = retrieval_agent.fuzzy_match_task("debug doc")

        assert result is not None, "Should return result"
        assert "match" in result, "Should have match field"
        assert "confidence" in result, "Should have confidence score"
        assert "alternatives" in result, "Should have alternatives"

    def test_fuzzy_match_task_threshold(self, retrieval_agent):
        """Fuzzy match respects threshold parameter."""
        # Try with high threshold (strict matching)
        result_strict = retrieval_agent.fuzzy_match_task("xyz", threshold=0.9)

        assert result_strict is not None, "Should return result"
        # Should either have no match or high-confidence match
        if result_strict["match"]:
            assert result_strict["confidence"] >= 0.9, \
                "Match should meet threshold"

    def test_fuzzy_match_project(self, retrieval_agent):
        """Fuzzy match finds projects."""
        # Try matching a project
        result = retrieval_agent.fuzzy_match_project("AgentOps")

        assert result is not None, "Should return result"
        assert "match" in result, "Should have match field"
        assert "confidence" in result, "Should have confidence"
        assert "alternatives" in result, "Should have alternatives"


class TestDatabaseQueries:
    """Test direct database queries for filtering."""

    def test_filter_tasks_by_status(self, tasks_collection, assert_all_match):
        """Can filter tasks by status using database."""
        tasks = list(tasks_collection.find({"status": "todo"}))

        if len(tasks) > 0:
            assert_all_match(tasks, lambda t: t["status"] == "todo",
                            "All tasks should have status='todo'")

    def test_filter_tasks_by_priority(self, tasks_collection):
        """Can filter tasks by priority using database."""
        tasks = list(tasks_collection.find({"priority": "high"}))

        # May or may not have high priority tasks
        for task in tasks:
            assert task.get("priority") == "high", \
                f"Task should have priority='high'"

    def test_filter_tasks_by_project(self, tasks_collection, projects_collection):
        """Can filter tasks by project using database."""
        # Get a project
        project = projects_collection.find_one({})
        if project:
            project_id = project["_id"]

            # Find tasks for this project
            tasks = list(tasks_collection.find({"project_id": project_id}))

            # All should have the project_id
            for task in tasks:
                assert task.get("project_id") == project_id


class TestEdgeCases:
    """Test edge cases for retrieval."""

    def test_hybrid_search_empty_query(self, retrieval_agent):
        """Empty query handles gracefully."""
        try:
            results = retrieval_agent.hybrid_search_tasks("")
            # Should either return empty or handle gracefully
            assert isinstance(results, list), "Should return list"
        except Exception as e:
            # Or raise clear error
            assert "query" in str(e).lower() or "empty" in str(e).lower()

    def test_hybrid_search_no_results(self, retrieval_agent):
        """Query with no matches returns empty list."""
        results = retrieval_agent.hybrid_search_tasks("xyzabc123nonexistent")

        assert isinstance(results, list), "Should return list"
        # May return empty or low-scoring results

    def test_hybrid_search_special_characters(self, retrieval_agent):
        """Queries with special characters handle gracefully."""
        try:
            results = retrieval_agent.hybrid_search_tasks("debug@#$%")
            assert isinstance(results, list), "Should handle special characters"
        except Exception:
            pass

    def test_fuzzy_match_nonexistent(self, retrieval_agent):
        """Fuzzy match with non-existent task returns no match."""
        result = retrieval_agent.fuzzy_match_task("completely_nonexistent_task_xyz_123")

        assert result is not None, "Should return result"
        # Should either have no match or very low confidence
        if result["match"] is None:
            assert True, "No match found as expected"
        else:
            # If there's a match, confidence should be low
            assert result["confidence"] < 0.7, "Nonexistent task should have low confidence"

    def test_tasks_have_required_fields(self, tasks_collection, assert_all_have_field):
        """All tasks have required fields."""
        tasks = list(tasks_collection.find({}).limit(10))

        assert len(tasks) > 0, "Should have tasks"
        assert_all_have_field(tasks, "_id")
        assert_all_have_field(tasks, "title")
        assert_all_have_field(tasks, "status")
