#!/usr/bin/env python3
"""
Comprehensive test script for the agent memory system.

Tests all three memory types:
1. Short-term Memory - Session context (2-hour TTL)
2. Long-term Memory - Action history with vector search
3. Shared Memory - Agent-to-agent handoffs (5-minute TTL)

Usage:
    # Test all memory systems
    python scripts/test_memory_system.py

    # Test specific memory type
    python scripts/test_memory_system.py --short-term
    python scripts/test_memory_system.py --long-term
    python scripts/test_memory_system.py --shared

    # Test coordinator integration
    python scripts/test_memory_system.py --coordinator
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryManager
from shared.db import MongoDB
from agents.coordinator import coordinator
from agents.retrieval import retrieval_agent
from agents.worklog import worklog_agent


def test_short_term_memory(memory, session_id="test_session_123"):
    """Test short-term memory operations."""

    print("\n" + "=" * 60)
    print("Testing Short-term Memory")
    print("=" * 60)

    # Write short-term memory
    print("\n1. Writing session context...")
    memory.write_short_term(
        session_id=session_id,
        user_id="test_user",
        context={
            "current_project": "AgentOps",
            "current_task": "debugging_doc",
            "last_action": "completed_task"
        }
    )
    print("   ✓ Context written")

    # Read it back
    print("\n2. Reading session context...")
    context = memory.read_short_term(session_id)
    if context:
        print(f"   ✓ Retrieved context: {context.get('data', {})}")
    else:
        print("   ✗ Failed to retrieve context")

    # Check stats
    print("\n3. Checking memory stats...")
    stats = memory.get_memory_stats(session_id)
    print(f"   Short-term entries: {stats.get('short_term_count', 0)}")

    return context is not None


def test_long_term_memory(memory, user_id="test_user"):
    """Test long-term memory operations."""

    print("\n" + "=" * 60)
    print("Testing Long-term Memory")
    print("=" * 60)

    # Check if embedding function exists
    if not memory.embed:
        print("\n⚠️  Embedding function not configured")
        print("   Long-term memory requires embeddings for vector search")
        return False

    # Write action to long-term memory
    print("\n1. Recording action to long-term memory...")
    memory.write_long_term(
        user_id=user_id,
        type="action",
        content="Completed debugging documentation task",
        metadata={
            "action_type": "completed",
            "task_id": "test_task_123",
            "task_title": "Create debugging methodologies doc"
        }
    )
    print("   ✓ Action recorded")

    # Search long-term memory
    print("\n2. Searching long-term memory...")
    results = memory.search_long_term(
        user_id=user_id,
        query="debugging documentation",
        limit=5
    )
    if results:
        print(f"   ✓ Found {len(results)} matching actions")
        for i, result in enumerate(results[:3], 1):
            content = result.get("content", "")[:50]
            score = result.get("score", 0)
            print(f"   {i}. {content}... (score: {score:.2f})")
    else:
        print("   ✗ No results found")

    # Check stats
    print("\n3. Checking memory stats...")
    stats = memory.get_memory_stats(user_id)
    print(f"   Long-term total: {stats.get('long_term_total', 0)}")
    print(f"   Long-term actions: {stats.get('long_term_actions', 0)}")

    return len(results) > 0 if results else False


def test_shared_memory(memory, session_id="test_session_456"):
    """Test shared memory (agent handoff) operations."""

    print("\n" + "=" * 60)
    print("Testing Shared Memory (Agent Handoffs)")
    print("=" * 60)

    # Write handoff
    print("\n1. Writing agent handoff...")
    memory.write_shared(
        session_id=session_id,
        from_agent="retrieval",
        to_agent="worklog",
        data={
            "task_id": "test_task_789",
            "task_title": "Build voice agent reference app",
            "action": "complete"
        }
    )
    print("   ✓ Handoff written (retrieval → worklog)")

    # Read handoff
    print("\n2. Reading handoff (as worklog agent)...")
    handoff = memory.read_shared(session_id, to_agent="worklog")
    if handoff:
        print(f"   ✓ Retrieved handoff from {handoff.get('from_agent', 'unknown')}")
        print(f"   Data: {handoff.get('data', {})}")
    else:
        print("   ✗ No handoff found")

    # Try to read again (should be consumed)
    print("\n3. Attempting to read again (should fail - already consumed)...")
    handoff2 = memory.read_shared(session_id, to_agent="worklog")
    if handoff2:
        print("   ✗ Handoff was not marked as consumed!")
    else:
        print("   ✓ Handoff correctly consumed (can't read twice)")

    # Check stats
    print("\n4. Checking memory stats...")
    stats = memory.get_memory_stats(session_id)
    print(f"   Shared memory pending: {stats.get('shared_pending', 0)}")

    return handoff is not None and handoff2 is None


def test_coordinator_integration():
    """Test that coordinator has memory integration."""

    print("\n" + "=" * 60)
    print("Testing Coordinator Memory Integration")
    print("=" * 60)

    # Check if coordinator has memory
    if coordinator.memory:
        print("\n✅ Coordinator has memory manager")
        print(f"   Type: {type(coordinator.memory).__name__}")

        # Check embedding function
        if coordinator.memory.embed:
            print("✅ Embedding function configured")
        else:
            print("⚠️  Embedding function not configured")

        # Get stats
        stats = coordinator.memory.get_memory_stats()
        print(f"\n📊 Memory Stats:")
        print(f"   Short-term: {stats.get('short_term_count', 0)}")
        print(f"   Long-term: {stats.get('long_term_total', 0)}")
        print(f"   Shared pending: {stats.get('shared_pending', 0)}")

        return True
    else:
        print("\n✗ Coordinator does not have memory manager")
        return False


def test_agent_memory_integration():
    """Test that all agents have memory manager access."""

    print("\n" + "=" * 60)
    print("Testing Agent Memory Integration")
    print("=" * 60)

    agents = [
        ("Coordinator", coordinator),
        ("Retrieval", retrieval_agent),
        ("Worklog", worklog_agent)
    ]

    all_have_memory = True

    for name, agent in agents:
        if hasattr(agent, 'memory') and agent.memory:
            print(f"✅ {name} agent has memory manager")
        else:
            print(f"✗ {name} agent missing memory manager")
            all_have_memory = False

    return all_have_memory


def test_memory_timing(memory, session_id="test_timing"):
    """Test memory operation performance."""

    print("\n" + "=" * 60)
    print("Testing Memory Performance")
    print("=" * 60)

    import time

    # Time short-term write
    start = time.time()
    memory.write_short_term(session_id, "test_user", {"test": "data"})
    short_write = (time.time() - start) * 1000

    # Time short-term read
    start = time.time()
    memory.read_short_term(session_id)
    short_read = (time.time() - start) * 1000

    # Time shared write
    start = time.time()
    memory.write_shared(session_id, "agent1", "agent2", {"test": "data"})
    shared_write = (time.time() - start) * 1000

    # Time shared read
    start = time.time()
    memory.read_shared(session_id, "agent2")
    shared_read = (time.time() - start) * 1000

    print(f"\n📈 Performance Results:")
    print(f"   Short-term write: {short_write:.1f}ms")
    print(f"   Short-term read:  {short_read:.1f}ms")
    print(f"   Shared write:     {shared_write:.1f}ms")
    print(f"   Shared read:      {shared_read:.1f}ms")

    # Check if within acceptable range
    acceptable = short_write < 50 and short_read < 50 and shared_write < 50 and shared_read < 50
    if acceptable:
        print("\n✅ All operations under 50ms")
    else:
        print("\n⚠️  Some operations slower than expected")

    return acceptable


def main():
    parser = argparse.ArgumentParser(
        description="Test the agent memory system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--short-term",
        action="store_true",
        help="Test short-term memory only"
    )

    parser.add_argument(
        "--long-term",
        action="store_true",
        help="Test long-term memory only"
    )

    parser.add_argument(
        "--shared",
        action="store_true",
        help="Test shared memory only"
    )

    parser.add_argument(
        "--coordinator",
        action="store_true",
        help="Test coordinator integration only"
    )

    parser.add_argument(
        "--agents",
        action="store_true",
        help="Test agent integration only"
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help="Test memory performance only"
    )

    args = parser.parse_args()

    # Connect to database
    mongodb = MongoDB()
    db = mongodb.connect()

    # Create memory manager
    memory = MemoryManager(db=db, embedding_fn=None)

    # Track test results
    results = []

    # Determine what to test
    test_all = not any([
        args.short_term, args.long_term, args.shared,
        args.coordinator, args.agents, args.performance
    ])

    # Run tests
    if test_all or args.short_term:
        results.append(("Short-term Memory", test_short_term_memory(memory)))

    if test_all or args.long_term:
        results.append(("Long-term Memory", test_long_term_memory(memory)))

    if test_all or args.shared:
        results.append(("Shared Memory", test_shared_memory(memory)))

    if test_all or args.coordinator:
        results.append(("Coordinator Integration", test_coordinator_integration()))

    if test_all or args.agents:
        results.append(("Agent Integration", test_agent_memory_integration()))

    if test_all or args.performance:
        results.append(("Memory Performance", test_memory_timing(memory)))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
