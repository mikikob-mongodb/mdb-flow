"""
Flow Companion Evals Dashboard
Separate app for comparing optimization configurations.

Run: streamlit run evals_app.py --server.port 8502
"""

import streamlit as st
import os
import sys
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("🚀 Run Comparison", type="primary", disabled=len(selected) < 2):
            st.session_state.run_comparison = True

    with col2:
        has_results = st.session_state.get("comparison_run") is not None
        if st.button("📥 Export JSON", disabled=not has_results):
            st.session_state.export_results = True

    with col3:
        if st.button("🗑️ Clear Results"):
            st.session_state.comparison_run = None
            st.rerun()

    with col4:
        if len(selected) < 2:
            st.caption("Select 2+ configs")
        else:
            st.caption(f"{len(selected)} configs selected")


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
    """Render comparison matrix with test results."""
    st.subheader("🧪 Comparison Matrix")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run or not run.tests:
        st.info("Matrix will appear here after running comparison.")
        return

    configs = run.configs_compared

    # Build header
    header_cols = st.columns([0.5, 2] + [1.5] * len(configs) + [1.5])
    header_cols[0].write("**#**")
    header_cols[1].write("**Query**")
    for i, cfg in enumerate(configs):
        header_cols[2 + i].write(f"**{EVAL_CONFIGS[cfg]['short']}**")
    header_cols[-1].write("**Best**")

    st.markdown("---")

    # Render each test row
    for test in run.tests:
        render_matrix_row(test, configs)


def render_matrix_row(test, configs: list):
    """Render a single row in the matrix."""
    cols = st.columns([0.5, 2] + [1.5] * len(configs) + [1.5])

    # Test ID
    cols[0].write(f"**{test.test_id}**")

    # Query (truncated)
    query_short = test.query[:25] + "..." if len(test.query) > 25 else test.query
    cols[1].write(query_short)

    # Results per config
    for i, cfg in enumerate(configs):
        result = test.results_by_config.get(cfg)
        if result:
            latency_s = result.latency_ms / 1000
            tokens = result.tokens_in or "-"

            # Color based on relative performance
            if cfg == test.best_config:
                cols[2 + i].markdown(f"🟢 **{latency_s:.1f}s**<br>{tokens}", unsafe_allow_html=True)
            else:
                cols[2 + i].markdown(f"{latency_s:.1f}s<br>{tokens}", unsafe_allow_html=True)
        else:
            cols[2 + i].write("-")

    # Best config
    if test.best_config and test.improvement_pct:
        best_name = EVAL_CONFIGS[test.best_config]["short"]
        cols[-1].write(f"✅ {best_name} (-{test.improvement_pct:.0f}%)")
    else:
        cols[-1].write("-")

    # Expandable details
    with st.expander(f"Details #{test.test_id}"):
        render_row_details(test, configs)


def render_row_details(test, configs: list):
    """Render expanded details for a test."""

    # Config cards side by side
    cols = st.columns(len(configs))

    for i, cfg in enumerate(configs):
        result = test.results_by_config.get(cfg)
        with cols[i]:
            st.markdown(f"**{EVAL_CONFIGS[cfg]['name']}**")
            if result:
                is_best = cfg == test.best_config

                st.write(f"Latency: **{result.latency_ms}ms** {'✅' if is_best else ''}")
                st.write(f"Tokens In: {result.tokens_in or '-'}")
                st.write(f"Tokens Out: {result.tokens_out or '-'}")
                st.write(f"LLM Time: {result.llm_time_ms or '-'}ms")
                st.write(f"Tool Time: {result.tool_time_ms or '-'}ms")
                st.write(f"Cache Hit: {'✅' if result.cache_hit else '❌'}")

                if result.tools_called:
                    st.write(f"Tools: {', '.join(result.tools_called)}")

                if result.error:
                    st.error(f"Error: {result.error}")
            else:
                st.write("No result")

    # Notes
    st.markdown("---")
    notes = st.text_input(
        "Notes",
        value=test.notes,
        key=f"notes_{test.test_id}",
        placeholder="Add observations..."
    )
    if notes != test.notes:
        test.notes = notes


def render_charts_section():
    """Render impact analysis charts."""
    st.subheader("📉 Impact Analysis")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run or not run.summary_by_config:
        st.info("Charts will appear here after running comparison.")
        return

    # Prepare data
    configs = run.configs_compared
    summaries = run.summary_by_config

    # Row 1: Latency and Tokens charts
    col1, col2 = st.columns(2)

    with col1:
        render_latency_chart(configs, summaries)

    with col2:
        render_tokens_chart(configs, summaries)

    # Row 2: Accuracy and Breakdown
    col1, col2 = st.columns(2)

    with col1:
        render_accuracy_chart(configs, summaries)

    with col2:
        render_breakdown_chart(configs, summaries)

    # Row 3: Latency over sequence
    render_sequence_chart(run)


