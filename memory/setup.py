"""Setup memory collections and indexes."""

from pymongo.database import Database
from pymongo import errors


def setup_memory_collections(db: Database):
    """Create memory collections with appropriate indexes.

    Args:
        db: MongoDB database instance
    """

    # Helper function to safely create index
    def safe_create_index(collection, keys, **kwargs):
        try:
            collection.create_index(keys, **kwargs)
        except errors.OperationFailure as e:
            if "already exists" not in str(e).lower():
                raise

    # ========== Short-term memory - session context, expires after 2 hours ==========
    if "memory_short_term" not in db.list_collection_names():
        db.create_collection("memory_short_term")

    safe_create_index(db.memory_short_term, "session_id")
    safe_create_index(db.memory_short_term, "agent")
    safe_create_index(db.memory_short_term, "expires_at", expireAfterSeconds=0)  # TTL index

    # ========== Long-term memory - persistent, no TTL ==========
    if "memory_long_term" not in db.list_collection_names():
        db.create_collection("memory_long_term")

    safe_create_index(db.memory_long_term, "user_id")
    safe_create_index(db.memory_long_term, "type")

    # Note: Vector search index (memory_embeddings) must be created manually in Atlas UI
    # This 2dsphere index is for geospatial queries
    try:
        safe_create_index(db.memory_long_term, [("embedding", "2dsphere")])  # For vector search
    except Exception:
        # 2dsphere index may fail for high-dimensional vectors
        # Vector search index must be created in Atlas UI instead
        pass

    # ========== Shared memory - agent handoff, expires after 5 minutes ==========
    if "memory_shared" not in db.list_collection_names():
        db.create_collection("memory_shared")

    safe_create_index(db.memory_shared, "session_id")
    safe_create_index(db.memory_shared, "from_agent")
    safe_create_index(db.memory_shared, "to_agent")
    safe_create_index(db.memory_shared, "status")
    safe_create_index(db.memory_shared, "expires_at", expireAfterSeconds=0)  # TTL index

    print("✅ Memory collections created")
