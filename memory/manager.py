"""Agent Memory Manager for Flow Companion.

Manages three types of memory:
- Short-term: Session context, working memory (TTL: 2 hours)
- Long-term: Episodic memory, learned facts (persistent)
- Shared: Agent-to-agent handoffs (TTL: 5 minutes)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
import time


class MemoryManager:
    """
    Manages agent memory across three types:
    - Short-term: Session context, working memory (TTL: 2 hours)
    - Long-term: Episodic memory, learned facts (persistent)
    - Shared: Agent-to-agent handoffs (TTL: 5 minutes)
    """

    def __init__(self, db, embedding_fn=None):
        """Initialize memory manager.

        Args:
            db: MongoDB database instance
            embedding_fn: Optional embedding function (Voyage AI)
        """
        self.db = db
        self.short_term = db.short_term_memory
        self.long_term = db.long_term_memory
        self.shared = db.shared_memory
        self.embed = embedding_fn  # Voyage embedding function

        # Timing tracking for debug panel
        self.last_read_ms = 0
        self.last_write_ms = 0

    # ==================== SHORT-TERM MEMORY ====================

    def write_short_term(
        self,
        session_id: str,
        agent: str,
        content: Dict[str, Any],
        ttl_hours: int = 2
    ) -> ObjectId:
        """Write to short-term memory (session context).

        Args:
            session_id: Session identifier
            agent: Agent name (e.g., "coordinator", "worklog", "retrieval")
            content: Memory content dict
            ttl_hours: Time-to-live in hours (default: 2)

        Returns:
            Inserted document ID
        """
        start = time.time()

        doc = {
            "session_id": session_id,
            "agent": agent,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=ttl_hours)
        }

        result = self.short_term.insert_one(doc)
        self.last_write_ms = (time.time() - start) * 1000

        return result.inserted_id

    def read_short_term(
        self,
        session_id: str,
        agent: Optional[str] = None
    ) -> List[Dict]:
        """Read short-term memory for a session.

        Args:
            session_id: Session identifier
            agent: Optional agent filter

        Returns:
            List of memory documents (most recent first)
        """
        start = time.time()

        query = {"session_id": session_id}
        if agent:
            query["agent"] = agent

        results = list(self.short_term.find(query).sort("created_at", -1))
        self.last_read_ms = (time.time() - start) * 1000

        return results

    def update_short_term(
        self,
        session_id: str,
        agent: str,
        content: Dict[str, Any]
    ) -> bool:
        """Update or insert short-term memory (upsert).

        Args:
            session_id: Session identifier
            agent: Agent name
            content: Memory content dict

        Returns:
            True if updated/inserted
        """
        start = time.time()

        result = self.short_term.update_one(
            {"session_id": session_id, "agent": agent},
            {
                "$set": {
                    "content": content,
                    "updated_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=2)
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        self.last_write_ms = (time.time() - start) * 1000
        return result.modified_count > 0 or result.upserted_id is not None

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get aggregated context from short-term memory.

        Extracts common context keys:
        - current_project
        - current_task
        - last_action
        - last_search_results
        - conversation_goal

        Args:
            session_id: Session identifier

        Returns:
            Aggregated context dict
        """
        memories = self.read_short_term(session_id)

        context = {
            "current_project": None,
            "current_task": None,
            "last_action": None,
            "last_search_results": [],
            "conversation_goal": None
        }

        for mem in memories:
            content = mem.get("content", {})
            for key in context:
                if content.get(key):
                    context[key] = content[key]

        return context

    # ==================== LONG-TERM MEMORY ====================

    def write_long_term(
        self,
        user_id: str,
        memory_type: str,  # "action", "fact", "preference"
        content: Dict[str, Any],
        tags: List[str] = None
    ) -> ObjectId:
        """Write to long-term memory (persistent).

        Args:
            user_id: User identifier
            memory_type: Type ("action", "fact", "preference")
            content: Memory content dict
            tags: Optional tags for categorization

        Returns:
            Inserted document ID
        """
        start = time.time()

        # Generate embedding for semantic retrieval
        text_for_embedding = self._content_to_text(content)
        embedding = self.embed(text_for_embedding) if self.embed else None

        doc = {
            "user_id": user_id,
            "type": memory_type,
            "content": content,
            "tags": tags or [],
            "embedding": embedding,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "access_count": 0,
            "strength": 1.0  # For memory decay algorithms
        }

        result = self.long_term.insert_one(doc)
        self.last_write_ms = (time.time() - start) * 1000

        return result.inserted_id

    def read_long_term(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Read long-term memories by type.

        Automatically updates access metadata (last_accessed, access_count).

        Args:
            user_id: User identifier
            memory_type: Optional filter by type
            limit: Maximum number of results

        Returns:
            List of memory documents (most recently accessed first)
        """
        start = time.time()

        query = {"user_id": user_id}
        if memory_type:
            query["type"] = memory_type

        results = list(
            self.long_term.find(query)
            .sort("last_accessed", -1)
            .limit(limit)
        )

        # Update access metadata
        ids = [r["_id"] for r in results]
        if ids:
            self.long_term.update_many(
                {"_id": {"$in": ids}},
                {
                    "$set": {"last_accessed": datetime.utcnow()},
                    "$inc": {"access_count": 1}
                }
            )

        self.last_read_ms = (time.time() - start) * 1000
        return results

    def search_long_term(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Semantic search over long-term memories using vector embeddings.

        Args:
            user_id: User identifier
            query: Search query text
            limit: Maximum number of results

        Returns:
            List of memory documents with similarity scores
        """
        if not self.embed:
            return []

        start = time.time()
        query_embedding = self.embed(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "memory_embeddings",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,
                    "limit": limit,
                    "filter": {"user_id": user_id}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "type": 1,
                    "content": 1,
                    "created_at": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(self.long_term.aggregate(pipeline))
        self.last_read_ms = (time.time() - start) * 1000

        return results

    # ==================== SHARED MEMORY ====================

    def write_shared(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        ttl_minutes: int = 5
    ) -> ObjectId:
        """Write to shared memory for agent handoff.

        Args:
            session_id: Session identifier
            from_agent: Source agent name
            to_agent: Target agent name
            content: Handoff content dict
            ttl_minutes: Time-to-live in minutes (default: 5)

        Returns:
            Inserted document ID
        """
        start = time.time()

        doc = {
            "session_id": session_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=ttl_minutes)
        }

        result = self.shared.insert_one(doc)
        self.last_write_ms = (time.time() - start) * 1000

        return result.inserted_id

    def read_shared(
        self,
        session_id: str,
        to_agent: str,
        consume: bool = True
    ) -> Optional[Dict]:
        """Read shared memory addressed to an agent.

        Uses atomic find_one_and_update to prevent race conditions.

        Args:
            session_id: Session identifier
            to_agent: Target agent name
            consume: Whether to mark as consumed (default: True)

        Returns:
            Handoff document or None
        """
        start = time.time()

        query = {
            "session_id": session_id,
            "to_agent": to_agent,
            "status": "pending"
        }

        if consume:
            # Atomically read and mark as consumed
            result = self.shared.find_one_and_update(
                query,
                {"$set": {"status": "consumed", "consumed_at": datetime.utcnow()}},
                sort=[("created_at", -1)]
            )
        else:
            result = self.shared.find_one(query, sort=[("created_at", -1)])

        self.last_read_ms = (time.time() - start) * 1000
        return result

    # ==================== HELPERS ====================

    def _content_to_text(self, content: Dict) -> str:
        """Convert content dict to text for embedding.

        Args:
            content: Content dictionary

        Returns:
            Text representation for embedding
        """
        parts = []
        for key, value in content.items():
            if isinstance(value, str):
                parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                parts.append(f"{key}: {value.get('title', value.get('name', str(value)))}")
        return " | ".join(parts)

    def get_timing(self) -> Dict[str, float]:
        """Get last operation timings for debug panel.

        Returns:
            Dict with read_ms and write_ms
        """
        return {
            "read_ms": self.last_read_ms,
            "write_ms": self.last_write_ms
        }

    def clear_session(self, session_id: str):
        """Clear all memory for a session.

        Args:
            session_id: Session identifier to clear
        """
        self.short_term.delete_many({"session_id": session_id})
        self.shared.delete_many({"session_id": session_id})

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "short_term": {
                "total": self.short_term.count_documents({}),
                "by_session": {}  # Could be expanded
            },
            "long_term": {
                "total": self.long_term.count_documents({}),
                "by_type": {
                    "action": self.long_term.count_documents({"type": "action"}),
                    "fact": self.long_term.count_documents({"type": "fact"}),
                    "preference": self.long_term.count_documents({"type": "preference"})
                }
            },
            "shared": {
                "total": self.shared.count_documents({}),
                "pending": self.shared.count_documents({"status": "pending"}),
                "consumed": self.shared.count_documents({"status": "consumed"})
            }
        }