def render_latency_chart(configs, summaries):
    """Bar chart of average latency by config."""
    data = []
    for cfg in configs:
        summary = summaries.get(cfg, {})
        data.append({
            "Config": EVAL_CONFIGS[cfg]["short"],
            "Latency (s)": summary.get("avg_latency_ms", 0) / 1000
        })

    df = pd.DataFrame(data)
    fig = px.bar(df, x="Config", y="Latency (s)", title="⏱️ Average Latency by Config")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_tokens_chart(configs, summaries):
    """Bar chart of average tokens by config."""
    data = []
    for cfg in configs:
        summary = summaries.get(cfg, {})
        data.append({
            "Config": EVAL_CONFIGS[cfg]["short"],
            "Tokens In": summary.get("avg_tokens_in", 0)
        })

    df = pd.DataFrame(data)
    fig = px.bar(df, x="Config", y="Tokens In", title="🪙 Average Tokens by Config")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_accuracy_chart(configs, summaries):
    """Bar chart of accuracy/pass rate by config."""
    data = []
    for cfg in configs:
        summary = summaries.get(cfg, {})
        data.append({
            "Config": EVAL_CONFIGS[cfg]["short"],
            "Pass Rate (%)": summary.get("pass_rate", 0) * 100
        })

    df = pd.DataFrame(data)
    fig = px.bar(df, x="Config", y="Pass Rate (%)", title="✅ Accuracy by Config")
    fig.update_layout(height=300, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)


def render_breakdown_chart(configs, summaries):
    """Show improvement breakdown vs baseline."""
    if "baseline" not in summaries:
        st.info("Need baseline for comparison")
        return

    baseline = summaries["baseline"]
    baseline_latency = baseline.get("avg_latency_ms", 1)

    data = []
    for cfg in configs:
        if cfg == "baseline":
            continue
        summary = summaries.get(cfg, {})
        reduction = baseline_latency - summary.get("avg_latency_ms", 0)
        reduction_pct = (reduction / baseline_latency) * 100 if baseline_latency > 0 else 0
        data.append({
            "Config": EVAL_CONFIGS[cfg]["short"],
            "Reduction (%)": round(reduction_pct, 1)
        })

    if not data:
        return

    df = pd.DataFrame(data)
    fig = px.bar(df, x="Config", y="Reduction (%)",
                 title="📊 Latency Reduction vs Baseline")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_sequence_chart(run: ComparisonRun):
    """Line chart showing latency over test sequence (cache warming effect)."""
    st.markdown("#### 📉 Latency Over Test Sequence")

    if not run.tests:
        return

    data = []
    for test in run.tests:
        for cfg, result in test.results_by_config.items():
            data.append({
                "Test": f"#{test.test_id}",
                "Test ID": test.test_id,
                "Config": EVAL_CONFIGS[cfg]["short"],
                "Latency (s)": result.latency_ms / 1000
            })

    df = pd.DataFrame(data)
    fig = px.line(df, x="Test ID", y="Latency (s)", color="Config",
                  title="Latency Over Test Sequence (shows cache warming)")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Note: Cache warming visible in 'Caching' config - first query slower, subsequent faster.")


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


def calculate_improvements(run: ComparisonRun) -> dict:
    """Calculate improvement percentages for export."""
    if "baseline" not in run.summary_by_config:
        return {}

    baseline = run.summary_by_config["baseline"]
    improvements = {}

    for cfg, summary in run.summary_by_config.items():
        if cfg == "baseline":
            continue

        baseline_latency = baseline.get("avg_latency_ms", 1)
        baseline_tokens = baseline.get("avg_tokens_in", 1)
        baseline_accuracy = baseline.get("pass_rate", 0)

        cfg_latency = summary.get("avg_latency_ms", 0)
        cfg_tokens = summary.get("avg_tokens_in", 0)
        cfg_accuracy = summary.get("pass_rate", 0)

        improvements[cfg] = {
            "latency_reduction_pct": round((baseline_latency - cfg_latency) / baseline_latency * 100, 1) if baseline_latency else 0,
            "tokens_reduction_pct": round((baseline_tokens - cfg_tokens) / baseline_tokens * 100, 1) if baseline_tokens else 0,
            "accuracy_change_pct": round((cfg_accuracy - baseline_accuracy) * 100, 1)
        }

    return improvements


def export_results():
    """Export comparison results to JSON."""
    run: ComparisonRun = st.session_state.get("comparison_run")

    if not run:
        st.warning("No results to export. Run a comparison first.")
        return

    # Convert to exportable format
    export_data = {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "exported_at": datetime.utcnow().isoformat(),
        "configs_compared": run.configs_compared,
        "config_details": {
            k: EVAL_CONFIGS[k] for k in run.configs_compared
        },
        "summary_by_config": run.summary_by_config,
        "improvements": calculate_improvements(run),
        "tests": [t.to_dict() for t in run.tests]
    }

    # Trigger download
    filename = f"evals_{run.run_id}.json"

    st.download_button(
        label="📥 Download JSON",
        data=json.dumps(export_data, indent=2, default=str),
        file_name=filename,
        mime="application/json"
    )


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

    # Handle Export
    if st.session_state.get("export_results"):
        st.session_state.export_results = False
        export_results()


if __name__ == "__main__":
    main()
