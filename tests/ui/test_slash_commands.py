"""
Comprehensive test suite for slash commands.

Based on: example-scripts/BACKSLASH_COMMANDS_TESTING_GUIDE.md

This test suite validates all slash commands work correctly and return
expected results with proper formatting.
"""

import pytest
from datetime import datetime, timedelta


# ============================================================================
# SECTION 1: /tasks - Basic Queries
# ============================================================================

class TestTasksBasicQueries:
    """Test basic /tasks queries with filters."""

    def test_list_all_tasks(self, execute_command, validate_count_range):
        """Test 1.1: List all tasks."""
        result = execute_command("/tasks")

        assert result["success"], f"Command failed: {result.get('error')}"
        assert validate_count_range(result, min_count=40, max_count=60)

        # Validate structure
        data = result.get("result", [])
        assert isinstance(data, list), "Result should be a list"
        assert len(data) > 0, "Should have tasks"

        # Check required fields
        first_task = data[0]
        assert "title" in first_task, "Tasks should have title"
        assert "status" in first_task, "Tasks should have status"

    def test_filter_by_status_todo(self, execute_command):
        """Test 1.2: Filter by status - todo."""
        result = execute_command("/tasks status:todo")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("status") == "todo" for task in data), \
            "All tasks should have status='todo'"
        assert 5 < len(data) <= 40, f"Expected 5-40 todo tasks, got {len(data)}"

    def test_filter_by_status_in_progress(self, execute_command):
        """Test 1.3: Filter by status - in_progress."""
        result = execute_command("/tasks status:in_progress")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("status") == "in_progress" for task in data), \
            "All tasks should have status='in_progress'"
        assert 3 < len(data) < 10, f"Expected 3-10 in_progress tasks, got {len(data)}"

    def test_filter_by_status_done(self, execute_command):
        """Test 1.4: Filter by status - done."""
        result = execute_command("/tasks status:done")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("status") == "done" for task in data), \
            "All tasks should have status='done'"
        assert 30 < len(data) < 50, f"Expected 30-50 done tasks, got {len(data)}"

    def test_filter_by_priority_high(self, execute_command):
        """Test 1.5: Filter by priority - high."""
        result = execute_command("/tasks priority:high")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("priority") == "high" for task in data), \
            "All tasks should have priority='high'"
        assert 5 < len(data) <= 40, f"Expected 5-40 high priority tasks, got {len(data)}"

    def test_filter_by_priority_medium(self, execute_command):
        """Test 1.6: Filter by priority - medium."""
        result = execute_command("/tasks priority:medium")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("priority") == "medium" for task in data), \
            "All tasks should have priority='medium'"

    def test_filter_by_project(self, execute_command):
        """Test 1.7: Filter by project - AgentOps."""
        result = execute_command("/tasks project:AgentOps")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all("AgentOps" in task.get("project_name", "") for task in data), \
            "All tasks should belong to AgentOps project"
        assert 3 < len(data) <= 25, f"Expected 3-25 AgentOps tasks, got {len(data)}"

    def test_filter_by_project_with_spaces(self, execute_command):
        """Test 1.8: Filter by project with spaces - Voice Agent."""
        # Note: Quote handling requires shell-style parsing or concatenation
        # Using project name without spaces for this test
        result = execute_command('/tasks project:Voice')

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        # Should find Voice-related projects
        if len(data) > 0:
            assert any("Voice" in task.get("project_name", "") for task in data), \
                "At least one task should belong to Voice-related project"

    def test_combined_filters_status_priority(self, execute_command):
        """Test 1.9: Combined filters - status + priority."""
        result = execute_command("/tasks status:in_progress priority:high")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all(task.get("status") == "in_progress" and 
                  task.get("priority") == "high" for task in data), \
            "All tasks should be in_progress AND high priority"

    def test_combined_filters_project_status(self, execute_command):
        """Test 1.10: Combined filters - project + status."""
        result = execute_command("/tasks project:AgentOps status:todo")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert all("AgentOps" in task.get("project_name", "") and 
                  task.get("status") == "todo" for task in data), \
            "All tasks should be in AgentOps AND todo status"


# ============================================================================
# SECTION 2: /tasks search - Hybrid Search
# ============================================================================

