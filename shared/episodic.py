"""Episodic memory generation utilities for Flow Companion.

Automatically generates AI summaries of activity history for tasks and projects.
Summaries are stored in memory_episodic collection in Atlas.
"""

from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from anthropic import Anthropic

from shared.config import settings
from shared.models import Task, Project


def generate_task_episodic_summary(task: Task) -> str:
    """Generate AI summary from task's episodic memory (activity log) using Haiku.

    Args:
        task: Task model with activity_log

    Returns:
        AI-generated summary string
    """
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
    """Generate AI summary from project's episodic memory (all task activity) using Haiku.

    Args:
        project: Project model with activity_log
        tasks: List of tasks belonging to this project

    Returns:
        AI-generated summary string
    """
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


def should_generate_task_summary(task_activity_count: int) -> bool:
    """Determine if a new episodic summary should be generated for a task.

    Generate every 3-5 activity log entries (using modulo to catch multiples of 4).

    Args:
        task_activity_count: Number of activity log entries in the task

    Returns:
        True if summary should be generated
    """
    # Generate on creation (count=1) and every 4 entries after (5, 9, 13, etc.)
    return task_activity_count == 1 or task_activity_count % 4 == 1


def should_generate_project_summary(
    old_description: Optional[str],
    new_description: Optional[str],
    old_notes: Optional[List[str]],
    new_notes: Optional[List[str]]
) -> bool:
    """Determine if a new episodic summary should be generated for a project.

    Generate when description or notes change.

    Args:
        old_description: Previous project description
        new_description: New project description
        old_notes: Previous project notes list
        new_notes: New project notes list

    Returns:
        True if summary should be generated
    """
    # Description changed
    if old_description != new_description:
        return True

    # Notes changed (added or removed)
    old_notes_set = set(old_notes or [])
    new_notes_set = set(new_notes or [])
    if old_notes_set != new_notes_set:
        return True

    return False
