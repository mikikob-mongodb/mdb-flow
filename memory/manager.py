"""
Memory Manager for Flow Companion

Future-ready architecture supporting:
- Multiple agent LLMs (Coordinator, Retrieval, Worklog)
- MCP server integration (Tavily, MongoDB)
- Agent-to-agent handoffs via shared memory
- Cross-agent action attribution

Memory Types:
- Short-term: Session context, agent working memory, disambiguation (TTL: 2hr)
- Long-term: Action history with embeddings (persistent)
- Shared: Agent handoffs with chain tracking (TTL: 5min)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
import uuid


class MemoryManager:
    def __init__(self, db, embedding_fn: Callable = None):
        """
        Initialize memory manager.

        Args:
            db: MongoDB database instance
            embedding_fn: Function to generate embeddings (optional)
        """
        self.db = db
        self.embed = embedding_fn
        self._setup_collections()

    def _setup_collections(self):
        """Create collections and indexes."""

        # ═══════════════════════════════════════════════════════════════
        # SHORT-TERM MEMORY (TTL: 2 hours)
        # ═══════════════════════════════════════════════════════════════
        self.short_term = self.db.short_term_memory

        # Indexes
        self.short_term.create_index("expires_at", expireAfterSeconds=0)
        self.short_term.create_index([("session_id", ASCENDING), ("memory_type", ASCENDING)])
        self.short_term.create_index([("session_id", ASCENDING), ("agent_id", ASCENDING)])

        # ═══════════════════════════════════════════════════════════════
        # LONG-TERM MEMORY (persistent)
        # ═══════════════════════════════════════════════════════════════
        self.long_term = self.db.long_term_memory

        # Indexes
        self.long_term.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.long_term.create_index([("user_id", ASCENDING), ("action_type", ASCENDING)])
        self.long_term.create_index([("user_id", ASCENDING), ("source_agent", ASCENDING)])
        self.long_term.create_index([("user_id", ASCENDING), ("entity.project_name", ASCENDING)])

        # ═══════════════════════════════════════════════════════════════
        # SHARED MEMORY (TTL: 5 minutes)
        # ═══════════════════════════════════════════════════════════════
        self.shared = self.db.shared_memory

        # Indexes
        self.shared.create_index("expires_at", expireAfterSeconds=0)
        self.shared.create_index("handoff_id", unique=True)
        self.shared.create_index([
            ("session_id", ASCENDING),
            ("target_agent", ASCENDING),
            ("status", ASCENDING)
        ])
        self.shared.create_index("chain_id")

    # ═══════════════════════════════════════════════════════════════════
    # SHORT-TERM: SESSION CONTEXT
    # ═══════════════════════════════════════════════════════════════════

    def read_session_context(self, session_id: str) -> Optional[Dict]:
        """Read session-level context."""
        doc = self.short_term.find_one({
            "session_id": session_id,
            "memory_type": "session_context"
        })
        return doc.get("context") if doc else None

    def update_session_context(self, session_id: str, updates: Dict,
                               user_id: str = None) -> None:
        """Merge updates into session context."""
        now = datetime.utcnow()
        expires = now + timedelta(hours=2)

        # Get existing context
        existing = self.read_session_context(session_id) or {}

        # Deep merge
        for key, value in updates.items():
            if value is None:
                existing.pop(key, None)
            elif isinstance(value, dict) and isinstance(existing.get(key), dict):
                existing[key].update(value)
            else:
                existing[key] = value

        self.short_term.update_one(
            {"session_id": session_id, "memory_type": "session_context"},
            {
                "$set": {
                    "context": existing,
                    "updated_at": now,
                    "expires_at": expires
                },
                "$setOnInsert": {
                    "created_at": now,
                    "user_id": user_id,
                    "agent_id": None
                }
            },
            upsert=True
        )

    def clear_session_context(self, session_id: str) -> None:
        """Clear session context."""
        self.short_term.delete_one({
            "session_id": session_id,
            "memory_type": "session_context"
        })

    # ═══════════════════════════════════════════════════════════════════
    # SHORT-TERM: AGENT WORKING MEMORY
    # ═══════════════════════════════════════════════════════════════════

    def read_agent_working(self, session_id: str, agent_id: str) -> Optional[Dict]:
        """Read agent's working memory."""
        doc = self.short_term.find_one({
            "session_id": session_id,
            "agent_id": agent_id,
            "memory_type": "agent_working"
        })
        return doc.get("working") if doc else None

    def update_agent_working(self, session_id: str, agent_id: str,
                            updates: Dict) -> None:
        """Update agent's working memory."""
        now = datetime.utcnow()
        expires = now + timedelta(hours=2)

        self.short_term.update_one(
            {
                "session_id": session_id,
                "agent_id": agent_id,
                "memory_type": "agent_working"
            },
            {
                "$set": {
                    **{f"working.{k}": v for k, v in updates.items()},
                    "updated_at": now,
                    "expires_at": expires
                },
                "$setOnInsert": {
                    "created_at": now,
                    "memory_type": "agent_working"
                }
            },
            upsert=True
        )

    def clear_agent_working(self, session_id: str, agent_id: str) -> None:
        """Clear agent's working memory."""
        self.short_term.delete_one({
            "session_id": session_id,
            "agent_id": agent_id,
            "memory_type": "agent_working"
        })

    # ═══════════════════════════════════════════════════════════════════
    # SHORT-TERM: DISAMBIGUATION
    # ═══════════════════════════════════════════════════════════════════

    def store_disambiguation(self, session_id: str, query: str,
                            results: List[Dict], source_agent: str) -> None:
        """Store search results for disambiguation."""
        now = datetime.utcnow()
        expires = now + timedelta(hours=2)

        # Add index to each result
        indexed_results = [
            {"index": i, **r} for i, r in enumerate(results[:5])
        ]

        self.short_term.update_one(
            {"session_id": session_id, "memory_type": "disambiguation"},
            {
                "$set": {
                    "disambiguation": {
                        "query": query,
                        "results": indexed_results,
                        "awaiting_selection": True,
                        "source_agent": source_agent,
                        "created_at": now
                    },
                    "updated_at": now,
                    "expires_at": expires
                },
                "$setOnInsert": {
                    "created_at": now,
                    "agent_id": None
                }
            },
            upsert=True
        )

    def resolve_disambiguation(self, session_id: str, index: int) -> Optional[Dict]:
        """Resolve disambiguation by index."""
        doc = self.short_term.find_one({
            "session_id": session_id,
            "memory_type": "disambiguation"
        })

        if not doc:
            return None

        results = doc.get("disambiguation", {}).get("results", [])
        if index < 0 or index >= len(results):
            return None

        selected = results[index]

        # Mark as resolved
        self.short_term.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "disambiguation.awaiting_selection": False,
                "disambiguation.selected_index": index
            }}
        )

        return selected

    def get_pending_disambiguation(self, session_id: str) -> Optional[Dict]:
        """Get pending disambiguation if any."""
        doc = self.short_term.find_one({
            "session_id": session_id,
            "memory_type": "disambiguation",
            "disambiguation.awaiting_selection": True
        })
        return doc.get("disambiguation") if doc else None

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: RECORDING ACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def record_action(self, user_id: str, session_id: str, action_type: str,
                      entity_type: str, entity: Dict, metadata: Dict = None,
                      source_agent: str = "coordinator",
                      triggered_by: str = "user",
                      handoff_id: str = None,
                      generate_embedding: bool = True) -> str:
        """Record an action to long-term memory."""

        # Build embedding text
        embedding_text = self._build_embedding_text(
            action_type, entity_type, entity, metadata
        )

        # Generate embedding if function provided
        embedding = None
        if generate_embedding and self.embed:
            try:
                embedding = self.embed(embedding_text)
            except Exception as e:
                print(f"Embedding generation failed: {e}")

        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity": entity,
            "metadata": metadata or {},
            "source_agent": source_agent,
            "triggered_by": triggered_by,
            "handoff_id": handoff_id,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }

        result = self.long_term.insert_one(doc)
        return str(result.inserted_id)

    def _build_embedding_text(self, action_type: str, entity_type: str,
                              entity: Dict, metadata: Dict) -> str:
        """Build text for embedding generation."""
        parts = []

        action_verbs = {
            "complete": "Completed",
            "start": "Started",
            "stop": "Stopped",
            "create": "Created",
            "update": "Updated",
            "add_note": "Added note to",
            "search": "Searched for",
            "research": "Researched"
        }

        verb = action_verbs.get(action_type, action_type.title())

        if entity_type == "task":
            parts.append(f"{verb} task: {entity.get('task_title', 'unknown')}")
            if entity.get("project_name"):
                parts.append(f"in project {entity['project_name']}")
        elif entity_type == "project":
            parts.append(f"{verb} project: {entity.get('project_name', 'unknown')}")
        elif entity_type in ["search", "research"]:
            query = (metadata or {}).get("query") or entity.get("query", "unknown")
            parts.append(f"{'Researched' if entity_type == 'research' else 'Searched for'}: {query}")

        if metadata and metadata.get("completion_note"):
            parts.append(f"Note: {metadata['completion_note'][:100]}")

        return " ".join(parts)

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: QUERYING HISTORY
    # ═══════════════════════════════════════════════════════════════════

    def get_action_history(self, user_id: str, time_range: str = None,
                          action_type: str = None, entity_type: str = None,
                          source_agent: str = None, project_name: str = None,
                          limit: int = 20) -> List[Dict]:
        """Query action history with filters."""

        query = {"user_id": user_id}

        # Time range filter
        if time_range and time_range != "all":
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            time_filters = {
                "today": {"$gte": today_start},
                "yesterday": {
                    "$gte": today_start - timedelta(days=1),
                    "$lt": today_start
                },
                "this_week": {
                    "$gte": (now - timedelta(days=now.weekday())).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                },
                "last_week": {
                    "$gte": (now - timedelta(days=now.weekday() + 7)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                    "$lt": (now - timedelta(days=now.weekday())).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                },
                "this_month": {
                    "$gte": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                }
            }

            if time_range in time_filters:
                query["timestamp"] = time_filters[time_range]

        # Other filters
        if action_type and action_type != "all":
            query["action_type"] = action_type

        if entity_type:
            query["entity_type"] = entity_type

        if source_agent and source_agent != "all":
            query["source_agent"] = source_agent

        if project_name:
            query["entity.project_name"] = project_name

        # Execute query
        cursor = self.long_term.find(query).sort("timestamp", DESCENDING).limit(limit)

        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)

        return results

    def search_history(self, user_id: str, semantic_query: str,
                      time_range: str = None, action_type: str = None,
                      limit: int = 10) -> List[Dict]:
        """Search action history using vector similarity.

        Args:
            user_id: User ID to filter by
            semantic_query: Natural language query (e.g., "debugging tasks", "memory work")
            time_range: Optional time range filter
            action_type: Optional action type filter
            limit: Maximum results to return

        Returns:
            List of actions sorted by similarity score
        """
        if not self.embed:
            raise ValueError("Embedding function not provided to MemoryManager")

        # Generate query embedding
        try:
            query_embedding = self.embed(semantic_query)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate query embedding: {str(e)}",
                "results": []
            }

        # Build $vectorSearch pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "memory_embeddings",  # Atlas search index name
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,  # Scan more candidates for better results
                    "limit": limit * 2,  # Get more before filtering
                    "filter": {"user_id": user_id}  # Filter by user
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "session_id": 1,
                    "action_type": 1,
                    "entity_type": 1,
                    "entity": 1,
                    "metadata": 1,
                    "source_agent": 1,
                    "timestamp": 1,
                    "embedding_text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        # Add additional filters if specified
        match_filters = {}

        if time_range and time_range != "all":
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            time_filters = {
                "today": {"$gte": today_start},
                "yesterday": {
                    "$gte": today_start - timedelta(days=1),
                    "$lt": today_start
                },
                "this_week": {
                    "$gte": (now - timedelta(days=now.weekday())).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                },
                "last_week": {
                    "$gte": (now - timedelta(days=now.weekday() + 7)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                    "$lt": (now - timedelta(days=now.weekday())).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                },
                "this_month": {
                    "$gte": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                }
            }

            if time_range in time_filters:
                match_filters["timestamp"] = time_filters[time_range]

        if action_type and action_type != "all":
            match_filters["action_type"] = action_type

        # Add $match stage if filters exist
        if match_filters:
            pipeline.append({"$match": match_filters})

        # Limit final results
        pipeline.append({"$limit": limit})

        # Execute search
        try:
            results = list(self.long_term.aggregate(pipeline))

            # Convert ObjectIds to strings
            for doc in results:
                doc["_id"] = str(doc["_id"])

            return results

        except Exception as e:
            # Return error details
            error_msg = str(e)
            if "index" in error_msg.lower():
                error_msg = f"Vector search index 'memory_embeddings' not found. Please create it in Atlas UI. Error: {error_msg}"

            return {
                "success": False,
                "error": error_msg,
                "results": []
            }

    def get_activity_summary(self, user_id: str,
                            time_range: str = "this_week") -> Dict:
        """Generate activity summary."""

        actions = self.get_action_history(user_id, time_range=time_range, limit=100)

        if not actions:
            return {
                "total": 0,
                "time_range": time_range,
                "by_type": {},
                "by_project": {},
                "by_agent": {},
                "timeline": []
            }

        summary = {
            "total": len(actions),
            "time_range": time_range,
            "by_type": {},
            "by_project": {},
            "by_agent": {},
            "timeline": []
        }

        for action in actions:
            # By type
            t = action["action_type"]
            summary["by_type"][t] = summary["by_type"].get(t, 0) + 1

            # By project
            project = action.get("entity", {}).get("project_name", "Unknown")
            if project not in summary["by_project"]:
                summary["by_project"][project] = {"total": 0, "by_type": {}}
            summary["by_project"][project]["total"] += 1
            summary["by_project"][project]["by_type"][t] = \
                summary["by_project"][project]["by_type"].get(t, 0) + 1

            # By agent
            agent = action.get("source_agent", "unknown")
            summary["by_agent"][agent] = summary["by_agent"].get(agent, 0) + 1

        # Timeline (most recent first)
        for action in actions[:10]:
            summary["timeline"].append({
                "action": action["action_type"],
                "entity": action.get("entity", {}).get("task_title") or
                         action.get("entity", {}).get("project_name"),
                "project": action.get("entity", {}).get("project_name"),
                "timestamp": action["timestamp"].isoformat() if action.get("timestamp") else None,
                "agent": action.get("source_agent")
            })

        return summary

    def generate_narrative(self, summary: Dict) -> str:
        """Generate narrative text from raw activity summary.

        Args:
            summary: Raw activity summary from get_activity_summary()

        Returns:
            Formatted markdown narrative text
        """
        parts = []
        time_range = summary.get("time_range", "unknown").replace("_", " ").title()
        total = summary.get("total", 0)

        # No activity
        if total == 0:
            return f"**Activity Summary ({time_range})**\n\nNo activity recorded for this period."

        # Overview
        parts.append(f"**Activity Summary ({time_range})**")
        parts.append(f"Total actions: {total}")

        # By type (sorted by count)
        by_type = summary.get("by_type", {})
        if by_type:
            parts.append("\n**Actions:**")
            sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
            for action_type, count in sorted_types:
                # Make action type more readable
                readable_type = action_type.replace("_", " ").title()
                parts.append(f"- {readable_type}: {count}")

        # By project (top 5)
        by_project = summary.get("by_project", {})
        if by_project:
            parts.append("\n**Top Projects:**")
            sorted_projects = sorted(
                by_project.items(),
                key=lambda x: x[1]["total"],
                reverse=True
            )
            for project, data in sorted_projects[:5]:
                project_total = data["total"]
                # Show breakdown of action types for this project
                project_types = data.get("by_type", {})
                if project_types:
                    # Get top 2 action types for this project
                    top_actions = sorted(
                        project_types.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:2]
                    action_details = ", ".join([
                        f"{count} {action_type}"
                        for action_type, count in top_actions
                    ])
                    parts.append(f"- **{project}**: {project_total} actions ({action_details})")
                else:
                    parts.append(f"- **{project}**: {project_total} actions")

        # By agent
        by_agent = summary.get("by_agent", {})
        if by_agent and len(by_agent) > 1:  # Only show if multiple agents
            parts.append("\n**Agent Activity:**")
            sorted_agents = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)
            for agent, count in sorted_agents:
                parts.append(f"- {agent.title()}: {count} actions")

        # Recent timeline (last 5)
        timeline = summary.get("timeline", [])
        if timeline:
            parts.append("\n**Recent Activity:**")
            for item in timeline[:5]:
                action = item.get("action", "unknown").replace("_", " ").title()
                entity = item.get("entity", "Unknown")
                project = item.get("project", "")
                timestamp = item.get("timestamp", "")

                # Format timestamp if available
                time_str = ""
                if timestamp:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        time_str = dt.strftime("%b %d, %I:%M %p")
                    except:
                        time_str = timestamp[:16]  # Just take date/time portion

                # Build timeline entry
                if project:
                    entry = f"- {action}: **{entity}** ({project})"
                else:
                    entry = f"- {action}: **{entity}**"

                if time_str:
                    entry += f" - {time_str}"

                parts.append(entry)

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════════
    # SHARED: WRITING HANDOFFS
    # ═══════════════════════════════════════════════════════════════════

    def write_handoff(self, session_id: str, user_id: str,
                      source_agent: str, target_agent: str,
                      handoff_type: str, payload: Dict,
                      chain_id: str = None, parent_handoff_id: str = None,
                      priority: str = "normal") -> str:
        """Write a handoff for another agent."""

        handoff_id = str(uuid.uuid4())
        chain_id = chain_id or str(uuid.uuid4())
        now = datetime.utcnow()

        # Calculate sequence in chain
        sequence = 1
        if parent_handoff_id:
            parent = self.shared.find_one({"handoff_id": parent_handoff_id})
            if parent:
                sequence = parent.get("sequence", 0) + 1

        doc = {
            "handoff_id": handoff_id,
            "session_id": session_id,
            "user_id": user_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "handoff_type": handoff_type,
            "payload": payload,
            "status": "pending",
            "priority": priority,
            "error": None,
            "chain_id": chain_id,
            "parent_handoff_id": parent_handoff_id,
            "sequence": sequence,
            "created_at": now,
            "consumed_at": None,
            "expires_at": now + timedelta(minutes=5)
        }

        self.shared.insert_one(doc)
        return handoff_id

    # ═══════════════════════════════════════════════════════════════════
    # SHARED: READING HANDOFFS
    # ═══════════════════════════════════════════════════════════════════

    def read_handoff(self, session_id: str, target_agent: str,
                     handoff_type: str = None, consume: bool = True) -> Optional[Dict]:
        """Read a handoff (optionally consuming it)."""

        query = {
            "session_id": session_id,
            "target_agent": target_agent,
            "status": "pending"
        }

        if handoff_type:
            query["handoff_type"] = handoff_type

        sort = [("priority", DESCENDING), ("created_at", ASCENDING)]

        if consume:
            doc = self.shared.find_one_and_update(
                query,
                {"$set": {
                    "status": "consumed",
                    "consumed_at": datetime.utcnow()
                }},
                sort=sort
            )
        else:
            doc = self.shared.find_one(query, sort=sort)

        return doc

    def read_all_pending(self, session_id: str, target_agent: str) -> List[Dict]:
        """Read all pending handoffs for an agent (without consuming)."""

        cursor = self.shared.find({
            "session_id": session_id,
            "target_agent": target_agent,
            "status": "pending"
        }).sort([("priority", DESCENDING), ("created_at", ASCENDING)])

        return list(cursor)

    def check_pending(self, session_id: str, target_agent: str) -> bool:
        """Check if there are pending handoffs."""
        return self.shared.count_documents({
            "session_id": session_id,
            "target_agent": target_agent,
            "status": "pending"
        }) > 0

    # ═══════════════════════════════════════════════════════════════════
    # SHARED: CHAIN OPERATIONS
    # ═══════════════════════════════════════════════════════════════════

    def get_chain(self, chain_id: str) -> List[Dict]:
        """Get all handoffs in a chain."""
        cursor = self.shared.find({"chain_id": chain_id}).sort("sequence", ASCENDING)
        return list(cursor)

    def get_chain_status(self, chain_id: str) -> Dict:
        """Get status summary for a chain."""
        handoffs = self.get_chain(chain_id)

        return {
            "chain_id": chain_id,
            "total": len(handoffs),
            "pending": sum(1 for h in handoffs if h["status"] == "pending"),
            "consumed": sum(1 for h in handoffs if h["status"] == "consumed"),
            "error": sum(1 for h in handoffs if h["status"] == "error"),
            "agents_involved": list(set(
                [h["source_agent"] for h in handoffs] +
                [h["target_agent"] for h in handoffs]
            )),
            "latest": handoffs[-1] if handoffs else None
        }

    def mark_error(self, handoff_id: str, error: str) -> None:
        """Mark a handoff as errored."""
        self.shared.update_one(
            {"handoff_id": handoff_id},
            {"$set": {"status": "error", "error": error}}
        )

    # ═══════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════

    def get_memory_stats(self, session_id: str, user_id: str) -> Dict:
        """Get memory statistics."""
        return {
            "short_term_count": self.short_term.count_documents({
                "session_id": session_id
            }),
            "long_term_count": self.long_term.count_documents({
                "user_id": user_id
            }),
            "shared_pending": self.shared.count_documents({
                "session_id": session_id,
                "status": "pending"
            }),
            "action_counts": self._get_action_counts(user_id)
        }

    def _get_action_counts(self, user_id: str) -> Dict[str, int]:
        """Get counts by action type."""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$action_type", "count": {"$sum": 1}}}
        ]
        results = list(self.long_term.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in results}

    def clear_session(self, session_id: str) -> Dict[str, int]:
        """Clear all memory for a session (for testing/demo reset)."""
        short = self.short_term.delete_many({"session_id": session_id})
        shared = self.shared.delete_many({"session_id": session_id})
        return {
            "short_term_deleted": short.deleted_count,
            "shared_deleted": shared.deleted_count
        }
