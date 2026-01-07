"""Table formatting functions for slash command results."""

import streamlit as st
from typing import Dict, Any


def format_tasks_table(tasks, show_raw=False):
    """Format tasks as a markdown table."""
    if not tasks:
        return "No tasks found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Header
    lines = ["| # | Title | Status | Priority | Project | Last Activity |"]
    lines.append("|---|-------|--------|----------|---------|---------------|")

    for i, task in enumerate(tasks, 1):
        title = task.get("title", "Untitled")[:40]
        if len(task.get("title", "")) > 40:
            title += "..."

        status = task.get("status", "-")
        priority = task.get("priority") or "-"
        project = task.get("project_name") or "-"

        # Get last activity timestamp
        activity_log = task.get("activity_log", [])
        if activity_log:
            last = activity_log[-1].get("timestamp")
            if last:
                # Handle both datetime objects and strings
                if hasattr(last, 'strftime'):
                    last_activity = last.strftime("%b %d")
                else:
                    # Parse string if needed
                    last_activity = str(last)[:10]
            else:
                last_activity = "-"
        else:
            last_activity = "-"

        lines.append(f"| {i} | {title} | {status} | {priority} | {project} | {last_activity} |")

    return "\n".join(lines)


def format_projects_table(projects, show_raw=False):
    """Format projects as a markdown table."""
    if not projects:
        return "No projects found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Check if these are search results (have score field)
    is_search_results = len(projects) > 0 and "score" in projects[0]

    if is_search_results:
        # Header for search results
        lines = ["| # | Name | Score | Description | Todo | In Progress | Done | Total |"]
        lines.append("|---|------|-------|-------------|------|-------------|------|-------|")

        for i, project in enumerate(projects, 1):
            name = project.get("name", "Untitled")[:25]
            if len(project.get("name", "")) > 25:
                name += "..."

            score = project.get("score", "-")
            if isinstance(score, float):
                score = f"{score:.2f}"

            description = project.get("description", "")[:30]
            if len(project.get("description", "")) > 30:
                description += "..."
            if not description:
                description = "-"

            # Get task counts
            tasks_todo = project.get("todo_count", 0)
            tasks_in_progress = project.get("in_progress_count", 0)
            tasks_done = project.get("done_count", 0)
            tasks_total = project.get("total_tasks", 0)

            lines.append(f"| {i} | {name} | {score} | {description} | {tasks_todo} | {tasks_in_progress} | {tasks_done} | {tasks_total} |")
    else:
        # Header for regular list
        lines = ["| # | Name | Description | Todo | In Progress | Done | Total |"]
        lines.append("|---|------|-------------|------|-------------|------|-------|")

        for i, project in enumerate(projects, 1):
            name = project.get("name", "Untitled")[:30]
            if len(project.get("name", "")) > 30:
                name += "..."

            description = project.get("description", "")[:40]
            if len(project.get("description", "")) > 40:
                description += "..."
            if not description:
                description = "-"

            # Get task counts from aggregation
            tasks_todo = project.get("todo_count", 0)
            tasks_in_progress = project.get("in_progress_count", 0)
            tasks_done = project.get("done_count", 0)
            tasks_total = project.get("total_tasks", 0)

            lines.append(f"| {i} | {name} | {description} | {tasks_todo} | {tasks_in_progress} | {tasks_done} | {tasks_total} |")

    return "\n".join(lines)


def format_search_results_table(results, show_raw=False):
    """Format TASK search results as a markdown table."""
    if not results:
        return "No results found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Header
    lines = ["| # | Title | Score | Status | Project | Priority |"]
    lines.append("|---|-------|-------|--------|---------|----------|")

    for i, item in enumerate(results, 1):
        title = item.get("title", "Untitled")[:50]
        if len(item.get("title", "")) > 50:
            title += "..."

        # Score from hybrid search
        score = item.get("score", "-")
        if isinstance(score, float):
            score = f"{score:.2f}"

        status = item.get("status", "-")
        project = item.get("project_name") or "-"
        priority = item.get("priority") or "-"

        lines.append(f"| {i} | {title} | {score} | {status} | {project} | {priority} |")

    return "\n".join(lines)


def format_project_search_results_table(results, show_raw=False):
    """Format PROJECT search results as a markdown table."""
    if not results:
        return "No results found."

    if show_raw:
        return None  # Signal to show JSON instead

    # Header for project search results
    lines = ["| # | Name | Description | Status | Score |"]
    lines.append("|---|------|-------------|--------|-------|")

    for i, project in enumerate(results, 1):
        name = project.get("name", "Untitled")[:40]
        if len(project.get("name", "")) > 40:
            name += "..."

        description = project.get("description", "")[:50]
        if len(project.get("description", "")) > 50:
            description += "..."
        if not description:
            description = "-"

        status = project.get("status", "active")

        # Score from hybrid search
        score = project.get("score", "-")
        if isinstance(score, float):
            score = f"{score:.2f}"

        lines.append(f"| {i} | {name} | {description} | {status} | {score} |")

    return "\n".join(lines)


