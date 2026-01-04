#!/usr/bin/env python3
"""Clean up test data pollution from the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION

def cleanup_test_data():
    """Remove test data pollution."""
    tasks_collection = get_collection(TASKS_COLLECTION)
    projects_collection = get_collection(PROJECTS_COLLECTION)

    print("=== Cleaning up test data pollution ===\n")

    # 1. Delete tasks marked as test data
    result1 = tasks_collection.delete_many({"is_test": True})
    print(f"✓ Deleted {result1.deleted_count} tasks with is_test=True")

    # 2. Delete tasks with no project (orphaned)
    result2 = tasks_collection.delete_many({"project_id": None})
    print(f"✓ Deleted {result2.deleted_count} tasks with no project_id")

    # 3. Delete tasks starting with "Test"
    result3 = tasks_collection.delete_many({"title": {"$regex": "^Test"}})
    print(f"✓ Deleted {result3.deleted_count} tasks with title starting with 'Test'")

    # 4. Delete projects marked as test data
    result4 = projects_collection.delete_many({"is_test": True})
    print(f"✓ Deleted {result4.deleted_count} projects with is_test=True")

    total_deleted = result1.deleted_count + result2.deleted_count + result3.deleted_count + result4.deleted_count
    print(f"\n✅ Total deleted: {total_deleted} documents")

    # Show remaining counts
    remaining_tasks = tasks_collection.count_documents({})
    remaining_projects = projects_collection.count_documents({})
    print(f"\n📊 Remaining: {remaining_tasks} tasks, {remaining_projects} projects")

if __name__ == "__main__":
    cleanup_test_data()
