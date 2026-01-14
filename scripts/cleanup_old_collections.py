#!/usr/bin/env python3
"""
Cleanup script to drop old memory collections after migration.

Run this AFTER the code migration is complete to remove:
- memory_short_term (replaced by in-memory dicts)
- memory_long_term (split to memory_episodic + memory_semantic)
- memory_shared (replaced by in-memory dicts)

WARNING: This will permanently delete data. Backup first if needed.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from dotenv import load_dotenv

def main():
    """Drop old memory collections from the database."""

    # Load environment variables
    load_dotenv()

    # Get MongoDB connection string
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment")
        return 1

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = MongoClient(mongodb_uri)

    # Get database name from URI or use default
    db_name = os.getenv("MONGODB_DATABASE", "mdb_flow")
    db = client[db_name]

    print(f"Database: {db_name}")
    print("")

    # List old collections to drop
    old_collections = [
        "memory_short_term",
        "memory_long_term",
        "memory_shared"
    ]

    # Check which collections exist
    existing_collections = db.list_collection_names()
    to_drop = [col for col in old_collections if col in existing_collections]

    if not to_drop:
        print("✅ No old collections found. Migration cleanup already complete!")
        return 0

    # Show what will be dropped
    print("The following collections will be PERMANENTLY DELETED:")
    for col in to_drop:
        count = db[col].count_documents({})
        print(f"  - {col} ({count} documents)")
    print("")

    # Confirm deletion
    print("⚠️  WARNING: This action cannot be undone!")
    response = input("Type 'DROP' to confirm deletion: ")

    if response != "DROP":
        print("❌ Deletion cancelled")
        return 1

    print("")
    print("Dropping collections...")

    # Drop each collection
    for col in to_drop:
        print(f"  Dropping {col}...", end=" ")
        db[col].drop()
        print("✅ Done")

    print("")
    print(f"✅ Successfully dropped {len(to_drop)} old collection(s)")
    print("")
    print("New memory structure:")
    print("  - memory_episodic: Actions and events (persistent)")
    print("  - memory_semantic: Knowledge cache and preferences (persistent)")
    print("  - memory_procedural: Templates and workflows (persistent)")
    print("  - Working memory: Session context, handoffs, disambiguation (in-memory only)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
