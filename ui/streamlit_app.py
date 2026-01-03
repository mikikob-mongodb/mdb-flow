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
    total_calls = sum(len(turn["tool_calls"]) for turn in debug_history)
    total_time = sum(turn["total_duration_ms"] for turn in debug_history)
    st.caption(f"**{total_turns} turns** • **{total_calls} tool calls** • **{total_time}ms total**")

    # Clear button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.debug_history = []
        st.rerun()

    st.divider()

    # Show turns in reverse order (most recent first)
    for turn in reversed(debug_history):
        # Determine if this is the most recent turn (should be expanded)
        is_most_recent = (turn == debug_history[-1])

        # Create expander label
        user_input_preview = turn["user_input"][:50]
        if len(turn["user_input"]) > 50:
            user_input_preview += "..."

        expander_label = f"**Turn {turn['turn']}**: {user_input_preview} ({turn['total_duration_ms']}ms)"

        with st.expander(expander_label, expanded=is_most_recent):
            # Show timestamp
            st.caption(f"🕐 {turn['timestamp']}")

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
                # Add microphone icon for voice messages
                if message.get("input_type") == "voice":
                    st.markdown(f"🎤 {message['content']}")
                else:
                    st.markdown(message["content"])

        # Chat input
        prompt = st.chat_input("Ask me anything about your tasks or projects...")

        # Voice input
        audio_bytes = st.audio_input("🎤 Or record a voice update")

    with debug_col:
        render_debug_panel()

    # Handle text input
    if prompt:
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
                history = st.session_state.messages[:-1]  # Exclude the current message

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
                    history = st.session_state.messages[:-1]  # Exclude the current message

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

    # Create layout: sidebar for tasks, main area for chat
    render_task_list()
    render_chat()

    # Add footer
    st.markdown("---")
    st.caption("Flow Companion Milestone 2 - Voice Input with Claude & Voyage AI")


if __name__ == "__main__":
    main()
