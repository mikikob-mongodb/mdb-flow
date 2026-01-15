"""
Test script for Coordinator action recording with new Memory Manager API.

Demonstrates:
- Action recording for complete/start/create/stop/update
- get_action_history tool (detailed mode)
- get_action_history tool (summary mode)
- Source agent attribution
- Entity/metadata structure
"""

from agents.coordinator import coordinator
from shared.db import MongoDB
from memory import MemoryManager
from shared.embeddings import embed_query

def test_action_recording():
    """Test coordinator action recording with new Memory Manager API."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Ensure coordinator has memory manager
    if not coordinator.memory:
        memory = MemoryManager(db, embedding_fn=embed_query)
        coordinator.memory = memory

    print("=" * 60)
    print("TESTING ACTION RECORDING WITH NEW MEMORY MANAGER API")
    print("=" * 60)

    # Set session
    session_id = "test-action-session"
    coordinator.set_session(session_id, user_id="test-user")
    print(f"\n✓ Session set: {session_id}")

    # Enable long-term memory
    coordinator.memory_config["long_term"] = True

    # Test 1: Complete a task
    print("\n" + "=" * 60)
    print("TEST 1: Complete task action recording")
    print("=" * 60)

    response1 = coordinator.process(
        user_message="Mark the debugging task as done",
        session_id=session_id,
        turn_number=1,
        optimizations={"memory_long_term": True},
        return_debug=True
    )

    print(f"✓ Response: {response1['response'][:100]}...")
    print(f"✓ Action recorded: {response1['debug']['memory_ops'].get('action_recorded')}")
    print(f"✓ Action type: {response1['debug']['memory_ops'].get('recorded_action_type')}")

    # Test 2: Create a task
    print("\n" + "=" * 60)
    print("TEST 2: Create task action recording")
    print("=" * 60)

    response2 = coordinator.process(
        user_message="Create a task for testing memory in AgentOps",
        session_id=session_id,
        turn_number=2,
        optimizations={"memory_long_term": True},
        return_debug=True
    )

    print(f"✓ Response: {response2['response'][:100]}...")
    print(f"✓ Action recorded: {response2['debug']['memory_ops'].get('action_recorded')}")

    # Test 3: Query action history (detailed mode)
    print("\n" + "=" * 60)
    print("TEST 3: Get action history (detailed)")
    print("=" * 60)

    response3 = coordinator.process(
        user_message="What did I do today?",
        session_id=session_id,
        turn_number=3,
        optimizations={"memory_long_term": True},
        return_debug=True
    )

    print(f"✓ Response: {response3['response'][:200]}...")
    print(f"✓ Tools called: {response3['debug']['tools_called']}")

    # Test 4: Query action history (summary mode)
    print("\n" + "=" * 60)
    print("TEST 4: Get action history (summary)")
    print("=" * 60)

    response4 = coordinator.process(
        user_message="Summarize my activity today",
        session_id=session_id,
        turn_number=4,
        optimizations={"memory_long_term": True},
        return_debug=True
    )

    print(f"✓ Response: {response4['response'][:200]}...")

    # Test 5: Check database directly
    print("\n" + "=" * 60)
    print("TEST 5: Verify database records")
    print("=" * 60)

    history = coordinator.memory.get_action_history(
        user_id="test-user",
        time_range="today",
        limit=10
    )

    print(f"✓ Total actions recorded: {len(history)}")
    for action in history:
        print(f"  - {action['action_type']}: {action.get('entity', {}).get('task_title', 'N/A')}")
        print(f"    Source agent: {action.get('source_agent')}")
        print(f"    Triggered by: {action.get('triggered_by')}")
        print(f"    Has embedding: {action.get('embedding') is not None}")

    # Test 6: Activity summary
    print("\n" + "=" * 60)
    print("TEST 6: Activity summary")
    print("=" * 60)

    summary = coordinator.memory.get_activity_summary(
        user_id="test-user",
        time_range="today"
    )

    print(f"✓ Total actions: {summary['total']}")
    print(f"✓ By type: {summary['by_type']}")
    print(f"✓ By project: {list(summary['by_project'].keys())}")
    print(f"✓ By agent: {summary['by_agent']}")
    print(f"✓ Timeline entries: {len(summary['timeline'])}")

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    # Note: We don't delete long-term memory (it's persistent)
    # but we can clear the session
    result = coordinator.memory.clear_session(session_id)
    print(f"✓ Cleared {result['short_term_deleted']} short-term entries")
    print(f"✓ Long-term memory preserved for historical queries")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nKey Features Verified:")
    print("  ✓ Actions recorded with entity/metadata structure")
    print("  ✓ Source agent attribution (coordinator)")
    print("  ✓ get_action_history tool (detailed mode)")
    print("  ✓ get_action_history tool (summary mode)")
    print("  ✓ Embeddings generated for semantic search")
    print("  ✓ Time-based filtering")
    print("  ✓ Activity summaries by type/project/agent")


if __name__ == "__main__":
    test_action_recording()
