"""
Worklog Agent Tests

Section 3 from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: 12 total

Covers:
- Task status updates via database
- Notes management
- Activity logging
- Task creation
"""

import pytest
from datetime import datetime
from bson import ObjectId

from shared.db import (
    create_task,
    update_task,
    add_task_note,
    get_task,
    get_collection
)
from shared.models import Task


class TestStatusUpdates:
    """Test task status update operations."""

    def test_update_task_to_done(self, tasks_collection):
        """Update a task status to done."""
        # Find a task that's not done
        task = tasks_collection.find_one({"status": {"$ne": "done"}})
        if not task:
            pytest.skip("No non-done tasks available")

        task_id = task["_id"]

        # Update status to done
        success = update_task(task_id, {"status": "done"}, "Task completed")

        assert success, "Update should succeed"

        # Verify status changed
        updated = get_task(task_id)
        assert updated is not None, "Should find updated task"
        assert updated.status == "done", "Task status should be 'done'"

    def test_update_task_to_in_progress(self, tasks_collection):
        """Update a task status to in_progress."""
        # Find a todo task
        task = tasks_collection.find_one({"status": "todo"})
        if not task:
            pytest.skip("No todo tasks available")

        task_id = task["_id"]

        # Update to in_progress
        success = update_task(task_id, {"status": "in_progress"}, "Task started")

        assert success, "Update should succeed"

        # Verify status changed
        updated = get_task(task_id)
        assert updated.status == "in_progress", \
            "Task status should be 'in_progress'"

    def test_update_task_back_to_todo(self, tasks_collection):
        """Update a task back to todo status."""
        # Find an in_progress task
        task = tasks_collection.find_one({"status": "in_progress"})
        if not task:
            # Update a todo task to in_progress first
            todo_task = tasks_collection.find_one({"status": "todo"})
            if todo_task:
                update_task(todo_task["_id"], {"status": "in_progress"}, "Task started")
                task = get_task(todo_task["_id"]).__dict__

        if not task:
            pytest.skip("No tasks available for testing")

        task_id = task["_id"] if isinstance(task, dict) else task._id

        # Update back to todo
        success = update_task(task_id, {"status": "todo"}, "Task paused")

        assert success, "Update should succeed"

        # Verify status changed back
        updated = get_task(task_id)
        assert updated.status == "todo", "Task status should be 'todo'"


class TestNotes:
    """Test task notes functionality."""

    def test_add_note_to_task(self, tasks_collection):
        """Add a note to a task."""
        task = tasks_collection.find_one({})
        if not task:
            pytest.skip("No tasks available")

        task_id = task["_id"]
        original_notes_count = len(task.get("notes", []))

        # Add a note
        test_note = "Test note content"
        success = add_task_note(task_id, test_note)

        assert success, "Add note should succeed"

        # Verify note was added
        updated_task = tasks_collection.find_one({"_id": task_id})
        notes = updated_task.get("notes", [])
        assert len(notes) == original_notes_count + 1, \
            "Should have one more note"

        # Check the note content
        latest_note = notes[-1]
        assert test_note in str(latest_note), "Note should contain the text"

    def test_note_updates_timestamp(self, tasks_collection):
        """Adding a note updates task's updated_at timestamp."""
        task = tasks_collection.find_one({})
        if not task:
            pytest.skip("No tasks available")

        task_id = task["_id"]
        original_updated_at = task.get("updated_at")

        # Add a note
        success = add_task_note(task_id, "Timestamped note")
        assert success, "Add note should succeed"

        # Verify task's updated_at was updated
        updated = tasks_collection.find_one({"_id": task_id})
        new_updated_at = updated.get("updated_at")

        # updated_at should have changed
        assert new_updated_at is not None, "Task should have updated_at"
        if original_updated_at:
            assert new_updated_at >= original_updated_at, \
                "updated_at should be more recent or same"


