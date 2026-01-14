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

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any, Callable
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
import uuid

# Memory type constants
LONG_TERM_TYPES = {
    "episodic": "action",      # What happened (existing action_history)
    "semantic": "preference",   # What I know (user preferences, facts)
    "procedural": "rule"        # How to act (learned rules/workflows)
}


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
        from pymongo.errors import OperationFailure

        # ═══════════════════════════════════════════════════════════════
        # WORKING MEMORY (In-memory session state - not persisted)
        # ═══════════════════════════════════════════════════════════════
        # Session context, handoffs, and disambiguation now handled in-memory
        # No database collection needed
        self._session_contexts = {}  # session_id -> context dict
        self._agent_working = {}  # (session_id, agent_id) -> working memory dict
        self._handoffs = {}  # handoff_id -> handoff dict
        self._disambiguations = {}  # session_id -> disambiguation dict

        # ═══════════════════════════════════════════════════════════════
        # EPISODIC MEMORY (persistent - actions and events)
        # ═══════════════════════════════════════════════════════════════
        self.episodic = self.db.memory_episodic

        # Indexes for actions/events
        try:
            self.episodic.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        except OperationFailure:
            pass
        try:
            self.episodic.create_index([("user_id", ASCENDING), ("action_type", ASCENDING)])
        except OperationFailure:
            pass
        try:
            self.episodic.create_index([("user_id", ASCENDING), ("source_agent", ASCENDING)])
        except OperationFailure:
            pass
        try:
            self.episodic.create_index([
                ("entity_type", ASCENDING),
                ("entity_id", ASCENDING),
                ("generated_at", DESCENDING)
            ])
        except OperationFailure:
            pass

        # ═══════════════════════════════════════════════════════════════
        # SEMANTIC MEMORY (persistent - knowledge cache and preferences)
        # ═══════════════════════════════════════════════════════════════
        self.semantic = self.db.memory_semantic

        # Indexes for knowledge and preferences
        try:
            self.semantic.create_index([
                ("user_id", ASCENDING),
                ("semantic_type", ASCENDING),
                ("key", ASCENDING)
            ])
        except OperationFailure:
            pass
        try:
            self.semantic.create_index([("user_id", ASCENDING), ("query", ASCENDING)])
        except OperationFailure:
            pass
        try:
            self.semantic.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        except OperationFailure:
            pass

        # ═══════════════════════════════════════════════════════════════
        # PROCEDURAL MEMORY (persistent - workflow patterns and rules)
        # ═══════════════════════════════════════════════════════════════
        self.procedural = self.db.memory_procedural

        # Indexes
        try:
            self.procedural.create_index([
                ("user_id", ASCENDING),
                ("rule_type", ASCENDING),
                ("trigger_pattern", ASCENDING)
            ])
        except OperationFailure:
            pass
        try:
            self.procedural.create_index([
                ("user_id", ASCENDING),
                ("times_used", DESCENDING),
                ("success_rate", DESCENDING)
            ])
        except OperationFailure:
            pass
        try:
            # Vector index for semantic workflow search
            self.procedural.create_index([("embedding", ASCENDING)])
        except OperationFailure:
            pass

    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY: SESSION CONTEXT (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def read_session_context(self, session_id: str) -> Optional[Dict]:
        """Read session-level context from in-memory storage."""
        session_data = self._session_contexts.get(session_id, {})
        return session_data.get("context")

    def update_session_context(self, session_id: str, updates: Dict,
                               user_id: str = None) -> None:
        """Merge updates into session context (in-memory)."""
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

        # Store in memory
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow()
            }

        self._session_contexts[session_id]["context"] = existing
        self._session_contexts[session_id]["updated_at"] = datetime.utcnow()

    def clear_session_context(self, session_id: str) -> None:
        """Clear session context from in-memory storage."""
        if session_id in self._session_contexts:
            del self._session_contexts[session_id]

    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY: AGENT WORKING MEMORY (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def read_agent_working(self, session_id: str, agent_id: str) -> Optional[Dict]:
        """Read agent's working memory from in-memory storage."""
        key = (session_id, agent_id)
        agent_data = self._agent_working.get(key, {})
        return agent_data.get("working")

    def update_agent_working(self, session_id: str, agent_id: str,
                            updates: Dict) -> None:
        """Update agent's working memory in in-memory storage."""
        key = (session_id, agent_id)

        # Get existing working memory
        existing = self.read_agent_working(session_id, agent_id) or {}

        # Apply updates
        for k, v in updates.items():
            existing[k] = v

        # Store back
        if key not in self._agent_working:
            self._agent_working[key] = {
                "session_id": session_id,
                "agent_id": agent_id,
                "created_at": datetime.utcnow()
            }

        self._agent_working[key]["working"] = existing
        self._agent_working[key]["updated_at"] = datetime.utcnow()

    def clear_agent_working(self, session_id: str, agent_id: str) -> None:
        """Clear agent's working memory from in-memory storage."""
        key = (session_id, agent_id)
        if key in self._agent_working:
            del self._agent_working[key]

    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY: DISAMBIGUATION (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def store_disambiguation(self, session_id: str, query: str,
                            results: List[Dict], source_agent: str) -> None:
        """Store search results for disambiguation in in-memory storage."""
        now = datetime.utcnow()

        # Add index to each result
        indexed_results = [
            {"index": i, **r} for i, r in enumerate(results[:5])
        ]

        self._disambiguations[session_id] = {
            "session_id": session_id,
            "query": query,
            "results": indexed_results,
            "awaiting_selection": True,
            "source_agent": source_agent,
            "created_at": now,
            "updated_at": now
        }

    def resolve_disambiguation(self, session_id: str, index: int) -> Optional[Dict]:
        """Resolve disambiguation by index from in-memory storage."""
        disambiguation = self._disambiguations.get(session_id)

        if not disambiguation:
            return None

        results = disambiguation.get("results", [])
        if index < 0 or index >= len(results):
            return None

        selected = results[index]

        # Mark as resolved
        disambiguation["awaiting_selection"] = False
        disambiguation["selected_index"] = index

        return selected

    def get_pending_disambiguation(self, session_id: str) -> Optional[Dict]:
        """Get pending disambiguation if any from in-memory storage."""
        disambiguation = self._disambiguations.get(session_id)
        if disambiguation and disambiguation.get("awaiting_selection"):
            return disambiguation
        return None

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: RECORDING ACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def record_action(self, user_id: str, session_id: str, action_type: str,
                      entity_type: str, entity: Dict, metadata: Dict = None,
                      source_agent: str = "coordinator",
                      triggered_by: str = "user",
                      handoff_id: str = None,
                      generate_embedding: bool = True) -> str:
        """Record an action to episodic memory."""

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

        result = self.episodic.insert_one(doc)
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
        cursor = self.episodic.find(query).sort("timestamp", DESCENDING).limit(limit)

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
            results = list(self.episodic.aggregate(pipeline))

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
    # WORKING MEMORY: WRITING HANDOFFS (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def write_handoff(self, session_id: str, user_id: str,
                      source_agent: str, target_agent: str,
                      handoff_type: str, payload: Dict,
                      chain_id: str = None, parent_handoff_id: str = None,
                      priority: str = "normal") -> str:
        """Write a handoff for another agent to in-memory storage."""

        handoff_id = str(uuid.uuid4())
        chain_id = chain_id or str(uuid.uuid4())
        now = datetime.utcnow()

        # Calculate sequence in chain
        sequence = 1
        if parent_handoff_id:
            parent = self._handoffs.get(parent_handoff_id)
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
            "consumed_at": None
        }

        self._handoffs[handoff_id] = doc
        return handoff_id

    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY: READING HANDOFFS (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def read_handoff(self, session_id: str, target_agent: str,
                     handoff_type: str = None, consume: bool = True) -> Optional[Dict]:
        """Read a handoff from in-memory storage (optionally consuming it)."""

        # Filter matching handoffs
        matching = [
            h for h in self._handoffs.values()
            if h["session_id"] == session_id
            and h["target_agent"] == target_agent
            and h["status"] == "pending"
            and (handoff_type is None or h["handoff_type"] == handoff_type)
        ]

        if not matching:
            return None

        # Sort by priority (descending) then created_at (ascending)
        priority_order = {"high": 3, "normal": 2, "low": 1}
        matching.sort(
            key=lambda h: (-priority_order.get(h["priority"], 2), h["created_at"])
        )

        doc = matching[0]

        if consume:
            doc["status"] = "consumed"
            doc["consumed_at"] = datetime.utcnow()

        return doc

    def read_all_pending(self, session_id: str, target_agent: str) -> List[Dict]:
        """Read all pending handoffs for an agent from in-memory storage (without consuming)."""

        matching = [
            h for h in self._handoffs.values()
            if h["session_id"] == session_id
            and h["target_agent"] == target_agent
            and h["status"] == "pending"
        ]

        # Sort by priority (descending) then created_at (ascending)
        priority_order = {"high": 3, "normal": 2, "low": 1}
        matching.sort(
            key=lambda h: (-priority_order.get(h["priority"], 2), h["created_at"])
        )

        return matching

    def check_pending(self, session_id: str, target_agent: str) -> bool:
        """Check if there are pending handoffs in in-memory storage."""
        return any(
            h["session_id"] == session_id
            and h["target_agent"] == target_agent
            and h["status"] == "pending"
            for h in self._handoffs.values()
        )

    # ═══════════════════════════════════════════════════════════════════
    # WORKING MEMORY: CHAIN OPERATIONS (In-Memory)
    # ═══════════════════════════════════════════════════════════════════

    def get_chain(self, chain_id: str) -> List[Dict]:
        """Get all handoffs in a chain from in-memory storage."""
        matching = [h for h in self._handoffs.values() if h["chain_id"] == chain_id]
        matching.sort(key=lambda h: h["sequence"])
        return matching

    def get_chain_status(self, chain_id: str) -> Dict:
        """Get status summary for a chain from in-memory storage."""
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
        """Mark a handoff as errored in in-memory storage."""
        if handoff_id in self._handoffs:
            self._handoffs[handoff_id]["status"] = "error"
            self._handoffs[handoff_id]["error"] = error

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: SEMANTIC MEMORY (Preferences)
    # ═══════════════════════════════════════════════════════════════════

    def record_preference(self, user_id: str, key: str, value: any,
                          source: str = "inferred", confidence: float = 0.8) -> str:
        """
        Store or update a preference in Semantic Memory (long-term).

        Args:
            user_id: User identifier
            key: Preference key (e.g., "focus_project", "priority_filter")
            value: Preference value
            source: "explicit" (user stated) or "inferred" (detected from behavior)
            confidence: 0.0-1.0, higher = more certain

        Returns:
            Document ID
        """
        existing = self.semantic.find_one({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": key
        })

        now = datetime.utcnow()

        if existing:
            # Update existing preference
            new_confidence = max(existing.get("confidence", 0), confidence)
            if source == "explicit":
                new_confidence = max(new_confidence, 0.9)

            self.semantic.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "value": value,
                    "source": source,
                    "confidence": new_confidence,
                    "updated_at": now
                },
                "$inc": {"times_used": 1}}
            )
            return str(existing["_id"])

        # Create new preference
        doc = {
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": key,
            "value": value,
            "source": source,
            "confidence": confidence if source != "explicit" else 0.9,
            "times_used": 1,
            "created_at": now,
            "updated_at": now
        }
        result = self.semantic.insert_one(doc)
        return str(result.inserted_id)

    def get_preferences(self, user_id: str, min_confidence: float = 0.0) -> list:
        """
        Get all preferences (Semantic Memory) for a user.

        Args:
            user_id: User identifier
            min_confidence: Minimum confidence threshold

        Returns:
            List of preference documents, sorted by confidence (highest first)
        """
        query = {
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "preference"
        }

        if min_confidence > 0:
            query["confidence"] = {"$gte": min_confidence}

        results = list(self.semantic.find(query).sort("confidence", -1))

        # Convert ObjectId to string
        for r in results:
            r["_id"] = str(r["_id"])

        return results

    def get_preference(self, user_id: str, key: str) -> Optional[dict]:
        """Get a specific preference by key."""
        doc = self.semantic.find_one({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": key
        })

        if doc:
            doc["_id"] = str(doc["_id"])

        return doc

    def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a preference."""
        result = self.semantic.delete_one({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "preference",
            "key": key
        })
        return result.deleted_count > 0

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: PROCEDURAL MEMORY (Rules)
    # ═══════════════════════════════════════════════════════════════════

    def record_rule(self, user_id: str, trigger: str, action: str,
                    parameters: dict = None, source: str = "explicit",
                    confidence: float = 0.8) -> str:
        """
        Store or update a rule in Procedural Memory (long-term).

        Args:
            user_id: User identifier
            trigger: Trigger pattern (e.g., "done", "next", "skip")
            action: Action to perform (e.g., "complete_current_task")
            parameters: Optional parameters for the action
            source: "explicit" (user stated) or "inferred"
            confidence: 0.0-1.0

        Returns:
            Document ID
        """
        # Normalize trigger
        trigger_normalized = trigger.lower().strip()

        existing = self.procedural.find_one({
            "user_id": user_id,
            "trigger_pattern": trigger_normalized
        })

        now = datetime.utcnow()

        if existing:
            # Update existing rule
            new_confidence = max(existing.get("confidence", 0), confidence)

            self.procedural.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "action_type": action,
                    "parameters": parameters or {},
                    "confidence": new_confidence,
                    "updated_at": now
                },
                "$inc": {"times_used": 1}}
            )
            return str(existing["_id"])

        # Create new rule
        doc = {
            "user_id": user_id,
            "trigger_pattern": trigger_normalized,
            "action_type": action,
            "parameters": parameters or {},
            "source": source,
            "confidence": confidence,
            "times_used": 1,
            "created_at": now,
            "updated_at": now
        }
        result = self.procedural.insert_one(doc)
        return str(result.inserted_id)

    def get_rules(self, user_id: str, min_confidence: float = 0.0) -> list:
        """
        Get all rules (Procedural Memory) for a user.

        Args:
            user_id: User identifier
            min_confidence: Minimum confidence threshold

        Returns:
            List of rule documents, sorted by times_used (most used first)
        """
        query = {"user_id": user_id}

        if min_confidence > 0:
            query["confidence"] = {"$gte": min_confidence}

        results = list(self.procedural.find(query).sort("times_used", -1))

        for r in results:
            r["_id"] = str(r["_id"])

        return results

    def get_workflows(self, user_id: str, min_success_rate: float = 0.0) -> list:
        """
        Get all workflow patterns (Procedural Memory) for a user.

        Workflows are multi-step operation patterns that guide the agent
        through complex sequences like "create task then start it".

        Args:
            user_id: User identifier
            min_success_rate: Minimum success rate threshold (0.0-1.0)

        Returns:
            List of workflow documents, sorted by times_used and success_rate
        """
        query = {
            "user_id": user_id,
            "rule_type": "workflow"
        }

        if min_success_rate > 0:
            query["success_rate"] = {"$gte": min_success_rate}

        results = list(self.procedural.find(query).sort([
            ("times_used", -1),  # Most used first
            ("success_rate", -1)  # Then by success rate
        ]))

        for r in results:
            r["_id"] = str(r["_id"])

        return results

    def get_workflow_for_pattern(self, user_id: str, user_message: str) -> Optional[dict]:
        """
        Get workflow matching a trigger pattern in the user's message.

        Args:
            user_id: User identifier
            user_message: User's input text

        Returns:
            Matching workflow or None
        """
        import re

        # Get all workflows for this user
        workflows = self.procedural.find({
            "user_id": user_id,
            "rule_type": "workflow"
        })

        # Check each workflow's trigger pattern
        for workflow in workflows:
            trigger_pattern = workflow.get("trigger_pattern", "")
            if trigger_pattern:
                try:
                    if re.search(trigger_pattern, user_message, re.IGNORECASE):
                        # Update last_used timestamp
                        from datetime import datetime
                        self.procedural.update_one(
                            {"_id": workflow["_id"]},
                            {
                                "$set": {"last_used": datetime.utcnow()},
                                "$inc": {"times_used": 1}
                            }
                        )
                        workflow["_id"] = str(workflow["_id"])
                        return workflow
                except re.error:
                    # Invalid regex pattern, skip
                    continue

        return None

    def search_workflows_semantic(
        self,
        user_id: str,
        user_message: str,
        min_score: float = 0.7,
        limit: int = 3
    ) -> Optional[dict]:
        """
        Search for workflow using combined regex + vector similarity.

        First tries exact regex pattern matching. If no match found,
        falls back to semantic vector search.

        Args:
            user_id: User identifier
            user_message: User's input text
            min_score: Minimum similarity score for vector search (0.0-1.0)
            limit: Maximum number of vector search results to consider

        Returns:
            Best matching workflow or None
        """
        import re
        from datetime import datetime

        # STEP 1: Try regex pattern matching (fast, precise)
        workflows = list(self.procedural.find({
            "user_id": user_id,
            "rule_type": "workflow"
        }))

        for workflow in workflows:
            trigger_pattern = workflow.get("trigger_pattern", "")
            if trigger_pattern:
                try:
                    if re.search(trigger_pattern, user_message, re.IGNORECASE):
                        # Update usage stats
                        self.procedural.update_one(
                            {"_id": workflow["_id"]},
                            {
                                "$set": {"last_used": datetime.utcnow()},
                                "$inc": {"times_used": 1}
                            }
                        )
                        workflow["_id"] = str(workflow["_id"])
                        workflow["match_type"] = "regex"
                        workflow["match_score"] = 1.0
                        return workflow
                except re.error:
                    continue

        # STEP 2: Fall back to vector similarity search
        if not self.embed:
            return None

        # Generate embedding for user message
        query_embedding = self.embed(user_message)

        # Vector search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,
                    "limit": limit,
                    "filter": {
                        "user_id": user_id,
                        "rule_type": "workflow"
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(self.procedural.aggregate(pipeline))

        if results and results[0].get("score", 0) >= min_score:
            best_match = results[0]

            # Update usage stats
            self.procedural.update_one(
                {"_id": best_match["_id"]},
                {
                    "$set": {"last_used": datetime.utcnow()},
                    "$inc": {"times_used": 1}
                }
            )

            best_match["_id"] = str(best_match["_id"])
            best_match["match_type"] = "semantic"
            best_match["match_score"] = best_match.get("score", 0)
            return best_match

        return None

    def get_rule_for_trigger(self, user_id: str, trigger: str) -> Optional[dict]:
        """
        Get the rule matching a trigger pattern.

        Args:
            user_id: User identifier
            trigger: Trigger text to match

        Returns:
            Matching rule or None
        """
        trigger_normalized = trigger.lower().strip()

        doc = self.procedural.find_one({
            "user_id": user_id,
            "trigger_pattern": trigger_normalized
        })

        if doc:
            doc["_id"] = str(doc["_id"])

            # Increment usage
            self.procedural.update_one(
                {"_id": ObjectId(doc["_id"])},
                {"$inc": {"times_used": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )

        return doc

    def delete_rule(self, user_id: str, trigger: str) -> bool:
        """Delete a rule by trigger pattern."""
        result = self.procedural.delete_one({
            "user_id": user_id,
            "trigger_pattern": trigger.lower().strip()
        })
        return result.deleted_count > 0

    def get_procedural_rule(
        self,
        user_id: str,
        rule_type: str = None,
        trigger: str = None,
        name: str = None
    ) -> Optional[dict]:
        """
        Retrieve a procedural rule (template, checklist, behavior rule).

        Can search by:
        - rule_type: "template", "checklist", "behavior"
        - trigger: the trigger keyword (e.g., "create_gtm_project")
        - name: exact name match

        Args:
            user_id: User identifier
            rule_type: Optional filter by rule type
            trigger: Optional filter by trigger keyword
            name: Optional filter by exact name match

        Returns:
            Matching rule document or None
        """
        query = {"user_id": user_id}

        if rule_type:
            query["rule_type"] = rule_type
        if trigger:
            query["trigger"] = trigger
        if name:
            query["name"] = name

        doc = self.procedural.find_one(query)

        if doc:
            # Update usage stats
            self.procedural.update_one(
                {"_id": doc["_id"]},
                {
                    "$inc": {"times_used": 1},
                    "$set": {"last_used": datetime.utcnow()}
                }
            )
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])

        return doc

    def search_procedural_rules(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Semantic search over procedural rules using vector embeddings.

        Useful for natural language queries like:
        - "find a template for go-to-market"
        - "what checklists do I have?"
        - "show me project templates"

        Args:
            user_id: User identifier
            query: Natural language search query
            limit: Maximum number of results (default 5)

        Returns:
            List of matching rule documents with similarity scores
        """
        if not self.embed:
            # Fallback to text search if no embedding function
            return []

        # Generate embedding for query
        query_embedding = self.embed(query)

        # Vector search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 4,  # Search more candidates for better results
                    "limit": limit,
                    "filter": {
                        "user_id": user_id
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(self.procedural.aggregate(pipeline))

        # Convert ObjectIds to strings
        for r in results:
            r["_id"] = str(r["_id"])

        return results

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: COMBINED QUERIES
    # ═══════════════════════════════════════════════════════════════════

    def get_user_memory_profile(self, user_id: str) -> dict:
        """
        Get complete memory profile for a user.

        Returns:
            {
                "preferences": [...],
                "rules": [...],
                "action_summary": {...}
            }
        """
        return {
            "preferences": self.get_preferences(user_id),
            "rules": self.get_rules(user_id),
            "action_summary": self.get_activity_summary(user_id, time_range="this_week")
        }

    # ═══════════════════════════════════════════════════════════════════
    # LONG-TERM: KNOWLEDGE CACHE (Semantic Memory - Knowledge)
    # ═══════════════════════════════════════════════════════════════════

    def cache_knowledge(
        self,
        user_id: str,
        query: str,
        results: any,
        source: str = "tavily",
        freshness_days: int = 7
    ) -> str:
        """
        Cache search/research results as knowledge.

        Stored in memory_semantic with:
        - memory_type: "semantic"
        - semantic_type: "knowledge"

        Args:
            user_id: User identifier
            query: Search query text
            results: Search results to cache
            source: Source of knowledge (e.g., "tavily", "mcp")
            freshness_days: Days until cache expires (default 7)

        Returns:
            Inserted document ID as string
        """
        now = datetime.now(timezone.utc)

        # Generate embedding for semantic search
        embedding = None
        if self.embed:
            try:
                embedding = self.embed(query)
            except Exception as e:
                from shared.logger import get_logger
                logger = get_logger("memory")
                logger.warning(f"Failed to generate embedding for knowledge cache: {e}")

        doc = {
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "knowledge",
            "query": query,
            "results": results,
            "source": source,
            "embedding": embedding,
            "fetched_at": now,
            "expires_at": now + timedelta(days=freshness_days),
            "times_accessed": 0,
            "created_at": now
        }

        result = self.semantic.insert_one(doc)
        return str(result.inserted_id)

    def get_cached_knowledge(
        self,
        user_id: str,
        query: str,
        max_age_days: int = 7,
        similarity_threshold: float = 0.85
    ) -> Optional[dict]:
        """
        Find cached knowledge matching the query via vector search.

        Returns None if:
        - No similar query found
        - Found but expired
        - No embedding function available

        If found and fresh:
        - Increments times_accessed
        - Returns the document

        Args:
            user_id: User identifier
            query: Search query
            max_age_days: Maximum age in days (default 7)
            similarity_threshold: Minimum similarity score (default 0.85)

        Returns:
            Cached knowledge document or None
        """
        if not self.embed:
            return None

        now = datetime.now(timezone.utc)

        try:
            query_embedding = self.embed(query)
        except Exception:
            return None

        # Vector search on knowledge entries
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 20,
                    "limit": 5,
                    "filter": {
                        "user_id": user_id,
                        "memory_type": "semantic",
                        "semantic_type": "knowledge"
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {
                "$match": {
                    "score": {"$gte": similarity_threshold},
                    "expires_at": {"$gt": now}
                }
            },
            {"$limit": 1}
        ]

        try:
            results = list(self.semantic.aggregate(pipeline))
        except Exception as e:
            from shared.logger import get_logger
            logger = get_logger("memory")
            logger.warning(f"Vector search failed for knowledge cache: {e}")
            return None

        if not results:
            return None

        doc = results[0]

        # Increment access count
        self.semantic.update_one(
            {"_id": doc["_id"]},
            {
                "$inc": {"times_accessed": 1},
                "$set": {"last_accessed": now}
            }
        )

        return doc

    def search_knowledge(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[dict]:
        """
        Semantic search over all cached knowledge (regardless of age).
        Useful for "what do you know about X" queries.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results to return (default 5)

        Returns:
            List of knowledge documents with similarity scores
        """
        if not self.embed:
            return []

        try:
            query_embedding = self.embed(query)
        except Exception:
            return []

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 50,
                    "limit": limit,
                    "filter": {
                        "user_id": user_id,
                        "memory_type": "semantic",
                        "semantic_type": "knowledge"
                    }
                }
            },
            {
                "$addFields": {
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            return list(self.semantic.aggregate(pipeline))
        except Exception as e:
            from shared.logger import get_logger
            logger = get_logger("memory")
            logger.warning(f"Vector search failed for knowledge: {e}")
            return []

    def clear_knowledge_cache(self, user_id: str) -> int:
        """
        Clear all cached knowledge for a user.

        Args:
            user_id: User identifier

        Returns:
            Count of deleted documents
        """
        result = self.semantic.delete_many({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "knowledge"
        })
        return result.deleted_count

    def get_knowledge_stats(self, user_id: str) -> dict:
        """
        Get knowledge cache statistics.

        Args:
            user_id: User identifier

        Returns:
            Dict with total, fresh, and expired counts
        """
        now = datetime.now(timezone.utc)

        total = self.semantic.count_documents({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "knowledge"
        })

        fresh = self.semantic.count_documents({
            "user_id": user_id,
            "memory_type": "semantic",
            "semantic_type": "knowledge",
            "expires_at": {"$gt": now}
        })

        return {
            "total": total,
            "fresh": fresh,
            "expired": total - fresh
        }

    # ═══════════════════════════════════════════════════════════════════
    # EPISODIC MEMORY: AI-GENERATED ACTIVITY SUMMARIES
    # ═══════════════════════════════════════════════════════════════════

    def store_episodic_summary(
        self,
        user_id: str,
        entity_type: str,
        entity_id: Any,
        summary: str,
        activity_count: int,
        entity_title: str = None,
        entity_status: str = None
    ) -> str:
        """
        Store an AI-generated episodic memory summary.

        Args:
            user_id: User identifier
            entity_type: "task" or "project"
            entity_id: ObjectId of task or project
            summary: AI-generated natural language summary
            activity_count: Number of activity log entries at time of generation
            entity_title: Task title or project name (optional)
            entity_status: Current status (optional)

        Returns:
            Inserted document ID as string
        """
        from bson import ObjectId

        # Convert entity_id to ObjectId if needed
        if not isinstance(entity_id, ObjectId):
            entity_id = ObjectId(entity_id)

        doc = {
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "summary": summary,
            "activity_count": activity_count,
            "entity_title": entity_title,
            "entity_status": entity_status,
            "created_at": datetime.utcnow(),
            "generated_at": datetime.utcnow()
        }

        result = self.episodic.insert_one(doc)
        return str(result.inserted_id)

    def get_latest_episodic_summary(
        self,
        entity_type: str,
        entity_id: Any
    ) -> Optional[Dict]:
        """
        Get the most recent episodic memory summary for a task or project.

        Args:
            entity_type: "task" or "project"
            entity_id: ObjectId of task or project

        Returns:
            Latest summary document or None
        """
        from bson import ObjectId

        # Convert entity_id to ObjectId if needed
        if not isinstance(entity_id, ObjectId):
            entity_id = ObjectId(entity_id)

        doc = self.episodic.find_one(
            {
                "entity_type": entity_type,
                "entity_id": entity_id
            },
            sort=[("generated_at", DESCENDING)]
        )

        if doc:
            doc["_id"] = str(doc["_id"])
            doc["entity_id"] = str(doc["entity_id"])

        return doc

    def get_all_episodic_summaries(
        self,
        entity_type: str,
        entity_id: Any,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get all episodic memory summaries for a task or project (most recent first).

        Args:
            entity_type: "task" or "project"
            entity_id: ObjectId of task or project
            limit: Maximum number of summaries to return

        Returns:
            List of summary documents
        """
        from bson import ObjectId

        # Convert entity_id to ObjectId if needed
        if not isinstance(entity_id, ObjectId):
            entity_id = ObjectId(entity_id)

        cursor = self.episodic.find(
            {
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        ).sort("generated_at", DESCENDING).limit(limit)

        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["entity_id"] = str(doc["entity_id"])
            results.append(doc)

        return results

    # ═══════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════

    def get_memory_stats(self, session_id: str, user_id: str) -> Dict:
        """Get memory statistics including all memory types."""

        # Working memory counts (in-memory)
        session_count = 1 if session_id in self._session_contexts else 0
        agent_working_count = sum(1 for k in self._agent_working.keys() if k[0] == session_id)
        disambiguation_count = 1 if session_id in self._disambiguations else 0
        handoff_pending = sum(
            1 for h in self._handoffs.values()
            if h["session_id"] == session_id and h["status"] == "pending"
        )
        working_memory_count = session_count + agent_working_count + disambiguation_count

        # Long-term breakdown by memory_type
        episodic_count = self.episodic.count_documents({
            "user_id": user_id
        })

        semantic_count = self.semantic.count_documents({
            "user_id": user_id
        })

        # Procedural workflows and rules (from dedicated collection)
        procedural_count = self.procedural.count_documents({
            "user_id": user_id
        })

        # Knowledge cache stats
        knowledge_stats = self.get_knowledge_stats(user_id)

        # Action counts (episodic only)
        action_counts = self._get_action_counts(user_id)

        return {
            "working_memory_count": working_memory_count,
            "long_term_count": episodic_count + semantic_count + procedural_count,
            "handoff_pending": handoff_pending,
            "by_type": {
                "working_memory": working_memory_count,
                "episodic_memory": episodic_count,
                "semantic_memory": semantic_count,
                "procedural_memory": procedural_count,
                "handoffs_pending": handoff_pending
            },
            "knowledge_cache": knowledge_stats,
            "action_counts": action_counts
        }

    def _get_action_counts(self, user_id: str) -> Dict[str, int]:
        """Get counts by action type (episodic memory only)."""
        pipeline = [
            {"$match": {
                "user_id": user_id
            }},
            {"$group": {"_id": "$action_type", "count": {"$sum": 1}}}
        ]
        results = list(self.episodic.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in results if r["_id"]}

    def clear_session(self, session_id: str) -> Dict[str, int]:
        """Clear all memory for a session from in-memory storage (for testing/demo reset)."""
        # Clear session contexts
        session_deleted = 0
        if session_id in self._session_contexts:
            del self._session_contexts[session_id]
            session_deleted = 1

        # Clear agent working memory
        agent_deleted = 0
        keys_to_delete = [k for k in self._agent_working.keys() if k[0] == session_id]
        for key in keys_to_delete:
            del self._agent_working[key]
            agent_deleted += 1

        # Clear disambiguation
        disambiguation_deleted = 0
        if session_id in self._disambiguations:
            del self._disambiguations[session_id]
            disambiguation_deleted = 1

        # Clear handoffs
        handoff_deleted = 0
        handoff_ids_to_delete = [
            hid for hid, h in self._handoffs.items()
            if h["session_id"] == session_id
        ]
        for hid in handoff_ids_to_delete:
            del self._handoffs[hid]
            handoff_deleted += 1

        return {
            "session_contexts_deleted": session_deleted,
            "agent_working_deleted": agent_deleted,
            "disambiguation_deleted": disambiguation_deleted,
            "handoffs_deleted": handoff_deleted
        }
