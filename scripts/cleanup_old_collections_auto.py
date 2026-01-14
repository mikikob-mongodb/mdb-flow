#!/usr/bin/env python3
"""
Non-interactive cleanup script to drop old memory collections.

WARNING: This will immediately delete data without confirmation!
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
    print("Dropping the following collections:")
    total_docs = 0
    for col in to_drop:
        count = db[col].count_documents({})
        total_docs += count
        print(f"  - {col} ({count} documents)")
    print("")

    # Drop each collection
    print("Dropping collections...")
    for col in to_drop:
        print(f"  Dropping {col}...", end=" ")
        db[col].drop()
        print("✅ Done")

    print("")
    print(f"✅ Successfully dropped {len(to_drop)} old collection(s) ({total_docs} documents total)")
    print("")
    print("New memory structure:")
    print("  - memory_episodic: Actions and events (persistent)")
    print("  - memory_semantic: Knowledge cache and preferences (persistent)")
    print("  - memory_procedural: Templates and workflows (persistent)")
    print("  - Working memory: Session context, handoffs, disambiguation (in-memory only)")
    print("")

    # Verify new collections exist
    print("Verifying new collections...")
    new_collections = ["memory_episodic", "memory_semantic", "memory_procedural"]
    for col in new_collections:
        if col in existing_collections:
            count = db[col].count_documents({})
            print(f"  ✅ {col}: {count} documents")
        else:
            print(f"  ⚠️  {col}: NOT FOUND (will be created on first use)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
