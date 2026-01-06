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
from evals.storage import save_comparison_run, list_comparison_runs, load_comparison_run

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


def compute_section_averages(comparison_run: ComparisonRun) -> dict:
    """
    Aggregate test results by section for charts.

    Returns dict with per-section, per-config averages:
    {
        "slash_commands": {
            "baseline": {
                "avg_latency": 123.4,
                "avg_tokens_in": 1000,
                "avg_tokens_out": 50,
                "avg_llm_time": 100,
                "avg_tool_time": 23,
                "test_count": 10
            },
            "all_context": {...}
        },
        "text_queries": {...},
        ...
    }
    """
    from evals.test_suite import Section

    sections = [s.value for s in Section]
    results = {}

    for section in sections:
        # Get all tests for this section
        section_tests = [t for t in comparison_run.tests if t.section == section]
        results[section] = {}

        for config in comparison_run.configs_compared:
            # Get all results for this config in this section
            config_results = []
            for test in section_tests:
                if config in test.results_by_config:
                    config_results.append(test.results_by_config[config])

            if config_results:
                results[section][config] = {
                    "avg_latency": sum(r.latency_ms or 0 for r in config_results) / len(config_results),
                    "avg_tokens_in": sum(r.tokens_in or 0 for r in config_results) / len(config_results),
                    "avg_tokens_out": sum(r.tokens_out or 0 for r in config_results) / len(config_results),
                    "avg_llm_time": sum(r.llm_time_ms or 0 for r in config_results) / len(config_results),
                    "avg_tool_time": sum(r.tool_time_ms or 0 for r in config_results) / len(config_results),
                    "test_count": len(config_results)
                }

    return results


def render_charts_section():
    """Render impact analysis charts."""
    st.subheader("📈 Impact Analysis")

    run: ComparisonRun = st.session_state.get("comparison_run")
    if not run or not run.summary_by_config:
        st.info("Charts will appear here after running comparison.")
        return

    # Prepare data
    configs = run.configs_compared
    summaries = run.summary_by_config

    # Row 1: Optimization Waterfall and Impact by Query Type
    col1, col2 = st.columns(2)

    with col1:
        render_optimization_waterfall(run)

    with col2:
        render_impact_by_query_type(run)

    # Row 2: LLM vs Tool Time and Token Savings
    col1, col2 = st.columns(2)

    with col1:
        render_llm_tool_breakdown(run)

    with col2:
        render_token_savings_by_type(run)


def render_optimization_waterfall(run: ComparisonRun):
    """Horizontal waterfall showing cumulative latency reduction."""
    # Order: baseline → compress → streamlined → caching → all_context
    waterfall_order = ["baseline", "compress_results", "streamlined_prompt", "prompt_caching", "all_context"]

    # Filter to only configs that were run
    ordered_configs = [cfg for cfg in waterfall_order if cfg in run.configs_compared]

    if len(ordered_configs) < 2:
        st.info("Run baseline + optimizations to see waterfall")
        return

    summaries = run.summary_by_config

    # Collect data
    latencies = []
    labels = []
    for cfg in ordered_configs:
        summary = summaries.get(cfg, {})
        latency_s = summary.get("avg_latency_ms", 0) / 1000
        latencies.append(latency_s)
        labels.append(EVAL_CONFIGS[cfg]["short"])

    # Calculate % reduction from baseline
    baseline = latencies[0] if latencies else 1
    reductions = [f"{((baseline - lat) / baseline * 100):.0f}%" for lat in latencies]

    # Color gradient
    colors = ['#6b7280', '#8b5cf6', '#3b82f6', '#f59e0b', '#10b981'][:len(latencies)]

    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        x=latencies,
        y=labels,
        orientation='h',
        text=[f"{lat:.1f}s ({red})" for lat, red in zip(latencies, reductions)],
        textposition='outside',
        marker_color=colors
    ))

    fig.update_layout(
        title="⚡ Optimization Waterfall",
        xaxis_title="Latency (seconds)",
        yaxis=dict(autorange="reversed"),  # Baseline at top
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)


