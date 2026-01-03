"""
Worklog Agent Tests

Section 3 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 12 total

Covers:
- Status updates (complete, start, stop)
- Notes management
- Activity logging
- Task creation
"""

import pytest
from datetime import datetime
from bson import ObjectId


class TestStatusUpdates:
    """Test task status update operations."""

    def test_complete_task(self, worklog_agent, tasks_collection):
        """Mark a task as complete."""
        # Find a task that's in progress
        task = tasks_collection.find_one({"status": "in_progress"})
        if not task:
            # If no in_progress task, create one for testing
            task = tasks_collection.find_one({"status": "todo"})
        
        assert task is not None, "Should have a task to test with"
        task_id = task["_id"]
        
        # Complete the task
        result = worklog_agent.complete_task(task_id)
        
        assert result["success"], f"Complete should succeed: {result.get('error')}"
        
        # Verify status changed
        updated = tasks_collection.find_one({"_id": task_id})
        assert updated["status"] == "done", "Task status should be 'done'"

    def test_start_task(self, worklog_agent, tasks_collection):
        """Mark a task as in_progress."""
        # Find a todo task
        task = tasks_collection.find_one({"status": "todo"})
        assert task is not None, "Should have a todo task"
        task_id = task["_id"]
        
        # Start the task
        result = worklog_agent.start_task(task_id)
        
        assert result["success"], f"Start should succeed: {result.get('error')}"
        
        # Verify status changed
        updated = tasks_collection.find_one({"_id": task_id})
        assert updated["status"] == "in_progress", \
            "Task status should be 'in_progress'"

    def test_stop_task(self, worklog_agent, tasks_collection):
        """Mark a task back to todo."""
        # Find an in_progress task
        task = tasks_collection.find_one({"status": "in_progress"})
        if not task:
            # Start a todo task first
            todo_task = tasks_collection.find_one({"status": "todo"})
            worklog_agent.start_task(todo_task["_id"])
            task = tasks_collection.find_one({"_id": todo_task["_id"]})
        
        assert task is not None, "Should have an in_progress task"
        task_id = task["_id"]
        
        # Stop the task
        result = worklog_agent.stop_task(task_id)
        
        assert result["success"], f"Stop should succeed: {result.get('error')}"
        
        # Verify status changed back
        updated = tasks_collection.find_one({"_id": task_id})
        assert updated["status"] == "todo", "Task status should be 'todo'"


class TestNotes:
    """Test task notes functionality."""

    def test_add_note(self, worklog_agent, tasks_collection):
        """Add a note to a task."""
        task = tasks_collection.find_one({})
        assert task is not None, "Should have a task"
        task_id = task["_id"]
        
        original_notes_count = len(task.get("notes", []))
        
        # Add a note
        test_note = "Test note content"
        result = worklog_agent.add_note(task_id, test_note)
        
        assert result["success"], f"Add note should succeed: {result.get('error')}"
        
        # Verify note was added
        updated = tasks_collection.find_one({"_id": task_id})
        notes = updated.get("notes", [])
        assert len(notes) == original_notes_count + 1, \
            "Should have one more note"
        
        # Check the note content
        latest_note = notes[-1]
        assert test_note in str(latest_note), "Note should contain the text"

    def test_note_has_timestamp(self, worklog_agent, tasks_collection):
        """Notes should have timestamps."""
        task = tasks_collection.find_one({})
        task_id = task["_id"]
        
        before_time = datetime.utcnow()
        
        # Add a note
        result = worklog_agent.add_note(task_id, "Timestamped note")
        assert result["success"]
        
        after_time = datetime.utcnow()
        
        # Verify timestamp
        updated = tasks_collection.find_one({"_id": task_id})
        latest_note = updated["notes"][-1]
        
        # Note should have timestamp or created_at field
        timestamp_field = latest_note.get("timestamp") or latest_note.get("created_at")
        assert timestamp_field is not None, "Note should have timestamp"
        
        # Timestamp should be recent (within the test execution time)
        if isinstance(timestamp_field, datetime):
            assert before_time <= timestamp_field <= after_time, \
                "Timestamp should be within test execution time"


