"""Setup MongoDB indexes for Flow Companion."""

import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure

from shared.db import get_db, TASKS_COLLECTION, PROJECTS_COLLECTION, SETTINGS_COLLECTION


def create_standard_indexes():
    """Create standard indexes for efficient queries."""
    print("\n" + "="*60)
    print("Creating Standard Indexes")
    print("="*60)

    db = get_db()

    # Tasks collection indexes
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
        print(f"✓ Created {len(result)} indexes for tasks collection")
        for index_name in result:
            print(f"  - {index_name}")
    except OperationFailure as e:
        print(f"✗ Error creating task indexes: {e}")

    # Projects collection indexes
    print("\n📁 Creating indexes for 'projects' collection...")
    projects = db[PROJECTS_COLLECTION]

    project_indexes = [
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("last_activity", DESCENDING)], name="idx_last_activity"),
    ]

    try:
        result = projects.create_indexes(project_indexes)
        print(f"✓ Created {len(result)} indexes for projects collection")
        for index_name in result:
            print(f"  - {index_name}")
    except OperationFailure as e:
        print(f"✗ Error creating project indexes: {e}")

    # Settings collection indexes
    print("\n⚙️  Creating indexes for 'settings' collection...")
    settings = db[SETTINGS_COLLECTION]

    settings_indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id", unique=True),
    ]

    try:
        result = settings.create_indexes(settings_indexes)
        print(f"✓ Created {len(result)} indexes for settings collection")
        for index_name in result:
            print(f"  - {index_name}")
    except OperationFailure as e:
        print(f"✗ Error creating settings indexes: {e}")


def create_text_indexes():
    """Create text search indexes for full-text search."""
    print("\n" + "="*60)
    print("Creating Text Search Indexes")
    print("="*60)

    db = get_db()

    # Tasks text index
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
        print("✓ Created text search index for tasks")
        print("  - Fields: title (weight: 10), context (weight: 5), notes (weight: 2)")
    except OperationFailure as e:
        print(f"✗ Error creating tasks text index: {e}")

    # Projects text index
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
        print("✓ Created text search index for projects")
        print("  - Fields: name (10), description (7), context (5), decisions (4), methods (3), notes (2)")
    except OperationFailure as e:
        print(f"✗ Error creating projects text index: {e}")


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
    print("\n📝 Notes:")
    print("  - Index names MUST match exactly: 'task_embedding_index' and 'project_embedding_index'")
    print("  - These names are used in the RetrievalAgent code")
    print("  - numDimensions: 1024 (for Voyage AI voyage-3 model)")
    print("  - similarity: cosine (recommended for text embeddings)")
    print("\n  - Index creation may take a few minutes")
    print("  - You can check index status in the Atlas UI")


def list_existing_indexes():
    """List all existing indexes to verify setup."""
    print("\n" + "="*60)
    print("Existing Indexes Summary")
    print("="*60)

    db = get_db()

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


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("Flow Companion - MongoDB Index Setup")
    print("="*60)

    try:
        # Create standard indexes
        create_standard_indexes()

        # Create text search indexes
        create_text_indexes()

        # List existing indexes
        list_existing_indexes()

        # Print vector index instructions
        print_vector_index_instructions()

        print("\n" + "="*60)
        print("✓ Index Setup Complete!")
        print("="*60)
        print("\n⚠️  Don't forget to create the vector search indexes in Atlas UI!")
        print("   See instructions above ⬆️\n")

    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
