#!/usr/bin/env python3
"""
Test multi-step intent classification in Coordinator.

Usage:
    python scripts/test_multi_step_intent.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import MongoDB
from memory.manager import MemoryManager
from shared.embeddings import embed_query
from agents.coordinator import CoordinatorAgent


def test_multi_step_classification():
    """Test the multi-step intent classification."""

    print("=" * 70)
    print("Multi-Step Intent Classification Test")
    print("=" * 70)

    # Initialize coordinator
    print("\n🔧 Initializing Coordinator...")
    mongodb = MongoDB()
    db = mongodb.get_database()
    memory = MemoryManager(db, embedding_fn=embed_query)

    coordinator = CoordinatorAgent(
        memory_manager=memory,
        db=db
    )
    coordinator.user_id = "test-user"
    coordinator.session_id = "test-session"
    print("✓ Coordinator initialized")

    # Test cases
    test_cases = [
        # Multi-step requests
        {
            "message": "Research the gaming market and create a GTM project with tasks",
            "expected_multi_step": True,
            "expected_steps": 3
        },
        {
            "message": "Look up MongoDB features then make a project for it",
            "expected_multi_step": True,
            "expected_steps": 2
        },
        {
            "message": "Find information about AI trends and then create tasks",
            "expected_multi_step": True,
            "expected_steps": 2
        },
        # Single-step requests (should not trigger multi-step)
        {
            "message": "Create a new GTM project",
            "expected_multi_step": False,
            "expected_steps": 0
        },
        {
            "message": "Research the healthcare market",
            "expected_multi_step": False,
            "expected_steps": 0
        },
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"Test Case {i}")
        print(f"{'=' * 70}")
        print(f"\n📝 Message: \"{test['message']}\"")
        print(f"Expected multi-step: {test['expected_multi_step']}")

        # Classify
        result = coordinator._classify_multi_step_intent(test['message'])

        is_multi_step = result.get("is_multi_step", False)
        steps = result.get("steps", [])

        print(f"\n🔍 Result:")
        print(f"  Is multi-step: {is_multi_step}")
        print(f"  Number of steps: {len(steps)}")

        if steps:
            print(f"\n  Steps:")
            for j, step in enumerate(steps, 1):
                print(f"    {j}. [{step['intent']}] {step['description']}")

        # Validate
        passed = True
        if is_multi_step != test['expected_multi_step']:
            print(f"\n  ❌ FAILED: Expected multi-step={test['expected_multi_step']}, got {is_multi_step}")
            passed = False
        elif test['expected_multi_step'] and len(steps) != test['expected_steps']:
            print(f"\n  ⚠️  WARNING: Expected {test['expected_steps']} steps, got {len(steps)}")
            # Don't fail on this - LLM might reasonably parse differently

        if passed:
            print(f"\n  ✓ PASSED")

        results.append({
            "message": test['message'],
            "passed": passed,
            "result": result
        })

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)

    print(f"\nTests passed: {passed_count}/{total_count}")

    for i, result in enumerate(results, 1):
        status = "✓" if result["passed"] else "❌"
        print(f"\n{status} Test {i}: {result['message'][:60]}...")

    print("\n" + "=" * 70)

    if passed_count == total_count:
        print("✅ ALL TESTS PASSED")
        return True
    else:
        print(f"⚠️  {total_count - passed_count} TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = test_multi_step_classification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
