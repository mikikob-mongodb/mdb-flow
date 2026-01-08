#!/usr/bin/env python3
"""
Memory Demo Data Seeder for Flow Companion

Seeds the three memory collections with realistic demo data:
1. Short-term Memory - Session context, agent working memory, disambiguation
2. Long-term Memory - Action history with realistic timeline
3. Shared Memory - Sample handoffs (optional, for future multi-agent)

This makes the UI demo-ready on first load, showcasing all memory features.

Usage:
    # Seed memory only (assumes projects/tasks already loaded)
    python scripts/seed_memory_demo_data.py

    # Load sample data first, then seed memory
    python scripts/seed_memory_demo_data.py --with-sample-data

    # Skip embeddings for faster seeding
    python scripts/seed_memory_demo_data.py --skip-embeddings

    # Seed specific memory types
    python scripts/seed_memory_demo_data.py --short-term-only
    python scripts/seed_memory_demo_data.py --long-term-only

Requires:
    - .env file with MONGODB_URI, MONGODB_DATABASE, VOYAGE_API_KEY
    - Virtual environment activated with dependencies installed
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import MongoDB
from memory import MemoryManager
from shared.embeddings import embed_query
import uuid


# =============================================================================
# CONFIGURATION
# =============================================================================

DEMO_USER_ID = "demo_user"
DEMO_SESSION_ID = "demo-session-001"

# Action type weights (for realistic distribution)
ACTION_WEIGHTS = {
    "complete": 0.25,  # 25% completions
    "start": 0.20,     # 20% starts
    "update": 0.15,    # 15% updates
    "create": 0.10,    # 10% creates
    "search": 0.20,    # 20% searches
    "stop": 0.05,      # 5% stops
    "note": 0.05       # 5% note additions
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def random_past_datetime(days_ago_max: int = 7, days_ago_min: int = 0) -> datetime:
    """Generate a random datetime in the past."""
    days = random.randint(days_ago_min, days_ago_max)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    return datetime.utcnow() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def get_working_hours_datetime(base_date: datetime) -> datetime:
    """Adjust datetime to working hours (9am-6pm weekdays)."""
    # Set to working hours (9am-6pm)
    hour = random.randint(9, 17)
    minute = random.randint(0, 59)

    adjusted = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Skip weekends
    while adjusted.weekday() >= 5:  # 5=Saturday, 6=Sunday
        adjusted += timedelta(days=1)

    return adjusted


# =============================================================================
# LONG-TERM MEMORY SEEDING
# =============================================================================

def seed_action_history(memory: MemoryManager, db, skip_embeddings: bool = False):
    """Seed action history with realistic timeline of user activity."""

    print("\n" + "=" * 60)
    print("SEEDING LONG-TERM MEMORY (Action History)")
    print("=" * 60)

    # Get existing projects and tasks
    projects = list(db.projects.find({"status": {"$in": ["active", "archived"]}}))
    tasks = list(db.tasks.find({}))

    if not projects or not tasks:
        print("\n⚠️  No projects or tasks found in database")
        print("   Run 'python scripts/load_sample_data.py' first")
        return 0

    print(f"\n✓ Found {len(projects)} projects and {len(tasks)} tasks")

    # Generate actions over past 7 days
    actions_to_create = []

    # 1. Create actions for completed tasks
    completed_tasks = [t for t in tasks if t.get("status") == "done"]
    print(f"\n1. Creating completion actions for {len(completed_tasks)} completed tasks...")

    for task in completed_tasks:
        project = next((p for p in projects if p["_id"] == task.get("project_id")), None)

        # Use completed_at if available, otherwise random past date
        timestamp = task.get("completed_at") or random_past_datetime(7, 1)
        timestamp = get_working_hours_datetime(timestamp)

        actions_to_create.append({
            "action_type": "complete",
            "entity_type": "task",
            "entity": {
                "task_id": str(task["_id"]),
                "task_title": task["title"],
                "project_id": str(project["_id"]) if project else None,
                "project_name": project["name"] if project else None
            },
            "metadata": {
                "previous_status": "in_progress",
                "new_status": "done",
                "completion_note": "Task completed successfully"
            },
            "timestamp": timestamp
        })

    # 2. Create actions for in-progress tasks (started)
    in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
    print(f"2. Creating start actions for {len(in_progress_tasks)} in-progress tasks...")

    for task in in_progress_tasks:
        project = next((p for p in projects if p["_id"] == task.get("project_id")), None)

        # Use started_at if available
        timestamp = task.get("started_at") or random_past_datetime(5, 1)
        timestamp = get_working_hours_datetime(timestamp)

        actions_to_create.append({
            "action_type": "start",
            "entity_type": "task",
            "entity": {
                "task_id": str(task["_id"]),
                "task_title": task["title"],
                "project_id": str(project["_id"]) if project else None,
                "project_name": project["name"] if project else None
            },
            "metadata": {
                "previous_status": "todo",
                "new_status": "in_progress"
            },
            "timestamp": timestamp
        })

    # 3. Create task creation actions (sample of tasks created recently)
    recent_tasks = sorted(tasks, key=lambda t: t.get("created_at", datetime.min), reverse=True)[:10]
    print(f"3. Creating create actions for {len(recent_tasks)} recent tasks...")

    for task in recent_tasks:
        project = next((p for p in projects if p["_id"] == task.get("project_id")), None)

        timestamp = task.get("created_at") or random_past_datetime(7, 0)
        timestamp = get_working_hours_datetime(timestamp)

        actions_to_create.append({
            "action_type": "create",
            "entity_type": "task",
            "entity": {
                "task_id": str(task["_id"]),
                "task_title": task["title"],
                "project_id": str(project["_id"]) if project else None,
                "project_name": project["name"] if project else None
            },
            "metadata": {
                "initial_status": task.get("status", "todo"),
                "priority": task.get("priority")
            },
            "timestamp": timestamp
        })

    # 4. Create update actions for tasks with activity
    tasks_with_notes = [t for t in in_progress_tasks + completed_tasks if t.get("notes")]
    sample_update_tasks = random.sample(tasks_with_notes, min(8, len(tasks_with_notes)))
    print(f"4. Creating update actions for {len(sample_update_tasks)} tasks with activity...")

    for task in sample_update_tasks:
        project = next((p for p in projects if p["_id"] == task.get("project_id")), None)

        timestamp = random_past_datetime(4, 1)
        timestamp = get_working_hours_datetime(timestamp)

        actions_to_create.append({
            "action_type": "update",
            "entity_type": "task",
            "entity": {
                "task_id": str(task["_id"]),
                "task_title": task["title"],
                "project_id": str(project["_id"]) if project else None,
                "project_name": project["name"] if project else None
            },
            "metadata": {
                "fields_updated": ["notes", "context"],
                "note_added": True
            },
            "timestamp": timestamp
        })

    # 5. Create search actions (realistic queries)
    search_queries = [
        ("debugging documentation", "AgentOps Framework"),
        ("voice agent architecture", "Voice Agent Architecture"),
        ("memory patterns", "Memory Engineering Content"),
        ("webinar prep", "Developer Webinar Series"),
        ("LangGraph integration", "LangGraph Integration"),
        ("demo video", None),
        ("high priority tasks", None),
        ("in progress work", None)
    ]

    print(f"5. Creating {len(search_queries)} search actions...")

    for query, project_name in search_queries:
        timestamp = random_past_datetime(6, 0)
        timestamp = get_working_hours_datetime(timestamp)

        # Find matching tasks for results_count
        if project_name:
            project = next((p for p in projects if p["name"] == project_name), None)
            project_id = project["_id"] if project else None
            matching_tasks = [t for t in tasks if t.get("project_id") == project_id]
        else:
            matching_tasks = tasks

        results_count = min(len(matching_tasks), random.randint(3, 8))

        actions_to_create.append({
            "action_type": "search",
            "entity_type": "search",
            "entity": {
                "query": query
            },
            "metadata": {
                "query": query,
                "results_count": results_count,
                "search_mode": random.choice(["hybrid", "vector", "text"])
            },
            "timestamp": timestamp
        })

    # Sort actions by timestamp
    actions_to_create.sort(key=lambda a: a["timestamp"])

    print(f"\n✓ Generated {len(actions_to_create)} actions")
    print(f"  Recording to long-term memory...")

    # Record all actions
    recorded_count = 0
    for action in actions_to_create:
        try:
            memory.record_action(
                user_id=DEMO_USER_ID,
                session_id=DEMO_SESSION_ID,
                action_type=action["action_type"],
                entity_type=action["entity_type"],
                entity=action["entity"],
                metadata=action["metadata"],
                source_agent="coordinator",
                triggered_by="user",
                generate_embedding=not skip_embeddings
            )
            recorded_count += 1

            if recorded_count % 10 == 0:
                print(f"  Progress: {recorded_count}/{len(actions_to_create)} actions recorded...")
        except Exception as e:
            print(f"  ✗ Failed to record action: {e}")

    print(f"\n✓ Recorded {recorded_count} actions to long-term memory")

    # Show summary by type
    action_counts = {}
    for action in actions_to_create:
        action_type = action["action_type"]
        action_counts[action_type] = action_counts.get(action_type, 0) + 1

    print("\n📊 Action Summary:")
    for action_type, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action_type}: {count}")

    return recorded_count


# =============================================================================
# SHORT-TERM MEMORY SEEDING
# =============================================================================

def seed_session_context(memory: MemoryManager, db):
    """Seed session context with demo user preferences and current state."""

    print("\n" + "=" * 60)
    print("SEEDING SHORT-TERM MEMORY (Session Context)")
    print("=" * 60)

    # Get a realistic current project (one with in-progress tasks)
    in_progress_tasks = list(db.tasks.find({"status": "in_progress"}).limit(1))

    if in_progress_tasks:
        current_task = in_progress_tasks[0]
        project = db.projects.find_one({"_id": current_task.get("project_id")})

        current_project = project["name"] if project else None
        current_task_title = current_task["title"]
        current_task_id = str(current_task["_id"])
    else:
        # Fallback to first active project
        project = db.projects.find_one({"status": "active"})
        current_project = project["name"] if project else "AgentOps Framework"
        current_task_title = None
        current_task_id = None

    print(f"\n1. Setting session context for demo user...")
    print(f"   Current project: {current_project}")
    print(f"   Current task: {current_task_title}")

    # Build context
    context_updates = {
        "current_project": current_project,
        "last_action": "completed",
    }

    if current_task_title:
        context_updates["current_task"] = current_task_title
        context_updates["current_task_id"] = current_task_id

    # Add preferences
    context_updates["preferences"] = {
        "focus_project": current_project,
        "default_priority": "medium",
        "auto_timestamp": True
    }

    # Add rules
    context_updates["rules"] = [
        "Always add notes when completing tasks",
        "Update task context with key decisions",
        "Tag tasks with relevant project milestones"
    ]

    # Write session context
    memory.update_session_context(DEMO_SESSION_ID, context_updates, DEMO_USER_ID)

    print(f"   ✓ Session context written")

    # Verify
    saved_context = memory.read_session_context(DEMO_SESSION_ID)
    if saved_context:
        print(f"   ✓ Verified: {len(saved_context.keys())} context keys")

    return True


def seed_disambiguation(memory: MemoryManager, db):
    """Seed disambiguation with sample search results."""

    print("\n2. Adding sample disambiguation...")

    # Find tasks with "debug" in title
    debug_tasks = list(db.tasks.find(
        {"title": {"$regex": "debug", "$options": "i"}},
        {"title": 1, "_id": 1}
    ).limit(3))

    if len(debug_tasks) >= 2:
        results = []
        for idx, task in enumerate(debug_tasks):
            results.append({
                "index": idx,
                "task_id": str(task["_id"]),
                "title": task["title"]
            })

        memory.store_disambiguation(
            DEMO_SESSION_ID,
            "debugging task",
            results,
            "coordinator"
        )

        print(f"   ✓ Stored disambiguation with {len(results)} results")
        print(f"     Query: 'debugging task'")
        for r in results:
            print(f"       {r['index'] + 1}. {r['title']}")
    else:
        print("   ⚠️  Not enough tasks for disambiguation example")

    return len(debug_tasks) >= 2


def seed_agent_working_memory(memory: MemoryManager):
    """Seed agent working memory (future multi-agent support)."""

    print("\n3. Adding agent working memory...")

    # Retrieval agent working memory
    memory.update_agent_working(
        DEMO_SESSION_ID,
        "retrieval",
        {
            "search_iteration": 1,
            "last_query": "debugging documentation",
            "results_returned": 5
        }
    )
    print("   ✓ Retrieval agent working memory set")

    # Worklog agent working memory
    memory.update_agent_working(
        DEMO_SESSION_ID,
        "worklog",
        {
            "pending_task_id": None,
            "last_operation": "complete_task",
            "tasks_modified_today": 3
        }
    )
    print("   ✓ Worklog agent working memory set")

    return True


# =============================================================================
# SHARED MEMORY SEEDING (OPTIONAL)
# =============================================================================

def seed_handoffs(memory: MemoryManager):
    """Seed sample handoffs for multi-agent workflow demonstration."""

    print("\n" + "=" * 60)
    print("SEEDING SHARED MEMORY (Handoffs)")
    print("=" * 60)

    print("\n1. Creating sample handoff chain...")

    # Create a handoff chain: coordinator → retrieval → worklog
    chain_id = str(uuid.uuid4())

    # First handoff: coordinator to retrieval
    handoff1_id = memory.write_handoff(
        session_id=DEMO_SESSION_ID,
        user_id=DEMO_USER_ID,
        source_agent="coordinator",
        target_agent="retrieval",
        handoff_type="search_request",
        payload={
            "query": "debugging documentation tasks",
            "limit": 5,
            "search_mode": "hybrid"
        },
        chain_id=chain_id,
        priority="normal"
    )

    print(f"   ✓ Created handoff: coordinator → retrieval")

    # Second handoff: retrieval to worklog (as part of chain)
    handoff2_id = memory.write_handoff(
        session_id=DEMO_SESSION_ID,
        user_id=DEMO_USER_ID,
        source_agent="retrieval",
        target_agent="worklog",
        handoff_type="create_task_from_search",
        payload={
            "search_results": [
                {"task_id": "abc123", "title": "Debug memory issue", "relevance": 0.95}
            ],
            "create_followup": True
        },
        chain_id=chain_id,
        parent_handoff_id=handoff1_id,
        priority="normal"
    )

    print(f"   ✓ Created handoff: retrieval → worklog")
    print(f"   ✓ Chain ID: {chain_id}")

    # Get chain status
    chain_status = memory.get_chain_status(chain_id)
    print(f"\n📊 Chain Status:")
    print(f"   Total handoffs: {chain_status['total']}")
    print(f"   Pending: {chain_status['pending']}")
    print(f"   Agents: {', '.join(chain_status['agents_involved'])}")

    return True


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def seed_memory_data(
    with_sample_data: bool = False,
    skip_embeddings: bool = False,
    short_term_only: bool = False,
    long_term_only: bool = False,
    include_handoffs: bool = False
):
    """Main function to seed all memory collections."""

    print("\n" + "=" * 60)
    print("Flow Companion - Memory Demo Data Seeder")
    print("=" * 60)

    # Load sample data first if requested
    if with_sample_data:
        print("\n📥 Loading sample projects and tasks first...")
        script_path = Path(__file__).parent / "load_sample_data.py"
        cmd = ["python", str(script_path)]
        if skip_embeddings:
            cmd.append("--skip-embeddings")

        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("\n❌ Failed to load sample data")
            return False
        print("\n✓ Sample data loaded")

    # Initialize MongoDB and Memory Manager
    print("\n🔧 Initializing Memory Manager...")
    mongodb = MongoDB()
    db = mongodb.get_database()

    memory = MemoryManager(db, embedding_fn=embed_query if not skip_embeddings else None)
    print("✓ Memory Manager initialized")

    # Clear existing memory data
    print("\n🗑️  Clearing existing memory data...")
    db.memory_short_term.delete_many({"user_id": DEMO_USER_ID})
    db.long_term_memory.delete_many({"user_id": DEMO_USER_ID})
    db.shared_memory.delete_many({"user_id": DEMO_USER_ID})
    print("✓ Existing demo user memory cleared")

    results = {}

    # Seed short-term memory
    if not long_term_only:
        seed_session_context(memory, db)
        seed_disambiguation(memory, db)
        seed_agent_working_memory(memory)
        results["short_term"] = True

    # Seed long-term memory
    if not short_term_only:
        action_count = seed_action_history(memory, db, skip_embeddings)
        results["long_term"] = action_count

    # Seed shared memory (optional)
    if include_handoffs and not short_term_only and not long_term_only:
        seed_handoffs(memory)
        results["shared"] = True

    # Final stats
    print("\n" + "=" * 60)
    print("✅ MEMORY SEEDING COMPLETE")
    print("=" * 60)

    stats = memory.get_memory_stats(DEMO_SESSION_ID, DEMO_USER_ID)

    print(f"\n📊 Final Memory Stats:")
    print(f"   User ID: {DEMO_USER_ID}")
    print(f"   Session ID: {DEMO_SESSION_ID}")
    print(f"   Short-term entries: {stats['short_term_count']}")
    print(f"   Long-term actions: {stats['long_term_count']}")
    print(f"   Shared pending: {stats['shared_pending']}")

    if stats.get('action_counts'):
        print(f"\n   Action breakdown:")
        for action_type, count in stats['action_counts'].items():
            print(f"     {action_type}: {count}")

    print("\n✅ Demo data ready! Launch the UI:")
    print("   streamlit run ui/streamlit_app.py\n")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed memory collections with demo data for Flow Companion"
    )
    parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Load sample projects/tasks first (runs load_sample_data.py)"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip generating embeddings (faster, but semantic search won't work)"
    )
    parser.add_argument(
        "--short-term-only",
        action="store_true",
        help="Only seed short-term memory (session context)"
    )
    parser.add_argument(
        "--long-term-only",
        action="store_true",
        help="Only seed long-term memory (action history)"
    )
    parser.add_argument(
        "--include-handoffs",
        action="store_true",
        help="Include handoff examples in shared memory"
    )

    args = parser.parse_args()

    if args.skip_embeddings:
        print("\n⚠️  Skipping embeddings (semantic search will not work)")

    try:
        success = seed_memory_data(
            with_sample_data=args.with_sample_data,
            skip_embeddings=args.skip_embeddings,
            short_term_only=args.short_term_only,
            long_term_only=args.long_term_only,
            include_handoffs=args.include_handoffs
        )

        if not success:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error seeding memory data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
