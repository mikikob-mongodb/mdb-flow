"""MongoDB database connection and utilities."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from shared.config import settings
from shared.models import Task, Project, Settings, ActivityLogEntry, ProjectUpdate


class MongoDB:
    """MongoDB connection manager."""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> Database:
        """
        Establish connection to MongoDB.

        Returns:
            Database instance
        """
        if self._client is None:
            self._client = MongoClient(settings.mongodb_uri)
            self._db = self._client[settings.mongodb_database]
            print(f"Connected to MongoDB database: {settings.mongodb_database}")

        return self._db

    def get_database(self) -> Database:
        """
        Get the database instance.

        Returns:
            Database instance
        """
        if self._db is None:
            return self.connect()
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection instance
        """
        db = self.get_database()
        return db[collection_name]

    def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("MongoDB connection closed")


# Global MongoDB instance
mongodb = MongoDB()


def get_db() -> Database:
    """
    Get the MongoDB database instance.

    Returns:
        Database instance
    """
    return mongodb.get_database()


def get_collection(collection_name: str) -> Collection:
    """
    Get a MongoDB collection.

    Args:
        collection_name: Name of the collection

    Returns:
        Collection instance
    """
    return mongodb.get_collection(collection_name)


# Collection names
TASKS_COLLECTION = "tasks"
PROJECTS_COLLECTION = "projects"
SETTINGS_COLLECTION = "settings"


# Task helper functions

def create_task(task: Task, action_note: str = "Task created") -> ObjectId:
    """
    Create a new task with automatic activity logging.

    Args:
        task: Task model instance
        action_note: Note for the activity log entry

    Returns:
        ObjectId of the created task
    """
    now = datetime.utcnow()
    task.created_at = now
    task.updated_at = now

    # Add activity log entry
    task.activity_log.append(ActivityLogEntry(
        timestamp=now,
        action="created",
        note=action_note
    ))

    # Convert to MongoDB document
    task_doc = task.to_mongo()

    # Insert into database
    collection = get_collection(TASKS_COLLECTION)
    result = collection.insert_one(task_doc)

    # Auto-generate episodic summary for new task (activity_count = 1)
    _maybe_generate_task_episodic_summary(result.inserted_id)

    return result.inserted_id


def update_task(
    task_id: ObjectId,
    updates: Dict[str, Any],
    action: str,
    action_note: Optional[str] = None
) -> bool:
    """
    Update a task with automatic activity logging and timestamp management.

    Args:
        task_id: ObjectId of the task to update
        updates: Dictionary of fields to update
        action: Action description for activity log
        action_note: Optional note for the activity log entry

    Returns:
        True if update was successful, False otherwise
    """
    now = datetime.utcnow()
    collection = get_collection(TASKS_COLLECTION)

    # Get current task to check for status changes
    current_task = collection.find_one({"_id": task_id})
    if not current_task:
        return False

    # Handle status-specific timestamps
    if "status" in updates:
        new_status = updates["status"]
        old_status = current_task.get("status")

        if new_status == "in_progress" and old_status != "in_progress":
            updates["started_at"] = now
            updates["last_worked_on"] = now
        elif new_status == "done" and old_status != "done":
            updates["completed_at"] = now
            updates["last_worked_on"] = now
        elif new_status == "in_progress":
            updates["last_worked_on"] = now

    # Update timestamp
    updates["updated_at"] = now

    # Create activity log entry
    activity_entry = ActivityLogEntry(
        timestamp=now,
        action=action,
        note=action_note
    ).model_dump()

    # Update document
    result = collection.update_one(
        {"_id": task_id},
        {
            "$set": updates,
            "$push": {"activity_log": activity_entry}
        }
    )

    if result.modified_count > 0:
        # Auto-generate episodic summary if conditions met
        _maybe_generate_task_episodic_summary(task_id)

    return result.modified_count > 0


def add_task_note(task_id: ObjectId, note: str) -> bool:
    """
    Add a note to a task with automatic activity logging.

    Args:
        task_id: ObjectId of the task
        note: Note text to add

    Returns:
        True if successful, False otherwise
    """
    collection = get_collection(TASKS_COLLECTION)
    now = datetime.utcnow()

    # Create activity log entry
    activity_entry = ActivityLogEntry(
        timestamp=now,
        action="note_added",
        note=note
    ).model_dump()

    result = collection.update_one(
        {"_id": task_id},
        {
            "$push": {
                "notes": note,
                "activity_log": activity_entry
            },
            "$set": {"updated_at": now}
        }
    )

    if result.modified_count > 0:
        # Auto-generate episodic summary if conditions met
        _maybe_generate_task_episodic_summary(task_id)

    return result.modified_count > 0


