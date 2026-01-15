# MCP Agent - Dynamic Tool Discovery and Learning

**Version:** 1.0 (Milestone 6)
**Status:** 🧪 Experimental

The MCP Agent extends Flow Companion's capabilities by connecting to external Model Context Protocol (MCP) servers, enabling dynamic tool discovery and intelligent solution reuse.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Connected Servers](#connected-servers)
- [Discovery Learning](#discovery-learning)
- [Knowledge Cache](#knowledge-cache)
- [Configuration](#configuration)
- [Usage](#usage)
- [Developer Insights](#developer-insights)
- [Testing](#testing)

---

## Overview

The MCP Agent handles requests that static tools can't by:
1. Connecting to MCP servers (Tavily for web search)
2. Discovering available tools dynamically
3. Using LLM to figure out which tool to use for novel requests
4. Executing solutions via MCP protocol
5. Logging discoveries for developer review and future reuse
6. Caching knowledge to avoid redundant API calls

**Key Benefits:**
- **Extensibility** - Add new capabilities without code changes
- **Learning** - Agent improves over time by reusing solutions
- **Transparency** - All discoveries logged for developer review
- **Performance** - Knowledge cache reduces API calls

---

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 🧪 Experimental Section                          │   │
│  │ - MCP Mode Toggle                                │   │
│  │ - MCP Servers Status                             │   │
│  │ - Knowledge Cache Stats                          │   │
│  │ - Tool Discoveries Viewer                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Coordinator Agent                          │
│  - Intent Classification (_classify_intent)             │
│  - Static Tool Routing (_can_static_tools_handle)       │
│  - MCP Routing (if enabled and applicable)              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  MCP Agent                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Check Knowledge Cache (7-day TTL)            │   │
│  │ 2. Find Similar Discovery (vector search)       │   │
│  │ 3. Figure Out Solution (LLM + tools)             │   │
│  │ 4. Execute via MCP Protocol                      │   │
│  │ 5. Log Discovery                                 │   │
│  │ 6. Cache Knowledge                               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
            ↓                                ↓
┌───────────────────────┐      ┌───────────────────────────┐
│  Tool Discovery Store │      │   Memory Manager          │
│  - log_discovery()    │      │   - cache_knowledge()     │
│  - find_similar()     │      │   - get_cached_knowledge()│
│  - get_popular()      │      │   - search_knowledge()    │
└───────────────────────┘      └───────────────────────────┘
            ↓                                ↓
┌─────────────────────────────────────────────────────────┐
│              MongoDB Atlas                              │
│  - tool_discoveries (with vector index)                 │
│  - long_term_memory (knowledge cache)                   │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│           MCP Servers (External)                        │
│  - Tavily (Stdio Local, fallback to SSE Remote)         │
│  - MongoDB MCP (Stdio Local - Optional)                 │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request: "What's the latest AI news?"
     ↓
Coordinator classifies intent: "web_search"
     ↓
Static tools can't handle → Route to MCP Agent
     ↓
MCP Agent:
  1. Check knowledge cache → MISS
  2. Check similar discovery → MISS
  3. Figure out solution:
     - LLM analyzes request + available tools
     - Returns: {mcp_server: "tavily", tool_used: "tavily-search", arguments: {...}}
  4. Execute via MCP:
     - session.call_tool("tavily-search", {...})
     - Get results
  5. Log discovery to tool_discoveries
  6. Cache knowledge to long_term_memory
     ↓
Return results to user with source indicator (🆕 New Discovery)
```

**Next Similar Request:** "AI news"
```
User Request: "AI news"
     ↓
MCP Agent:
  1. Check knowledge cache → HIT (semantic similarity 0.87)
  2. Return cached results
     ↓
Return results with source indicator (📚 Knowledge Cache)
```

**Subsequent Similar Request:** "Show me recent AI developments"
```
User Request: "Show me recent AI developments"
     ↓
MCP Agent:
  1. Check knowledge cache → MISS (expired or low similarity)
  2. Check similar discovery → HIT (similarity 0.88)
  3. Reuse solution from previous discovery
  4. Execute via MCP
  5. Update times_used counter
     ↓
Return results with source indicator (🔄 Discovery Reuse)
```

---

## How It Works

### 1. Intent Classification

The Coordinator classifies user intent before routing:

```python
intent = coordinator._classify_intent(user_message)

# Static tool intents (handled normally):
# - create_task, update_task, complete_task, start_task, stop_task
# - create_project, update_project
# - list_tasks, search_tasks, get_history

# MCP intents (routed to MCP if enabled):
# - research, web_search, find_information
# - complex_query, aggregation, data_extraction
# - unknown
```

### 2. MCP Routing

If static tools can't handle and MCP mode is enabled:

```python
if not coordinator._can_static_tools_handle(intent, user_message):
    if not mcp_mode_enabled:
        return "Enable MCP Mode to handle this request"

    # Route to MCP Agent
    result = await mcp_agent.handle_request(
        user_request=user_message,
        intent=intent,
        context=session_context,
        user_id=user_id
    )
```

### 3. Solution Discovery

MCP Agent uses LLM to figure out which tool to use:

```python
# Prompt includes available tools from all connected servers
prompt = f"""
Available MCP Tools:
{tools_description}

User Request: {user_request}
Intent: {intent}

Respond with JSON:
{{"mcp_server": "tavily", "tool_used": "tavily-search", "arguments": {{...}}}}
"""

solution = llm.generate(prompt, temperature=0.0)  # Deterministic
```

### 4. MCP Execution

Execute tool via MCP protocol:

```python
result = await asyncio.wait_for(
    session.call_tool(name="tavily-search", arguments=arguments),
    timeout=30.0
)

content = [item.text for item in result.content if hasattr(item, 'text')]
```

### 5. Discovery Logging

All solutions logged to MongoDB:

```python
discovery_id = discovery_store.log_discovery(
    user_request=user_request,
    intent=intent,
    solution={
        "mcp_server": "tavily",
        "tool_used": "tavily-search",
        "arguments": {"query": "...", "max_results": 5}
    },
    result_preview=truncated_result,
    success=True,
    execution_time_ms=850
)
```

---

## Connected Servers

### Tavily (Stdio Primary, SSE Fallback)

**Transport:** Stdio (local NPX process) with SSE fallback
**Tools:**
- `tavily-search` - Web search with AI-optimized results
- `tavily-extract` - Extract content from URLs
- `tavily-map` - Website structure mapping
- `tavily-crawl` - Systematic website crawling

**Configuration:**
```bash
TAVILY_API_KEY=your-key-here
```

**Connection Strategy:**
1. **Primary (Stdio):** Spawns `npx -y tavily-mcp@latest` as local process
   - More reliable, avoids SSE timeout issues
   - Requires Node.js/NPX installed
2. **Fallback (SSE):** Connects to `https://mcp.tavily.com/mcp/?tavilyApiKey=XXX`
   - Used if stdio connection fails
   - Subject to known SSE comment parsing issues

**Connection Code (Stdio):**
```python
streams = await stdio_client(
    command="npx",
    args=["-y", "tavily-mcp@latest"],
    env={"TAVILY_API_KEY": settings.tavily_api_key}
)
session = ClientSession(*streams)
await session.initialize()
tools = await session.list_tools()
```

### MongoDB MCP (Local Docker - Optional)

**Note:** Not yet implemented. Planned for future milestone.

**Transport:** Stdio (subprocess)
**Tools:** Dynamic database queries, aggregations
**Configuration:**
```bash
MONGODB_MCP_ENABLED=false  # Set true when available
```

---

## Discovery Learning

### Schema: `tool_discoveries`

```javascript
{
  _id: ObjectId("..."),
  user_request: "What's the latest AI news?",
  intent: "web_search",
  request_embedding: [0.123, -0.456, ...],  // 1024-dim Voyage AI
  solution: {
    mcp_server: "tavily",
    tool_used: "tavily-search",
    arguments: {
      query: "latest AI news",
      max_results: 5,
      search_depth: "basic"
    }
  },
  result_preview: "Recent AI developments include...",  // Truncated to 500 chars
  success: true,
  execution_time_ms: 850,
  times_used: 5,
  first_used: ISODate("2026-01-08T10:00:00Z"),
  last_used: ISODate("2026-01-08T14:30:00Z"),
  user_id: "demo_user",
  promoted_to_static: false,
  developer_notes: ""
}
```

### Vector Search Index

**Name:** `discovery_vector_index`
**Field:** `request_embedding`
**Dimensions:** 1024
**Similarity:** cosine

### Finding Similar Discoveries

```python
# Semantic similarity search
previous = discovery_store.find_similar_discovery(
    user_request="AI news",
    similarity_threshold=0.85,  # Configurable
    require_success=True
)

# If found and success=true:
# - Reuse solution
# - Increment times_used
# - Update last_used timestamp
```

### Developer Workflow

```python
# Get popular discoveries (promotion candidates)
popular = discovery_store.get_popular_discoveries(
    min_uses=5,
    exclude_promoted=True,
    limit=20
)

# Mark as promoted
discovery_store.mark_as_promoted(
    discovery_id="...",
    notes="Promoted to static web_search tool"
)

# Add developer notes
discovery_store.add_developer_notes(
    discovery_id="...",
    notes="Users frequently ask about AI trends"
)
```

---

## Knowledge Cache

### Schema: `long_term_memory` (semantic.knowledge)

```javascript
{
  user_id: "demo_user",
  memory_type: "semantic",
  semantic_type: "knowledge",
  query: "latest AI news",
  results: ["Article 1...", "Article 2..."],  // Full search results
  source: "tavily",
  embedding: [0.1, -0.2, ...],  // 1024-dim
  fetched_at: ISODate("2026-01-08T10:00:00Z"),
  expires_at: ISODate("2026-01-15T10:00:00Z"),  // 7-day TTL
  times_accessed: 3,
  last_accessed: ISODate("2026-01-08T14:30:00Z"),
  created_at: ISODate("2026-01-08T10:00:00Z")
}
```

### Cache Behavior

**Cache Hit (< 7 days old, high similarity):**
```python
cached = memory.get_cached_knowledge(
    user_id="demo_user",
    query="AI news",
    similarity_threshold=0.85
)

if cached:
    # Return immediately, no API call
    return {
        "success": True,
        "result": cached["results"],
        "source": "knowledge_cache",
        "cached_at": cached["fetched_at"]
    }
```

**Cache Miss:**
- Execute MCP search
- Cache results with 7-day expiration
- Return fresh results

**Benefits:**
- Reduces redundant API calls (saves cost)
- Improves response time (instant cache hits)
- Preserves fresh context (7-day TTL configurable)

---

## Configuration

### Environment Variables (.env)

```bash
# Required for MCP Mode
TAVILY_API_KEY=your-tavily-api-key

# Optional: Enable MongoDB MCP server (not yet implemented)
MONGODB_MCP_ENABLED=false

# Optional: Enable MCP mode by default (can toggle in UI)
MCP_MODE_ENABLED=false
```

### Runtime Settings (shared/config.py)

```python
class Settings(BaseSettings):
    # Tavily MCP
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    # MongoDB MCP
    mongodb_mcp_enabled: bool = Field(default=False, alias="MONGODB_MCP_ENABLED")

    # Experimental mode toggle
    mcp_mode_enabled: bool = Field(default=False, alias="MCP_MODE_ENABLED")

    @property
    def mcp_available(self) -> bool:
        """Returns True if any MCP server can be connected"""
        return bool(self.tavily_api_key) or self.mongodb_mcp_enabled
```

---

## Usage

### 1. Enable MCP Mode (UI)

1. Open Flow Companion
2. Go to sidebar → **🧪 Experimental** section
3. Toggle **MCP Mode** on
4. Wait for "✅ MCP Mode enabled!" message

**If API key not set:**
- Shows: "⚠️ MCP not configured. Set TAVILY_API_KEY in .env"

### 2. Make a Request

Try a request that static tools can't handle:

```
User: "What are the latest MongoDB Atlas features announced in 2026?"
```

**Response with MCP disabled:**
```
I don't have a built-in tool for this request.
Enable Experimental MCP Mode to let me try to figure it out.

💡 This request might work better with MCP Mode enabled (see sidebar)
```

**Response with MCP enabled:**
```
🆕 I figured out how to do this:

Here are the latest MongoDB Atlas features announced in 2026:
- Vector Search enhancements...
- New pricing tiers...
- [Full results from Tavily]

🔌 MCP: tavily/tavily-search
📝 Discovery: a1b2c3d4...
```

### 3. View Discoveries

In sidebar → **🔬 Tool Discoveries**:
```
📊 Total: 12 discoveries
✅ Success rate: 91.7% (11/12)

Recent:
• What's the latest AI news? (5x)
• MongoDB Atlas features 2026 (3x)
• Python best practices (2x)
```

### 4. Manage Knowledge Cache

In sidebar → **🌐 Knowledge Cache**:
```
📚 Cached: 8 fresh, 2 expired

[🗑️ Clear Cache]
```

---

## Developer Insights

### Identifying Promotion Candidates

```python
# Get discoveries with high usage
popular = discovery_store.get_popular_discoveries(
    min_uses=10,  # Used 10+ times
    exclude_promoted=True,
    limit=20
)

for disc in popular:
    print(f"Request: {disc['user_request']}")
    print(f"Times used: {disc['times_used']}")
    print(f"Success rate: {disc['success']}")
    print(f"Tool: {disc['solution']['mcp_server']}/{disc['solution']['tool_used']}")
    print(f"Arguments: {disc['solution']['arguments']}")
    print()
```

**Example Output:**
```
Request: What's the latest news about MongoDB?
Times used: 23
Success rate: True
Tool: tavily/tavily-search
Arguments: {'query': 'latest MongoDB news', 'max_results': 5}

→ Candidate for promotion to static web_search tool
```

### Monitoring Statistics

```python
stats = discovery_store.get_stats()

# Returns:
{
    "total_discoveries": 47,
    "successful": 43,
    "failed": 4,
    "promoted": 2,
    "avg_uses": 3.2,
    "most_used_server": "tavily",
    "most_used_tool": "tavily-search"
}
```

### Query by Intent

```python
# See what research requests users make
research_requests = discovery_store.get_discoveries_by_intent(
    intent="research",
    limit=50
)

# Identify patterns
common_topics = analyze_requests(research_requests)
# → ["AI trends", "MongoDB features", "Python best practices"]
```

---

## Testing

### Unit Tests (tests/test_mcp_agent.py)

**Coverage:** 18 tests with mocked MCP connections

```bash
pytest tests/test_mcp_agent.py -v
# Result: 18 passed, 1 skipped
```

**Tests:**
- Initialization without API key
- Tool discovery
- Request handling (reuse, new discovery)
- LLM solution generation
- MCP tool execution (success, timeout, error)
- Result formatting and truncation
- Cleanup

### Integration Tests (tests/integration/test_mcp_agent.py)

**Coverage:** 11 tests with real Tavily API calls

**Requirements:**
- `TAVILY_API_KEY` environment variable
- Active internet connection

```bash
# Set API key
export TAVILY_API_KEY=your-key

# Run integration tests
pytest tests/integration/test_mcp_agent.py -v -s
```

**Tests:**
- Tavily connection and tool discovery
- Real web search execution
- Discovery logging and reuse
- Knowledge caching
- Error handling
- Performance benchmarks

**Auto-skip:** All tests skip if `TAVILY_API_KEY` not set.

---

## Future Enhancements

### Planned Features

1. **MongoDB MCP Server**
   - Local stdio server for dynamic database queries
   - Natural language → aggregation pipeline
   - Complex analytics without hardcoded tools

2. **Multi-Server Orchestration**
   - Use multiple MCP servers in sequence
   - Example: Tavily search → MongoDB store → Analysis

3. **Automatic Tool Promotion**
   - Auto-promote discoveries with 50+ uses
   - Generate static tool code from solution pattern

4. **Discovery Expiration**
   - Mark old discoveries as stale after N days
   - Re-verify and update solutions

5. **User-Specific Learning**
   - Per-user discovery preferences
   - Personalized tool selection

---

## References

- **MCP Specification:** https://modelcontextprotocol.io
- **Tavily MCP Server:** https://docs.tavily.com/docs/mcp-server
- **Implementation:** `agents/mcp_agent.py`
- **Discovery Store:** `memory/tool_discoveries.py`
- **Integration Tests:** `tests/integration/test_mcp_agent.py`
- **UI Integration:** `ui/streamlit_app.py` (lines 415-524)

---

**Last Updated:** January 8, 2026
**Author:** Flow Companion Development Team
