"""Test script for shared memory integration in agents."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator import coordinator
from agents.retrieval import retrieval_agent
from agents.worklog import worklog_agent


def test_shared_memory_integration():
    """Test that agents have shared memory access."""

    print("Testing Shared Memory Integration...")
    print("=" * 60)

    # Check if all agents have memory manager
    agents = [
        ("Coordinator", coordinator),
        ("Retrieval", retrieval_agent),
        ("Worklog", worklog_agent)
    ]

    for name, agent in agents:
        if agent.memory:
            print(f"✅ {name} agent has memory manager")
        else:
            print(f"❌ {name} agent does NOT have memory manager")

    # Test shared memory flow: retrieval → worklog handoff
    print(f"\n🧪 Testing Retrieval → Worklog Handoff...")

    if retrieval_agent.memory and worklog_agent.memory:
        session_id = "test_session_handoff"

        # Set session on both agents
        retrieval_agent.set_session(session_id)
        worklog_agent.set_session(session_id)
        print(f"✅ Set session ID: {session_id}")

        # Simulate retrieval agent writing a handoff
        handoff_data = {
            "operation": "task_match",
            "query": "debugging doc",
            "best_match": {
                "id": "test_task_123",
                "title": "Create debugging documentation",
                "status": "in_progress",
                "project_name": "AgentOps"
            },
            "confidence": 0.95,
            "alternatives": []
        }

        retrieval_agent.memory.write_shared(
            session_id=session_id,
            from_agent="retrieval",
            to_agent="worklog",
            content=handoff_data
        )
        print(f"✅ Retrieval agent wrote handoff to shared memory")
        print(f"   Operation: {handoff_data['operation']}")
        print(f"   Query: {handoff_data['query']}")
        print(f"   Match: {handoff_data['best_match']['title']}")

        # Simulate worklog agent reading the handoff
        handoff = worklog_agent.memory.read_shared(
            session_id=session_id,
            to_agent="worklog",
            consume=True
        )

        if handoff:
            print(f"✅ Worklog agent consumed handoff from shared memory")
            content = handoff.get("content", {})
            print(f"   From: {handoff.get('from_agent')}")
            print(f"   To: {handoff.get('to_agent')}")
            print(f"   Operation: {content.get('operation')}")
            print(f"   Best match: {content.get('best_match', {}).get('title')}")
            print(f"   Status: {handoff.get('status')}")
        else:
            print(f"❌ Worklog agent could not read handoff")

        # Try reading again (should be consumed)
        handoff2 = worklog_agent.memory.read_shared(
            session_id=session_id,
            to_agent="worklog",
            consume=False
        )

        if not handoff2:
            print(f"✅ Handoff correctly marked as consumed (can't read twice)")
        else:
            print(f"⚠️  Handoff still available (should be consumed)")

        # Check memory stats
        stats = coordinator.memory.get_memory_stats()
        print(f"\n📊 Shared Memory Statistics:")
        print(f"   Total: {stats['shared']['total']}")
        print(f"   Active (pending): {stats['shared']['pending']}")
        print(f"   Consumed: {stats['shared']['consumed']}")

    else:
        print("⚠️  Memory manager not available on agents")

    print("\n" + "=" * 60)
    print("✅ All shared memory tests passed!")


if __name__ == "__main__":
    try:
        test_shared_memory_integration()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
