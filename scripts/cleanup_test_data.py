#!/usr/bin/env python3
"""
Cleanup script to remove test data pollution from the database.

This script:
1. Marks test-like data with is_test=True flag
2. Optionally deletes all data marked as test data

Benefits:
- Production queries automatically exclude test data (is_test != true)
- Easy cleanup with simple query: {is_test: true}
- No complex regex patterns needed
- Can toggle test data visibility for debugging
"""

from shared.db import get_db, mongodb
import sys

def mark_test_data():
    """Mark existing test-like data with is_test=True flag."""

    # Connect to database
    mongodb.connect()
    db = get_db()

    print("=" * 60)
    print("Database Cleanup - Marking Test Data")
    print("=" * 60)
    print()

    # 1. Mark test tasks (pattern matching)
    print("1. Marking test task patterns...")
    result1 = db.tasks.update_many(
        {
            "$or": [
                {"title": {"$regex": "^Test"}},
                {"title": {"$regex": "^Write unit tests"}},
                {"title": {"$regex": "^Review documentation"}},
                {"title": {"$regex": "^-t "}},  # Malformed
                {"title": {"$regex": "^-p "}},  # Malformed
                {"title": {"$regex": "^--"}},   # Malformed
            ],
            "is_test": {"$exists": False}  # Only mark if not already marked
        },
        {"$set": {"is_test": True}}
    )
    print(f"   ✓ Marked {result1.modified_count} tasks as test data")
    print()

    # 2. Mark orphan tasks (no project_id)
    print("2. Marking orphan tasks (no project)...")
    result2 = db.tasks.update_many(
        {
            "project_id": None,
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    print(f"   ✓ Marked {result2.modified_count} orphan tasks as test data")
    print()

    # 3. Mark test projects (pattern matching)
    print("3. Marking test project patterns...")
    result3 = db.projects.update_many(
        {
            "name": {"$regex": "^Test"},
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    print(f"   ✓ Marked {result3.modified_count} projects as test data")
    print()

    # 4. Get valid project IDs (non-test)
    print("4. Validating project references...")
    valid_project_ids = [
        p["_id"] for p in db.projects.find(
            {"is_test": {"$ne": True}},
            {"_id": 1}
        )
    ]
    print(f"   Found {len(valid_project_ids)} valid (non-test) projects")

    # 5. Mark tasks with nonexistent project references
    print("5. Marking tasks with invalid project_id...")
    result5 = db.tasks.update_many(
        {
            "project_id": {"$ne": None, "$nin": valid_project_ids},
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    print(f"   ✓ Marked {result5.modified_count} tasks with invalid project_id")
    print()

    # 6. Show summary
    total_marked = (
        result1.modified_count +
        result2.modified_count +
        result3.modified_count +
        result5.modified_count
    )

    print("=" * 60)
    print(f"Marking Complete: {total_marked} total items marked as test data")
    print("=" * 60)
    print()

    # 7. Show current counts
    print("Current Database Status:")
    tasks_count = db.tasks.count_documents({"is_test": {"$ne": True}})
    test_tasks_count = db.tasks.count_documents({"is_test": True})
    projects_count = db.projects.count_documents({"is_test": {"$ne": True}})
    test_projects_count = db.projects.count_documents({"is_test": True})

    print(f"  - Production Tasks: {tasks_count}")
    print(f"  - Test Tasks: {test_tasks_count}")
    print(f"  - Production Projects: {projects_count}")
    print(f"  - Test Projects: {test_projects_count}")
    print()

    return test_tasks_count, test_projects_count


def delete_test_data():
    """Delete all data marked with is_test=True."""

    # Connect to database
    mongodb.connect()
    db = get_db()

    print("=" * 60)
    print("Deleting Test Data")
    print("=" * 60)
    print()

    # 1. Delete test tasks
    print("1. Deleting test tasks...")
    result1 = db.tasks.delete_many({"is_test": True})
    print(f"   ✓ Deleted {result1.deleted_count} test tasks")
    print()

    # 2. Delete test projects
    print("2. Deleting test projects...")
    result2 = db.projects.delete_many({"is_test": True})
    print(f"   ✓ Deleted {result2.deleted_count} test projects")
    print()

    total_deleted = result1.deleted_count + result2.deleted_count

    print("=" * 60)
    print(f"Deletion Complete: {total_deleted} total items deleted")
    print("=" * 60)
    print()

    # Show remaining counts
    tasks_count = db.tasks.count_documents({})
    projects_count = db.projects.count_documents({})
    print(f"  - Remaining Tasks: {tasks_count}")
    print(f"  - Remaining Projects: {projects_count}")
    print()


if __name__ == "__main__":
    # Step 1: Always mark test data
    test_tasks, test_projects = mark_test_data()

    # Step 2: Ask if user wants to delete
    if test_tasks > 0 or test_projects > 0:
        print()
        response = input(f"Delete {test_tasks + test_projects} test items? (y/n): ")
        if response.lower() == 'y':
            delete_test_data()
        else:
            print("\nTest data marked but not deleted.")
            print("Production queries will automatically exclude test data.")
            print("To delete later, run: db.tasks.delete_many({'is_test': True})")
    else:
        print("No test data found to delete.")