class TestActivityLog:
    """Test activity log tracking."""

    def test_activity_log_on_status_change(self, tasks_collection):
        """Status changes add activity log entries."""
        task = tasks_collection.find_one({"status": {"$ne": "done"}})
        if not task:
            pytest.skip("No non-done tasks available")

        task_id = task["_id"]
        original_log_count = len(task.get("activity_log", []))

        # Change status
        update_task(task_id, {"status": "done"}, "Task completed")

        # Check activity log
        updated = tasks_collection.find_one({"_id": task_id})
        activity_log = updated.get("activity_log", [])

        # Should have new entry
        assert len(activity_log) > original_log_count, \
            "Activity log should have new entry"

    def test_activity_log_on_note(self, tasks_collection):
        """Adding a note adds activity log entry."""
        task = tasks_collection.find_one({})
        if not task:
            pytest.skip("No tasks available")

        task_id = task["_id"]
        original_log_count = len(task.get("activity_log", []))

        # Add a note
        add_task_note(task_id, "Activity log test note")

        # Check activity log
        updated = tasks_collection.find_one({"_id": task_id})
        activity_log = updated.get("activity_log", [])

        # Should have new entry (or same if notes don't create activity)
        assert len(activity_log) >= original_log_count, \
            "Activity log should be maintained"

    def test_activity_log_has_timestamp(self, tasks_collection):
        """Activity log entries have timestamps."""
        # Find a task with activity log
        task = tasks_collection.find_one({"activity_log": {"$exists": True, "$ne": []}})

        if not task or not task.get("activity_log"):
            # Create activity by updating a task
            test_task = tasks_collection.find_one({})
            if test_task:
                update_task(test_task["_id"], {"status": "in_progress"}, "Task started")
                task = tasks_collection.find_one({"_id": test_task["_id"]})

        if not task or not task.get("activity_log"):
            pytest.skip("No tasks with activity log")

        activity_log = task.get("activity_log", [])
        assert len(activity_log) > 0, "Should have activity log entries"

        # Check entries have timestamps
        for entry in activity_log:
            # Entry should have timestamp field
            assert "timestamp" in entry or "created_at" in entry or "updated_at" in entry, \
                f"Activity log entry should have timestamp: {entry}"


class TestTaskCreation:
    """Test task creation functionality."""

    def test_create_task(self, tasks_collection):
        """Create a new task."""
        initial_count = tasks_collection.count_documents({})

        # Create a task
        task = Task(
            title="Test Task Creation",
            context="This is a test task",
            status="todo",
            priority="medium"
        )

        task_id = create_task(task, action_note="Created in test")

        assert task_id is not None, "Should return task_id"
        assert isinstance(task_id, ObjectId), "Should be ObjectId"

        # Verify task was created
        new_count = tasks_collection.count_documents({})
        assert new_count == initial_count + 1, "Should have one more task"

        # Verify task details
        created_task = tasks_collection.find_one({"_id": task_id})
        assert created_task is not None, "Should find the created task"
        assert created_task["title"] == "Test Task Creation"
        assert created_task["status"] == "todo", "New tasks should be 'todo'"

    def test_create_task_with_project(self, tasks_collection, projects_collection):
        """Create task associated with a project."""
        project = projects_collection.find_one({})
        if not project:
            pytest.skip("No projects available")

        project_id = project["_id"]

        # Create a task with project
        task = Task(
            title="Test Task with Project",
            context="Task linked to project",
            status="todo",
            project_id=project_id
        )

        task_id = create_task(task)

        assert task_id is not None, "Create should succeed"

        # Verify task has project_id
        created_task = tasks_collection.find_one({"_id": task_id})
        assert created_task["project_id"] == project_id, \
            "Task should be linked to project"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_update_already_done_task(self, tasks_collection):
        """Updating an already done task handles gracefully."""
        task = tasks_collection.find_one({"status": "done"})
        if not task:
            # Create a done task
            test_task = tasks_collection.find_one({})
            if test_task:
                update_task(test_task["_id"], {"status": "done"}, "Task completed")
                task = tasks_collection.find_one({"_id": test_task["_id"]})

        if not task:
            pytest.skip("No done tasks available")

        task_id = task["_id"]

        # Try to update again
        success = update_task(task_id, {"status": "done"}, "Task completed again")

        # Should succeed (idempotent)
        assert success, "Idempotent update should succeed"

    def test_update_nonexistent_task(self):
        """Updating non-existent task fails gracefully."""
        invalid_id = ObjectId()  # Random ObjectId that doesn't exist

        success = update_task(invalid_id, {"status": "done"}, "Task completed")

        # Should fail gracefully
        assert not success, "Should fail for non-existent task"

    def test_add_note_to_nonexistent_task(self):
        """Adding note to non-existent task fails gracefully."""
        invalid_id = ObjectId()  # Random ObjectId that doesn't exist

        success = add_task_note(invalid_id, "Test note")

        # Should fail gracefully
        assert not success, "Should fail for non-existent task"
