#!/usr/bin/env python3
"""
Demo Data Seeder for Flow Companion Presentation

Seeds a complete demo dataset including:
- Projects (8 realistic projects: 4 active, 2 completed, 2 planned)
- Tasks (38 tasks across all projects with varied status/priority)
- Procedural Memory (GTM, Reference Architecture, Blog Post templates + Checklists)
- Semantic Memory (User Preferences + 27 AI/MongoDB/Computer Vision knowledge topics)
- Episodic Memory (12+ past actions spanning completed projects and tasks)
- AI-Generated Episodic Summaries (for demo app sidebar display)

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
    - seed_semantic_memory(db, skip_embeddings, clean) -> int
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
from shared.embeddings import embed_document, build_task_embedding_text, build_project_embedding_text
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
            "description": "Q4 infrastructure modernization initiative focusing on cloud migration and cost optimization. This multi-phase project aims to reduce TCO by 40% while improving system reliability and compliance. We're targeting migration of 15 core services to a hybrid cloud architecture by end of Q1 2026.",
            "context": "Legacy infrastructure running on bare metal is becoming cost-prohibitive and limiting our ability to scale. Board approved $2M budget for modernization based on projected 3-year ROI.",
            "status": "active",
            "created_at": now - timedelta(days=30),
            "last_activity": now - timedelta(days=1),
            "user_id": DEMO_USER_ID,
            "tags": ["infrastructure", "modernization", "cloud", "cost-optimization", "migration"],
            "priority": "high",
            "stakeholders": ["Luffy", "Nami", "Franky's Crew", "Finance"],
            "methods": ["Castlevania Alucard Services", "MongoDB Atlas", "Forgemaster", "MerryCI"],
            "decisions": [
                "Chose phased migration approach over big-bang to minimize risk",
                "Will maintain hybrid cloud for 6 months during transition",
                "DevOps team to own migration execution with external consulting support"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=25),
                    "content": "Project kickoff completed. Infrastructure audit revealed 18 services eligible for migration, 3 requiring major refactoring."
                },
                {
                    "date": now - timedelta(days=15),
                    "content": "Cloud provider evaluation complete. Castlevania selected for compute (Alucard Services), MongoDB Atlas for databases. Estimated 42% cost reduction vs current spend."
                },
                {
                    "date": now - timedelta(days=5),
                    "content": "Phase 1 timeline approved: 6 weeks for non-critical services migration. Security compliance review scheduled for next week."
                }
            ]
        },
        {
            "_id": ObjectId(),
            "name": "Voice Agent Architecture",
            "description": "Real-time audio processing demo with streaming TTS and STT integration for MongoDB Developer Day. Building production-ready reference architecture with WebSocket-based bidirectional audio streaming, conversation state management, and latency optimization. Target: sub-200ms end-to-end latency for natural conversational experience.",
            "context": "Developer Day needs compelling voice agent demo to showcase MongoDB's real-time capabilities and checkpointing for conversation state. This will be the flagship demo for the event.",
            "status": "active",
            "created_at": now - timedelta(days=5),
            "last_activity": now - timedelta(hours=12),
            "user_id": DEMO_USER_ID,
            "tags": ["voice", "real-time", "demo", "audio", "streaming", "websocket", "developer-day"],
            "priority": "high",
            "stakeholders": ["Luffy", "Straw Hat Relations", "Sunny Demo Crew"],
            "methods": ["WebSocket", "SonarSense STT", "SunnyLabs TTS", "MongoDB Change Streams"],
            "decisions": [
                "Using WebSocket for bidirectional streaming instead of separate upload/download endpoints",
                "Storing conversation state in MongoDB with change streams for real-time updates",
                "Building web interface instead of mobile to reduce demo complexity"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=4),
                    "content": "Architecture design complete. Chose SonarSense Nova 2 for STT and SunnyLabs streaming API for TTS. Initial latency tests show 180ms achievable."
                },
                {
                    "date": now - timedelta(days=2),
                    "content": "SonarSense integration working. Real-time transcription with 95% accuracy on test conversations. Working on turn-taking logic next."
                },
                {
                    "date": now - timedelta(hours=12),
                    "content": "Conversation state management implemented with MongoDB. Testing interruption handling - need to improve response cancellation logic."
                }
            ]
        },
        {
            "_id": ObjectId(),
            "name": "GrandLine Integration",
            "description": "Contributing MongoDB checkpointing backend to GrandLine ecosystem as open-source contribution. Implementing BaseCheckpointSaver interface to enable graph state persistence in MongoDB Atlas. This will make MongoDB a first-class citizen in the BelmontChain ecosystem and provide production-grade state management for complex agent workflows.",
            "context": "GrandLine currently only has PostgreSQL and SQLite checkpointers. MongoDB backend would unlock document-based state storage for complex agent graphs and enable our field teams to reference this in customer conversations.",
            "status": "active",
            "created_at": now - timedelta(days=20),
            "last_activity": now - timedelta(days=2),
            "user_id": DEMO_USER_ID,
            "tags": ["open-source", "grandline", "integration", "contribution", "belmontchain"],
            "priority": "medium",
            "stakeholders": ["Luffy", "Sypha Circle", "Belmont Guild"],
            "methods": ["Python", "GrandLine", "MongoDB", "pytest"],
            "decisions": [
                "Implementing full BaseCheckpointSaver interface for compatibility with all GrandLine features",
                "Using separate collection for checkpoints vs threads for better query performance",
                "Including migration guide in docs to help users switch from PostgreSQL checkpointer"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=18),
                    "content": "Initial implementation complete. All BaseCheckpointSaver methods implemented with MongoDB-specific optimizations."
                },
                {
                    "date": now - timedelta(days=10),
                    "content": "Test suite passing 47/50 tests. Debugging serialization issues with complex nested state objects."
                },
                {
                    "date": now - timedelta(days=2),
                    "content": "PR submitted to GrandLine repo! All tests passing. Waiting for maintainer review. Added comprehensive documentation and examples."
                }
            ]
        },
        {
            "_id": ObjectId(),
            "name": "Developer Day Presentation",
            "description": "MongoDB Developer Day talk on agentic memory systems and retrieval patterns for AI applications. 30-minute technical deep-dive covering 5-tier memory architecture, episodic memory implementation, and semantic search optimization techniques. Target audience: senior developers building production AI systems.",
            "context": "MongoDB Developer Day is January 15th with 800+ expected attendees. This is a key opportunity to position MongoDB as the database for AI agents and showcase our expertise in agentic architectures.",
            "status": "active",
            "created_at": now - timedelta(days=15),
            "last_activity": now,
            "user_id": DEMO_USER_ID,
            "tags": ["presentation", "speaking", "mongodb", "developer-day", "ai-agents"],
            "priority": "high",
            "stakeholders": ["Luffy", "Straw Hat Relations", "Grand Line Events", "Product Marketing"], "methods": ["Keynote", "Live Demo", "MongoDB Atlas", "Streamlit"],
            "decisions": [
                "Focus on practical patterns over theory - show working code and architecture diagrams",
                "Lead with impressive voice agent demo to hook audience, then explain memory architecture",
                "Keep slides minimal (15 max) - spend more time on live demo and code walkthrough"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=12),
                    "content": "Outline approved by Dev Rel. Structure: 5 min intro, 10 min architecture deep-dive, 10 min live demo, 5 min Q&A."
                },
                {
                    "date": now - timedelta(days=7),
                    "content": "Slides 60% complete. Working on memory architecture diagrams. Need to finalize demo script this week."
                },
                {
                    "date": now,
                    "content": "Full dry run completed. Timing good at 28 minutes. Feedback: add more context on why episodic memory matters. Revising intro section."
                }
            ]
        },

        # Recently Completed Projects
        {
            "_id": ObjectId(),
            "name": "AgentOps Starter Kit",
            "description": "Reference implementation for agent observability with OpenTelemetry and LangSmith integration. Production-ready starter kit that demonstrates best practices for instrumenting AI agents with distributed tracing, metrics collection, and LLM call monitoring. Released as open-source template repository with comprehensive documentation.",
            "context": "Customers repeatedly asking how to monitor AI agents in production. Built this starter kit to provide reference architecture that field teams can demo and customers can fork.",
            "status": "completed",
            "created_at": now - timedelta(days=35),
            "completed_at": now - timedelta(days=7),
            "last_activity": now - timedelta(days=7),
            "user_id": DEMO_USER_ID,
            "tags": ["observability", "agentops", "reference-architecture", "open-source", "production"],
            "priority": "high",
            "stakeholders": ["Luffy", "Trevor's Engineers", "Product Marketing"], "methods": ["OpenTelemetry", "LangSmith", "Python", "Docker", "Grafana"],
            "decisions": [
                "Used OpenTelemetry for vendor-neutral instrumentation instead of proprietary solutions",
                "Included both self-hosted (Grafana) and SaaS (LangSmith) observability options",
                "Kept codebase minimal (<500 lines) to make it easy to understand and fork"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=28),
                    "content": "Initial implementation complete. All 3 example agents instrumented with OpenTelemetry traces and metrics."
                },
                {
                    "date": now - timedelta(days=14),
                    "content": "Documentation complete including architecture diagrams and deployment guides. Ready for review."
                },
                {
                    "date": now - timedelta(days=7),
                    "content": "Released v1.0! Published to GitHub, added to MongoDB AI resources page. Already seeing 20+ stars and 3 community PRs."
                }
            ]
        },
        {
            "_id": ObjectId(),
            "name": "Memory Engineering Blog Series",
            "description": "Thought leadership content on context engineering and memory patterns for AI agents. 4-part technical blog series covering working memory, episodic memory, semantic memory, and procedural memory implementations. Written for senior developers building production AI systems with concrete code examples and MongoDB-specific optimizations.",
            "context": "Need to establish MongoDB thought leadership in AI agent space. Blog series positions us as experts in agent memory architecture while providing practical value to developer community.",
            "status": "completed",
            "created_at": now - timedelta(days=60),
            "completed_at": now - timedelta(days=25),
            "last_activity": now - timedelta(days=25),
            "user_id": DEMO_USER_ID,
            "tags": ["content", "blog", "memory", "thought-leadership", "technical-writing"],
            "priority": "medium",
            "stakeholders": ["Luffy", "Content Marketing", "Straw Hat Relations"], "methods": ["Robin's Docs", "MongoDB", "Python", "Code Examples"],
            "decisions": [
                "Publishing on MongoDB blog for SEO benefit rather than Medium/personal blog",
                "Including companion GitHub repo with full working examples for each pattern",
                "Targeting senior developer audience - assuming familiarity with LLMs and databases"
            ],
            "updates": [
                {
                    "date": now - timedelta(days=50),
                    "content": "Outlines complete for all 4 posts. Part 1 (Working Memory) first draft done, in review with Dev Rel."
                },
                {
                    "date": now - timedelta(days=35),
                    "content": "Parts 1 and 2 published! Great engagement: 5K views, 200+ shares. Comments asking for more real-world examples."
                },
                {
                    "date": now - timedelta(days=25),
                    "content": "Series complete! Part 4 published. Total series: 15K views, featured in 3 AI newsletters. Companion repo has 150 stars."
                }
            ]
        },

        # Planned Projects
        {
            "_id": ObjectId(),
            "name": "Gaming NPC Memory Demo",
            "description": "Domain-specific hero demo showcasing persistent NPC memory and relationship tracking for gaming vertical. Build playable RPG demo where NPCs remember conversations, player actions, and relationship history using MongoDB's memory patterns. Designed to resonate with game developers and showcase MongoDB's fit for gaming use cases.",
            "context": "Gaming is a strategic vertical for MongoDB. This demo will showcase how MongoDB's flexible schema and memory patterns enable rich NPC behavior that would be difficult with traditional game databases.",
            "status": "planned",
            "created_at": now - timedelta(days=3),
            "last_activity": now - timedelta(days=3),
            "user_id": DEMO_USER_ID,
            "tags": ["gaming", "demo", "vertical", "npc", "memory", "relationships"],
            "priority": "medium",
            "stakeholders": ["Gaming Sales Team", "Product Marketing", "Luffy"], "methods": ["Unity", "MongoDB Atlas", "Vector Search", "LLM Integration"],
            "decisions": []
        },
        {
            "_id": ObjectId(),
            "name": "Education Tutor Demo",
            "description": "Adaptive tutoring reference app with student knowledge tracking and personalized learning paths. AI tutor that maintains detailed student models including knowledge gaps, learning style preferences, and progress history. Demonstrates how MongoDB's memory patterns enable personalized education at scale.",
            "context": "Education technology is another strategic vertical. This demo will show how MongoDB enables personalized learning experiences that adapt to each student's needs and learning history.",
            "status": "planned",
            "created_at": now - timedelta(days=1),
            "last_activity": now - timedelta(days=1),
            "user_id": DEMO_USER_ID,
            "tags": ["education", "demo", "adaptive-learning", "edtech", "personalization"],
            "priority": "low",
            "stakeholders": ["EdTech Sales Team", "Luffy"], "methods": ["Streamlit", "MongoDB Atlas", "OpenAI GPT-4", "Learning Analytics"],
            "decisions": []
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
                "description": "Analyze findings from Q3 infrastructure audit conducted by external consultants. Identify critical issues, assess risk levels, and create prioritized action plan for modernization initiative. Report includes performance benchmarks, cost analysis, and security compliance gaps.",
                "context": "Audit was commissioned to provide objective assessment before committing to $2M modernization budget. Results will inform migration strategy and timeline.",
                "tags": ["audit", "review", "analysis"],
                "assignee": "Zoro",
                "notes": [
                    "Key findings: 18 services eligible for cloud migration, 3 require major refactoring",
                    "Performance issues: Database queries 3x slower than industry benchmarks",
                    "Security gaps: 7 high-priority vulnerabilities identified in authentication layer"
                ]
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
                "description": "Align key stakeholders on modernization approach, migration strategy, and timeline. Present audit findings, proposed architecture, and get buy-in from Finance, Engineering, and Executive leadership.",
                "context": "Critical to get stakeholder alignment before detailed planning phase. Finance particularly concerned about cost overruns.",
                "tags": ["meeting", "stakeholders", "alignment"],
                "assignee": "Nami",
                "notes": [
                    "Meeting scheduled for Dec 15th, 2 hours allocated",
                    "Attendees: Mike (tech lead), Sarah (PM), Finance VP, CTO, DevOps manager",
                    "Outcome: Unanimous approval for phased approach, monthly cost reporting requirement added"
                ]
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
                "description": "Create detailed phased migration timeline with task dependencies, resource allocation, and risk mitigation strategies. Timeline must account for zero-downtime requirements and include rollback plans for each phase.",
                "context": "Board wants to see detailed timeline before final budget approval. Need to demonstrate we've thought through dependencies and risks.",
                "tags": ["planning", "timeline", "project-management"],
                "assignee": "Luffy",
                "due_date": now - timedelta(days=3),  # 3 days overdue
                "blockers": [
                    "Waiting on DevOps team capacity planning for Q1 2026",
                    "Need to finalize Castlevania architecture before estimating Phase 1 duration"
                ],
                "notes": [
                    "Draft structure: Phase 1 (6 weeks) - non-critical services, Phase 2 (8 weeks) - core services, Phase 3 (4 weeks) - auth refactor",
                    "Dependencies mapped: Auth service must be last due to system-wide impact",
                    "Risk: Holiday freeze in December will delay start by 2 weeks"
                ]
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
                "description": "Quantify expected ROI and TCO reduction over 3-year period. Build financial model comparing current infrastructure costs vs projected cloud costs including migration expenses. Present results to Finance for final budget approval.",
                "context": "Finance needs detailed ROI projections before releasing full $2M budget. CFO specifically wants 3-year TCO comparison.",
                "tags": ["analysis", "roi", "finance"],
                "assignee": "Nami",
                "due_date": now + timedelta(days=2),  # Due soon (not overdue)
                "notes": [
                    "Initial calculations show 42% cost reduction by year 2",
                    "Need to include: current hosting costs, Castlevania compute/storage costs, migration labor, training"
                ]
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
                "description": "Ensure modernization plan meets SOC2 Type II requirements and doesn't introduce new compliance risks. Review proposed architecture with security team and document compliance controls for each migration phase.",
                "context": "Company is SOC2 certified and audit is in 4 months. Can't introduce compliance gaps during migration or we risk losing certification.",
                "tags": ["security", "compliance", "soc2"],
                "assignee": "Alucard Guard",
                "due_date": now - timedelta(days=5),  # 5 days overdue
                "blockers": [
                    "Security team backlog is 3 weeks out - may need to escalate for priority review"
                ]
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
                "description": "Create internal communication strategy for infrastructure modernization rollout. Plan includes: pre-migration announcements, phase-by-phase updates, troubleshooting resources, and success celebration.",
                "context": "DevOps team stressed about managing user expectations during migration. Good communication can prevent panic when services are temporarily affected.",
                "tags": ["communication", "planning", "change-management"],
                "assignee": "Robin",
                "notes": [
                    "Target audience: Engineering (100 people), Product (30 people), Customer Support (50 people)",
                    "Channels: Slack announcements, email updates, documentation wiki"
                ]
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
                "description": "Design streaming architecture with WebSocket integration for bidirectional audio. Architecture must support real-time transcription, response generation, and audio playback with <200ms latency. Include conversation state persistence in MongoDB for demo continuity.",
                "context": "This is the foundational architecture for Developer Day demo. Need to nail the streaming architecture first before building higher-level features.",
                "tags": ["architecture", "websocket", "streaming", "real-time"],
                "assignee": "Sanji",
                "due_date": now - timedelta(days=1),  # 1 day overdue
                "notes": [
                    "Architecture decision: Using WebSocket for full-duplex communication instead of HTTP polling",
                    "State storage: MongoDB change streams for real-time conversation updates",
                    "Latency target: <200ms end-to-end for natural conversation feel"
                ],
                "blockers": [
                    "Need to decide: Server-side audio buffering strategy to minimize latency"
                ]
            },
            {
                "_id": ObjectId(),
                "title": "Integrate SonarSense STT",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "high",
                "created_at": now - timedelta(days=4),
                "started_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Set up real-time speech-to-text with SonarSense Nova 2 API. Implement streaming transcription with interim results for real-time feedback. Handle audio format conversion (browser -> SonarSense) and implement error recovery for network issues.",
                "context": "SonarSense selected after benchmarking 3 STT providers. Nova 2 model has best accuracy (95%) and lowest latency (140ms) for our use case.",
                "tags": ["stt", "sonarsense", "integration", "audio"],
                "assignee": "Luffy",
                "notes": [
                    "API integration complete - achieving 140ms transcription latency",
                    "Accuracy testing: 95% on customer support conversations, 88% with background noise",
                    "Next: Implement punctuation and capitalization post-processing"
                ]
            },
            {
                "_id": ObjectId(),
                "title": "Implement SunnyLabs TTS streaming",
                "project": "Voice Agent Architecture",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "high",
                "created_at": now - timedelta(days=3),
                "user_id": DEMO_USER_ID,
                "description": "Integrate SunnyLabs streaming TTS for voice responses",
                "tags": ["tts", "sunnylabs", "audio"]
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

    # ==================== GrandLine Integration (5 tasks) ====================
    if "GrandLine Integration" in project_lookup:
        p = project_lookup["GrandLine Integration"]
        tasks.extend([
            {
                "_id": ObjectId(),
                "title": "Submit PR to GrandLine checkpointing",
                "project": "GrandLine Integration",
                "project_id": p["_id"],
                "status": "done",
                "priority": "high",
                "created_at": now - timedelta(days=15),
                "completed_at": now - timedelta(days=1),
                "user_id": DEMO_USER_ID,
                "description": "Submitted MongoDB checkpointer implementation to GrandLine",
                "tags": ["open-source", "pr", "code"]
            },
            {
                "_id": ObjectId(),
                "title": "Implement StrawHat AI memory patterns",
                "project": "GrandLine Integration",
                "project_id": p["_id"],
                "status": "in_progress",
                "priority": "medium",
                "created_at": now - timedelta(days=10),
                "started_at": now - timedelta(days=8),
                "user_id": DEMO_USER_ID,
                "description": "Add MongoDB support to StrawHat AI memory system",
                "tags": ["strawhat-ai", "memory", "integration"]
            },
            {
                "_id": ObjectId(),
                "title": "Write integration examples",
                "project": "GrandLine Integration",
                "project_id": p["_id"],
                "status": "todo",
                "priority": "medium",
                "created_at": now - timedelta(days=5),
                "user_id": DEMO_USER_ID,
                "description": "Create code examples for MongoDB + GrandLine usage",
                "tags": ["examples", "documentation"]
            },
            {
                "_id": ObjectId(),
                "title": "Add unit tests for checkpointer",
                "project": "GrandLine Integration",
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
                "project": "GrandLine Integration",
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
        # ═════════════════════════════════════════════════════════════════
        # WORKFLOWS - Multi-step operation patterns
        # ═════════════════════════════════════════════════════════════════

        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "workflow",
            "name": "Create Task and Start Workflow",
            "description": "Pattern for creating a task and immediately starting work on it",
            "trigger_pattern": r"create.*task.*(?:then|and)\s+start",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "create_task",
                        "extract_from_user": ["title", "project_name", "priority", "assignee", "due_date"],
                        "capture_result": "task_id"
                    },
                    {
                        "step": 2,
                        "action": "start_task",
                        "use_captured": {"task_id": "step_1.task_id"},
                        "description": "Mark the newly created task as in_progress"
                    }
                ],
                "success_criteria": "Both tools return success=true"
            },
            "examples": [
                "Create a task for API docs, assign to Sarah, due tomorrow, then start it",
                "Create high priority task for testing and start working on it"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": now,
            "last_used": None,
            "updated_at": now
        },

        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "workflow",
            "name": "Query and Complete Workflow",
            "description": "Pattern for finding tasks and completing the first/selected one",
            "trigger_pattern": r"(show|what\'s|list).*(?:then|and)\s+(complete|mark.*done|finish)",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "get_tasks",
                        "extract_from_user": ["status", "priority"],
                        "capture_result": "tasks"
                    },
                    {
                        "step": 2,
                        "action": "confirm_selection",
                        "description": "Show results and ask user which task to complete",
                        "wait_for_user": True
                    },
                    {
                        "step": 3,
                        "action": "complete_task",
                        "use_captured": {"task_id": "step_2.selected_task_id"}
                    }
                ],
                "success_criteria": "Task status changes to done"
            },
            "examples": [
                "Show me what's overdue, then complete the first one",
                "What's blocked? Mark the top one as done"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": now,
            "last_used": None,
            "updated_at": now
        },

        {
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "workflow",
            "name": "Search and Add Note Workflow",
            "description": "Pattern for finding a task and adding a note to it",
            "trigger_pattern": r"add.*note.*to|note.*on.*task",
            "workflow": {
                "steps": [
                    {
                        "step": 1,
                        "action": "search_tasks",
                        "extract_from_user": ["task_reference"],
                        "capture_result": "tasks"
                    },
                    {
                        "step": 2,
                        "action": "confirm_selection",
                        "description": "Ask which task if multiple matches",
                        "wait_for_user": True
                    },
                    {
                        "step": 3,
                        "action": "add_note_to_task",
                        "use_captured": {
                            "task_id": "step_2.selected_task_id",
                            "note": "user_input.note_content"
                        }
                    }
                ],
                "success_criteria": "Note appears in task's notes array"
            },
            "examples": [
                "Add a note to the migration task: completed phase 1",
                "Note on API docs task: reviewed by Sarah"
            ],
            "times_used": 0,
            "success_rate": 1.0,
            "created_at": now,
            "last_used": None,
            "updated_at": now
        },

        # ═════════════════════════════════════════════════════════════════
        # TEMPLATES - Project and task generation patterns
        # ═════════════════════════════════════════════════════════════════

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


def get_knowledge_base_data() -> List[Dict[str, Any]]:
    """Get AI/MongoDB/Computer Vision knowledge for semantic memory."""
    now = datetime.utcnow()

    return [
        # ═══════════════════════════════════════════════════════════════
        # AI FRAMEWORKS & TOOLS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "langchain_framework",
            "value": "LangChain is a popular Python framework for building LLM applications with chains, agents, and memory. It provides abstractions for prompts, callbacks, and tool integration. Key features include LCEL (LangChain Expression Language), LangGraph for stateful agents, and LangSmith for observability.",
            "tags": ["framework", "python", "llm", "agents"],
            "confidence": 0.95,
            "source": "research"
        },
        {
            "key": "langgraph_agents",
            "value": "LangGraph enables building stateful, multi-actor agents with cycles and persistence. It supports checkpointing for state management, human-in-the-loop workflows, and complex agent orchestration. Built on top of LangChain with graph-based execution.",
            "tags": ["framework", "agents", "stateful", "langchain"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "anthropic_claude",
            "value": "Anthropic Claude is a large language model family known for long context windows (200K+), strong instruction following, and safety features. Claude 3.5 Sonnet offers excellent balance of speed, intelligence, and cost. Supports tool use, prompt caching, and vision.",
            "tags": ["llm", "anthropic", "claude", "ai"],
            "confidence": 0.95,
            "source": "research"
        },
        {
            "key": "openai_gpt",
            "value": "OpenAI GPT-4 is a multimodal LLM supporting text and images. GPT-4 Turbo offers 128K context, function calling, and vision capabilities. GPT-4o optimizes for speed and cost. Widely used for chatbots, coding assistants, and content generation.",
            "tags": ["llm", "openai", "gpt", "multimodal"],
            "confidence": 0.94,
            "source": "research"
        },
        {
            "key": "llamaindex_framework",
            "value": "LlamaIndex (formerly GPT Index) is a data framework for LLM applications. Specializes in ingestion, indexing, and querying of private data. Supports multiple data sources, vector stores, and retrieval strategies including hybrid search.",
            "tags": ["framework", "rag", "retrieval", "indexing"],
            "confidence": 0.90,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # MONGODB & VECTOR SEARCH
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "mongodb_vector_search",
            "value": "MongoDB Atlas Vector Search enables semantic similarity search using embeddings. Supports hybrid search combining vector similarity with traditional text search, uses HNSW indexing for fast approximate nearest neighbor queries, and integrates with popular embedding providers like OpenAI and Voyage AI.",
            "tags": ["database", "vector-search", "embeddings", "mongodb"],
            "confidence": 0.95,
            "source": "research"
        },
        {
            "key": "mongodb_aggregation",
            "value": "MongoDB aggregation pipeline provides powerful data processing with stages like $match, $group, $project, and $lookup. Atlas Search stages include $search and $vectorSearch. Optimized for complex queries with indexing support and parallel execution.",
            "tags": ["database", "mongodb", "query", "aggregation"],
            "confidence": 0.93,
            "source": "research"
        },
        {
            "key": "mongodb_atlas_search",
            "value": "Atlas Search provides full-text search with Lucene-based indexing. Features include fuzzy matching, autocomplete, faceting, and synonyms. Supports compound queries combining text, numeric, and geospatial filters. Integrates seamlessly with aggregation pipelines.",
            "tags": ["database", "mongodb", "search", "atlas"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "hnsw_indexing",
            "value": "Hierarchical Navigable Small World (HNSW) is an approximate nearest neighbor algorithm used for vector search. Provides fast similarity search with configurable accuracy-speed tradeoffs. Used by MongoDB Atlas Vector Search, Pinecone, and other vector databases.",
            "tags": ["algorithm", "vector-search", "indexing", "performance"],
            "confidence": 0.88,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # AI AGENT ARCHITECTURES
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "ai_agent_memory",
            "value": "AI agent memory systems typically include short-term (working memory), long-term (episodic/semantic), and procedural memory. Modern approaches use vector databases for semantic recall, confidence scoring for preference learning, and temporal decay for relevance. Key challenges include memory consolidation and conflict resolution.",
            "tags": ["ai-agents", "memory", "architecture", "vector-db"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "react_agents",
            "value": "ReAct (Reasoning + Acting) is an agent architecture where LLMs alternate between reasoning about the next action and executing tools. Enables iterative problem-solving with thought traces. Widely used in frameworks like LangChain and AutoGPT.",
            "tags": ["agents", "architecture", "reasoning", "tools"],
            "confidence": 0.91,
            "source": "research"
        },
        {
            "key": "tool_calling",
            "value": "LLM tool calling (function calling) allows models to invoke external functions with structured parameters. Modern LLMs like Claude and GPT-4 natively support tool use. Enables agents to interact with APIs, databases, and services while maintaining conversation flow.",
            "tags": ["llm", "tools", "agents", "api"],
            "confidence": 0.93,
            "source": "research"
        },
        {
            "key": "rag_architecture",
            "value": "Retrieval-Augmented Generation (RAG) combines LLMs with information retrieval. Query is embedded, similar documents retrieved from vector database, then provided as context to LLM. Reduces hallucinations and enables querying of private data without fine-tuning.",
            "tags": ["architecture", "retrieval", "embeddings", "llm"],
            "confidence": 0.94,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # EMBEDDINGS & NLP
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "voyage_embeddings",
            "value": "Voyage AI provides state-of-the-art embedding models optimized for retrieval. Voyage-3 offers 1024-dimensional embeddings with superior performance on semantic search tasks. Supports domain-specific fine-tuning and batch processing.",
            "tags": ["embeddings", "voyage", "retrieval", "semantic"],
            "confidence": 0.91,
            "source": "research"
        },
        {
            "key": "openai_embeddings",
            "value": "OpenAI text-embedding-3-large and text-embedding-3-small provide high-quality embeddings for semantic search. Support up to 8191 tokens input, customizable dimensions, and batch processing. Widely used for RAG and similarity search applications.",
            "tags": ["embeddings", "openai", "semantic", "retrieval"],
            "confidence": 0.93,
            "source": "research"
        },
        {
            "key": "semantic_search",
            "value": "Semantic search finds results based on meaning rather than keyword matching. Uses embeddings to encode queries and documents in vector space, then computes similarity (cosine, dot product). Outperforms keyword search for conceptual queries.",
            "tags": ["search", "embeddings", "nlp", "retrieval"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "hybrid_search",
            "value": "Hybrid search combines vector similarity search with traditional keyword search using algorithms like Reciprocal Rank Fusion (RRF). Balances semantic understanding with exact keyword matches. MongoDB Atlas supports native hybrid search via $rankFusion.",
            "tags": ["search", "hybrid", "mongodb", "retrieval"],
            "confidence": 0.91,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # PROMPT ENGINEERING & OPTIMIZATION
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "prompt_engineering",
            "value": "Prompt engineering involves optimizing LLM inputs for better outputs. Techniques include few-shot examples, chain-of-thought reasoning, prompt compression, and caching. Context window management is critical - reducing token counts improves latency and reduces costs.",
            "tags": ["llm", "optimization", "prompts", "caching"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "prompt_caching",
            "value": "Anthropic Claude supports prompt caching to reuse frequently repeated context. System prompts and tool definitions can be cached for 5 minutes, reducing latency by 80-90% and costs by 90% on cached portions. Requires minimum 1024 tokens to cache.",
            "tags": ["optimization", "caching", "anthropic", "performance"],
            "confidence": 0.93,
            "source": "research"
        },
        {
            "key": "context_compression",
            "value": "Context compression reduces LLM input tokens while preserving key information. Techniques include summarization, entity extraction, and selective context inclusion. Can achieve 50-80% token reduction with minimal quality loss, improving speed and cost.",
            "tags": ["optimization", "compression", "tokens", "performance"],
            "confidence": 0.89,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # COMPUTER VISION
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "clip_model",
            "value": "CLIP (Contrastive Language-Image Pre-training) from OpenAI learns visual concepts from natural language descriptions. Enables zero-shot image classification, image-text matching, and multimodal embeddings. Foundation for image search and generation models.",
            "tags": ["computer-vision", "multimodal", "openai", "embeddings"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "yolo_object_detection",
            "value": "YOLO (You Only Look Once) is a real-time object detection system. YOLOv8 offers state-of-the-art accuracy with fast inference speeds. Single-stage detector processes images in one forward pass, suitable for video processing and robotics applications.",
            "tags": ["computer-vision", "object-detection", "real-time", "yolo"],
            "confidence": 0.91,
            "source": "research"
        },
        {
            "key": "stable_diffusion",
            "value": "Stable Diffusion is an open-source text-to-image generation model using latent diffusion. Supports image generation, inpainting, and style transfer. Runs efficiently on consumer GPUs. Popular for creative applications and customizable with LoRA fine-tuning.",
            "tags": ["computer-vision", "generation", "diffusion", "image"],
            "confidence": 0.89,
            "source": "research"
        },
        {
            "key": "vision_transformers",
            "value": "Vision Transformers (ViT) apply transformer architecture to images by treating image patches as tokens. Achieved state-of-the-art results on image classification. Foundation for models like CLIP, DINO, and multimodal LLMs like GPT-4V and Claude 3.",
            "tags": ["computer-vision", "transformers", "architecture", "image"],
            "confidence": 0.88,
            "source": "research"
        },
        {
            "key": "sam_segmentation",
            "value": "Segment Anything Model (SAM) from Meta AI enables zero-shot image segmentation with prompts (points, boxes, text). Trained on 1 billion masks, supports automatic mask generation and interactive segmentation. Useful for image editing, annotation, and robotics.",
            "tags": ["computer-vision", "segmentation", "meta", "zero-shot"],
            "confidence": 0.87,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # MLOps & MONITORING
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "langsmith_observability",
            "value": "LangSmith provides observability for LLM applications with tracing, debugging, and evaluation. Tracks token usage, latency, and errors across chains. Supports dataset creation, prompt versioning, and A/B testing for LLM applications.",
            "tags": ["mlops", "observability", "langchain", "monitoring"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "agentops_monitoring",
            "value": "AgentOps provides specialized monitoring for AI agents including agent traces, tool call tracking, and multi-step workflow visualization. Supports cost tracking, latency analysis, and error debugging. Integrates with LangChain, CrewAI, and custom agents.",
            "tags": ["mlops", "monitoring", "agents", "observability"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "opentelemetry_tracing",
            "value": "OpenTelemetry provides standardized observability with traces, metrics, and logs. For LLM apps, tracks request flows, tool calls, and performance. Vendor-agnostic with exporters for Datadog, New Relic, and custom backends.",
            "tags": ["mlops", "tracing", "observability", "telemetry"],
            "confidence": 0.89,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # VECTOR DATABASES
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "pinecone_vectordb",
            "value": "Pinecone is a managed vector database optimized for similarity search at scale. Supports metadata filtering, hybrid search, and real-time updates. Popular for RAG applications, recommendation systems, and semantic search.",
            "tags": ["vector-db", "database", "search", "managed"],
            "confidence": 0.91,
            "source": "research"
        },
        {
            "key": "weaviate_vectordb",
            "value": "Weaviate is an open-source vector database with built-in vectorization modules. Supports GraphQL and REST APIs, hybrid search, and multi-tenancy. Integrates with Cohere, OpenAI, and Hugging Face for automatic embedding generation.",
            "tags": ["vector-db", "database", "open-source", "graphql"],
            "confidence": 0.88,
            "source": "research"
        },
        {
            "key": "qdrant_vectordb",
            "value": "Qdrant is a high-performance vector database written in Rust. Features advanced filtering, payload indexing, and distributed deployment. Offers quantization for memory efficiency and supports SIMD optimization for fast similarity search.",
            "tags": ["vector-db", "database", "rust", "performance"],
            "confidence": 0.87,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # AI TECHNIQUES & CONCEPTS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "few_shot_learning",
            "value": "Few-shot learning enables models to learn from limited examples. In LLMs, providing 1-5 examples in the prompt guides output format and style. More effective than zero-shot for structured outputs, classification, and domain-specific tasks.",
            "tags": ["technique", "llm", "learning", "prompts"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "chain_of_thought",
            "value": "Chain-of-Thought (CoT) prompting encourages LLMs to show reasoning steps before answering. Significantly improves performance on complex reasoning tasks. Variants include zero-shot CoT ('Let's think step by step') and few-shot CoT with examples.",
            "tags": ["technique", "reasoning", "prompts", "llm"],
            "confidence": 0.91,
            "source": "research"
        },
        {
            "key": "fine_tuning_llms",
            "value": "LLM fine-tuning adapts pre-trained models to specific tasks or domains. Techniques include full fine-tuning, LoRA (Low-Rank Adaptation), and PEFT (Parameter-Efficient Fine-Tuning). Trade-offs between cost, quality, and inference speed compared to few-shot prompting.",
            "tags": ["technique", "training", "llm", "adaptation"],
            "confidence": 0.89,
            "source": "research"
        },
        {
            "key": "retrieval_augmented_generation",
            "value": "RAG enhances LLM responses by retrieving relevant documents from a knowledge base. Typical flow: embed query → vector search → inject results as context → generate response. Reduces hallucinations and enables querying of private/recent data.",
            "tags": ["architecture", "rag", "retrieval", "llm"],
            "confidence": 0.94,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # AGENT PATTERNS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "multi_agent_systems",
            "value": "Multi-agent systems coordinate multiple specialized agents for complex tasks. Patterns include hierarchical (manager-worker), peer-to-peer (collaborative), and marketplace (competitive bidding). Requires communication protocols, task distribution, and conflict resolution.",
            "tags": ["agents", "architecture", "coordination", "systems"],
            "confidence": 0.88,
            "source": "research"
        },
        {
            "key": "agent_handoffs",
            "value": "Agent handoffs transfer conversation context between specialized agents. Shared memory enables context preservation across handoffs. Common in customer service (sales → support) and technical workflows (retrieval → processing → synthesis).",
            "tags": ["agents", "coordination", "memory", "handoff"],
            "confidence": 0.87,
            "source": "research"
        },
        {
            "key": "autonomous_agents",
            "value": "Autonomous agents operate independently with goals, planning, and self-correction. Examples include AutoGPT, BabyAGI, and AgentGPT. Challenges include task decomposition, long-horizon planning, and preventing infinite loops. Requires robust error handling.",
            "tags": ["agents", "autonomous", "planning", "ai"],
            "confidence": 0.86,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # COMPUTER VISION APPLICATIONS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "visual_question_answering",
            "value": "Visual Question Answering (VQA) systems answer questions about images using multimodal models. Modern approaches use vision-language models like GPT-4V, Claude 3, or BLIP-2. Applications include accessibility, content moderation, and visual search.",
            "tags": ["computer-vision", "multimodal", "qa", "vqa"],
            "confidence": 0.88,
            "source": "research"
        },
        {
            "key": "image_embeddings",
            "value": "Image embeddings encode visual content as fixed-size vectors for similarity search. CLIP produces multimodal embeddings aligned with text. DINOv2 excels at general visual features. Used for reverse image search, content-based recommendation, and duplicate detection.",
            "tags": ["computer-vision", "embeddings", "search", "multimodal"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "ocr_document_ai",
            "value": "Optical Character Recognition (OCR) extracts text from images and PDFs. Modern approaches combine traditional OCR (Tesseract) with deep learning (PaddleOCR, EasyOCR). Document AI adds layout analysis, table extraction, and form understanding.",
            "tags": ["computer-vision", "ocr", "document", "extraction"],
            "confidence": 0.89,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # DEVELOPER TOOLS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "streamlit_framework",
            "value": "Streamlit is a Python framework for building data apps and ML dashboards with minimal code. Supports reactive updates, caching, and session state. Popular for prototyping LLM interfaces, data visualization, and internal tools.",
            "tags": ["framework", "python", "ui", "dashboard"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "gradio_interfaces",
            "value": "Gradio creates web interfaces for ML models with Python functions. Supports chat interfaces, file uploads, and real-time updates. Integrates with Hugging Face Spaces for easy deployment. Popular for model demos and prototyping.",
            "tags": ["framework", "ui", "ml", "python"],
            "confidence": 0.88,
            "source": "research"
        },
        {
            "key": "fastapi_framework",
            "value": "FastAPI is a modern Python web framework for building APIs with automatic OpenAPI documentation. Supports async/await, type validation with Pydantic, and dependency injection. Popular for LLM application backends and microservices.",
            "tags": ["framework", "api", "python", "backend"],
            "confidence": 0.91,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # AI SAFETY & ETHICS
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "llm_hallucinations",
            "value": "LLM hallucinations occur when models generate plausible but factually incorrect information. Mitigation strategies include RAG for grounding, citation requirements, confidence scoring, and fact-checking layers. More common in low-probability scenarios.",
            "tags": ["safety", "llm", "accuracy", "mitigation"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "ai_alignment",
            "value": "AI alignment ensures systems behave according to human values and intentions. Techniques include RLHF (Reinforcement Learning from Human Feedback), Constitutional AI, and red-teaming. Critical for safe deployment of autonomous agents and powerful models.",
            "tags": ["safety", "alignment", "ethics", "rlhf"],
            "confidence": 0.87,
            "source": "research"
        },

        # ═══════════════════════════════════════════════════════════════
        # EMERGING TECH
        # ═══════════════════════════════════════════════════════════════
        {
            "key": "multimodal_llms",
            "value": "Multimodal LLMs process multiple input types: text, images, audio, video. GPT-4V, Claude 3, and Gemini 1.5 support vision. Use cases include visual QA, document understanding, and image generation. Challenges include alignment and efficient encoding.",
            "tags": ["llm", "multimodal", "vision", "audio"],
            "confidence": 0.92,
            "source": "research"
        },
        {
            "key": "agentic_workflows",
            "value": "Agentic workflows decompose complex tasks into agent-executable steps with feedback loops. Patterns include planning-execution cycles, tool-based problem solving, and self-correction. Requires orchestration, state management, and error recovery.",
            "tags": ["agents", "workflows", "orchestration", "automation"],
            "confidence": 0.90,
            "source": "research"
        },
        {
            "key": "mcp_protocol",
            "value": "Model Context Protocol (MCP) enables LLM applications to discover and use external tools dynamically. Supports server-based tool registries, capability negotiation, and standardized tool schemas. Anthropic's approach to extensible agent systems.",
            "tags": ["protocol", "tools", "agents", "anthropic"],
            "confidence": 0.89,
            "source": "research"
        },
    ]


def get_semantic_memory_data() -> List[Dict[str, Any]]:
    """Get semantic memory (user preferences + knowledge) for seeding."""
    now = datetime.utcnow()

    # User preferences
    preferences = [
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

    # Knowledge base - combine with preferences
    knowledge_base = get_knowledge_base_data()

    # Convert knowledge items to semantic memory format
    knowledge_memories = []
    for i, knowledge in enumerate(knowledge_base):
        knowledge_memories.append({
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "knowledge",
            "key": knowledge["key"],
            "value": knowledge["value"],
            "tags": knowledge.get("tags", []),
            "source": knowledge.get("source", "research"),
            "confidence": knowledge.get("confidence", 0.90),
            "times_accessed": 0,
            "created_at": now - timedelta(days=3),  # Cached 3 days ago
            "updated_at": now - timedelta(days=3),
            "expires_at": now + timedelta(days=7)  # 7-day TTL for knowledge
        })

    return preferences + knowledge_memories


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

    # ==================== GrandLine Integration Actions ====================
    if "GrandLine Integration" in project_lookup:
        p = project_lookup["GrandLine Integration"]
        actions.append({
            "user_id": DEMO_USER_ID,
            "session_id": f"{DEMO_SESSION_PREFIX}-grandline-1",
            "memory_type": "episodic",
            "action_type": "completed_task",
            "entity_type": "task",
            "entity": {
                "task_title": "Submit PR to GrandLine checkpointing",
                "project_name": "GrandLine Integration",
                "priority": "high"
            },
            "metadata": {
                "pr_url": "github.com/belmontchain-ai/grandline/pull/xxx",
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
            # Create comprehensive searchable text including:
            # name, description, context, notes, updates, stakeholders, methods, decisions
            # Enables richer queries like: "infrastructure project" → Project Alpha
            # "what's Mike working on" → projects with Mike as stakeholder
            searchable_text = build_project_embedding_text(project)

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
            # Create comprehensive searchable text including:
            # title, description, context, notes, blockers, assignee, priority
            # Enables richer queries like: "debugging task" → Create debugging methodologies doc
            # "what's blocking Mike's work" → tasks with blockers assigned to Mike
            searchable_text = build_task_embedding_text(task)

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
        deleted = db.memory_procedural.delete_many({
            "user_id": DEMO_USER_ID
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing procedural memories")

    procedures = get_procedural_memory_data()

    # Check for existing procedures
    existing_names = set()
    for proc in db.memory_procedural.find({
        "user_id": DEMO_USER_ID
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

        db.memory_procedural.insert_one(proc)
        print(f"  ✓ Inserted: {proc['name']} ({proc['rule_type']}, used {proc['times_used']}x)")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new procedures, {len(existing_names)} existing")

    return inserted_count


def seed_semantic_memory(db, skip_embeddings: bool = False, clean: bool = False) -> int:
    """Seed semantic memory (user preferences + knowledge base)."""
    print("\n" + "=" * 60)
    print("SEEDING SEMANTIC MEMORY")
    print("=" * 60)

    if clean:
        deleted = db.memory_semantic.delete_many({
            "user_id": DEMO_USER_ID
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing semantic memories")

    all_memories = get_semantic_memory_data()

    # Check for existing keys
    existing_keys = set()
    for mem in db.memory_semantic.find({
        "user_id": DEMO_USER_ID
    }, {"key": 1}):
        existing_keys.add(mem["key"])

    inserted_count = 0
    embedding_count = 0

    for mem in all_memories:
        if mem["key"] in existing_keys:
            print(f"  ⏭️  Skipping existing: {mem['key']}")
            continue

        # Generate embeddings for knowledge items (searchable)
        if mem.get("semantic_type") == "knowledge" and not skip_embeddings:
            try:
                # Embed the knowledge value for semantic search
                mem["embedding"] = embed_document(mem["value"])

                if len(mem["embedding"]) != 1024:
                    print(f"  ⚠️  Warning: Expected 1024 dims, got {len(mem['embedding'])}")

                print(f"  📊 Generated embedding for: {mem['key']} (1024-dim)")
                embedding_count += 1
            except Exception as e:
                print(f"  ⚠️  Failed to generate embedding for {mem['key']}: {e}")
                print(f"      Continuing without embedding")

        db.memory_semantic.insert_one(mem)

        # Display differently based on type
        if mem.get("semantic_type") == "preference":
            times_used = mem.get("times_used", 0)
            print(f"  ✓ Inserted preference: {mem['key']} = {mem['value']} (confidence: {mem['confidence']}, used {times_used}x)")
        else:  # knowledge
            tags = ', '.join(mem.get('tags', [])[:3])
            print(f"  ✓ Inserted knowledge: {mem['key']} ({tags})")

        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new semantic memories ({embedding_count} with embeddings), {len(existing_keys)} existing")

    return inserted_count


def seed_episodic_memory(db, skip_embeddings: bool = False, clean: bool = False) -> int:
    """Seed episodic memory (past actions)."""
    print("\n" + "=" * 60)
    print("SEEDING EPISODIC MEMORY")
    print("=" * 60)

    if clean:
        deleted = db.memory_episodic.delete_many({
            "user_id": DEMO_USER_ID
        })
        print(f"\n🗑️  Cleared {deleted.deleted_count} existing episodic memories")

    # Get current projects for reference
    projects = list(db.projects.find({"user_id": DEMO_USER_ID}))
    actions = get_episodic_memory_data(projects)

    # Check for existing actions by action_type and timestamp (unique combo)
    existing_actions = set()
    for action in db.memory_episodic.find({
        "user_id": DEMO_USER_ID
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

        db.memory_episodic.insert_one(action)
        print(f"  ✓ Inserted: {action['action_type']} - {action['entity'].get('project_name', 'N/A')} ({action['outcome']})")
        inserted_count += 1

    print(f"\n📊 Summary: {inserted_count} new actions, {len(existing_actions)} existing")

    return inserted_count


def seed_episodic_summaries(db) -> int:
    """Generate and store AI-generated episodic summaries for tasks and projects."""
    print("\n" + "=" * 60)
    print("GENERATING EPISODIC SUMMARIES (AI)")
    print("=" * 60)

    from shared.episodic import generate_task_episodic_summary, generate_project_episodic_summary
    from shared.models import Task, Project
    from memory.manager import MemoryManager
    from shared.embeddings import embed_query

    # Initialize memory manager
    try:
        memory_manager = MemoryManager(db=db, embedding_fn=embed_query)
    except Exception as e:
        print(f"⚠️  Could not initialize memory manager: {e}")
        return 0

    # Check if AI-generated summaries already exist for demo user
    # (Documents with 'summary' field are AI-generated, not manual episodic memories)
    existing_count = db.memory_episodic.count_documents({
        "user_id": DEMO_USER_ID,
        "summary": {"$exists": True}
    })
    if existing_count > 0:
        print(f"  ⏭️  Skipping: {existing_count} AI summaries already exist for {DEMO_USER_ID}")
        print(f"     (Use --clean to regenerate)")
        return 0

    summary_count = 0

    # Generate task summaries
    print("\n📋 Generating task summaries...")
    tasks = list(db.tasks.find({"user_id": DEMO_USER_ID}))

    for task_doc in tasks:
        try:
            # Convert to Task model
            task = Task(**task_doc)

            # Only generate if task has activity (in real usage, this is auto-generated)
            # For demo, we'll create synthetic activity logs
            if not task_doc.get("activity_log"):
                # Add synthetic activity log entry
                from datetime import datetime
                activity_entry = {
                    "timestamp": task_doc.get("created_at", datetime.utcnow()),
                    "action": "created",
                    "note": f"Task created for {task_doc.get('project', 'demo')}"
                }
                db.tasks.update_one(
                    {"_id": task_doc["_id"]},
                    {"$push": {"activity_log": activity_entry}}
                )
                # Reload task
                task_doc = db.tasks.find_one({"_id": task_doc["_id"]})
                task = Task(**task_doc)

            # Generate summary
            summary = generate_task_episodic_summary(task)

            # Store in memory_episodic
            memory_manager.store_episodic_summary(
                user_id=DEMO_USER_ID,
                entity_type="task",
                entity_id=task.id,
                summary=summary,
                activity_count=len(task.activity_log),
                entity_title=task.title,
                entity_status=task.status
            )

            print(f"  ✓ Generated summary for: {task.title}")
            summary_count += 1

        except Exception as e:
            print(f"  ⚠️  Failed to generate summary for task {task_doc.get('title', 'unknown')}: {e}")
            continue

    # Generate project summaries
    print("\n📁 Generating project summaries...")
    projects = list(db.projects.find({"user_id": DEMO_USER_ID}))

    for project_doc in projects:
        try:
            # Convert to Project model
            project = Project(**project_doc)

            # Get tasks for this project
            project_tasks = []
            task_docs = db.tasks.find({"project_id": project.id, "user_id": DEMO_USER_ID})
            for task_doc in task_docs:
                project_tasks.append(Task(**task_doc))

            # Generate summary
            summary = generate_project_episodic_summary(project, project_tasks)

            # Store in memory_episodic
            memory_manager.store_episodic_summary(
                user_id=DEMO_USER_ID,
                entity_type="project",
                entity_id=project.id,
                summary=summary,
                activity_count=len(project.activity_log) if project.activity_log else 0,
                entity_title=project.name,
                entity_status=project.status
            )

            print(f"  ✓ Generated summary for: {project.name}")
            summary_count += 1

        except Exception as e:
            print(f"  ⚠️  Failed to generate summary for project {project_doc.get('name', 'unknown')}: {e}")
            continue

    print(f"\n📊 Summary: {summary_count} episodic summaries generated")

    return summary_count


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
            "memory_episodic",
            "memory_semantic",
            "memory_procedural",
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
    results["counts"]["procedural"] = db.memory_procedural.count_documents({
        "user_id": DEMO_USER_ID
    })
    results["counts"]["semantic"] = db.memory_semantic.count_documents({
        "user_id": DEMO_USER_ID
    })
    results["counts"]["episodic"] = db.memory_episodic.count_documents({
        "user_id": DEMO_USER_ID
    })

    # Check critical items for expanded demo data
    gtm_template = db.memory_procedural.find_one({
        "user_id": DEMO_USER_ID,
        "rule_type": "template",
        "name": "GTM Roadmap Template"
    })
    results["critical_items"]["gtm_template"] = gtm_template is not None
    if not gtm_template:
        results["missing"].append("GTM Roadmap Template")
        results["success"] = False

    ref_arch_template = db.memory_procedural.find_one({
        "user_id": DEMO_USER_ID,
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

    user_preferences = db.memory_semantic.count_documents({
        "user_id": DEMO_USER_ID,
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
        for proc in db.memory_procedural.find({
            "user_id": DEMO_USER_ID
        }, {"name": 1, "rule_type": 1}):
            print(f"    • {proc.get('name', 'N/A')} ({proc.get('rule_type', 'unknown')})")

    # Print semantic memory
    print(f"\n🧠 Semantic Memory: {results['counts']['semantic']}")
    if results['counts']['semantic'] == 0:
        print("  ❌ No semantic memories found")
    else:
        for sem in db.memory_semantic.find({
            "user_id": DEMO_USER_ID
        }, {"key": 1, "value": 1}):
            print(f"    • {sem.get('key', 'N/A')} = {sem.get('value', 'N/A')}")

    # Print episodic memory
    print(f"\n📚 Episodic Memory: {results['counts']['episodic']}")
    if results['counts']['episodic'] == 0:
        print("  ❌ No episodic memories found")
    else:
        for epi in db.memory_episodic.find({
            "user_id": DEMO_USER_ID
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
    results["semantic"] = seed_semantic_memory(db, skip_embeddings=skip_embeddings, clean=False)
    results["episodic"] = seed_episodic_memory(db, skip_embeddings=skip_embeddings, clean=False)

    # Generate AI episodic summaries (for demo app sidebar)
    results["episodic_summaries"] = seed_episodic_summaries(db)

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
        # Count embeddings in episodic and semantic memory
        episodic_embeddings = db.memory_episodic.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        semantic_embeddings = db.memory_semantic.count_documents({
            "user_id": DEMO_USER_ID,
            "embedding": {"$exists": True}
        })
        memory_embeddings = episodic_embeddings + semantic_embeddings
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
        print(f"  Episodic summaries generated: {results['episodic_summaries']}")
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
