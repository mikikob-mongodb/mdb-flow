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

    # Store in session state
    st.session_state.optimizations = {
        "compress_results": compress_results,
        "streamlined_prompt": streamline_prompt,
        "prompt_caching": cache_prompts
    }

    # Show active status
    active = []
    if compress_results:
        active.append("📦")
    if streamline_prompt:
        active.append("⚡")
    if cache_prompts:
        active.append("💾")
    st.sidebar.caption(f"Active: {' '.join(active) if active else 'None'}")

    st.sidebar.markdown("---")


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
        for message in st.session_state.messages:
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

                    # Process message through coordinator
                    response = st.session_state.coordinator.process(
                        prompt, history, input_type="text", turn_number=turn_number
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

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

                    # Process message through coordinator with voice flag
                    response = st.session_state.coordinator.process(
                        transcript, history, input_type="voice", turn_number=turn_number
                    )

                    # Display response
                    st.markdown(response)

                    # Store debug info in session state (backwards compatibility)
                    st.session_state.last_debug_info = st.session_state.coordinator.last_debug_info

                    # Append current turn to debug history
                    if st.session_state.coordinator.current_turn:
                        st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

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
