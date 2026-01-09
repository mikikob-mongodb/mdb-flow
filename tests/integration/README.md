# Integration Tests

Integration tests for Flow Companion that test real external services and end-to-end workflows.

## MCP Agent Integration Tests

Tests in `test_mcp_agent.py` verify the MCP Agent's integration with Tavily's remote MCP server.

### Requirements

1. **Tavily API Key**: Set `TAVILY_API_KEY` environment variable
   ```bash
   export TAVILY_API_KEY=your-tavily-api-key
   ```

2. **Active Internet Connection**: Tests make real API calls to Tavily

3. **MongoDB Instance**: For discovery storage (can be mocked)

### Running the Tests

**Run all MCP Agent integration tests:**
```bash
pytest tests/integration/test_mcp_agent.py -v
```

**Run with output visible:**
```bash
pytest tests/integration/test_mcp_agent.py -v -s
```

**Run specific test:**
```bash
pytest tests/integration/test_mcp_agent.py::TestMCPAgentWebSearch::test_basic_web_search -v -s
```

**Skip if no API key:**
All tests automatically skip if `TAVILY_API_KEY` is not set.

### Test Coverage

**Initialization (2 tests)**
- ✅ Tavily connection successful
- ✅ Tools discovered from Tavily server

**Web Search (2 tests)**
- ✅ Basic web search via MCP
- ✅ Research intent routing

**Discovery Reuse (2 tests)**
- ✅ Discovery logging to database
- ✅ Similar query reuse

**Knowledge Cache (1 test)**
- ✅ Search results cached in memory

**Error Handling (2 tests)**
- ✅ Empty query handling
- ✅ No servers connected error

**Cleanup (1 test)**
- ✅ Proper resource cleanup

**Performance (1 test)**
- ✅ Search performance benchmark (<10s)

### Note on Mocked Database

Tests use a mocked MongoDB database, so discovery reuse and knowledge caching tests verify the *logic* but don't test actual persistence. For full end-to-end testing with real MongoDB, update the fixtures to use a real test database.

### Example Output

```
tests/integration/test_mcp_agent.py::TestMCPAgentInitialization::test_tavily_connection PASSED
✓ Connected to Tavily with 4 tools

tests/integration/test_mcp_agent.py::TestMCPAgentWebSearch::test_basic_web_search PASSED
✓ Search completed in 1234ms
✓ Source: new_discovery
✓ Results: 5 items
```

## Other Integration Tests

- `test_compression_integration.py`: Tests context compression with real LLM calls
- `test_multiturn_conversations.py`: Tests multi-turn conversation handling
- `memory/`: Memory system integration tests
