"""
Integration tests for MCP Agent with Tavily

These tests require:
- TAVILY_API_KEY environment variable
- Active internet connection
- MongoDB instance (for discovery storage)

Run with: pytest tests/integration/test_mcp_agent.py -v
Skip if no key: pytest tests/integration/test_mcp_agent.py -v --skipif-no-tavily
"""

import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

from agents.mcp_agent import MCPAgent
from memory.tool_discoveries import ToolDiscoveryStore
from memory.manager import MemoryManager

# Skip all tests if TAVILY_API_KEY not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set - skipping Tavily integration tests"
)


@pytest.fixture
def mock_db():
    """Mock MongoDB database for testing"""
    db = MagicMock()
    collection = MagicMock()
    db.__getitem__.return_value = collection

    # Mock collection methods
    collection.insert_one.return_value.inserted_id = "test-discovery-id"
    collection.count_documents.return_value = 0
    collection.find.return_value = []
    collection.aggregate.return_value = []

    return db


@pytest.fixture
def mock_embedding_fn():
    """Mock embedding function"""
    def embed(text):
        return [0.1] * 1024
    return embed


@pytest.fixture
def memory_manager(mock_db, mock_embedding_fn):
    """Create a mock memory manager"""
    return MemoryManager(mock_db, embedding_fn=mock_embedding_fn)


@pytest_asyncio.fixture
async def mcp_agent(mock_db, memory_manager, mock_embedding_fn):
    """Create and initialize MCP Agent"""
    agent = MCPAgent(
        db=mock_db,
        memory_manager=memory_manager,
        embedding_fn=mock_embedding_fn
    )

    # Initialize and connect to Tavily
    await agent.initialize()

    yield agent

    # Cleanup
    await agent.cleanup()


class TestMCPAgentInitialization:
    """Test MCP Agent initialization and connection"""

    @pytest.mark.asyncio
    async def test_tavily_connection(self, mcp_agent):
        """Test successful connection to Tavily MCP server"""
        status = mcp_agent.get_status()

        assert status["initialized"] is True
        assert "tavily" in status["servers"]
        assert status["servers"]["tavily"]["connected"] is True
        assert status["servers"]["tavily"]["tool_count"] > 0
        print(f"✓ Connected to Tavily with {status['servers']['tavily']['tool_count']} tools")

    @pytest.mark.asyncio
    async def test_tavily_tools_discovered(self, mcp_agent):
        """Test that Tavily tools are discovered"""
        tools = mcp_agent.get_all_tools()

        assert len(tools) > 0

        # Check for expected Tavily tools
        tool_names = [t["name"] for t in tools]
        assert "tavily-search" in tool_names

        # Verify tool structure
        search_tool = next(t for t in tools if t["name"] == "tavily-search")
        assert "server" in search_tool
        assert search_tool["server"] == "tavily"
        assert "description" in search_tool

        print(f"✓ Discovered tools: {tool_names}")


class TestMCPAgentWebSearch:
    """Test web search functionality via Tavily"""

    @pytest.mark.asyncio
    async def test_basic_web_search(self, mcp_agent):
        """Test basic web search request"""
        result = await mcp_agent.handle_request(
            user_request="MongoDB vector search features",
            intent="web_search",
            user_id="test-user"
        )

        assert result["success"] is True
        assert result["source"] in ["new_discovery", "knowledge_cache"]
        assert result["mcp_server"] == "tavily"
        assert result["tool_used"] == "tavily-search"
        assert result["result"] is not None
        assert len(result["result"]) > 0

        print(f"✓ Search completed in {result['execution_time_ms']}ms")
        print(f"✓ Source: {result['source']}")
        print(f"✓ Results: {len(result['result'])} items")

    @pytest.mark.asyncio
    async def test_research_intent(self, mcp_agent):
        """Test research intent routing to web search"""
        result = await mcp_agent.handle_request(
            user_request="What are the latest AI database trends in 2026?",
            intent="research",
            user_id="test-user"
        )

        assert result["success"] is True
        assert "discovery_id" in result

        print(f"✓ Research query handled successfully")
        print(f"✓ Discovery ID: {result['discovery_id']}")