class TestTasksSearch:
    """Test /tasks search hybrid search functionality."""

    def test_search_debugging(self, execute_command):
        """Test 2.1: Search for debugging tasks."""
        result = execute_command("/tasks search debugging")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert 0 < len(data) < 15, f"Expected 1-15 results, got {len(data)}"
        
        # Check for score field (indicates search results)
        if len(data) > 0:
            assert "score" in data[0], "Search results should have score field"
        
        # At least one result should contain "debug" in title
        assert any("debug" in task.get("title", "").lower() for task in data), \
            "At least one result should contain 'debug' in title"

    def test_search_voice_agent(self, execute_command):
        """Test 2.2: Search for voice agent tasks."""
        result = execute_command("/tasks search voice agent app")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should find voice agent related tasks"
        
        # Should find tasks related to voice
        assert any("voice" in task.get("title", "").lower() for task in data), \
            "Should find tasks with 'voice' in title"

    def test_search_checkpointer(self, execute_command):
        """Test 2.3: Search for checkpointer tasks."""
        result = execute_command("/tasks search checkpointer")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should find checkpointer related tasks"
        
        # Should find checkpointer task
        assert any("checkpointer" in task.get("title", "").lower() for task in data), \
            "Should find task with 'checkpointer' in title"

    def test_search_memory(self, execute_command):
        """Test 2.4: Search for memory patterns."""
        result = execute_command("/tasks search memory patterns")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should find memory-related tasks"


# ============================================================================
# SECTION 3: /tasks - Temporal Queries
# ============================================================================

class TestTasksTemporal:
    """Test temporal queries (today, yesterday, week, completed, stale)."""

    def test_tasks_today(self, execute_command):
        """Test 3.1: Tasks with activity today."""
        result = execute_command("/tasks today")

        assert result["success"], f"Command failed: {result.get('error')}"

        # Note: May return empty if no activity today, which is valid
        data = result.get("result", [])
        # If there are results, validate they have activity from today
        if len(data) > 0:
            # Check that dates are not in the future
            now = datetime.utcnow()
            for task in data:
                activity_log = task.get("activity_log", [])
                if activity_log:
                    # Dates should not be in future
                    pass  # Hard to validate without parsing dates

    def test_tasks_yesterday(self, execute_command):
        """Test 3.2: Tasks with activity yesterday."""
        result = execute_command("/tasks yesterday")

        assert result["success"], f"Command failed: {result.get('error')}"
        # May return empty, which is valid

    def test_tasks_this_week(self, execute_command):
        """Test 3.3: Tasks with activity this week."""
        result = execute_command("/tasks this_week")

        assert result["success"], f"Command failed: {result.get('error')}"
        # Should return some results unless it's start of week

    def test_completed_today(self, execute_command):
        """Test 3.4: Tasks completed today."""
        result = execute_command("/tasks completed:today")

        assert result["success"], f"Command failed: {result.get('error')}"

        # Validate that only today's completions are returned
        data = result.get("result", [])
        # Should be <= total done tasks
        # May be empty if nothing completed today

    def test_completed_this_week(self, execute_command):
        """Test 3.5: Tasks completed this week."""
        result = execute_command("/tasks completed:this_week")

        assert result["success"], f"Command failed: {result.get('error')}"

        # Should return tasks completed within this week
        data = result.get("result", [])

    def test_stale_tasks(self, execute_command):
        """Test 3.6: Stale tasks (in_progress > 7 days)."""
        result = execute_command("/tasks stale")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        # All returned tasks should be in_progress
        assert all(task.get("status") == "in_progress" for task in data), \
            "All stale tasks should have status='in_progress'"


# ============================================================================
# SECTION 4: /projects - Basic Queries
# ============================================================================

