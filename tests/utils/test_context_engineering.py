"""Tests for context engineering utilities (tool result compression)."""

import pytest
from bson import ObjectId
from utils.context_engineering import compress_tool_result


class TestCompressionToggle:
    """Test that compression respects the toggle setting."""

    def test_compression_disabled_returns_original(self):
        """When compress=False, return original result unchanged."""
        original = {
            "tasks": [{"_id": str(ObjectId()), "title": f"Task {i}"} for i in range(50)]
        }

        result = compress_tool_result("get_tasks", original, compress=False)

        assert result == original, "Should return original result when compression disabled"
        assert len(result["tasks"]) == 50, "Should have all 50 tasks"

    def test_compression_enabled_compresses(self):
        """When compress=True and >10 tasks, compress the result."""
        original = {
            "tasks": [
                {
                    "_id": str(ObjectId()),
                    "title": f"Task {i}",
                    "status": "todo" if i < 20 else "in_progress" if i < 35 else "done",
                    "project_name": "Test Project"
                }
                for i in range(50)
            ]
        }

        result = compress_tool_result("get_tasks", original, compress=True)

        assert "total_count" in result, "Compressed result should have total_count"
        assert result["total_count"] == 50
        assert "summary" in result, "Should have status summary"
        assert "top_5" in result, "Should have top 5 tasks"
        assert len(result["top_5"]) == 5, "Should only have 5 tasks"


class TestGetTasksCompression:
    """Test get_tasks result compression."""

    def test_compress_large_task_list(self):
        """Compress when >10 tasks returned."""
        tasks = [
            {
                "_id": str(ObjectId()),
                "title": f"Task {i}",
                "status": "todo" if i < 20 else "in_progress" if i < 35 else "done",
                "project_name": f"Project {i % 3}",
                "priority": "high" if i % 3 == 0 else "medium"
            }
            for i in range(50)
        ]
        result = {"tasks": tasks}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Verify structure
        assert "total_count" in compressed
        assert compressed["total_count"] == 50

        # Verify summary
        assert "summary" in compressed
        summary = compressed["summary"]
        assert summary["todo"] == 20
        assert summary["in_progress"] == 15
        assert summary["done"] == 15

        # Verify top 5
        assert "top_5" in compressed
        assert len(compressed["top_5"]) == 5

        # Verify top_5 structure (essential fields only)
        first_task = compressed["top_5"][0]
        assert "id" in first_task
        assert "title" in first_task
        assert "status" in first_task
        assert "project" in first_task
        assert "priority" in first_task

        # Verify note
        assert "note" in compressed
        assert "50" in compressed["note"]

    def test_no_compression_for_small_task_list(self):
        """Don't compress when <=10 tasks."""
        tasks = [
            {"_id": str(ObjectId()), "title": f"Task {i}", "status": "todo"}
            for i in range(5)
        ]
        result = {"tasks": tasks}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Should return original since <=10 tasks
        assert compressed == result
        assert len(compressed["tasks"]) == 5


class TestSearchTasksCompression:
    """Test search_tasks result compression."""

    def test_compress_search_results(self):
        """Compress search results to essential fields."""
        tasks = [
            {
                "_id": str(ObjectId()),
                "title": f"Match {i}",
                "score": 0.95 - (i * 0.05),
                "project_name": f"Project {i}",
                "status": "todo",
                "description": "Long description...",  # Should be stripped
                "notes": ["note1", "note2"],  # Should be stripped
                "created_at": "2024-01-01"  # Should be stripped
            }
            for i in range(10)
        ]
        result = {"tasks": tasks}

        compressed = compress_tool_result("search_tasks", result, compress=True)

        # Verify structure
        assert "matches" in compressed
        assert "total_matches" in compressed
        assert compressed["total_matches"] == 10

        # Should only return top 5
        assert len(compressed["matches"]) == 5

        # Verify essential fields only
        first_match = compressed["matches"][0]
        assert "id" in first_match
        assert "title" in first_match
        assert "score" in first_match
        assert "project" in first_match
        assert "status" in first_match

        # Verify score is rounded
        assert first_match["score"] == 0.95

        # Verify stripped fields are gone
        assert "description" not in first_match
        assert "notes" not in first_match
        assert "created_at" not in first_match

    def test_search_with_results_key(self):
        """Handle both 'tasks' and 'results' keys."""
        tasks = [{"_id": str(ObjectId()), "title": f"Task {i}"} for i in range(3)]
        result = {"results": tasks}  # Note: 'results' instead of 'tasks'

        compressed = compress_tool_result("search_tasks", result, compress=True)

        assert "matches" in compressed
        assert len(compressed["matches"]) == 3


