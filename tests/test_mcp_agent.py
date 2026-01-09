"""Tests for MCP Agent"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from bson import ObjectId

from agents.mcp_agent import MCPAgent


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    collection = MagicMock()
    db.__getitem__.return_value = collection
    return db


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager"""
    memory = MagicMock()
    return memory


@pytest.fixture
def mock_embedding_fn():
    """Mock embedding function"""
    def embed(text):
        return [0.1] * 1024
    return embed


@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    with patch('agents.mcp_agent.LLMService') as MockLLM:
        mock_llm = MagicMock()
        MockLLM.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def agent(mock_db, mock_memory_manager, mock_embedding_fn):
    """Create MCPAgent with mocked dependencies"""
    with patch('agents.mcp_agent.settings') as mock_settings:
        mock_settings.tavily_api_key = ""  # No key, skip Tavily connection
        agent = MCPAgent(
            db=mock_db,
            memory_manager=mock_memory_manager,
            embedding_fn=mock_embedding_fn
        )
        return agent


class TestMCPAgent:
    """Test suite for MCPAgent"""

    @pytest.mark.asyncio
    async def test_initialize_no_api_key(self, agent):
        """Test initialization when Tavily API key is not set"""
        status = await agent.initialize()

        assert agent._initialized is True
        assert status["initialized"] is True
        assert len(status["servers"]) == 0  # No servers connected

    @pytest.mark.asyncio
    async def test_initialize_with_tavily_key(self, mock_db, mock_memory_manager, mock_embedding_fn):
        """Test initialization with Tavily API key"""
        # Skip this test for now - requires full async mocking of MCP client
        pytest.skip("Skipping full MCP async context manager test")

    @pytest.mark.asyncio
    async def test_get_status(self, agent):
        """Test getting agent status"""
        await agent.initialize()

        status = agent.get_status()

        assert "initialized" in status
        assert "servers" in status
        assert isinstance(status["servers"], dict)

    @pytest.mark.asyncio
    async def test_get_all_tools(self, agent):
        """Test getting all tools from all servers"""
        # Manually add some tools
        agent.available_tools = {
            "tavily": [
                {"name": "tavily-search", "description": "Search"},
                {"name": "tavily-extract", "description": "Extract"}
            ]
        }

        tools = agent.get_all_tools()

        assert len(tools) == 2
        assert all("server" in tool for tool in tools)
        assert tools[0]["server"] == "tavily"

    @pytest.mark.asyncio
    async def test_handle_request_no_servers(self, agent):
        """Test handling request when no servers are connected"""
        await agent.initialize()

        result = await agent.handle_request(
            user_request="Search for AI news",
            intent="web_search"
        )

        assert result["success"] is False
        assert "No MCP servers connected" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_request_reuses_discovery(self, agent, mock_db):
        """Test that similar requests reuse previous discoveries"""
        await agent.initialize()

        # Add a mock server
        agent.available_tools = {"tavily": []}

        # Mock finding similar discovery
        mock_discovery = {
            "_id": ObjectId(),
            "user_request": "Latest AI news",
            "solution": {
                "mcp_server": "tavily",
                "tool_used": "tavily-search",
                "arguments": {"query": "AI news", "max_results": 5}
            },
            "success": True,
            "times_used": 3
        }

        with patch.object(agent.discovery_store, 'find_similar_discovery') as mock_find:
            mock_find.return_value = mock_discovery

            # Mock execute solution
            with patch.object(agent, '_execute_solution') as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "content": ["Result 1", "Result 2"]
                }

                result = await agent.handle_request(
                    user_request="Show me recent AI developments",
                    intent="web_search"
                )

                # Verify discovery was reused
                assert mock_find.called
                assert result["source"] == "discovery_reuse"
                assert result["success"] is True
                assert result["mcp_server"] == "tavily"
                assert result["tool_used"] == "tavily-search"
                assert "times_used" in result

    @pytest.mark.asyncio
    async def test_handle_request_new_discovery(self, agent, mock_db):
        """Test handling request with new discovery"""
        await agent.initialize()

        # Add a mock server
        agent.available_tools = {"tavily": [{"name": "tavily-search", "description": "Search"}]}

        # Mock no similar discovery found
        with patch.object(agent.discovery_store, 'find_similar_discovery') as mock_find:
            mock_find.return_value = None

            # Mock LLM figuring out solution
            with patch.object(agent.llm, 'generate') as mock_generate:
                mock_generate.return_value = json.dumps({
                    "mcp_server": "tavily",
                    "tool_used": "tavily-search",
                    "arguments": {"query": "AI news", "max_results": 5}
                })

                # Mock execute solution
                with patch.object(agent, '_execute_solution') as mock_execute:
                    mock_execute.return_value = {
                        "success": True,
                        "content": ["Search result 1", "Search result 2"]
                    }

                    # Mock log_discovery
                    with patch.object(agent.discovery_store, 'log_discovery') as mock_log:
                        mock_log.return_value = str(ObjectId())

                        result = await agent.handle_request(
                            user_request="What's the latest AI news?",
                            intent="web_search"
                        )

                        # Verify new discovery was created
                        assert result["source"] == "new_discovery"
                        assert result["success"] is True
                        assert mock_log.called

    @pytest.mark.asyncio
    async def test_figure_out_solution_web_search(self, agent):
        """Test LLM figuring out solution for web search"""
        # Mock LLM response
        with patch.object(agent.llm, 'generate') as mock_generate:
            mock_generate.return_value = json.dumps({
                "mcp_server": "tavily",
                "tool_used": "tavily-search",
                "arguments": {
                    "query": "latest AI developments",
                    "max_results": 5,
                    "search_depth": "basic"
                }
            })

            solution = await agent._figure_out_solution(
                user_request="What are the latest AI developments?",
                intent="web_search",
                context=None
            )

            assert solution is not None
            assert solution["mcp_server"] == "tavily"
            assert solution["tool_used"] == "tavily-search"
            assert "query" in solution["arguments"]

    @pytest.mark.asyncio
    async def test_figure_out_solution_handles_markdown(self, agent):
        """Test parsing solution from markdown code block"""
        # Mock LLM response with markdown
        with patch.object(agent.llm, 'generate') as mock_generate:
            mock_generate.return_value = """```json
{
  "mcp_server": "tavily",
  "tool_used": "tavily-search",
  "arguments": {"query": "test"}
}
```"""

            solution = await agent._figure_out_solution(
                user_request="Search for test",
                intent="web_search",
                context=None
            )

            assert solution is not None
            assert solution["mcp_server"] == "tavily"

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_success(self, agent):
        """Test executing MCP tool successfully"""
        # Mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [
            MagicMock(text="Result 1"),
            MagicMock(text="Result 2")
        ]
        mock_session.call_tool.return_value = mock_result

        agent.mcp_clients["tavily"] = mock_session

        result = await agent._execute_mcp_tool(
            server_name="tavily",
            tool_name="tavily-search",
            arguments={"query": "test"}
        )

        assert result["success"] is True
        assert len(result["content"]) == 2
        assert result["content"][0] == "Result 1"

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_timeout(self, agent):
        """Test MCP tool timeout handling"""
        # Mock session that times out
        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = asyncio.TimeoutError()

        agent.mcp_clients["tavily"] = mock_session

        result = await agent._execute_mcp_tool(
            server_name="tavily",
            tool_name="tavily-search",
            arguments={"query": "test"},
            timeout_seconds=1.0
        )

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_error(self, agent):
        """Test MCP tool error handling"""
        # Mock session that raises error
        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = Exception("Connection failed")

        agent.mcp_clients["tavily"] = mock_session

        result = await agent._execute_mcp_tool(
            server_name="tavily",
            tool_name="tavily-search",
            arguments={"query": "test"}
        )

        assert result["success"] is False
        assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_server_not_connected(self, agent):
        """Test executing tool on non-existent server"""
        result = await agent._execute_mcp_tool(
            server_name="nonexistent",
            tool_name="some-tool",
            arguments={}
        )

        assert result["success"] is False
        assert "not connected" in result["error"]

    def test_format_tools_for_llm(self, agent):
        """Test formatting tools for LLM prompt"""
        agent.available_tools = {
            "tavily": [
                {"name": "tavily-search", "description": "Search the web"},
                {"name": "tavily-extract", "description": "Extract content"}
            ]
        }

        formatted = agent._format_tools_for_llm()

        assert "TAVILY" in formatted
        assert "tavily-search" in formatted
        assert "Search the web" in formatted

    def test_format_tools_for_llm_empty(self, agent):
        """Test formatting when no tools available"""
        agent.available_tools = {}

        formatted = agent._format_tools_for_llm()

        assert "No tools available" in formatted

    def test_truncate_result_string(self, agent):
        """Test truncating string results"""
        long_text = "x" * 1000
        truncated = agent._truncate_result(long_text, max_length=500)

        assert len(truncated) == 500

    def test_truncate_result_list(self, agent):
        """Test truncating list results"""
        result_list = ["Result 1", "Result 2", "Result 3"]
        truncated = agent._truncate_result(result_list, max_length=50)

        assert isinstance(truncated, str)
        assert len(truncated) <= 50

    def test_truncate_result_none(self, agent):
        """Test truncating None"""
        truncated = agent._truncate_result(None)

        assert truncated is None

    @pytest.mark.asyncio
    async def test_cleanup(self, agent):
        """Test cleanup disconnects properly"""
        agent._initialized = True
        agent.available_tools = {"tavily": []}
        agent.mcp_clients = {"tavily": MagicMock()}

        await agent.cleanup()

        assert agent._initialized is False
        assert len(agent.mcp_clients) == 0
        assert len(agent.available_tools) == 0


# Import json for test that needs it
import json
