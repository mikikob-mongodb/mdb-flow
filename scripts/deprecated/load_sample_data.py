"""
Sample Data Loader for Flow Companion

Loads 10 realistic projects with 2-6 tasks each into MongoDB with embeddings.
Perfect for testing and demonstrating the Flow Companion features.

Usage:
    # Load with embeddings (recommended)
    python scripts/load_sample_data.py

    # Skip embeddings for faster loading (semantic search won't work)
    python scripts/load_sample_data.py --skip-embeddings

Requires:
    - .env file with MONGODB_URI, MONGODB_DATABASE, VOYAGE_API_KEY
    - Virtual environment activated with dependencies installed
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_db
from shared.embeddings import embed_document
from bson import ObjectId


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def random_past_date(days_ago_max: int = 30, days_ago_min: int = 0) -> datetime:
    """Generate a random datetime in the past."""
    days = random.randint(days_ago_min, days_ago_max)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return datetime.utcnow() - timedelta(days=days, hours=hours, minutes=minutes)


def create_activity_log(action: str, note: str = None, timestamp: datetime = None) -> dict:
    """Create an activity log entry."""
    return {
        "timestamp": timestamp or datetime.utcnow(),
        "action": action,
        "note": note
    }


def generate_embedding_text(item: dict, item_type: str) -> str:
    """Generate text to embed for a task or project."""
    if item_type == "project":
        parts = [
            item["name"],
            item.get("description", ""),
            item.get("context", ""),
            " ".join(item.get("notes", [])),
            " ".join(item.get("methods", [])),
            " ".join(item.get("decisions", []))
        ]
    else:  # task
        parts = [
            item["title"],
            item.get("context", ""),
            " ".join(item.get("notes", []))
        ]
    return " ".join(filter(None, parts))


# =============================================================================
# SAMPLE DATA DEFINITION
# =============================================================================

PROJECTS_DATA = [
    {
        "name": "AgentOps Framework",
        "description": "Establish AgentOps as a discipline with observability, debugging, and reliability frameworks for agent systems",
        "status": "active",
        "context": "Developers struggle with debugging agent failures and ensuring production reliability. No established operational frameworks exist yet.",
        "notes": [
            "Three pillars: observability, debugging, reliability",
            "Target audience: developers moving from prototypes to production",
            "Builds on Memory Engineering foundation"
        ],
        "methods": ["OpenTelemetry", "Grafana", "Docker Compose", "MongoDB Change Streams"],
        "decisions": [
            "Focus on practical starter kits over theoretical frameworks",
            "Open source all templates and dashboards",
            "Partner with observability tool vendors"
        ],
        "tasks": [
            {
                "title": "Write 'What Is AgentOps?' article",
                "status": "done",
                "priority": "high",
                "context": "Establishes AgentOps as a discipline, foundational thought leadership",
                "notes": [
                    "Framed around three pillars: observability, debugging, reliability",
                    "Used popular observability tools as reference points",
                    "Manager reviewed draft - suggested more MongoDB-specific examples",
                    "Published on MongoDB Developer Center"
                ]
            },
            {
                "title": "Create debugging methodologies doc",
                "status": "in_progress",
                "priority": "high",
                "context": "Document patterns for debugging agent failures in production",
                "notes": [
                    "Start with trace aggregation patterns",
                    "Need to cover: token tracking, latency analysis, failure classification",
                    "Interview platform team about common customer issues"
                ]
            },
            {
                "title": "Build AgentOps Starter Kit",
                "status": "in_progress",
                "priority": "high",
                "context": "Monitoring templates, observability setup for agent systems",
                "notes": [
                    "Using OpenTelemetry for instrumentation",
                    "Include Grafana dashboard templates",
                    "Docker compose for local setup"
                ]
            },
            {
                "title": "Design evaluation framework",
                "status": "todo",
                "priority": "medium",
                "context": "Testing patterns for multi-agent system reliability",
                "notes": [
                    "Research existing eval frameworks, custom metrics",
                    "Need both offline and online evaluation patterns"
                ]
            },
            {
                "title": "Record AgentOps webinar",
                "status": "todo",
                "priority": "medium",
                "context": "Monthly technical webinar on operational patterns",
                "notes": [
                    "Target late February",
                    "Demo the starter kit live",
                    "Coordinate with DevRel on promotion"
                ]
            }
        ]
    },
    {
        "name": "Memory Engineering Content",
        "description": "Scale Memory Engineering concepts into operational frameworks developers can implement",
        "status": "active",
        "context": "Memory Engineering article established concepts; developers need operational implementation guidance",
        "notes": [
            "Foundation article performed well with strong engagement",
            "Need to translate theory into practical guides",
            "Focus on debugging and scaling patterns"
        ],
        "methods": ["MongoDB Atlas Vector Search", "TTL Indexes", "Aggregation Pipelines"],
        "decisions": [
            "Extend thought leadership into practical frameworks",
            "Create debugging-first documentation",
            "Benchmark all recommendations"
        ],
        "tasks": [
            {
                "title": "Publish 'Why Multi-Agent Systems Need Memory'",
                "status": "done",
                "priority": "high",
                "context": "Strong engagement, recognized as foundational work",
                "notes": [
                    "Took 3 weeks to write",
                    "Key insight: memory as coordination mechanism, not just storage",
                    "Received 'foundational work' comment from framework engineer",
                    "Shared widely on social media"
                ]
            },
            {
                "title": "Write scaling guidance doc",
                "status": "in_progress",
                "priority": "medium",
                "context": "Performance patterns for production memory systems",
                "notes": [
                    "Cover: sharding strategies, TTL indexes, read/write patterns",
                    "Include benchmarks from large document collections",
                    "Need to test Atlas Search performance at scale"
                ]
            },
            {
                "title": "Create memory failure debugging guide",
                "status": "todo",
                "priority": "high",
                "context": "Operational implementation guidance from the article concepts",
                "notes": [
                    "Common failures: context window overflow, stale memory retrieval, embedding drift",
                    "Include MongoDB-specific solutions"
                ]
            },
            {
                "title": "Update Text-to-MQL reference architecture",
                "status": "done",
                "priority": "medium",
                "context": "Integrated into Gen-AI Showcase",
                "notes": [
                    "Added vector search examples",
                    "Improved error handling based on customer feedback",
                    "Now supports aggregation pipelines"
                ]
            }
        ]
    },
    {
        "name": "LangGraph Integration",
        "description": "Deep integration of MongoDB into LangGraph framework through code contributions",
        "status": "active",
        "context": "MongoDB partnerships should be code-level, not just marketing. Developers need MongoDB deeply integrated into LangGraph workflows.",
        "notes": [
            "Focus on checkpointer implementation",
            "Must pass their test suite",
            "Joint documentation effort"
        ],
        "methods": ["Motor async driver", "LangGraph Checkpointer API", "pytest"],
        "decisions": [
            "Contribute code directly to framework repo",
            "Follow their coding standards exactly",
            "Create migration path from default storage"
        ],
        "tasks": [
            {
                "title": "Implement MongoDB checkpointer for LangGraph",
                "status": "in_progress",
                "priority": "high",
                "context": "Code contribution to core framework, not just marketing",
                "notes": [
                    "Based on existing checkpointer interface",
                    "Using Motor for async support",
                    "Need to handle serialization of complex state objects",
                    "Framework team engineer reviewing approach"
                ]
            },
            {
                "title": "Write checkpointer documentation",
                "status": "todo",
                "priority": "medium",
                "context": "Joint technical docs with LangGraph team",
                "notes": [
                    "Follow LangGraph docs style guide",
                    "Include migration guide from default storage"
                ]
            },
            {
                "title": "Create LangGraph + MongoDB tutorial",
                "status": "todo",
                "priority": "medium",
                "context": "Hands-on implementation guide for developers",
                "notes": [
                    "Build a simple multi-agent workflow",
                    "Show checkpoint recovery after failure",
                    "Deploy to Atlas"
                ]
            },
            {
                "title": "Submit PR to LangGraph repo",
                "status": "todo",
                "priority": "high",
                "context": "Get MongoDB persistence merged into official repo",
                "notes": [
                    "Target: official LangGraph repo",
                    "Need to add tests matching their coverage requirements"
                ]
            }
        ]
    },
    {
        "name": "Voice Agent Architecture",
        "description": "Reference architecture for real-time voice agents with low-latency requirements",
        "status": "active",
        "context": "Q2 FY26 theme: Voice & Multimodal AI. Real-time audio requires different architectural patterns.",
        "notes": [
            "Target sub-500ms end-to-end latency",
            "WebSocket-based streaming architecture",
            "MongoDB for conversation state persistence"
        ],
        "methods": ["WebRTC", "FastAPI", "WebSockets", "React Web Audio API", "MongoDB Change Streams"],
        "decisions": [
            "Use streaming STT for lowest latency",
            "MongoDB for state, not audio buffers",
            "Build interruption handling into core architecture"
        ],
        "tasks": [
            {
                "title": "Design real-time audio pipeline",
                "status": "done",
                "priority": "high",
                "context": "Low-latency architecture for voice agents",
                "notes": [
                    "Using WebRTC for audio capture",
                    "Evaluated multiple STT providers - chose fastest for real-time",
                    "Target <500ms end-to-end latency",
                    "MongoDB for conversation state and audio metadata"
                ]
            },
            {
                "title": "Build voice agent reference app",
                "status": "in_progress",
                "priority": "high",
                "context": "Q2 FY26 theme: Voice & Multimodal AI",
                "notes": [
                    "FastAPI backend with WebSocket support",
                    "React frontend with Web Audio API",
                    "Integrate with Claude for responses",
                    "Need to solve interruption handling"
                ]
            },
            {
                "title": "Document WebSocket streaming patterns",
                "status": "in_progress",
                "priority": "medium",
                "context": "Real-time state management with MongoDB",
                "notes": [
                    "Change streams for real-time sync",
                    "Optimistic UI updates pattern",
                    "Handle reconnection gracefully"
                ]
            },
            {
                "title": "Create multimodal demo",
                "status": "todo",
                "priority": "medium",
                "context": "Extends voice work into multimodal",
                "notes": [
                    "Add image understanding to voice agent",
                    "Use case: describe what you're looking at",
                    "Claude vision API integration"
                ]
            },
            {
                "title": "Write voice agent blog post",
                "status": "todo",
                "priority": "low",
                "context": "Technical tutorial on the architecture",
                "notes": [
                    "Focus on latency optimization techniques",
                    "Include architecture diagram"
                ]
            }
        ]
    },
    {
        "name": "Gaming NPC Demo",
        "description": "Domain-specific hero demo showing NPCs with persistent memory across gaming sessions",
        "status": "active",
        "context": "Generic AI demos don't differentiate. Gaming vertical shows MongoDB's versatility with complex memory patterns.",
        "notes": [
            "NPCs remember player interactions",
            "World state persists across sessions",
            "Relationship system between NPCs and players"
        ],
        "methods": ["LangGraph", "MongoDB Geospatial", "Event Sourcing", "Embeddings"],
        "decisions": [
            "Separate short-term and long-term NPC memory",
            "Use embeddings for semantic recall of past interactions",
            "Implement gossip system for NPC-to-NPC info sharing"
        ],
        "tasks": [
            {
                "title": "Design NPC memory schema",
                "status": "done",
                "priority": "high",
                "context": "Document model for persistent NPC state",
                "notes": [
                    "Separate collections: npc_profiles, interactions, world_state",
                    "Embedding on interaction summaries for semantic recall",
                    "TTL on short-term memory, permanent long-term"
                ]
            },
            {
                "title": "Build NPC conversation system",
                "status": "in_progress",
                "priority": "high",
                "context": "NPCs remember player interactions across sessions",
                "notes": [
                    "Using LangGraph for conversation flow",
                    "Retrieval: recent interactions + semantically similar past events",
                    "Personality affects response style"
                ]
            },
            {
                "title": "Implement world-state management",
                "status": "todo",
                "priority": "high",
                "context": "Game world persistence patterns",
                "notes": [
                    "Time-series data for world events",
                    "Geospatial indexing for location-based queries",
                    "Event sourcing pattern for history"
                ]
            },
            {
                "title": "Create player relationship tracking",
                "status": "todo",
                "priority": "medium",
                "context": "NPCs form opinions based on player actions",
                "notes": [
                    "Sentiment scoring on interactions",
                    "Relationship graph between NPCs and players",
                    "Gossip system - NPCs share info about players"
                ]
            },
            {
                "title": "Deploy demo to GitHub",
                "status": "todo",
                "priority": "medium",
                "context": "Full source code and deployment guide",
                "notes": [
                    "Docker compose setup",
                    "Atlas free tier compatible",
                    "Include sample NPC data"
                ]
            },
            {
                "title": "Record gaming demo walkthrough",
                "status": "todo",
                "priority": "low",
                "context": "Video content for developer reach",
                "notes": [
                    "5-minute demo video",
                    "Show memory in action across sessions",
                    "Post on YouTube and Twitter"
                ]
            }
        ]
    },
    {
        "name": "AWS re:Invent Prep",
        "description": "Preparation for AWS re:Invent conference session on Engineering Agent Memory",
        "status": "active",
        "context": "Major conference opportunity to establish thought leadership on agent memory architecture",
        "notes": [
            "45-minute breakout session",
            "Large room capacity",
            "Live demo required"
        ],
        "methods": ["Keynote/Slides", "Live Demo", "Flow Companion"],
        "decisions": [
            "Lead with customer pain points",
            "Build demo with offline fallback",
            "Keep slides under 30"
        ],
        "tasks": [
            {
                "title": "Submit session proposal",
                "status": "done",
                "priority": "high",
                "context": "Agent memory deep-dive session",
                "notes": [
                    "Title: Engineering Agent Memory",
                    "Accepted as breakout session",
                    "45 minutes including Q&A",
                    "Large room assigned"
                ]
            },
            {
                "title": "Create presentation slides",
                "status": "in_progress",
                "priority": "high",
                "context": "Engineering Agent Memory talk",
                "notes": [
                    "Structure: Problem → Patterns → Demo → MongoDB specifics",
                    "Manager suggested leading with customer pain points",
                    "Include customer examples (anonymized)",
                    "Max 30 slides"
                ]
            },
            {
                "title": "Build live demo",
                "status": "in_progress",
                "priority": "high",
                "context": "Flow Companion ambient assistant demo",
                "notes": [
                    "Must work on conference WiFi",
                    "Fallback: pre-recorded video",
                    "Show: capture → memory → retrieval → response",
                    "Practice offline mode"
                ]
            },
            {
                "title": "Practice run-through",
                "status": "todo",
                "priority": "high",
                "context": "Manager suggested doing dry run with team",
                "notes": [
                    "Schedule for next week",
                    "Invite: manager, DevRel team, PMM",
                    "Record for self-review",
                    "Target: 40 minutes with buffer"
                ]
            }
        ]
    },
    {
        "name": "CrewAI Memory Patterns",
        "description": "MongoDB memory backend contribution for CrewAI framework",
        "status": "active",
        "context": "CrewAI has good memory abstractions but no persistence layer. Opportunity for code contribution.",
        "notes": [
            "They have short-term, long-term, entity memory concepts",
            "Current implementation is in-memory only",
            "Good relationship with their team"
        ],
        "methods": ["CrewAI Memory API", "MongoDB TTL Indexes", "Serialization"],
        "decisions": [
            "Map their memory types directly to collections",
            "Handle crew state serialization carefully",
            "Follow their contribution guidelines exactly"
        ],
        "tasks": [
            {
                "title": "Research CrewAI memory architecture",
                "status": "done",
                "priority": "medium",
                "context": "Understand current implementation gaps",
                "notes": [
                    "Current: in-memory only, lost on restart",
                    "They have short-term, long-term, entity memory concepts",
                    "Good abstraction but no persistence layer",
                    "Talked to their team lead"
                ]
            },
            {
                "title": "Design MongoDB memory backend",
                "status": "in_progress",
                "priority": "medium",
                "context": "Persistent crew memory across runs",
                "notes": [
                    "Map their memory types to collections",
                    "Short-term: TTL index, Long-term: permanent",
                    "Entity memory: separate collection with relationships",
                    "Need to handle crew serialization"
                ]
            },
            {
                "title": "Submit contribution PR",
                "status": "todo",
                "priority": "high",
                "context": "Code contribution to CrewAI framework",
                "notes": [
                    "Follow their contribution guidelines",
                    "Add integration tests",
                    "Document in their memory section"
                ]
            }
        ]
    },
    {
        "name": "Education Adaptive Tutoring Demo",
        "description": "Domain-specific demo showing adaptive learning system with persistent learner models",
        "status": "active",
        "context": "Q3 domain applications theme. Education vertical demonstrates memory-driven personalization.",
        "notes": [
            "Track student knowledge state over time",
            "Adaptive difficulty based on mastery",
            "Spaced repetition for retention"
        ],
        "methods": ["Bayesian Knowledge Tracing", "Item Response Theory", "MongoDB Aggregation"],
        "decisions": [
            "Base learner model on established learning science",
            "Support multiple students per instance",
            "Focus on math domain for demo"
        ],
        "tasks": [
            {
                "title": "Design learner model schema",
                "status": "done",
                "priority": "medium",
                "context": "Track student knowledge state over time",
                "notes": [
                    "Knowledge components with mastery scores",
                    "Interaction history with timestamps",
                    "Misconception tracking",
                    "Based on learning science literature"
                ]
            },
            {
                "title": "Build adaptive question system",
                "status": "todo",
                "priority": "high",
                "context": "Adjusts difficulty based on memory",
                "notes": [
                    "Item Response Theory for difficulty calibration",
                    "Spaced repetition for review scheduling",
                    "MongoDB aggregation for next-best-question selection"
                ]
            },
            {
                "title": "Implement progress persistence",
                "status": "todo",
                "priority": "medium",
                "context": "Student can resume across sessions",
                "notes": [
                    "Session state in memory_short_term",
                    "Learning progress in memory_long_term",
                    "Support multiple students per tutor instance"
                ]
            },
            {
                "title": "Create demo video",
                "status": "todo",
                "priority": "low",
                "context": "Q3 domain applications theme",
                "notes": [
                    "Show learning progression over time",
                    "Highlight memory-driven personalization",
                    "Before/after comparison"
                ]
            }
        ]
    },
    {
        "name": "Q4 FY25 Deliverables",
        "description": "Completed work from Q4 FY25 that established foundation for FY26",
        "status": "archived",
        "context": "Archive of completed Q4 work. These deliverables validated the approach for FY26.",
        "notes": [
            "All items completed successfully",
            "Formed basis for FY26 priorities",
            "Strong customer and partner feedback"
        ],
        "methods": ["MongoDB Vector Search", "LangChain", "Gen-AI Showcase"],
        "decisions": [
            "Archive but keep for reference",
            "Use as foundation for new work",
            "Cite in future content"
        ],
        "tasks": [
            {
                "title": "Agent Memory demo",
                "status": "done",
                "priority": "high",
                "context": "Completed for Q4 theme",
                "notes": [
                    "Demonstrated at team all-hands",
                    "Well received - became basis for Flow Companion",
                    "Code in gen-ai-showcase repo"
                ]
            },
            {
                "title": "Advanced Text-to-MQL",
                "status": "done",
                "priority": "high",
                "context": "Integrated into Gen-AI Showcase",
                "notes": [
                    "Handles complex aggregations now",
                    "Added validation layer for generated queries",
                    "Used by several SAs for customer demos"
                ]
            },
            {
                "title": "AgentOps foundations article",
                "status": "done",
                "priority": "high",
                "context": "Published successfully",
                "notes": [
                    "Outlined the three pillars",
                    "Set up FY26 AgentOps work",
                    "Good SEO performance"
                ]
            },
            {
                "title": "Partner sync with LangChain team",
                "status": "done",
                "priority": "medium",
                "context": "Established relationship for FY26",
                "notes": [
                    "Met the team at their office",
                    "Agreed on checkpointer contribution",
                    "Quarterly syncs scheduled",
                    "They'll promote our content"
                ]
            }
        ]
    },
    {
        "name": "Developer Webinar Series",
        "description": "Monthly technical webinars for developer engagement and top-of-funnel reach",
        "status": "active",
        "context": "Direct developer interaction through webinars reaches developers early in evaluation journey",
        "notes": [
            "Monthly cadence",
            "Mix of conceptual and hands-on content",
            "All recordings archived on YouTube"
        ],
        "methods": ["Zoom Webinar", "MongoDB Charts", "YouTube"],
        "decisions": [
            "Target consistent monthly schedule",
            "Include live demos in every session",
            "Track metrics for continuous improvement"
        ],
        "tasks": [
            {
                "title": "January webinar: Agent Memory Basics",
                "status": "done",
                "priority": "medium",
                "context": "Monthly technical webinar",
                "notes": [
                    "Good registration and attendance",
                    "Strong Q&A engagement",
                    "Recording posted to YouTube",
                    "Follow-up questions about vector search performance"
                ]
            },
            {
                "title": "February webinar: RAG Evolution",
                "status": "in_progress",
                "priority": "medium",
                "context": "Prep slides and demo",
                "notes": [
                    "Cover: naive RAG → advanced RAG → agentic RAG",
                    "Demo: show retrieval quality improvements",
                    "Guest speaker from AI company interested"
                ]
            },
            {
                "title": "Create webinar landing page",
                "status": "done",
                "priority": "low",
                "context": "Registration and recordings",
                "notes": [
                    "Using MongoDB.com/developer events",
                    "All recordings archived",
                    "Added to developer newsletter"
                ]
            },
            {
                "title": "March webinar: AgentOps Intro",
                "status": "todo",
                "priority": "medium",
                "context": "Ties into AgentOps framework launch",
                "notes": [
                    "Coordinate with AgentOps article publish date",
                    "Demo the starter kit",
                    "Set aggressive registration target"
                ]
            },
            {
                "title": "Analyze attendance metrics",
                "status": "todo",
                "priority": "low",
                "context": "Track developer reach success metrics",
                "notes": [
                    "Build dashboard in Charts",
                    "Track: registration, attendance, watch time, follow-up actions",
                    "Report to manager monthly"
                ]
            }
        ]
    }
]


# =============================================================================
# LOADER FUNCTION
# =============================================================================

def load_sample_data(skip_embeddings: bool = False):
    """Load all sample data into MongoDB."""

    db = get_db()

    # Clear existing data
    print("Clearing existing data...")
    db.projects.delete_many({})
    db.tasks.delete_many({})
    db.settings.delete_many({})

    # Create default settings
    print("Creating default settings...")
    db.settings.insert_one({
        "user_id": "default",
        "current_task_id": None,
        "current_project_id": None,
        "context_set_at": None,
        "default_project_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    project_count = 0
    task_count = 0

    for project_data in PROJECTS_DATA:
        print(f"\nCreating project: {project_data['name']}")

        # Generate project dates
        project_created = random_past_date(days_ago_max=60, days_ago_min=14)

        # Build project activity log
        project_activity_log = [
            create_activity_log("created", None, project_created)
        ]

        if project_data.get("decisions"):
            for i, decision in enumerate(project_data["decisions"]):
                decision_date = project_created + timedelta(days=random.randint(1, 7), hours=random.randint(1, 12))
                project_activity_log.append(
                    create_activity_log("decision_added", decision, decision_date)
                )

        # Generate project embedding
        project_embedding = None
        if not skip_embeddings:
            try:
                embed_text_content = generate_embedding_text(project_data, "project")
                project_embedding = embed_document(embed_text_content)
                print(f"  ✓ Generated project embedding")
            except Exception as e:
                print(f"  ✗ Failed to generate project embedding: {e}")

        # Insert project
        project_doc = {
            "name": project_data["name"],
            "description": project_data["description"],
            "status": project_data["status"],
            "context": project_data["context"],
            "notes": project_data["notes"],
            "methods": project_data["methods"],
            "decisions": project_data["decisions"],
            "activity_log": project_activity_log,
            "created_at": project_created,
            "updated_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "embedding": project_embedding
        }

        project_result = db.projects.insert_one(project_doc)
        project_id = project_result.inserted_id
        project_count += 1

        # Create tasks for this project
        for task_data in project_data["tasks"]:
            print(f"  Creating task: {task_data['title'][:50]}...")

            # Generate task dates based on status
            task_created = project_created + timedelta(days=random.randint(0, 14), hours=random.randint(1, 23))

            started_at = None
            completed_at = None
            last_worked_on = task_created

            task_activity_log = [
                create_activity_log("created", None, task_created)
            ]

            if task_data["status"] in ["in_progress", "done"]:
                started_at = task_created + timedelta(days=random.randint(0, 3), hours=random.randint(1, 12))
                task_activity_log.append(
                    create_activity_log("started", "Beginning work", started_at)
                )
                last_worked_on = started_at + timedelta(hours=random.randint(1, 48))
                task_activity_log.append(
                    create_activity_log("updated", "Making progress", last_worked_on)
                )

            if task_data["status"] == "done":
                completed_at = last_worked_on + timedelta(hours=random.randint(1, 24))
                last_worked_on = completed_at
                task_activity_log.append(
                    create_activity_log("completed", "Task finished", completed_at)
                )

            # Add notes to activity log
            for note in task_data.get("notes", [])[:2]:  # First 2 notes
                note_date = task_created + timedelta(days=random.randint(0, 7), hours=random.randint(1, 23))
                task_activity_log.append(
                    create_activity_log("note_added", note[:100], note_date)
                )

            # Sort activity log by timestamp
            task_activity_log.sort(key=lambda x: x["timestamp"])

            # Generate task embedding
            task_embedding = None
            if not skip_embeddings:
                try:
                    embed_text_content = generate_embedding_text(task_data, "task")
                    task_embedding = embed_document(embed_text_content)
                    print(f"    ✓ Generated task embedding")
                except Exception as e:
                    print(f"    ✗ Failed to generate task embedding: {e}")

            # Insert task
            task_doc = {
                "title": task_data["title"],
                "status": task_data["status"],
                "priority": task_data.get("priority"),
                "project_id": project_id,
                "context": task_data.get("context"),
                "notes": task_data.get("notes", []),
                "activity_log": task_activity_log,
                "created_at": task_created,
                "updated_at": datetime.utcnow(),
                "started_at": started_at,
                "completed_at": completed_at,
                "last_worked_on": last_worked_on,
                "embedding": task_embedding
            }

            db.tasks.insert_one(task_doc)
            task_count += 1

    print(f"\n{'='*60}")
    print(f"✓ DONE!")
    print(f"  Created {project_count} projects and {task_count} tasks")
    print(f"{'='*60}")

    # Print summary
    print("\n📊 Project Summary:")
    for project in db.projects.find({}, {"name": 1, "status": 1}).sort("created_at", -1):
        task_counts = {
            "todo": db.tasks.count_documents({"project_id": project["_id"], "status": "todo"}),
            "in_progress": db.tasks.count_documents({"project_id": project["_id"], "status": "in_progress"}),
            "done": db.tasks.count_documents({"project_id": project["_id"], "status": "done"})
        }
        status_indicator = "📦" if project['status'] == "archived" else "📁"
        print(f"  {status_indicator} {project['name']}: {task_counts['done']}✓ {task_counts['in_progress']}◐ {task_counts['todo']}○")

    print("\n✅ Sample data loaded successfully!")
    print("   You can now run the app: streamlit run ui/streamlit_app.py\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load sample data into Flow Companion")
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Skip generating embeddings (faster, but semantic search won't work)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("Flow Companion - Sample Data Loader")
    print("="*60 + "\n")

    if args.skip_embeddings:
        print("⚠️  Skipping embeddings (semantic search will not work)\n")

    try:
        load_sample_data(skip_embeddings=args.skip_embeddings)
    except Exception as e:
        print(f"\n❌ Error loading sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
