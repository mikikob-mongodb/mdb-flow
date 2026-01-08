"""
Test rule trigger checking with procedural memory.

Verifies that _check_rule_triggers() matches user messages
against rules stored in long-term procedural memory.
"""

from agents.coordinator import coordinator

def test_rule_triggers():
    """Test rule trigger matching from long-term memory."""

    print("=" * 60)
    print("TESTING RULE TRIGGER MATCHING")
    print("=" * 60)

    # Setup
    user_id = "test-user-rule-triggers"
    session_id = "test-session-rule-triggers"

    # Clean up
    if coordinator.memory:
        coordinator.memory.long_term.delete_many({"user_id": user_id})
        coordinator.memory.clear_session(session_id)

    coordinator.set_session(session_id, user_id=user_id)
    print(f"\n✓ Session set: {session_id}")
    print(f"  User ID: {user_id}")

    # ═══════════════════════════════════════════════════════════════
    # TEST 1: No match when no rules exist
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 1: No match when no rules exist")
    print("=" * 60)

    result = coordinator._check_rule_triggers("done")
    print(f"\n✓ Check for 'done': {result}")

    if result is None:
        print("✅ No match when no rules exist")
    else:
        print("❌ Should not match when no rules exist")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 2: Match trigger after adding rule
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 2: Match trigger after adding rule")
    print("=" * 60)

    # Add rule
    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="done",
        action="complete_current_task",
        source="explicit",
        confidence=0.9
    )
    print("\n✓ Added rule: done → complete_current_task")

    result = coordinator._check_rule_triggers("done")
    print(f"\n✓ Check for 'done': {result}")

    if result and result.get("matched"):
        print("✅ Rule matched successfully")
        print(f"  Trigger: {result['trigger']}")
        print(f"  Action: {result['action']}")

        if result["trigger"] == "done":
            print("✅ Correct trigger matched")
        else:
            print("❌ Wrong trigger matched")
            return False

        if result["action"] == "complete_current_task":
            print("✅ Correct action returned")
        else:
            print("❌ Wrong action returned")
            return False
    else:
        print("❌ Rule should have matched")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 3: Case-insensitive matching
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 3: Case-insensitive matching")
    print("=" * 60)

    result = coordinator._check_rule_triggers("DONE")
    if result and result.get("matched"):
        print("\n✅ Case-insensitive match works (DONE → done)")
    else:
        print("\n❌ Case-insensitive match failed")
        return False

    result = coordinator._check_rule_triggers("Done")
    if result and result.get("matched"):
        print("✅ Case-insensitive match works (Done → done)")
    else:
        print("❌ Case-insensitive match failed")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 4: Trigger in sentence
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 4: Trigger within sentence")
    print("=" * 60)

    result = coordinator._check_rule_triggers("I'm done with this task")
    if result and result.get("matched"):
        print("\n✅ Trigger matched in sentence: 'I'm done with this task'")
    else:
        print("\n❌ Should match trigger within sentence")
        return False

    result = coordinator._check_rule_triggers("This is done now")
    if result and result.get("matched"):
        print("✅ Trigger matched in sentence: 'This is done now'")
    else:
        print("❌ Should match trigger within sentence")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 5: Multiple rules - first match wins
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 5: Multiple rules")
    print("=" * 60)

    # Add more rules
    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="next",
        action="start_next_task",
        source="explicit",
        confidence=0.85
    )
    print("\n✓ Added rule: next → start_next_task")

    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="skip",
        action="skip_current_task",
        source="explicit",
        confidence=0.8
    )
    print("✓ Added rule: skip → skip_current_task")

    # Test each trigger
    result_next = coordinator._check_rule_triggers("next task please")
    if result_next and result_next["trigger"] == "next":
        print("\n✅ 'next' rule matched")
    else:
        print("\n❌ 'next' rule should have matched")
        return False

    result_skip = coordinator._check_rule_triggers("skip this one")
    if result_skip and result_skip["trigger"] == "skip":
        print("✅ 'skip' rule matched")
    else:
        print("❌ 'skip' rule should have matched")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 6: No match for non-trigger words
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 6: No match for non-trigger words")
    print("=" * 60)

    result = coordinator._check_rule_triggers("show me the tasks")
    if result is None:
        print("\n✅ No match for 'show me the tasks'")
    else:
        print(f"\n❌ Should not match: {result}")
        return False

    result = coordinator._check_rule_triggers("what is the status?")
    if result is None:
        print("✅ No match for 'what is the status?'")
    else:
        print(f"❌ Should not match: {result}")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 7: Confidence filtering
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 7: Confidence filtering")
    print("=" * 60)

    # Add low confidence rule
    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="maybe",
        action="tentative_action",
        source="inferred",
        confidence=0.3  # Below min_confidence threshold
    )
    print("\n✓ Added low confidence rule: maybe → tentative_action (confidence: 0.3)")

    result = coordinator._check_rule_triggers("maybe do this")
    if result is None:
        print("\n✅ Low confidence rule (0.3) not matched (min: 0.5)")
    else:
        print(f"\n❌ Low confidence rule should be filtered out: {result}")
        return False

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    coordinator.memory.long_term.delete_many({"user_id": user_id})
    coordinator.memory.clear_session(session_id)
    print("✓ Cleaned up test data")

    print("\n" + "=" * 60)
    print("✅ ALL RULE TRIGGER TESTS PASSED!")
    print("=" * 60)

    print("\nKey Features Verified:")
    print("  ✓ Rules loaded from Procedural Memory (long-term)")
    print("  ✓ Case-insensitive trigger matching")
    print("  ✓ Triggers matched within sentences")
    print("  ✓ Multiple rules supported")
    print("  ✓ Non-trigger words don't match")
    print("  ✓ Confidence filtering (min 0.5)")

    print("\n💡 Benefits:")
    print("  • Rules persist across sessions")
    print("  • Natural language trigger matching")
    print("  • Confidence-based filtering")
    print("  • Clear action mapping")

    return True


if __name__ == "__main__":
    success = test_rule_triggers()
    if not success:
        print("\n❌ Some rule trigger tests failed")
        exit(1)
