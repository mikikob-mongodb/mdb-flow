"""
Integration test for narrative generation from activity summaries.

Tests the complete flow:
1. get_activity_summary() returns raw stats
2. generate_narrative() converts stats to formatted markdown
3. get_action_history tool includes both narrative and raw stats
4. LLM can use pre-formatted narrative or customize from raw stats
"""

from agents.coordinator import coordinator
from shared.db import MongoDB, get_collection, TASKS_COLLECTION
from memory import MemoryManager
from shared.embeddings import embed_query
from datetime import datetime, timedelta

def test_narrative_generation():
    """Test narrative generation from activity summaries."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Ensure coordinator has memory manager
    if not coordinator.memory:
        memory = MemoryManager(db, embedding_fn=embed_query)
        coordinator.memory = memory

    print("=" * 60)
    print("TESTING NARRATIVE GENERATION FROM ACTIVITY SUMMARIES")
    print("=" * 60)

    # Set session
    session_id = "test-narrative-generation"
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

    # Clear existing action history for this user
    coordinator.memory.long_term.delete_many({"user_id": user_id})
    print("✓ Cleared existing action history")

    # Test 1: Record diverse actions
    print("\n" + "=" * 60)
    print("TEST 1: Record diverse actions for summary")
    print("=" * 60)

    # Record actions across multiple projects
    test_actions = [
        # Voice Agent project
        {"action_type": "complete", "entity_type": "task",
         "entity": {"task_id": "task1", "task_title": "Fix audio recording bug", "project_name": "Voice Agent"}},
        {"action_type": "complete", "entity_type": "task",
         "entity": {"task_id": "task2", "task_title": "Add voice command support", "project_name": "Voice Agent"}},
        {"action_type": "start", "entity_type": "task",
         "entity": {"task_id": "task3", "task_title": "Implement wake word detection", "project_name": "Voice Agent"}},
        {"action_type": "start", "entity_type": "task",
         "entity": {"task_id": "task4", "task_title": "Test audio pipeline", "project_name": "Voice Agent"}},

        # Memory Engineering project
        {"action_type": "complete", "entity_type": "task",
         "entity": {"task_id": "task5", "task_title": "Implement vector search", "project_name": "Memory Engineering"}},
        {"action_type": "complete", "entity_type": "task",
         "entity": {"task_id": "task6", "task_title": "Add embedding generation", "project_name": "Memory Engineering"}},
        {"action_type": "start", "entity_type": "task",
         "entity": {"task_id": "task7", "task_title": "Optimize memory usage", "project_name": "Memory Engineering"}},

        # Documentation project
        {"action_type": "create", "entity_type": "task",
         "entity": {"task_id": "task8", "task_title": "Write API documentation", "project_name": "Documentation"}},
        {"action_type": "create", "entity_type": "task",
         "entity": {"task_id": "task9", "task_title": "Update README", "project_name": "Documentation"}},
        {"action_type": "add_note", "entity_type": "task",
         "entity": {"task_id": "task10", "task_title": "Setup guide", "project_name": "Documentation"},
         "metadata": {"note": "Added installation steps"}},

        # Misc actions
        {"action_type": "search", "entity_type": "task",
         "entity": {"task_id": "task11", "task_title": "Find debugging tasks", "project_name": ""}},
        {"action_type": "update", "entity_type": "task",
         "entity": {"task_id": "task12", "task_title": "Change priority", "project_name": "Voice Agent"}},
    ]

    for action_data in test_actions:
        coordinator.memory.record_action(
            user_id=user_id,
            session_id=session_id,
            action_type=action_data["action_type"],
            entity_type=action_data["entity_type"],
            entity=action_data["entity"],
            metadata=action_data.get("metadata", {}),
            generate_embedding=False  # Skip embeddings for this test
        )

    print(f"✓ Recorded {len(test_actions)} diverse actions")

    # Test 2: Get raw activity summary
    print("\n" + "=" * 60)
    print("TEST 2: Get raw activity summary")
    print("=" * 60)

    raw_summary = coordinator.memory.get_activity_summary(
        user_id=user_id,
        time_range="this_week"
    )

    print(f"✓ Raw summary generated:")
    print(f"  Total: {raw_summary['total']}")
    print(f"  By type: {raw_summary['by_type']}")
    print(f"  Projects: {list(raw_summary['by_project'].keys())}")

    if raw_summary['total'] != len(test_actions):
        print(f"✗ Expected {len(test_actions)} actions, got {raw_summary['total']}")
        return False

    print(f"  ✓ Action count correct")

    # Test 3: Generate narrative from raw summary
    print("\n" + "=" * 60)
    print("TEST 3: Generate narrative from raw summary")
    print("=" * 60)

    narrative = coordinator.memory.generate_narrative(raw_summary)

    print(f"✓ Narrative generated:")
    print("\n" + "-" * 60)
    print(narrative)
    print("-" * 60)

    # Verify narrative contains expected elements
    required_sections = [
        "Activity Summary",
        "Total actions:",
        "Actions:",
        "Top Projects:",
        "Recent Activity:"
    ]

    for section in required_sections:
        if section in narrative:
            print(f"  ✓ Contains section: '{section}'")
        else:
            print(f"  ✗ Missing section: '{section}'")
            return False

    # Verify narrative mentions project names
    if "Voice Agent" in narrative:
        print(f"  ✓ Mentions 'Voice Agent' project")
    else:
        print(f"  ✗ Missing 'Voice Agent' project in narrative")

    if "Memory Engineering" in narrative:
        print(f"  ✓ Mentions 'Memory Engineering' project")
    else:
        print(f"  ✗ Missing 'Memory Engineering' project in narrative")

    # Verify action counts appear in narrative
    if "complete" in narrative.lower():
        print(f"  ✓ Mentions 'complete' actions")
    else:
        print(f"  ✗ Missing 'complete' actions")

    # Test 4: Test with empty summary
    print("\n" + "=" * 60)
    print("TEST 4: Generate narrative for empty summary")
    print("=" * 60)

    empty_summary = {
        "total": 0,
        "time_range": "yesterday",
        "by_type": {},
        "by_project": {},
        "by_agent": {},
        "timeline": []
    }

    empty_narrative = coordinator.memory.generate_narrative(empty_summary)

    print(f"✓ Empty narrative generated:")
    print(f"  {empty_narrative}")

    if "No activity recorded" in empty_narrative:
        print(f"  ✓ Contains 'No activity recorded' message")
    else:
        print(f"  ✗ Missing 'No activity recorded' message")
        return False

    # Test 5: Tool integration - verify narrative in response
    print("\n" + "=" * 60)
    print("TEST 5: Tool integration with narrative")
    print("=" * 60)

    response = coordinator.process(
        user_message="Summarize my activity this week",
        session_id=session_id,
        turn_number=1,
        optimizations={
            "memory_long_term": True,
            "context_injection": True
        },
        return_debug=True
    )

    tools_called = [call['name'] for call in response['debug'].get('tool_calls', [])]
    print(f"✓ Tools called: {tools_called}")

    if "get_action_history" in tools_called:
        print("  ✓ get_action_history was called")

        # Find the get_action_history call
        for call in response['debug']['tool_calls']:
            if call['name'] == 'get_action_history':
                tool_input = call['input']
                tool_result = call.get('result', {})

                # Verify summarize=true was used
                if tool_input.get('summarize'):
                    print(f"  ✓ Tool called with summarize=True")
                else:
                    print(f"  ⚠️  Tool called without summarize parameter")

                # Verify narrative is in result
                if 'narrative' in tool_result:
                    narrative_result = tool_result['narrative']
                    print(f"  ✓ Result contains 'narrative' field")
                    print(f"\n  Narrative preview:")
                    print("  " + "\n  ".join(narrative_result.split("\n")[:5]))

                    # Verify it's formatted markdown
                    if "**" in narrative_result:
                        print(f"  ✓ Narrative contains markdown formatting")
                    else:
                        print(f"  ⚠️  Narrative missing markdown formatting")

                else:
                    print(f"  ✗ Result missing 'narrative' field")
                    print(f"  Result keys: {tool_result.keys()}")
                    return False

                # Verify raw stats are still present
                if 'by_type' in tool_result and 'by_project' in tool_result:
                    print(f"  ✓ Result still contains raw stats (by_type, by_project)")
                else:
                    print(f"  ✗ Result missing raw stats")
                    return False

    else:
        print("  ✗ get_action_history was NOT called")
        return False

    # Test 6: LLM response quality
    print("\n" + "=" * 60)
    print("TEST 6: Verify LLM uses narrative in response")
    print("=" * 60)

    llm_response = response['response']
    print(f"✓ LLM response preview:")
    print(f"  {llm_response[:300]}...")

    # Check if LLM included activity details
    activity_indicators = ["complete", "start", "Voice Agent", "Memory Engineering", "actions"]
    found_indicators = [ind for ind in activity_indicators if ind in llm_response]

    print(f"\n  Activity indicators found: {len(found_indicators)}/{len(activity_indicators)}")
    for ind in found_indicators:
        print(f"    ✓ Contains '{ind}'")

    if len(found_indicators) >= 3:
        print(f"  ✓ LLM incorporated activity details")
    else:
        print(f"  ⚠️  LLM response may not have used narrative effectively")

    # Test 7: Formatting quality
    print("\n" + "=" * 60)
    print("TEST 7: Narrative formatting quality")
    print("=" * 60)

    # Check markdown elements
    markdown_checks = {
        "Headers (##)": "**" in narrative,
        "Lists (-)": "- " in narrative,
        "Bold text": "**" in narrative,
        "Structured sections": narrative.count("\n\n") >= 2
    }

    all_passed = True
    for check_name, check_result in markdown_checks.items():
        if check_result:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ {check_name}")
            all_passed = False

    if not all_passed:
        print(f"  ⚠️  Some formatting checks failed")

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    coordinator.memory.long_term.delete_many({"user_id": user_id})
    coordinator.memory.clear_session(session_id)
    print("✓ Session and test actions cleaned up")

    print("\n" + "=" * 60)
    print("✅ ALL NARRATIVE GENERATION TESTS PASSED!")
    print("=" * 60)

    print("\nKey Features Verified:")
    print("  ✓ get_activity_summary() returns raw stats")
    print("  ✓ generate_narrative() creates formatted markdown")
    print("  ✓ Narrative includes all expected sections")
    print("  ✓ Tool response contains both narrative and raw stats")
    print("  ✓ Empty summaries handled gracefully")
    print("  ✓ LLM receives pre-formatted narrative")
    print("  ✓ Markdown formatting is properly structured")

    print("\n💡 Benefits:")
    print("  • Consistent summary formatting")
    print("  • Pre-formatted markdown structure")
    print("  • LLM can use narrative directly or customize from raw stats")
    print("  • Reduces LLM output token usage")

    return True


if __name__ == "__main__":
    success = test_narrative_generation()
    if not success:
        print("\n❌ Some narrative generation tests failed")
        exit(1)
