"""
Tool Discovery Store for MCP Agent

Stores successful MCP tool interactions so similar future requests can:
1. Reuse proven solutions (semantic similarity matching)
2. Be reviewed by developers for insights
3. Be promoted to static tools if popular enough

Example flow:
- User: "What's the latest news about AI?"
- MCP Agent discovers: tavily-search with specific params works
- Store this discovery with embedding of user request
- Next user: "Show me recent AI developments"
- Find similar discovery via vector search → reuse solution
"""

from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
from bson import ObjectId

from shared.logger import get_logger

logger = get_logger("tool_discoveries")


class ToolDiscoveryStore:
    """Manages the tool_discoveries collection in MongoDB"""

    def __init__(self, db, embedding_fn=None):
        """
        Initialize the tool discovery store.

        Args:
            db: MongoDB database instance
            embedding_fn: Function to generate embeddings (from shared/embeddings.py)
        """
        self.db = db
        self.collection: Collection = db["tool_discoveries"]
        self.embed = embedding_fn
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for efficient queries"""
        try:
            # Index on times_used for popularity sorting
            self.collection.create_index(
                [("times_used", DESCENDING)],
                name="times_used_desc"
            )
        except OperationFailure:
            pass  # Index already exists

        try:
            # Index on success for filtering
            self.collection.create_index(
                [("success", ASCENDING)],
                name="success_asc"
            )
        except OperationFailure:
            pass

        try:
            # Index on promoted_to_static for filtering
            self.collection.create_index(
                [("promoted_to_static", ASCENDING)],
                name="promoted_asc"
            )
        except OperationFailure:
            pass

        try:
            # Compound index for popular unpromoted discoveries
            self.collection.create_index(
                [
                    ("promoted_to_static", ASCENDING),
                    ("times_used", DESCENDING)
                ],
                name="unpromoted_popular"
            )
        except OperationFailure:
            pass

        try:
            # Index on user_id for user-specific queries
            self.collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_asc"
            )
        except OperationFailure:
            pass

        try:
            # Index on mcp_server and tool for tool-specific queries
            self.collection.create_index(
                [
                    ("solution.mcp_server", ASCENDING),
                    ("solution.tool_used", ASCENDING)
                ],
                name="server_tool"
            )
        except OperationFailure:
            pass

        # Note: Vector search index for request_embedding should be created
        # manually in MongoDB Atlas with name "discovery_vector_index"
        # Path: "request_embedding", Dimensions: 1024, Similarity: cosine

        logger.info("Tool discovery indexes ensured")

    def log_discovery(
        self,
        user_request: str,
        intent: str,
        solution: Dict[str, Any],  # {mcp_server, tool_used, arguments, query_template?}
        result_preview: Any,
        success: bool,
        execution_time_ms: int,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log a newly discovered solution.

        Args:
            user_request: Original user request text
            intent: Extracted intent (e.g., "web_search", "data_extraction")
            solution: Dict with mcp_server, tool_used, arguments, query_template (optional)
            result_preview: Truncated result for review (first 500 chars)
            success: Whether the tool call succeeded
            execution_time_ms: How long the tool took to execute
            user_id: Optional user identifier

        Schema:
        {
            _id: ObjectId,
            user_request: str,
            intent: str,
            request_embedding: list[float],  # 1024-dim Voyage AI vector
            solution: {
                mcp_server: str,
                tool_used: str,
                arguments: dict,
                query_template: str (optional)
            },
            result_preview: any (truncated to 500 chars),
            success: bool,
            execution_time_ms: int,
            times_used: int (starts at 1),
            first_used: datetime,
            last_used: datetime,
            user_id: str (optional),
            promoted_to_static: bool (default false),
            developer_notes: str (default "")
        }

        Returns:
            The inserted document ID as string
        """
        now = datetime.now(timezone.utc)

        # Generate embedding for semantic matching
        request_embedding = None
        if self.embed:
            try:
                request_embedding = self.embed(user_request)
            except Exception as e:
                logger.error(f"Failed to generate embedding for discovery: {e}")

        # Truncate result preview to 500 chars
        if isinstance(result_preview, str):
            preview = result_preview[:500]
        elif isinstance(result_preview, (dict, list)):
            preview = str(result_preview)[:500]
        else:
            preview = str(result_preview)[:500]

        # Ensure solution has required fields
        if not all(k in solution for k in ["mcp_server", "tool_used", "arguments"]):
            logger.error(f"Invalid solution format: {solution}")
            raise ValueError("Solution must contain mcp_server, tool_used, and arguments")

        discovery_doc = {
            "user_request": user_request,
            "intent": intent,
            "request_embedding": request_embedding,
            "solution": {
                "mcp_server": solution["mcp_server"],
                "tool_used": solution["tool_used"],
                "arguments": solution["arguments"],
                "query_template": solution.get("query_template", "")
            },
            "result_preview": preview,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "times_used": 1,
            "first_used": now,
            "last_used": now,
            "promoted_to_static": False,
            "developer_notes": ""
        }

        if user_id:
            discovery_doc["user_id"] = user_id

        result = self.collection.insert_one(discovery_doc)
        discovery_id = str(result.inserted_id)

        logger.info(
            f"Logged discovery {discovery_id}: {solution['mcp_server']}.{solution['tool_used']} "
            f"for intent '{intent}' (success={success}, {execution_time_ms}ms)"
        )

        return discovery_id

    def find_similar_discovery(
        self,
        user_request: str,
        similarity_threshold: float = 0.85,
        require_success: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Find a previously discovered solution for a similar request.
        Uses vector search on request_embedding.

        Args:
            user_request: Current user request to match against
            similarity_threshold: Minimum cosine similarity (0.0-1.0)
            require_success: Only return successful discoveries

        Returns:
            Discovery document if found, None otherwise

        Side effects:
            - Increments times_used on the matched discovery
            - Updates last_used timestamp
        """
        if not self.embed:
            logger.warning("No embedding function available for similarity search")
            return None

        # Generate embedding for user request
        try:
            query_embedding = self.embed(user_request)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return None

        # Vector search pipeline
        # Note: Requires Atlas vector search index named "discovery_vector_index"
        # on the "request_embedding" field
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "discovery_vector_index",
                    "path": "request_embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 50,
                    "limit": 5
                }
            },
            {
                "$addFields": {
                    "similarity_score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        # Filter by success if required
        if require_success:
            pipeline.append({
                "$match": {"success": True}
            })

        # Filter by similarity threshold
        pipeline.append({
            "$match": {"similarity_score": {"$gte": similarity_threshold}}
        })

        # Sort by similarity (highest first)
        pipeline.append({"$sort": {"similarity_score": -1}})

        # Limit to top match
        pipeline.append({"$limit": 1})

        try:
            results = list(self.collection.aggregate(pipeline))

            if not results:
                logger.debug(f"No similar discovery found for: '{user_request[:50]}...'")
                return None

            discovery = results[0]
            discovery_id = discovery["_id"]
            similarity = discovery.get("similarity_score", 0.0)

            logger.info(
                f"Found similar discovery {discovery_id} with {similarity:.2f} similarity: "
                f"{discovery['solution']['mcp_server']}.{discovery['solution']['tool_used']}"
            )

            # Increment usage and update timestamp
            self.collection.update_one(
                {"_id": discovery_id},
                {
                    "$inc": {"times_used": 1},
                    "$set": {"last_used": datetime.now(timezone.utc)}
                }
            )

            # Update the returned doc to reflect new usage
            discovery["times_used"] += 1

            return discovery

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            logger.info("Falling back to exact match search")

            # Fallback: exact text match on user_request
            return self._exact_match_fallback(user_request, require_success)

    def _exact_match_fallback(
        self,
        user_request: str,
        require_success: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Fallback to exact text matching when vector search unavailable"""
        query = {"user_request": user_request}
        if require_success:
            query["success"] = True

        discovery = self.collection.find_one(
            query,
            sort=[("times_used", DESCENDING)]
        )

        if discovery:
            # Increment usage
            self.collection.update_one(
                {"_id": discovery["_id"]},
                {
                    "$inc": {"times_used": 1},
                    "$set": {"last_used": datetime.now(timezone.utc)}
                }
            )
            discovery["times_used"] += 1
            logger.info(f"Exact match found: {discovery['_id']}")

        return discovery

    def get_popular_discoveries(
        self,
        min_uses: int = 2,
        limit: int = 20,
        exclude_promoted: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get discoveries sorted by times_used (descending).
        For developer dashboard and identifying promotion candidates.

        Args:
            min_uses: Minimum times_used threshold
            limit: Maximum results to return
            exclude_promoted: Skip discoveries already promoted to static tools

        Returns:
            List of discovery documents
        """
        query = {
            "times_used": {"$gte": min_uses}
        }

        if exclude_promoted:
            query["promoted_to_static"] = False

        results = list(self.collection.find(query)
            .sort("times_used", DESCENDING)
            .limit(limit))

        logger.info(
            f"Retrieved {len(results)} popular discoveries "
            f"(min_uses={min_uses}, exclude_promoted={exclude_promoted})"
        )

        return results

    def mark_as_promoted(self, discovery_id: str, notes: str = "") -> bool:
        """
        Mark a discovery as promoted to static tool.

        Args:
            discovery_id: MongoDB ObjectId as string
            notes: Optional developer notes about the promotion

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(discovery_id)},
                {
                    "$set": {
                        "promoted_to_static": True,
                        "developer_notes": notes
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Marked discovery {discovery_id} as promoted")
                return True
            else:
                logger.warning(f"Discovery {discovery_id} not found or already promoted")
                return False

        except Exception as e:
            logger.error(f"Failed to mark discovery as promoted: {e}")
            return False

    def add_developer_notes(self, discovery_id: str, notes: str) -> bool:
        """
        Add or update developer notes on a discovery.

        Args:
            discovery_id: MongoDB ObjectId as string
            notes: Developer notes text

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(discovery_id)},
                {"$set": {"developer_notes": notes}}
            )

            if result.modified_count > 0:
                logger.info(f"Added notes to discovery {discovery_id}")
                return True
            else:
                logger.warning(f"Discovery {discovery_id} not found")
                return False

        except Exception as e:
            logger.error(f"Failed to add developer notes: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Return statistics for UI/dashboard.

        Returns:
            {
                total_discoveries: int,
                successful: int,
                failed: int,
                promoted: int,
                avg_uses: float,
                most_used_server: str,
                most_used_tool: str
            }
        """
        total = self.collection.count_documents({})
        successful = self.collection.count_documents({"success": True})
        failed = self.collection.count_documents({"success": False})
        promoted = self.collection.count_documents({"promoted_to_static": True})

        # Calculate average uses
        pipeline = [
            {"$group": {
                "_id": None,
                "avg_uses": {"$avg": "$times_used"}
            }}
        ]
        avg_result = list(self.collection.aggregate(pipeline))
        avg_uses = avg_result[0]["avg_uses"] if avg_result else 0.0

        # Find most used MCP server
        server_pipeline = [
            {"$group": {
                "_id": "$solution.mcp_server",
                "count": {"$sum": "$times_used"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        server_result = list(self.collection.aggregate(server_pipeline))
        most_used_server = server_result[0]["_id"] if server_result else "None"

        # Find most used tool
        tool_pipeline = [
            {"$group": {
                "_id": "$solution.tool_used",
                "count": {"$sum": "$times_used"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        tool_result = list(self.collection.aggregate(tool_pipeline))
        most_used_tool = tool_result[0]["_id"] if tool_result else "None"

        stats = {
            "total_discoveries": total,
            "successful": successful,
            "failed": failed,
            "promoted": promoted,
            "avg_uses": round(avg_uses, 2),
            "most_used_server": most_used_server,
            "most_used_tool": most_used_tool
        }

        logger.debug(f"Discovery stats: {stats}")
        return stats

    def get_discoveries_by_server(self, mcp_server: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get discoveries for a specific MCP server.

        Args:
            mcp_server: Name of MCP server (e.g., "tavily")
            limit: Maximum results

        Returns:
            List of discovery documents
        """
        results = list(self.collection.find(
            {"solution.mcp_server": mcp_server}
        ).sort("times_used", DESCENDING).limit(limit))

        logger.info(f"Retrieved {len(results)} discoveries for server '{mcp_server}'")
        return results

    def get_discoveries_by_intent(self, intent: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get discoveries by intent type.

        Args:
            intent: Intent category (e.g., "web_search", "data_extraction")
            limit: Maximum results

        Returns:
            List of discovery documents
        """
        results = list(self.collection.find(
            {"intent": intent}
        ).sort("times_used", DESCENDING).limit(limit))

        logger.info(f"Retrieved {len(results)} discoveries for intent '{intent}'")
        return results

    def delete_discovery(self, discovery_id: str) -> bool:
        """
        Delete a discovery (for cleanup/testing).

        Args:
            discovery_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(discovery_id)})

            if result.deleted_count > 0:
                logger.info(f"Deleted discovery {discovery_id}")
                return True
            else:
                logger.warning(f"Discovery {discovery_id} not found")
                return False

        except Exception as e:
            logger.error(f"Failed to delete discovery: {e}")
            return False
