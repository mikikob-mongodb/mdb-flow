#!/usr/bin/env python3
"""
MongoDB Database Initialization Script for Flow Companion.

Creates all collections and indexes required for the application to function.
This should be run ONCE when setting up a new database or environment.

Features:
    - Creates all 8 required collections
    - Creates standard indexes (tasks, projects, settings)
    - Creates memory system indexes (short-term, long-term, shared)
    - Creates tool discovery indexes (MCP Agent)
    - Creates evaluation indexes
    - Creates TTL indexes for automatic document expiration
    - Creates text search indexes for full-text search
    - Provides instructions for vector search indexes (Atlas UI)

Usage:
    # Initialize everything (recommended for first-time setup)
    python scripts/init_db.py

    # Initialize specific components
    python scripts/init_db.py --collections-only
    python scripts/init_db.py --indexes-only

    # List what exists
    python scripts/init_db.py --check

    # Force recreate indexes (drop existing)
    python scripts/init_db.py --force
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure, CollectionInvalid
from shared.db import MongoDB
from shared.config import settings

# =============================================================================
# CONFIGURATION
# =============================================================================

# All collections used by the application
COLLECTIONS = {
    # Main application collections
    "tasks": "User tasks with activity logging",
    "projects": "User projects with activity tracking",
    "settings": "User settings and current context",

    # Memory system collections
    "short_term_memory": "Session context (2-hour TTL)",
    "long_term_memory": "Persistent memory (episodic, semantic, procedural)",
    "shared_memory": "Agent handoffs (5-minute TTL)",

    # MCP Agent collections
    "tool_discoveries": "MCP tool usage learning and reuse",

    # Evaluation collections
    "eval_comparison_runs": "Evaluation comparison run results"
}

# =============================================================================
# COLLECTION CREATION
# =============================================================================

def create_collections(db_instance, force: bool = False) -> Dict[str, str]:
    """
    Create all required collections.

    Args:
        db_instance: MongoDB database instance
        force: If True, drop and recreate collections (dangerous!)

    Returns:
        Dictionary of collection name to status
    """
    print("\n" + "="*70)
    print("CREATING COLLECTIONS")
    print("="*70)

    results = {}
    existing = set(db_instance.list_collection_names())

    for collection_name, description in COLLECTIONS.items():
        try:
            if collection_name in existing:
                if force:
                    print(f"\n⚠️  Dropping existing collection: {collection_name}")
                    db_instance[collection_name].drop()
                    db_instance.create_collection(collection_name)
                    results[collection_name] = "recreated"
                    print(f"✓ {collection_name}: RECREATED")
                else:
                    results[collection_name] = "exists"
                    print(f"  {collection_name}: already exists")
            else:
                db_instance.create_collection(collection_name)
                results[collection_name] = "created"
                print(f"✓ {collection_name}: CREATED")
                print(f"    → {description}")

        except CollectionInvalid as e:
            results[collection_name] = f"error: {e}"
            print(f"✗ {collection_name}: ERROR - {e}")
        except Exception as e:
            results[collection_name] = f"error: {e}"
            print(f"✗ {collection_name}: ERROR - {e}")

    created_count = sum(1 for v in results.values() if v in ["created", "recreated"])
    existing_count = sum(1 for v in results.values() if v == "exists")

    print(f"\n📊 Summary: {created_count} created, {existing_count} already existed")

    return results

# =============================================================================
# INDEX CREATION - TASKS
# =============================================================================

def create_tasks_indexes(db_instance, verbose: bool = True) -> List[str]:
    """Create indexes for tasks collection."""

    if verbose:
        print("\n" + "-"*70)
        print("📋 TASKS COLLECTION INDEXES")
        print("-"*70)

    tasks = db_instance["tasks"]
    created_indexes = []

    # Standard indexes
    indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id"),
        IndexModel([("project_id", ASCENDING)], name="idx_project_id"),
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("priority", ASCENDING)], name="idx_priority"),
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("last_worked_on", DESCENDING)], name="idx_last_worked_on"),
        IndexModel([("activity_log.timestamp", DESCENDING)], name="idx_activity_timestamp"),

        # Compound indexes for common queries
        IndexModel([("user_id", ASCENDING), ("project_id", ASCENDING)], name="idx_user_project"),
        IndexModel([("project_id", ASCENDING), ("status", ASCENDING)], name="idx_project_status"),
        IndexModel([("status", ASCENDING), ("priority", ASCENDING)], name="idx_status_priority"),
        IndexModel([("user_id", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING)], name="idx_user_status_priority"),
    ]

    try:
        result = tasks.create_indexes(indexes)
        created_indexes.extend(result)
        if verbose:
            print(f"✓ Created {len(result)} standard indexes")
            for index_name in result:
                print(f"    - {index_name}")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating standard indexes: {e}")

    # Text search index
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
        created_indexes.append("idx_text_search")
        if verbose:
            print(f"✓ Created text search index")
            print(f"    - Fields: title (weight: 10), context (5), notes (2)")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating text search index: {e}")

    return created_indexes

# =============================================================================
# INDEX CREATION - PROJECTS
# =============================================================================

def create_projects_indexes(db_instance, verbose: bool = True) -> List[str]:
    """Create indexes for projects collection."""

    if verbose:
        print("\n" + "-"*70)
        print("📁 PROJECTS COLLECTION INDEXES")
        print("-"*70)

    projects = db_instance["projects"]
    created_indexes = []

    # Standard indexes
    indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id"),
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("last_activity", DESCENDING)], name="idx_last_activity"),

        # Compound indexes
        IndexModel([("user_id", ASCENDING), ("status", ASCENDING)], name="idx_user_status"),
        IndexModel([("user_id", ASCENDING), ("last_activity", DESCENDING)], name="idx_user_activity"),
    ]

    try:
        result = projects.create_indexes(indexes)
        created_indexes.extend(result)
        if verbose:
            print(f"✓ Created {len(result)} standard indexes")
            for index_name in result:
                print(f"    - {index_name}")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating standard indexes: {e}")

    # Text search index
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
        created_indexes.append("idx_text_search")
        if verbose:
            print(f"✓ Created text search index")
            print(f"    - Fields: name (10), description (7), context (5), decisions (4), methods (3), notes (2)")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating text search index: {e}")

    return created_indexes

# =============================================================================
# INDEX CREATION - SETTINGS
# =============================================================================

def create_settings_indexes(db_instance, verbose: bool = True) -> List[str]:
    """Create indexes for settings collection."""

    if verbose:
        print("\n" + "-"*70)
        print("⚙️  SETTINGS COLLECTION INDEXES")
        print("-"*70)

    settings_col = db_instance["settings"]
    created_indexes = []

    indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id", unique=True),
    ]

    try:
        result = settings_col.create_indexes(indexes)
        created_indexes.extend(result)
        if verbose:
            print(f"✓ Created unique index on user_id")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating settings indexes: {e}")

    return created_indexes

# =============================================================================
# INDEX CREATION - MEMORY COLLECTIONS
# =============================================================================

def create_memory_indexes(db_instance, verbose: bool = True) -> Dict[str, List[str]]:
    """Create indexes for all memory collections."""

    if verbose:
        print("\n" + "-"*70)
        print("🧠 MEMORY SYSTEM INDEXES")
        print("-"*70)

    results = {}

    # SHORT-TERM MEMORY (2-hour TTL)
    if verbose:
        print("\nShort-Term Memory (session context):")

    short_term = db_instance["short_term_memory"]
    stm_indexes = []

    indexes = [
        IndexModel([("session_id", ASCENDING)], name="idx_session_id"),
        IndexModel([("agent", ASCENDING)], name="idx_agent"),
        IndexModel([("memory_type", ASCENDING)], name="idx_memory_type"),
        IndexModel([("expires_at", ASCENDING)], name="idx_expires_at", expireAfterSeconds=0),  # TTL

        # Compound indexes
        IndexModel([("session_id", ASCENDING), ("memory_type", ASCENDING)], name="idx_session_memory_type"),
        IndexModel([("session_id", ASCENDING), ("agent", ASCENDING)], name="idx_session_agent"),
    ]

    try:
        result = short_term.create_indexes(indexes)
        stm_indexes.extend(result)
        if verbose:
            print(f"  ✓ Created {len(result)} indexes (includes TTL for auto-expiration)")
    except OperationFailure as e:
        if verbose:
            print(f"  ✗ Error: {e}")

    results["short_term_memory"] = stm_indexes

    # LONG-TERM MEMORY (persistent)
    if verbose:
        print("\nLong-Term Memory (persistent):")

    long_term = db_instance["long_term_memory"]
    ltm_indexes = []

    indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id"),
        IndexModel([("memory_type", ASCENDING)], name="idx_memory_type"),
        IndexModel([("timestamp", DESCENDING)], name="idx_timestamp"),

        # Episodic memory indexes
        IndexModel([("action_type", ASCENDING)], name="idx_action_type"),
        IndexModel([("source_agent", ASCENDING)], name="idx_source_agent"),

        # Semantic memory indexes
        IndexModel([("semantic_type", ASCENDING)], name="idx_semantic_type"),
        IndexModel([("key", ASCENDING)], name="idx_key"),

        # Procedural memory indexes
        IndexModel([("rule_type", ASCENDING)], name="idx_rule_type"),
        IndexModel([("trigger_pattern", ASCENDING)], name="idx_trigger_pattern"),

        # Compound indexes
        IndexModel([("user_id", ASCENDING), ("memory_type", ASCENDING)], name="idx_user_memory_type"),
        IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="idx_user_timestamp"),
        IndexModel([("user_id", ASCENDING), ("action_type", ASCENDING)], name="idx_user_action_type"),
        IndexModel([("user_id", ASCENDING), ("source_agent", ASCENDING)], name="idx_user_source_agent"),
        IndexModel([
            ("user_id", ASCENDING),
            ("memory_type", ASCENDING),
            ("semantic_type", ASCENDING),
            ("key", ASCENDING)
        ], name="idx_semantic_lookup"),
        IndexModel([
            ("user_id", ASCENDING),
            ("memory_type", ASCENDING),
            ("trigger_pattern", ASCENDING)
        ], name="idx_procedural_lookup"),
    ]

    try:
        result = long_term.create_indexes(indexes)
        ltm_indexes.extend(result)
        if verbose:
            print(f"  ✓ Created {len(result)} indexes")
    except OperationFailure as e:
        if verbose:
            print(f"  ✗ Error: {e}")

    results["long_term_memory"] = ltm_indexes

    # SHARED MEMORY (5-minute TTL)
    if verbose:
        print("\nShared Memory (agent handoffs):")

    shared = db_instance["shared_memory"]
    sm_indexes = []

    indexes = [
        IndexModel([("session_id", ASCENDING)], name="idx_session_id"),
        IndexModel([("from_agent", ASCENDING)], name="idx_from_agent"),
        IndexModel([("to_agent", ASCENDING)], name="idx_to_agent"),
        IndexModel([("status", ASCENDING)], name="idx_status"),
        IndexModel([("handoff_id", ASCENDING)], name="idx_handoff_id", unique=True),
        IndexModel([("chain_id", ASCENDING)], name="idx_chain_id"),
        IndexModel([("expires_at", ASCENDING)], name="idx_expires_at", expireAfterSeconds=0),  # TTL

        # Compound indexes
        IndexModel([
            ("session_id", ASCENDING),
            ("to_agent", ASCENDING),
            ("status", ASCENDING)
        ], name="idx_session_target_status"),
    ]

    try:
        result = shared.create_indexes(indexes)
        sm_indexes.extend(result)
        if verbose:
            print(f"  ✓ Created {len(result)} indexes (includes TTL for auto-expiration)")
    except OperationFailure as e:
        if verbose:
            print(f"  ✗ Error: {e}")

    results["shared_memory"] = sm_indexes

    return results

# =============================================================================
# INDEX CREATION - TOOL DISCOVERIES
# =============================================================================

def create_tool_discoveries_indexes(db_instance, verbose: bool = True) -> List[str]:
    """Create indexes for tool_discoveries collection (MCP Agent)."""

    if verbose:
        print("\n" + "-"*70)
        print("🔌 TOOL DISCOVERIES COLLECTION INDEXES (MCP Agent)")
        print("-"*70)

    tool_discoveries = db_instance["tool_discoveries"]
    created_indexes = []

    indexes = [
        IndexModel([("user_id", ASCENDING)], name="idx_user_id"),
        IndexModel([("times_used", DESCENDING)], name="idx_times_used"),
        IndexModel([("success", ASCENDING)], name="idx_success"),
        IndexModel([("promoted_to_static", ASCENDING)], name="idx_promoted"),
        IndexModel([("timestamp", DESCENDING)], name="idx_timestamp"),

        # Compound indexes
        IndexModel([
            ("promoted_to_static", ASCENDING),
            ("times_used", DESCENDING)
        ], name="idx_unpromoted_popular"),

        IndexModel([
            ("solution.mcp_server", ASCENDING),
            ("solution.tool_used", ASCENDING)
        ], name="idx_server_tool"),

        IndexModel([
            ("user_id", ASCENDING),
            ("promoted_to_static", ASCENDING),
            ("times_used", DESCENDING)
        ], name="idx_user_unpromoted_popular"),
    ]

    try:
        result = tool_discoveries.create_indexes(indexes)
        created_indexes.extend(result)
        if verbose:
            print(f"✓ Created {len(result)} indexes for tool usage learning")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating tool discovery indexes: {e}")

    return created_indexes

# =============================================================================
# INDEX CREATION - EVALUATIONS
# =============================================================================

def create_eval_indexes(db_instance, verbose: bool = True) -> List[str]:
    """Create indexes for eval_comparison_runs collection."""

    if verbose:
        print("\n" + "-"*70)
        print("📊 EVALUATION COLLECTION INDEXES")
        print("-"*70)

    eval_runs = db_instance["eval_comparison_runs"]
    created_indexes = []

    indexes = [
        IndexModel([("timestamp", DESCENDING)], name="idx_timestamp"),
        IndexModel([("run_name", ASCENDING)], name="idx_run_name"),
    ]

    try:
        result = eval_runs.create_indexes(indexes)
        created_indexes.extend(result)
        if verbose:
            print(f"✓ Created {len(result)} indexes")
    except OperationFailure as e:
        if verbose:
            print(f"✗ Error creating eval indexes: {e}")

    return created_indexes

# =============================================================================
# VECTOR SEARCH INDEX INSTRUCTIONS
# =============================================================================

def print_vector_index_instructions():
    """Print instructions for creating vector search indexes in Atlas."""

    print("\n" + "="*70)
    print("⚠️  MANUAL SETUP REQUIRED: VECTOR SEARCH INDEXES")
    print("="*70)

    print("\nVector search indexes CANNOT be created via PyMongo.")
    print("You must create them manually in the MongoDB Atlas UI.")

    print("\n📋 STEPS:")
    print("1. Go to your MongoDB Atlas cluster")
    print("2. Navigate to: Database → Search → Create Search Index")
    print("3. Choose 'JSON Editor'")
    print("4. Create the following 4 indexes:")

    print("\n" + "-"*70)
    print("1. TASKS - vector_index")
    print("-"*70)
    print("""