def get_task(task_id: ObjectId) -> Optional[Task]:
    """
    Get a task by ID.

    Args:
        task_id: ObjectId of the task

    Returns:
        Task model instance or None if not found
    """
    collection = get_collection(TASKS_COLLECTION)
    task_doc = collection.find_one({"_id": task_id})

    if task_doc:
        return Task(**task_doc)
    return None


# Project helper functions

def create_project(project: Project, action_note: str = "Project created") -> ObjectId:
    """
    Create a new project with automatic activity logging.

    Args:
        project: Project model instance
        action_note: Note for the activity log entry

    Returns:
        ObjectId of the created project
    """
    now = datetime.utcnow()
    project.created_at = now
    project.updated_at = now
    project.last_activity = now

    # Add activity log entry
    project.activity_log.append(ActivityLogEntry(
        timestamp=now,
        action="created",
        note=action_note
    ))

    # Convert to MongoDB document
    project_doc = project.to_mongo()

    # Insert into database
    collection = get_collection(PROJECTS_COLLECTION)
    result = collection.insert_one(project_doc)

    return result.inserted_id


def update_project(
    project_id: ObjectId,
    updates: Dict[str, Any],
    action: str,
    action_note: Optional[str] = None
) -> bool:
    """
    Update a project with automatic activity logging.

    Args:
        project_id: ObjectId of the project to update
        updates: Dictionary of fields to update
        action: Action description for activity log
        action_note: Optional note for the activity log entry

    Returns:
        True if update was successful, False otherwise
    """
    now = datetime.utcnow()
    collection = get_collection(PROJECTS_COLLECTION)

    # Update timestamps
    updates["updated_at"] = now
    updates["last_activity"] = now

    # Create activity log entry
    activity_entry = ActivityLogEntry(
        timestamp=now,
        action=action,
        note=action_note
    ).model_dump()

    # Update document
    result = collection.update_one(
        {"_id": project_id},
        {
            "$set": updates,
            "$push": {"activity_log": activity_entry}
        }
    )

    return result.modified_count > 0


def add_project_note(project_id: ObjectId, note: str) -> bool:
    """
    Add a note to a project with automatic activity logging.

    Args:
        project_id: ObjectId of the project
        note: Note text to add

    Returns:
        True if successful, False otherwise
    """
    collection = get_collection(PROJECTS_COLLECTION)
    now = datetime.utcnow()

    # Get current project for episodic summary trigger
    current_project = collection.find_one({"_id": project_id})
    if not current_project:
        return False

    old_activity_count = len(current_project.get("activity_log", []))

    # Create activity log entry
    activity_entry = ActivityLogEntry(
        timestamp=now,
        action="note_added",
        note=note
    ).model_dump()

    # Create project update entry for UI display
    project_update = ProjectUpdate(
        date=now,
        content=note
    ).model_dump()

    result = collection.update_one(
        {"_id": project_id},
        {
            "$push": {
                "activity_log": activity_entry,
                "updates": project_update
            },
            "$set": {
                "updated_at": now,
                "last_activity": now
            }
        }
    )

    if result.modified_count > 0:
        # Auto-generate episodic summary if conditions met
        new_activity_count = old_activity_count + 1
        _maybe_generate_project_episodic_summary(
            project_id,
            old_activity_count=old_activity_count,
            new_activity_count=new_activity_count
        )

    return result.modified_count > 0


