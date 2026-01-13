#!/usr/bin/env python3
"""
MongoDB database setup script for Flow Companion.

Creates all necessary indexes for:
- Tasks and projects collections (standard + text search)
- Memory collections (short-term, long-term, shared)
- Vector search index instructions

Usage:
    # Setup everything
    python scripts/setup_database.py

    # Setup standard indexes only
    python scripts/setup_database.py --standard

    # Setup memory indexes only
    python scripts/setup_database.py --memory

    # List existing indexes
    python scripts/setup_database.py --list
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure
from shared.db import get_db, mongodb, TASKS_COLLECTION, PROJECTS_COLLECTION, SETTINGS_COLLECTION
from memory.setup import setup_memory_collections


def create_standard_indexes(db, verbose=True):
    """Create standard indexes for efficient queries."""

    if verbose:
        print("\n" + "="*60)
        print("Creating Standard Indexes")
        print("="*60)

    # Tasks collection indexes
    if verbose:
        print("\n📋 Creating indexes for 'tasks' collection...")
    tasks = db[TASKS_COLLECTION]

    task_indexes = [
        IndexModel([("project_id", ASCENDING)], name="idx_project_id"),
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("last_worked_on", DESCENDING)], name="idx_last_worked_on"),
        IndexModel([("activity_log.timestamp", DESCENDING)], name="idx_activity_timestamp"),
        IndexModel([("project_id", ASCENDING), ("status", ASCENDING)], name="idx_project_status"),
        IndexModel([("status", ASCENDING), ("priority", ASCENDING)], name="idx_status_priority"),
    ]

    try:
        result = tasks.create_indexes(task_indexes)
        if verbose:
            print(f"✓ Created {len(result)} indexes for tasks collection")
            for index_name in result:
                print(f"  - {index_name}")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating task indexes: {e}")

    # Projects collection indexes
    if verbose:
        print("\n📁 Creating indexes for 'projects' collection...")
    projects = db[PROJECTS_COLLECTION]

    project_indexes = [
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("last_activity", DESCENDING)], name="idx_last_activity"),
    ]

    try:
        result = projects.create_indexes(project_indexes)
        if verbose:
            print(f"✓ Created {len(result)} indexes for projects collection")
            for index_name in result:
                print(f"  - {index_name}")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating project indexes: {e}")

    # Settings collection indexes
    if verbose:
        print("\n⚙️  Creating indexes for 'settings' collection...")
    settings = db[SETTINGS_COLLECTION]

    settings_indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id", unique=True),
    ]

    try:
        result = settings.create_indexes(settings_indexes)
        if verbose:
            print(f"✓ Created {len(result)} indexes for settings collection")
            for index_name in result:
                print(f"  - {index_name}")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating settings indexes: {e}")


def create_text_indexes(db, verbose=True):
    """Create text search indexes for full-text search."""

    if verbose:
        print("\n" + "="*60)
        print("Creating Text Search Indexes")
        print("="*60)

    # Tasks text index
    if verbose:
        print("\n📋 Creating text index for 'tasks' collection...")
    tasks = db[TASKS_COLLECTION]

    try:
        tasks.create_index(
            [
                ("title", TEXT),
                ("context", TEXT),
                ("notes", TEXT),
            ],
            name="idx_text_search",
            weights={
                "title": 10,      # Higher weight for title matches
                "context": 5,     # Medium weight for context
                "notes": 2        # Lower weight for notes
            }
        )
        if verbose:
            print("✓ Created text search index for tasks")
            print("  - Fields: title (weight: 10), context (weight: 5), notes (weight: 2)")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating tasks text index: {e}")

    # Projects text index
    if verbose:
        print("\n📁 Creating text index for 'projects' collection...")
    projects = db[PROJECTS_COLLECTION]

    try:
        projects.create_index(
            [
                ("name", TEXT),
                ("description", TEXT),
                ("context", TEXT),
                ("notes", TEXT),
                ("methods", TEXT),
                ("decisions", TEXT),
            ],
            name="idx_text_search",
            weights={
                "name": 10,           # Highest weight for name
                "description": 7,     # High weight for description
                "context": 5,         # Medium weight for context
                "decisions": 4,       # Medium-low for decisions
                "methods": 3,         # Lower for methods
                "notes": 2            # Lowest for notes
            }
        )
        if verbose:
            print("✓ Created text search index for projects")
            print("  - Fields: name (10), description (7), context (5), decisions (4), methods (3), notes (2)")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating projects text index: {e}")


def create_memory_indexes(db, verbose=True):
    """Create indexes for memory collections."""

    if verbose:
        print("\n" + "="*60)
        print("Creating Memory Collection Indexes")
        print("="*60)

    # Use the setup function from memory package
    setup_memory_collections(db)

    if verbose:
        print("\n✅ All memory indexes created successfully!")
        print("\nMemory Collections:")
        print("  - memory_short_term: Session context (2-hour TTL)")
        print("  - memory_long_term: Action history (persistent, with vector search)")
        print("  - memory_shared: Agent handoffs (5-minute TTL)")

        # Show index summary
        short_term = db["memory_short_term"]
        long_term = db["memory_long_term"]
        shared = db["memory_shared"]

        print("\n📊 Memory Index Summary:")
        print(f"  memory_short_term: {len(list(short_term.list_indexes()))} indexes")
        print(f"  memory_long_term: {len(list(long_term.list_indexes()))} indexes")
        print(f"  memory_shared: {len(list(shared.list_indexes()))} indexes")


def print_vector_index_instructions():
    """Print instructions for creating vector search indexes in Atlas."""

    print("\n" + "="*60)
    print("Vector Search Indexes (Manual Setup Required)")
    print("="*60)

    print("\n⚠️  Vector search indexes must be created in the MongoDB Atlas UI or via Atlas Admin API.")
    print("\nPlease follow these steps:")
    print("\n1. Go to your MongoDB Atlas cluster")
    print("2. Navigate to: Database → Browse Collections → Search Indexes")
    print("3. Click 'Create Index' → 'JSON Editor'")
    print("4. Create the following indexes:")

    print("\n" + "-"*60)
    print("📋 TASKS VECTOR INDEX")
    print("-"*60)
    print("""
{
  "name": "task_embedding_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embedding",
        "type": "vector",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
""")

    print("-"*60)
    print("📁 PROJECTS VECTOR INDEX")
    print("-"*60)
    print("""
{
  "name": "project_embedding_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embedding",
        "type": "vector",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
""")

    print("-"*60)
    print("🧠 LONG-TERM MEMORY VECTOR INDEX")
    print("-"*60)
    print("""
{
  "name": "memory_embeddings",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embedding",
        "type": "vector",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
""")

    print("-"*60)
    print("\n📝 Notes:")
    print("  - Index names MUST match exactly:")
    print("    * 'task_embedding_index' (tasks collection)")
    print("    * 'project_embedding_index' (projects collection)")
    print("    * 'memory_embeddings' (memory_long_term collection)")
    print("  - These names are used in the RetrievalAgent and MemoryManager code")
    print("  - numDimensions: 1024 (for Voyage AI voyage-3 model)")
    print("  - similarity: cosine (recommended for text embeddings)")
    print("\n  - Index creation may take a few minutes")
    print("  - You can check index status in the Atlas UI")


def list_existing_indexes(db):
    """List all existing indexes to verify setup."""

    print("\n" + "="*60)
    print("Existing Indexes Summary")
    print("="*60)

    # Tasks indexes
    print("\n📋 Tasks collection indexes:")
    tasks = db[TASKS_COLLECTION]
    for index in tasks.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")

    # Projects indexes
    print("\n📁 Projects collection indexes:")
    projects = db[PROJECTS_COLLECTION]
    for index in projects.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")

    # Settings indexes
    print("\n⚙️  Settings collection indexes:")
    settings = db[SETTINGS_COLLECTION]
    for index in settings.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")

    # Memory collection indexes
    if "memory_short_term" in db.list_collection_names():
        print("\n🧠 Short-term Memory indexes:")
        short_term = db["memory_short_term"]
        for index in short_term.list_indexes():
            print(f"  - {index['name']}: {index.get('key', {})}")

    if "memory_long_term" in db.list_collection_names():
        print("\n🧠 Long-term Memory indexes:")
        long_term = db["memory_long_term"]
        for index in long_term.list_indexes():
            print(f"  - {index['name']}: {index.get('key', {})}")

    if "memory_shared" in db.list_collection_names():
        print("\n🧠 Shared Memory indexes:")
        shared = db["memory_shared"]
        for index in shared.list_indexes():
            print(f"  - {index['name']}: {index.get('key', {})}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup MongoDB indexes for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--standard",
        action="store_true",
        help="Setup standard indexes only (tasks, projects, settings)"
    )

    parser.add_argument(
        "--memory",
        action="store_true",
        help="Setup memory indexes only (short-term, long-term, shared)"
    )

    parser.add_argument(
        "--text",
        action="store_true",
        help="Setup text search indexes only"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing indexes"
    )

    parser.add_argument(
        "--vector-instructions",
        action="store_true",
        help="Show vector index creation instructions only"
    )

    args = parser.parse_args()

    # Connect to database
    mongodb.connect()
    db = get_db()

    # Handle list only
    if args.list:
        list_existing_indexes(db)
        return

    # Handle vector instructions only
    if args.vector_instructions:
        print_vector_index_instructions()
        return

    # Determine what to setup
    setup_all = not any([args.standard, args.memory, args.text])

    try:
        print("\n" + "="*60)
        print("Flow Companion - MongoDB Index Setup")
        print("="*60)

        # Create standard indexes
        if setup_all or args.standard:
            create_standard_indexes(db)

        # Create text search indexes
        if setup_all or args.text:
            create_text_indexes(db)

        # Create memory indexes
        if setup_all or args.memory:
            create_memory_indexes(db)

        # List existing indexes
        if setup_all:
            list_existing_indexes(db)
            print_vector_index_instructions()

        print("\n" + "="*60)
        print("✓ Database Setup Complete!")
        print("="*60)

        if setup_all:
            print("\n⚠️  Don't forget to create the vector search indexes in Atlas UI!")
            print("   See instructions above ⬆️\n")

    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
