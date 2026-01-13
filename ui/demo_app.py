"""
Flow Companion - Demo App
Simplified UI for MongoDB Developer Day presentation
Run with: streamlit run ui/demo_app.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import uuid

# Backend imports
from agents.coordinator import coordinator
from shared.db import get_collection, TASKS_COLLECTION, PROJECTS_COLLECTION
from shared.models import Task, Project
from shared.config import settings
from ui.slash_commands import parse_slash_command, detect_natural_language_query, SlashCommandExecutor
from ui.formatters import render_command_result

# Anthropic for episodic memory summaries
from anthropic import Anthropic


# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Flow Companion - Demo",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ═══════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Tighter spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }

    /* Compact checkboxes */
    .stCheckbox {
        padding: 0.1rem 0;
    }

    /* Hide hamburger menu and footer for cleaner demo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "coordinator" not in st.session_state:
        st.session_state.coordinator = coordinator

    if "slash_executor" not in st.session_state:
        st.session_state.slash_executor = SlashCommandExecutor(coordinator)

    if "debug_history" not in st.session_state:
        st.session_state.debug_history = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "user_id" not in st.session_state:
        st.session_state.user_id = "demo_user"

    if "mcp_enabled" not in st.session_state:
        st.session_state.mcp_enabled = False

    if "mcp_initialized" not in st.session_state:
        st.session_state.mcp_initialized = False

    # Set coordinator session for memory isolation
    if coordinator and hasattr(coordinator, 'set_session'):
        coordinator.set_session(
            st.session_state.session_id,
            user_id=st.session_state.user_id
        )


# ═══════════════════════════════════════════════════════════════════
# DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_all_projects_with_tasks() -> List[Dict[str, Any]]:
    """Get all projects with their associated tasks from MongoDB."""
    projects_collection = get_collection(PROJECTS_COLLECTION)
    tasks_collection = get_collection(TASKS_COLLECTION)

    # Get all projects (not just active) and exclude test projects
    projects_cursor = projects_collection.find(
        {"is_test": {"$ne": True}}
    ).sort([("status", 1), ("last_activity", -1)])

    projects_with_tasks = []

    for project_doc in projects_cursor:
        project = Project(**project_doc)
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


def get_memory_stats() -> Dict[str, int]:
    """Get memory statistics from the coordinator."""
    if coordinator and coordinator.memory:
        try:
            stats = coordinator.memory.get_memory_stats(
                st.session_state.session_id,
                st.session_state.user_id
            )
            by_type = stats.get("by_type", {})
            return {
                "working": by_type.get("working_memory", 0),
                "episodic": by_type.get("episodic_memory", 0),
                "semantic": by_type.get("semantic_memory", 0),
                "procedural": by_type.get("procedural_memory", 0),
                "shared": by_type.get("memory_shared", 0),
            }
        except Exception:
            pass
    return {"working": 0, "episodic": 0, "semantic": 0, "procedural": 0, "shared": 0}


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


def generate_task_episodic_summary(task: Task) -> str:
    """Generate AI summary from task's episodic memory (activity log) using Haiku."""
    try:
        # Format activity log
        activity_text = ""
        for entry in task.activity_log[-10:]:  # Last 10 entries
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M") if entry.timestamp else "N/A"
            activity_text += f"- {timestamp}: {entry.action}"
            if entry.note:
                activity_text += f" - {entry.note}"
            activity_text += "\n"

        if not activity_text:
            activity_text = "- Task created (no additional activity recorded)"

        # Build prompt
        prompt = f"""Summarize this task's episodic memory (activity history) in 2-3 concise sentences.

Task: {task.title}
Status: {task.status}
Priority: {task.priority or 'none'}
Created: {task.created_at.strftime('%Y-%m-%d') if task.created_at else 'N/A'}

Activity History (Episodic Memory):
{activity_text}

Provide a brief summary focusing on current state and recent progress. Be concise and factual."""

        # Use Haiku for speed and cost efficiency
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except Exception as e:
        return f"Unable to generate summary: {str(e)}"