def add_project_method(project_id: ObjectId, method: str) -> bool:
    """
    Add a method/technology to a project.

    Args:
        project_id: ObjectId of the project
        method: Method/technology to add

    Returns:
        True if successful, False otherwise
    """
    collection = get_collection(PROJECTS_COLLECTION)
    result = collection.update_one(
        {"_id": project_id},
        {
            "$push": {"methods": method},
            "$set": {
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0


def add_project_decision(project_id: ObjectId, decision: str) -> bool:
    """
    Add a decision to a project.

    Args:
        project_id: ObjectId of the project
        decision: Decision to add

    Returns:
        True if successful, False otherwise
    """
    collection = get_collection(PROJECTS_COLLECTION)
    result = collection.update_one(
        {"_id": project_id},
        {
            "$push": {"decisions": decision},
            "$set": {
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0


def get_project(project_id: ObjectId) -> Optional[Project]:
    """
    Get a project by ID.

    Args:
        project_id: ObjectId of the project

    Returns:
        Project model instance or None if not found
    """
    collection = get_collection(PROJECTS_COLLECTION)
    project_doc = collection.find_one({"_id": project_id})

    if project_doc:
        return Project(**project_doc)
    return None


def get_project_by_name(project_name: str) -> Optional[Project]:
    """
    Get a project by name (case-insensitive exact match).

    Args:
        project_name: Name of the project

    Returns:
        Project model instance or None if not found
    """
    collection = get_collection(PROJECTS_COLLECTION)
    project_doc = collection.find_one({
        "name": {"$regex": f"^{project_name}$", "$options": "i"},
        "is_test": {"$ne": True}
    })

    if project_doc:
        return Project(**project_doc)
    return None


# Settings helper functions

def get_settings(user_id: str = "default") -> Optional[Settings]:
    """
    Get user settings.

    Args:
        user_id: User ID (default: "default")

    Returns:
        Settings model instance or None if not found
    """
    collection = get_collection(SETTINGS_COLLECTION)
    settings_doc = collection.find_one({"user_id": user_id})

    if settings_doc:
        return Settings(**settings_doc)
    return None


def update_settings(user_id: str = "default", **updates) -> bool:
    """
    Update user settings.

    Args:
        user_id: User ID (default: "default")
        **updates: Fields to update

    Returns:
        True if successful, False otherwise
    """
    collection = get_collection(SETTINGS_COLLECTION)
    result = collection.update_one(
        {"user_id": user_id},
        {"$set": updates},
        upsert=True
    )
    return result.modified_count > 0 or result.upserted_id is not None


def set_current_context(
    task_id: Optional[ObjectId] = None,
    project_id: Optional[ObjectId] = None,
    user_id: str = "default"
) -> bool:
    """
    Set the current task and/or project context.

    Args:
        task_id: Optional task ID to set as current
        project_id: Optional project ID to set as current
        user_id: User ID (default: "default")

    Returns:
        True if successful, False otherwise
    """
    updates = {"context_set_at": datetime.utcnow()}

    if task_id is not None:
        updates["current_task_id"] = task_id

    if project_id is not None:
        updates["current_project_id"] = project_id

    return update_settings(user_id, **updates)


# ═══════════════════════════════════════════════════════════════════
# EPISODIC MEMORY AUTO-GENERATION
# ═══════════════════════════════════════════════════════════════════

def _maybe_generate_task_episodic_summary(task_id: ObjectId) -> None:
    """
    Auto-generate episodic memory summary for a task if conditions are met.

    Generates every 3-5 activity log entries (specifically at counts 1, 5, 9, 13, etc.).

    Args:
        task_id: ObjectId of the task
    """
    try:
        # Import here to avoid circular imports
        from shared.episodic import should_generate_task_summary, generate_task_episodic_summary
        from agents.coordinator import memory_manager

        # Get updated task
        task = get_task(task_id)
        if not task:
            return

        # Check if we should generate a summary
        activity_count = len(task.activity_log)
        if should_generate_task_summary(activity_count):
            # Generate summary
            summary = generate_task_episodic_summary(task)

            # Store in memory_episodic collection
            memory_manager.store_episodic_summary(
                user_id="default",  # TODO: Get from context
                entity_type="task",
                entity_id=task_id,
                summary=summary,
                activity_count=activity_count,
                entity_title=task.title,
                entity_status=task.status
            )

    except Exception as e:
        # Silently fail - episodic summary generation is optional
        # Don't break the task update if this fails
        pass


def _maybe_generate_project_episodic_summary(
    project_id: ObjectId,
    old_description: Optional[str] = None,
    new_description: Optional[str] = None,
    old_activity_count: Optional[int] = None,
    new_activity_count: Optional[int] = None
) -> None:
    """
    Auto-generate episodic memory summary for a project if conditions are met.

    Generates when description changes or activity count crosses thresholds.

    Args:
        project_id: ObjectId of the project
        old_description: Previous description (if known)
        new_description: New description (if known)
        old_activity_count: Previous activity count (if known)
        new_activity_count: New activity count (if known)
    """
    try:
        # Import here to avoid circular imports
        from shared.episodic import should_generate_project_summary, generate_project_episodic_summary
        from agents.coordinator import memory_manager

        # Check if we should generate a summary (if we have before/after state)
        if old_description is not None or old_activity_count is not None:
            if not should_generate_project_summary(old_description, new_description, old_activity_count, new_activity_count):
                return

        # Get updated project
        project = get_project(project_id)
        if not project:
            return

        # Get tasks for this project
        tasks_collection = get_collection(TASKS_COLLECTION)
        task_docs = tasks_collection.find({"project_id": project_id})
        tasks = [Task(**doc) for doc in task_docs]

        # Generate summary
        summary = generate_project_episodic_summary(project, tasks)

        # Store in memory_episodic collection
        activity_count = len(project.activity_log)
        memory_manager.store_episodic_summary(
            user_id="default",  # TODO: Get from context
            entity_type="project",
            entity_id=project_id,
            summary=summary,
            activity_count=activity_count,
            entity_title=project.name,
            entity_status=project.status
        )

    except Exception as e:
        # Silently fail - episodic summary generation is optional
        pass
