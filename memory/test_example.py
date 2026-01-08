"""
Test examples for the comprehensive Memory Manager.

Run this script to test all three memory types:
- Short-term (session context, agent working, disambiguation)
- Long-term (action history, activity summaries)
- Shared (handoffs, chains)
"""

from memory import MemoryManager
from shared.db import MongoDB
from shared.embeddings import embed_query


def test_memory_manager():
    """Test all Memory Manager features."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()
    mm = MemoryManager(db, embedding_fn=embed_query)

    print("=" * 60)
    print("TESTING MEMORY MANAGER")
    print("=" * 60)

    # Test session context
    print("\n1. SHORT-TERM: Session Context")
    print("-" * 60)
    mm.update_session_context("session-1", {"current_project": "AgentOps"})
    ctx = mm.read_session_context("session-1")
    print(f"✓ Session context: {ctx}")

    # Update with merge
    mm.update_session_context("session-1", {"last_action": "created_task"})
    ctx = mm.read_session_context("session-1")
    print(f"✓ After merge: {ctx}")

    # Test agent working memory
    print("\n2. SHORT-TERM: Agent Working Memory")
    print("-" * 60)
    mm.update_agent_working("session-1", "retrieval", {"search_iteration": 1})
    working = mm.read_agent_working("session-1", "retrieval")
    print(f"✓ Retrieval agent working: {working}")

    mm.update_agent_working("session-1", "worklog", {"pending_task_id": "abc123"})
    working = mm.read_agent_working("session-1", "worklog")
    print(f"✓ Worklog agent working: {working}")

    # Test disambiguation
    print("\n3. SHORT-TERM: Disambiguation")
    print("-" * 60)
    mm.store_disambiguation(
        "session-1",
        "MCP task",
        [
            {"task_id": "abc", "title": "MCP integration"},
            {"task_id": "def", "title": "MCP testing"},
            {"task_id": "ghi", "title": "MCP documentation"}
        ],
        "retrieval"
    )

    pending = mm.get_pending_disambiguation("session-1")
    print(f"✓ Pending disambiguation: {pending['query']}")
    print(f"  - {len(pending['results'])} results awaiting selection")

    selected = mm.resolve_disambiguation("session-1", 0)
    print(f"✓ Selected: {selected['title']}")

    # Test long-term action recording
    print("\n4. LONG-TERM: Action Recording")
    print("-" * 60)

    # Record multiple actions
    mm.record_action(
        user_id="user-1",
        session_id="session-1",
        action_type="complete",
        entity_type="task",
        entity={"task_id": "123", "task_title": "MCP integration", "project_name": "AgentOps"},
        metadata={"completion_note": "Finished implementation"},
        source_agent="worklog",
        generate_embedding=False  # Skip for speed
    )

    mm.record_action(
        user_id="user-1",
        session_id="session-1",
        action_type="start",
        entity_type="task",
        entity={"task_id": "456", "task_title": "MCP testing", "project_name": "AgentOps"},
        source_agent="worklog",
        generate_embedding=False
    )

    mm.record_action(
        user_id="user-1",
        session_id="session-1",
        action_type="search",
        entity_type="search",
        entity={"query": "debugging documentation"},
        metadata={"query": "debugging documentation", "results_count": 5},
        source_agent="retrieval",
        generate_embedding=False
    )

    print("✓ Recorded 3 actions")

    # Query action history
    print("\n5. LONG-TERM: Query History")
    print("-" * 60)

    history = mm.get_action_history("user-1", time_range="today")
    print(f"✓ Actions today: {len(history)}")
    for action in history:
        print(f"  - {action['action_type']}: {action['entity_type']} by {action['source_agent']}")

    # Get activity summary
    print("\n6. LONG-TERM: Activity Summary")
    print("-" * 60)

    summary = mm.get_activity_summary("user-1", time_range="today")
    print(f"✓ Total actions: {summary['total']}")
    print(f"  By type: {summary['by_type']}")
    print(f"  By agent: {summary['by_agent']}")
    print(f"  By project: {list(summary['by_project'].keys())}")

    # Test shared memory handoffs
    print("\n7. SHARED: Handoffs")
    print("-" * 60)

    handoff_id = mm.write_handoff(
        session_id="session-1",
        user_id="user-1",
        source_agent="coordinator",
        target_agent="retrieval",
        handoff_type="search_request",
        payload={"query": "debugging task", "limit": 5},
        priority="high"
    )
    print(f"✓ Created handoff: {handoff_id}")

    # Check pending
    has_pending = mm.check_pending("session-1", "retrieval")
    print(f"✓ Retrieval has pending: {has_pending}")

    # Read handoff
    handoff = mm.read_handoff("session-1", "retrieval", consume=True)
    print(f"✓ Retrieved handoff: {handoff['handoff_type']}")
    print(f"  Priority: {handoff['priority']}")
    print(f"  Payload: {handoff['payload']}")

    # Test handoff chains
    print("\n8. SHARED: Handoff Chains")
    print("-" * 60)

    chain_id = mm.write_handoff(
        session_id="session-1",
        user_id="user-1",
        source_agent="coordinator",
        target_agent="retrieval",
        handoff_type="complex_research",
        payload={"topic": "memory systems"},
        priority="normal"
    )

    # Child handoff
    mm.write_handoff(
        session_id="session-1",
        user_id="user-1",
        source_agent="retrieval",
        target_agent="worklog",
        handoff_type="create_summary",
        payload={"findings": ["fact 1", "fact 2"]},
        chain_id=chain_id,
        parent_handoff_id=chain_id
    )

    chain_status = mm.get_chain_status(chain_id)
    print(f"✓ Chain status: {chain_status['total']} handoffs")
    print(f"  Pending: {chain_status['pending']}")
    print(f"  Agents involved: {chain_status['agents_involved']}")

    # Get memory stats
    print("\n9. MEMORY STATS")
    print("-" * 60)

    stats = mm.get_memory_stats("session-1", "user-1")
    print(f"✓ Short-term entries: {stats['short_term_count']}")
    print(f"✓ Long-term entries: {stats['long_term_count']}")
    print(f"✓ Shared pending: {stats['shared_pending']}")
    print(f"✓ Action counts: {stats['action_counts']}")

    # Cleanup
    print("\n10. CLEANUP")
    print("-" * 60)

    result = mm.clear_session("session-1")
    print(f"✓ Deleted {result['short_term_deleted']} short-term entries")
    print(f"✓ Deleted {result['shared_deleted']} shared entries")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_memory_manager()
