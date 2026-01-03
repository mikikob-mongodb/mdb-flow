"""Streamlit Chat UI for Flow Companion."""

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


def render_chat():
    """Render the chat interface."""
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

                # Process message through coordinator
                response = st.session_state.coordinator.process(prompt, history, input_type="text")

                # Display response
                st.markdown(response)

        # Add assistant response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        # Rerun to update the display (including task list)
        st.rerun()

    # Handle audio input
    elif audio_bytes:
        # Show transcribing spinner
        with st.spinner("🎤 Transcribing..."):
            # Get bytes from the audio file
            audio_data = audio_bytes.getvalue()
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

                    # Process message through coordinator with voice flag
                    response = st.session_state.coordinator.process(transcript, history, input_type="voice")

                    # Display response
                    st.markdown(response)

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
