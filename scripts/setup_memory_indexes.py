"""Setup MongoDB indexes for agent memory collections.

Creates three memory collections with appropriate TTL indexes:
- short_term_memory: 2-hour TTL on expires_at field
- long_term_memory: No TTL, vector search index
- shared_memory: 5-minute TTL on expires_at field
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.setup import setup_memory_collections
from shared.db import MongoDB


def setup_memory_indexes():
    """Create indexes for memory collections."""

    print("Setting up memory collection indexes...")

    mongodb = MongoDB()
    db = mongodb.connect()

    # Use the setup function from memory package
    setup_memory_collections(db)

    print("\n✅ All memory indexes created successfully!")
    print("\nMemory Collections:")
    print("  - short_term_memory: Session context (2-hour TTL)")
    print("  - long_term_memory: Action history (persistent, with vector search)")
    print("  - shared_memory: Agent handoffs (5-minute TTL)")

    # Show index summary
    short_term = db["short_term_memory"]
    long_term = db["long_term_memory"]
    shared = db["shared_memory"]

    print("\n📊 Index Summary:")
    print(f"  short_term_memory: {len(list(short_term.list_indexes()))} indexes")
    print(f"  long_term_memory: {len(list(long_term.list_indexes()))} indexes")
    print(f"  shared_memory: {len(list(shared.list_indexes()))} indexes")


if __name__ == "__main__":
    try:
        setup_memory_indexes()
    except Exception as e:
        print(f"\n❌ Error setting up indexes: {e}")
        sys.exit(1)