class TestActivityLog:
    """Test activity log tracking."""

    def test_activity_log_on_complete(self, worklog_agent, tasks_collection):
        """Completing a task adds activity log entry."""
        task = tasks_collection.find_one({"status": {"$in": ["todo", "in_progress"]}})
        assert task is not None
        task_id = task["_id"]
        
        # Complete the task
        worklog_agent.complete_task(task_id)
        
        # Check activity log
        updated = tasks_collection.find_one({"_id": task_id})
        activity_log = updated.get("activity_log", [])
        
        assert len(activity_log) > 0, "Should have activity log entries"
        
        # Check for completion action
        completion_entries = [
            entry for entry in activity_log 
            if entry.get("action") in ["completed", "complete", "done"]
        ]
        assert len(completion_entries) > 0, \
            "Should have a completion entry in activity log"

    def test_activity_log_on_start(self, worklog_agent, tasks_collection):
        """Starting a task adds activity log entry."""
        task = tasks_collection.find_one({"status": "todo"})
        if not task:
            pytest.skip("No todo tasks available")
        
        task_id = task["_id"]
        original_log_count = len(task.get("activity_log", []))
        
        # Start the task
        worklog_agent.start_task(task_id)
        
        # Check activity log
        updated = tasks_collection.find_one({"_id": task_id})
        activity_log = updated.get("activity_log", [])
        
        assert len(activity_log) > original_log_count, \
            "Activity log should have new entry"
        
        # Check for start action
        start_entries = [
            entry for entry in activity_log 
            if entry.get("action") in ["started", "start", "in_progress"]
        ]
        assert len(start_entries) > 0, "Should have a start entry"

    def test_activity_log_on_note(self, worklog_agent, tasks_collection):
        """Adding a note adds activity log entry."""
        task = tasks_collection.find_one({})
        task_id = task["_id"]
        original_log_count = len(task.get("activity_log", []))
        
        # Add a note
        worklog_agent.add_note(task_id, "Activity log test note")
        
        # Check activity log
        updated = tasks_collection.find_one({"_id": task_id})
        activity_log = updated.get("activity_log", [])
        
        assert len(activity_log) > original_log_count, \
            "Activity log should have new entry for note"
        
        # Check for note action
        note_entries = [
            entry for entry in activity_log 
            if entry.get("action") in ["note_added", "note", "added_note"]
        ]
        assert len(note_entries) > 0, "Should have a note_added entry"

    def test_activity_log_has_timestamp(self, worklog_agent, tasks_collection):
        """Activity log entries have timestamps."""
        task = tasks_collection.find_one({"activity_log": {"$exists": True, "$ne": []}})
        
        if not task or not task.get("activity_log"):
            # Create activity by completing a task
            test_task = tasks_collection.find_one({"status": {"$ne": "done"}})
            if test_task:
                worklog_agent.complete_task(test_task["_id"])
                task = tasks_collection.find_one({"_id": test_task["_id"]})
        
        assert task is not None, "Should have task with activity log"
        activity_log = task.get("activity_log", [])
        assert len(activity_log) > 0, "Should have activity log entries"
        
        # Check all entries have timestamps
        for entry in activity_log:
            assert "timestamp" in entry, \
                f"Activity log entry should have timestamp: {entry}"
            assert isinstance(entry["timestamp"], datetime), \
                "Timestamp should be datetime object"


class TestTaskCreation:
    """Test task creation functionality."""

    def test_create_task(self, worklog_agent, tasks_collection):
        """Create a new task."""
        initial_count = tasks_collection.count_documents({})
        
        # Create a task
        result = worklog_agent.create_task(
            title="Test Task Creation",
            context="This is a test task",
            priority="medium"
        )
        
        assert result["success"], f"Create should succeed: {result.get('error')}"
        assert "task_id" in result, "Should return task_id"
        
        # Verify task was created
        new_count = tasks_collection.count_documents({})
        assert new_count == initial_count + 1, "Should have one more task"
        
        # Verify task details
        task = tasks_collection.find_one({"_id": result["task_id"]})
        assert task is not None, "Should find the created task"
        assert task["title"] == "Test Task Creation"
        assert task["status"] == "todo", "New tasks should default to 'todo'"

    def test_create_task_with_project(self, worklog_agent, tasks_collection, 
                                      projects_collection):
        """Create task associated with a project."""
        project = projects_collection.find_one({})
        assert project is not None, "Should have a project"
        project_id = project["_id"]
        
        # Create a task with project
        result = worklog_agent.create_task(
            title="Test Task with Project",
            context="Task linked to project",
            project_id=project_id
        )
        
        assert result["success"]
        
        # Verify task has project_id
        task = tasks_collection.find_one({"_id": result["task_id"]})
        assert task["project_id"] == project_id, \
            "Task should be linked to project"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_complete_already_done_task(self, worklog_agent, tasks_collection):
        """Completing an already done task should handle gracefully."""
        task = tasks_collection.find_one({"status": "done"})
        if not task:
            # Create a done task
            test_task = tasks_collection.find_one({})
            worklog_agent.complete_task(test_task["_id"])
            task = tasks_collection.find_one({"_id": test_task["_id"]})
        
        task_id = task["_id"]
        
        # Try to complete again
        result = worklog_agent.complete_task(task_id)
        
        # Should either succeed (idempotent) or return graceful message
        # Should NOT raise an error
        assert "success" in result or "error" in result

    def test_start_already_in_progress_task(self, worklog_agent, tasks_collection):
        """Starting an already in_progress task should handle gracefully."""
        task = tasks_collection.find_one({"status": "in_progress"})
        if not task:
            todo_task = tasks_collection.find_one({"status": "todo"})
            worklog_agent.start_task(todo_task["_id"])
            task = tasks_collection.find_one({"_id": todo_task["_id"]})
        
        task_id = task["_id"]
        
        # Try to start again
        result = worklog_agent.start_task(task_id)
        
        # Should handle gracefully
        assert "success" in result or "error" in result

    def test_invalid_task_id(self, worklog_agent):
        """Operations with invalid task_id should fail gracefully."""
        invalid_id = ObjectId()  # Random ObjectId that doesn't exist
        
        result = worklog_agent.complete_task(invalid_id)
        
        # Should return error, not raise exception
        assert not result.get("success", False), \
            "Should fail for non-existent task"
        assert "error" in result, "Should have error message"
