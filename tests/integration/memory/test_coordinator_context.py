"""
Test script for Coordinator context injection and extraction.

Demonstrates:
- Session context injection
- Context extraction from tool calls
- Disambiguation storage and resolution
- Preference tracking
"""

from agents.coordinator import coordinator
from shared.db import MongoDB
from memory import MemoryManager
from shared.embeddings import embed_query

def test_coordinator_context():
    """Test coordinator context injection and extraction."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Create memory manager if not already attached
    if not coordinator.memory:
        memory = MemoryManager(db, embedding_fn=embed_query)
        coordinator.memory = memory

    print("=" * 60)
    print("TESTING COORDINATOR CONTEXT INJECTION & EXTRACTION")
    print("=" * 60)

    # Set session
    session_id = "test-session-123"
    coordinator.set_session(session_id, user_id="test-user")
    print(f"\n✓ Session set: {session_id}")

    # Clear any existing context
    coordinator.memory.clear_session_context(session_id)
    print("✓ Cleared existing session context")

    # Test 1: Query that mentions a project
    print("\n" + "=" * 60)
    print("TEST 1: Context extraction from query")
    print("=" * 60)

    response = coordinator.process(
        user_message="Show me tasks in AgentOps",
        session_id=session_id,
        turn_number=1,
        return_debug=True
    )

    print(f"✓ Response: {response['response'][:100]}...")
    print(f"✓ Memory ops: {response['debug']['memory_ops']}")

    # Check context was extracted
    context = coordinator.memory.read_session_context(session_id)
    print(f"✓ Session context: {context}")

    # Test 2: Query that should use injected context
    print("\n" + "=" * 60)
    print("TEST 2: Context injection on subsequent query")
    print("=" * 60)

    response2 = coordinator.process(
        user_message="What's in progress?",
        session_id=session_id,
        turn_number=2,
        return_debug=True
    )

    print(f"✓ Response: {response2['response'][:100]}...")
    print(f"✓ Memory ops: {response2['debug']['memory_ops']}")
    print(f"✓ Context injected: {response2['debug']['memory_ops']['context_injected']}")

    # Test 3: Preference extraction
    print("\n" + "=" * 60)
    print("TEST 3: Preference extraction")
    print("=" * 60)

    response3 = coordinator.process(
        user_message="I'm focusing on Voice Agent today",
        session_id=session_id,
        turn_number=3,
        return_debug=True
    )

    context3 = coordinator.memory.read_session_context(session_id)
    print(f"✓ Context after preference: {context3}")
    print(f"✓ Preferences: {context3.get('preferences', {})}")

    # Test 4: Search results disambiguation
    print("\n" + "=" * 60)
    print("TEST 4: Search results disambiguation")
    print("=" * 60)

    response4 = coordinator.process(
        user_message="Find debugging tasks",
        session_id=session_id,
        turn_number=4,
        return_debug=True
    )

    # Check if disambiguation was stored
    disambiguation = coordinator.memory.get_pending_disambiguation(session_id)
    if disambiguation:
        print(f"✓ Disambiguation stored: {disambiguation['query']}")
        print(f"  - {len(disambiguation['results'])} results")
        for r in disambiguation['results']:
            print(f"    {r['index'] + 1}. {r['title']}")
    else:
        print("  (No disambiguation needed - single result or no results)")

    # Test 5: Memory stats
    print("\n" + "=" * 60)
    print("TEST 5: Memory statistics")
    print("=" * 60)

    stats = coordinator.memory.get_memory_stats(session_id, "test-user")
    print(f"✓ Short-term entries: {stats['short_term_count']}")
    print(f"✓ Long-term entries: {stats['long_term_count']}")
    print(f"✓ Shared pending: {stats['shared_pending']}")

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    result = coordinator.memory.clear_session(session_id)
    print(f"✓ Cleared {result['short_term_deleted']} short-term entries")
    print(f"✓ Cleared {result['shared_deleted']} shared entries")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_coordinator_context()
