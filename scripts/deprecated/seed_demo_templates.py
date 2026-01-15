"""
Seed demo templates for multi-memory showcase.

Adds:
- PRD Template (Problem → Requirements → Spec → Metrics)
- Roadmap Template (Discovery → Design → Build → Launch)
- Market Research Template (Analysis → Strategy → Planning)
"""

from shared.db import get_db
from shared.embeddings import embed_query
from datetime import datetime

DEMO_USER_ID = "demo-user"


def get_templates():
    """Define templates with task generation structure."""
    now = datetime.now()

    return [
        # PRD Template
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "template",
            "name": "PRD Template",
            "description": "Product Requirements Document template with problem definition, requirements gathering, technical specifications, and success metrics",
            "trigger": "prd|product requirements|requirements document",
            "phases": [
                {
                    "name": "Problem Definition",
                    "description": "Define the problem and opportunity",
                    "tasks": [
                        {
                            "title": "Problem Statement",
                            "description": "Define the core problem we're solving"
                        },
                        {
                            "title": "User Research",
                            "description": "Research target users and their needs"
                        },
                        {
                            "title": "Market Analysis",
                            "description": "Analyze market opportunity and competition"
                        }
                    ]
                },
                {
                    "name": "Requirements",
                    "description": "Document functional and non-functional requirements",
                    "tasks": [
                        {
                            "title": "Functional Requirements",
                            "description": "List all functional requirements"
                        },
                        {
                            "title": "Non-Functional Requirements",
                            "description": "Performance, security, scalability requirements"
                        },
                        {
                            "title": "User Stories",
                            "description": "Write user stories and acceptance criteria"
                        }
                    ]
                },
                {
                    "name": "Technical Specification",
                    "description": "Technical architecture and implementation details",
                    "tasks": [
                        {
                            "title": "System Architecture",
                            "description": "Design overall system architecture"
                        },
                        {
                            "title": "API Design",
                            "description": "Design APIs and data models"
                        },
                        {
                            "title": "Technology Stack",
                            "description": "Select technologies and frameworks"
                        }
                    ]
                },
                {
                    "name": "Success Metrics",
                    "description": "Define how we'll measure success",
                    "tasks": [
                        {
                            "title": "KPIs",
                            "description": "Define key performance indicators"
                        },
                        {
                            "title": "Measurement Plan",
                            "description": "How we'll track and report metrics"
                        }
                    ]
                }
            ],
            "usage_notes": "Use this template for new product features or projects requiring detailed planning",
            "times_used": 0,
            "created_at": now,
            "updated_at": now
        },

        # Roadmap Template
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "template",
            "name": "Roadmap Template",
            "description": "Product/Project roadmap template with discovery, design, build, and launch phases",
            "trigger": "roadmap|project plan|release plan",
            "phases": [
                {
                    "name": "Discovery",
                    "description": "Research and validation phase",
                    "tasks": [
                        {
                            "title": "User Research",
                            "description": "Conduct user interviews and surveys"
                        },
                        {
                            "title": "Competitive Analysis",
                            "description": "Research competitors and alternatives"
                        },
                        {
                            "title": "Technical Feasibility",
                            "description": "Assess technical feasibility and risks"
                        }
                    ]
                },
                {
                    "name": "Design",
                    "description": "Design solution and plan implementation",
                    "tasks": [
                        {
                            "title": "Solution Design",
                            "description": "Design the solution architecture"
                        },
                        {
                            "title": "Wireframes & Mockups",
                            "description": "Create UI/UX designs"
                        },
                        {
                            "title": "Technical Design Doc",
                            "description": "Write detailed technical design"
                        }
                    ]
                },
                {
                    "name": "Build",
                    "description": "Implementation and testing",
                    "tasks": [
                        {
                            "title": "MVP Implementation",
                            "description": "Build minimum viable product"
                        },
                        {
                            "title": "Testing & QA",
                            "description": "Test functionality and fix bugs"
                        },
                        {
                            "title": "Documentation",
                            "description": "Write user and technical documentation"
                        }
                    ]
                },
                {
                    "name": "Launch",
                    "description": "Release and measure results",
                    "tasks": [
                        {
                            "title": "Beta Testing",
                            "description": "Run beta program with select users"
                        },
                        {
                            "title": "Production Deployment",
                            "description": "Deploy to production"
                        },
                        {
                            "title": "Monitor & Iterate",
                            "description": "Track metrics and iterate based on feedback"
                        }
                    ]
                }
            ],
            "usage_notes": "Use this template for feature rollouts or project execution",
            "times_used": 0,
            "created_at": now,
            "updated_at": now
        },

        # Market Research Template (already exists as "Market Research Questions" checklist)
        # Let's add a proper template version
        {
            "user_id": DEMO_USER_ID,
            "rule_type": "template",
            "name": "Market Research Template",
            "description": "Market research template for competitive analysis, user needs assessment, and go-to-market planning",
            "trigger": "market research|competitive analysis|market analysis",
            "phases": [
                {
                    "name": "Competitive Analysis",
                    "description": "Analyze market and competitors",
                    "tasks": [
                        {
                            "title": "Identify Competitors",
                            "description": "List direct and indirect competitors"
                        },
                        {
                            "title": "Feature Comparison",
                            "description": "Compare features and positioning"
                        },
                        {
                            "title": "Market Sizing",
                            "description": "Estimate total addressable market"
                        }
                    ]
                },
                {
                    "name": "User Needs Assessment",
                    "description": "Understand target users",
                    "tasks": [
                        {
                            "title": "User Personas",
                            "description": "Define target user personas"
                        },
                        {
                            "title": "Pain Points",
                            "description": "Document user pain points and needs"
                        },
                        {
                            "title": "User Interviews",
                            "description": "Conduct interviews with potential users"
                        }
                    ]
                },
                {
                    "name": "Opportunity Analysis",
                    "description": "Identify market opportunities",
                    "tasks": [
                        {
                            "title": "Market Gaps",
                            "description": "Identify underserved segments"
                        },
                        {
                            "title": "Differentiation Strategy",
                            "description": "Define competitive advantages"
                        },
                        {
                            "title": "Business Model",
                            "description": "Design revenue and pricing model"
                        }
                    ]
                }
            ],
            "usage_notes": "Use this template for market research and competitive analysis",
            "times_used": 0,
            "created_at": now,
            "updated_at": now
        }
    ]


