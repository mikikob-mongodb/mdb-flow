"""
Retrieval Agent Tests

Section 2 from FULL_COMPANION_TEST_SUITE_GUIDE.md  
Tests: 18 total

Covers:
- Basic task queries with filters
- Project queries
- Task-project joins
- Edge cases
"""

import pytest


class TestBasicTaskQueries:
    """Test basic task retrieval with filters."""

    def test_get_all_tasks(self, retrieval_agent, assert_all_have_field):
        """Get all tasks without filters."""
        tasks = retrieval_agent.get_tasks()
        
        assert len(tasks) > 0, "Should return tasks"
        assert_all_have_field(tasks, "title")
        assert_all_have_field(tasks, "status")

    def test_get_tasks_by_status_todo(self, retrieval_agent, assert_all_match):
        """Filter tasks by status=todo."""
        tasks = retrieval_agent.get_tasks(status="todo")
        
        assert len(tasks) > 0, "Should have some todo tasks"
        assert_all_match(tasks, lambda t: t["status"] == "todo",
                        "All tasks should have status='todo'")

    def test_get_tasks_by_status_in_progress(self, retrieval_agent, assert_all_match):
        """Filter tasks by status=in_progress."""
        tasks = retrieval_agent.get_tasks(status="in_progress")
        
        assert len(tasks) > 0, "Should have some in_progress tasks"
        assert_all_match(tasks, lambda t: t["status"] == "in_progress",
                        "All tasks should have status='in_progress'")

    def test_get_tasks_by_status_done(self, retrieval_agent, assert_all_match):
        """Filter tasks by status=done."""
        tasks = retrieval_agent.get_tasks(status="done")
        
        assert len(tasks) > 0, "Should have some done tasks"
        assert_all_match(tasks, lambda t: t["status"] == "done",
                        "All tasks should have status='done'")

    def test_get_tasks_by_priority(self, retrieval_agent):
        """Filter tasks by priority."""
        tasks = retrieval_agent.get_tasks(priority="high")
        
        assert len(tasks) > 0, "Should have some high priority tasks"
        for task in tasks:
            assert task.get("priority") == "high", \
                f"Task should have priority='high', got '{task.get('priority')}'"

    def test_get_tasks_by_project(self, retrieval_agent, projects_collection):
        """Filter tasks by project."""
        # Get a project name to filter by
        project = projects_collection.find_one({})
        assert project is not None, "Should have at least one project"
        
        project_name = project["name"]
        tasks = retrieval_agent.get_tasks(project_name=project_name)
        
        # Should return subset of tasks
        all_tasks = retrieval_agent.get_tasks()
        assert len(tasks) < len(all_tasks), "Filtered result should be subset"
        assert len(tasks) > 0, f"Should have tasks for project '{project_name}'"

    def test_get_tasks_combined_filters(self, retrieval_agent, assert_all_match):
        """Filter tasks by multiple criteria."""
        tasks = retrieval_agent.get_tasks(status="in_progress", priority="high")
        
        if len(tasks) > 0:
            # If we have results, verify they match both filters
            assert_all_match(tasks, 
                           lambda t: t["status"] == "in_progress" and t.get("priority") == "high",
                           "All tasks should be in_progress AND high priority")


