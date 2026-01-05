#!/usr/bin/env python3
"""
One-time cleanup script to delete duplicate "Review documentation" tasks.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_db


def cleanup_duplicates():
    db = get_db()

    # Find AgentOps project
    agentops = db.projects.find_one({"name": {"$regex": "AgentOps", "$options": "i"}})
    if not agentops:
        print("AgentOps project not found")
        return

    # Find all "Review documentation" tasks in AgentOps
    duplicates = list(db.tasks.find({
        "title": "Review documentation",
        "project_id": agentops["_id"]
    }).sort("created_at", 1))  # Sort by oldest first

    print(f"Found {len(duplicates)} 'Review documentation' tasks in AgentOps")

    if len(duplicates) <= 1:
        print("No duplicates to remove")
        return

    # Keep the first one, delete the rest
    keep = duplicates[0]
    to_delete = duplicates[1:]

    delete_ids = [t["_id"] for t in to_delete]
    result = db.tasks.delete_many({"_id": {"$in": delete_ids}})

    print(f"Kept: {keep['_id']}")
    print(f"Deleted: {result.deleted_count} duplicate tasks")


if __name__ == "__main__":
    cleanup_duplicates()
