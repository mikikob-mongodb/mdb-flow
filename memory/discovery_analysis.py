"""
Tool Discovery Analysis

Analyzes patterns in MCP tool discoveries to generate actionable suggestions
for new features, Atlas optimizations, and template candidates.

This showcases the "agents teaching developers what to build" narrative.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict


def analyze_discoveries(
    db,
    user_id: str = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    Analyze tool discovery patterns and generate suggestions.

    Args:
        db: MongoDB database instance
        user_id: Optional user ID to filter by
        days: Number of days to analyze (default 7)

    Returns:
        {
            "summary": {...},
            "suggested_tools": [...],
            "atlas_optimizations": [...],
            "template_candidates": [...],
            "feature_gaps": [...]
        }
    """
    # Calculate time range
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Build query filter
    query_filter = {"first_used": {"$gte": cutoff_date}}
    if user_id:
        query_filter["user_id"] = user_id

    # Get all discoveries in range
    discoveries = list(db.tool_discoveries.find(query_filter))

    if not discoveries:
        return {
            "summary": {
                "total_discoveries": 0,
                "period_days": days,
                "message": f"No tool discoveries found in the last {days} days"
            },
            "suggested_tools": [],
            "atlas_optimizations": [],
            "template_candidates": [],
            "feature_gaps": []
        }

    # Analyze patterns
    summary = _analyze_summary(discoveries, days)
    suggested_tools = _suggest_new_tools(discoveries)
    atlas_optimizations = _suggest_atlas_optimizations(discoveries)
    template_candidates = _suggest_templates(db, user_id, days)
    feature_gaps = _identify_feature_gaps(discoveries)

    return {
        "summary": summary,
        "suggested_tools": suggested_tools,
        "atlas_optimizations": atlas_optimizations,
        "template_candidates": template_candidates,
        "feature_gaps": feature_gaps
    }


def _analyze_summary(discoveries: List[Dict], days: int) -> Dict[str, Any]:
    """Generate summary statistics."""
    total = len(discoveries)
    successful = sum(1 for d in discoveries if d.get("success", False))
    failed = total - successful

    # Group by intent
    by_intent = defaultdict(int)
    for d in discoveries:
        intent = d.get("intent", "unknown")
        by_intent[intent] += 1

    # Group by MCP server
    by_server = defaultdict(int)
    for d in discoveries:
        server = d.get("solution", {}).get("mcp_server", "unknown")
        by_server[server] += 1

    # Find most reused
    most_reused = sorted(
        discoveries,
        key=lambda d: d.get("times_used", 0),
        reverse=True
    )[:3]

    # Calculate total reuse count
    total_reuses = sum(d.get("times_used", 0) for d in discoveries)

    return {
        "total_discoveries": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
        "period_days": days,
        "by_intent": dict(by_intent),
        "by_server": dict(by_server),
        "total_reuses": total_reuses,
        "most_reused": [
            {
                "request": d.get("user_request", "")[:60] + "...",
                "times_used": d.get("times_used", 0),
                "intent": d.get("intent", "unknown")
            }
            for d in most_reused if d.get("times_used", 0) > 1
        ]
    }


def _suggest_new_tools(discoveries: List[Dict]) -> List[Dict[str, Any]]:
    """
    Suggest new built-in tools based on repeated successful patterns.

    Logic: If a discovery has been reused 3+ times, it's a candidate for
    becoming a built-in tool.
    """
    suggestions = []

    # Find high-reuse discoveries
    candidates = [
        d for d in discoveries
        if d.get("times_used", 0) >= 3 and d.get("success", False)
    ]

    # Sort by reuse count
    candidates.sort(key=lambda d: d.get("times_used", 0), reverse=True)

    for disc in candidates[:5]:  # Top 5 candidates
        solution = disc.get("solution", {})
        suggestions.append({
            "request_pattern": disc.get("user_request", "")[:80],
            "intent": disc.get("intent", "unknown"),
            "times_used": disc.get("times_used", 0),
            "current_solution": {
                "mcp_server": solution.get("mcp_server", ""),
                "tool": solution.get("tool_used", "")
            },
            "suggestion": f"Consider adding a built-in tool for '{disc.get('intent', 'this pattern')}' "
                         f"to avoid repeated MCP calls",
            "avg_latency_ms": disc.get("execution_time_ms", 0)
        })

    return suggestions


