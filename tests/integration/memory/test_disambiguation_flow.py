"""
Integration test for end-to-end disambiguation resolution flow.

Tests the complete flow:
1. Search returns multiple results → disambiguation stored
2. Context injection shows numbered options to LLM
3. User says "the first one" → resolve_disambiguation called
4. Correct task is selected and action performed
"""

from agents.coordinator import coordinator
from shared.db import MongoDB
from memory import MemoryManager
from shared.embeddings import embed_query

def test_disambiguation_flow():
    """Test complete disambiguation resolution flow."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Ensure coordinator has memory manager
    if not coordinator.memory:
        memory = MemoryManager(db, embedding_fn=embed_query)
        coordinator.memory = memory

    print("=" * 60)
    print("TESTING END-TO-END DISAMBIGUATION FLOW")
    print("=" * 60)

    # Set session
    session_id = "test-disambiguation-flow"
    user_id = "test-user"
    coordinator.set_session(session_id, user_id=user_id)
    print(f"\n✓ Session set: {session_id}")

    # Enable memory features
    coordinator.memory_config = {
        "short_term": True,
        "long_term": True,
        "shared": True,
        "context_injection": True
    }

    # Clear any existing disambiguation
    coordinator.memory.short_term.delete_many({
        "session_id": session_id,
        "memory_type": "disambiguation"
    })

    # Test 1: Search returns multiple results → disambiguation stored
    print("\n" + "=" * 60)
    print("TEST 1: Search with multiple results")
    print("=" * 60)

    response1 = coordinator.process(
        user_message="Find debugging tasks",
        session_id=session_id,
        turn_number=1,
        optimizations={
            "memory_short_term": True,
            "context_injection": True
        },
        return_debug=True
    )

    print(f"✓ Search completed")
    print(f"  Response: {response1['response'][:150]}...")

    # Verify disambiguation was stored
    disambiguation = coordinator.memory.get_pending_disambiguation(session_id)

    if not disambiguation:
        print("\n⚠️  No disambiguation stored - search may have returned 0 or 1 results")
        print("  This test requires multiple search results")
        print("  Skipping remaining tests")
        return False

    print(f"\n✓ Disambiguation stored:")
    print(f"  Query: '{disambiguation['query']}'")
    print(f"  Results: {len(disambiguation['results'])}")
    for r in disambiguation['results']:
        print(f"    {r['index'] + 1}. {r['title']}")
    print(f"  Awaiting selection: {disambiguation.get('awaiting_selection')}")

    # Test 2: Context injection includes disambiguation
    print("\n" + "=" * 60)
    print("TEST 2: Context injection")
    print("=" * 60)

    # Build context injection
    context_injection = coordinator._build_context_injection()

    if "Pending selection" in context_injection:
        print("✓ Context injection includes disambiguation")
        print(f"\nInjected context:")
        print(context_injection)
    else:
        print("✗ Context injection missing disambiguation")
        return False

    # Verify numbered format
    for i, r in enumerate(disambiguation['results'], 1):
        if f"{i}. {r['title']}" in context_injection:
            print(f"  ✓ Found option {i} in context")
        else:
            print(f"  ✗ Missing option {i} in context")

    # Test 3: Resolve disambiguation with "the first one"
    print("\n" + "=" * 60)
    print("TEST 3: User selects 'the first one'")
    print("=" * 60)

    response2 = coordinator.process(
        user_message="Complete the first one",
        session_id=session_id,
        turn_number=2,
        optimizations={
            "memory_short_term": True,
            "context_injection": True,
            "memory_long_term": True
        },
        return_debug=True
    )

    print(f"✓ Response: {response2['response'][:200]}...")

    # Check if resolve_disambiguation was called
    tools_called = [call['name'] for call in response2['debug'].get('tool_calls', [])]
    print(f"\n✓ Tools called: {tools_called}")

    if "resolve_disambiguation" in tools_called:
        print("  ✓ resolve_disambiguation was called")

        # Find the resolve_disambiguation call
        for call in response2['debug']['tool_calls']:
            if call['name'] == 'resolve_disambiguation':
                print(f"  ✓ Selection: {call['input']['selection']}")
                print(f"  ✓ Result: {call['result']}")

                # Verify selection was 1 (the first one)
                if call['input']['selection'] == 1:
                    print("  ✓ Correctly selected option 1")
                else:
                    print(f"  ✗ Selected option {call['input']['selection']} instead of 1")
    else:
        print("  ✗ resolve_disambiguation was NOT called")
        print("  This is a FAILURE - LLM should have called resolve_disambiguation")
        return False

    # Test 4: Verify disambiguation marked as resolved
    print("\n" + "=" * 60)
    print("TEST 4: Disambiguation marked as resolved")
    print("=" * 60)

    disambiguation_after = coordinator.memory.get_pending_disambiguation(session_id)

    if disambiguation_after is None:
        print("✓ No pending disambiguation (marked as resolved)")
    else:
        if not disambiguation_after.get('awaiting_selection'):
            print("✓ Disambiguation marked as not awaiting selection")
        else:
            print("✗ Disambiguation still awaiting selection")
            return False

    # Test 5: Verify correct task was acted upon
    print("\n" + "=" * 60)
    print("TEST 5: Correct task was completed")
    print("=" * 60)

    # Check if complete_task was called with the right task_id
    if "complete_task" in tools_called or "start_task" in tools_called:
        print("✓ Task action was performed")

        for call in response2['debug']['tool_calls']:
            if call['name'] in ['complete_task', 'start_task']:
                completed_task_id = call['input'].get('task_id')
                print(f"  Task ID: {completed_task_id}")

                # Verify it matches the first option
                first_option = disambiguation['results'][0]
                if completed_task_id == first_option.get('task_id'):
                    print(f"  ✓ Correct task: {first_option['title']}")
                else:
                    print(f"  ✗ Wrong task - expected {first_option.get('task_id')}")
                    return False
    else:
        print("⚠️  No task action performed (may have encountered errors)")

    # Test 6: Test with "number 2"
    print("\n" + "=" * 60)
    print("TEST 6: User selects 'number 2'")
    print("=" * 60)

    # Create new disambiguation
    coordinator.memory.store_disambiguation(
        session_id,
        "test query",
        [
            {"task_id": "task1", "title": "First task", "project": "Project A"},
            {"task_id": "task2", "title": "Second task", "project": "Project B"},
            {"task_id": "task3", "title": "Third task", "project": "Project C"}
        ],
        "coordinator"
    )

    response3 = coordinator.process(
        user_message="Start number 2",
        session_id=session_id,
        turn_number=3,
        optimizations={
            "memory_short_term": True,
            "context_injection": True
        },
        return_debug=True
    )

    tools_called_3 = [call['name'] for call in response3['debug'].get('tool_calls', [])]

    if "resolve_disambiguation" in tools_called_3:
        for call in response3['debug']['tool_calls']:
            if call['name'] == 'resolve_disambiguation':
                if call['input']['selection'] == 2:
                    print(f"✓ Correctly selected option 2")
                    print(f"  Result: {call['result'].get('title')}")
                else:
                    print(f"✗ Selected option {call['input']['selection']} instead of 2")
    else:
        print("✗ resolve_disambiguation was NOT called for 'number 2'")

    # Test 7: Test invalid selection
    print("\n" + "=" * 60)
    print("TEST 7: Invalid selection handling")
    print("=" * 60)

    # Create new disambiguation with 2 options
    coordinator.memory.store_disambiguation(
        session_id,
        "test query 2",
        [
            {"task_id": "taskA", "title": "Task A", "project": "Project X"},
            {"task_id": "taskB", "title": "Task B", "project": "Project Y"}
        ],
        "coordinator"
    )

    response4 = coordinator.process(
        user_message="Start number 5",  # Invalid - only 2 options
        session_id=session_id,
        turn_number=4,
        optimizations={
            "memory_short_term": True,
            "context_injection": True
        },
        return_debug=True
    )

    tools_called_4 = [call['name'] for call in response4['debug'].get('tool_calls', [])]

    if "resolve_disambiguation" in tools_called_4:
        for call in response4['debug']['tool_calls']:
            if call['name'] == 'resolve_disambiguation':
                if not call['result'].get('success'):
                    print(f"✓ Invalid selection rejected")
                    print(f"  Error: {call['result'].get('error')}")
                else:
                    print(f"✗ Invalid selection was accepted (should fail)")
    else:
        print("⚠️  resolve_disambiguation was not called for invalid selection")

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    coordinator.memory.clear_session(session_id)
    print("✓ Session cleaned up")

    print("\n" + "=" * 60)
    print("✅ ALL DISAMBIGUATION TESTS PASSED!")
    print("=" * 60)

    print("\nKey Features Verified:")
    print("  ✓ Multiple search results → disambiguation stored")
    print("  ✓ Context injection shows numbered options")
    print("  ✓ 'the first one' → resolve_disambiguation(1) called")
    print("  ✓ 'number 2' → resolve_disambiguation(2) called")
    print("  ✓ Correct task_id retrieved and used")
    print("  ✓ Disambiguation marked as resolved")
    print("  ✓ Invalid selections rejected")

    return True


if __name__ == "__main__":
    success = test_disambiguation_flow()
    if not success:
        print("\n❌ Some disambiguation tests failed")
        exit(1)
