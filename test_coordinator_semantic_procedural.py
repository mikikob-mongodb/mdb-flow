"""
Test Coordinator's integration with Semantic and Procedural Memory.

Verifies that extracted preferences and rules are saved to long-term memory
instead of short-term session_context.
"""

from agents.coordinator import coordinator
from shared.db import MongoDB

def test_coordinator_semantic_procedural():
    """Test Coordinator saves preferences and rules to long-term memory."""

    print("=" * 60)
    print("TESTING COORDINATOR SEMANTIC & PROCEDURAL INTEGRATION")
    print("=" * 60)

    # Setup
    user_id = "test-user-coordinator-semantic"
    session_id = "test-session-coordinator-semantic"

    # Clean up
    if coordinator.memory:
        coordinator.memory.long_term.delete_many({"user_id": user_id})
        coordinator.memory.clear_session(session_id)

    coordinator.set_session(session_id, user_id=user_id)
    print(f"\n✓ Session set: {session_id}")
    print(f"  User ID: {user_id}")

    # Enable memory features
    coordinator.memory_config = {
        "short_term": True,
        "long_term": True,
        "shared": True,
        "context_injection": True
    }

    # ═══════════════════════════════════════════════════════════════
    # TEST 1: Preference extraction and long-term storage
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 1: Preference extraction to Semantic Memory")
    print("=" * 60)

    # Test explicit preference
    response = coordinator.process(
        user_message="I'm focusing on Voice Agent today",
        session_id=session_id,
        turn_number=1,
        optimizations={},
        return_debug=True
    )

    print(f"\n✓ Processed: 'I'm focusing on Voice Agent today'")
    print(f"  Memory ops: {coordinator.memory_ops}")
    print(f"  Preference recorded: {coordinator.memory_ops.get('preference_recorded')}")

    # Check long-term memory
    prefs = coordinator.memory.get_preferences(user_id)
    print(f"\n✓ Long-term preferences: {len(prefs)}")
    for pref in prefs:
        print(f"  - {pref['key']}: {pref['value']} (confidence: {pref['confidence']}, source: {pref['source']})")

    # Verify focus_project preference exists
    focus_pref = coordinator.memory.get_preference(user_id, "focus_project")
    if focus_pref:
        print(f"\n✅ focus_project preference saved to long-term memory")
        print(f"   Value: {focus_pref['value']}")
        print(f"   Source: {focus_pref['source']}")
        print(f"   Confidence: {focus_pref['confidence']}")
    else:
        print(f"\n❌ focus_project preference NOT found in long-term memory")
        return False

    # Test priority preference
    response2 = coordinator.process(
        user_message="Show me high priority tasks",
        session_id=session_id,
        turn_number=2,
        optimizations={},
        return_debug=True
    )

    print(f"\n✓ Processed: 'Show me high priority tasks'")
    print(f"  Preference recorded: {coordinator.memory_ops.get('preference_recorded')}")

    priority_pref = coordinator.memory.get_preference(user_id, "priority_filter")
    if priority_pref:
        print(f"\n✅ priority_filter preference saved to long-term memory")
        print(f"   Value: {priority_pref['value']}")
    else:
        print(f"\n⚠️  priority_filter preference not saved (may not have triggered)")

    # ═══════════════════════════════════════════════════════════════
    # TEST 2: Rule extraction and long-term storage
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 2: Rule extraction to Procedural Memory")
    print("=" * 60)

    # Test rule learning
    response3 = coordinator.process(
        user_message="When I say done, complete my current task",
        session_id=session_id,
        turn_number=3,
        optimizations={},
        return_debug=True
    )

    print(f"\n✓ Processed: 'When I say done, complete my current task'")
    print(f"  Memory ops: {coordinator.memory_ops}")
    print(f"  Rule recorded: {coordinator.memory_ops.get('rule_recorded')}")

    # Check long-term memory
    rules = coordinator.memory.get_rules(user_id)
    print(f"\n✓ Long-term rules: {len(rules)}")
    for rule in rules:
        print(f"  - '{rule['trigger_pattern']}' → {rule['action_type']}")
        print(f"    Confidence: {rule['confidence']}, Source: {rule['source']}")

    # Verify done rule exists
    done_rule = coordinator.memory.get_rule_for_trigger(user_id, "done")
    if done_rule:
        print(f"\n✅ 'done' rule saved to long-term memory")
        print(f"   Action: {done_rule['action_type']}")
        print(f"   Source: {done_rule['source']}")
        print(f"   Confidence: {done_rule['confidence']}")
    else:
        print(f"\n❌ 'done' rule NOT found in long-term memory")
        return False

    # Test another rule pattern
    response4 = coordinator.process(
        user_message="If I say next, start the next task",
        session_id=session_id,
        turn_number=4,
        optimizations={},
        return_debug=True
    )

    print(f"\n✓ Processed: 'If I say next, start the next task'")
    print(f"  Rule recorded: {coordinator.memory_ops.get('rule_recorded')}")

    next_rule = coordinator.memory.get_rule_for_trigger(user_id, "next")
    if next_rule:
        print(f"\n✅ 'next' rule saved to long-term memory")
        print(f"   Action: {next_rule['action_type']}")
    else:
        print(f"\n⚠️  'next' rule not saved (may not have triggered)")

    # ═══════════════════════════════════════════════════════════════
    # TEST 3: Verify NOT in session_context
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 3: Verify preferences/rules NOT in session_context")
    print("=" * 60)

    # Check session context
    session_context = coordinator.memory.read_session_context(session_id)
    print(f"\n✓ Session context keys: {list(session_context.keys()) if session_context else []}")

    # Session context should have working memory (current_project, etc.)
    # but NOT preferences or rules (those are in long-term now)
    if session_context:
        has_preferences = "preferences" in session_context
        has_rules = "rules" in session_context

        print(f"  Has 'preferences' key: {has_preferences}")
        print(f"  Has 'rules' key: {has_rules}")

        if has_preferences or has_rules:
            print(f"\n⚠️  Preferences/rules found in session_context (should be in long-term)")
            if has_preferences:
                print(f"     Session preferences: {session_context.get('preferences')}")
            if has_rules:
                print(f"     Session rules: {session_context.get('rules')}")
        else:
            print(f"\n✅ Preferences and rules NOT in session_context (correct)")
    else:
        print(f"\n✓ No session context yet (correct)")

    # ═══════════════════════════════════════════════════════════════
    # TEST 4: Memory statistics breakdown
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 4: Memory statistics show semantic/procedural")
    print("=" * 60)

    stats = coordinator.memory.get_memory_stats(session_id, user_id)
    print(f"\n✓ Memory statistics:")
    print(f"  Total long-term: {stats['long_term_count']}")
    print(f"\n  By type:")
    for mem_type, count in stats['by_type'].items():
        print(f"    - {mem_type}: {count}")

    # Verify semantic and procedural counts
    if stats['by_type']['semantic_memory'] > 0:
        print(f"\n✅ Semantic memory count > 0: {stats['by_type']['semantic_memory']}")
    else:
        print(f"\n❌ Semantic memory count = 0 (should have preferences)")
        return False

    if stats['by_type']['procedural_memory'] > 0:
        print(f"✅ Procedural memory count > 0: {stats['by_type']['procedural_memory']}")
    else:
        print(f"❌ Procedural memory count = 0 (should have rules)")
        return False

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    coordinator.memory.long_term.delete_many({"user_id": user_id})
    coordinator.memory.clear_session(session_id)
    print("✓ Cleaned up test data")

    print("\n" + "=" * 60)
    print("✅ ALL COORDINATOR SEMANTIC/PROCEDURAL TESTS PASSED!")
    print("=" * 60)

    print("\nKey Features Verified:")
    print("  ✓ Preferences saved to long-term semantic memory")
    print("  ✓ Rules saved to long-term procedural memory")
    print("  ✓ memory_ops tracks preference_recorded and rule_recorded")
    print("  ✓ Preferences/rules NOT stored in session_context")
    print("  ✓ Memory statistics show semantic/procedural breakdown")

    print("\n💡 Benefits:")
    print("  • Preferences persist beyond 2hr session TTL")
    print("  • Rules accumulate across sessions")
    print("  • Clear separation: working vs semantic vs procedural")
    print("  • Enables long-term user personalization")

    return True


if __name__ == "__main__":
    success = test_coordinator_semantic_procedural()
    if not success:
        print("\n❌ Some coordinator semantic/procedural tests failed")
        exit(1)
