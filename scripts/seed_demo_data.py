#!/usr/bin/env python3
"""
Demo Data Seeder for Flow Companion Presentation

Seeds a complete demo dataset including:
- Projects (2-3 realistic projects)
- Tasks (5-8 tasks across projects)
- Procedural Memory (GTM Template + Due Diligence Questions)
- Semantic Memory (User Preferences)
- Episodic Memory (Past Actions)

This script is designed specifically for presentation demos with realistic,
interconnected data that showcases the 5-tier memory system.

CLI Usage:
    # Add demo data (idempotent)
    python scripts/seed_demo_data.py

    # Clear and re-add
    python scripts/seed_demo_data.py --clean

    # Verify data exists
    python scripts/seed_demo_data.py --verify

    # Skip embeddings for faster seeding
    python scripts/seed_demo_data.py --skip-embeddings

Programmatic Usage (from other scripts):
    from seed_demo_data import seed_all, clear_collections, verify_seed

    # Seed all data
    results = seed_all(db, clean=True, skip_embeddings=False)

    # Clear collections
    counts = clear_collections(db)

    # Verify seed data
    verification = verify_seed(db)
    if verification["success"]:
        print("All critical data exists")

Importable Functions:
    - seed_all(db, clean, skip_embeddings) -> Dict[str, int]
        Main orchestrator - seeds all demo data

    - clear_collections(db, collections) -> Dict[str, int]
        Clear specified collections, returns counts deleted

    - verify_seed(db) -> Dict[str, Any]
        Verify critical data exists, returns structured results

    - seed_projects(db, clean) -> int
    - seed_tasks(db, clean) -> int
    - seed_procedural_memory(db, skip_embeddings, clean) -> int
    - seed_semantic_memory(db, clean) -> int
    - seed_episodic_memory(db, skip_embeddings, clean) -> int

Requires:
    - .env file with MONGODB_URI, MONGODB_DATABASE, VOYAGE_API_KEY
    - Virtual environment activated with dependencies installed
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import MongoDB
from memory.manager import MemoryManager
from shared.embeddings import embed_document
from bson import ObjectId

# =============================================================================
# CONFIGURATION
# =============================================================================

DEMO_USER_ID = "demo-user"
DEMO_SESSION_PREFIX = "past-session"

# =============================================================================
# DATA DEFINITIONS
# =============================================================================

def get_projects_data() -> List[Dict[str, Any]]:
    """Get project data for seeding."""
    now = datetime.utcnow()

    return [
        {
            "_id": ObjectId(),
            "name": "Project Alpha",
            "description": "Q4 infrastructure modernization initiative",
            "status": "active",
            "created_at": now - timedelta(days=30),
            "user_id": DEMO_USER_ID,
            "tags": ["infrastructure", "modernization"],
            "priority": "high"
        },
        {
            "_id": ObjectId(),
            "name": "Q3 Fintech GTM",
            "description": "Go-to-market strategy for fintech vertical",
            "status": "completed",
            "created_at": now - timedelta(days=90),
            "completed_at": now - timedelta(days=45),
            "user_id": DEMO_USER_ID,
            "tags": ["gtm", "fintech", "strategy"],
            "priority": "high"
        },
        {
            "_id": ObjectId(),
            "name": "AI Developer Outreach",
            "description": "Developer engagement campaign for AI tools",
            "status": "completed",
            "created_at": now - timedelta(days=120),
            "completed_at": now - timedelta(days=60),
            "user_id": DEMO_USER_ID,
            "tags": ["ai", "developer-relations", "outreach"],
            "priority": "medium"
        }
    ]


def get_tasks_data(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get task data for seeding."""
    now = datetime.utcnow()

    # Find Project Alpha
    project_alpha = next((p for p in projects if p["name"] == "Project Alpha"), None)

    if not project_alpha:
        return []

    return [
        # Project Alpha tasks
        {
            "_id": ObjectId(),
            "title": "Review infrastructure audit report",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "done",
            "priority": "high",
            "created_at": now - timedelta(days=25),
            "completed_at": now - timedelta(days=20),
            "user_id": DEMO_USER_ID,
            "description": "Analyze findings from Q3 infrastructure audit",
            "tags": ["audit", "review"]
        },
        {
            "_id": ObjectId(),
            "title": "Schedule stakeholder alignment meeting",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "done",
            "priority": "medium",
            "created_at": now - timedelta(days=20),
            "completed_at": now - timedelta(days=15),
            "user_id": DEMO_USER_ID,
            "description": "Align key stakeholders on modernization approach",
            "tags": ["meeting", "stakeholders"]
        },
        {
            "_id": ObjectId(),
            "title": "Draft migration timeline",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "in_progress",
            "priority": "high",
            "created_at": now - timedelta(days=10),
            "started_at": now - timedelta(days=8),
            "user_id": DEMO_USER_ID,
            "description": "Create phased migration timeline with dependencies",
            "tags": ["planning", "timeline"]
        },
        {
            "_id": ObjectId(),
            "title": "Identify vendor dependencies",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "todo",
            "priority": "medium",
            "created_at": now - timedelta(days=5),
            "user_id": DEMO_USER_ID,
            "description": "Map all third-party vendor dependencies",
            "tags": ["vendors", "dependencies"]
        },
        {
            "_id": ObjectId(),
            "title": "Cost-benefit analysis",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "todo",
            "priority": "high",
            "created_at": now - timedelta(days=3),
            "user_id": DEMO_USER_ID,
            "description": "Quantify expected ROI and TCO reduction",
            "tags": ["analysis", "roi"]
        },
        {
            "_id": ObjectId(),
            "title": "Security compliance review",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "todo",
            "priority": "high",
            "created_at": now - timedelta(days=2),
            "user_id": DEMO_USER_ID,
            "description": "Ensure modernization meets SOC2 requirements",
            "tags": ["security", "compliance"]
        },
        {
            "_id": ObjectId(),
            "title": "Draft communication plan",
            "project": "Project Alpha",
            "project_id": project_alpha["_id"],
            "status": "todo",
            "priority": "low",
            "created_at": now - timedelta(days=1),
            "user_id": DEMO_USER_ID,
            "description": "Create internal communication strategy for rollout",
            "tags": ["communication", "planning"]
        }
    ]


