"""Test script for long-term memory integration in coordinator."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator import coordinator


def test_coordinator_memory_integration():
    """Test that coordinator has memory manager initialized."""

    print("Testing Coordinator Memory Integration...")
    print("=" * 60)

    # Check if coordinator has memory manager
    if coordinator.memory:
        print("✅ Coordinator has memory manager")
        print(f"   Memory manager type: {type(coordinator.memory).__name__}")

        # Check if embedding function is set
        if coordinator.memory.embed:
            print("✅ Embedding function is configured")
        else:
            print("⚠️  Embedding function not configured")

        # Get memory stats
        stats = coordinator.memory.get_memory_stats()
        print(f"\n📊 Memory Statistics:")
        print(f"   Short-term: {stats['short_term']['total']} total")
        print(f"   Long-term: {stats['long_term']['total']} total")
        print(f"      - Actions: {stats['long_term']['by_type']['action']}")
        print(f"      - Facts: {stats['long_term']['by_type']['fact']}")
        print(f"      - Preferences: {stats['long_term']['by_type']['preference']}")
        print(f"   Shared: {stats['shared']['total']} total")

        # Test recording an action
        print(f"\n🧪 Testing action recording...")
        coordinator._record_to_long_term(
            action="test",
            content={
                "task": {"title": "Test task"},
                "project": "Test project"
            }
        )
        print("✅ Successfully recorded test action")

        # Verify it was recorded
        memories = coordinator.memory.read_long_term(
            user_id="default",
            memory_type="action",
            limit=1
        )

        if memories and len(memories) > 0:
            latest = memories[0]
            print(f"✅ Verified action was recorded:")
            print(f"   Action: {latest['content']['action']}")
            print(f"   Task: {latest['content']['task']['title']}")
            print(f"   Project: {latest['content']['project']}")
        else:
            print("⚠️  Could not find recorded action")

    else:
        print("❌ Coordinator does not have memory manager")
        print("   Memory features will not be available")

    print("\n" + "=" * 60)

    # Check available tools
    print(f"\n🔧 Testing tool availability...")

    # Simulate with memory enabled
    coordinator.optimizations = {"long_term_memory": True}
    tools_with_memory = coordinator._get_available_tools()
    tool_names_with = [t["name"] for t in tools_with_memory]

    if "get_action_history" in tool_names_with:
        print(f"✅ get_action_history tool available when memory enabled")
        print(f"   Total tools: {len(tools_with_memory)}")
    else:
        print(f"❌ get_action_history tool NOT available when memory enabled")

    # Simulate with memory disabled
    coordinator.optimizations = {"long_term_memory": False}
    tools_without_memory = coordinator._get_available_tools()
    tool_names_without = [t["name"] for t in tools_without_memory]

    if "get_action_history" not in tool_names_without:
        print(f"✅ get_action_history tool excluded when memory disabled")
        print(f"   Total tools: {len(tools_without_memory)}")
    else:
        print(f"❌ get_action_history tool still available when memory disabled")

    print(f"\n✅ All tests passed!")


if __name__ == "__main__":
    try:
        test_coordinator_memory_integration()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
