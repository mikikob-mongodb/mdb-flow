"""
Memory competency metrics calculation.

Evaluates memory system performance across 10 competency dimensions:
- AR (Accurate Retrieval): AR-SH, AR-MH, AR-T
- TTL (Test-Time Learning): TTL-C, TTL-R, TTL-P
- LRU (Long-Range Understanding): LRU-S, LRU-P
- CR (Conflict Resolution): CR-SH, CR-MH

Based on MemoryAgentBench (Hu et al., 2025)
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

from evals.memory_competency_suite import (
    MEMORY_COMPETENCY_TESTS,
    COMPETENCY_TARGETS,
    Competency
)


@dataclass
class TestResult:
    """Result for a single test."""
    test_id: int
    competency: Competency
    config: str  # "memory_enabled" or "memory_disabled"
    passed: bool
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]


@dataclass
class CompetencyScore:
    """Aggregated score for a competency."""
    competency: Competency
    accuracy: float  # Proportion of tests passed
    num_tests: int
    num_passed: int
    target_accuracy: float
    meets_target: bool
    improvement_over_baseline: float  # Percentage improvement


def evaluate_test_result(
    test_id: int,
    config: str,
    response: Dict[str, Any],
    debug_info: Dict[str, Any]
) -> TestResult:
    """
    Evaluate a single test result against success criteria.

    Args:
        test_id: Test ID from MEMORY_COMPETENCY_TESTS
        config: "memory_enabled" or "memory_disabled"
        response: LLM response text
        debug_info: Debug info from coordinator (tool calls, memory ops, etc.)

    Returns:
        TestResult with pass/fail and score
    """
    # Find test definition
    test = next((t for t in MEMORY_COMPETENCY_TESTS if t.id == test_id), None)
    if not test:
        raise ValueError(f"Test {test_id} not found")

    # Get criteria for this config
    criteria = test.success_criteria.get(config, {})
    if not criteria:
        raise ValueError(f"No success criteria for config {config}")

    # Evaluate criteria
    checks = []
    details = {}

    # Check 1: must_contain (response text)
    if "must_contain" in criteria:
        for phrase in criteria["must_contain"]:
            found = phrase.lower() in response.get("response", "").lower()
            checks.append(found)
            details[f"contains_{phrase}"] = found

    # Check 2: must_not_contain (response text)
    if "must_not_contain" in criteria:
        for phrase in criteria["must_not_contain"]:
            not_found = phrase.lower() not in response.get("response", "").lower()
            checks.append(not_found)
            details[f"excludes_{phrase}"] = not_found

    # Check 3: context_read (memory operations)
    if "context_read" in criteria:
        expected = criteria["context_read"]
        actual = debug_info.get("memory_ops", {}).get("context_read", False)
        checks.append(actual == expected)
        details["context_read"] = actual

    # Check 4: context_written (memory operations)
    if "context_written" in criteria:
        expected = criteria["context_written"]
        actual = debug_info.get("memory_ops", {}).get("context_written", False)
        checks.append(actual == expected)
        details["context_written"] = actual

    # Check 5: action_recorded (memory operations)
    if "action_recorded" in criteria:
        expected = criteria["action_recorded"]
        actual = debug_info.get("memory_ops", {}).get("action_recorded", False)
        checks.append(actual == expected)
        details["action_recorded"] = actual

    # Check 6: tool_called (specific tool must be called)
    if "tool_called" in criteria:
        expected_tool = criteria["tool_called"]
        tools_called = [call["name"] for call in debug_info.get("tool_calls", [])]
        tool_was_called = expected_tool in tools_called
        checks.append(tool_was_called)
        details["tool_called"] = tools_called

    # Check 7: tool_params_must_include (tool parameters)
    if "tool_params_must_include" in criteria:
        expected_params = criteria["tool_params_must_include"]

        # Find the relevant tool call
        target_tool = criteria.get("tool_called", "get_tasks")
        tool_call = next(
            (call for call in debug_info.get("tool_calls", [])
             if call["name"] == target_tool),
            None
        )

        if tool_call:
            actual_params = tool_call.get("input", {})
            for param_name, expected_value in expected_params.items():
                actual_value = actual_params.get(param_name)

                # Fuzzy matching for strings
                if isinstance(expected_value, str) and isinstance(actual_value, str):
                    match = expected_value.lower() in actual_value.lower()
                else:
                    match = actual_value == expected_value

                checks.append(match)
                details[f"param_{param_name}"] = actual_value
        else:
            checks.append(False)
            details["tool_called"] = "not_called"

    # Check 8: tool_params_missing (parameters that should NOT be present)
    if "tool_params_missing" in criteria:
        missing_param = criteria["tool_params_missing"]

        # Find the relevant tool call
        target_tool = criteria.get("tool_called", "get_tasks")
        tool_call = next(
            (call for call in debug_info.get("tool_calls", [])
             if call["name"] == target_tool),
            None
        )

        if tool_call:
            actual_params = tool_call.get("input", {})
            param_is_missing = missing_param not in actual_params
            checks.append(param_is_missing)
            details[f"missing_{missing_param}"] = param_is_missing
        else:
            # If tool not called, param is missing (counts as pass)
            checks.append(True)
            details[f"missing_{missing_param}"] = True

    # Check 9: rule_triggered (rule learning)
    if "rule_triggered" in criteria:
        expected_trigger = criteria["rule_triggered"]
        actual_trigger = debug_info.get("memory_ops", {}).get("rule_triggered")

        if expected_trigger and actual_trigger:
            match = expected_trigger.lower() in actual_trigger.lower()
        elif not expected_trigger and not actual_trigger:
            match = True
        else:
            match = False

        checks.append(match)
        details["rule_triggered"] = actual_trigger

    # Check 10: result_count (number of results)
    if "result_count" in criteria:
        expected_count = criteria["result_count"]

        # Extract from response or tool results
        # Try to find task count in response
        match = re.search(r'(\d+)\s+(?:tasks?|results?)', response.get("response", ""))
        actual_count = int(match.group(1)) if match else None

        if actual_count is not None:
            if isinstance(expected_count, dict):
                # Range check
                min_count = expected_count.get("min", 0)
                max_count = expected_count.get("max", float('inf'))
                in_range = min_count <= actual_count <= max_count
                checks.append(in_range)
            else:
                # Exact count
                checks.append(actual_count == expected_count)
        else:
            checks.append(False)

        details["result_count"] = actual_count

    # Calculate score
    if checks:
        score = sum(checks) / len(checks)
        passed = all(checks)
    else:
        # No criteria defined - default to pass
        score = 1.0
        passed = True

    return TestResult(
        test_id=test_id,
        competency=test.competency,
        config=config,
        passed=passed,
        score=score,
        details=details
    )


def calculate_competency_scores(
    results_memory_enabled: List[TestResult],
    results_memory_disabled: List[TestResult]
) -> Dict[Competency, CompetencyScore]:
    """
    Calculate aggregated scores by competency.

    Args:
        results_memory_enabled: Test results with memory enabled
        results_memory_disabled: Test results with memory disabled (baseline)

    Returns:
        Dict mapping competency to CompetencyScore
    """
    scores = {}

    # Group results by competency
    by_competency_enabled = defaultdict(list)
    by_competency_disabled = defaultdict(list)

    for result in results_memory_enabled:
        by_competency_enabled[result.competency].append(result)

    for result in results_memory_disabled:
        by_competency_disabled[result.competency].append(result)

    # Calculate scores for each competency
    for competency in Competency:
        enabled_results = by_competency_enabled.get(competency, [])
        disabled_results = by_competency_disabled.get(competency, [])

        if not enabled_results:
            continue

        # Calculate accuracy for memory-enabled
        num_tests = len(enabled_results)
        num_passed = sum(1 for r in enabled_results if r.passed)
        accuracy = num_passed / num_tests if num_tests > 0 else 0.0

        # Calculate baseline accuracy
        baseline_accuracy = 0.0
        if disabled_results:
            baseline_passed = sum(1 for r in disabled_results if r.passed)
            baseline_accuracy = baseline_passed / len(disabled_results)

        # Get target
        target = COMPETENCY_TARGETS.get(competency, {})
        target_accuracy = target.get("accuracy", 0.8)

        # Calculate improvement
        improvement = 0.0
        if baseline_accuracy > 0:
            improvement = ((accuracy - baseline_accuracy) / baseline_accuracy) * 100

        scores[competency] = CompetencyScore(
            competency=competency,
            accuracy=accuracy,
            num_tests=num_tests,
            num_passed=num_passed,
            target_accuracy=target_accuracy,
            meets_target=accuracy >= target_accuracy,
            improvement_over_baseline=improvement
        )

    return scores


def calculate_overall_metrics(
    competency_scores: Dict[Competency, CompetencyScore]
) -> Dict[str, Any]:
    """
    Calculate overall memory system metrics.

    Returns:
        Dict with overall statistics
    """
    if not competency_scores:
        return {}

    total_tests = sum(score.num_tests for score in competency_scores.values())
    total_passed = sum(score.num_passed for score in competency_scores.values())
    overall_accuracy = total_passed / total_tests if total_tests > 0 else 0.0

    num_competencies_met = sum(
        1 for score in competency_scores.values()
        if score.meets_target
    )
    total_competencies = len(competency_scores)

    avg_improvement = sum(
        score.improvement_over_baseline
        for score in competency_scores.values()
    ) / total_competencies if total_competencies > 0 else 0.0

    # Group by category
    ar_scores = [s for c, s in competency_scores.items() if c.name.startswith("AR_")]
    ttl_scores = [s for c, s in competency_scores.items() if c.name.startswith("TTL_")]
    lru_scores = [s for c, s in competency_scores.items() if c.name.startswith("LRU_")]
    cr_scores = [s for c, s in competency_scores.items() if c.name.startswith("CR_")]

    def avg_accuracy(scores):
        if not scores:
            return 0.0
        return sum(s.accuracy for s in scores) / len(scores)

    return {
        "overall_accuracy": overall_accuracy,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "competencies_met": num_competencies_met,
        "total_competencies": total_competencies,
        "competency_target_rate": num_competencies_met / total_competencies if total_competencies > 0 else 0.0,
        "avg_improvement_over_baseline": avg_improvement,
        "category_scores": {
            "AR": avg_accuracy(ar_scores),
            "TTL": avg_accuracy(ttl_scores),
            "LRU": avg_accuracy(lru_scores),
            "CR": avg_accuracy(cr_scores)
        }
    }


def format_competency_report(
    competency_scores: Dict[Competency, CompetencyScore],
    overall_metrics: Dict[str, Any]
) -> str:
    """
    Format competency scores as human-readable report.

    Returns:
        Formatted markdown report
    """
    lines = []

    lines.append("# Memory Competency Evaluation Report")
    lines.append("")

    # Overall summary
    lines.append("## Overall Performance")
    lines.append("")
    lines.append(f"- **Overall Accuracy**: {overall_metrics['overall_accuracy']:.1%}")
    lines.append(f"- **Tests Passed**: {overall_metrics['total_passed']}/{overall_metrics['total_tests']}")
    lines.append(f"- **Competencies Met Target**: {overall_metrics['competencies_met']}/{overall_metrics['total_competencies']} ({overall_metrics['competency_target_rate']:.1%})")
    lines.append(f"- **Avg Improvement Over Baseline**: {overall_metrics['avg_improvement_over_baseline']:.1f}%")
    lines.append("")

    # Category breakdown
    lines.append("## Performance by Category")
    lines.append("")
    for category, accuracy in overall_metrics["category_scores"].items():
        lines.append(f"- **{category}**: {accuracy:.1%}")
    lines.append("")

    # Individual competencies
    lines.append("## Individual Competencies")
    lines.append("")

    # Group by category
    categories = {
        "AR": "Accurate Retrieval",
        "TTL": "Test-Time Learning",
        "LRU": "Long-Range Understanding",
        "CR": "Conflict Resolution"
    }

    for category_prefix, category_name in categories.items():
        category_competencies = [
            (c, s) for c, s in competency_scores.items()
            if c.name.startswith(category_prefix)
        ]

        if not category_competencies:
            continue

        lines.append(f"### {category_name}")
        lines.append("")

        for competency, score in sorted(category_competencies):
            status = "✅" if score.meets_target else "⚠️"
            lines.append(f"**{status} {competency.value}**")
            lines.append(f"- Accuracy: {score.accuracy:.1%} (target: {score.target_accuracy:.1%})")
            lines.append(f"- Tests: {score.num_passed}/{score.num_tests} passed")
            lines.append(f"- Improvement: {score.improvement_over_baseline:+.1f}%")
            lines.append("")

    return "\n".join(lines)


def export_results_csv(
    results: List[TestResult],
    filepath: str
):
    """
    Export test results to CSV for analysis.

    Args:
        results: List of TestResult objects
        filepath: Output CSV path
    """
    import csv

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "test_id",
            "competency",
            "config",
            "passed",
            "score",
            "details"
        ])

        # Rows
        for result in results:
            writer.writerow([
                result.test_id,
                result.competency.value,
                result.config,
                result.passed,
                result.score,
                str(result.details)
            ])