def render_impact_by_query_type(run: ComparisonRun):
    """Grouped bar chart: Baseline vs optimized config by query type."""
    from evals.test_suite import Section, SECTION_NAMES

    # Need baseline and at least one optimization config
    if "baseline" not in run.configs_compared:
        st.info("Need baseline for comparison")
        return

    # Find best optimization config (prefer all_context, or take first non-baseline)
    opt_config = None
    if "all_context" in run.configs_compared:
        opt_config = "all_context"
    else:
        for cfg in run.configs_compared:
            if cfg != "baseline":
                opt_config = cfg
                break

    if not opt_config:
        st.info("Need at least one optimization config")
        return

    # Get aggregated data by section
    section_averages = compute_section_averages(run)

    # Build data for sections (exclude voice)
    sections = [Section.SLASH_COMMANDS, Section.TEXT_QUERIES, Section.TEXT_ACTIONS, Section.MULTI_TURN]
    section_names = [SECTION_NAMES.get(s, s.value) for s in sections]

    # Collect latencies for each config
    baseline_latencies = []
    opt_latencies = []

    for section in sections:
        section_key = section.value
        section_data = section_averages.get(section_key, {})

        baseline_lat = section_data.get("baseline", {}).get("avg_latency", 0) / 1000
        opt_lat = section_data.get(opt_config, {}).get("avg_latency", 0) / 1000

        baseline_latencies.append(baseline_lat)
        opt_latencies.append(opt_lat)

    # Create grouped bar chart
    fig = go.Figure()

    # Baseline bars
    fig.add_trace(go.Bar(
        name="Baseline",
        x=section_names,
        y=baseline_latencies,
        marker_color="#6b7280"
    ))

    # Optimized config bars
    fig.add_trace(go.Bar(
        name=EVAL_CONFIGS[opt_config]["short"],
        x=section_names,
        y=opt_latencies,
        marker_color="#10b981"
    ))

    fig.update_layout(
        title="📊 Impact by Query Type",
        yaxis_title="Avg Latency (seconds)",
        barmode='group',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_llm_tool_breakdown(run: ComparisonRun):
    """Stacked horizontal bar showing % time in LLM vs tools."""
    summaries = run.summary_by_config

    data = []
    for cfg in run.configs_compared:
        summary = summaries.get(cfg, {})
        llm_time = summary.get("avg_llm_time_ms", 0)
        tool_time = summary.get("avg_tool_time_ms", 0)
        total = llm_time + tool_time

        if total > 0:
            llm_pct = (llm_time / total) * 100
            tool_pct = (tool_time / total) * 100

            data.append({
                "Config": EVAL_CONFIGS[cfg]["short"],
                "LLM Time (%)": round(llm_pct, 1),
                "Tool Time (%)": round(tool_pct, 1)
            })

    if not data:
        st.info("Need LLM/tool time data")
        return

    df = pd.DataFrame(data)

    # Create stacked horizontal bar
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="LLM",
        y=df["Config"],
        x=df["LLM Time (%)"],
        orientation='h',
        marker_color='#FF6B6B'
    ))
    fig.add_trace(go.Bar(
        name="Tools",
        y=df["Config"],
        x=df["Tool Time (%)"],
        orientation='h',
        marker_color='#4ECDC4'
    ))

    fig.update_layout(
        title="🔧 LLM vs Tool Time Breakdown",
        barmode='stack',
        height=350,
        xaxis_title="Time Distribution (%)",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_token_savings_by_type(run: ComparisonRun):
    """Bar chart showing token reduction % by query type."""
    from evals.test_suite import Section, SECTION_NAMES

    if "baseline" not in run.configs_compared:
        st.info("Need baseline for comparison")
        return

    # Find best optimization config
    opt_config = None
    if "all_context" in run.configs_compared:
        opt_config = "all_context"
    else:
        for cfg in run.configs_compared:
            if cfg != "baseline":
                opt_config = cfg
                break

    if not opt_config:
        st.info("Need optimization config")
        return

    # Get aggregated data by section
    section_averages = compute_section_averages(run)

    # Calculate savings per section
    data = []
    for section in Section:
        section_key = section.value
        section_name = SECTION_NAMES.get(section, section_key).replace(" ", "\n")

        section_data = section_averages.get(section_key, {})

        if "baseline" in section_data and opt_config in section_data:
            avg_baseline = section_data["baseline"]["avg_tokens_in"]
            avg_opt = section_data[opt_config]["avg_tokens_in"]

            if avg_baseline > 0:
                reduction_pct = ((avg_baseline - avg_opt) / avg_baseline) * 100
                data.append({
                    "Query Type": section_name,
                    "Reduction (%)": round(reduction_pct, 1)
                })

    if not data:
        st.info("Need token data")
        return

    df = pd.DataFrame(data)
    fig = px.bar(df, x="Query Type", y="Reduction (%)",
                 title="🪙 Token Savings by Query Type")
    fig.update_layout(height=350, xaxis_title="", yaxis_title="Token Reduction (%)")
    st.plotly_chart(fig, use_container_width=True)


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

        # Save to MongoDB
        progress.progress(1.0, text="Saving results...")
        try:
            save_comparison_run(run)
            st.success(f"Completed {len(run.tests)} tests. Saved as {run.run_id}")
        except Exception as e:
            st.warning(f"Results not saved to DB: {e}")
            st.success(f"Completed {len(run.tests)} tests (not persisted)")

        progress.empty()
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


def render_history_sidebar():
    """Render sidebar with past runs."""
    st.sidebar.header("📜 Past Runs")

    try:
        runs = list_comparison_runs(limit=10)
    except:
        runs = []

    if not runs:
        st.sidebar.caption("No saved runs yet")
        return

    for run in runs:
        run_id = run.get("run_id", "unknown")
        timestamp = run.get("timestamp", "")
        configs = run.get("configs_compared", [])

        # Format timestamp
        if isinstance(timestamp, str):
            display_time = timestamp[:16].replace("T", " ")
        else:
            display_time = timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else ""

        # Summary
        summary = run.get("summary_by_config", {})
        baseline_latency = summary.get("baseline", {}).get("avg_latency_ms", 0)

        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.caption(f"{display_time}")
            st.caption(f"{len(configs)} configs")
        with col2:
            if st.button("Load", key=f"load_{run_id}"):
                load_saved_run(run_id)


def load_saved_run(run_id: str):
    """Load a saved run into session state."""
    try:
        doc = load_comparison_run(run_id)
        if doc:
            # Reconstruct ComparisonRun from dict
            run = ComparisonRun(
                run_id=doc.get("run_id"),
                timestamp=doc.get("timestamp"),
                configs_compared=doc.get("configs_compared", []),
            )
            run.summary_by_config = doc.get("summary_by_config", {})
            # Note: Full test reconstruction would need more work
            # For now just load summaries for charts
            st.session_state.comparison_run = run
            st.session_state.selected_configs = doc.get("configs_compared", [])
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Failed to load: {e}")


def main():
    st.title("📊 Flow Companion Evals Dashboard")
    st.caption("Compare optimization configurations across test queries")

    init_session_state()
    init_coordinator()

    # Sidebar with history
    render_history_sidebar()

    # Main content
    render_config_section()
    st.markdown("---")
    render_summary_section()
    st.markdown("---")
    render_charts_section()
    st.markdown("---")
    render_matrix_section()

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