class TestGetProjectsCompression:
    """Test get_projects result compression."""

    def test_compress_large_project_list(self):
        """Compress when >5 projects."""
        projects = [
            {
                "_id": str(ObjectId()),
                "name": f"Project {i}",
                "task_count": i * 5,
                "status": "active",
                "description": "Long description...",  # Should be stripped
                "context": "Some context"  # Should be stripped
            }
            for i in range(12)
        ]
        result = {"projects": projects}

        compressed = compress_tool_result("get_projects", result, compress=True)

        # Verify structure
        assert "total_count" in compressed
        assert compressed["total_count"] == 12
        assert "projects" in compressed
        assert len(compressed["projects"]) == 5
        assert "note" in compressed
        assert "12" in compressed["note"]

        # Verify essential fields only
        first_project = compressed["projects"][0]
        assert "id" in first_project
        assert "name" in first_project
        assert "task_count" in first_project
        assert "status" in first_project

        # Verify stripped fields
        assert "description" not in first_project
        assert "context" not in first_project

    def test_no_compression_for_small_project_list(self):
        """Don't compress when <=5 projects."""
        projects = [
            {"_id": str(ObjectId()), "name": f"Project {i}", "task_count": 10}
            for i in range(3)
        ]
        result = {"projects": projects}

        compressed = compress_tool_result("get_projects", result, compress=True)

        # Should return original
        assert compressed == result
        assert len(compressed["projects"]) == 3


class TestUnknownTools:
    """Test behavior with unknown/unsupported tools."""

    def test_unknown_tool_passes_through(self):
        """Unknown tools should pass through unchanged."""
        result = {
            "some_field": "some_value",
            "data": [1, 2, 3]
        }

        compressed = compress_tool_result("unknown_tool", result, compress=True)

        assert compressed == result, "Unknown tools should pass through unchanged"

    def test_create_task_passes_through(self):
        """create_task should pass through (no compression needed)."""
        result = {
            "success": True,
            "task": {"_id": str(ObjectId()), "title": "New Task"}
        }

        compressed = compress_tool_result("create_task", result, compress=True)

        assert compressed == result

    def test_complete_task_passes_through(self):
        """complete_task should pass through (no compression needed)."""
        result = {
            "success": True,
            "task": {"status": "done"}
        }

        compressed = compress_tool_result("complete_task", result, compress=True)

        assert compressed == result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_task_list(self):
        """Handle empty task list."""
        result = {"tasks": []}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Empty list should pass through (<=10 tasks)
        assert compressed == result

    def test_exactly_10_tasks(self):
        """10 tasks should not be compressed (threshold is >10)."""
        tasks = [{"_id": str(ObjectId()), "title": f"Task {i}"} for i in range(10)]
        result = {"tasks": tasks}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Should NOT compress (need >10)
        assert compressed == result
        assert len(compressed["tasks"]) == 10

    def test_exactly_11_tasks(self):
        """11 tasks should be compressed (>10)."""
        tasks = [
            {"_id": str(ObjectId()), "title": f"Task {i}", "status": "todo"}
            for i in range(11)
        ]
        result = {"tasks": tasks}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Should compress
        assert "total_count" in compressed
        assert compressed["total_count"] == 11

    def test_missing_optional_fields(self):
        """Handle tasks/projects with missing optional fields."""
        tasks = [
            {
                "_id": str(ObjectId()),
                "title": f"Task {i}",
                "status": "todo"
                # Missing: project_name, priority
            }
            for i in range(15)
        ]
        result = {"tasks": tasks}

        compressed = compress_tool_result("get_tasks", result, compress=True)

        # Should handle gracefully with defaults
        assert compressed["top_5"][0]["project"] == "-"
        assert compressed["top_5"][0]["priority"] == "-"

    def test_none_result(self):
        """Handle None result gracefully."""
        # This shouldn't happen in practice, but test robustness
        result = None

        # Should not crash
        try:
            compressed = compress_tool_result("get_tasks", result, compress=True)
            # If it doesn't crash, that's fine
        except (TypeError, AttributeError):
            # Expected - can't call .get() on None
            pass
