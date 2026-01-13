#!/usr/bin/env python3
"""
Demo Data Seeder for Flow Companion Presentation

Seeds a complete demo dataset including:
- Projects (8 realistic projects: 4 active, 2 completed, 2 planned)
- Tasks (38 tasks across all projects with varied status/priority)
- Procedural Memory (GTM, Reference Architecture, Blog Post templates + Checklists)
- Semantic Memory (User Preferences)
- Episodic Memory (12+ past actions spanning completed projects and tasks)

This script is designed specifically for presentation demos with realistic,
interconnected data that showcases the 5-tier memory system and supports
varied demo queries.

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
        # In Progress Projects
        {
            "_id": ObjectId(),
            "name": "Project Alpha",
            "description": "Q4 infrastructure modernization initiative focusing on cloud migration and cost optimization",
            "status": "active",
            "created_at": now - timedelta(days=30),
            "last_activity": now - timedelta(days=1),
            "user_id": DEMO_USER_ID,
            "tags": ["infrastructure", "modernization", "cloud"],
            "priority": "high"
        },
        {
            "_id": ObjectId(),
            "name": "Voice Agent Architecture",
            "description": "Real-time audio processing demo with streaming TTS and STT integration",
            "status": "active",
            "created_at": now - timedelta(days=5),
            "last_activity": now - timedelta(hours=12),
            "user_id": DEMO_USER_ID,
            "tags": ["voice", "real-time", "demo", "audio"],
            "priority": "high"
        },
        {
            "_id": ObjectId(),
            "name": "LangGraph Integration",
            "description": "Contributing MongoDB checkpointing backend to LangGraph ecosystem",
            "status": "active",
            "created_at": now - timedelta(days=20),
            "last_activity": now - timedelta(days=2),
            "user_id": DEMO_USER_ID,
            "tags": ["open-source", "langgraph", "integration"],
            "priority": "medium"
        },
        {
            "_id": ObjectId(),
            "name": "Developer Day Presentation",
            "description": "MongoDB Developer Day talk on agentic memory systems and retrieval patterns",
            "status": "active",
            "created_at": now - timedelta(days=15),
            "last_activity": now,
            "user_id": DEMO_USER_ID,
            "tags": ["presentation", "speaking", "mongodb"],
            "priority": "high"
        },

        # Recently Completed Projects
        {
            "_id": ObjectId(),
            "name": "AgentOps Starter Kit",
            "description": "Reference implementation for agent observability with OpenTelemetry and LangSmith",
            "status": "completed",
            "created_at": now - timedelta(days=35),
            "completed_at": now - timedelta(days=7),
            "last_activity": now - timedelta(days=7),
            "user_id": DEMO_USER_ID,
            "tags": ["observability", "agentops", "reference-architecture"],
            "priority": "high"
        },
        {
            "_id": ObjectId(),
            "name": "Memory Engineering Blog Series",
            "description": "Thought leadership content on context engineering and memory patterns for AI agents",
            "status": "completed",
            "created_at": now - timedelta(days=60),
            "completed_at": now - timedelta(days=25),
            "last_activity": now - timedelta(days=25),
            "user_id": DEMO_USER_ID,
            "tags": ["content", "blog", "memory", "thought-leadership"],
            "priority": "medium"
        },

        # Planned Projects
        {
            "_id": ObjectId(),
            "name": "Gaming NPC Memory Demo",
            "description": "Domain-specific hero demo showcasing persistent NPC memory and relationship tracking for gaming vertical",
            "status": "planned",
            "created_at": now - timedelta(days=3),
            "last_activity": now - timedelta(days=3),
            "user_id": DEMO_USER_ID,
            "tags": ["gaming", "demo", "vertical", "npc"],
            "priority": "medium"
        },
        {
            "_id": ObjectId(),
            "name": "Education Tutor Demo",
            "description": "Adaptive tutoring reference app with student knowledge tracking and personalized learning paths",
            "status": "planned",
            "created_at": now - timedelta(days=1),
            "last_activity": now - timedelta(days=1),
            "user_id": DEMO_USER_ID,
            "tags": ["education", "demo", "adaptive-learning"],
            "priority": "low"
        }
    ]


def get_tasks_data(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get task data for seeding - 35+ tasks across 8 projects."""
    now = datetime.utcnow()

    # Create project lookup
    project_lookup = {p["name"]: p for p in projects}

    tasks = []

    # ==================== Project Alpha (6 tasks) ====================
    if "Project Alpha" in project_lookup:
        p = project_lookup["Project Alpha"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Review infrastructure audit report",
                "project": "Project Alpha",
                "project_id": p["_id"],
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
                "project_id": p["_id"],
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
                "project_id": p["_id"],
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
                "title": "Cost-benefit analysis",
                "project": "Project Alpha",
                "project_id": p["_id"],
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
                "project_id": p["_id"],
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
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Create internal communication strategy for rollout",
                "tags": ["communication", "planning"]
            }
        ])

    # ==================== Voice Agent Architecture (7 tasks) ====================
    if "Voice Agent Architecture" in project_lookup:
        p = project_lookup["Voice Agent Architecture"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Build voice agent reference architecture",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "high",
                "created_at": now - timedelta(days=5),
                "started_at": now - timedelta(days=4),
                "user_id": DEMO_USER_ID,
                "description": "Design streaming architecture with WebSocket integration",
                "tags": ["architecture", "websocket", "streaming"]
            },
            {
                "_id": ObjectId(),
                "title": "Integrate Deepgram STT",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "high",
                "created_at": now - timedelta(days=4),
                "started_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Set up real-time speech-to-text with Deepgram API",
                "tags": ["stt", "deepgram", "integration"]
            },
            {
                "_id": ObjectId(),
                "title": "Implement ElevenLabs TTS streaming",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "high",
                "created_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Integrate ElevenLabs streaming TTS for voice responses",
                "tags": ["tts", "elevenlabs", "audio"]
            },
            {
                "_id": ObjectId(),
                "title": "Build conversation state management",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=2),
                "user_id": DEMO_USER_ID,
                "description": "Track turn-taking, interruptions, and conversation context",
                "tags": ["state-management", "conversation"]
            },
            {
                "_id": ObjectId(),
                "title": "Add voice activity detection",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Implement VAD for better turn-taking detection",
                "tags": ["vad", "audio-processing"]
            },
            {
                "_id": ObjectId(),
                "title": "Create demo web interface",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Build simple web UI for voice demo",
                "tags": ["frontend", "demo"]
            },
            {
                "_id": ObjectId(),
                "title": "Write architecture documentation",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(hours=12),
                "user_id": DEMO_USER_ID,
                "description": "Document architecture patterns and integration guide",
                "tags": ["documentation"]
            }
        ])

    # ==================== LangGraph Integration (5 tasks) ====================
    if "LangGraph Integration" in project_lookup:
        p = project_lookup["LangGraph Integration"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Submit PR to LangGraph checkpointing",
                "project": "LangGraph Integration",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=15),
                "completed_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Submitted MongoDB checkpointer implementation to LangGraph",
                "tags": ["open-source", "pr", "code"]
            },
            {
                "_id": ObjectId(),
                "title": "Implement CrewAI memory patterns",
                "project": "LangGraph Integration",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "medium",
                "created_at": now - timedelta(days=10),
                "started_at": now - timedelta(days=8),
                "user_id": DEMO_USER_ID,
                "description": "Add MongoDB support to CrewAI memory system",
                "tags": ["crewai", "memory", "integration"]
            },
            {
                "_id": ObjectId(),
                "title": "Write integration examples",
                "project": "LangGraph Integration",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=5),
                "user_id": DEMO_USER_ID,
                "description": "Create code examples for MongoDB + LangGraph usage",
                "tags": ["examples", "documentation"]
            },
            {
                "_id": ObjectId(),
                "title": "Add unit tests for checkpointer",
                "project": "LangGraph Integration",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "high",
                "created_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Comprehensive test coverage for MongoDB checkpointer",
                "tags": ["testing", "quality"]
            },
            {
                "_id": ObjectId(),
                "title": "Review PR feedback",
                "project": "LangGraph Integration",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=2),
                "user_id": DEMO_USER_ID,
                "description": "Address reviewer comments on PR",
                "tags": ["code-review", "collaboration"]
            }
        ])

    # ==================== Developer Day Presentation (5 tasks) ====================
    if "Developer Day Presentation" in project_lookup:
        p = project_lookup["Developer Day Presentation"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Draft Developer Day presentation slides",
                "project": "Developer Day Presentation",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "high",
                "created_at": now - timedelta(days=12),
                "started_at": now - timedelta(days=10),
                "user_id": DEMO_USER_ID,
                "description": "Create slide deck covering memory systems and retrieval patterns",
                "tags": ["presentation", "slides", "speaking"]
            },
            {
                "_id": ObjectId(),
                "title": "Prepare live demo script",
                "project": "Developer Day Presentation",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "high",
                "created_at": now - timedelta(days=8),
                "started_at": now - timedelta(days=6),
                "user_id": DEMO_USER_ID,
                "description": "Write and practice 7-command demo sequence",
                "tags": ["demo", "script", "practice"]
            },
            {
                "_id": ObjectId(),
                "title": "Create code examples repository",
                "project": "Developer Day Presentation",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=5),
                "user_id": DEMO_USER_ID,
                "description": "Set up GitHub repo with demo code for attendees",
                "tags": ["code", "github", "examples"]
            },
            {
                "_id": ObjectId(),
                "title": "Schedule dry-run with team",
                "project": "Developer Day Presentation",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "high",
                "created_at": now - timedelta(days=2),
                "user_id": DEMO_USER_ID,
                "description": "Practice full presentation with internal team",
                "tags": ["practice", "rehearsal"]
            },
            {
                "_id": ObjectId(),
                "title": "Prepare Q&A talking points",
                "project": "Developer Day Presentation",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Anticipate questions and prepare answers",
                "tags": ["qa", "preparation"]
            }
        ])

    # ==================== AgentOps Starter Kit (5 tasks - all done) ====================
    if "AgentOps Starter Kit" in project_lookup:
        p = project_lookup["AgentOps Starter Kit"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Record AgentOps webinar",
                "project": "AgentOps Starter Kit",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=30),
                "completed_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Record technical webinar on agent observability patterns",
                "tags": ["webinar", "video", "content"]
            },
            {
                "_id": ObjectId(),
                "title": "Publish 'What Is AgentOps?' article",
                "project": "AgentOps Starter Kit",
                "project_id": p["_id"],
                "status": "done",
                "priority": "medium",
                "created_at": now - timedelta(days=28),
                "completed_at": now - timedelta(days=14),
                "user_id": DEMO_USER_ID,
                "description": "Educational article explaining agent operations fundamentals",
                "tags": ["article", "content", "education"]
            },
            {
                "_id": ObjectId(),
                "title": "Implement OpenTelemetry tracing",
                "project": "AgentOps Starter Kit",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=25),
                "completed_at": now - timedelta(days=10),
                "user_id": DEMO_USER_ID,
                "description": "Add distributed tracing with OpenTelemetry",
                "tags": ["observability", "tracing", "code"]
            },
            {
                "_id": ObjectId(),
                "title": "Integrate LangSmith for evaluation",
                "project": "AgentOps Starter Kit",
                "project_id": p["_id"],
                "status": "done",
                "priority": "medium",
                "created_at": now - timedelta(days=20),
                "completed_at": now - timedelta(days=8),
                "user_id": DEMO_USER_ID,
                "description": "Set up LangSmith for agent evaluation and debugging",
                "tags": ["langsmith", "evaluation", "debugging"]
            },
            {
                "_id": ObjectId(),
                "title": "Write reference architecture docs",
                "project": "AgentOps Starter Kit",
                "project_id": p["_id"],
                "status": "done",
                "priority": "medium",
                "created_at": now - timedelta(days=15),
                "completed_at": now - timedelta(days=7),
                "user_id": DEMO_USER_ID,
                "description": "Comprehensive architecture guide with best practices",
                "tags": ["documentation", "architecture"]
            }
        ])

    # ==================== Memory Engineering Blog Series (4 tasks - all done) ====================
    if "Memory Engineering Blog Series" in project_lookup:
        p = project_lookup["Memory Engineering Blog Series"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Write Memory Engineering blog post",
                "project": "Memory Engineering Blog Series",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=55),
                "completed_at": now - timedelta(days=30),
                "user_id": DEMO_USER_ID,
                "description": "Foundational post on memory patterns for AI agents",
                "tags": ["blog", "writing", "content"]
            },
            {
                "_id": ObjectId(),
                "title": "Write multimodal AI tutorial",
                "project": "Memory Engineering Blog Series",
                "project_id": p["_id"],
                "status": "done",
                "priority": "medium",
                "created_at": now - timedelta(days=50),
                "completed_at": now - timedelta(days=28),
                "user_id": DEMO_USER_ID,
                "description": "Tutorial on building multimodal AI applications",
                "tags": ["tutorial", "multimodal", "ai"]
            },
            {
                "_id": ObjectId(),
                "title": "Publish vector search patterns article",
                "project": "Memory Engineering Blog Series",
                "project_id": p["_id"],
                "status": "done",
                "priority": "medium",
                "created_at": now - timedelta(days=45),
                "completed_at": now - timedelta(days=26),
                "user_id": DEMO_USER_ID,
                "description": "Deep dive on vector search and hybrid retrieval",
                "tags": ["vector-search", "rag", "article"]
            },
            {
                "_id": ObjectId(),
                "title": "Create context engineering guide",
                "project": "Memory Engineering Blog Series",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=40),
                "completed_at": now - timedelta(days=25),
                "user_id": DEMO_USER_ID,
                "description": "Comprehensive guide on prompt and context optimization",
                "tags": ["context", "prompting", "guide"]
            }
        ])

    # ==================== Gaming NPC Memory Demo (3 tasks - planned) ====================
    if "Gaming NPC Memory Demo" in project_lookup:
        p = project_lookup["Gaming NPC Memory Demo"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Create gaming NPC memory schema",
                "project": "Gaming NPC Memory Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Design schema for NPC relationships and memory",
                "tags": ["schema", "design", "gaming"]
            },
            {
                "_id": ObjectId(),
                "title": "Build NPC dialogue system",
                "project": "Gaming NPC Memory Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=2),
                "user_id": DEMO_USER_ID,
                "description": "Implement context-aware NPC conversations",
                "tags": ["dialogue", "llm", "gaming"]
            },
            {
                "_id": ObjectId(),
                "title": "Demo at gaming conference",
                "project": "Gaming NPC Memory Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Present NPC memory demo at industry event",
                "tags": ["demo", "conference", "speaking"]
            }
        ])

    # ==================== Education Tutor Demo (3 tasks - planned) ====================
    if "Education Tutor Demo" in project_lookup:
        p = project_lookup["Education Tutor Demo"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Design student knowledge tracking",
                "project": "Education Tutor Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Schema for tracking student understanding and progress",
                "tags": ["education", "schema", "tracking"]
            },
            {
                "_id": ObjectId(),
                "title": "Build adaptive learning algorithm",
                "project": "Education Tutor Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(hours=20),
                "user_id": DEMO_USER_ID,
                "description": "Algorithm for personalized learning path generation",
                "tags": ["algorithm", "adaptive", "ai"]
            },
            {
                "_id": ObjectId(),
                "title": "Schedule quarterly product feedback session",
                "project": "Education Tutor Demo",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "low",
                "created_at": now - timedelta(hours=12),
                "user_id": DEMO_USER_ID,
                "description": "Gather feedback from educators on demo",
                "tags": ["feedback", "research", "planning"]
            }
        ])

    return tasks


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
            "trigger_pattern": "create.*gtm|go.to.market.*project",
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
            "last_used": now - timedelta(days=90),
            "updated_at": now - timedelta(days=90)
        },

        # Reference Architecture Template
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "template",
            "name": "Reference Architecture Template",
            "description": "Standard template for building technical reference implementations and demos",
            "trigger_pattern": "reference.*architecture|demo.*project|starter.*kit",
            "template": {
                "phases": [
                    {
                        "name": "Design",
                        "tasks": [
                            "Define architecture patterns and components",
                            "Create system design diagrams",
                            "Identify key technologies and dependencies",
                            "Document technical requirements"
                        ]
                    },
                    {
                        "name": "Implement",
                        "tasks": [
                            "Build core functionality",
                            "Integrate third-party services",
                            "Add observability and logging",
                            "Implement error handling and validation"
                        ]
                    },
                    {
                        "name": "Document",
                        "tasks": [
                            "Write comprehensive README",
                            "Create architecture decision records",
                            "Document API endpoints and usage",
                            "Add code comments and examples"
                        ]
                    },
                    {
                        "name": "Demo",
                        "tasks": [
                            "Create demo scenarios and scripts",
                            "Build sample applications",
                            "Record walkthrough videos",
                            "Prepare presentation materials"
                        ]
                    }
                ]
            },
            "times_used": 2,
            "success_rate": 1.0,
            "created_at": now - timedelta(days=150),
            "last_used": now - timedelta(days=35),
            "updated_at": now - timedelta(days=35)
        },

        # Blog Post Template
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "template",
            "name": "Blog Post Template",
            "description": "Standard workflow for creating technical blog posts and articles",
            "trigger_pattern": "blog.*post|write.*article|content.*creation",
            "template": {
                "phases": [
                    {
                        "name": "Outline",
                        "tasks": [
                            "Define target audience and learning objectives",
                            "Research topic and gather technical details",
                            "Create content outline with key sections",
                            "Identify code examples and diagrams needed"
                        ]
                    },
                    {
                        "name": "Draft",
                        "tasks": [
                            "Write introduction and hook",
                            "Develop main content sections",
                            "Add code examples and screenshots",
                            "Write conclusion and call-to-action"
                        ]
                    },
                    {
                        "name": "Review",
                        "tasks": [
                            "Technical accuracy review",
                            "Editorial and style review",
                            "Test all code examples",
                            "Optimize for SEO and readability"
                        ]
                    },
                    {
                        "name": "Publish",
                        "tasks": [
                            "Final formatting and layout",
                            "Add images and metadata",
                            "Publish to blog platform",
                            "Promote on social channels"
                        ]
                    }
                ]
            },
            "times_used": 5,
            "success_rate": 0.95,
            "created_at": now - timedelta(days=200),
            "last_used": now - timedelta(days=30),
            "updated_at": now - timedelta(days=30)
        },

        # Market Research Questions Checklist
        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "checklist",
            "name": "Market Research Questions",
            "description": "Standard questions to answer when researching a new market",
            "trigger_pattern": "market.*research|competitive.*analysis",
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
    """Get episodic memory (past actions) for seeding - 10+ varied actions."""
    now = datetime.utcnow()

    # Create project lookup
    project_lookup = {p["name"]: p for p in projects}

    actions = []

    # ==================== AgentOps Starter Kit Actions ====================
    if "AgentOps Starter Kit" in project_lookup:
        p = project_lookup["AgentOps Starter Kit"]
        actions.extend([
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-agentops-1",
                "memory_type": "episodic",
                "action_type": "created_project",
                "entity_type": "project",
                "entity": {
                    "project_name": "AgentOps Starter Kit",
                    "project_id": str(p["_id"]),
                    "used_template": "Reference Architecture Template",
                    "tasks_generated": 5
                },
                "metadata": {
                    "template_used": True,
                    "phases_created": ["Design", "Implement", "Document", "Demo"],
                    "duration_ms": 1500
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=35),
                "created_at": now - timedelta(days=35)
            },
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-agentops-2",
                "memory_type": "episodic",
                "action_type": "completed_task",
                "entity_type": "task",
                "entity": {
                    "task_title": "Record AgentOps webinar",
                    "project_name": "AgentOps Starter Kit",
                    "priority": "high"
                },
                "metadata": {
                    "duration_days": 27,
                    "content_type": "video",
                    "reach": "500+ views"
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=3),
                "created_at": now - timedelta(days=3)
            },
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-agentops-3",
                "memory_type": "episodic",
                "action_type": "completed_project",
                "entity_type": "project",
                "entity": {
                    "project_name": "AgentOps Starter Kit",
                    "project_id": str(p["_id"]),
                    "duration_days": 28,
                    "tasks_completed": 5
                },
                "metadata": {
                    "completion_rate": 1.0,
                    "on_schedule": True,
                    "key_outcomes": [
                        "Published reference architecture",
                        "Recorded educational webinar",
                        "Integrated OpenTelemetry tracing"
                    ]
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=7),
                "created_at": now - timedelta(days=7)
            }
        ])

    # ==================== Memory Engineering Blog Series Actions ====================
    if "Memory Engineering Blog Series" in project_lookup:
        p = project_lookup["Memory Engineering Blog Series"]
        actions.extend([
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-blog-1",
                "memory_type": "episodic",
                "action_type": "created_project",
                "entity_type": "project",
                "entity": {
                    "project_name": "Memory Engineering Blog Series",
                    "project_id": str(p["_id"]),
                    "used_template": "Blog Post Template",
                    "tasks_generated": 4
                },
                "metadata": {
                    "template_used": True,
                    "phases_created": ["Outline", "Draft", "Review", "Publish"],
                    "series": True
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=60),
                "created_at": now - timedelta(days=60)
            },
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-blog-2",
                "memory_type": "episodic",
                "action_type": "completed_task",
                "entity_type": "task",
                "entity": {
                    "task_title": "Write Memory Engineering blog post",
                    "project_name": "Memory Engineering Blog Series",
                    "priority": "high"
                },
                "metadata": {
                    "word_count": 2500,
                    "content_type": "blog",
                    "topic": "memory patterns for AI agents"
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=30),
                "created_at": now - timedelta(days=30)
            },
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-blog-3",
                "memory_type": "episodic",
                "action_type": "completed_project",
                "entity_type": "project",
                "entity": {
                    "project_name": "Memory Engineering Blog Series",
                    "project_id": str(p["_id"]),
                    "duration_days": 35,
                    "tasks_completed": 4
                },
                "metadata": {
                    "completion_rate": 1.0,
                    "posts_published": 4,
                    "total_views": "5000+",
                    "key_topics": ["memory patterns", "multimodal AI", "vector search", "context engineering"]
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=25),
                "created_at": now - timedelta(days=25)
            }
        ])

    # ==================== LangGraph Integration Actions ====================
    if "LangGraph Integration" in project_lookup:
        p = project_lookup["LangGraph Integration"]
        actions.append({
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-langgraph-1",
            "memory_type": "episodic",
            "action_type": "completed_task",
            "entity_type": "task",
            "entity": {
                "task_title": "Submit PR to LangGraph checkpointing",
                "project_name": "LangGraph Integration",
                "priority": "high"
            },
            "metadata": {
                "pr_url": "github.com/langchain-ai/langgraph/pull/xxx",
                "lines_changed": 450,
                "contribution_type": "feature"
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=1),
            "created_at": now - timedelta(days=1)
        })

    # ==================== Project Alpha Actions ====================
    if "Project Alpha" in project_lookup:
        p = project_lookup["Project Alpha"]
        actions.extend([
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-alpha-1",
                "memory_type": "episodic",
                "action_type": "completed_task",
                "entity_type": "task",
                "entity": {
                    "task_title": "Review infrastructure audit report",
                    "project_name": "Project Alpha",
                    "priority": "high"
                },
                "metadata": {
                    "findings_count": 12,
                    "critical_issues": 3,
                    "review_duration_hours": 4
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=20),
                "created_at": now - timedelta(days=20)
            },
            {
                "user_id": DEMO_USER_ID,
                "session_id": f"{DEMO_SESSION_PREFIX}-alpha-2",
                "memory_type": "episodic",
                "action_type": "completed_task",
                "entity_type": "task",
                "entity": {
                    "task_title": "Schedule stakeholder alignment meeting",
                    "project_name": "Project Alpha",
                    "priority": "medium"
                },
                "metadata": {
                    "attendees_count": 8,
                    "stakeholder_groups": ["engineering", "product", "finance"],
                    "alignment_achieved": True
                },
                "outcome": "success",
                "source_agent": "coordinator",
                "triggered_by": "user",
                "timestamp": now - timedelta(days=15),
                "created_at": now - timedelta(days=15)
            }
        ])

    # ==================== Template Usage Actions ====================
    actions.extend([
        {
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-template-1",
            "memory_type": "episodic",
            "action_type": "template_applied",
            "entity_type": "template",
            "entity": {
                "template_name": "Reference Architecture Template",
                "applied_to_project": "AgentOps Starter Kit"
            },
            "metadata": {
                "tasks_generated": 16,
                "phases_used": ["Design", "Implement", "Document", "Demo"],
                "customizations": ["Added OpenTelemetry integration", "Included LangSmith setup"]
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=35),
            "created_at": now - timedelta(days=35)
        },
        {
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-template-2",
            "memory_type": "episodic",
            "action_type": "template_applied",
            "entity_type": "template",
            "entity": {
                "template_name": "Blog Post Template",
                "applied_to_project": "Memory Engineering Blog Series"
            },
            "metadata": {
                "tasks_generated": 16,
                "posts_planned": 4,
                "phases_used": ["Outline", "Draft", "Review", "Publish"]
            },
            "outcome": "success",
            "source_agent": "coordinator",
            "triggered_by": "user",
            "timestamp": now - timedelta(days=60),
            "created_at": now - timedelta(days=60)
        }
    ])

    return actions