def render_command_result(result: Dict[str, Any]):
    """Render the result of a slash command execution."""
    if not result.get("success"):
        # Show error
        st.error(f"❌ Command failed: {result.get('error', 'Unknown error')}")
        return

    # Show success banner with timing
    duration = result.get("duration_ms", 0)
    st.success(f"✓ Executed in {duration}ms")

    data = result.get("result", {})
    show_raw = result.get("show_raw", False)

    # Handle different result types
    if isinstance(data, dict) and "error" in data:
        st.error(f"❌ {data['error']}")
    elif isinstance(data, dict) and data.get("type") == "project_detail":
        # Project detail view with tasks
        project = data.get("project", {})
        tasks = data.get("tasks", [])

        st.markdown(f"**Project:** {project.get('name', 'Untitled')}")
        if project.get("description"):
            st.markdown(f"*{project.get('description')}*")

        st.markdown(f"**Status:** {data.get('todo_count', 0)} todo • {data.get('in_progress_count', 0)} in progress • {data.get('done_count', 0)} done")
        st.markdown("")

        if tasks:
            st.markdown(f"**Tasks ({len(tasks)}):**")
            table = format_tasks_table(tasks, show_raw)
            if table:
                st.markdown(table)
            else:
                st.json(tasks)
        else:
            st.info("No tasks in this project")
    elif "help_text" in data or "help" in data:
        # Help output
        help_text = data.get("help_text") or data.get("help")
        st.code(help_text, language=None)
    elif isinstance(data, dict) and "results" in data:
        # Search results with metadata
        mode = data.get("mode", "hybrid")
        target = data.get("target", "tasks")
        query = data.get("query", "")
        count = data.get("count", 0)
        results = data.get("results", [])

        # Display metadata
        mode_labels = {
            "hybrid": "🔍 Hybrid (Vector + Text)",
            "vector": "🧠 Vector Only (Semantic)",
            "text": "📝 Text Only (Keyword)"
        }
        mode_label = mode_labels.get(mode, mode.title())

        st.caption(f"**Search Mode:** {mode_label} | **Target:** {target.title()} | **Query:** '{query}' | **Results:** {count}")
        st.markdown("")

        # Display results based on target type
        if count == 0:
            st.info("No results found")
        elif target == "tasks":
            # Check if it's a search result (has score) or regular task list
            if results and isinstance(results[0], dict) and "score" in results[0]:
                table = format_search_results_table(results, show_raw)
            else:
                table = format_tasks_table(results, show_raw)

            if table:
                st.markdown(table)
            else:
                st.json(results)
        elif target == "projects":
            # Check if it's a search result (has score) or regular project list
            if results and isinstance(results[0], dict) and "score" in results[0]:
                table = format_project_search_results_table(results, show_raw)
            else:
                table = format_projects_table(results, show_raw)

            if table:
                st.markdown(table)
            else:
                st.json(results)
        else:
            st.json(results)
    elif "commands" in data:
        # Help output - legacy format
        st.markdown("**Available Commands:**")
        for cmd in data["commands"]:
            st.markdown(f"**`{cmd['command']}`** - {cmd['description']}")
            if cmd.get("examples"):
                st.caption(f"Examples: {', '.join(f'`{ex}`' for ex in cmd['examples'])}")
        if data.get("note"):
            st.info(data["note"])
    elif isinstance(data, list):
        # List of tasks, projects, or search results
        if len(data) == 0:
            st.info("No results found")
        else:
            # Determine type and format appropriately
            first_item = data[0]

            # Check if it's a PROJECT SEARCH result (has both "name" and "score" fields)
            if isinstance(first_item, dict) and "name" in first_item and "score" in first_item:
                table = format_project_search_results_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} project(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            # Check if it's a project list (has "name" but no "score")
            elif isinstance(first_item, dict) and "name" in first_item:
                table = format_projects_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} project(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            # Check if it's a TASK search result (has "score" and "title")
            elif isinstance(first_item, dict) and "score" in first_item and "title" in first_item:
                table = format_search_results_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} result(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            # Check if it's a task list (has "title" and "status" but no "score")
            elif isinstance(first_item, dict) and "title" in first_item and "status" in first_item:
                table = format_tasks_table(data, show_raw)
                if table:
                    st.markdown(f"**Found {len(data)} task(s):**")
                    st.markdown(table)
                else:
                    st.json(data)
            else:
                # Unknown type - show as JSON
                st.json(data)
    else:
        # Generic result - show as JSON
        st.json(data)
