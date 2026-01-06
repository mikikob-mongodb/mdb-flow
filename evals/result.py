"""Data classes for eval results."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class ConfigResult:
    """Result of a single test with one configuration."""
    config_key: str
    latency_ms: int = 0
    llm_time_ms: Optional[int] = None
    tool_time_ms: Optional[int] = None
    embedding_time_ms: Optional[int] = None
    mongodb_time_ms: Optional[int] = None
    processing_time_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cache_hit: bool = False
    tools_called: List[str] = field(default_factory=list)
    response: str = ""
    error: Optional[str] = None
    result: str = "pending"  # pending | pass | partial | fail
    rating: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TestComparison:
    """Comparison results for a single test across multiple configs."""
    test_id: int
    query: str
    section: str
    input_type: str
    expected: str

    # Results keyed by config_key
    results_by_config: Dict[str, ConfigResult] = field(default_factory=dict)

    # Computed after all configs run
    best_config: Optional[str] = None
    best_latency_ms: Optional[int] = None
    improvement_pct: Optional[float] = None

    # User notes
    notes: str = ""

    def add_result(self, config_key: str, result: ConfigResult):
        """Add a result for a configuration."""
        self.results_by_config[config_key] = result
        self._compute_best()

    def _compute_best(self):
        """Compute best config based on latency."""
        if not self.results_by_config:
            return

        # Find fastest
        best_key = None
        best_latency = float('inf')
        for key, result in self.results_by_config.items():
            if result.latency_ms < best_latency:
                best_latency = result.latency_ms
                best_key = key

        self.best_config = best_key
        self.best_latency_ms = best_latency

        # Calculate improvement vs baseline
        if "baseline" in self.results_by_config and best_key != "baseline":
            baseline_latency = self.results_by_config["baseline"].latency_ms
            if baseline_latency > 0:
                self.improvement_pct = round(
                    (baseline_latency - best_latency) / baseline_latency * 100, 1
                )

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "query": self.query,
            "section": self.section,
            "input_type": self.input_type,
            "expected": self.expected,
            "results_by_config": {
                k: v.to_dict() for k, v in self.results_by_config.items()
            },
            "best_config": self.best_config,
            "best_latency_ms": self.best_latency_ms,
            "improvement_pct": self.improvement_pct,
            "notes": self.notes
        }


@dataclass
class ComparisonRun:
    """A complete comparison run across multiple configs."""
    run_id: str = ""
    timestamp: str = ""
    configs_compared: List[str] = field(default_factory=list)
    tests: List[TestComparison] = field(default_factory=list)

    # Per-config aggregates
    summary_by_config: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        if not self.run_id:
            self.run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def compute_summaries(self):
        """Compute aggregate summaries per config."""
        for config_key in self.configs_compared:
            latencies = []
            tokens_in = []
            tokens_out = []
            llm_times = []
            tool_times = []
            passed = 0
            total = 0

            for test in self.tests:
                if config_key in test.results_by_config:
                    result = test.results_by_config[config_key]
                    latencies.append(result.latency_ms)
                    if result.tokens_in:
                        tokens_in.append(result.tokens_in)
                    if result.tokens_out:
                        tokens_out.append(result.tokens_out)
                    if result.llm_time_ms is not None:
                        llm_times.append(result.llm_time_ms)
                    if result.tool_time_ms is not None:
                        tool_times.append(result.tool_time_ms)
                    if result.result == "pass":
                        passed += 1
                    total += 1

            self.summary_by_config[config_key] = {
                "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
                "avg_tokens_in": round(sum(tokens_in) / len(tokens_in)) if tokens_in else 0,
                "avg_tokens_out": round(sum(tokens_out) / len(tokens_out)) if tokens_out else 0,
                "avg_llm_time_ms": round(sum(llm_times) / len(llm_times)) if llm_times else 0,
                "avg_tool_time_ms": round(sum(tool_times) / len(tool_times)) if tool_times else 0,
                "pass_rate": round(passed / total, 2) if total > 0 else 0,
                "total_tests": total
            }

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "configs_compared": self.configs_compared,
            "summary_by_config": self.summary_by_config,
            "tests": [t.to_dict() for t in self.tests]
        }