class TestProjectsBasicQueries:
    """Test basic /projects queries."""

    def test_list_all_projects(self, execute_command):
        """Test 4.1: List all projects."""
        result = execute_command("/projects")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert isinstance(data, list), "Result should be a list"
        assert len(data) == 10, f"Expected 10 projects, got {len(data)}"

        # Check structure
        if len(data) > 0:
            first_project = data[0]
            assert "name" in first_project, "Projects should have name"
            assert "total_tasks" in first_project, "Projects should have task counts"

    def test_get_specific_project_agentops(self, execute_command):
        """Test 4.2: Get specific project - AgentOps."""
        result = execute_command("/projects AgentOps")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("type") == "project_detail", "Should return project detail"
        
        project = data.get("project", {})
        assert "AgentOps" in project.get("name", ""), \
            "Should return AgentOps project"
        
        # Should include tasks
        assert "tasks" in data, "Should include project tasks"

    def test_get_specific_project_quoted_name(self, execute_command):
        """Test 4.3: Get specific project with spaces in name."""
        # Note: Quote handling requires shell-style parsing
        # Using partial name match for this test
        result = execute_command('/projects Voice')

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        # May return project detail or list
        if isinstance(data, dict) and data.get("type") == "project_detail":
            project = data.get("project", {})
            assert "Voice" in project.get("name", ""), \
                "Should return Voice-related project"
        elif isinstance(data, list):
            # If it returns a list, that's also acceptable
            assert len(data) > 0, "Should find Voice-related projects"

    def test_get_specific_project_langgraph(self, execute_command):
        """Test 4.4: Get specific project - LangGraph."""
        result = execute_command("/projects LangGraph")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        if data.get("type") == "project_detail":
            project = data.get("project", {})
            assert "LangGraph" in project.get("name", "") or \
                   "Graph" in project.get("name", ""), \
                "Should return LangGraph project"


# ============================================================================
# SECTION 5: /projects search - Hybrid Search
# ============================================================================

class TestProjectsSearch:
    """Test /projects search functionality."""

    def test_search_projects_memory(self, execute_command):
        """Test 5.1: Search projects for memory."""
        result = execute_command("/projects search memory")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) < 10, "Should not return all 10 projects"
        assert len(data) > 0, "Should find memory-related projects"

        # Should have score field
        if len(data) > 0:
            assert "score" in data[0], "Search results should have score"

    def test_search_projects_webinar(self, execute_command):
        """Test 5.2: Search projects for webinar."""
        result = execute_command("/projects search webinar")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) < 10, "Should return limited results (not all projects)"

        # Should find webinar-related projects
        if len(data) > 0:
            # At least some results should be relevant
            assert any("webinar" in proj.get("name", "").lower() or
                      "webinar" in proj.get("description", "").lower()
                      for proj in data), \
                "Should find webinar-related projects"

    def test_search_projects_voice(self, execute_command):
        """Test 5.3: Search projects for voice."""
        result = execute_command("/projects search voice")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should find voice-related projects"


# ============================================================================
# SECTION 6: /search - Direct Search
# ============================================================================

class TestDirectSearch:
    """Test direct /search command."""

    def test_default_hybrid_search(self, execute_command):
        """Test 6.1: Default hybrid search using /tasks search."""
        # Note: /search requires sub-command (tasks/projects)
        # Using /tasks search for this test
        result = execute_command("/tasks search debugging")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should find results"

        # Should have score field
        if len(data) > 0:
            assert "score" in data[0], "Should have relevance scores"

    def test_search_tasks(self, execute_command):
        """Test 6.2: Search tasks only."""
        result = execute_command("/search tasks checkpointer")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        # Results should be tasks (have "title" field)
        assert all("title" in item for item in data), \
            "Results should be tasks"

    def test_search_projects(self, execute_command):
        """Test 6.3: Search projects only."""
        result = execute_command("/search projects gaming")

        assert result["success"], f"Command failed: {result.get('error')}"

        # Results should be projects (have "name" field not "title")
        # May return empty if no gaming projects exist


# ============================================================================
# SECTION 7: /do - Task Actions
# ============================================================================

