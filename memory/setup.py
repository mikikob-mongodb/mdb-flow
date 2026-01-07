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
    if "short_term_memory" not in db.list_collection_names():
        db.create_collection("short_term_memory")

    safe_create_index(db.short_term_memory, "session_id")
    safe_create_index(db.short_term_memory, "agent")
    safe_create_index(db.short_term_memory, "expires_at", expireAfterSeconds=0)  # TTL index

    # ========== Long-term memory - persistent, no TTL ==========
    if "long_term_memory" not in db.list_collection_names():
        db.create_collection("long_term_memory")

    safe_create_index(db.long_term_memory, "user_id")
    safe_create_index(db.long_term_memory, "type")

    # Note: Vector search index (memory_embeddings) must be created manually in Atlas UI
    # This 2dsphere index is for geospatial queries
    try:
        safe_create_index(db.long_term_memory, [("embedding", "2dsphere")])  # For vector search
    except Exception:
        # 2dsphere index may fail for high-dimensional vectors
        # Vector search index must be created in Atlas UI instead
        pass

    # ========== Shared memory - agent handoff, expires after 5 minutes ==========
    if "shared_memory" not in db.list_collection_names():
        db.create_collection("shared_memory")

    safe_create_index(db.shared_memory, "session_id")
    safe_create_index(db.shared_memory, "from_agent")
    safe_create_index(db.shared_memory, "to_agent")
    safe_create_index(db.shared_memory, "status")
    safe_create_index(db.shared_memory, "expires_at", expireAfterSeconds=0)  # TTL index

    print("✅ Memory collections created")