def get_procedural_memory_data() -> List[Dict[str, Any]]:
    """Get procedural memory (templates and checklists) for seeding."""
    now = datetime.utcnow()

    return [
        # GTM Roadmap Template (critical for presentation finale)
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "template",
            "name": "GTM Roadmap Template",
            "description": "Standard go-to-market project template with research-backed task generation",
            "trigger": "create_gtm_project",
            "template": {
                "phases": [
                    {
                        "name": "Research",
                        "tasks": [
                            "Market size and growth analysis",
                            "Competitor landscape mapping",
                            "Target customer persona development",
                            "Pricing strategy research"
                        ]
                    },
                    {
                        "name": "Strategy",
                        "tasks": [
                            "Value proposition refinement",
                            "Channel strategy definition",
                            "Partnership opportunity identification",
                            "Go-to-market timeline creation"
                        ]
                    },
                    {
                        "name": "Execution",
                        "tasks": [
                            "Marketing collateral development",
                            "Sales enablement materials",
                            "Launch event planning",
                            "Success metrics definition"
                        ]
                    }
                ]
            },
            "times_used": 3,
            "success_rate": 1.0,
            "created_at": now - timedelta(days=180),
            "last_used": now - timedelta(days=45),
            "updated_at": now - timedelta(days=45)
        },

        # Market Research Questions Checklist
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "checklist",
            "name": "Market Research Questions",
            "description": "Standard questions to answer when researching a new market",
            "trigger": "market_research",
            "questions": [
                "What is the total addressable market (TAM)?",
                "Who are the top 3-5 competitors?",
                "What are the main customer pain points?",
                "What pricing models exist in this space?",
                "What are the key trends shaping this market?",
                "What regulatory considerations exist?"
            ],
            "times_used": 2,
            "created_at": now - timedelta(days=180),
            "last_used": now - timedelta(days=90),
            "updated_at": now - timedelta(days=90)
        }
    ]


