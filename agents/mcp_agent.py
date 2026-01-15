"""
MCP Agent - Learning agent that uses Model Context Protocol servers

Handles requests that static tools can't by:
1. Connecting to MCP servers (Tavily via stdio/SSE)
2. Discovering available tools dynamically
3. Using LLM to figure out which tool to use for novel requests
4. Executing solutions via MCP protocol
5. Logging discoveries for developer review
6. Reusing previous discoveries when similar requests come in

Transports:
- stdio (local): Spawns NPX process for reliable local connections
- SSE (remote): Fallback to remote server if stdio fails
"""

import asyncio
import json
import time
from contextlib import AsyncExitStack
from typing import Optional, Dict, List, Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters

from memory.tool_discoveries import ToolDiscoveryStore
from memory.manager import MemoryManager
from shared.config import settings
from shared.llm import LLMService
from shared.logger import get_logger

logger = get_logger("mcp_agent")


class MCPAgent:
    """
    MCP Client Agent - Handles requests that static tools can't.
    Discovers tools from MCP servers, figures out solutions, logs discoveries.
    """

    def __init__(
        self,
        db,
        memory_manager: MemoryManager,
        embedding_fn=None,
        model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize MCP Agent.

        Args:
            db: MongoDB database instance
            memory_manager: Memory manager for context
            embedding_fn: Function to generate embeddings
            model: Claude model to use for solution discovery
        """
        self.db = db
        self.memory = memory_manager
        self.discovery_store = ToolDiscoveryStore(db, embedding_fn=embedding_fn)
        self.llm = LLMService(model=model)

        # MCP state - use AsyncExitStack for proper resource management
        self.exit_stack = AsyncExitStack()
        self.mcp_clients: Dict[str, ClientSession] = {}  # server_name -> ClientSession
        self.available_tools: Dict[str, List[Dict]] = {}  # server_name -> list of tool dicts
        self._initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """
        Connect to configured MCP servers and discover tools.

        Returns:
            Status dict with connection info
        """
        if self._initialized:
            return self.get_status()

        logger.info("Initializing MCP Agent...")

        # Connect to Tavily if API key exists
        if settings.tavily_api_key and settings.tavily_api_key.strip():
            try:
                await self._connect_tavily()
            except Exception as e:
                logger.error(f"Failed to connect to Tavily MCP: {e}")
        else:
            logger.warning("Tavily API key not configured, skipping Tavily connection")

        self._initialized = True
        status = self.get_status()
        logger.info(f"MCP Agent initialized: {status}")
        return status

    async def _connect_tavily(self):
        """Connect to Tavily MCP server - tries stdio (local) first, then SSE (remote)."""
        logger.info("Connecting to Tavily MCP server...")

        # Try stdio (local) first - more reliable, avoids SSE timeout issues
        try:
            await self._connect_tavily_stdio()
            logger.info("✅ Using Tavily MCP via stdio (local NPX)")
            return
        except Exception as e:
            logger.warning(f"Stdio connection failed: {e}")
            logger.info("Falling back to SSE (remote)...")

        # Fall back to SSE (remote) if stdio fails
        await self._connect_tavily_sse()

    async def _connect_tavily_stdio(self):
        """Connect to Tavily MCP server via stdio (local NPX)."""
        logger.debug("Creating stdio client connection...")

        # Create server parameters for NPX process
        # Copy parent environment and add Tavily API key
        import os
        env = os.environ.copy()
        env["TAVILY_API_KEY"] = settings.tavily_api_key

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "tavily-mcp@latest"],
            env=env
        )

        try:
            # Connect via stdio transport
            streams_context = stdio_client(server=server_params)
            read_stream, write_stream = await self.exit_stack.enter_async_context(streams_context)

            # Create session as async context manager (MUST be used this way per MCP SDK docs)
            logger.debug("Creating MCP client session...")
            session = ClientSession(read_stream, write_stream)
            # Enter session context to properly manage lifecycle
            session = await self.exit_stack.enter_async_context(session)
            self.mcp_clients["tavily"] = session

            # Initialize the connection with timeout
            logger.debug("Initializing MCP session (sending initialize request)...")
            try:
                result = await asyncio.wait_for(session.initialize(), timeout=10.0)
                logger.debug(f"MCP initialize result: {result}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for initialize response from Tavily MCP server")
                raise

            # Discover available tools with timeout
            logger.debug("Discovering tools...")
            response = await asyncio.wait_for(
                session.list_tools(),
                timeout=10.0
            )
            self.available_tools["tavily"] = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]

            tool_names = [t['name'] for t in self.available_tools['tavily']]
            logger.info(
                f"✅ Connected to Tavily MCP (stdio): {len(self.available_tools['tavily'])} tools discovered"
            )
            logger.info(f"Tavily tools: {tool_names}")

        except asyncio.TimeoutError:
            logger.error("❌ Timeout during Tavily stdio initialization (>10s)")
            raise Exception("Tavily MCP session initialization timed out")
        except Exception as e:
            logger.error(f"❌ Error connecting to Tavily via stdio: {e}", exc_info=True)
            raise

    async def _connect_tavily_sse(self):
        """Connect to Tavily's remote MCP server via SSE transport."""
        logger.debug("Creating SSE client connection...")

        server_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={settings.tavily_api_key}"

        try:
            # Use AsyncExitStack for proper resource management
            streams_context = sse_client(url=server_url)
            streams = await self.exit_stack.enter_async_context(streams_context)

            # Create and initialize session
            logger.debug("Creating MCP client session...")
            session = ClientSession(*streams)
            self.mcp_clients["tavily"] = await self.exit_stack.enter_async_context(session)

            # Initialize the connection
            logger.debug("Initializing MCP session...")
            await self.mcp_clients["tavily"].initialize()

            # Discover available tools
            logger.debug("Discovering tools...")
            response = await self.mcp_clients["tavily"].list_tools()
            self.available_tools["tavily"] = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]

            tool_names = [t['name'] for t in self.available_tools['tavily']]
            logger.info(
                f"✅ Connected to Tavily MCP (SSE): {len(self.available_tools['tavily'])} tools discovered"
            )
            logger.info(f"Tavily tools: {tool_names}")

        except Exception as e:
            logger.error(f"❌ Error connecting to Tavily via SSE: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Return connection status for UI.

        Returns:
            Dict with initialization status and server info
        """
        return {
            "initialized": self._initialized,
            "servers": {
                name: {
                    "connected": True,
                    "tool_count": len(tools),
                    "tools": [t["name"] for t in tools]
                }
                for name, tools in self.available_tools.items()
            }
        }

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return all discovered tools from all servers.

        Returns:
            List of tool dicts with server field added
        """
        all_tools = []
        for server_name, tools in self.available_tools.items():
            for tool in tools:
                all_tools.append({**tool, "server": server_name})
        return all_tools

    async def handle_request(
        self,
        user_request: str,
        intent: str,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point - handle a request that static tools can't.

        Args:
            user_request: User's request text
            intent: Classified intent (e.g., "web_search", "research")
            context: Optional context dict
            user_id: Optional user identifier

        Returns:
            Dict with: success, result, source, discovery_id, mcp_server,
            tool_used, execution_time_ms, cached (optional)
        """
        start = time.time()

        if not self._initialized:
            logger.warning("MCP Agent not initialized, initializing now...")
            await self.initialize()

        if not self.available_tools:
            return {
                "success": False,
                "error": "No MCP servers connected",
                "source": "failed"
            }

        # 0. Check semantic memory cache FIRST (before making external calls)
        cache_check_info = None
        if user_id and self.memory:
            cache_check_start = time.time()
            logger.debug(f"🔍 Checking semantic cache for user '{user_id}' query: '{user_request[:80]}...'")
            cached_knowledge = self.memory.search_knowledge(
                user_id=user_id,
                query=user_request,
                limit=3
            )
            cache_check_time = int((time.time() - cache_check_start) * 1000)

            # If we have a high-confidence cache hit, return it
            if cached_knowledge and len(cached_knowledge) > 0:
                best_match = cached_knowledge[0]
                cache_score = best_match.get("score", 0)
                cache_threshold = 0.65  # Lowered to catch similar queries (exact matches score ~0.86)
                logger.debug(f"📊 Best cache match score: {cache_score:.3f} (threshold: {cache_threshold})")

                if cache_score >= cache_threshold:
                    logger.info(
                        f"📚 Cache HIT for '{user_request[:50]}...' "
                        f"(score: {cache_score:.2f})"
                    )
                    execution_time = int((time.time() - start) * 1000)

                    # Use summary if available, otherwise full results
                    summary = best_match.get("summary")
                    result_content = best_match.get("result", "")

                    if summary:
                        # Return summary (already pre-computed during caching)
                        cached_results = [summary]
                        logger.debug(f"Returning cached summary ({len(summary)} chars)")
                    else:
                        # No summary available, return full results
                        cached_results = [result_content]
                        logger.debug(f"No summary available, returning full results ({len(result_content)} chars)")

                    return {
                        "success": True,
                        "result": cached_results,
                        "summary": summary,  # Include summary in response for coordinator
                        "source": "knowledge_cache",  # Maps to coordinator's "📚 Found this in my knowledge cache:"
                        "cached": True,
                        "cache_score": cache_score,
                        "cache_check_time_ms": cache_check_time,
                        "original_source": best_match.get("source", "unknown"),
                        "cached_at": best_match.get("created_at"),
                        "execution_time_ms": execution_time
                    }
                else:
                    logger.debug(
                        f"Cache score too low ({cache_score:.2f} < {cache_threshold}), "
                        f"will make fresh search"
                    )
                    cache_check_info = {
                        "checked": True,
                        "hit": False,
                        "score": cache_score,
                        "threshold": cache_threshold,
                        "time_ms": cache_check_time
                    }
            else:
                logger.debug(f"No cache results found for query: '{user_request[:80]}...'")
                cache_check_info = {
                    "checked": True,
                    "hit": False,
                    "score": 0,
                    "threshold": 0.65,
                    "time_ms": cache_check_time
                }
        else:
            if not user_id:
                logger.debug("Skipping cache check: no user_id provided")
            if not self.memory:
                logger.debug("Skipping cache check: no memory manager available")

        # 1. Check for similar previous discovery
        previous = self.discovery_store.find_similar_discovery(
            user_request,
            similarity_threshold=0.85,
            require_success=True
        )

        if previous and previous.get("success"):
            logger.info(f"Reusing previous discovery for: '{user_request[:50]}...'")
            result = await self._execute_solution(previous["solution"])
            result_dict = {
                "success": result.get("success", False),
                "result": result.get("content"),
                "error": result.get("error"),
                "source": "discovery_reuse",
                "discovery_id": str(previous["_id"]),
                "mcp_server": previous["solution"]["mcp_server"],
                "tool_used": previous["solution"]["tool_used"],
                "times_used": previous["times_used"],
                "execution_time_ms": int((time.time() - start) * 1000)
            }
            if cache_check_info:
                result_dict["cache_check_info"] = cache_check_info
            return result_dict

        # 2. Figure out new solution using LLM
        logger.info(f"Figuring out solution for: '{user_request[:50]}...'")
        solution = await self._figure_out_solution(user_request, intent, context)

        if not solution or solution.get("error"):
            return {
                "success": False,
                "error": solution.get("error", "Could not determine how to handle this"),
                "source": "failed"
            }

        # 3. Execute the solution via MCP
        result = await self._execute_solution(solution)
        execution_time = int((time.time() - start) * 1000)
        success = result.get("success", False)

        # 4. Log the discovery to MongoDB
        discovery_id = self.discovery_store.log_discovery(
            user_request=user_request,
            intent=intent,
            solution=solution,
            result_preview=self._truncate_result(result.get("content")),
            success=success,
            execution_time_ms=execution_time,
            user_id=user_id
        )
        logger.info(
            f"Logged discovery {discovery_id}: "
            f"{solution['mcp_server']}.{solution['tool_used']} "
            f"(success={success}, {execution_time}ms)"
        )

        # 5. Cache successful results to semantic memory for future use
        if success and user_id and self.memory and result.get("content"):
            try:
                # Format result content for caching
                content = result.get("content", [])
                if isinstance(content, list):
                    result_text = "\n".join(str(item) for item in content)
                else:
                    result_text = str(content)

                # Summarize results before caching (if long)
                summary = None
                if len(result_text) > 800:
                    summary = await self._summarize_search_results(result_text, user_request)

                # Cache the knowledge with both full results and summary
                self.memory.cache_knowledge(
                    user_id=user_id,
                    query=user_request,
                    results=result_text,
                    summary=summary,
                    source=f"mcp_{solution['mcp_server']}"
                )
                logger.info(
                    f"🆕 Cached new knowledge from {solution['mcp_server']} "
                    f"for query: '{user_request[:50]}...' "
                    f"({'summarized ' if summary else ''})"
                )
            except Exception as e:
                # Don't fail the request if caching fails
                logger.error(f"Failed to cache knowledge: {e}")

        result_dict = {
            "success": success,
            "result": result.get("content"),
            "error": result.get("error"),
            "source": "new_discovery",
            "cached": False,  # This is a new discovery, not from cache
            "discovery_id": discovery_id,
            "mcp_server": solution["mcp_server"],
            "tool_used": solution["tool_used"],
            "execution_time_ms": execution_time
        }

        # Include cache check info if cache was checked
        if cache_check_info:
            result_dict["cache_check_info"] = cache_check_info

        return result_dict

    async def _summarize_search_results(self, search_results: str, query: str) -> str:
        """
        Summarize search results to extract key insights.

        Args:
            search_results: Full search results text (potentially very long)
            query: The original user query

        Returns:
            Concise summary of key findings
        """
        try:
            summary_prompt = f"""Summarize these search results in response to the query: "{query}"

Extract and present:
1. **Key Findings** (2-4 bullet points of the most important insights)
2. **Main Sources** (2-3 most relevant sources with titles/URLs)
3. **Quick Answer** (1-2 sentence direct answer to the query if possible)

Keep it concise and actionable. Focus on what's most relevant to the user's question.

Search Results:
{search_results[:6000]}
"""

            response = await self.llm.agenerate(
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=800,
                temperature=0.3
            )

            summary = response.get("content", "")

            # Add note about full results being cached
            summary += "\n\n*💾 Full search results cached for reference*"

            logger.info(f"📝 Summarized {len(search_results)} chars → {len(summary)} chars")
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize search results: {e}")
            # Fallback to truncated results if summarization fails
            return search_results[:1500] + "\n\n...(truncated)"

    async def _figure_out_solution(
        self,
        user_request: str,
        intent: str,
        context: Optional[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to figure out which MCP tool to use and with what arguments.

        Args:
            user_request: User's request text
            intent: Classified intent
            context: Optional context dict

        Returns:
            Dict with mcp_server, tool_used, arguments, or error
        """
        tools_description = self._format_tools_for_llm()

        prompt = f"""You are an MCP tool selector. Given a user request, determine which MCP tool to use and what arguments to pass.

Available MCP Tools:
{tools_description}

User Request: {user_request}
Intent: {intent}

Guidelines for common intents:
- web_search, research, find_information: Use tavily-search
  - query: the search query string
  - max_results: number of results (default 5, max 10)
  - search_depth: "basic" (faster) or "advanced" (more comprehensive)

- data_extraction, extract_content: Use tavily-extract
  - urls: list of URLs to extract content from

Respond with JSON only (no markdown, no explanation):
{{"mcp_server": "tavily", "tool_used": "tavily-search", "arguments": {{"query": "...", "max_results": 5, "search_depth": "basic"}}}}

If this request cannot be handled by any available tool:
{{"error": "No suitable tool found"}}"""

        try:
            response = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.0  # Deterministic for tool selection
            )

            # Parse JSON from response
            text = response.strip()

            # Handle markdown code blocks
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            solution = json.loads(text)
            logger.debug(f"LLM solution: {solution}")
            return solution

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM solution response: {e}")
            logger.error(f"Response was: {response}")
            return {"error": "Failed to parse solution"}
        except Exception as e:
            logger.error(f"Error figuring out solution: {e}")
            return {"error": str(e)}

    async def _execute_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a solution via MCP protocol.

        Args:
            solution: Dict with mcp_server, tool_used, arguments

        Returns:
            Dict with success, content, error
        """
        return await self._execute_mcp_tool(
            server_name=solution["mcp_server"],
            tool_name=solution["tool_used"],
            arguments=solution.get("arguments", {})
        )

    async def _execute_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Execute a tool via MCP with timeout and error handling.

        Args:
            server_name: Name of MCP server (e.g., "tavily")
            tool_name: Name of tool (e.g., "tavily-search")
            arguments: Tool arguments dict
            timeout_seconds: Timeout in seconds (default 30)

        Returns:
            Dict with success, content, error, raw
        """
        session = self.mcp_clients.get(server_name)
        if not session:
            logger.error(f"Server '{server_name}' not connected")
            return {
                "success": False,
                "error": f"Server '{server_name}' not connected"
            }

        logger.info(f"Executing MCP tool: {server_name}/{tool_name} with args: {arguments}")

        try:
            # Call tool with timeout
            result = await asyncio.wait_for(
                session.call_tool(name=tool_name, arguments=arguments),
                timeout=timeout_seconds
            )

            # Extract content from result
            content = []
            for item in result.content:
                if hasattr(item, 'text'):
                    content.append(item.text)
                elif hasattr(item, 'data'):
                    content.append(item.data)
                else:
                    content.append(str(item))

            logger.info(
                f"MCP tool {server_name}/{tool_name} returned {len(content)} content items"
            )

            return {
                "success": True,
                "content": content,
                "raw": result
            }

        except asyncio.TimeoutError:
            logger.error(f"MCP tool call timed out: {server_name}/{tool_name}")
            return {
                "success": False,
                "error": f"Tool call timed out after {timeout_seconds}s"
            }
        except Exception as e:
            logger.error(f"MCP tool call failed: {server_name}/{tool_name} - {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            }

    def _format_tools_for_llm(self) -> str:
        """
        Format available tools as a string for the LLM prompt.

        Returns:
            Formatted string describing all available tools
        """
        lines = []
        for server, tools in self.available_tools.items():
            lines.append(f"\n## {server.upper()} MCP Server")
            for tool in tools:
                lines.append(f"- **{tool['name']}**: {tool['description']}")
        return "\n".join(lines) if lines else "No tools available"

    def _truncate_result(self, result: Any, max_length: int = 500) -> Optional[str]:
        """
        Truncate result for storage (don't store huge responses).

        Args:
            result: Result to truncate
            max_length: Maximum length in characters

        Returns:
            Truncated string or None
        """
        if result is None:
            return None

        # Handle list of text items
        if isinstance(result, list):
            result = "\n".join(str(item) for item in result)

        text = str(result)
        return text[:max_length] if len(text) > max_length else text

    async def cleanup(self):
        """Clean up all MCP connections."""
        logger.info("Disconnecting MCP agent...")
        await self.exit_stack.aclose()
        self.mcp_clients = {}
        self.available_tools = {}
        self._initialized = False
        logger.info("MCP agent disconnected")

    def __del__(self):
        """Ensure cleanup on deletion."""
        if self._initialized and self.exit_stack:
            # Note: This won't work properly if event loop is closed
            # Prefer explicit cleanup() call
            logger.warning("MCPAgent deleted without explicit cleanup")
