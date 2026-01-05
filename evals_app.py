"""
Flow Companion Evals Dashboard
Separate app for comparing optimization configurations.

Run: streamlit run evals_app.py --server.port 8502
"""

import streamlit as st
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Flow Companion Evals",
    page_icon="📊",
    layout="wide"
)

from evals.configs import EVAL_CONFIGS, DEFAULT_SELECTED
from evals.runner import ComparisonRunner
from evals.result import ComparisonRun

# Import coordinator
from agents.coordinator import coordinator


def init_session_state():
    """Initialize session state variables."""
    if "comparison_run" not in st.session_state:
        st.session_state.comparison_run = None
    if "selected_configs" not in st.session_state:
        st.session_state.selected_configs = DEFAULT_SELECTED.copy()
    if "coordinator" not in st.session_state:
        st.session_state.coordinator = None


def init_coordinator():
    """Initialize the coordinator if not already done."""
    if st.session_state.coordinator is None:
        try:
            st.session_state.coordinator = coordinator
        except Exception as e:
            st.error(f"Failed to initialize coordinator: {e}")


def render_config_section():
    """Render configuration selection."""
    st.subheader("🔬 Test Configuration")

    st.write("**Select configurations to compare:**")

    cols = st.columns(len(EVAL_CONFIGS))
    selected = []

    for i, (key, config) in enumerate(EVAL_CONFIGS.items()):
        with cols[i]:
            checked = st.checkbox(
                config["short"],
                value=key in st.session_state.selected_configs,
                help=config["description"],
                key=f"cfg_{key}"
            )
            if checked:
                selected.append(key)

    st.session_state.selected_configs = selected

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🚀 Run Comparison", type="primary", disabled=len(selected) < 2):
            st.session_state.run_comparison = True
    with col2:
        if st.button("📥 Export"):
            st.session_state.export_results = True
    with col3:
        if len(selected) < 2:
            st.caption("Select at least 2 configs to compare")


def render_summary_section():
    """Render summary metrics cards comparing baseline to best."""
    st.subheader("📈 Summary")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run or not run.summary_by_config:
        st.info("No results yet. Select configs and click 'Run Comparison'.")
        return

    # Get baseline and best config summaries
    baseline = run.summary_by_config.get("baseline", {})

    # Find best config (lowest latency, excluding baseline)
    best_key = None
    best_latency = float('inf')
    for key, summary in run.summary_by_config.items():
        if key != "baseline" and summary.get("avg_latency_ms", float('inf')) < best_latency:
            best_latency = summary["avg_latency_ms"]
            best_key = key

    best = run.summary_by_config.get(best_key, {}) if best_key else {}

    if not baseline or not best:
        st.warning("Need baseline and at least one other config for comparison.")
        return

    # Calculate improvements
    def calc_change(baseline_val, best_val):
        if baseline_val == 0:
            return 0
        return round((best_val - baseline_val) / baseline_val * 100, 1)

    latency_change = calc_change(baseline.get("avg_latency_ms", 0), best.get("avg_latency_ms", 0))
    tokens_change = calc_change(baseline.get("avg_tokens_in", 0), best.get("avg_tokens_in", 0))

    st.caption(f"Comparing: **Baseline** → **{EVAL_CONFIGS.get(best_key, {}).get('name', best_key)}**")

    # Metric cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Avg Latency",
            f"{best.get('avg_latency_ms', 0) / 1000:.1f}s",
            f"{latency_change:+.0f}%"
        )

    with col2:
        st.metric(
            "Avg Tokens In",
            f"{best.get('avg_tokens_in', 0):,}",
            f"{tokens_change:+.0f}%"
        )

    with col3:
        st.metric(
            "Avg Tokens Out",
            f"{best.get('avg_tokens_out', 0):,}"
        )

    with col4:
        accuracy = best.get("pass_rate", 0) * 100
        baseline_accuracy = baseline.get("pass_rate", 0) * 100
        acc_change = accuracy - baseline_accuracy
        st.metric(
            "Accuracy",
            f"{accuracy:.0f}%",
            f"{acc_change:+.0f}%"
        )

    with col5:
        total = best.get("total_tests", 0)
        passed = int(total * best.get("pass_rate", 0))
        st.metric("Pass Rate", f"{passed}/{total}")


def render_matrix_section():
    """Render comparison matrix."""
    st.subheader("🧪 Comparison Matrix")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run:
        st.info("Matrix will appear here after running comparison.")
        return

    # TODO: Render matrix with test results
    st.write("Comparison matrix will appear here.")


def render_charts_section():
    """Render impact analysis charts."""
    st.subheader("📉 Impact Analysis")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run:
        st.info("Charts will appear here after running comparison.")
        return

    # TODO: Render charts
    st.write("Charts will appear here.")


def run_comparison():
    """Execute comparison across selected configs."""
    configs = st.session_state.selected_configs
    coordinator = st.session_state.coordinator

    if not coordinator:
        st.error("Coordinator not initialized")
        return

    if len(configs) < 2:
        st.error("Select at least 2 configs")
        return

    progress = st.progress(0, text="Starting comparison...")

    def update_progress(current, total, message):
        progress.progress(current / total, text=message)

    runner = ComparisonRunner(coordinator, progress_callback=update_progress)

    try:
        run = runner.run_comparison(configs, skip_voice=True)
        st.session_state.comparison_run = run
        progress.empty()
        st.success(f"Completed {len(run.tests)} tests across {len(configs)} configs")
        st.rerun()
    except Exception as e:
        progress.empty()
        st.error(f"Error: {e}")


def main():
    st.title("📊 Flow Companion Evals Dashboard")
    st.caption("Compare optimization configurations across test queries")

    init_session_state()
    init_coordinator()

    render_config_section()
    st.markdown("---")
    render_summary_section()
    st.markdown("---")
    render_matrix_section()
    st.markdown("---")
    render_charts_section()

    # Handle Run Comparison
    if st.session_state.get("run_comparison"):
        st.session_state.run_comparison = False
        run_comparison()


if __name__ == "__main__":
    main()