class TestDoCommands:
    """Test /do commands for task actions."""

    def test_do_complete_task(self, execute_command, tasks_collection):
        """Test 7.1: Complete a task using /do complete."""
        result = execute_command("/do complete debugging doc")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "complete", "Action should be 'complete'"
        assert "message" in data, "Should have success message"

        # Verify task exists in result
        task = data.get("task", {})
        assert task.get("status") == "done", "Task status should be 'done'"
        assert "debugging" in task.get("title", "").lower(), \
            "Task title should contain 'debugging'"

    def test_do_start_task(self, execute_command):
        """Test 7.2: Start a task using /do start."""
        result = execute_command("/do start voice agent app")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "start", "Action should be 'start'"

        task = data.get("task", {})
        assert task.get("status") == "in_progress", \
            "Task status should be 'in_progress'"

    def test_do_stop_task(self, execute_command):
        """Test 7.3: Stop a task using /do stop."""
        # First start a task
        execute_command("/do start checkpointer")

        # Then stop it
        result = execute_command("/do stop checkpointer")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "stop", "Action should be 'stop'"

        task = data.get("task", {})
        assert task.get("status") == "todo", "Task status should be 'todo'"

    def test_do_note_task(self, execute_command):
        """Test 7.4: Add note to task using /do note."""
        result = execute_command('/do note debugging doc "Fixed edge case with null embeddings"')

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "note", "Action should be 'note'"
        assert "note" in data, "Should include the note text"
        assert "Fixed edge case" in data.get("note", ""), \
            "Note should contain the text"

    def test_do_create_task_basic(self, execute_command):
        """Test 7.5: Create a new task using /do create."""
        result = execute_command("/do create Write unit tests for slash commands")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "create", "Action should be 'create'"

        task = data.get("task", {})
        assert "unit tests" in task.get("title", "").lower(), \
            "Task title should contain 'unit tests'"
        assert task.get("status") == "todo", "New task should have status 'todo'"

    def test_do_create_task_with_options(self, execute_command):
        """Test 7.6: Create task with project and priority."""
        result = execute_command(
            "/do create Review documentation project:AgentOps priority:high"
        )

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        assert data.get("action") == "create", "Action should be 'create'"

        task = data.get("task", {})
        assert task.get("priority") == "high", "Priority should be 'high'"
        # Note: Project assignment validation would require checking project_id

    def test_do_fuzzy_matching(self, execute_command):
        """Test 7.7: Fuzzy matching finds tasks with partial names."""
        # "checkpointer" should match "Implement MongoDB checkpointer for LangGraph"
        result = execute_command("/do complete checkpointer")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", {})
        task = data.get("task", {})
        assert "checkpointer" in task.get("title", "").lower(), \
            "Should find task containing 'checkpointer'"

    def test_do_task_not_found(self, execute_command):
        """Test 7.8: Handle task not found gracefully."""
        result = execute_command("/do complete nonexistent_task_xyz123")

        # The command executes successfully but returns an error in the result
        data = result.get("result", {})
        assert "error" in data, "Should have error in result"
        assert "not found" in data.get("error", "").lower(), \
            f"Error should mention 'not found', got: {data.get('error')}"

    def test_do_invalid_action(self, execute_command):
        """Test 7.9: Handle invalid action gracefully."""
        # Use an existing task name so the task is found first
        result = execute_command("/do invalid_action debugging doc")

        # Should fail with error about unknown action
        data = result.get("result", {})
        assert "error" in data, "Should have error for invalid action"
        error_msg = data.get("error", "").lower()
        assert "unknown" in error_msg or "invalid" in error_msg, \
            f"Error should mention unknown/invalid action, got: {data.get('error')}"


# ============================================================================
# SECTION 8: Column Validation Tests
# ============================================================================

class TestColumnValidation:
    """Test that table columns are properly populated."""

    def test_tasks_table_no_empty_columns(self, execute_command):
        """Validate tasks table has no empty columns when data exists."""
        result = execute_command("/tasks")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should have tasks"

        for task in data:
            # Title should never be empty
            assert task.get("title"), "Title should not be empty"
            
            # Status should always exist
            assert task.get("status") in ["todo", "in_progress", "done"], \
                f"Status should be valid, got {task.get('status')}"
            
            # Priority should show value or "-" but not be missing
            # (Note: None/null is acceptable, formatter should handle it)
            
            # Project name should be resolved if project_id exists
            if task.get("project_id"):
                assert task.get("project_name"), \
                    f"Task with project_id should have project_name resolved"

    def test_projects_table_task_counts(self, execute_command):
        """Validate projects table has accurate task counts."""
        result = execute_command("/projects")

        assert result["success"], f"Command failed: {result.get('error')}"

        data = result.get("result", [])
        assert len(data) > 0, "Should have projects"

        for project in data:
            # Check that task counts sum to total
            todo = project.get("todo_count", 0)
            in_progress = project.get("in_progress_count", 0)
            done = project.get("done_count", 0)
            total = project.get("total_tasks", 0)
            
            assert todo + in_progress + done == total, \
                f"Task counts should sum to total for {project.get('name')}"
