"""Streamlit Chat UI for Flow Companion."""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any

# Import the coordinator agent
from agents.coordinator import coordinator
from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION
from shared.models import Task, Project
from utils.audio import transcribe_audio

# Import slash command functionality
from ui.slash_commands import parse_slash_command, SlashCommandExecutor
from ui.formatters import render_command_result


# Page configuration
st.set_page_config(
    page_title="Flow Companion",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "coordinator" not in st.session_state:
        st.session_state.coordinator = coordinator

    if "slash_executor" not in st.session_state:
        st.session_state.slash_executor = SlashCommandExecutor(coordinator)

    if "last_audio_bytes" not in st.session_state:
        st.session_state.last_audio_bytes = None

    if "last_debug_info" not in st.session_state:
        st.session_state.last_debug_info = []

    if "debug_history" not in st.session_state:
        st.session_state.debug_history = []

    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    if "user_id" not in st.session_state:
        st.session_state.user_id = "demo_user"

    if "current_context" not in st.session_state:
        st.session_state.current_context = {}

    # Set coordinator session for memory isolation
    if coordinator and hasattr(coordinator, 'set_session'):
        coordinator.set_session(
            st.session_state.session_id,
            user_id=st.session_state.user_id
        )


def get_all_projects_with_tasks() -> List[Dict[str, Any]]:
    """
    Get all projects with their associated tasks.

    Returns:
        List of projects with tasks
    """
    projects_collection = get_collection(PROJECTS_COLLECTION)
    tasks_collection = get_collection(TASKS_COLLECTION)

    # Get all active projects
    projects_cursor = projects_collection.find(
        {"status": "active"}
    ).sort("last_activity", -1)

    projects_with_tasks = []

    for project_doc in projects_cursor:
        project = Project(**project_doc)

        # Get tasks for this project
        tasks_cursor = tasks_collection.find(
            {"project_id": project.id}
        ).sort([("status", 1), ("created_at", -1)])

        tasks = [Task(**task_doc) for task_doc in tasks_cursor]

        projects_with_tasks.append({
            "project": project,
            "tasks": tasks
        })

    # Also get tasks without a project
    orphan_tasks_cursor = tasks_collection.find(
        {"project_id": None}
    ).sort([("status", 1), ("created_at", -1)])

    orphan_tasks = [Task(**task_doc) for task_doc in orphan_tasks_cursor]

    if orphan_tasks:
        projects_with_tasks.append({
            "project": None,
            "tasks": orphan_tasks
        })

    return projects_with_tasks


def get_status_icon(status: str) -> str:
    """Get icon for task status."""
    icons = {
        "todo": "○",
        "in_progress": "◐",
        "done": "✓"
    }
    return icons.get(status, "○")


def get_priority_badge(priority: str) -> str:
    """Get colored badge for priority."""
    if priority == "high":
        return "🔴"
    elif priority == "medium":
        return "🟡"
    elif priority == "low":
        return "🟢"
    return ""


def render_context_engineering_toggles():
    """Render context engineering optimization toggles in the sidebar."""
    st.sidebar.subheader("⚡ Context Engineering")

    compress_results = st.sidebar.toggle(
        "Compress Results",
        value=True,
        help="Compress tool results to reduce context size"
    )
    streamline_prompt = st.sidebar.toggle(
        "Streamlined Prompt",
        value=True,
        help="Use directive prompt patterns"
    )
    cache_prompts = st.sidebar.toggle(
        "Prompt Caching",
        value=True,
        help="Cache system prompt for faster subsequent calls"
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🧠 Memory Settings")

    # Memory master toggle
    memory_enabled = st.sidebar.checkbox(
        "Enable Memory",
        value=True,
        help="Master toggle for all memory features"
    )

    if memory_enabled:
        col1, col2 = st.sidebar.columns(2)

        with col1:
            short_term = st.sidebar.checkbox(
                "Short-term",
                value=True,
                help="Session context (2h TTL)"
            )
            long_term = st.sidebar.checkbox(
                "Long-term",
                value=True,
                help="Action history (persistent)"
            )

        with col2:
            shared = st.sidebar.checkbox(
                "Shared",
                value=True,
                help="Agent handoffs (5m TTL)"
            )
            context_inject = st.sidebar.checkbox(
                "Ctx Inject",
                value=True,
                help="Inject context into prompt"
            )
    else:
        short_term = False
        long_term = False
        shared = False
        context_inject = False

    # Store in session state
    st.session_state.optimizations = {
        "compress_results": compress_results,
        "streamlined_prompt": streamline_prompt,
        "prompt_caching": cache_prompts,
        "memory_enabled": memory_enabled,
        "short_term_memory": short_term,
        "long_term_memory": long_term,
        "shared_memory": shared,
        "context_injection": context_inject
    }

    # Update coordinator memory config
    if coordinator:
        coordinator.memory_config = {
            "short_term": short_term,
            "long_term": long_term,
            "shared": shared,
            "context_injection": context_inject
        }

    # Show current context if available
    if short_term and coordinator.memory:
        with st.sidebar.expander("📍 Session Context", expanded=False):
            try:
                context = coordinator.memory.read_session_context(st.session_state.session_id)

                if context:
                    # Current project/task/action
                    if context.get("current_project"):
                        st.write(f"**Project:** {context['current_project']}")
                    if context.get("current_task"):
                        st.write(f"**Task:** {context['current_task']}")
                    if context.get("last_action"):
                        st.write(f"**Last Action:** {context['last_action']}")

                    # Preferences
                    if context.get("preferences"):
                        st.markdown("**Preferences:**")
                        for key, value in context["preferences"].items():
                            st.caption(f"• {key}: {value}")

                    # Rules
                    if context.get("rules"):
                        st.markdown("**Rules:**")
                        for rule in context["rules"]:
                            st.caption(f"• {rule}")
                else:
                    st.caption("_No context yet_")

                # Pending disambiguation
                disambiguation = coordinator.memory.get_pending_disambiguation(st.session_state.session_id)
                if disambiguation:
                    st.markdown("---")
                    st.markdown(f"**🔍 Pending Selection:** '{disambiguation['query']}'")
                    for r in disambiguation.get("results", []):
                        st.caption(f"{r['index'] + 1}. {r['title']}")
            except Exception as e:
                st.caption(f"_Error loading context: {e}_")

    # Agent Working Memory (future multi-agent support)
    if shared and coordinator.memory:
        with st.sidebar.expander("🔧 Agent State", expanded=False):
            try:
                has_working = False
                for agent_id in ["coordinator", "retrieval", "worklog"]:
                    working = coordinator.memory.read_agent_working(st.session_state.session_id, agent_id)
                    if working:
                        has_working = True
                        st.markdown(f"**{agent_id.capitalize()}:**")
                        for key, value in working.items():
                            if not key.startswith("_"):  # Skip internal fields
                                st.caption(f"• {key}: {value}")
                        st.markdown("")

                if not has_working:
                    st.caption("_No agent state_")
            except Exception as e:
                st.caption(f"_Error: {e}_")

    # Pending Handoffs (future multi-agent support)
    if shared and coordinator.memory:
        with st.sidebar.expander("🤝 Handoffs", expanded=False):
            try:
                has_handoffs = False
                for agent_id in ["coordinator", "retrieval", "worklog"]:
                    pending_count = coordinator.memory.check_pending(st.session_state.session_id, agent_id)
                    if pending_count:
                        has_handoffs = True
                        st.write(f"**{agent_id.capitalize()}:** {pending_count} pending")

                if not has_handoffs:
                    st.caption("_No pending handoffs_")
            except Exception as e:
                st.caption(f"_Error: {e}_")

    # Show memory stats
    if memory_enabled and coordinator.memory:
        with st.sidebar.expander("📊 Memory Stats", expanded=False):
            try:
                stats = coordinator.memory.get_memory_stats(
                    st.session_state.session_id,
                    st.session_state.user_id
                )
                st.write(f"**Short-term:** {stats['short_term_count']} entries")
                st.write(f"**Long-term:** {stats['long_term_count']} actions")

                # Show action breakdown if available
                if stats.get('action_counts'):
                    st.caption("  Action types:")
                    for action_type, count in stats['action_counts'].items():
                        st.caption(f"  • {action_type}: {count}")

                st.write(f"**Shared:** {stats['shared_pending']} pending")
            except Exception as e:
                st.write(f"Error loading stats: {e}")

    # Session controls
    if memory_enabled and coordinator.memory:
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear current session memory"):
                try:
                    coordinator.memory.clear_session(st.session_state.session_id)
                    st.session_state.current_context = {}
                    st.sidebar.success("✅ Cleared!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

        with col2:
            if st.button("🆕 New", use_container_width=True, help="Start a new session"):
                try:
                    import uuid
                    # Clear old session
                    coordinator.memory.clear_session(st.session_state.session_id)

                    # Create new session
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    st.session_state.debug_history = []
                    st.session_state.current_context = {}

                    # Update coordinator
                    coordinator.set_session(
                        st.session_state.session_id,
                        user_id=st.session_state.user_id
                    )

                    st.sidebar.success("✅ New session!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    # Show active status
    active = []
    if compress_results:
        active.append("📦")
    if streamline_prompt:
        active.append("⚡")
    if cache_prompts:
        active.append("💾")
    if memory_enabled:
        active.append("🧠")
    st.sidebar.caption(f"Active: {' '.join(active) if active else 'None'}")

    st.sidebar.markdown("---")


def render_memory_debug(debug_info: dict):
    """Render memory section of debug panel with competency indicators.

    Args:
        debug_info: Debug information dict with memory_ops
    """
    # Get memory_ops from debug info
    memory_ops = debug_info.get("memory_ops", {})

    if not memory_ops:
        return  # No memory activity

    st.markdown("---")
    st.markdown("**🧠 Memory Operations**")

    # Build competency indicators
    indicators = []

    # Context operations
    if memory_ops.get("context_injected"):
        indicators.append("CR-SH")  # Context Read from Short-term
    if memory_ops.get("context_updated"):
        indicators.append("CW-SH")  # Context Write to Short-term

    # Action recording
    if memory_ops.get("action_recorded"):
        action_type = memory_ops.get("recorded_action_type", "")
        indicators.append(f"AR-T:{action_type}")  # Action Recorded to long-Term

    # Show indicators
    if indicators:
        st.markdown(f"**Competency:** `{' | '.join(indicators)}`")
        st.caption("CR-SH=Context Read, CW-SH=Context Write, AR-T=Action Recorded")

    # Memory timing
    memory_read = memory_ops.get("memory_read_ms", 0)
    memory_write = memory_ops.get("memory_write_ms", 0)

    if memory_read or memory_write:
        cols = st.columns(3)

        with cols[0]:
            if memory_read:
                st.metric("Read", f"{memory_read:.0f}ms")

        with cols[1]:
            if memory_write:
                st.metric("Write", f"{memory_write:.0f}ms")

        with cols[2]:
            total = memory_read + memory_write
            if total:
                st.metric("Total", f"{total:.0f}ms")

    # Show full memory_ops dict in expander
    with st.expander("Memory Ops Detail", expanded=False):
        st.json(memory_ops)


def render_task_list():
    """Render the task list in the sidebar."""
    st.sidebar.title("📋 Tasks & Projects")

    # Get all projects with tasks
    projects_with_tasks = get_all_projects_with_tasks()

    if not projects_with_tasks:
        st.sidebar.info("No projects or tasks yet. Start by creating one in the chat!")
        return

    # Render each project and its tasks
    for item in projects_with_tasks:
        project = item["project"]
        tasks = item["tasks"]

        # Project header
        if project:
            st.sidebar.markdown(f"### 📁 {project.name}")
            if project.description:
                st.sidebar.caption(project.description)
        else:
            st.sidebar.markdown("### 📝 Unassigned Tasks")

        # Render tasks
        if tasks:
            for task in tasks:
                status_icon = get_status_icon(task.status)
                priority_badge = get_priority_badge(task.priority) if task.priority else ""

                # Task display
                task_text = f"{status_icon} {priority_badge} {task.title}".strip()

                # Use expander for task details
                with st.sidebar.expander(task_text, expanded=False):
                    st.caption(f"**Status:** {task.status}")
                    if task.priority:
                        st.caption(f"**Priority:** {task.priority}")
                    if task.context:
                        st.caption(f"**Context:** {task.context}")
                    if task.notes:
                        st.caption(f"**Notes:** {len(task.notes)}")
                    st.caption(f"**Created:** {task.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if task.last_worked_on:
                        st.caption(f"**Last worked:** {task.last_worked_on.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.sidebar.caption("_No tasks in this project_")

        st.sidebar.divider()

    # Add refresh button
    if st.sidebar.button("🔄 Refresh Tasks", use_container_width=True):
        st.rerun()


def render_debug_panel():
    """Render the debug panel showing all tool calls grouped by conversation turn."""
    st.markdown("### 🔍 Agent Debug")
    st.caption("Complete trace of all tool calls")

    debug_history = st.session_state.get("debug_history", [])

    if not debug_history:
        st.info("No tool calls yet. Send a message to see the agent's work.")
        return

    # Summary stats at the top
    total_turns = len(debug_history)
    slash_turns = sum(1 for turn in debug_history if turn.get("is_slash_command"))
    llm_turns = total_turns - slash_turns
    total_calls = sum(len(turn["tool_calls"]) for turn in debug_history)
    total_time = sum(turn["total_duration_ms"] for turn in debug_history)
    st.caption(f"**{total_turns} turns** ({llm_turns} LLM, {slash_turns} slash) • **{total_calls} operations** • **{total_time}ms total**")

    # Latency breakdown legend
    with st.expander("⏱️ Latency Legend", expanded=False):
        st.markdown("""
        **Component breakdown:**
        - 🔵 **LLM Thinking**: Claude deciding actions and generating responses (typically 500-3000ms)
        - 🟢 **MongoDB Query**: Database read/write operations (typically 50-150ms)
        - 🟡 **Embedding Generation**: Voyage AI API for semantic vectors (typically 200-400ms)
        - ⚪ **Processing**: Python overhead and serialization (typically <50ms)

        *MongoDB is fast! Most latency comes from LLM thinking and external API calls.*
        """)

    # Clear button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.debug_history = []
        st.rerun()

    st.divider()

    # Show turns in chronological order (oldest first, newest last)
    for turn in debug_history:
        # Expand the most recent turn (last in the list)
        is_most_recent = (turn == debug_history[-1])

        # Create expander label with LLM vs Tool breakdown
        user_input_preview = turn["user_input"][:50]
        if len(turn["user_input"]) > 50:
            user_input_preview += "..."

        # Calculate time breakdown
        total_time = turn['total_duration_ms']
        llm_time = turn.get('llm_time_ms', 0)
        tool_time = sum(tc["duration_ms"] for tc in turn["tool_calls"]) if turn["tool_calls"] else 0

        # Calculate percentages (avoid division by zero)
        if total_time > 0:
            llm_pct = int((llm_time / total_time) * 100)
            tool_pct = int((tool_time / total_time) * 100)
        else:
            llm_pct = 0
            tool_pct = 0

        # Build label with breakdown
        # Check if this is a slash command
        is_slash = turn.get("is_slash_command", False)
        command_type = "⚡ Slash" if is_slash else "🤖 LLM"

        expander_label = f"**Turn {turn['turn']}** ({command_type}): {user_input_preview} ({total_time}ms)\n"

        if is_slash:
            # Slash commands: only show DB query time
            expander_label += f"        💾 MongoDB: {total_time}ms (100%)"
        else:
            # LLM-routed: show LLM and tool breakdown
            expander_label += f"        🔵 LLM: {llm_time}ms ({llm_pct}%)"
            if tool_time > 0:
                expander_label += f" • 🛠️ Tools: {tool_time}ms ({tool_pct}%)"

        with st.expander(expander_label, expanded=is_most_recent):
            # Show timestamp
            st.caption(f"🕐 {turn['timestamp']}")

            # Show command type indicator
            if is_slash:
                st.info("⚡ **Slash Command** - Direct MongoDB query (no LLM)")
            else:
                st.info("🤖 **LLM-Routed** - Claude decided and executed tools")

            # Show full user input if it was truncated
            if len(turn["user_input"]) > 50:
                st.caption(f"*Full input: {turn['user_input']}*")

            st.markdown("---")

            # Show each tool call
            for i, call in enumerate(turn["tool_calls"], 1):
                st.markdown(f"**Call {i}:** `{call['name']}`")

                # Two-column layout: details on left, timing/status on right
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Input parameters (collapsible)
                    if call["input"]:
                        with st.expander("Input", expanded=False):
                            st.json(call["input"])
                    else:
                        st.caption("*No input*")

                    # Output summary
                    st.caption(f"**Output:** {call['output']}")

                    # Show search mode metadata if this is a search command
                    if "search" in call["name"]:
                        # Extract mode and target from tool name
                        # e.g., "vector_search_tasks" → mode="vector", target="tasks"
                        tool_name = call["name"]
                        if "vector_search" in tool_name:
                            mode = "vector"
                        elif "text_search" in tool_name:
                            mode = "text"
                        elif "hybrid_search" in tool_name or "search" in tool_name:
                            mode = "hybrid"
                        else:
                            mode = "hybrid"

                        target = "tasks" if "tasks" in tool_name else "projects"

                        # Get query from input
                        query = call.get("input", {}).get("query", "")

                        # Get result count
                        result = call.get("result")
                        if isinstance(result, list):
                            count = len(result)
                        elif isinstance(result, dict):
                            count = result.get("count", len(result.get("results", [])))
                        else:
                            count = 0

                        mode_labels = {
                            "hybrid": "🔍 Hybrid (Vector + Text)",
                            "vector": "🧠 Vector Only (Semantic)",
                            "text": "📝 Text Only (Keyword)"
                        }
                        mode_label = mode_labels.get(mode, mode)

                        st.caption(f"**Search Mode:** {mode_label}")
                        st.caption(f"**Target:** {target.capitalize()} | **Query:** '{query}' | **Results:** {count}")

                    # Show latency breakdown if available
                    if call.get("breakdown"):
                        breakdown = call["breakdown"]

                        # Calculate total time for percentages
                        total_breakdown_time = sum(breakdown.values())

                        # Determine MongoDB operation type based on tool name
                        tool_name = call["name"]
                        mongodb_op_type_map = {
                            "get_tasks": "find query",
                            "get_projects": "find query",
                            "search_tasks": "$rankFusion hybrid",
                            "search_projects": "$rankFusion hybrid",
                            "vector_search_tasks": "$vectorSearch (semantic)",
                            "vector_search_projects": "$vectorSearch (semantic)",
                            "text_search_tasks": "$search (keyword)",
                            "text_search_projects": "$search (keyword)",
                            "hybrid_search_tasks": "$rankFusion hybrid",
                            "hybrid_search_projects": "$rankFusion hybrid",
                            "get_tasks_by_time": "temporal query ($elemMatch)",
                            "complete_task": "update",
                            "start_task": "update",
                            "add_note_to_task": "update"
                        }
                        mongodb_op_type = mongodb_op_type_map.get(tool_name, "query")

                        # Check if get_tasks/get_projects has filters for more specific labeling
                        if tool_name in ["get_tasks", "get_projects"] and call.get("input"):
                            has_filters = any(v for v in call["input"].values() if v)
                            if has_filters:
                                mongodb_op_type = "filtered find"
                            else:
                                mongodb_op_type = "simple find"

                        # Create detailed component mapping
                        component_info = {
                            "embedding_generation": {"emoji": "🟡", "label": "Embedding (Voyage)"},
                            "mongodb_query": {"emoji": "🟢", "label": f"MongoDB ({mongodb_op_type})"},
                            "processing": {"emoji": "⚪", "label": "Processing (Python)"}
                        }

                        # Build breakdown with percentages
                        st.caption("**Breakdown:**")
                        for component, ms in breakdown.items():
                            info = component_info.get(component, {"emoji": "⚪", "label": component.replace("_", " ").title()})
                            emoji = info["emoji"]
                            label = info["label"]

                            # Calculate percentage
                            if total_breakdown_time > 0:
                                pct = int((ms / total_breakdown_time) * 100)
                            else:
                                pct = 0

                            st.caption(f"{emoji} {label}: {ms}ms ({pct}%)")

                with col2:
                    # Duration
                    st.caption(f"⏱️ {call['duration_ms']}ms")

                    # Success/Error indicator
                    if call["success"]:
                        st.success("✓")
                    else:
                        error_msg = call.get("error", "Failed")
                        st.error(f"✗")
                        if error_msg:
                            st.caption(f"*{error_msg}*")

                # Show arrow between calls (except after last call)
                if i < len(turn["tool_calls"]):
                    st.markdown("↓")
                    st.markdown("")  # Add spacing

            # Show LLM calls (Claude thinking/responding)
            if turn.get("llm_calls"):
                # Add separator if there were tool calls
                if turn["tool_calls"]:
                    st.markdown("---")

                st.markdown("**🔵 LLM Thinking**")

                # Group LLM calls by purpose
                llm_time = turn.get("llm_time_ms", 0)
                num_calls = len(turn["llm_calls"])

                # Two-column layout
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Show breakdown of LLM calls
                    for llm_call in turn["llm_calls"]:
                        purpose = llm_call["purpose"].replace("_", " ").title()
                        duration = llm_call["duration_ms"]
                        st.caption(f"• {purpose}: {duration}ms")

                with col2:
                    st.caption(f"⏱️ {llm_time}ms")
                    st.caption(f"({num_calls} call{'s' if num_calls > 1 else ''})")

            # Show memory operations if available
            render_memory_debug(turn)


def render_chat():
    """Render the chat interface."""
    # Add custom CSS for full-height debug panel
    st.markdown("""
    <style>
    [data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 0;
        height: calc(100vh - 100px);
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create two columns: chat (main) and debug panel (sidebar on right)
    chat_col, debug_col = st.columns([2.5, 1.5])

    with chat_col:
        st.title("💬 Flow Companion")
        st.caption("Your AI-powered task and project management assistant")

        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                # Handle different message types
                if message.get("is_command_result"):
                    # Slash command result - render with special formatting
                    render_command_result(message["content"])
                elif message.get("is_slash_command"):
                    # Slash command input - show with terminal style
                    st.markdown(f"⚡ `{message['content']}`")
                    st.caption("*Direct (no LLM)*")
                elif message.get("input_type") == "voice":
                    # Voice input
                    st.markdown(f"🎤 {message['content']}")
                else:
                    # Normal text message
                    st.markdown(message["content"])

                    # Add memory indicators for assistant messages
                    if message["role"] == "assistant" and message.get("memory_ops"):
                        ops = message["memory_ops"]
                        badges = []

                        if ops.get("context_injected"):
                            badges.append("🧠 CR-SH")
                        if ops.get("context_updated"):
                            badges.append("🧠 CW-SH")
                        if ops.get("action_recorded"):
                            action_type = ops.get("recorded_action_type", "")
                            badges.append(f"🧠 AR-T:{action_type}")

                        if badges:
                            st.caption(" • ".join(badges))

        # Chat input
        prompt = st.chat_input("Ask me anything about your tasks or projects...")

        # Voice input
        audio_bytes = st.audio_input("🎤 Or record a voice update")

    with debug_col:
        render_debug_panel()

    # Handle text input
    if prompt:
        # Check if this is a slash command
        parsed_command = parse_slash_command(prompt)

        if parsed_command:
            # Slash command - execute directly without LLM
            # Add command to history
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "input_type": "command",
                "is_slash_command": True
            })

            # Display command with terminal style
            with st.chat_message("user"):
                st.markdown(f"⚡ `{prompt}`")
                st.caption("*Direct (no LLM)*")

            # Execute command and show result
            with st.chat_message("assistant"):
                with st.spinner("Executing..."):
                    result = st.session_state.slash_executor.execute(parsed_command)

                    # Render the result
                    render_command_result(result)

                    # Store result in history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result,
                        "is_command_result": True
                    })

                    # Add to debug history for tracking
                    from datetime import datetime
                    turn_number = len(st.session_state.debug_history) + 1

                    # Build output summary
                    if result.get('success'):
                        result_data = result.get('result', {})
                        if isinstance(result_data, dict):
                            count = result_data.get('count', result_data.get('tasks', result_data.get('projects', 'N/A')))
                            if isinstance(count, list):
                                count = len(count)
                            output_summary = f"Direct DB query - {count} items"
                        elif isinstance(result_data, list):
                            output_summary = f"Direct DB query - {len(result_data)} items"
                        else:
                            output_summary = f"Direct DB query - Success"
                    else:
                        output_summary = f"Error: {result.get('error', 'Unknown')}"

                    slash_turn = {
                        "turn": turn_number,
                        "user_input": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "is_slash_command": True,
                        "command": result.get("command", prompt),
                        "tool_calls": [{
                            "name": f"slash_command_{parsed_command['command']}",
                            "input": {"command": result.get("command")},
                            "output": output_summary,
                            "duration_ms": result.get("duration_ms", 0),
                            "breakdown": None,
                            "success": result.get("success", False),
                            "error": None if result.get("success") else result.get("error")
                        }],
                        "llm_calls": [],  # No LLM for slash commands
                        "llm_time_ms": 0,
                        "total_duration_ms": result.get("duration_ms", 0)
                    }
                    st.session_state.debug_history.append(slash_turn)

            # Rerun to update the display
            st.rerun()

        else:
            # Normal text input - process through LLM
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "input_type": "text"
            })

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Prepare conversation history for the coordinator
                    # Filter out slash commands and their results - they shouldn't be sent to the API
                    history = [
                        msg for msg in st.session_state.messages[:-1]
                        if not msg.get("is_slash_command") and not msg.get("is_command_result")
                    ]

                    # Calculate turn number
                    turn_number = len(st.session_state.debug_history) + 1

                    # Get optimizations from session state
                    optimizations = st.session_state.get("optimizations", {})

                    # Process message through coordinator
                    response = st.session_state.coordinator.process(
                        prompt, history, input_type="text", turn_number=turn_number,
                        optimizations=optimizations, session_id=st.session_state.session_id
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history with memory_ops
            message_data = {
                "role": "assistant",
                "content": response
            }

            # Include memory_ops if available
            if st.session_state.coordinator.current_turn:
                memory_ops = st.session_state.coordinator.current_turn.get("memory_ops")
                if memory_ops:
                    message_data["memory_ops"] = memory_ops

            st.session_state.messages.append(message_data)

            # Rerun to update the display (including task list)
            st.rerun()

    # Handle audio input
    elif audio_bytes:
        # Get bytes from the audio file
        audio_data = audio_bytes.getvalue()

        # Check if this is the same audio we just processed (prevent duplicates)
        if audio_data == st.session_state.last_audio_bytes:
            # Skip - already processed this audio
            return

        # Store this audio as the last processed
        st.session_state.last_audio_bytes = audio_data

        # Show transcribing spinner
        with st.spinner("🎤 Transcribing..."):
            transcript = transcribe_audio(audio_data)

        if transcript:
            # Add user message to history with voice flag
            st.session_state.messages.append({
                "role": "user",
                "content": transcript,
                "input_type": "voice"
            })

            # Display user message with microphone icon
            with st.chat_message("user"):
                st.markdown(f"🎤 {transcript}")

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Prepare conversation history for the coordinator
                    # Filter out slash commands and their results - they shouldn't be sent to the API
                    history = [
                        msg for msg in st.session_state.messages[:-1]
                        if not msg.get("is_slash_command") and not msg.get("is_command_result")
                    ]

                    # Calculate turn number
                    turn_number = len(st.session_state.debug_history) + 1

                    # Get optimizations from session state
                    optimizations = st.session_state.get("optimizations", {})

                    # Process message through coordinator with voice flag
                    response = st.session_state.coordinator.process(
                        transcript, history, input_type="voice", turn_number=turn_number,
                        optimizations=optimizations, session_id=st.session_state.session_id
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history with memory_ops
            message_data = {
                "role": "assistant",
                "content": response
            }

            # Include memory_ops if available
            if st.session_state.coordinator.current_turn:
                memory_ops = st.session_state.coordinator.current_turn.get("memory_ops")
                if memory_ops:
                    message_data["memory_ops"] = memory_ops

            st.session_state.messages.append(message_data)

            # Rerun to update the display (including task list)
            st.rerun()
        else:
            st.error("Failed to transcribe audio. Please try again.")


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Create layout: sidebar for toggles and tasks, main area for chat
    render_context_engineering_toggles()
    render_task_list()
    render_chat()

    # Add footer
    st.markdown("---")
    st.caption("Flow Companion Milestone 2 - Voice Input with Claude & Voyage AI")


if __name__ == "__main__":
    main()
