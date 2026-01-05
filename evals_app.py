"""
Flow Companion Evals Dashboard
Separate app for comparing optimization configurations.

Run: streamlit run evals_app.py --server.port 8502
"""

import streamlit as st

st.set_page_config(
    page_title="Flow Companion Evals",
    page_icon="📊",
    layout="wide"
)

from evals.configs import EVAL_CONFIGS, DEFAULT_SELECTED


def init_session_state():
    """Initialize session state variables."""
    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = {}
    if "selected_configs" not in st.session_state:
        st.session_state.selected_configs = DEFAULT_SELECTED.copy()
    if "coordinator" not in st.session_state:
        st.session_state.coordinator = None


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
    """Render summary metrics cards."""
    st.subheader("📈 Summary")

    results = st.session_state.comparison_results
    if not results:
        st.info("No results yet. Select configs and click 'Run Comparison'.")
        return

    # TODO: Calculate and display summary metrics
    st.write("Summary cards will appear here after running comparison.")


def render_matrix_section():
    """Render comparison matrix."""
    st.subheader("🧪 Comparison Matrix")

    results = st.session_state.comparison_results
    if not results:
        st.info("Matrix will appear here after running comparison.")
        return

    # TODO: Render matrix with test results
    st.write("Comparison matrix will appear here.")


def render_charts_section():
    """Render impact analysis charts."""
    st.subheader("📉 Impact Analysis")

    results = st.session_state.comparison_results
    if not results:
        st.info("Charts will appear here after running comparison.")
        return

    # TODO: Render charts
    st.write("Charts will appear here.")


def main():
    st.title("📊 Flow Companion Evals Dashboard")
    st.caption("Compare optimization configurations across test queries")

    init_session_state()

    render_config_section()
    st.markdown("---")
    render_summary_section()
    st.markdown("---")
    render_matrix_section()
    st.markdown("---")
    render_charts_section()


if __name__ == "__main__":
    main()