Database: {database}
Collection: tasks
Index Name: vector_index

{
  "fields": [
    {
      "path": "embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
""".replace("{database}", settings.mongodb_database))

    print("-"*70)
    print("2. PROJECTS - vector_index")
    print("-"*70)
    print("""
Database: {database}
Collection: projects
Index Name: vector_index

{
  "fields": [
    {
      "path": "embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
""".replace("{database}", settings.mongodb_database))

    print("-"*70)
    print("3. LONG-TERM MEMORY - memory_embeddings")
    print("-"*70)
    print("""
Database: {database}
Collection: long_term_memory
Index Name: memory_embeddings

{
  "fields": [
    {
      "path": "embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
""".replace("{database}", settings.mongodb_database))

    print("-"*70)
    print("4. LONG-TERM MEMORY - vector_index (alternative name)")
    print("-"*70)
    print("""
Database: {database}
Collection: long_term_memory
Index Name: vector_index

{
  "fields": [
    {
      "path": "embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
""".replace("{database}", settings.mongodb_database))

    print("-"*70)
    print("5. TOOL DISCOVERIES - discovery_vector_index")
    print("-"*70)
    print("""
Database: {database}
Collection: tool_discoveries
Index Name: discovery_vector_index

{
  "fields": [
    {
      "path": "request_embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
""".replace("{database}", settings.mongodb_database))

    print("-"*70)
    print("\n⚠️  IMPORTANT:")
    print("  - Index names MUST match exactly (case-sensitive)")
    print("  - numDimensions: 1024 (Voyage AI voyage-3 model)")
    print("  - similarity: cosine (optimal for text embeddings)")
    print("  - Index creation may take several minutes")
    print("  - You can verify indexes in Atlas UI: Search → Search Indexes")

    print("\n💡 TIP:")
    print("  Run 'python scripts/verify_setup.py' after creating indexes")
    print("  to verify everything is working correctly.")

# =============================================================================
# CHECK EXISTING SETUP
# =============================================================================

def check_existing_setup(db_instance):
    """Check what collections and indexes already exist."""

    print("\n" + "="*70)
    print("EXISTING DATABASE SETUP")
    print("="*70)

    existing_collections = set(db_instance.list_collection_names())

    print("\n📦 Collections:")
    for collection_name, description in COLLECTIONS.items():
        exists = collection_name in existing_collections
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {status}: {collection_name}")

        if exists:
            # Show index count
            index_count = len(list(db_instance[collection_name].list_indexes()))
            doc_count = db_instance[collection_name].count_documents({})
            print(f"           → {index_count} indexes, {doc_count} documents")

    print(f"\n📊 Summary: {len(existing_collections & COLLECTIONS.keys())}/{len(COLLECTIONS)} collections exist")

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Initialize MongoDB database for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--collections-only",
        action="store_true",
        help="Only create collections, skip indexes"
    )

    parser.add_argument(
        "--indexes-only",
        action="store_true",
        help="Only create indexes, skip collection creation"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check existing setup without making changes"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate collections (DANGEROUS: will drop existing data!)"
    )

    parser.add_argument(
        "--vector-instructions",
        action="store_true",
        help="Show vector index creation instructions only"
    )

    args = parser.parse_args()

    # Show vector instructions only
    if args.vector_instructions:
        print_vector_index_instructions()
        return 0

    # Connect to MongoDB
    try:
        print("\n" + "="*70)
        print("FLOW COMPANION - DATABASE INITIALIZATION")
        print("="*70)
        print(f"\n📡 Connecting to MongoDB...")
        print(f"   Database: {settings.mongodb_database}")

        mongodb = MongoDB()
        db = mongodb.get_database()

        print(f"✓ Connected successfully")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return 1

    # Check existing setup only
    if args.check:
        check_existing_setup(db)
        return 0

    # Confirm force operation
    if args.force:
        print("\n⚠️  WARNING: --force will DROP and RECREATE collections!")
        print("   All existing data will be LOST!")
        response = input("\nContinue? (type 'yes' to confirm): ").strip().lower()
        if response != "yes":
            print("❌ Aborted")
            return 1

    try:
        # Create collections
        if not args.indexes_only:
            create_collections(db, force=args.force)

        # Create indexes
        if not args.collections_only:
            print("\n" + "="*70)
            print("CREATING INDEXES")
            print("="*70)

            create_tasks_indexes(db)
            create_projects_indexes(db)
            create_settings_indexes(db)
            create_memory_indexes(db)
            create_tool_discoveries_indexes(db)
            create_eval_indexes(db)

        # Show vector index instructions
        if not args.collections_only and not args.indexes_only:
            print_vector_index_instructions()

        # Final summary
        print("\n" + "="*70)
        print("✅ DATABASE INITIALIZATION COMPLETE")
        print("="*70)

        if not args.indexes_only:
            print(f"\n✓ All {len(COLLECTIONS)} collections ready")
        if not args.collections_only:
            print("✓ All standard, text search, and TTL indexes created")

        print("\n📋 Next steps:")
        if not args.collections_only and not args.indexes_only:
            print("  1. Create vector search indexes in Atlas UI (see instructions above)")
            print("  2. Run: python scripts/verify_setup.py")
            print("  3. Run: python scripts/seed_demo_data.py (optional)")
            print("  4. Run: streamlit run streamlit_app.py")
        elif args.collections_only:
            print("  1. Run: python scripts/init_db.py --indexes-only")
        elif args.indexes_only:
            print("  1. Create vector search indexes in Atlas UI")
            print("  2. Run: python scripts/verify_setup.py")

        return 0

    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
