#!/usr/bin/env python3
"""
Cleanup script to remove test data pollution from the database.

This script removes:
- Test tasks created by automated tests
- Tasks with malformed titles (flag parsing bugs)
- Orphan tasks (no project_id when project is required)
- Tasks with nonexistent project references
"""

from shared.db import get_db, mongodb

def cleanup_test_data():
    """Remove test data artifacts from the database."""

    # Connect to database
    mongodb.connect()
    db = get_db()

    print("=" * 60)
    print("Database Cleanup - Removing Test Artifacts")
    print("=" * 60)
    print()

    # 1. Delete test tasks (created by automated tests)
    print("1. Removing 'Test Task' entries...")
    result1 = db.tasks.delete_many({
        "$or": [
            {"title": {"$regex": "^Test Task"}},
            {"title": {"$regex": "^Write unit tests for slash commands"}},
            {"title": {"$regex": "^Review documentation"}},
        ]
    })
    print(f"   ✓ Deleted {result1.deleted_count} test task entries")
    print()

    # 2. Delete tasks with malformed titles (flag parsing bugs)
    print("2. Removing tasks with malformed titles (flag bugs)...")
    result2 = db.tasks.delete_many({
        "$or": [
            {"title": {"$regex": "^-t "}},
            {"title": {"$regex": "^-p "}},
            {"title": {"$regex": "^--"}},
        ]
    })
    print(f"   ✓ Deleted {result2.deleted_count} malformed tasks")
    print()

    # 3. Get valid project IDs
    print("3. Validating project references...")
    valid_project_ids = [p["_id"] for p in db.projects.find({}, {"_id": 1})]
    print(f"   Found {len(valid_project_ids)} valid projects")

    # 4. Delete tasks with nonexistent project references
    print("4. Removing tasks with invalid project_id...")
    result4 = db.tasks.delete_many({
        "project_id": {"$ne": None, "$nin": valid_project_ids}
    })
    print(f"   ✓ Deleted {result4.deleted_count} tasks with invalid project_id")
    print()

    # 5. Show summary
    total_deleted = (
        result1.deleted_count +
        result2.deleted_count +
        result4.deleted_count
    )

    print("=" * 60)
    print(f"Cleanup Complete: {total_deleted} total artifacts removed")
    print("=" * 60)
    print()

    # 6. Show current counts
    print("Current Database Status:")
    tasks_count = db.tasks.count_documents({})
    projects_count = db.projects.count_documents({})
    print(f"  - Tasks: {tasks_count}")
    print(f"  - Projects: {projects_count}")
    print()

    # 7. Show tasks without projects (orphans - might be intentional)
    orphan_count = db.tasks.count_documents({"project_id": None})
    if orphan_count > 0:
        print(f"⚠️  Note: {orphan_count} tasks have no project_id (might be intentional)")
        print("   These were NOT deleted. To remove orphans, run:")
        print("   db.tasks.delete_many({'project_id': None})")
        print()

if __name__ == "__main__":
    cleanup_test_data()