def generate_project_episodic_summary(project: Project, tasks: List[Task]) -> str:
    """Generate AI summary from project's episodic memory (all task activity) using Haiku."""
    try:
        # Aggregate all task activity
        all_activity = []
        for task in tasks:
            for entry in task.activity_log:
                all_activity.append({
                    "task": task.title,
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "note": entry.note
                })

        # Sort by timestamp descending (most recent first)
        all_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = all_activity[:20]  # Last 20 events

        # Format activity
        activity_text = ""
        for event in recent_activity:
            timestamp = event["timestamp"].strftime("%Y-%m-%d %H:%M") if event["timestamp"] else "N/A"
            activity_text += f"- {timestamp}: [{event['task']}] {event['action']}"
            if event.get("note"):
                activity_text += f" - {event['note']}"
            activity_text += "\n"

        if not activity_text:
            activity_text = "- No recent activity recorded"

        # Calculate task metrics
        task_counts = {
            "total": len(tasks),
            "todo": len([t for t in tasks if t.status == "todo"]),
            "in_progress": len([t for t in tasks if t.status == "in_progress"]),
            "done": len([t for t in tasks if t.status == "done"])
        }

        # Build prompt
        prompt = f"""Summarize this project's episodic memory in 3-4 concise sentences.

Project: {project.name}
Status: {project.status}
Tasks: {task_counts['total']} total ({task_counts['in_progress']} in progress, {task_counts['done']} done, {task_counts['todo']} todo)

Recent Activity (Last 20 events across all tasks):
{activity_text}

Focus on: current momentum, what's being worked on, recent completions, and project health. Be concise and factual."""

        # Use Haiku for speed and cost efficiency
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except Exception as e:
        return f"Unable to generate summary: {str(e)}"


def render_task_with_metadata(task):
    """Render a task as a collapsible expander with full metadata."""
    from datetime import datetime

    # Build header: status icon + priority + title
    status_icon = get_status_icon(task.status)
    priority_badge = get_priority_badge(task.priority) if task.priority else ""
    header = f"{status_icon} {priority_badge} {task.title}"

    with st.expander(header, expanded=False):
        # Generate episodic memory summary (cached in session state)
        task_id_str = str(task.id) if task.id else "unknown"

        # Initialize cache if needed
        if "task_episodic_summaries" not in st.session_state:
            st.session_state.task_episodic_summaries = {}

        # Generate summary if not cached
        if task_id_str not in st.session_state.task_episodic_summaries:
            with st.spinner("🧠 Generating episodic memory summary..."):
                summary = generate_task_episodic_summary(task)
                st.session_state.task_episodic_summaries[task_id_str] = summary

        # Display episodic memory summary
        st.markdown("**🧠 Episodic Memory Summary**")
        st.info(st.session_state.task_episodic_summaries[task_id_str])

        st.divider()

        # Create two columns for metadata
        col1, col2 = st.columns(2)

        with col1:
            st.caption("**Status:**")
            st.text(task.status.replace("_", " ").title())

            if task.priority:
                st.caption("**Priority:**")
                st.text(task.priority.title())

            st.caption("**Created:**")
            created_date = task.created_at.strftime("%Y-%m-%d") if task.created_at else "N/A"
            st.text(created_date)

        with col2:
            if task.started_at:
                st.caption("**Started:**")
                started_date = task.started_at.strftime("%Y-%m-%d")
                st.text(started_date)

            if task.completed_at:
                st.caption("**Completed:**")
                completed_date = task.completed_at.strftime("%Y-%m-%d")
                st.text(completed_date)

            st.caption("**ID:**")
            task_id = str(task.id)[:8] if task.id else "N/A"
            st.text(task_id)

        # Show context if available
        if task.context:
            st.caption("**Context:**")
            st.text(task.context[:200] + "..." if len(task.context) > 200 else task.context)

        # Show notes if available
        if task.notes:
            st.caption(f"**Notes:** ({len(task.notes)})")
            for note in task.notes[:3]:
                st.text(f"• {note}")
            if len(task.notes) > 3:
                st.caption(f"... and {len(task.notes) - 3} more")


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════

