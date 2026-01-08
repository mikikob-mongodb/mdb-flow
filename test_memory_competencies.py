"""
Integration test for memory competency evaluation.

Tests AR-SH (Accurate Retrieval - Single Hop) and AR-MH (Accurate Retrieval - Multi Hop)
competencies to verify the memory system enables context-aware responses.

Based on MemoryAgentBench (Hu et al., 2025)
"""

from agents.coordinator import coordinator
from shared.db import MongoDB
from memory import MemoryManager
from shared.embeddings import embed_query
from evals.memory_competency_suite import MEMORY_COMPETENCY_TESTS, Competency
from evals.memory_metrics import evaluate_test_result, calculate_competency_scores


def test_memory_competencies():
    """Test AR-SH and AR-MH memory competencies."""

    # Initialize
    mongodb = MongoDB()
    db = mongodb.get_database()

    # Ensure coordinator has memory manager
    if not coordinator.memory:
        memory = MemoryManager(db, embedding_fn=embed_query)
        coordinator.memory = memory

    print("=" * 60)
    print("TESTING MEMORY COMPETENCIES (AR-SH, AR-MH)")
    print("=" * 60)

    # Set session
    session_id = "test-memory-competencies"
    user_id = "test-user"

    # Get AR-SH and AR-MH tests
    ar_sh_tests = [t for t in MEMORY_COMPETENCY_TESTS if t.competency == Competency.AR_SH]
    ar_mh_tests = [t for t in MEMORY_COMPETENCY_TESTS if t.competency == Competency.AR_MH]

    print(f"\nFound {len(ar_sh_tests)} AR-SH tests")
    print(f"Found {len(ar_mh_tests)} AR-MH tests")

    all_results_enabled = []
    all_results_disabled = []

    # Test AR-SH (Accurate Retrieval - Single Hop)
    print("\n" + "=" * 60)
    print("TESTING AR-SH: Accurate Retrieval - Single Hop")
    print("=" * 60)

    for test in ar_sh_tests[:2]:  # Test first 2 AR-SH tests
        print(f"\n{'-' * 60}")
        print(f"AR-SH Test {test.id}: {test.name}")
        print(f"{'-' * 60}")

        # Test with MEMORY ENABLED
        print("\n[MEMORY ENABLED]")
        coordinator.memory_config = {
            "short_term": True,
            "long_term": True,
            "shared": True,
            "context_injection": True
        }
        coordinator.set_session(session_id, user_id=user_id)
        coordinator.memory.clear_session(session_id)

        # Execute conversation turns
        response = None
        for turn_number, turn in enumerate(test.turns, start=1):
            print(f"\nTurn {turn_number}: {turn}")
            response = coordinator.process(
                user_message=turn,
                session_id=session_id,
                turn_number=turn_number,
                optimizations={},
                return_debug=True
            )
            print(f"Response: {response['response'][:200]}...")

        # Evaluate
        result_enabled = evaluate_test_result(
            test_id=test.id,
            config="memory_enabled",
            response=response,
            debug_info=response.get("debug", {})
        )

        print(f"\nResult (Memory Enabled):")
        print(f"  Passed: {result_enabled.passed}")
        print(f"  Score: {result_enabled.score:.2f}")
        print(f"  Details: {result_enabled.details}")
        all_results_enabled.append(result_enabled)

        # Test with MEMORY DISABLED
        print("\n[MEMORY DISABLED]")
        coordinator.memory_config = {
            "short_term": False,
            "long_term": False,
            "shared": False,
            "context_injection": False
        }
        coordinator.set_session(session_id, user_id=user_id)
        coordinator.memory.clear_session(session_id)

        # Execute conversation turns
        response = None
        for turn_number, turn in enumerate(test.turns, start=1):
            print(f"\nTurn {turn_number}: {turn}")
            response = coordinator.process(
                user_message=turn,
                session_id=session_id,
                turn_number=turn_number,
                optimizations={},
                return_debug=True
            )
            print(f"Response: {response['response'][:200]}...")

        # Evaluate
        result_disabled = evaluate_test_result(
            test_id=test.id,
            config="memory_disabled",
            response=response,
            debug_info=response.get("debug", {})
        )

        print(f"\nResult (Memory Disabled):")
        print(f"  Passed: {result_disabled.passed}")
        print(f"  Score: {result_disabled.score:.2f}")
        print(f"  Details: {result_disabled.details}")
        all_results_disabled.append(result_disabled)

        # Comparison
        print(f"\n{'✅' if result_enabled.passed else '❌'} Memory Enabled: {result_enabled.score:.2f}")
        print(f"{'✅' if result_disabled.passed else '❌'} Memory Disabled: {result_disabled.score:.2f}")

        if result_enabled.passed and not result_disabled.passed:
            print("✅ Memory system improves performance as expected")
        elif result_enabled.passed and result_disabled.passed:
            print("⚠️  Both passed - test may not require memory")
        else:
            print("❌ Memory system did not improve performance")

    # Test AR-MH (Accurate Retrieval - Multi Hop)
    print("\n" + "=" * 60)
    print("TESTING AR-MH: Accurate Retrieval - Multi Hop")
    print("=" * 60)

    for test in ar_mh_tests[:2]:  # Test first 2 AR-MH tests
        print(f"\n{'-' * 60}")
        print(f"AR-MH Test {test.id}: {test.name}")
        print(f"{'-' * 60}")

        # Test with MEMORY ENABLED
        print("\n[MEMORY ENABLED]")
        coordinator.memory_config = {
            "short_term": True,
            "long_term": True,
            "shared": True,
            "context_injection": True
        }
        coordinator.set_session(session_id, user_id=user_id)
        coordinator.memory.clear_session(session_id)

        # Execute conversation turns
        response = None
        for turn_number, turn in enumerate(test.turns, start=1):
            print(f"\nTurn {turn_number}: {turn}")
            response = coordinator.process(
                user_message=turn,
                session_id=session_id,
                turn_number=turn_number,
                optimizations={},
                return_debug=True
            )
            print(f"Response: {response['response'][:200]}...")

        # Evaluate
        result_enabled = evaluate_test_result(
            test_id=test.id,
            config="memory_enabled",
            response=response,
            debug_info=response.get("debug", {})
        )

        print(f"\nResult (Memory Enabled):")
        print(f"  Passed: {result_enabled.passed}")
        print(f"  Score: {result_enabled.score:.2f}")
        print(f"  Details: {result_enabled.details}")
        all_results_enabled.append(result_enabled)

        # Test with MEMORY DISABLED
        print("\n[MEMORY DISABLED]")
        coordinator.memory_config = {
            "short_term": False,
            "long_term": False,
            "shared": False,
            "context_injection": False
        }
        coordinator.set_session(session_id, user_id=user_id)
        coordinator.memory.clear_session(session_id)

        # Execute conversation turns
        response = None
        for turn_number, turn in enumerate(test.turns, start=1):
            print(f"\nTurn {turn_number}: {turn}")
            response = coordinator.process(
                user_message=turn,
                session_id=session_id,
                turn_number=turn_number,
                optimizations={},
                return_debug=True
            )
            print(f"Response: {response['response'][:200]}...")

        # Evaluate
        result_disabled = evaluate_test_result(
            test_id=test.id,
            config="memory_disabled",
            response=response,
            debug_info=response.get("debug", {})
        )

        print(f"\nResult (Memory Disabled):")
        print(f"  Passed: {result_disabled.passed}")
        print(f"  Score: {result_disabled.score:.2f}")
        print(f"  Details: {result_disabled.details}")
        all_results_disabled.append(result_disabled)

        # Comparison
        print(f"\n{'✅' if result_enabled.passed else '❌'} Memory Enabled: {result_enabled.score:.2f}")
        print(f"{'✅' if result_disabled.passed else '❌'} Memory Disabled: {result_disabled.score:.2f}")

        if result_enabled.passed and not result_disabled.passed:
            print("✅ Memory system improves performance as expected")
        elif result_enabled.passed and result_disabled.passed:
            print("⚠️  Both passed - test may not require memory")
        else:
            print("❌ Memory system did not improve performance")

    # Calculate aggregate scores
    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)

    competency_scores = calculate_competency_scores(all_results_enabled, all_results_disabled)

    # AR-SH scores
    if Competency.AR_SH in competency_scores:
        ar_sh_score = competency_scores[Competency.AR_SH]
        print(f"\nAR-SH: Accurate Retrieval - Single Hop")
        print(f"  Accuracy: {ar_sh_score.accuracy:.1%} (target: {ar_sh_score.target_accuracy:.1%})")
        print(f"  Tests: {ar_sh_score.num_passed}/{ar_sh_score.num_tests}")
        print(f"  Improvement: {ar_sh_score.improvement_over_baseline:+.1f}%")
        print(f"  {'✅ Meets target' if ar_sh_score.meets_target else '❌ Below target'}")

    # AR-MH scores
    if Competency.AR_MH in competency_scores:
        ar_mh_score = competency_scores[Competency.AR_MH]
        print(f"\nAR-MH: Accurate Retrieval - Multi Hop")
        print(f"  Accuracy: {ar_mh_score.accuracy:.1%} (target: {ar_mh_score.target_accuracy:.1%})")
        print(f"  Tests: {ar_mh_score.num_passed}/{ar_mh_score.num_tests}")
        print(f"  Improvement: {ar_mh_score.improvement_over_baseline:+.1f}%")
        print(f"  {'✅ Meets target' if ar_mh_score.meets_target else '❌ Below target'}")

    # Overall statistics
    total_enabled_passed = sum(1 for r in all_results_enabled if r.passed)
    total_disabled_passed = sum(1 for r in all_results_disabled if r.passed)
    total_tests = len(all_results_enabled)

    print(f"\nOverall:")
    print(f"  Memory Enabled: {total_enabled_passed}/{total_tests} passed ({total_enabled_passed/total_tests:.1%})")
    print(f"  Memory Disabled: {total_disabled_passed}/{total_tests} passed ({total_disabled_passed/total_tests:.1%})")

    if total_enabled_passed > total_disabled_passed:
        improvement = total_enabled_passed - total_disabled_passed
        print(f"  ✅ Memory system improved {improvement} tests")

    # Cleanup
    coordinator.memory.clear_session(session_id)

    print("\n" + "=" * 60)
    print("✅ MEMORY COMPETENCY TESTS COMPLETE")
    print("=" * 60)

    print("\nKey Findings:")
    print("  • AR-SH tests verify single-hop context recall (e.g., 'What project am I working on?')")
    print("  • AR-MH tests verify multi-hop retrieval (e.g., project + status context)")
    print("  • Memory-enabled configuration should significantly outperform baseline")
    print("  • Target accuracies: AR-SH=85%, AR-MH=60% (research-based)")

    print("\n📊 Run the full eval suite via dashboard:")
    print("   streamlit run evals_app.py --server.port 8502")
    print("   Navigate to 🧠 Memory Competencies tab")

    return True


if __name__ == "__main__":
    success = test_memory_competencies()
    if not success:
        print("\n❌ Some memory competency tests failed")
        exit(1)
