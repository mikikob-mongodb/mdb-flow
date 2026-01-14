"""Context engineering utilities for optimizing LLM API calls."""

from typing import Dict, Any, List


def compress_tool_result(tool_name: str, result: dict, compress: bool = True) -> dict:
    """
    Compress tool results to reduce context size.

    Args:
        tool_name: Name of the tool that produced the result
        result: The raw tool result
        compress: Whether to compress (controlled by toggle)

    Returns:
        Compressed result if compression enabled, otherwise original result
    """
    if not compress:
        return result

    # Compress get_tasks - return summary + top 5 instead of all tasks
    if tool_name == "get_tasks":
        tasks = result.get("tasks", [])
        if len(tasks) > 10:
            # Build compressed task objects with enrichment fields
            top_5_tasks = []
            for t in tasks[:5]:
                task_obj = {
                    "id": str(t.get("_id", "")),
                    "title": t.get("title", ""),
                    "status": t.get("status", ""),
                    "project": t.get("project_name", "-"),
                    "priority": t.get("priority", "-")
                }
                # Include enrichment fields if present
                if t.get("assignee"):
                    task_obj["assignee"] = t.get("assignee")
                if t.get("due_date"):
                    task_obj["due_date"] = str(t.get("due_date"))
                if t.get("blockers"):
                    task_obj["blockers"] = t.get("blockers")
                top_5_tasks.append(task_obj)

            return {
                "total_count": len(tasks),
                "summary": {
                    "todo": len([t for t in tasks if t.get("status") == "todo"]),
                    "in_progress": len([t for t in tasks if t.get("status") == "in_progress"]),
                    "done": len([t for t in tasks if t.get("status") == "done"])
                },
                "top_5": top_5_tasks,
                "note": f"Showing 5 of {len(tasks)}. Use filters to narrow down."
            }
        return result

    # Compress search_tasks - return essential fields only
    if tool_name == "search_tasks":
        tasks = result.get("tasks", result.get("results", []))
        # Build matches with enrichment fields
        matches = []
        for t in tasks[:5]:
            match_obj = {
                "id": str(t.get("_id", "")),
                "title": t.get("title", ""),
                "score": round(t.get("score", 0), 2) if "score" in t else None,
                "project": t.get("project_name", "-"),
                "status": t.get("status", "")
            }
            # Include enrichment fields if present
            if t.get("assignee"):
                match_obj["assignee"] = t.get("assignee")
            if t.get("due_date"):
                match_obj["due_date"] = str(t.get("due_date"))
            if t.get("blockers"):
                match_obj["blockers"] = t.get("blockers")
            matches.append(match_obj)

        return {
            "matches": matches,
            "total_matches": len(tasks)
        }

    # Compress get_projects - return summary if many projects
    if tool_name == "get_projects":
        projects = result.get("projects", [])
        if len(projects) > 5:
            # Build compressed project objects with stakeholders
            compressed_projects = []
            for p in projects[:5]:
                proj_obj = {
                    "id": str(p.get("_id", "")),
                    "name": p.get("name", ""),
                    "task_count": p.get("task_count", 0),
                    "status": p.get("status", "")
                }
                # Include stakeholders if present
                if p.get("stakeholders"):
                    proj_obj["stakeholders"] = p.get("stakeholders")
                compressed_projects.append(proj_obj)

            return {
                "total_count": len(projects),
                "projects": compressed_projects,
                "note": f"Showing 5 of {len(projects)} projects."
            }
        return result

    # No compression for other tools
    return result
