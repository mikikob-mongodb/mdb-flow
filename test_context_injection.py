"""
Test context injection with semantic and procedural memory.

Verifies that _build_context_injection() loads preferences and rules
from long-term memory and includes them in the system prompt.
"""

from agents.coordinator import coordinator

def test_context_injection():
    """Test context injection with long-term memory."""

    print("=" * 60)
    print("TESTING CONTEXT INJECTION WITH LONG-TERM MEMORY")
    print("=" * 60)

    # Setup
    user_id = "test-user-context-injection"
    session_id = "test-session-context-injection"

    # Clean up
    if coordinator.memory:
        coordinator.memory.long_term.delete_many({"user_id": user_id})
        coordinator.memory.clear_session(session_id)

    coordinator.set_session(session_id, user_id=user_id)
    print(f"\n✓ Session set: {session_id}")
    print(f"  User ID: {user_id}")

    # Enable context injection
    coordinator.memory_config = {
        "short_term": True,
        "long_term": True,
        "shared": True,
        "context_injection": True
    }

    # ═══════════════════════════════════════════════════════════════
    # TEST 1: Empty injection (no memory yet)
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 1: Empty injection (no memory)")
    print("=" * 60)

    injection = coordinator._build_context_injection()
    print(f"\n✓ Injection length: {len(injection)} chars")
    if injection:
        print(f"  Empty check failed: {injection[:200]}")
    else:
        print("  ✅ No injection when no memory exists")

    # ═══════════════════════════════════════════════════════════════
    # TEST 2: Add preferences to long-term memory
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 2: Inject preferences from Semantic Memory")
    print("=" * 60)

    # Add some preferences
    coordinator.memory.record_preference(
        user_id=user_id,
        key="focus_project",
        value="Voice Agent",
        source="explicit",
        confidence=0.9
    )
    print("\n✓ Added preference: focus_project = Voice Agent")

    coordinator.memory.record_preference(
        user_id=user_id,
        key="priority_filter",
        value="high",
        source="explicit",
        confidence=0.85
    )
    print("✓ Added preference: priority_filter = high")

    injection = coordinator._build_context_injection()
    print(f"\n✓ Injection:\n{injection}")

    # Verify preferences appear
    if "User preferences (Semantic Memory):" in injection:
        print("\n✅ Semantic Memory section present")
    else:
        print("\n❌ Semantic Memory section missing")
        return False

    if "focus_project: Voice Agent" in injection:
        print("✅ focus_project preference included")
    else:
        print("❌ focus_project preference missing")
        return False

    if "priority_filter: high" in injection:
        print("✅ priority_filter preference included")
    else:
        print("❌ priority_filter preference missing")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 3: Add rules to long-term memory
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 3: Inject rules from Procedural Memory")
    print("=" * 60)

    # Add some rules
    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="done",
        action="complete_current_task",
        source="explicit",
        confidence=0.9
    )
    print("\n✓ Added rule: done → complete_current_task")

    coordinator.memory.record_rule(
        user_id=user_id,
        trigger="next",
        action="start_next_task",
        source="explicit",
        confidence=0.85
    )
    print("✓ Added rule: next → start_next_task")

    injection = coordinator._build_context_injection()
    print(f"\n✓ Injection:\n{injection}")

    # Verify rules appear
    if "User rules (Procedural Memory):" in injection:
        print("\n✅ Procedural Memory section present")
    else:
        print("\n❌ Procedural Memory section missing")
        return False

    if 'When user says "done" → complete the current task' in injection:
        print("✅ 'done' rule included with correct description")
    else:
        print("❌ 'done' rule missing or incorrectly formatted")
        return False

    if 'When user says "next" → start the next task' in injection:
        print("✅ 'next' rule included with correct description")
    else:
        print("❌ 'next' rule missing or incorrectly formatted")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 4: Add working memory (short-term)
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 4: Inject working memory (short-term)")
    print("=" * 60)

    # Add working memory
    coordinator.memory.update_session_context(
        session_id=session_id,
        updates={
            "current_project": "Voice Agent",
            "current_task": "Implement speech recognition",
            "last_action": "start"
        }
    )
    print("\n✓ Added working memory: current_project, current_task, last_action")

    injection = coordinator._build_context_injection()
    print(f"\n✓ Injection:\n{injection}")

    # Verify working memory appears
    if "Current project: Voice Agent" in injection:
        print("\n✅ Working memory: current_project included")
    else:
        print("\n❌ Working memory: current_project missing")
        return False

    if "Current task: Implement speech recognition" in injection:
        print("✅ Working memory: current_task included")
    else:
        print("❌ Working memory: current_task missing")
        return False

    if "Last action: start" in injection:
        print("✅ Working memory: last_action included")
    else:
        print("❌ Working memory: last_action missing")
        return False

    # ═══════════════════════════════════════════════════════════════
    # TEST 5: Verify tag name and instructions
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("TEST 5: Verify tag and instructions")
    print("=" * 60)

    if "<memory_context>" in injection and "</memory_context>" in injection:
        print("\n✅ <memory_context> tags present")
    else:
        print("\n❌ <memory_context> tags missing")
        return False

    if "Filter queries to the current project when relevant" in injection:
        print("✅ Usage instructions included")
    else:
        print("❌ Usage instructions missing")
        return False

    if "Do NOT mention the memory system to the user unless asked" in injection:
        print("✅ Privacy instruction included")
    else:
        print("❌ Privacy instruction missing")
        return False

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    coordinator.memory.long_term.delete_many({"user_id": user_id})
    coordinator.memory.clear_session(session_id)
    print("✓ Cleaned up test data")

    print("\n" + "=" * 60)
    print("✅ ALL CONTEXT INJECTION TESTS PASSED!")
    print("=" * 60)

    print("\nKey Features Verified:")
    print("  ✓ Preferences loaded from Semantic Memory (long-term)")
    print("  ✓ Rules loaded from Procedural Memory (long-term)")
    print("  ✓ Working memory loaded from session_context (short-term)")
    print("  ✓ Correct tag name: <memory_context>")
    print("  ✓ Clear separation of memory types in prompt")
    print("  ✓ Action descriptions mapped for rules")

    print("\n💡 Benefits:")
    print("  • LLM sees all 3 memory types in context")
    print("  • Persistent preferences and rules always available")
    print("  • Clear instructions on how to use memory")
    print("  • Privacy-preserving (don't mention memory system)")

    return True


if __name__ == "__main__":
    success = test_context_injection()
    if not success:
        print("\n❌ Some context injection tests failed")
        exit(1)
