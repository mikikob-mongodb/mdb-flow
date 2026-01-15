#!/usr/bin/env python3
"""
Database Initialization Script for Flow Companion.

Creates all MongoDB collections and indexes required for the application.
Reviews the codebase to ensure all collections and indexes are properly set up.

Usage:
    python scripts/init_db.py              # Create collections + indexes
    python scripts/init_db.py --drop-first # Drop collections and recreate (requires --force)
    python scripts/init_db.py --verify     # Just check what exists, don't create anything
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure, CollectionInvalid
from shared.db import MongoDB
from shared.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# COLLECTION AND INDEX DEFINITIONS
# Based on comprehensive codebase review
# =============================================================================

COLLECTIONS = {
    # Main application collections
    "tasks": "User tasks with activity logging",
    "projects": "User projects with activity tracking",

    # Memory system collections
    "memory_episodic": "Immutable event log of actions and events",
    "memory_semantic": "Knowledge cache and user preferences",
    "memory_procedural": "Templates, workflows, and rules",

    # MCP Agent collections
    "tool_discoveries": "MCP tool usage learning and reuse",
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_collections(db, verify_only: bool = False) -> Dict[str, str]:
    """Create all required collections."""
    results = {}
    existing = set(db.list_collection_names())

    for collection_name in COLLECTIONS.keys():
        if collection_name in existing:
            results[collection_name] = "exists"
        else:
            if not verify_only:
                try:
                    db.create_collection(collection_name)
                    results[collection_name] = "created"
                except CollectionInvalid:
                    results[collection_name] = "exists"
            else:
                results[collection_name] = "missing"

    return results

def create_tasks_indexes(db, verify_only: bool = False) -> List[str]:
    """Create indexes for tasks collection."""
    tasks = db["tasks"]
    created = []

    indexes = [
        # Standard indexes
        IndexModel([("user_id", ASCENDING)], name="user_id_1"),
        IndexModel([("project_id", ASCENDING)], name="project_id_1"),
        # Note: status_1 and priority_1 removed in Phase 2 cleanup (low cardinality, covered by compounds)
        # IndexModel([("status", ASCENDING)], name="status_1"),
        # IndexModel([("priority", ASCENDING)], name="priority_1"),
        IndexModel([("created_at", DESCENDING)], name="created_at_-1"),
        IndexModel([("last_worked_on", DESCENDING)], name="last_worked_on_-1"),
        IndexModel([("activity_log.timestamp", DESCENDING)], name="activity_log.timestamp_-1"),

        # Compound indexes for common queries
        IndexModel([("user_id", ASCENDING), ("project_id", ASCENDING)], name="user_id_1_project_id_1"),
        IndexModel([("project_id", ASCENDING), ("status", ASCENDING)], name="project_id_1_status_1"),
        IndexModel([("status", ASCENDING), ("priority", ASCENDING)], name="status_1_priority_1"),
        IndexModel([("user_id", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING)], name="user_id_1_status_1_priority_1"),
    ]

    if not verify_only:
        try:
            result = tasks.create_indexes(indexes)
            created.extend(result)
        except OperationFailure:
            pass

    # Text search index
    if not verify_only:
        try:
            tasks.create_index(
                [("title", TEXT), ("context", TEXT), ("notes", TEXT)],
                name="title_text_context_text_notes_text",
                weights={"title": 10, "context": 5, "notes": 2}
            )
            created.append("title_text_context_text_notes_text")
        except OperationFailure:
            pass

    return created

def create_projects_indexes(db, verify_only: bool = False) -> List[str]:
    """Create indexes for projects collection."""
    projects = db["projects"]
    created = []

    indexes = [
        IndexModel([("user_id", ASCENDING)], name="user_id_1"),
        # Note: status_1 removed in Phase 2 cleanup (low cardinality, covered by user_id_1_status_1)
        # IndexModel([("status", ASCENDING)], name="status_1"),
        IndexModel([("created_at", DESCENDING)], name="created_at_-1"),
        IndexModel([("last_activity", DESCENDING)], name="last_activity_-1"),
        IndexModel([("user_id", ASCENDING), ("status", ASCENDING)], name="user_id_1_status_1"),
        IndexModel([("user_id", ASCENDING), ("last_activity", DESCENDING)], name="user_id_1_last_activity_-1"),
    ]

    if not verify_only:
        try:
            result = projects.create_indexes(indexes)
            created.extend(result)
        except OperationFailure:
            pass

    # Text search index
    if not verify_only:
        try:
            projects.create_index(
                [("name", TEXT), ("description", TEXT), ("context", TEXT), ("notes", TEXT), ("methods", TEXT), ("decisions", TEXT)],
                name="name_text",
                weights={"name": 10, "description": 7, "context": 5, "decisions": 4, "methods": 3, "notes": 2}
            )
            created.append("name_text")
        except OperationFailure:
            pass

    return created

def create_memory_indexes(db, verify_only: bool = False) -> Dict[str, List[str]]:
    """Create indexes for all memory collections.

    New structure:
    - memory_episodic: Actions and events (immutable event log)
    - memory_semantic: Knowledge cache and preferences (long-term)
    - memory_procedural: Templates and workflows (unchanged)
    - Working memory: In-memory only (session context, handoffs, disambiguation)
    """
    results = {}

    # EPISODIC MEMORY (Actions and Events)
    episodic = db["memory_episodic"]
    episodic_created = []

    episodic_indexes = [
        # Primary query patterns
        IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="user_id_1_timestamp_-1"),
        IndexModel([("user_id", ASCENDING), ("action_type", ASCENDING)], name="user_id_1_action_type_1"),
        IndexModel([("user_id", ASCENDING), ("entity_type", ASCENDING)], name="user_id_1_entity_type_1"),
        IndexModel([("user_id", ASCENDING), ("source_agent", ASCENDING)], name="user_id_1_source_agent_1"),
        IndexModel([("session_id", ASCENDING), ("timestamp", DESCENDING)], name="session_id_1_timestamp_-1"),

        # For handoff tracking
        IndexModel([("handoff_id", ASCENDING)], name="handoff_id_1"),
    ]

    if not verify_only:
        try:
            result = episodic.create_indexes(episodic_indexes)
            episodic_created.extend(result)
        except OperationFailure:
            pass

    results["memory_episodic"] = episodic_created

    # SEMANTIC MEMORY (Knowledge Cache and Preferences)
    semantic = db["memory_semantic"]
    semantic_created = []

    semantic_indexes = [
        # Primary query patterns
        IndexModel([("user_id", ASCENDING), ("semantic_type", ASCENDING), ("key", ASCENDING)], name="semantic_lookup"),
        IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="user_id_1_timestamp_-1"),
        IndexModel([("semantic_type", ASCENDING)], name="semantic_type_1"),

        # For knowledge cache queries
        IndexModel([("user_id", ASCENDING), ("semantic_type", ASCENDING), ("query", ASCENDING)], name="knowledge_query"),
        IndexModel([("user_id", ASCENDING), ("semantic_type", ASCENDING), ("created_at", DESCENDING)], name="knowledge_recency"),
    ]

    if not verify_only:
        try:
            result = semantic.create_indexes(semantic_indexes)
            semantic_created.extend(result)
        except OperationFailure:
            pass

    results["memory_semantic"] = semantic_created

    # PROCEDURAL MEMORY (Templates and Workflows)
    procedural = db["memory_procedural"]
    procedural_created = []

    procedural_indexes = [
        IndexModel([("user_id", ASCENDING), ("rule_type", ASCENDING)], name="user_id_1_rule_type_1"),
        IndexModel([("user_id", ASCENDING), ("name", ASCENDING)], name="user_id_1_name_1"),
        IndexModel([("user_id", ASCENDING), ("trigger_pattern", ASCENDING)], name="procedural_lookup"),
    ]

    if not verify_only:
        try:
            result = procedural.create_indexes(procedural_indexes)
            procedural_created.extend(result)
        except OperationFailure:
            pass

    results["memory_procedural"] = procedural_created

    return results

def create_tool_discoveries_indexes(db, verify_only: bool = False) -> List[str]:
    """Create indexes for tool_discoveries collection."""
    tool_discoveries = db["tool_discoveries"]
    created = []

    indexes = [
        IndexModel([("user_id", ASCENDING)], name="user_id_1"),
        IndexModel([("times_used", DESCENDING)], name="times_used_-1"),
        IndexModel([("success", ASCENDING)], name="success_1"),
        IndexModel([("promoted_to_static", ASCENDING)], name="promoted_to_static_1"),
        IndexModel([("timestamp", DESCENDING)], name="timestamp_-1"),
        IndexModel([("promoted_to_static", ASCENDING), ("times_used", DESCENDING)], name="promoted_to_static_1_times_used_-1"),
        IndexModel([("solution.mcp_server", ASCENDING), ("solution.tool_used", ASCENDING)], name="mcp_server_1_tool_used_1"),
        IndexModel([("user_id", ASCENDING), ("promoted_to_static", ASCENDING), ("times_used", DESCENDING)], name="user_unpromoted_popular"),
    ]

    if not verify_only:
        try:
            result = tool_discoveries.create_indexes(indexes)
            created.extend(result)
        except OperationFailure:
            pass

    return created

def get_existing_indexes(db) -> Dict[str, Set[str]]:
    """Get all existing indexes for each collection."""
    existing = {}

    for collection_name in COLLECTIONS.keys():
        if collection_name in db.list_collection_names():
            indexes = db[collection_name].list_indexes()
            existing[collection_name] = {idx["name"] for idx in indexes if idx["name"] != "_id_"}

    return existing

def create_text_search_indexes(db, verify_only: bool = False) -> Dict[str, str]:
    """
    Create Atlas Search text indexes for keyword/hybrid search.

    Text indexes enable $search operator for keyword matching and hybrid search.

    Returns:
        Dict mapping index names to status (created, exists, failed, skipped)
    """
    results = {}

    # Text index definitions for hybrid search
    text_indexes = {
        "tasks_text_index": {
            "collection": "tasks",
            "definition": {
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        "title": {"type": "string"},
                        "context": {"type": "string"},
                        "notes": {"type": "string"}
                    }
                }
            }
        },
        "projects_text_index": {
            "collection": "projects",
            "definition": {
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        },
        "semantic_text_index": {
            "collection": "memory_semantic",
            "definition": {
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        "query": {"type": "string"},
                        "result": {"type": "string"}
                    }
                }
            }
        }
    }

    if verify_only:
        for index_name in text_indexes.keys():
            results[index_name] = "verify_mode"
        return results

    for index_name, index_config in text_indexes.items():
        collection_name = index_config["collection"]
        try:
            collection = db[collection_name]

            # Check if search index already exists
            try:
                existing_search_indexes = list(collection.list_search_indexes())
                if any(idx.get("name") == index_name for idx in existing_search_indexes):
                    results[index_name] = "exists"
                    continue
            except Exception:
                pass

            # Attempt to create text search index
            try:
                if hasattr(collection, 'create_search_index'):
                    collection.create_search_index({
                        "definition": index_config["definition"],
                        "name": index_name
                    })
                    results[index_name] = "created"
                else:
                    results[index_name] = "api_unavailable"
            except Exception as create_error:
                if "already exists" in str(create_error).lower():
                    results[index_name] = "exists"
                else:
                    logger.debug(f"    Failed to create {index_name}: {create_error}")
                    results[index_name] = "failed"

        except Exception as e:
            logger.debug(f"    Error processing {index_name}: {e}")
            results[index_name] = "error"

    return results

def create_vector_indexes(db, verify_only: bool = False) -> Dict[str, str]:
    """
    Create Atlas Search vector indexes for semantic search.

    Attempts to create vector indexes programmatically using MongoDB Atlas Search API.
    Falls back to manual instructions if automatic creation fails.

    Returns:
        Dict mapping collection names to status (created, exists, failed, skipped)
    """
    results = {}

    # Vector index definitions: collection -> (field, index_name, description)
    # Note: Index name must match retrieval.py expectations ("vector_index")
    vector_indexes = {
        "tasks": ("embedding", "vector_index", "Task semantic search"),
        "projects": ("embedding", "vector_index", "Project semantic search"),
        "memory_episodic": ("embedding", "vector_index", "Episodic memory semantic search"),
        "memory_semantic": ("embedding", "vector_index", "Semantic memory search"),
        "tool_discoveries": ("request_embedding", "vector_index", "Tool discovery semantic search"),
    }

    if verify_only:
        # In verify mode, just check if collections exist
        for collection_name in vector_indexes.keys():
            if collection_name in db.list_collection_names():
                results[collection_name] = "exists (verify mode)"
            else:
                results[collection_name] = "missing"
        return results

    for collection_name, (field_name, index_name, description) in vector_indexes.items():
        try:
            collection = db[collection_name]

            # Check if search index already exists
            try:
                existing_search_indexes = list(collection.list_search_indexes())
                if any(idx.get("name") == index_name for idx in existing_search_indexes):
                    results[collection_name] = "exists"
                    continue
            except Exception:
                # list_search_indexes might not be available in all pymongo versions
                pass

            # Attempt to create vector search index
            # Note: This requires MongoDB Atlas and pymongo >= 4.5
            # Vector index with filter fields for common query patterns
            vector_index_definition = {
                "fields": [
                    {
                        "path": field_name,
                        "type": "vector",
                        "numDimensions": 1024,  # Voyage AI embeddings
                        "similarity": "cosine"
                    },
                    {
                        "path": "user_id",
                        "type": "filter"
                    },
                    {
                        "path": "memory_type",
                        "type": "filter"
                    },
                    {
                        "path": "semantic_type",
                        "type": "filter"
                    },
                    {
                        "path": "status",
                        "type": "filter"
                    }
                ]
            }

            try:
                # Use SearchIndexModel for vector indexes (pymongo >= 4.5)
                # This is the correct approach for vectorSearch type indexes
                try:
                    from pymongo.operations import SearchIndexModel

                    model = SearchIndexModel(
                        definition=vector_index_definition,
                        name=index_name,
                        type="vectorSearch"
                    )

                    collection.create_search_indexes([model])
                    results[collection_name] = "created"

                except ImportError:
                    # Fallback for older pymongo versions
                    if hasattr(collection, 'create_search_index'):
                        collection.create_search_index(
                            {"definition": vector_index_definition, "name": index_name}
                        )
                        results[collection_name] = "created"
                    else:
                        results[collection_name] = "api_unavailable"

            except Exception as create_error:
                # Check if it's a "already exists" error
                if "already exists" in str(create_error).lower():
                    results[collection_name] = "exists"
                else:
                    # Log the specific error for debugging
                    logger.debug(f"    Failed to create {collection_name}.{index_name}: {create_error}")
                    results[collection_name] = "failed"

        except Exception as e:
            logger.debug(f"    Error processing {collection_name}: {e}")
            results[collection_name] = "error"

    return results

def print_vector_index_warning():
    """Print warning about vector indexes that need manual creation."""
    logger.info("")
    logger.info("⚠️  Vector indexes may need manual creation in Atlas UI")
    logger.info("")
    logger.info("The following vector indexes should be created manually in MongoDB Atlas:")
    logger.info("  1. tasks.vector_index (1024 dimensions, cosine similarity)")
    logger.info("  2. projects.vector_index (1024 dimensions, cosine similarity)")
    logger.info("  3. memory_episodic.vector_index (1024 dimensions, cosine similarity)")
    logger.info("  4. memory_semantic.vector_index (1024 dimensions, cosine similarity)")
    logger.info("  5. tool_discoveries.vector_index (1024 dimensions, cosine similarity)")
    logger.info("")
    logger.info("IMPORTANT: Index name MUST be 'vector_index' to match retrieval code expectations")
    logger.info("")
    logger.info("To create these indexes:")
    logger.info("  1. Go to MongoDB Atlas → Database → Search Indexes")
    logger.info("  2. Create Search Index → JSON Editor")
    logger.info("  3. Select the collection (tasks, projects, memory_episodic, memory_semantic, or tool_discoveries)")
    logger.info("  4. Set Index Name to: vector_index")
    logger.info("  5. Use the following JSON definition:")
    logger.info("")
    logger.info('  {')
    logger.info('    "fields": [')
    logger.info('      {')
    logger.info('        "path": "embedding",')
    logger.info('        "type": "vector",')
    logger.info('        "numDimensions": 1024,')
    logger.info('        "similarity": "cosine"')
    logger.info('      }')
    logger.info('    ]')
    logger.info('  }')
    logger.info("")
    logger.info("  Note: For tool_discoveries collection, use path: 'request_embedding' instead of 'embedding'")
    logger.info("")

# =============================================================================
# MAIN LOGIC
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Initialize MongoDB database for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Drop collections and recreate (DANGEROUS - requires --force)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Confirm dangerous operations like --drop-first"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Just check what exists, don't create anything"
    )

    args = parser.parse_args()

    # Validate --drop-first requires --force
    if args.drop_first and not args.force:
        logger.error("❌ --drop-first requires --force flag for safety")
        logger.error("   This operation will DELETE all data!")
        logger.error("   Use: python scripts/init_db.py --drop-first --force")
        return 1

    # Connect to MongoDB
    try:
        logger.info("🔌 Connecting to MongoDB Atlas...")
        mongodb = MongoDB()
        db = mongodb.get_database()

        # Get connection info
        db_name = settings.mongodb_database
        # Try to get cluster name from URI
        uri_parts = settings.mongodb_uri.split('@')
        if len(uri_parts) > 1:
            cluster_info = uri_parts[1].split('/')[0]
        else:
            cluster_info = "localhost"

        logger.info(f"✅ Connected to: {cluster_info} / {db_name}")

    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("   Check your MONGODB_URI and network connection")
        return 1

    # Drop collections if requested
    if args.drop_first:
        logger.info("")
        logger.info("⚠️  DROPPING ALL COLLECTIONS...")
        for collection_name in COLLECTIONS.keys():
            if collection_name in db.list_collection_names():
                db[collection_name].drop()
                logger.info(f"  🗑️  Dropped: {collection_name}")
        logger.info("")

    # Get existing state before changes
    existing_before = get_existing_indexes(db)

    # Create collections
    logger.info("📁 Collections:")
    collection_results = create_collections(db, verify_only=args.verify)

    for name, status in collection_results.items():
        if status == "exists":
            logger.info(f"  ✅ {name} (exists)")
        elif status == "created":
            logger.info(f"  🆕 {name} (created)")
        elif status == "missing":
            logger.info(f"  ❌ {name} (missing)")

    # Create indexes
    logger.info("")
    logger.info("📇 Indexes:")

    # Tasks indexes
    logger.info("  tasks:")
    tasks_indexes = create_tasks_indexes(db, verify_only=args.verify)
    existing_tasks = existing_before.get("tasks", set())

    if not args.verify:
        # Show newly created indexes
        newly_created = [idx for idx in tasks_indexes if idx not in existing_tasks]
        if newly_created:
            for idx_name in newly_created:
                logger.info(f"    🆕 {idx_name} (created)")
        # Show existing count
        if existing_tasks:
            logger.info(f"    ✅ {len(existing_tasks)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_tasks)} indexes exist")

    # Projects indexes
    logger.info("  projects:")
    projects_indexes = create_projects_indexes(db, verify_only=args.verify)
    existing_projects = existing_before.get("projects", set())

    if not args.verify:
        newly_created = [idx for idx in projects_indexes if idx not in existing_projects]
        if newly_created:
            for idx_name in newly_created:
                logger.info(f"    🆕 {idx_name} (created)")
        if existing_projects:
            logger.info(f"    ✅ {len(existing_projects)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_projects)} indexes exist")

    # Memory indexes
    logger.info("  memory_episodic:")
    memory_results = create_memory_indexes(db, verify_only=args.verify)
    existing_episodic = existing_before.get("memory_episodic", set())

    if not args.verify:
        newly_created = [idx for idx in memory_results.get("memory_episodic", []) if idx not in existing_episodic]
        for idx_name in newly_created:
            logger.info(f"    🆕 {idx_name} (created)")
        if existing_episodic:
            logger.info(f"    ✅ {len(existing_episodic)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_episodic)} indexes exist")

    logger.info("  memory_semantic:")
    existing_semantic = existing_before.get("memory_semantic", set())

    if not args.verify:
        newly_created = [idx for idx in memory_results.get("memory_semantic", []) if idx not in existing_semantic]
        if newly_created:
            for idx_name in newly_created:
                logger.info(f"    🆕 {idx_name} (created)")
        if existing_semantic:
            logger.info(f"    ✅ {len(existing_semantic)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_semantic)} indexes exist")

    logger.info("  memory_procedural:")
    existing_procedural = existing_before.get("memory_procedural", set())

    if not args.verify:
        newly_created = [idx for idx in memory_results.get("memory_procedural", []) if idx not in existing_procedural]
        if newly_created:
            for idx_name in newly_created:
                logger.info(f"    🆕 {idx_name} (created)")
        if existing_procedural:
            logger.info(f"    ✅ {len(existing_procedural)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_procedural)} indexes exist")

    # Tool discoveries indexes
    logger.info("  tool_discoveries:")
    tool_indexes = create_tool_discoveries_indexes(db, verify_only=args.verify)
    existing_tool = existing_before.get("tool_discoveries", set())

    if not args.verify:
        newly_created = [idx for idx in tool_indexes if idx not in existing_tool]
        if newly_created:
            for idx_name in newly_created:
                logger.info(f"    🆕 {idx_name} (created)")
        if existing_tool:
            logger.info(f"    ✅ {len(existing_tool)} indexes already exist")
    else:
        logger.info(f"    ✅ {len(existing_tool)} indexes exist")

    # Vector search indexes (Atlas Search)
    logger.info("")
    logger.info("🔍 Vector Search Indexes (Atlas Search):")
    vector_results = create_vector_indexes(db, verify_only=args.verify)

    for collection_name, status in vector_results.items():
        if status == "created":
            logger.info(f"  🆕 {collection_name}.vector_index (created, 1024-dim cosine)")
        elif status == "exists":
            logger.info(f"  ✅ {collection_name}.vector_index (exists)")
        elif status == "exists (verify mode)":
            logger.info(f"  ✅ {collection_name} (collection exists)")
        elif status == "api_unavailable":
            logger.info(f"  ⚠️  {collection_name} (pymongo API unavailable - manual creation required)")
        elif status == "failed":
            logger.info(f"  ⚠️  {collection_name} (creation failed - may require Atlas UI)")
        elif status == "error":
            logger.info(f"  ❌ {collection_name} (error during creation)")
        elif status == "missing":
            logger.info(f"  ❌ {collection_name} (collection missing)")

    # Print vector index warning if any failed or API unavailable
    need_manual_creation = any(
        status in ["failed", "api_unavailable", "error"]
        for status in vector_results.values()
    )

    if not args.verify and need_manual_creation:
        print_vector_index_warning()

    # Text search indexes (Atlas Search) for hybrid search
    logger.info("")
    logger.info("📝 Text Search Indexes (Atlas Search - for hybrid search):")
    text_results = create_text_search_indexes(db, verify_only=args.verify)

    for index_name, status in text_results.items():
        if status == "created":
            logger.info(f"  🆕 {index_name} (created)")
        elif status == "exists":
            logger.info(f"  ✅ {index_name} (exists)")
        elif status == "verify_mode":
            logger.info(f"  ℹ️  {index_name} (verify mode - cannot check search indexes)")
        elif status == "api_unavailable":
            logger.info(f"  ⚠️  {index_name} (pymongo API unavailable - manual creation required)")
        elif status == "failed":
            logger.info(f"  ⚠️  {index_name} (creation failed - may require Atlas UI)")
        elif status == "error":
            logger.info(f"  ❌ {index_name} (error during creation)")

    # Summary
    logger.info("")
    if args.verify:
        logger.info(f"✅ Verification complete! ({len(COLLECTIONS)} collections)")
    else:
        collections_created = sum(1 for v in collection_results.values() if v == "created")
        total_indexes = (len(tasks_indexes) + len(projects_indexes) +
                        len(memory_results.get("memory_episodic", [])) +
                        len(memory_results.get("memory_semantic", [])) +
                        len(memory_results.get("memory_procedural", [])) +
                        len(tool_indexes))

        if args.drop_first:
            logger.info(f"✅ Database reinitialized! ({len(COLLECTIONS)} collections, {total_indexes} indexes)")
        else:
            logger.info(f"✅ Database initialized! ({len(COLLECTIONS)} collections, {total_indexes} indexes)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