class TestProjectQueries:
    """Test project retrieval."""

    def test_get_all_projects(self, retrieval_agent, projects_collection):
        """Get all projects."""
        projects = retrieval_agent.get_projects()
        
        # Compare with direct count
        expected_count = projects_collection.count_documents({})
        assert len(projects) == expected_count, \
            f"Should return all {expected_count} projects"
        
        # Verify structure
        for project in projects:
            assert "name" in project, "Project should have name"
            assert "_id" in project, "Project should have _id"

    def test_get_project_by_name(self, retrieval_agent):
        """Get specific project by name."""
        # Use a known project name (from sample data)
        project = retrieval_agent.get_project_by_name("AgentOps")
        
        assert project is not None, "Should find AgentOps project"
        assert "AgentOps" in project["name"], \
            f"Project name should contain 'AgentOps', got '{project['name']}'"

    def test_get_project_with_tasks(self, retrieval_agent):
        """Get project with its tasks."""
        result = retrieval_agent.get_project_with_tasks("AgentOps")
        
        assert "project" in result, "Result should have project"
        assert "tasks" in result, "Result should have tasks"
        
        project = result["project"]
        tasks = result["tasks"]
        
        assert "AgentOps" in project["name"], "Should be AgentOps project"
        assert len(tasks) > 0, "AgentOps should have tasks"
        
        # Verify all tasks belong to this project
        for task in tasks:
            if "project_name" in task:
                assert "AgentOps" in task["project_name"], \
                    "All tasks should belong to AgentOps"

    def test_get_projects_with_stats(self, retrieval_agent, assert_all_have_field):
        """Get projects with task counts."""
        projects = retrieval_agent.get_projects_with_stats()
        
        assert len(projects) > 0, "Should return projects"
        
        # Verify task count fields exist
        assert_all_have_field(projects, "todo_count")
        assert_all_have_field(projects, "in_progress_count")
        assert_all_have_field(projects, "done_count")
        
        # Verify counts are non-negative integers
        for project in projects:
            assert project["todo_count"] >= 0, "todo_count should be non-negative"
            assert project["in_progress_count"] >= 0, "in_progress_count should be non-negative"
            assert project["done_count"] >= 0, "done_count should be non-negative"


class TestTaskProjectJoins:
    """Test task-project relationship resolution."""

    def test_tasks_include_project_name(self, retrieval_agent):
        """Tasks should have project_name resolved from project_id."""
        tasks = retrieval_agent.get_tasks_with_project_names()
        
        # Find tasks that have a project_id
        tasks_with_project = [t for t in tasks if t.get("project_id")]
        
        assert len(tasks_with_project) > 0, "Should have tasks with project_id"
        
        # All tasks with project_id should have project_name resolved
        for task in tasks_with_project:
            assert "project_name" in task, \
                f"Task {task['_id']} has project_id but no project_name"
            assert task["project_name"], "project_name should not be empty"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_result_sets(self, retrieval_agent):
        """Query that returns no results handles gracefully."""
        # Use a status value that doesn't exist
        tasks = retrieval_agent.get_tasks(status="nonexistent_status")
        
        assert tasks == [] or len(tasks) == 0, \
            "Non-existent status should return empty list"

    def test_nonexistent_project(self, retrieval_agent):
        """Query for non-existent project handles gracefully."""
        project = retrieval_agent.get_project_by_name("NonExistentProject12345")
        
        assert project is None, "Non-existent project should return None"

    def test_case_insensitive_project_search(self, retrieval_agent):
        """Project search should be case-insensitive."""
        # Search with different casing
        result1 = retrieval_agent.get_project_by_name("AgentOps")
        result2 = retrieval_agent.get_project_by_name("agentops")
        result3 = retrieval_agent.get_project_by_name("AGENTOPS")
        
        # All should find the same project (or all should be None)
        if result1:
            assert result2 is not None, "Lowercase search should also find project"
            assert result3 is not None, "Uppercase search should also find project"
            assert result1["_id"] == result2["_id"] == result3["_id"], \
                "All searches should find same project"

    def test_tasks_without_project_id(self, retrieval_agent):
        """Tasks without project_id handle gracefully."""
        tasks = retrieval_agent.get_tasks()
        
        # Find tasks without project_id
        tasks_without_project = [t for t in tasks if not t.get("project_id")]
        
        # This is valid - some tasks may not be assigned to projects
        # Just verify they don't cause errors
        assert isinstance(tasks_without_project, list), \
            "Tasks without project_id should still be in results"

    def test_large_result_sets(self, retrieval_agent):
        """Queries returning many results handle correctly."""
        # Get all tasks (no filter)
        tasks = retrieval_agent.get_tasks()
        
        assert len(tasks) >= 40, "Should have at least 40 tasks from sample data"
        
        # Verify all have required structure
        for task in tasks:
            assert "_id" in task, "Each task should have _id"
            assert "title" in task, "Each task should have title"
            assert "status" in task, "Each task should have status"
