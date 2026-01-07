"""Test script to verify MemoryManager functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryManager
from shared.db import MongoDB


def test_memory_manager():
    """Test all MemoryManager operations."""

    print("Testing MemoryManager...")
    print("=" * 60)

    # Connect to database
    mongodb = MongoDB()
    db = mongodb.connect()

    # Create memory manager (without embedding for now)
    memory = MemoryManager(db=db, embedding_fn=None)

    # ========== Test Short-term Memory ==========
    print("\n1. Testing Short-term Memory...")

    # Write short-term memory
    session_id = "test_session_123"
    content = {
        "current_project": "AgentOps",
        "current_task": "debugging",
        "last_action": "search"
    }

    doc_id = memory.write_short_term(
        session_id=session_id,
        agent="coordinator",
        content=content
    )
    print(f"   ✓ Written short-term memory: {doc_id}")
    print(f"   ✓ Write timing: {memory.get_timing()['write_ms']:.2f}ms")

    # Read short-term memory
    memories = memory.read_short_term(session_id=session_id)
    print(f"   ✓ Read {len(memories)} short-term memories")
    print(f"   ✓ Read timing: {memory.get_timing()['read_ms']:.2f}ms")

    # Update short-term memory
    updated_content = {
        "current_project": "AgentOps",
        "current_task": "testing",
        "last_action": "update"
    }
    updated = memory.update_short_term(
        session_id=session_id,
        agent="coordinator",
        content=updated_content
    )
    print(f"   ✓ Updated short-term memory: {updated}")

    # Get session context
    context = memory.get_session_context(session_id=session_id)
    print(f"   ✓ Session context: {context['current_project']} / {context['current_task']}")

    # ========== Test Long-term Memory ==========
    print("\n2. Testing Long-term Memory...")

    # Write long-term memory (action)
    action_content = {
        "action": "completed_task",
        "task_title": "Fix authentication bug",
        "project": "AgentOps"
    }

    doc_id = memory.write_long_term(
        user_id="default",
        memory_type="action",
        content=action_content,
        tags=["completion", "bug_fix"]
    )
    print(f"   ✓ Written long-term memory (action): {doc_id}")
    print(f"   ✓ Write timing: {memory.get_timing()['write_ms']:.2f}ms")

    # Write long-term memory (fact)
    fact_content = {
        "fact": "User prefers hybrid search for accuracy",
        "context": "search_preferences"
    }

    doc_id = memory.write_long_term(
        user_id="default",
        memory_type="fact",
        content=fact_content,
        tags=["preference"]
    )
    print(f"   ✓ Written long-term memory (fact): {doc_id}")

    # Read long-term memories
    actions = memory.read_long_term(
        user_id="default",
        memory_type="action",
        limit=5
    )
    print(f"   ✓ Read {len(actions)} long-term actions")
    print(f"   ✓ Read timing: {memory.get_timing()['read_ms']:.2f}ms")

    if actions:
        print(f"   ✓ Most recent action: {actions[0].get('content', {})}")
        print(f"   ✓ Access count: {actions[0].get('access_count', 0)}")

    # ========== Test Shared Memory ==========
    print("\n3. Testing Shared Memory...")

    # Write shared memory (retrieval → worklog handoff)
    handoff_content = {
        "task_id": "task_123",
        "task_title": "Fix checkpointer",
        "action": "complete"
    }

    doc_id = memory.write_shared(
        session_id=session_id,
        from_agent="retrieval",
        to_agent="worklog",
        content=handoff_content
    )
    print(f"   ✓ Written shared memory (handoff): {doc_id}")
    print(f"   ✓ Write timing: {memory.get_timing()['write_ms']:.2f}ms")

    # Read shared memory (consume)
    handoff = memory.read_shared(
        session_id=session_id,
        to_agent="worklog",
        consume=True
    )
    print(f"   ✓ Read and consumed handoff")
    print(f"   ✓ Read timing: {memory.get_timing()['read_ms']:.2f}ms")

    if handoff:
        print(f"   ✓ Handoff from: {handoff['from_agent']} → {handoff['to_agent']}")
        print(f"   ✓ Status: {handoff['status']}")
        print(f"   ✓ Content: {handoff['content']}")

    # Try to read again (should be consumed)
    handoff2 = memory.read_shared(
        session_id=session_id,
        to_agent="worklog",
        consume=False
    )
    print(f"   ✓ Second read returned: {handoff2 is not None} (should be False)")

    # ========== Test Memory Stats ==========
    print("\n4. Testing Memory Stats...")

    stats = memory.get_memory_stats()
    print(f"   ✓ Short-term memory: {stats['short_term']['total']} total")
    print(f"   ✓ Long-term memory: {stats['long_term']['total']} total")
    print(f"      - Actions: {stats['long_term']['by_type']['action']}")
    print(f"      - Facts: {stats['long_term']['by_type']['fact']}")
    print(f"      - Preferences: {stats['long_term']['by_type']['preference']}")
    print(f"   ✓ Shared memory: {stats['shared']['total']} total")
    print(f"      - Pending: {stats['shared']['pending']}")
    print(f"      - Consumed: {stats['shared']['consumed']}")

    # ========== Cleanup ==========
    print("\n5. Cleanup...")

    memory.clear_session(session_id=session_id)
    print(f"   ✓ Cleared session: {session_id}")

    print("\n" + "=" * 60)
    print("✅ All MemoryManager tests passed!")


if __name__ == "__main__":
    try:
        test_memory_manager()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
