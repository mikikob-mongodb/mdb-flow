"""Test runner for multi-config comparisons."""

import time
from typing import List, Optional, Callable

from evals.test_suite import TestQuery, InputType, TEST_SUITE, get_test_by_id
from evals.result import ConfigResult, TestComparison, ComparisonRun
from evals.configs import get_optimizations


class ComparisonRunner:
    """Runs tests across multiple configurations."""

    def __init__(self, coordinator, progress_callback: Callable = None):
        """
        Args:
            coordinator: The coordinator agent instance
            progress_callback: Optional callback(current, total, message)
        """
        self.coordinator = coordinator
        self.progress_callback = progress_callback
        self.conversation_history = []

    def clear_history(self):
        self.conversation_history = []

    def run_comparison(
        self,
        config_keys: List[str],
        test_ids: Optional[List[int]] = None,
        skip_voice: bool = True
    ) -> ComparisonRun:
        """
        Run all tests across multiple configurations.

        Args:
            config_keys: List of config keys to compare
            test_ids: Optional specific test IDs (default: all)
            skip_voice: Skip voice tests

        Returns:
            ComparisonRun with all results
        """
        # Determine which tests to run
        if test_ids:
            tests = [get_test_by_id(tid) for tid in test_ids if get_test_by_id(tid)]
        else:
            tests = [t for t in TEST_SUITE if not (skip_voice and t.input_type == InputType.VOICE)]

        # Create run
        run = ComparisonRun(configs_compared=config_keys)

        total_ops = len(tests) * len(config_keys)
        current_op = 0

        # For each test, run across all configs
        for test in tests:
            comparison = TestComparison(
                test_id=test.id,
                query=test.query,
                section=test.section.value,
                input_type=test.input_type.value,
                expected=test.expected
            )

            for config_key in config_keys:
                current_op += 1
                if self.progress_callback:
                    self.progress_callback(
                        current_op, total_ops,
                        f"Test #{test.id} with {config_key}"
                    )

                # Get optimizations for this config
                optimizations = get_optimizations(config_key)

                # Run the test
                result = self._run_single_test(test, optimizations, config_key)
                comparison.add_result(config_key, result)

            run.tests.append(comparison)

        # Compute summaries
        run.compute_summaries()

        return run

    def _run_single_test(
        self,
        test: TestQuery,
        optimizations: dict,
        config_key: str
    ) -> ConfigResult:
        """Run a single test with given optimizations."""

        # Reset history for non-dependent tests
        if test.depends_on is None:
            self.clear_history()

        if test.input_type == InputType.SLASH:
            return self._run_slash_test(test, config_key)
        else:
            return self._run_llm_test(test, optimizations, config_key)

    def _run_slash_test(self, test: TestQuery, config_key: str) -> ConfigResult:
        """Run slash command (no LLM, no optimizations apply)."""
        start_time = time.time()

        try:
            from ui.slash_commands import parse_slash_command, SlashCommandExecutor

            parsed = parse_slash_command(test.query)
            if not parsed:
                return ConfigResult(
                    config_key=config_key,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error="Failed to parse slash command",
                    result="fail"
                )

            executor = SlashCommandExecutor(self.coordinator)
            result_data = executor.execute(parsed)

            latency_ms = int((time.time() - start_time) * 1000)

            return ConfigResult(
                config_key=config_key,
                latency_ms=latency_ms,
                llm_time_ms=0,
                tool_time_ms=latency_ms,
                response=str(result_data.get("result", ""))[:500],
                result="pass" if result_data.get("result") else "fail"
            )
        except Exception as e:
            return ConfigResult(
                config_key=config_key,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                result="fail"
            )

    def _run_llm_test(
        self,
        test: TestQuery,
        optimizations: dict,
        config_key: str
    ) -> ConfigResult:
        """Run LLM test with given optimizations."""
        start_time = time.time()

        if not self.coordinator:
            return ConfigResult(
                config_key=config_key,
                error="No coordinator",
                result="fail"
            )

        try:
            response_data = self.coordinator.process(
                test.query,
                self.conversation_history,
                optimizations=optimizations,
                return_debug=True
            )

            latency_ms = int((time.time() - start_time) * 1000)
            response_text = response_data.get("response", "")
            debug_info = response_data.get("debug", {})

            # Update history for dependent tests
            self.conversation_history.append({"role": "user", "content": test.query})
            self.conversation_history.append({"role": "assistant", "content": response_text})

            return ConfigResult(
                config_key=config_key,
                latency_ms=latency_ms,
                llm_time_ms=debug_info.get("llm_time_ms"),
                tool_time_ms=debug_info.get("tool_time_ms"),
                embedding_time_ms=debug_info.get("embedding_time_ms"),
                mongodb_time_ms=debug_info.get("mongodb_time_ms"),
                processing_time_ms=debug_info.get("processing_time_ms"),
                tokens_in=debug_info.get("tokens_in"),
                tokens_out=debug_info.get("tokens_out"),
                cache_hit=debug_info.get("cache_hit", False),
                tools_called=debug_info.get("tools_called", []),
                response=response_text[:500] if response_text else "",
                result="pass"  # TODO: Auto-evaluate based on expected
            )
        except Exception as e:
            return ConfigResult(
                config_key=config_key,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                result="fail"
            )