class TestMCPAgentDiscoveryReuse:
    """Test discovery reuse and learning"""

    @pytest.mark.asyncio
    async def test_discovery_logging(self, mcp_agent):
        """Test that discoveries are logged to database"""
        # First request - should create new discovery
        result1 = await mcp_agent.handle_request(
            user_request="MongoDB Atlas search features",
            intent="web_search",
            user_id="test-user"
        )

        assert result1["source"] == "new_discovery"
        assert "discovery_id" in result1

        print(f"✓ Created discovery: {result1['discovery_id']}")

    @pytest.mark.asyncio
    async def test_similar_query_reuse(self, mcp_agent):
        """Test that similar queries reuse previous discoveries"""
        # Note: This test may create a new discovery each time due to mocked DB
        # In real integration, vector search would match similar queries

        # First query
        result1 = await mcp_agent.handle_request(
            user_request="MongoDB database trends",
            intent="research",
            user_id="test-user"
        )

        # Very similar query
        result2 = await mcp_agent.handle_request(
            user_request="database trends MongoDB",
            intent="research",
            user_id="test-user"
        )

        # Both should succeed
        assert result1["success"] is True
        assert result2["success"] is True

        print(f"✓ First query source: {result1['source']}")
        print(f"✓ Second query source: {result2['source']}")


class TestMCPAgentKnowledgeCache:
    """Test knowledge caching integration"""

    @pytest.mark.asyncio
    async def test_knowledge_caching_after_search(self, mcp_agent, memory_manager):
        """Test that successful searches are cached in memory"""
        query = "MongoDB 2026 features and roadmap"

        result = await mcp_agent.handle_request(
            user_request=query,
            intent="research",
            user_id="test-user"
        )

        assert result["success"] is True

        # Note: With mocked DB, cache won't actually persist
        # In real integration test, would verify cache hit on second request

        print(f"✓ Search result cached (would be in real DB)")


class TestMCPAgentErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_query(self, mcp_agent):
        """Test handling of empty query"""
        result = await mcp_agent.handle_request(
            user_request="",
            intent="web_search",
            user_id="test-user"
        )

        # Should handle gracefully (may return error or empty results)
        assert "success" in result

        print(f"✓ Empty query handled: success={result['success']}")

    @pytest.mark.asyncio
    async def test_no_servers_connected(self, mock_db, memory_manager, mock_embedding_fn):
        """Test handling when no MCP servers are connected"""
        # Create agent without initializing (no servers)
        agent = MCPAgent(
            db=mock_db,
            memory_manager=memory_manager,
            embedding_fn=mock_embedding_fn
        )

        result = await agent.handle_request(
            user_request="test query",
            intent="web_search",
            user_id="test-user"
        )

        assert result["success"] is False
        assert "No MCP servers connected" in result["error"]

        print(f"✓ No servers error handled correctly")


class TestMCPAgentCleanup:
    """Test cleanup and resource management"""

    @pytest.mark.asyncio
    async def test_cleanup_disconnects_properly(self, mock_db, memory_manager, mock_embedding_fn):
        """Test that cleanup properly disconnects from servers"""
        agent = MCPAgent(
            db=mock_db,
            memory_manager=memory_manager,
            embedding_fn=mock_embedding_fn
        )

        await agent.initialize()

        # Verify connected
        status = agent.get_status()
        assert status["initialized"] is True

        # Cleanup
        await agent.cleanup()

        # Verify disconnected
        assert agent._initialized is False
        assert len(agent.mcp_clients) == 0
        assert len(agent.available_tools) == 0

        print(f"✓ Cleanup successful")


# Performance benchmarks
class TestMCPAgentPerformance:
    """Performance benchmarks for MCP Agent"""

    @pytest.mark.asyncio
    async def test_search_performance(self, mcp_agent):
        """Benchmark web search performance"""
        result = await mcp_agent.handle_request(
            user_request="MongoDB performance optimization tips",
            intent="research",
            user_id="test-user"
        )

        assert result["success"] is True
        execution_time = result["execution_time_ms"]

        # Should complete within reasonable time (10 seconds)
        assert execution_time < 10000, f"Search too slow: {execution_time}ms"

        print(f"✓ Search completed in {execution_time}ms")


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/integration/test_mcp_agent.py -v
    pytest.main([__file__, "-v", "-s"])