def _suggest_atlas_optimizations(discoveries: List[Dict]) -> List[Dict[str, Any]]:
    """
    Suggest Atlas optimizations based on query patterns.

    Logic: Look for patterns in tool arguments that suggest missing indexes
    or collection structures.
    """
    suggestions = []

    # Analyze tool arguments for patterns
    search_patterns = defaultdict(int)

    for disc in discoveries:
        if not disc.get("success", False):
            continue

        solution = disc.get("solution", {})
        args = solution.get("arguments", {})

        # Look for search/query patterns
        if "query" in args or "search" in args:
            search_patterns["text_search"] += 1

        # Look for filter patterns
        for key in ["assignee", "status", "priority", "tags"]:
            if key in str(args).lower():
                search_patterns[f"filter_{key}"] += 1

    # Generate suggestions based on patterns
    if search_patterns.get("text_search", 0) >= 3:
        suggestions.append({
            "type": "index",
            "collection": "inferred from discoveries",
            "field": "text fields",
            "reason": f"Detected {search_patterns['text_search']} text search operations",
            "suggestion": "Consider adding a text index for full-text search capabilities"
        })

    for pattern, count in search_patterns.items():
        if pattern.startswith("filter_") and count >= 3:
            field = pattern.replace("filter_", "")
            suggestions.append({
                "type": "index",
                "collection": "tasks or projects",
                "field": field,
                "reason": f"Detected {count} filter operations on '{field}'",
                "suggestion": f"Consider adding an index on '{field}' to improve query performance"
            })

    return suggestions


def _suggest_templates(db, user_id: Optional[str], days: int) -> List[Dict[str, Any]]:
    """
    Suggest workflow templates based on repeated action patterns.

    Logic: Look for multi-step workflows in episodic memory that repeat.
    """
    suggestions = []

    # Get recent episodic actions
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    query_filter = {
        "memory_type": "episodic",
        "timestamp": {"$gte": cutoff_date}
    }
    if user_id:
        query_filter["user_id"] = user_id

    actions = list(db.memory_episodic.find(query_filter).limit(100))

    # Look for repeated sequences
    # Group by session and find common patterns
    by_session = defaultdict(list)
    for action in actions:
        session_id = action.get("session_id", "unknown")
        by_session[session_id].append(action.get("action_type", ""))

    # Find sequences that appear multiple times
    sequences = defaultdict(int)
    for session_actions in by_session.values():
        if len(session_actions) >= 3:
            # Create sequence key (first 3 actions)
            seq_key = " → ".join(session_actions[:3])
            sequences[seq_key] += 1

    # Suggest templates for repeated sequences
    for seq, count in sequences.items():
        if count >= 2:  # Sequence repeated at least twice
            suggestions.append({
                "workflow_pattern": seq,
                "times_observed": count,
                "suggestion": f"This workflow pattern has been repeated {count} times. "
                             "Consider creating a template to streamline it.",
                "template_name": f"{seq.split(' → ')[0].title()} Workflow"
            })

    return suggestions[:3]  # Top 3 candidates


def _identify_feature_gaps(discoveries: List[Dict]) -> List[Dict[str, Any]]:
    """
    Identify feature gaps based on failed discoveries or missing functionality.

    Logic: Failed discoveries indicate features that don't exist or don't work well.
    """
    gaps = []

    # Group failed discoveries by intent
    failed_by_intent = defaultdict(list)
    for disc in discoveries:
        if not disc.get("success", False):
            intent = disc.get("intent", "unknown")
            failed_by_intent[intent].append(disc)

    # Create gap suggestions
    for intent, failed_discs in failed_by_intent.items():
        if len(failed_discs) >= 2:  # Multiple failures for same intent
            gaps.append({
                "intent": intent,
                "failure_count": len(failed_discs),
                "example_requests": [
                    d.get("user_request", "")[:60] + "..."
                    for d in failed_discs[:2]
                ],
                "suggestion": f"Multiple failures for '{intent}' intent. "
                             "This functionality may be missing or unreliable.",
                "severity": "high" if len(failed_discs) >= 3 else "medium"
            })

    # Also look for single high-impact failures
    for disc in discoveries:
        if not disc.get("success", False) and disc.get("times_used", 0) >= 3:
            # User tried this multiple times but it kept failing
            gaps.append({
                "intent": disc.get("intent", "unknown"),
                "failure_count": disc.get("times_used", 0),
                "example_requests": [disc.get("user_request", "")[:60] + "..."],
                "suggestion": f"User attempted this {disc.get('times_used', 0)} times without success. "
                             "High-priority feature gap.",
                "severity": "critical"
            })

    return gaps
