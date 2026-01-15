#!/usr/bin/env python3
"""
Database cleanup script for Flow Companion.

Consolidated script for all database cleanup operations:
- Mark and remove test data pollution
- Remove orphaned tasks (no project_id)
- Remove tasks with invalid project references
- Remove duplicate tasks

Usage:
    # Mark test data (safe, doesn't delete)
    python scripts/cleanup_database.py --mark

    # Delete all marked test data
    python scripts/cleanup_database.py --delete

    # Mark and delete in one command
    python scripts/cleanup_database.py --mark --delete

    # Remove specific duplicates
    python scripts/cleanup_database.py --remove-duplicates "Task Title"

    # Full cleanup (mark + delete + remove orphans)
    python scripts/cleanup_database.py --full
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_db, mongodb


def mark_test_data(db, verbose=True):
    """Mark test-like data with is_test=True flag."""

    if verbose:
        print("=" * 60)
        print("Marking Test Data")
        print("=" * 60)
        print()

    marked_count = 0

    # 1. Mark test tasks (pattern matching)
    if verbose:
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
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    marked_count += result1.modified_count
    if verbose:
        print(f"   ✓ Marked {result1.modified_count} tasks")

    # 2. Mark orphan tasks (no project_id)
    if verbose:
        print("2. Marking orphan tasks...")
    result2 = db.tasks.update_many(
        {
            "project_id": None,
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    marked_count += result2.modified_count
    if verbose:
        print(f"   ✓ Marked {result2.modified_count} orphan tasks")

    # 3. Mark test projects
    if verbose:
        print("3. Marking test projects...")
    result3 = db.projects.update_many(
        {
            "name": {"$regex": "^Test"},
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    marked_count += result3.modified_count
    if verbose:
        print(f"   ✓ Marked {result3.modified_count} projects")

    # 4. Mark tasks with invalid project references
    if verbose:
        print("4. Marking tasks with invalid project_id...")
    valid_project_ids = [
        p["_id"] for p in db.projects.find(
            {"is_test": {"$ne": True}},
            {"_id": 1}
        )
    ]

    result4 = db.tasks.update_many(
        {
            "project_id": {"$ne": None, "$nin": valid_project_ids},
            "is_test": {"$exists": False}
        },
        {"$set": {"is_test": True}}
    )
    marked_count += result4.modified_count
    if verbose:
        print(f"   ✓ Marked {result4.modified_count} tasks with invalid project_id")

    if verbose:
        print()
        print(f"Total marked: {marked_count} items")
        print()

    return marked_count


def delete_test_data(db, verbose=True):
    """Delete all data marked with is_test=True."""

    if verbose:
        print("=" * 60)
        print("Deleting Test Data")
        print("=" * 60)
        print()

    # 1. Delete test tasks
    if verbose:
        print("1. Deleting test tasks...")
    result1 = db.tasks.delete_many({"is_test": True})
    if verbose:
        print(f"   ✓ Deleted {result1.deleted_count} tasks")

    # 2. Delete test projects
    if verbose:
        print("2. Deleting test projects...")
    result2 = db.projects.delete_many({"is_test": True})
    if verbose:
        print(f"   ✓ Deleted {result2.deleted_count} projects")

    total_deleted = result1.deleted_count + result2.deleted_count

    if verbose:
        print()
        print(f"Total deleted: {total_deleted} items")
        print()

    return total_deleted


def remove_duplicates(db, title_pattern=None, project_name=None, verbose=True):
    """Remove duplicate tasks, keeping the oldest one."""

    if verbose:
        print("=" * 60)
        print("Removing Duplicate Tasks")
        print("=" * 60)
        print()

    query = {}
    if title_pattern:
        query["title"] = title_pattern
    if project_name:
        project = db.projects.find_one({"name": {"$regex": project_name, "$options": "i"}})
        if project:
            query["project_id"] = project["_id"]
        else:
            if verbose:
                print(f"Project '{project_name}' not found")
            return 0

    if not query:
        if verbose:
            print("No query specified, skipping duplicate removal")
        return 0

    # Find duplicates
    duplicates = list(db.tasks.find(query).sort("created_at", 1))

    if len(duplicates) <= 1:
        if verbose:
            print(f"No duplicates found for query: {query}")
        return 0

    # Keep first, delete rest
    to_delete = duplicates[1:]
    delete_ids = [t["_id"] for t in to_delete]
    result = db.tasks.delete_many({"_id": {"$in": delete_ids}})

    if verbose:
        print(f"Found {len(duplicates)} tasks matching {query}")
        print(f"Kept: {duplicates[0]['_id']}")
        print(f"Deleted: {result.deleted_count} duplicates")

    return result.deleted_count


def show_status(db):
    """Display current database status."""

    print("=" * 60)
    print("Database Status")
    print("=" * 60)
    print()

    # Count documents
    tasks_count = db.tasks.count_documents({"is_test": {"$ne": True}})
    test_tasks_count = db.tasks.count_documents({"is_test": True})
    projects_count = db.projects.count_documents({"is_test": {"$ne": True}})
    test_projects_count = db.projects.count_documents({"is_test": True})

    print(f"Production Tasks: {tasks_count}")
    print(f"Test Tasks: {test_tasks_count}")
    print(f"Production Projects: {projects_count}")
    print(f"Test Projects: {test_projects_count}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Database cleanup script for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--mark",
        action="store_true",
        help="Mark test data with is_test=True flag"
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete all data marked as test data"
    )

    parser.add_argument(
        "--remove-duplicates",
        metavar="TITLE",
        help="Remove duplicate tasks with specified title"
    )

    parser.add_argument(
        "--project",
        metavar="PROJECT_NAME",
        help="Filter duplicates by project name (use with --remove-duplicates)"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Full cleanup: mark + delete + show status"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show database status only"
    )

    args = parser.parse_args()

    # Connect to database
    mongodb.connect()
    db = get_db()

    # Handle --status
    if args.status:
        show_status(db)
        return

    # Handle --full
    if args.full:
        mark_test_data(db)
        delete_test_data(db)
        show_status(db)
        return

    # Handle individual operations
    if args.mark:
        mark_test_data(db)

    if args.delete:
        delete_test_data(db)

    if args.remove_duplicates:
        remove_duplicates(
            db,
            title_pattern=args.remove_duplicates,
            project_name=args.project
        )

    # Show status at the end
    show_status(db)


if __name__ == "__main__":
    main()