# =============================================================================
# SEEDING FUNCTIONS
# =============================================================================

def seed_projects(db, clean: bool = False, skip_embeddings: bool = False) -> int:
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

        # Generate embedding for semantic search
        if not skip_embeddings:
            # Create searchable text: name + description
            # Enables queries like: "infrastructure project" → Project Alpha
            searchable_text = f"{project['name']} {project['description']}"

            try:
                project["embedding"] = embed_document(searchable_text)

                # Verify embedding dimension (should be 1024 for Voyage AI)
                if len(project["embedding"]) != 1024:
                    print(f"  ⚠️  Warning: Expected 1024 dims, got {len(project['embedding'])}")

                print(f"  📊 Generated embedding for: {project['name']} (1024-dim)")
            except Exception as e:
                print(f"  ⚠️  Failed to generate embedding: {e}")
                print(f"      Continuing without embedding for: {project['name']}")

        db.projects.insert_one(project)
        print(f"  ✓ Inserted: {project['name']} ({project['status']})")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new projects, {len(existing_names)} existing")

    return inserted_count


def seed_tasks(db, clean: bool = False, skip_embeddings: bool = False) -> int:
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

        # Generate embedding for semantic search
        if not skip_embeddings:
            # Create searchable text: title + description (if exists)
            # Enables queries like: "debugging task" → Create debugging methodologies doc
            searchable_text = task['title']
            if task.get('description'):
                searchable_text += f" {task['description']}"

            try:
                task["embedding"] = embed_document(searchable_text)

                # Verify embedding dimension (should be 1024 for Voyage AI)
                if len(task["embedding"]) != 1024:
                    print(f"  ⚠️  Warning: Expected 1024 dims, got {len(task['embedding'])}")

                print(f"  📊 Generated embedding for: {task['title']} (1024-dim)")
            except Exception as e:
                print(f"  ⚠️  Failed to generate embedding: {e}")
                print(f"      Continuing without embedding for: {task['title']}")

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

    # Check critical items for expanded demo data
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

    ref_arch_template = db.long_term_memory.find_one({
        "user_id": DEMO_USER_ID,
        "memory_type": "procedural",
        "rule_type": "template",
        "name": "Reference Architecture Template"
    })
    results["critical_items"]["ref_arch_template"] = ref_arch_template is not None
    if not ref_arch_template:
        results["missing"].append("Reference Architecture Template")
        results["success"] = False

    project_alpha = db.projects.find_one({
        "user_id": DEMO_USER_ID,
        "name": "Project Alpha"
    })
    results["critical_items"]["project_alpha"] = project_alpha is not None
    if not project_alpha:
        results["missing"].append("Project Alpha")
        results["success"] = False

    # Check for at least one completed project
    completed_projects = db.projects.count_documents({
        "user_id": DEMO_USER_ID,
        "status": "completed"
    })
    results["critical_items"]["completed_projects"] = completed_projects > 0
    if completed_projects == 0:
        results["missing"].append("Completed projects")
        results["success"] = False

    # Check for varied task statuses
    task_statuses = ["todo", "in_progress", "done"]
    for status in task_statuses:
        count = db.tasks.count_documents({
            "user_id": DEMO_USER_ID,
            "status": status
        })
        if count == 0:
            results["missing"].append(f"Tasks with status: {status}")
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
    results["projects"] = seed_projects(db, clean=False, skip_embeddings=skip_embeddings)  # Already cleared if clean=True
    results["tasks"] = seed_tasks(db, clean=False, skip_embeddings=skip_embeddings)
    results["procedural"] = seed_procedural_memory(db, skip_embeddings=skip_embeddings, clean=False)
    results["semantic"] = seed_semantic_memory(db, clean=False)
    results["episodic"] = seed_episodic_memory(db, skip_embeddings=skip_embeddings, clean=False)

    # Count embeddings across all collections
    if not skip_embeddings:
        # Count embeddings in tasks and projects
        tasks_embeddings = db.tasks.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        projects_embeddings = db.projects.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        # Count embeddings in long_term_memory (procedural + episodic)
        memory_embeddings = db.long_term_memory.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        results["embeddings"] = tasks_embeddings + projects_embeddings + memory_embeddings
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