def render_sidebar():
    """Render the simplified sidebar."""
    with st.sidebar:
        st.title("🎯 Flow Companion")
        st.caption("Demo Mode")

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # CONTEXT ENGINEERING (single toggle for all 3 optimizations)
        # ─────────────────────────────────────────────────────────────────
        st.subheader("⚡ Context Engineering")
        context_engineering = st.toggle(
            "Enable Optimizations",
            value=True,
            help="Enables: Compress Results, Streamlined Prompt, Prompt Caching"
        )

        # Store all three optimizations with the same value
        st.session_state.optimizations = {
            "compress_results": context_engineering,
            "streamlined_prompt": context_engineering,
            "prompt_caching": context_engineering,
        }

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # MCP TOGGLE
        # ─────────────────────────────────────────────────────────────────
        st.subheader("🧪 Experimental")

        mcp_available = settings.mcp_available

        if not mcp_available:
            st.warning("⚠️ MCP not configured")
            mcp_enabled = False
        else:
            mcp_enabled = st.toggle(
                "MCP Mode",
                value=st.session_state.get("mcp_enabled", False),
                help="Enable dynamic tool discovery (Tavily)"
            )
            st.session_state.mcp_enabled = mcp_enabled

            # Initialize MCP when enabled
            if mcp_enabled and not st.session_state.get("mcp_initialized"):
                with st.spinner("🔬 Connecting to Tavily..."):
                    try:
                        status = asyncio.run(coordinator.enable_mcp_mode())
                        st.session_state.mcp_initialized = True
                        st.session_state.mcp_status = status
                        if status.get("success"):
                            tools = coordinator.mcp_agent.get_all_tools() if coordinator.mcp_agent else []
                            st.success(f"✅ tavily: {len(tools)} tools")
                        else:
                            st.error(f"❌ Failed: {status.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        st.session_state.mcp_enabled = False
                        mcp_enabled = False

            # Show tool count when connected
            if mcp_enabled and st.session_state.get("mcp_initialized"):
                if coordinator.mcp_agent:
                    tools = coordinator.mcp_agent.get_all_tools()
                    st.caption(f"🔌 MCP Servers: 1 connected (Tavily)")
                    st.caption(f"🛠️ Tools available: {len(tools)}")

            # Disable when toggled off
            if not mcp_enabled and st.session_state.get("mcp_initialized"):
                coordinator.disable_mcp_mode()

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # MEMORY SECTION (with 5 individual toggles)
        # ─────────────────────────────────────────────────────────────────
        col_header, col_toggle = st.columns([3, 1])
        with col_header:
            st.subheader("🧠 Memory")
        with col_toggle:
            memory_enabled = st.toggle("", value=True, key="memory_master")

        if memory_enabled:
            # Compact 2-column grid of all 5 memory types
            col1, col2 = st.columns(2)
            with col1:
                working = st.checkbox("Working", value=True, key="mem_working",
                                     help="Session context (2hr TTL)")
                episodic = st.checkbox("Episodic", value=True, key="mem_episodic",
                                      help="Action history (persistent)")
                semantic = st.checkbox("Semantic", value=True, key="mem_semantic",
                                      help="Learned preferences (persistent)")
            with col2:
                procedural = st.checkbox("Procedural", value=True, key="mem_procedural",
                                        help="Templates & workflows (persistent)")
                shared = st.checkbox("Shared", value=True, key="mem_shared",
                                    help="Agent handoffs (5min TTL)")

            # Update coordinator memory config
            # Map individual toggles to coordinator's expected format
            if coordinator:
                coordinator.memory_config = {
                    "short_term": working,  # Working memory
                    "long_term": episodic or semantic or procedural,  # Any long-term memory type
                    "shared": shared,  # Shared memory
                    "context_injection": True  # Always inject when memory enabled
                }

            # Collapsible memory stats
            with st.expander("📊 Memory Stats", expanded=False):
                stats = get_memory_stats()
                stat_cols = st.columns(5)
                stat_data = [
                    ("Working", stats.get("working", 0)),
                    ("Episodic", stats.get("episodic", 0)),
                    ("Semantic", stats.get("semantic", 0)),
                    ("Procedural", stats.get("procedural", 0)),
                    ("Shared", stats.get("shared", 0))
                ]
                for col, (name, value) in zip(stat_cols, stat_data):
                    with col:
                        st.metric(name, value, label_visibility="collapsed")
                        st.caption(name[:4])  # Show abbreviated name
        else:
            # Memory disabled - update coordinator
            if coordinator:
                coordinator.memory_config = {
                    "short_term": False,
                    "long_term": False,
                    "shared": False,
                    "context_injection": False
                }

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # PROJECTS SECTION
        # ─────────────────────────────────────────────────────────────────
        st.subheader("📁 Projects")

        # Legend
        with st.expander("ℹ️ Legend", expanded=False):
            st.caption("**Task Status:** ○ Todo  •  ◐ In Progress  •  ✓ Done")
            st.caption("**Task Priority:** 🔴 High  •  🟡 Medium  •  🟢 Low")
            st.caption("**Project Status:** 📁 Active  •  📋 Planned  •  ✅ Completed")

        projects_with_tasks = get_all_projects_with_tasks()

        if projects_with_tasks:
            for item in projects_with_tasks:
                project = item["project"]
                tasks = item["tasks"]

                if project:
                    # Select icon based on project status
                    if project.status == "completed":
                        icon = "✅"
                    elif project.status == "planned":
                        icon = "📋"
                    else:  # active or archived
                        icon = "📁"

                    with st.expander(f"{icon} {project.name}", expanded=False):
                        if project.description:
                            st.caption(project.description)
                        if project.status:
                            st.caption(f"Status: {project.status.title()}")

                        # Generate project episodic memory summary (cached in session state)
                        project_id_str = str(project.id) if project.id else "unknown"

                        # Initialize cache if needed
                        if "project_episodic_summaries" not in st.session_state:
                            st.session_state.project_episodic_summaries = {}

                        # Generate summary if not cached
                        if project_id_str not in st.session_state.project_episodic_summaries:
                            with st.spinner("🧠 Generating project episodic memory summary..."):
                                summary = generate_project_episodic_summary(project, tasks)
                                st.session_state.project_episodic_summaries[project_id_str] = summary

                        # Display project episodic memory summary
                        st.markdown("**🧠 Project Episodic Memory**")
                        st.success(st.session_state.project_episodic_summaries[project_id_str])

                        st.divider()

                        if tasks:
                            for task in tasks[:10]:  # Show max 10 tasks per project
                                render_task_with_metadata(task)

                            if len(tasks) > 10:
                                st.caption(f"... and {len(tasks) - 10} more tasks")
                        else:
                            st.caption("No tasks")
                else:
                    # Orphan tasks
                    if tasks:
                        with st.expander(f"📋 Other Tasks ({len(tasks)})", expanded=False):
                            for task in tasks[:10]:  # Show max 10 orphan tasks
                                render_task_with_metadata(task)

                            if len(tasks) > 10:
                                st.caption(f"... and {len(tasks) - 10} more tasks")
        else:
            st.caption("No projects found")

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # REFRESH BUTTON
        # ─────────────────────────────────────────────────────────────────
        if st.button("🔄 Refresh Tasks", use_container_width=True, help="Reload tasks and projects from database"):
            st.rerun()

        st.divider()

        # ─────────────────────────────────────────────────────────────────
        # SESSION CONTROLS
        # ─────────────────────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear session memory"):
                if coordinator and coordinator.memory:
                    coordinator.memory.clear_session(st.session_state.session_id)
                st.session_state.messages = []
                st.session_state.debug_history = []
                st.rerun()
        with col2:
            if st.button("🔄 New", use_container_width=True, help="Start new session"):
                if coordinator and coordinator.memory:
                    coordinator.memory.clear_session(st.session_state.session_id)
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.debug_history = []
                st.session_state.mcp_initialized = False
                if coordinator and hasattr(coordinator, 'set_session'):
                    coordinator.set_session(
                        st.session_state.session_id,
                        user_id=st.session_state.user_id
                    )
                st.rerun()


# ═══════════════════════════════════════════════════════════════════
# DEBUG PANEL
# ═══════════════════════════════════════════════════════════════════

def render_debug_panel():
    """Render the debug panel showing tool calls."""
    st.subheader("🔍 Agent Debug")
    st.caption("Complete trace of all tool calls")

    debug_history = st.session_state.get("debug_history", [])

    if not debug_history:
        st.info("No tool calls yet. Send a message to see the agent's work.")
        return

    # Summary stats
    total_turns = len(debug_history)
    slash_turns = sum(1 for turn in debug_history if turn.get("is_slash_command"))
    total_calls = sum(len(turn.get("tool_calls", [])) for turn in debug_history)
    total_time = sum(turn.get("total_duration_ms", 0) for turn in debug_history)

    st.caption(f"**{total_turns} turns** • **{total_calls} ops** • **{total_time:.0f}ms**")

    if st.button("🗑️ Clear Debug", use_container_width=True):
        st.session_state.debug_history = []
        st.rerun()

    st.divider()

    # Show each turn (most recent expanded)
    for idx, turn in enumerate(reversed(debug_history)):
        is_most_recent = (idx == 0)

        user_input_preview = turn.get("user_input", "")[:40]
        if len(turn.get("user_input", "")) > 40:
            user_input_preview += "..."

        total_time = turn.get('total_duration_ms', 0)
        is_slash = turn.get("is_slash_command", False)
        command_type = "⚡" if is_slash else "🤖"

        turn_num = len(debug_history) - idx
        expander_label = f"{command_type} **T{turn_num}**: {user_input_preview} ({total_time:.0f}ms)"

        with st.expander(expander_label, expanded=is_most_recent):
            st.caption(f"🕐 {turn.get('timestamp', '')}")

            if is_slash:
                st.info("⚡ **Slash Command** - Direct MongoDB (no LLM)")
            else:
                st.info("🤖 **Agent** - Claude + tools")

            # Show tool calls
            tool_calls = turn.get("tool_calls", [])
            for i, call in enumerate(tool_calls, 1):
                status_icon = "✅" if call.get("success", True) else "❌"
                new_badge = "🆕 " if call.get("new_discovery") else ""

                st.markdown(f"**{i}. {new_badge}{call.get('name', 'unknown')}** {status_icon}")
                st.caption(f"⏱️ {call.get('duration_ms', 0):.0f}ms")

                # Show input (collapsed by default)
                if call.get("input"):
                    with st.expander("📥 Input", expanded=False):
                        st.json(call["input"])

                # Show output preview
                output = call.get('output', 'N/A')
                if isinstance(output, str) and len(output) > 100:
                    st.caption(f"**Output:** {output[:100]}...")
                else:
                    st.caption(f"**Output:** {output}")

                # Show breakdown if available
                if call.get("breakdown"):
                    with st.expander("⏱️ Timing Breakdown", expanded=False):
                        for component, ms in call["breakdown"].items():
                            st.caption(f"• {component}: {ms:.0f}ms")

                # Arrow between tool calls
                if i < len(tool_calls):
                    st.markdown("↓")

            # Show LLM calls if present
            if turn.get("llm_calls"):
                st.markdown("---")
                st.markdown("**🔵 LLM Thinking**")
                llm_time = turn.get("llm_time_ms", 0)
                num_calls = len(turn['llm_calls'])
                st.caption(f"⏱️ {llm_time:.0f}ms ({num_calls} call{'s' if num_calls > 1 else ''})")


# ═══════════════════════════════════════════════════════════════════
# MAIN CHAT
# ═══════════════════════════════════════════════════════════════════

def render_chat():
    """Render the main chat interface."""
    col_main, col_debug = st.columns([3, 2])

    with col_main:
        st.title("💬 Flow Companion")
        st.caption("Your AI-powered task and project management assistant")

        # Chat container with fixed height
        chat_container = st.container(height=500)

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message.get("is_command_result"):
                        render_command_result(message["content"])
                    elif message.get("is_slash_command"):
                        st.markdown(f"⚡ `{message['content']}`")
                        st.caption("*Direct MongoDB query*")
                    else:
                        st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Try /tasks or ask a question..."):
            handle_input(prompt)

    with col_debug:
        render_debug_panel()


def handle_input(prompt: str):
    """Handle user input - auto-detect natural language queries, slash commands, or use agent."""
    # First, try to detect natural language queries that map to slash commands
    nl_command = detect_natural_language_query(prompt)
    if nl_command:
        # Convert natural language to slash command
        parsed_command = parse_slash_command(nl_command)
        original_prompt = prompt  # Save original for display
        prompt = nl_command  # Use slash command for execution
    else:
        # Try parsing as explicit slash command
        parsed_command = parse_slash_command(prompt)
        original_prompt = prompt

    if parsed_command:
        # ═════════════════════════════════════════════════════════════════
        # SLASH COMMAND
        # ═════════════════════════════════════════════════════════════════
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "is_slash_command": True
        })

        result = st.session_state.slash_executor.execute(parsed_command)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result,
            "is_command_result": True
        })

        # Add to debug history
        turn_number = len(st.session_state.debug_history) + 1
        st.session_state.debug_history.append({
            "turn": turn_number,
            "user_input": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "is_slash_command": True,
            "tool_calls": [{
                "name": f"slash_{parsed_command['command']}",
                "input": {"command": prompt},
                "output": f"Success" if result.get("success") else f"Error: {result.get('error')}",
                "duration_ms": result.get("duration_ms", 0),
                "success": result.get("success", False)
            }],
            "total_duration_ms": result.get("duration_ms", 0)
        })

    else:
        # ═════════════════════════════════════════════════════════════════
        # AGENT (with optional MCP)
        # ═════════════════════════════════════════════════════════════════
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Filter history for API (exclude slash commands and results)
        history = [
            msg for msg in st.session_state.messages[:-1]
            if not msg.get("is_slash_command") and not msg.get("is_command_result")
        ]

        turn_number = len(st.session_state.debug_history) + 1

        # Process through coordinator
        result = st.session_state.coordinator.process(
            prompt,
            history,
            input_type="text",
            turn_number=turn_number,
            session_id=st.session_state.session_id,
            return_debug=True
        )

        # Handle response
        if isinstance(result, dict):
            response = result.get("response", "")
            debug_info = result.get("debug", {})
        else:
            response = result
            debug_info = {}

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        # Add to debug history
        if st.session_state.coordinator.current_turn:
            st.session_state.debug_history.append(st.session_state.coordinator.current_turn)

    st.rerun()


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    render_chat()

    st.markdown("---")
    st.caption("Flow Companion Demo | MongoDB Developer Day 2026")


if __name__ == "__main__":
    main()