def get_semantic_memory_data() -> List[Dict[str, Any]]:
    """Get semantic memory (user preferences) for seeding."""
    now = datetime.utcnow()

    return [
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": "default_priority",
            "value": "high",
            "source": "inferred",
            "confidence": 0.8,
            "times_used": 15,
            "created_at": now - timedelta(days=60),
            "updated_at": now - timedelta(days=5)
        },
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": "communication_style",
            "value": "concise",
            "source": "explicit",
            "confidence": 0.9,
            "times_used": 25,
            "created_at": now - timedelta(days=90),
            "updated_at": now - timedelta(days=2)
        },
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": "focus_area",
            "value": "AI and developer tools",
            "source": "inferred",
            "confidence": 0.85,
            "times_used": 12,
            "created_at": now - timedelta(days=100),
            "updated_at": now - timedelta(days=10)
        },
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": "work_style",
            "value": "strategic planning",
            "source": "inferred",
            "confidence": 0.75,
            "times_used": 8,
            "created_at": now - timedelta(days=80),
            "updated_at": now - timedelta(days=15)
        }
    ]


def get_episodic_memory_data(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get episodic memory (past actions) for seeding."""
    now = datetime.utcnow()

    # Find Q3 Fintech GTM project
    fintech_project = next((p for p in projects if p["name"] == "Q3 Fintech GTM"), None)

    actions = [
        {
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-1",
            "memory_type": "episodic",
            "action_type": "created_project",
            "entity_type": "project",
            "entity": {
                "project_name": "Q3 Fintech GTM",
                "project_id": str(fintech_project["_id"]) if fintech_project else None,
                "used_template": "GTM Roadmap Template",
                "tasks_generated": 12
            },
            "metadata": {
                "template_used": True,
                "phases_created": ["Research", "Strategy", "Execution"],
                "duration_ms": 1200
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=90),
            "created_at": now - timedelta(days=90)
        },
        {
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-2",
            "memory_type": "episodic",
            "action_type": "completed_project",
            "entity_type": "project",
            "entity": {
                "project_name": "Q3 Fintech GTM",
                "project_id": str(fintech_project["_id"]) if fintech_project else None,
                "duration_days": 45,
                "tasks_completed": 12
            },
            "metadata": {
                "completion_rate": 1.0,
                "on_schedule": True,
                "key_outcomes": [
                    "Identified $50M TAM",
                    "Secured 3 launch partners",
                    "Published 5 case studies"
                ]
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=45),
            "created_at": now - timedelta(days=45)
        },
        {
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-3",
            "memory_type": "episodic",
            "action_type": "template_applied",
            "entity_type": "template",
            "entity": {
                "template_name": "GTM Roadmap Template",
                "applied_to_project": "AI Developer Outreach"
            },
            "metadata": {
                "tasks_generated": 11,
                "customizations": ["Added developer-specific channels", "Included technical content phase"]
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=120),
            "created_at": now - timedelta(days=120)
        }
    ]

    return actions


# =============================================================================
# SEEDING FUNCTIONS
# =============================================================================

def seed_projects(db, clean: bool = False) -> int:
    """Seed project data."""
    print("\n" + "=" * 60)
    print("SEEDING PROJECTS")
    print("=" * 60)

    if clean:
        deleted = db.projects.delete_many({"user_id": DEMO_USER_ID})
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing projects")

    projects = get_projects_data()

    # Check for existing projects to maintain idempotency
    existing_names = set()
    for project in db.projects.find({"user_id": DEMO_USER_ID}, {"name": 1}):
        existing_names.add(project["name"])

    inserted_count = 0
    for project in projects:
        if project["name"] in existing_names:
            print(f"  ⏭️  Skipping existing: {project['name']}")
            continue

        db.projects.insert_one(project)
        print(f"  ✓ Inserted: {project['name']} ({project['status']})")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new projects, {len(existing_names)} existing")

    return inserted_count


def seed_tasks(db, clean: bool = False) -> int:
    """Seed task data."""
    print("\n" + "=" * 60)
    print("SEEDING TASKS")
    print("=" * 60)

    if clean:
        deleted = db.tasks.delete_many({"user_id": DEMO_USER_ID})
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing tasks")

    # Get current projects
    projects = list(db.projects.find({"user_id": DEMO_USER_ID}))

    if not projects:
        print("  ⚠️  No projects found. Run with projects first.")
        return 0

    tasks = get_tasks_data(projects)

    # Check for existing tasks
    existing_titles = set()
    for task in db.tasks.find({"user_id": DEMO_USER_ID}, {"title": 1}):
        existing_titles.add(task["title"])

    inserted_count = 0
    for task in tasks:
        if task["title"] in existing_titles:
            print(f"  ⏭️  Skipping existing: {task['title']}")
            continue

        db.tasks.insert_one(task)
        print(f"  ✓ Inserted: {task['title']} ({task['status']}, {task['priority']})")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new tasks, {len(existing_titles)} existing")

    return inserted_count


def seed_procedural_memory(db, skip_embeddings: bool = False, clean: bool = False) -> int:
    """Seed procedural memory (templates and checklists)."""
    print("\n" + "=" * 60)
    print("SEEDING PROCEDURAL MEMORY")
    print("=" * 60)

    if clean:
        deleted = db.long_term_memory.delete_many({
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural"
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing procedural memories")

    procedures = get_procedural_memory_data()

    # Check for existing procedures
    existing_names = set()
    for proc in db.long_term_memory.find({
        "user_id": DEMO_USER_ID,
        "memory_type": "procedural"
    }, {"name": 1}):
        if "name" in proc:
            existing_names.add(proc["name"])

    inserted_count = 0
    for proc in procedures:
        if proc["name"] in existing_names:
            print(f"  ⏭️  Skipping existing: {proc['name']}")
            continue

        # Generate embedding for template/checklist content if needed
        if not skip_embeddings:
            # Create searchable text: name + description (focused for better semantic matching)
            # Enables queries like: "find template for go-to-market" → matches GTM template
            searchable_text = f"{proc['name']} {proc['description']}"

            # Add rule type and trigger for additional context
            if "trigger" in proc:
                searchable_text += f" {proc['trigger']}"

            try:
                proc["embedding"] = embed_document(searchable_text)

                # Verify embedding dimension (should be 1024 for Voyage AI)
                if len(proc["embedding"]) != 1024:
                    print(f"  ⚠️  Warning: Expected 1024 dims, got {len(proc['embedding'])}")

                print(f"  📊 Generated embedding for: {proc['name']} (1024-dim)")
            except Exception as e:
                print(f"  ⚠️  Failed to generate embedding: {e}")
                print(f"      Continuing without embedding for: {proc['name']}")

        db.long_term_memory.insert_one(proc)
        print(f"  ✓ Inserted: {proc['name']} ({proc['rule_type']}, used {proc['times_used']}x)")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new procedures, {len(existing_names)} existing")

    return inserted_count


def seed_semantic_memory(db, clean: bool = False) -> int:
    """Seed semantic memory (user preferences)."""
    print("\n" + "=" * 60)
    print("SEEDING SEMANTIC MEMORY")
    print("=" * 60)

    if clean:
        deleted = db.long_term_memory.delete_many({
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic"
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing semantic memories")

    preferences = get_semantic_memory_data()

    # Check for existing preferences
    existing_keys = set()
    for pref in db.long_term_memory.find({
        "user_id": DEMO_USER_ID,
        "memory_type": "semantic",
        "semantic_type": "preference"
    }, {"key": 1}):
        existing_keys.add(pref["key"])

    inserted_count = 0
    for pref in preferences:
        if pref["key"] in existing_keys:
            print(f"  ⏭️  Skipping existing: {pref['key']} = {pref['value']}")
            continue

        db.long_term_memory.insert_one(pref)
        print(f"  ✓ Inserted: {pref['key']} = {pref['value']} (confidence: {pref['confidence']}, used {pref['times_used']}x)")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new preferences, {len(existing_keys)} existing")

    return inserted_count


def seed_episodic_memory(db, skip_embeddings: bool = False, clean: bool = False) -> int:
    """Seed episodic memory (past actions)."""
    print("\n" + "=" * 60)
    print("SEEDING EPISODIC MEMORY")
    print("=" * 60)

    if clean:
        deleted = db.long_term_memory.delete_many({
            "user_id": DEMO_USER_ID,
            "memory_type": "episodic"
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing episodic memories")

    # Get current projects for reference
    projects = list(db.projects.find({"user_id": DEMO_USER_ID}))
    actions = get_episodic_memory_data(projects)

    # Check for existing actions by action_type and timestamp (unique combo)
    existing_actions = set()
    for action in db.long_term_memory.find({
        "user_id": DEMO_USER_ID,
        "memory_type": "episodic"
    }, {"action_type": 1, "timestamp": 1}):
        existing_actions.add((action["action_type"], action["timestamp"]))

    inserted_count = 0
    for action in actions:
        action_key = (action["action_type"], action["timestamp"])
        if action_key in existing_actions:
            print(f"  ⏭️  Skipping existing: {action['action_type']} at {action['timestamp']}")
            continue

        # Generate embedding for action if needed
        if not skip_embeddings:
            # Create natural language summary for better semantic matching
            # Enables queries like: "what GTM projects have I done?" → finds past GTM work
            parts = [action['action_type'].replace('_', ' ')]

            # Add entity details in natural language
            if "entity" in action:
                entity = action["entity"]
                if "project_name" in entity:
                    parts.append(f"project {entity['project_name']}")
                if "task_title" in entity:
                    parts.append(f"task {entity['task_title']}")
                if "used_template" in entity:
                    parts.append(f"using {entity['used_template']}")
                if "tasks_generated" in entity:
                    parts.append(f"with {entity['tasks_generated']} tasks")

            # Add key metadata
            if "metadata" in action:
                metadata = action["metadata"]
                if "template_used" in metadata and metadata["template_used"]:
                    parts.append("template-based")
                if "key_outcomes" in metadata:
                    parts.extend(metadata["key_outcomes"])

            searchable_text = " ".join(parts)

            try:
                action["embedding"] = embed_document(searchable_text)

                # Verify embedding dimension (should be 1024 for Voyage AI)
                if len(action["embedding"]) != 1024:
                    print(f"  ⚠️  Warning: Expected 1024 dims, got {len(action['embedding'])}")

                print(f"  📊 Generated embedding for: {action['action_type']} (1024-dim)")
            except Exception as e:
                print(f"  ⚠️  Failed to generate embedding: {e}")
                print(f"      Continuing without embedding for: {action['action_type']}")

        db.long_term_memory.insert_one(action)
        print(f"  ✓ Inserted: {action['action_type']} - {action['entity'].get('project_name', 'N/A')} ({action['outcome']})")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new actions, {len(existing_actions)} existing")

    return inserted_count


def clear_collections(db, collections: List[str] = None) -> Dict[str, int]:
    """
    Clear specified collections for demo user.

    Args:
        db: MongoDB database instance
        collections: List of collection names to clear (default: all demo collections)

    Returns:
        Dictionary of collection names to counts deleted
    """
    if collections is None:
        collections = [
            "projects",
            "tasks",
            "short_term_memory",
            "long_term_memory",
            "shared_memory",
            "tool_discoveries"
        ]

    results = {}

    for collection_name in collections:
        try:
            collection = db[collection_name]
            result = collection.delete_many({"user_id": DEMO_USER_ID})
            results[collection_name] = result.deleted_count
        except Exception as e:
            print(f"  ⚠️  Error clearing {collection_name}: {e}")
            results[collection_name] = 0

    return results


def verify_seed(db) -> Dict[str, Any]:
    """
    Verify critical demo data exists.

    Returns structured result (not just print) for use by other scripts.

    Returns:
        Dictionary with verification results:
        {
            "success": bool,
            "counts": {
                "projects": int,
                "tasks": int,
                "procedural": int,
                "semantic": int,
                "episodic": int
            },
            "critical_items": {
                "gtm_template": bool,
                "project_alpha": bool,
                "q3_gtm": bool,
                "user_preferences": bool
            },
            "missing": List[str]
        }
    """
    results = {
        "success": True,
        "counts": {},
        "critical_items": {},
        "missing": []
    }

    # Count documents
    results["counts"]["projects"] = db.projects.count_documents({"user_id": DEMO_USER_ID})
    results["counts"]["tasks"] = db.tasks.count_documents({"user_id": DEMO_USER_ID})
    results["counts"]["procedural"] = db.long_term_memory.count_documents({
        "user_id": DEMO_USER_ID,
        "memory_type": "procedural"
    })
    results["counts"]["semantic"] = db.long_term_memory.count_documents({
        "user_id": DEMO_USER_ID,
        "memory_type": "semantic"
    })
    results["counts"]["episodic"] = db.long_term_memory.count_documents({
        "user_id": DEMO_USER_ID,
        "memory_type": "episodic"
    })

    # Check critical items
    gtm_template = db.long_term_memory.find_one({
        "user_id": DEMO_USER_ID,
        "memory_type": "procedural",
        "rule_type": "template",
        "name": "GTM Roadmap Template"
    })
    results["critical_items"]["gtm_template"] = gtm_template is not None
    if not gtm_template:
        results["missing"].append("GTM Roadmap Template")
        results["success"] = False

    project_alpha = db.projects.find_one({
        "user_id": DEMO_USER_ID,
        "name": "Project Alpha"
    })
    results["critical_items"]["project_alpha"] = project_alpha is not None
    if not project_alpha:
        results["missing"].append("Project Alpha")
        results["success"] = False

    q3_gtm = db.projects.find_one({
        "user_id": DEMO_USER_ID,
        "name": "Q3 Fintech GTM"
    })
    results["critical_items"]["q3_gtm"] = q3_gtm is not None
    if not q3_gtm:
        results["missing"].append("Q3 Fintech GTM")
        results["success"] = False

    user_preferences = db.long_term_memory.count_documents({
        "user_id": DEMO_USER_ID,
        "memory_type": "semantic",
        "semantic_type": "preference"
    })
    results["critical_items"]["user_preferences"] = user_preferences > 0
    if user_preferences == 0:
        results["missing"].append("User preferences")
        results["success"] = False

    return results


def verify_data(db) -> bool:
    """
    Verify that demo data exists (with print output for CLI).

    This is the CLI-friendly version that prints results.
    For programmatic use, call verify_seed() instead.
    """
    print("\n" + "=" * 60)
    print("VERIFYING DEMO DATA")
    print("=" * 60)

    # Get structured results
    results = verify_seed(db)

    # Print projects
    print(f"\n📁 Projects: {results['counts']['projects']}")
    if results['counts']['projects'] == 0:
        print("  ❌ No projects found")
    else:
        for project in db.projects.find({"user_id": DEMO_USER_ID}, {"name": 1, "status": 1}):
            print(f"    • {project['name']} ({project['status']})")

    # Print tasks
    print(f"\n📋 Tasks: {results['counts']['tasks']}")
    if results['counts']['tasks'] == 0:
        print("  ❌ No tasks found")
    else:
        status_counts = {}
        for task in db.tasks.find({"user_id": DEMO_USER_ID}, {"status": 1}):
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        for status, count in status_counts.items():
            print(f"    • {status}: {count}")

    # Print procedural memory
    print(f"\n🔧 Procedural Memory: {results['counts']['procedural']}")
    if results['counts']['procedural'] == 0:
        print("  ❌ No procedural memories found")
    else:
        for proc in db.long_term_memory.find({
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural"
        }, {"name": 1, "rule_type": 1}):
            print(f"    • {proc.get('name', 'N/A')} ({proc.get('rule_type', 'unknown')})")

    # Print semantic memory
    print(f"\n🧠 Semantic Memory: {results['counts']['semantic']}")
    if results['counts']['semantic'] == 0:
        print("  ❌ No semantic memories found")
    else:
        for sem in db.long_term_memory.find({
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic"
        }, {"key": 1, "value": 1}):
            print(f"    • {sem.get('key', 'N/A')} = {sem.get('value', 'N/A')}")

    # Print episodic memory
    print(f"\n📚 Episodic Memory: {results['counts']['episodic']}")
    if results['counts']['episodic'] == 0:
        print("  ❌ No episodic memories found")
    else:
        for epi in db.long_term_memory.find({
            "user_id": DEMO_USER_ID,
            "memory_type": "episodic"
        }, {"action_type": 1, "timestamp": 1}).sort("timestamp", -1):
            print(f"    • {epi.get('action_type', 'N/A')} at {epi.get('timestamp', 'N/A')}")

    print("\n" + "=" * 60)
    if results["success"]:
        print("✅ ALL DEMO DATA VERIFIED")
    else:
        print("❌ SOME DEMO DATA MISSING")
        if results["missing"]:
            print(f"Missing items: {', '.join(results['missing'])}")
    print("=" * 60)

    return results["success"]


def seed_all(db, clean: bool = False, skip_embeddings: bool = False) -> Dict[str, int]:
    """
    Main orchestrator function - seed all demo data.

    Args:
        db: MongoDB database instance
        clean: If True, clear existing data first
        skip_embeddings: If True, skip generating embeddings

    Returns:
        Dictionary of counts:
        {
            "projects": int,
            "tasks": int,
            "procedural": int,
            "semantic": int,
            "episodic": int,
            "embeddings": int
        }
    """
    results = {}

    # Clear if requested
    if clean:
        clear_results = clear_collections(db)
        print(f"\n🗑️  Cleared collections:")
        for collection, count in clear_results.items():
            if count > 0:
                print(f"    {collection}: {count} deleted")

    # Seed all data types
    results["projects"] = seed_projects(db, clean=False)  # Already cleared if clean=True
    results["tasks"] = seed_tasks(db, clean=False)
    results["procedural"] = seed_procedural_memory(db, skip_embeddings=skip_embeddings, clean=False)
    results["semantic"] = seed_semantic_memory(db, clean=False)
    results["episodic"] = seed_episodic_memory(db, skip_embeddings=skip_embeddings, clean=False)

    # Count embeddings
    if not skip_embeddings:
        embeddings_count = db.long_term_memory.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        results["embeddings"] = embeddings_count
    else:
        results["embeddings"] = 0

    return results


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed demo data for Flow Companion presentation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear existing demo data before seeding"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify demo data exists (no seeding)"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip generating embeddings (faster, but semantic search won't work)"
    )

    args = parser.parse_args()

    # Initialize MongoDB
    print("\n" + "=" * 60)
    print("Flow Companion - Demo Data Seeder")
    print("=" * 60)
    print(f"\nDemo User ID: {DEMO_USER_ID}")

    if args.skip_embeddings:
        print("⚠️  Skipping embeddings (semantic search will not work)")

    try:
        from shared.config import settings
        print(f"\n📡 Connecting to MongoDB...")
        print(f"   Database: {settings.mongodb_database}")

        mongodb = MongoDB()
        db = mongodb.get_database()

        print(f"✓ Connected successfully")
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Verify mode
    if args.verify:
        success = verify_data(db)
        sys.exit(0 if success else 1)

    # Seeding mode
    try:
        # Use seed_all() orchestrator
        results = seed_all(db, clean=args.clean, skip_embeddings=args.skip_embeddings)

        # Final summary
        print("\n" + "=" * 60)
        print("✅ DEMO DATA SEEDING COMPLETE")
        print("=" * 60)

        print(f"\n📊 Summary:")
        print(f"  Projects inserted: {results['projects']}")
        print(f"  Tasks inserted: {results['tasks']}")
        print(f"  Procedural memories inserted: {results['procedural']}")
        print(f"  Semantic memories inserted: {results['semantic']}")
        print(f"  Episodic memories inserted: {results['episodic']}")
        print(f"  Embeddings generated: {results['embeddings']}")

        # Check embeddings status
        if not args.skip_embeddings and results['embeddings'] > 0:
            print(f"\n🔍 Vector Search Enabled:")
            print(f"  Embedding dimension: 1024 (Voyage AI)")
            print(f"\n  ✓ Semantic search queries will work:")
            print(f"    • 'find template for go-to-market' → GTM Roadmap Template")
            print(f"    • 'what GTM projects have I done?' → Past GTM actions")
        elif args.skip_embeddings:
            print(f"\n⚠️  Embeddings skipped - semantic search will not work")

        print(f"\n✨ Demo data ready for presentation!")
        print(f"   User ID: {DEMO_USER_ID}")
        print(f"\n💡 Next steps:")
        print(f"   1. Launch UI: streamlit run ui/streamlit_app.py")
        print(f"   2. Select user: {DEMO_USER_ID}")
        print(f"   3. Demo the 5-tier memory system!")

        print("\n" + "=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