def main():
    db = get_db()

    templates = get_templates()

    print(f"\n{'='*60}")
    print(f"SEEDING {len(templates)} DEMO TEMPLATES")
    print(f"{'='*60}\n")

    added_count = 0

    for template in templates:
        template_name = template["name"]

        # Check if exists
        existing = db.memory_procedural.find_one({
            "user_id": template["user_id"],
            "name": template_name
        })

        if existing:
            print(f"⏭️  Skipping: '{template_name}' (already exists)")
            continue

        # Generate embedding
        embedding_text = f"{template['name']}. {template['description']}. Phases: {', '.join([p['name'] for p in template['phases']])}"
        template["embedding"] = embed_query(embedding_text)

        # Insert
        result = db.memory_procedural.insert_one(template)
        print(f"✓ Added: '{template_name}'")
        print(f"  Phases: {len(template['phases'])}")
        total_tasks = sum(len(phase['tasks']) for phase in template['phases'])
        print(f"  Total Tasks: {total_tasks}")
        print()
        added_count += 1

    print(f"{'='*60}")
    print(f"✅ Added {added_count} new templates")
    print(f"{'='*60}\n")

    # Show final template count
    total_templates = db.memory_procedural.count_documents({
        "user_id": DEMO_USER_ID,
        "rule_type": "template"
    })
    print(f"Total templates in memory_procedural: {total_templates}\n")


if __name__ == "__main__":
    main()
