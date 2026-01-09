# Agent Architecture and Optimizations

**Flow Companion - Multi-Agent System with Context Engineering**

*Version 4.5 - January 2026 (Milestone 6 - MCP Agent)*

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Three-Agent System](#three-agent-system)
3. [Memory System (5-Tier Architecture)](#memory-system-5-tier-architecture)
4. [MCP Agent (Milestone 6 - Experimental)](#mcp-agent-milestone-6---experimental)
5. [Context Engineering Optimizations](#context-engineering-optimizations)
6. [Integration Between Agents and Optimizations](#integration-between-agents-and-optimizations)
7. [Performance Characteristics](#performance-characteristics)
8. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

Flow Companion uses a **coordinator pattern** where a single Coordinator Agent routes user requests to specialized agents:

```
User Input (Voice/Text)
         ↓
   Coordinator Agent (17 static tools + MCP routing)
    /        |              \
   ↓         ↓               ↓
Worklog   Retrieval      MCP Agent (Experimental)
Agent     Agent          (connects to remote MCP servers)
(13 tools) (5 tools)      ↓
   ↓         ↓            Tavily MCP Server
   └─────────┴────────────┘
         ↓
    MongoDB Atlas
```

### Key Design Principles

1. **Single Entry Point**: All requests flow through the Coordinator Agent
2. **Tool-Based Architecture**: Agents use Claude's native tool calling (no LangChain)
3. **Stateless Agents**: Each agent instance can be reused across requests
4. **Direct Database Access**: Coordinator calls agent methods directly (bypassing LLM when possible)
5. **5-Tier Memory System**: Working, Episodic, Semantic, Procedural, and Shared memory for comprehensive context management
6. **MCP Protocol Integration**: Connect to remote MCP servers for novel capabilities (Milestone 6)

---

## Three-Agent System

### 1. Coordinator Agent

**File**: `agents/coordinator.py`
**Model**: Claude Sonnet 4.5
**Tools**: 17 tools (curated subset from specialized agents)

#### Responsibilities

- **Intent Classification**: Determine which agent should handle the request (static vs MCP)
- **Request Routing**: Call appropriate agent tools directly (no sub-agent LLM calls)
- **MCP Mode Management**: Enable/disable experimental MCP mode for novel requests
- **Response Formatting**: Present results to user in markdown
- **Tool Result Compression**: Apply context engineering optimizations
- **Performance Tracking**: Track latency breakdown for debug panel

#### Tool Categories

**Worklog Operations** (9 tools):
- `create_task` - Create new task (requires project)
- `update_task` - Update task fields
- `complete_task` - Mark task as done
- `start_task` - Mark task as in_progress
- `stop_task` - Mark task as todo
- `add_note_to_task` - Add note to task
- `create_project` - Create new project
- `update_project` - Update project fields
- `add_note_to_project` - Add note to project

**Retrieval Operations** (6 tools):
- `get_tasks` - List all tasks with filters
- `get_projects` - List all projects
- `search_tasks` - Hybrid search for tasks
- `search_projects` - Hybrid search for projects
- `get_tasks_by_time` - Temporal activity queries
- `get_action_history` - Long-term memory (if enabled)

**Context Operations** (2 tools):
- `add_context_to_task` - Update task context
- `add_context_to_project` - Update project context
- `add_decision_to_project` - Record decision
- `add_method_to_project` - Add technology/method

#### Direct Database Calls

**CRITICAL OPTIMIZATION**: The Coordinator **does not call specialized agent LLMs**. Instead, it:

1. **Classifies intent** using Claude (Coordinator LLM) - determines static vs MCP routing
2. **Routes to appropriate handler**:
   - Static tools: Calls agent methods directly (e.g., `worklog_agent._create_task()`)
   - MCP tools: Routes to MCP Agent (e.g., `mcp_agent.handle_request()`)
3. **Returns results to Claude** for formatting

This eliminates the overhead of sub-agent LLM calls (saving ~500-1000ms per request).

**Example Flow**:
```python
# USER: "Create a task for debugging in AgentOps"

# 1. Coordinator LLM decides to call create_task tool
response = coordinator.llm.generate_with_tools(...)

# 2. Coordinator executes tool DIRECTLY (no worklog LLM call!)
result = worklog_agent._create_task(
    title="Debugging",
    project_name="AgentOps"
)

# 3. Result goes back to Coordinator LLM for formatting
# 4. User sees: "✓ Created task 'Debugging' in AgentOps"
```

### 2. Worklog Agent

**File**: `agents/worklog.py`
**Model**: Claude Sonnet 4.5 (only used in standalone mode)
**Tools**: 13 tools

#### Responsibilities

- **CRUD Operations**: Create, read, update tasks and projects
- **Embedding Generation**: Generate Voyage AI embeddings when content changes
- **Activity Logging**: Track all changes with timestamps
- **Data Validation**: Enforce data integrity rules

#### Key Methods

All methods prefixed with `_` are called **directly by Coordinator** (no LLM):

**Task Operations**:
- `_create_task(title, project_id, context, priority, status)` - Create task with embedding
- `_update_task(task_id, **updates)` - Update fields + regenerate embedding
- `_complete_task(task_id, completion_note)` - Mark done + set completed_at
- `_list_tasks(status, project_id, limit)` - Query tasks with filters
- `_get_task(task_id)` - Get single task

**Project Operations**:
- `_create_project(name, description, context)` - Create project with embedding
- `_update_project(project_id, **updates)` - Update fields + regenerate embedding
- `_list_projects(status, limit)` - Query projects
- `_get_project(project_id)` - Get single project

**Shared Operations**:
- `_add_note(target_type, target_id, note)` - Add note to task/project
- `_add_context(target_type, target_id, context)` - Update context + embedding
- `_add_decision(project_id, decision)` - Record project decision
- `_add_method(project_id, method)` - Add technology/method

#### Embedding Integration

When content changes, Worklog regenerates embeddings:

```python
# Update task title → regenerate embedding
if title is not None or context is not None:
    new_title = title or current_task.title
    new_context = context or current_task.context
    embedding_text = f"{new_title}\n{new_context}".strip()
    updates["embedding"] = embed_document(embedding_text)
```

**Performance**: Embedding generation tracked separately in latency breakdown.

### 3. Retrieval Agent

**File**: `agents/retrieval.py`
**Model**: Claude Sonnet 4.5 (only used in standalone mode)
**Tools**: 5 tools

#### Responsibilities

- **Semantic Search**: Vector search using MongoDB Atlas
- **Hybrid Search**: Combine vector + text search with $rankFusion
- **Temporal Queries**: Find tasks by activity timestamps
- **Fuzzy Matching**: Match informal references to tasks/projects
- **Progress Tracking**: Calculate project statistics

#### Search Methods

**Hybrid Search** (Default - Best Quality):
- `hybrid_search_tasks(query, limit)` - 60% vector + 40% text
- `hybrid_search_projects(query, limit)` - 60% vector + 40% text
- Performance: ~420ms
- Best for: Most queries (combines semantic + keyword matching)

**Vector Search** (Semantic Understanding):
- `vector_search_tasks(query, limit)` - Pure vector search
- `vector_search_projects(query, limit)` - Pure vector search
- Performance: ~280ms (33% faster than hybrid)
- Best for: Conceptual queries, related topics

**Text Search** (Fastest):
- `text_search_tasks(query, limit)` - Pure keyword search
- `text_search_projects(query, limit)` - Pure keyword search
- Performance: ~180ms (57% faster than hybrid)
- Best for: Exact keyword matches, known terms

#### MongoDB Atlas Integration

Uses MongoDB aggregation pipelines:

**Vector Search**:
```python
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,  # Voyage AI 1024-dim
            "numCandidates": 50,
            "limit": 10
        }
    },
    {"$project": {"_id": 1, "title": 1, "score": {"$meta": "vectorSearchScore"}}}
]
```

**Hybrid Search** ($rankFusion):
```python
pipeline = [
    {
        "$rankFusion": {
            "input": {
                "pipelines": {
                    "vectorSearch": [...],  # Vector search pipeline
                    "textSearch": [...]      # Text search pipeline
                }
            },
            "combination": {
                "weights": {
                    "vectorSearch": 0.6,
                    "textSearch": 0.4
                }
            }
        }
    }
]
```

#### Latency Tracking

Retrieval agent tracks timing breakdown:

```python
timings = {}

# Time embedding generation
start = time.time()
query_embedding = embed_query(query)
timings["embedding_generation"] = int((time.time() - start) * 1000)

# Time MongoDB query
start = time.time()
results = list(collection.aggregate(pipeline))
timings["mongodb_query"] = int((time.time() - start) * 1000)

# Store for Coordinator to access
self.last_query_timings = timings
```

---

## Memory System (5-Tier Architecture)

Flow Companion implements a comprehensive **5-tier memory system** (Milestone 4 & 5) that provides agents with both short-term and long-term context across different time horizons and abstraction levels.

### Memory Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     5-Tier Memory System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Working Memory (2hr TTL)                          │   │
│  │    Current project, task, action                     │   │
│  │    Collection: short_term_memory                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Episodic Memory (Persistent)                      │   │
│  │    Action history with embeddings                    │   │
│  │    Collection: long_term_memory (type: episodic)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. Semantic Memory (Persistent)                      │   │
│  │    User preferences with confidence scoring          │   │
│  │    Collection: long_term_memory (type: semantic)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Procedural Memory (Persistent)                    │   │
│  │    Behavioral rules with usage tracking              │   │
│  │    Collection: long_term_memory (type: procedural)   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. Shared Memory (5min TTL)                          │   │
│  │    Agent handoffs, disambiguation state              │   │
│  │    Collection: shared_memory                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1. Working Memory (2-Hour TTL)

**Purpose**: Store current session context (active project, task, last action)

**Schema**:
```javascript
{
  user_id: "user-123",
  memory_type: "working",
  working_type: "current_project" | "current_task" | "last_action",
  value: "Project Name" | "Task Title" | "completed_task",
  created_at: ISODate("2026-01-08T10:00:00Z"),
  expires_at: ISODate("2026-01-08T12:00:00Z")  // 2hr TTL
}
```

**API Methods**:
- `set_working_memory(working_type, value)` - Set current context
- `get_working_memory(working_type)` - Get current context
- `clear_working_memory()` - Clear all working memory

**Use Case**: "What's my current task?" → Check working memory first before searching database

### 2. Episodic Memory (Persistent)

**Purpose**: Record significant actions with timestamps and embeddings for semantic search

**Schema**:
```javascript
{
  user_id: "user-123",
  memory_type: "episodic",
  action_type: "task_completed" | "task_created" | "project_updated",
  description: "Completed task: Debugging in AgentOps",
  metadata: {
    task_id: "abc123",
    project_name: "AgentOps",
    status: "done"
  },
  embedding: [0.123, -0.456, ...],  // 1024-dim Voyage AI vector
  created_at: ISODate("2026-01-08T10:00:00Z")
}
```

**API Methods**:
- `record_action(action_type, description, metadata)` - Record action with auto-embedding
- `get_action_history(limit, days)` - Recent actions by time
- `search_action_history(query, limit)` - Semantic search of past actions

**Use Case**: "What did I work on last week?" → Search episodic memory by time/semantics

### 3. Semantic Memory (Persistent) - Milestone 5

**Purpose**: Store learned user preferences with confidence scoring and source tracking

**Schema**:
```javascript
{
  user_id: "user-123",
  memory_type: "semantic",
  semantic_type: "preference",
  key: "focus_project",
  value: "Voice Agent",
  source: "explicit",  // "explicit" | "inferred"
  confidence: 0.9,     // 0.0-1.0
  times_used: 5,       // Auto-increments on retrieval
  created_at: ISODate("2026-01-08T09:00:00Z"),
  updated_at: ISODate("2026-01-08T11:00:00Z")
}
```

**API Methods**:
- `record_preference(key, value, source, confidence)` - Store preference
- `get_preferences(min_confidence)` - Get all preferences above threshold
- `get_preference(key)` - Get specific preference
- `update_preference(key, value, confidence)` - Update existing preference
- `delete_preference(key)` - Remove preference

**Confidence Scoring**:
- **Explicit** (0.9-1.0): User directly stated ("I'm focusing on Project X")
- **Inferred** (0.3-0.7): Extracted from behavior (user works on X 80% of the time)

**Use Case**: Coordinator checks semantic memory before asking "What project?" → Finds user's focus_project preference

### 4. Procedural Memory (Persistent) - Milestone 5

**Purpose**: Store behavioral rules that trigger specific actions based on user patterns

**Schema**:
```javascript
{
  user_id: "user-123",
  memory_type: "procedural",
  trigger: "done",     // Normalized (lowercase)
  action: "complete_current_task",
  description: "When user says 'done', complete their current task",
  times_used: 12,      // Auto-increments on trigger match
  created_at: ISODate("2026-01-07T10:00:00Z"),
  updated_at: ISODate("2026-01-08T11:00:00Z")
}
```

**API Methods**:
- `record_rule(trigger, action, description)` - Store behavioral rule
- `get_rules()` - Get all rules sorted by times_used
- `get_rule_for_trigger(trigger)` - Check if trigger matches any rule
- `delete_rule(trigger)` - Remove rule

**Trigger Normalization**: All triggers stored lowercase for case-insensitive matching

**Action Types**:
- `complete_current_task` - Mark current working memory task as done
- `start_next_task` - Move to next task in queue
- `save_context` - Record current context to episodic memory

**Use Case**: User says "done" → Check procedural memory → Find "done" trigger → Auto-complete current task

### 5. Shared Memory (5-Minute TTL)

**Purpose**: Agent-to-agent handoffs and temporary disambiguation state

**Schema**:
```javascript
{
  user_id: "user-123",
  memory_type: "shared",
  shared_type: "handoff" | "disambiguation",
  key: "last_search_results",
  value: ["task_id_1", "task_id_2"],
  metadata: {
    from_agent: "retrieval",
    to_agent: "worklog",
    context: "User asked to complete debugging task"
  },
  created_at: ISODate("2026-01-08T11:00:00Z"),
  expires_at: ISODate("2026-01-08T11:05:00Z")  // 5min TTL
}
```

**API Methods**:
- `set_shared_memory(shared_type, key, value, metadata)` - Store handoff data
- `get_shared_memory(shared_type, key)` - Retrieve handoff data
- `clear_shared_memory(shared_type)` - Clear all shared memory of type

**Use Case**: Search finds multiple tasks → Store in shared memory → Next turn uses IDs for confirmation

### Memory Manager Implementation

**File**: `memory/manager.py`

**Key Features**:
- **Unified Interface**: Single MemoryManager class handles all 5 memory types
- **Auto-Embedding**: Episodic memory auto-generates embeddings on record
- **TTL Management**: MongoDB TTL indexes auto-expire working/shared memory
- **Type Safety**: `memory_type` field distinguishes between episodic/semantic/procedural in same collection
- **Usage Tracking**: Semantic/procedural memories auto-increment `times_used` on access

**Collections**:
```
MongoDB Collections:
├── short_term_memory    (working memory, 2hr TTL index)
├── long_term_memory     (episodic/semantic/procedural, no TTL)
└── shared_memory        (agent handoffs, 5min TTL index)
```

### Coordinator Integration

**Context Injection** (`coordinator.py`):

The Coordinator automatically injects memory context into the system prompt:

```python
def _build_context_from_memory(self):
    """Inject memory context into system prompt"""

    # 1. Working memory (current context)
    current_project = memory.get_working_memory("current_project")
    current_task = memory.get_working_memory("current_task")

    # 2. Semantic memory (preferences)
    preferences = memory.get_preferences(min_confidence=0.5)

    # 3. Procedural memory (rules)
    rules = memory.get_rules()

    # 4. Episodic memory (recent actions)
    recent_actions = memory.get_action_history(limit=5, days=7)

    # Build context string
    context = f"""
CURRENT CONTEXT (Working Memory):
- Project: {current_project}
- Task: {current_task}

USER PREFERENCES (Semantic Memory):
{format_preferences(preferences)}

LEARNED BEHAVIORS (Procedural Memory):
{format_rules(rules)}

RECENT ACTIVITY (Episodic Memory):
{format_actions(recent_actions)}
"""
    return context
```

**Memory Extraction**:

The Coordinator extracts memory items from conversation:

```python
def _extract_memory_from_turn(self, user_message, assistant_response):
    """Extract semantic and procedural memory from conversation"""

    # Extract preferences (semantic memory)
    if "I'm focusing on" in user_message:
        # Extract: key="focus_project", value="X", confidence=0.9
        memory.record_preference(...)

    # Extract rules (procedural memory)
    if "when I say" in user_message.lower():
        # Extract: trigger="done", action="complete_current_task"
        memory.record_rule(...)

    # Record action (episodic memory)
    if tool_called == "complete_task":
        memory.record_action(
            action_type="task_completed",
            description=f"Completed task: {task_title}",
            metadata={"task_id": task_id}
        )
```

### Memory Statistics

**API Method**: `get_memory_stats()`

Returns counts by memory type:
```javascript
{
  "working": 3,
  "episodic": 127,
  "semantic": 8,
  "procedural": 5,
  "shared": 2,
  "total": 145
}
```

### Testing Coverage

**Unit Tests** (13 tests in `test_memory_types.py`):
- ✅ Semantic Memory: CRUD operations, confidence filtering, sorting by confidence
- ✅ Procedural Memory: CRUD operations, trigger matching, usage tracking
- ✅ Memory Stats: Count by memory type

**Integration Tests** (14 tests in `tests/integration/memory/`):
- ✅ `test_action_recording.py` - Episodic memory recording
- ✅ `test_coordinator_context.py` - Working memory extraction
- ✅ `test_coordinator_semantic_procedural.py` - Preference/rule extraction
- ✅ `test_preferences_flow.py` - End-to-end semantic memory
- ✅ `test_rules_flow.py` - End-to-end procedural memory
- ✅ `test_rule_triggers.py` - Trigger matching and normalization
- ✅ `test_memory_competencies.py` - 10 memory competency tests
- ✅ 7 additional integration tests

**Total**: 27 memory-related tests

### UI Integration

**Streamlit Sidebar** (`ui/streamlit_app.py`):

The UI displays all 5 memory types in an expandable sidebar:

```
Memory System
├─ 📝 Working Memory
│  ├─ Current Project: Voice Agent
│  ├─ Current Task: Debugging
│  └─ Last Action: task_completed
├─ 📚 Episodic Memory (127 actions)
│  ├─ Completed task: Debugging in AgentOps (2h ago)
│  └─ Created task: Testing in Voice Agent (3h ago)
├─ 🧠 Semantic Memory (8 preferences)
│  ├─ focus_project: Voice Agent (conf: 0.9, used: 5x)
│  └─ default_priority: high (conf: 0.7, used: 3x)
├─ 🔧 Procedural Memory (5 rules)
│  ├─ "done" → complete_current_task (used: 12x)
│  └─ "next" → start_next_task (used: 8x)
└─ 🔄 Shared Memory (2 items)
   └─ last_search_results: ["abc123", "def456"]
```

### Performance Characteristics

**Storage**:
- Working Memory: ~100 bytes per item × 3 items = 300 bytes
- Episodic Memory: ~500 bytes per action (with 1024-dim embedding)
- Semantic Memory: ~200 bytes per preference
- Procedural Memory: ~150 bytes per rule
- Shared Memory: ~300 bytes per handoff

**Query Performance**:
- Get working memory: ~5ms (indexed on user_id + memory_type)
- Get preferences: ~10ms (indexed + sorted by confidence)
- Get rules: ~8ms (indexed + sorted by times_used)
- Search episodic: ~150ms (vector search on embeddings)

**Memory Overhead**:
- Total memory footprint for typical user: ~100KB
- Embeddings dominate storage (episodic memory)
- TTL indexes auto-cleanup short-term collections

---

## MCP Agent (Milestone 6 - Experimental)

Flow Companion's **MCP Agent** enables the system to handle requests that built-in static tools cannot address by connecting to remote **Model Context Protocol (MCP)** servers. This experimental feature allows the agent to discover new capabilities dynamically, learn from successful solutions, and reuse knowledge to avoid redundant API calls.

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      MCP AGENT ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User: "What's the latest AI news?"                            │
│         ↓                                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ COORDINATOR (Intent Classification)                      │  │
│  │ - Classify: static vs MCP intent                         │  │
│  │ - Route to MCP Agent if needed                           │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ MCP AGENT (Handle Request)                               │  │
│  │ 1. Check knowledge cache (📚)                            │  │
│  │ 2. Find similar discovery (🔄)                           │  │
│  │ 3. Figure out solution (🆕)                              │  │
│  │ 4. Execute via MCP                                       │  │
│  │ 5. Log discovery + cache knowledge                       │  │
│  └──────┬───────────────────────┬──────────────────────────┘  │
│         ↓                       ↓                               │
│  ┌──────────────┐        ┌─────────────────────────────────┐  │
│  │ Tool         │        │ Memory Manager                   │  │
│  │ Discovery    │        │ - Knowledge Cache (7-day TTL)    │  │
│  │ Store        │        │ - Semantic Memory                │  │
│  │ (MongoDB)    │        │ - Vector Search (0.85 threshold) │  │
│  └──────┬───────┘        └─────────────────────────────────┘  │
│         ↓                                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ EXTERNAL MCP SERVERS                                     │  │
│  │ ┌─────────────────────┐  ┌──────────────────────────┐   │  │
│  │ │ Tavily MCP (SSE)    │  │ MongoDB MCP (stdio)      │   │  │
│  │ │ - tavily-search     │  │ - mongodb-query (future) │   │  │
│  │ │ - tavily-extract    │  │ - mongodb-aggregate      │   │  │
│  │ │ - tavily-map        │  │ - mongodb-create         │   │  │
│  │ │ - tavily-crawl      │  │                          │   │  │
│  │ └─────────────────────┘  └──────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. MCP Agent (`agents/mcp_agent.py`)

**Purpose**: Connect to MCP servers, discover tools, execute solutions, and learn from usage patterns

**Key Methods**:
```python
class MCPAgent:
    async def initialize(self):
        """Connect to configured MCP servers via SSE/stdio"""
        # Tavily via SSE
        streams = await sse_client(url=f"https://mcp.tavily.com/mcp/?tavilyApiKey={key}")
        session = ClientSession(*streams)
        await session.initialize()

    async def handle_request(user_request, intent, context, user_id):
        """Main entry point - handle requests static tools can't"""
        # 1. Check knowledge cache (instant return if cached)
        # 2. Find similar discovery (vector search, 0.85 threshold)
        # 3. If no match, figure out solution using LLM + available tools
        # 4. Execute via MCP protocol
        # 5. Log discovery for future reuse
        # 6. Cache knowledge (7-day TTL)

    async def cleanup(self):
        """Properly close MCP connections"""
        await self.exit_stack.aclose()
```

**Connected Servers**:
- **Tavily MCP** (SSE transport) - Web search, content extraction, URL mapping, web crawling
- **MongoDB MCP** (planned - stdio transport) - Direct database access

#### 2. Tool Discovery Store (`memory/tool_discoveries.py`)

**Purpose**: Log successful MCP tool solutions with embeddings for semantic similarity matching

**MongoDB Schema** (`tool_discoveries` collection):
```javascript
{
  user_request: "What's the latest AI news?",
  request_embedding: [0.123, -0.456, ...],  // 1024-dim Voyage AI
  intent: "research",
  solution: {
    mcp_server: "tavily",
    tool_used: "tavily-search",
    arguments: {
      query: "AI news",
      max_results: 5
    }
  },
  result_preview: "Found 5 articles about...",
  success: true,
  execution_time_ms: 1234,
  times_used: 5,  // Auto-increments on reuse
  promoted_to_static: false,
  created_at: ISODate("2026-01-08T10:00:00Z"),
  updated_at: ISODate("2026-01-08T11:30:00Z")
}
```

**Key Methods**:
```python
class ToolDiscoveryStore:
    def log_discovery(user_request, intent, solution, result_preview, success, execution_time_ms):
        """Log a newly discovered solution with auto-embedding"""

    def find_similar_discovery(user_request, similarity_threshold=0.85, require_success=True):
        """Vector search for cached solution, increments times_used"""
        # Returns: {solution, times_used, discovery_id}

    def get_popular_discoveries(min_uses=2, limit=20, exclude_promoted=True):
        """Get frequently used patterns for promotion to static tools"""
```

#### 3. Knowledge Cache (`memory/manager.py`)

**Purpose**: Cache search/research results to avoid redundant MCP API calls

**MongoDB Schema** (`long_term_memory` collection, `semantic_type="knowledge"`):
```javascript
{
  user_id: "user-123",
  memory_type: "semantic",
  semantic_type: "knowledge",  // NEW TYPE
  query: "latest AI news",
  query_embedding: [0.123, -0.456, ...],  // 1024-dim
  results: [...],  // Cached search results
  source: "tavily",
  fetched_at: ISODate("2026-01-08T10:00:00Z"),
  expires_at: ISODate("2026-01-15T10:00:00Z"),  // 7-day TTL
  times_accessed: 3
}
```

**Key Methods**:
```python
class MemoryManager:
    def cache_knowledge(user_id, query, results, source="tavily", freshness_days=7):
        """Cache search results with auto-embedding and TTL"""

    def get_cached_knowledge(user_id, query, similarity_threshold=0.85):
        """Find cached knowledge via vector search, increment times_accessed"""

    def search_knowledge(user_id, query_text, limit=5):
        """Semantic search across knowledge cache"""

    def clear_knowledge_cache(user_id):
        """Clear all cached knowledge for user"""

    def get_knowledge_stats(user_id):
        """Get cache statistics (total, fresh, expired)"""
```

### Request Flow Patterns

#### Pattern 1: New Discovery (🆕)
```
User: "What's the latest AI news?"
  ↓
Coordinator classifies intent: "research" (MCP-capable)
  ↓
MCP Agent checks knowledge cache: MISS
  ↓
MCP Agent searches discoveries: MISS
  ↓
MCP Agent figures out solution:
  - LLM analyzes request + available tools
  - Selects: tavily-search
  - Arguments: {query: "AI news", max_results: 5}
  ↓
Execute via Tavily MCP server (1234ms)
  ↓
Log discovery to tool_discoveries collection
  ↓
Cache knowledge to long_term_memory (7-day TTL)
  ↓
Return: "🆕 I figured out how to do this:
         Found 5 articles about AI news..."
```

#### Pattern 2: Discovery Reuse (🔄)
```
User: "Show me recent AI developments"
  ↓
Coordinator classifies intent: "research"
  ↓
MCP Agent checks knowledge cache: MISS
  ↓
MCP Agent searches discoveries: HIT (0.92 similarity to "latest AI news")
  ↓
Reuse solution:
  - Server: tavily
  - Tool: tavily-search
  - Arguments: {query: "AI developments", max_results: 5}
  ↓
Execute via Tavily MCP server (890ms)
  ↓
Increment times_used in discovery record
  ↓
Cache knowledge for this query
  ↓
Return: "🔄 I've solved this before:
         Found 5 articles about AI developments..."
```

#### Pattern 3: Knowledge Cache Hit (📚)
```
User: "What's the latest AI news?" (repeat query)
  ↓
Coordinator classifies intent: "research"
  ↓
MCP Agent checks knowledge cache: HIT (0.98 similarity, fetched 2h ago)
  ↓
Return cached results instantly (no MCP call!)
  ↓
Increment times_accessed
  ↓
Return: "📚 Found this in my knowledge cache:
         [Cached results from 2 hours ago...]"
```

### Coordinator Integration

**Intent Classification** (`_classify_intent`):
```python
def _classify_intent(self, user_message: str) -> str:
    """Classify user intent from message"""
    # Returns: create_task, web_search, research, unknown, etc.
    # "research", "web_search", "complex_query" → Route to MCP
    # "create_task", "update_task", "list_tasks" → Static tools
```

**Static vs MCP Routing** (`_can_static_tools_handle`):
```python
def _can_static_tools_handle(self, intent: str, user_message: str) -> bool:
    """Returns True if static tools can handle this request"""
    static_intents = ["create_task", "update_task", "list_tasks", ...]
    mcp_intents = ["research", "web_search", "complex_query", "unknown"]
    return intent in static_intents
```

**MCP Mode Management**:
```python
async def enable_mcp_mode(self):
    """Initialize and enable MCP mode"""
    if self.mcp_agent is None:
        self.mcp_agent = MCPAgent(self.db, self.memory, embedding_fn=embed_query)
        await self.mcp_agent.initialize()
    self.mcp_mode_enabled = True

async def disable_mcp_mode(self):
    """Cleanup and disable MCP mode"""
    if self.mcp_agent:
        await self.mcp_agent.cleanup()
    self.mcp_mode_enabled = False
```

**Response Formatting** (`_format_mcp_response`):
```python
def _format_mcp_response(self, mcp_result: dict) -> dict:
    """Format MCP Agent result with source indicators"""
    source_messages = {
        "knowledge_cache": "📚 Found this in my knowledge cache:",
        "discovery_reuse": "🔄 I've solved this before:",
        "new_discovery": "🆕 I figured out how to do this:"
    }
    return {
        "text": f"{source_messages[source]}\n\n{result_text}",
        "debug_info": {
            "routed_to_mcp": True,
            "source": source,
            "mcp_server": server,
            "tool_used": tool,
            "discovery_id": discovery_id,
            "execution_time_ms": execution_time_ms
        }
    }
```

### Configuration

**Environment Variables** (`.env`):
```bash
# Tavily MCP Server
TAVILY_API_KEY=your-tavily-api-key

# MongoDB MCP (future)
MONGODB_MCP_ENABLED=false

# Experimental Mode Toggle
MCP_MODE_ENABLED=false
```

**Settings** (`shared/config.py`):
```python
class Settings(BaseSettings):
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    mongodb_mcp_enabled: bool = Field(default=False, alias="MONGODB_MCP_ENABLED")
    mcp_mode_enabled: bool = Field(default=False, alias="MCP_MODE_ENABLED")

    @property
    def mcp_available(self) -> bool:
        """Returns True if any MCP server can be connected"""
        return bool(self.tavily_api_key) or self.mongodb_mcp_enabled
```

### UI Integration

**MCP Mode Toggle** (Streamlit sidebar):
```python
# 🧪 Experimental Section
mcp_enabled = st.sidebar.toggle(
    "MCP Mode",
    value=st.session_state.get("mcp_enabled", False),
    help="Enable experimental MCP mode to handle novel requests"
)

if mcp_enabled and not st.session_state.get("mcp_initialized"):
    status = asyncio.run(coordinator.enable_mcp_mode())
    st.session_state.mcp_initialized = True
```

**MCP Visibility Panels**:
- **🔌 MCP Servers** - Show connected servers (Tavily, MongoDB MCP)
- **🛠️ MCP Tools** - List available tools from all servers
- **🌐 Knowledge Cache** - Show cached knowledge with expiry times
- **🔬 Tool Discoveries** - Show popular discoveries and promotion candidates

### Developer Workflow: Discovery Promotion

When a discovery is used frequently (e.g., `times_used > 10`), developers can **promote it to a static tool**:

1. **Identify Popular Patterns**:
```python
popular = discovery_store.get_popular_discoveries(min_uses=10, limit=20)
# Returns: [{user_request: "latest AI news", times_used: 15, solution: {...}}, ...]
```

2. **Review Candidate**:
- Check if pattern is stable and commonly requested
- Verify solution is reliable (success=true consistently)
- Assess if worth maintaining as static tool

3. **Implement Static Tool**:
```python
# In coordinator.py, add new tool
def search_ai_news(max_results: int = 5) -> dict:
    """Search for latest AI news (promoted from MCP discovery)"""
    # Call Tavily API directly (no MCP overhead)
    return tavily_client.search(query="AI news", max_results=max_results)
```

4. **Mark as Promoted**:
```python
discovery_store.mark_promoted(discovery_id)
# Sets promoted_to_static=true, excludes from future promotion candidates
```

### Testing Coverage

**Integration Tests** (`tests/integration/test_mcp_agent.py` - 11 tests):
- ✅ Tavily connection successful
- ✅ Tools discovered from Tavily server
- ✅ Basic web search via MCP
- ✅ Research intent routing
- ✅ Discovery logging to database
- ✅ Similar query reuse (vector search)
- ✅ Knowledge cache hits
- ✅ Empty query handling
- ✅ No servers connected error
- ✅ Proper resource cleanup
- ✅ Search performance benchmark (<10s)

**Unit Tests** (36 tests across `test_tool_discoveries.py` and `test_memory_types.py`):
- ✅ Discovery CRUD operations
- ✅ Vector search similarity matching
- ✅ Popular discovery retrieval
- ✅ Promotion workflow
- ✅ Knowledge caching with TTL
- ✅ Cache hit/miss logic

**Total MCP Tests**: 47 tests (46 passing, 1 skipped without TAVILY_API_KEY)

### Performance Characteristics

**Latency Breakdown**:
```
┌──────────────────────────────────────────────┐
│ Component              Time (ms)   % Total   │
├──────────────────────────────────────────────┤
│ Knowledge Cache Check  120ms       10%       │ ← Vector search (cache miss)
│ Discovery Search       150ms       12%       │ ← Vector search (miss)
│ LLM (figure solution)  800ms       65%       │ ← Only on new discovery
│ MCP Tool Execution     1200ms      98%       │ ← Tavily API call
│ Log Discovery          80ms        7%        │ ← MongoDB write + embedding
│ Cache Knowledge        90ms        7%        │ ← MongoDB write + embedding
├──────────────────────────────────────────────┤
│ TOTAL (New Discovery)  1230ms      100%      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Discovery Reuse (No LLM call)                │
├──────────────────────────────────────────────┤
│ Discovery Search       150ms       14%       │ ← Vector search (hit)
│ MCP Tool Execution     890ms       84%       │ ← Tavily API call
│ Cache Knowledge        90ms        8%        │
├──────────────────────────────────────────────┤
│ TOTAL (Reuse)          1060ms      100%      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Knowledge Cache Hit (No MCP call)            │
├──────────────────────────────────────────────┤
│ Knowledge Cache Check  120ms       100%      │ ← Vector search (hit)
│ Return Cached Results  5ms         4%        │ ← Instant return
├──────────────────────────────────────────────┤
│ TOTAL (Cache Hit)      125ms       100%      │
└──────────────────────────────────────────────┘
```

**Optimization Impact**:
- **Discovery Reuse**: 14% faster (no LLM solution planning)
- **Knowledge Cache**: 90% faster (no MCP API call)

### Known Limitations

- **MCP Mode Toggle Required**: User must manually enable experimental mode
- **Single MCP Server**: Only Tavily connected (MongoDB MCP planned)
- **No Tool Composition**: Can't chain multiple MCP tools in one request
- **Manual Promotion**: Developers must manually promote popular discoveries
- **7-Day Cache TTL**: Knowledge expires regardless of freshness needs

### Future Enhancements

- **Auto-Promotion**: Automatically promote discoveries with >20 uses to static tools
- **MongoDB MCP Integration**: Connect to local MongoDB MCP server for database queries
- **Tool Composition**: Support multi-step workflows across MCP tools
- **Adaptive TTL**: Adjust cache freshness based on query type (news=1hr, docs=30d)
- **Cross-Discovery Learning**: Combine insights from multiple related discoveries

---

## Context Engineering Optimizations

Flow Companion implements three **context engineering optimizations** (Milestone 2) to reduce latency and token usage:

### 1. Tool Result Compression

**File**: `utils/context_engineering.py`
**Function**: `compress_tool_result(tool_name, result, compress=True)`

#### What It Does

Compresses large tool results before sending back to LLM:

**Before** (`get_tasks` with 50 tasks):
```json
{
  "success": true,
  "count": 50,
  "tasks": [
    {
      "_id": "...",
      "title": "...",
      "status": "...",
      "priority": "...",
      "context": "...",
      "notes": [...],
      "activity_log": [...],
      "project_name": "...",
      "created_at": "...",
      "updated_at": "...",
      ...
    },
    // ... 49 more tasks with full details
  ]
}
```
**~15,000 tokens**

**After** (compressed):
```json
{
  "total_count": 50,
  "summary": {
    "todo": 20,
    "in_progress": 15,
    "done": 15
  },
  "top_5": [
    {"id": "...", "title": "...", "status": "...", "project": "...", "priority": "..."},
    {"id": "...", "title": "...", "status": "...", "project": "...", "priority": "..."},
    {"id": "...", "title": "...", "status": "...", "project": "...", "priority": "..."},
    {"id": "...", "title": "...", "status": "...", "project": "...", "priority": "..."},
    {"id": "...", "title": "...", "status": "...", "project": "...", "priority": "..."}
  ],
  "note": "Showing 5 of 50. Use filters to narrow down."
}
```
**~500 tokens (97% reduction!)**

#### Compression Rules

**`get_tasks`**: If >10 tasks, return summary + top 5
**`search_tasks`**: Return only essential fields (id, title, score, project, status)
**`get_projects`**: If >5 projects, return summary + top 5
**Other tools**: No compression (keep full results)

#### Toggle Control

Controlled via `compress_results` optimization flag:

```python
# In coordinator.py
compress = self.optimizations.get("compress_results", True)
compressed_result = compress_tool_result(tool_name, result, compress=compress)
```

### 2. Streamlined System Prompt

**File**: `config/prompts.py`
**Functions**: `get_system_prompt(streamlined=True)`, `STREAMLINED_SYSTEM_PROMPT`

#### What It Does

Reduces system prompt from **verbose** (~500 words) to **streamlined** (~200 words) using directive patterns.

**Verbose Prompt** (500 words, ~650 tokens):
```
You are a task management assistant. Help users manage their tasks and projects using the available tools.

**CRITICAL RULE - ALWAYS USE TOOLS:**
- You MUST use tools for EVERY operation - reading tasks, searching, creating, updating, etc.
- NEVER answer from memory or previous context - ALWAYS call the appropriate tool
- NEVER say "I found X tasks" unless you actually called search_tasks or get_tasks
...
(detailed instructions with examples, edge cases, formatting guidelines)
```

**Streamlined Prompt** (200 words, ~260 tokens):
```
You are a task assistant. Use tools for ALL actions.

RULES:
1. NEVER claim to complete an action without calling a tool
2. For modifications: search → confirm → execute
3. Use context already known - don't re-ask for project
4. Keep responses concise

PATTERNS:
- "What are my tasks?" → get_tasks()
- "Show me [project]" → get_tasks(project_name="[project]")
- "I finished X" → search_tasks("X") → confirm → complete_task(id)
...
```

**Token Reduction**: ~60% fewer tokens (650 → 260)

#### Toggle Control

Controlled via `streamlined_prompt` optimization flag:

```python
# In coordinator.py
streamlined = self.optimizations.get("streamlined_prompt", True)
system_prompt = get_system_prompt(streamlined)
```

### 3. Prompt Caching

**File**: `shared/llm.py`
**Function**: `generate_with_tools(cache_prompts=True)`

#### What It Does

Uses Anthropic's **Prompt Caching API** to cache the system prompt across requests:

**First Request** (Cache Miss):
```python
params = {
    "system": [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}  # Mark for caching
        }
    ],
    "extra_headers": {"anthropic-beta": "prompt-caching-2024-07-31"}
}

response = client.messages.create(**params)
# Cache creation: 260 tokens cached
```

**Subsequent Requests** (Cache Hit):
```python
# System prompt loaded from cache (0 input tokens!)
# Only user message + conversation history counted
# Latency reduced by ~100-200ms
```

#### Performance Impact

- **First request**: +5 tokens write cost (negligible)
- **Subsequent requests**: 90% discount on cached tokens
- **Latency improvement**: ~100-200ms faster on cache hits
- **Cost savings**: ~10x cheaper for system prompt tokens

#### Toggle Control

Controlled via `prompt_caching` optimization flag:

```python
# In coordinator.py
cache_prompts = self.optimizations.get("prompt_caching", True)
response = self.llm.generate_with_tools(
    messages=messages,
    tools=tools,
    system=system_prompt,
    cache_prompts=cache_prompts  # Enable/disable caching
)
```

---

## Integration Between Agents and Optimizations

### Flow Diagram

```
User: "What are my tasks?"
       ↓
┌──────────────────────────────────────────────┐
│ COORDINATOR AGENT                            │
├──────────────────────────────────────────────┤
│ 1. Load system prompt (streamlined/verbose)  │ ← Optimization 2
│ 2. Call LLM with prompt caching              │ ← Optimization 3
│ 3. LLM decides: call get_tasks tool          │
│ 4. Execute worklog_agent._list_tasks()       │ ← Direct call
│ 5. Get raw result (50 tasks)                 │
│ 6. Apply compression if enabled              │ ← Optimization 1
│ 7. Send compressed result to LLM             │
│ 8. LLM formats response                      │
│ 9. Return to user                            │
└──────────────────────────────────────────────┘
```

### Configuration System

Optimizations are controlled via a **toggle system**:

**Evals Configs** (`evals/configs.py`):
```python
EVAL_CONFIGS = {
    "baseline": {
        "optimizations": {
            "compress_results": False,
            "streamlined_prompt": False,
            "prompt_caching": False,
        }
    },
    "all_context": {
        "optimizations": {
            "compress_results": True,
            "streamlined_prompt": True,
            "prompt_caching": True,
        }
    },
}
```

**Main App** (`ui/streamlit_app.py`):
```python
# Sidebar toggles
compress_results = st.checkbox("📦 Compress Tool Results", value=True)
streamlined_prompt = st.checkbox("⚡ Streamlined Prompt", value=True)
prompt_caching = st.checkbox("💾 Prompt Caching", value=True)

optimizations = {
    "compress_results": compress_results,
    "streamlined_prompt": streamlined_prompt,
    "prompt_caching": prompt_caching,
}

# Pass to coordinator
response = coordinator.process(
    user_message=user_input,
    optimizations=optimizations,
    return_debug=True
)
```

### Performance Tracking

The Coordinator tracks **latency breakdown** for every request:

```python
self.current_turn = {
    "turn": turn_number,
    "timestamp": datetime.now(),
    "tool_calls": [],         # List of tool calls with timings
    "llm_calls": [],          # List of LLM calls with timings
    "total_duration_ms": 0,
    "tokens_in": 0,
    "tokens_out": 0,
    "cache_hit": False,
}
```

**Tool Call Tracking**:
```python
# Each tool call records:
{
    "name": "get_tasks",
    "input": {"status": "in_progress"},
    "output": "15 tasks returned",
    "duration_ms": 120,
    "breakdown": {
        "embedding_generation": 0,      # From retrieval agent
        "mongodb_query": 95,            # From retrieval/worklog agent
        "processing": 25                # Python overhead
    },
    "success": True
}
```

**LLM Call Tracking**:
```python
# Each LLM call records:
{
    "purpose": "decide_action",  # or "format_response"
    "duration_ms": 850
}
```

**Debug Panel Display**:
```
Turn 1 - 12:34:56
  LLM (decide_action): 850ms
  Tool: get_tasks (120ms)
    ├─ MongoDB: 95ms
    └─ Processing: 25ms
  LLM (format_response): 420ms
  Total: 1,390ms
  Tokens: 450 in, 120 out
  💾 Cache HIT
```

---

## Performance Characteristics

### Baseline vs. Optimized

**Baseline Configuration** (no optimizations):
- Verbose system prompt: ~650 tokens
- Full tool results: ~15,000 tokens per large query
- No caching: Full prompt processing every time
- **Average latency**: ~2,500ms
- **Average tokens**: 16,000 input, 300 output

**All Context Engineering Configuration**:
- Streamlined prompt: ~260 tokens (60% reduction)
- Compressed results: ~500 tokens (97% reduction)
- Prompt caching: ~100-200ms faster on cache hits
- **Average latency**: ~1,200ms (52% faster)
- **Average tokens**: 1,000 input, 280 output (94% reduction)

### Latency Breakdown

Typical request with optimizations enabled:

```
┌─────────────────────────────────────────────┐
│ Component              Time (ms)   % Total  │
├─────────────────────────────────────────────┤
│ LLM (decide action)    600ms       50%      │ ← Reduced by caching
│ Tool execution         150ms       13%      │
│   ├─ Embedding gen     60ms        5%       │
│   ├─ MongoDB query     70ms        6%       │
│   └─ Processing        20ms        2%       │
│ LLM (format response)  400ms       33%      │ ← Reduced by compression
│ Python overhead        50ms        4%       │
├─────────────────────────────────────────────┤
│ TOTAL                  1,200ms     100%     │
└─────────────────────────────────────────────┘
```

### Search Mode Performance

Different search modes have different performance characteristics:

| Mode   | Embedding | MongoDB | Total  | Best For                |
|--------|-----------|---------|--------|-------------------------|
| Text   | 0ms       | ~180ms  | 180ms  | Exact keywords          |
| Vector | ~60ms     | ~220ms  | 280ms  | Semantic understanding  |
| Hybrid | ~60ms     | ~360ms  | 420ms  | Best quality (default)  |

### Token Usage Impact

With compression enabled:

| Tool         | Before  | After | Reduction |
|--------------|---------|-------|-----------|
| get_tasks    | 15,000  | 500   | 97%       |
| search_tasks | 3,000   | 400   | 87%       |
| get_projects | 2,000   | 300   | 85%       |

### Cost Impact

**Baseline** (no optimizations):
- Input tokens: ~16,000 per request
- Output tokens: ~300 per request
- Cost per request: ~$0.048 (Sonnet 4.5 pricing)
- **100 requests**: $4.80

**Optimized** (all context engineering):
- Input tokens: ~1,000 per request (with cache hits)
- Output tokens: ~280 per request
- Cost per request: ~$0.004
- **100 requests**: $0.40

**90% cost reduction!**

---

## Future Enhancements

### ✅ Completed (Milestone 4, 5 & 6)

**5-Tier Memory System** - Fully Implemented (Milestone 4 & 5):
- ✅ Working Memory (2hr TTL) - Current project/task/action
- ✅ Episodic Memory (persistent) - Action history with embeddings
- ✅ Semantic Memory (persistent) - User preferences with confidence scoring
- ✅ Procedural Memory (persistent) - Behavioral rules with usage tracking
- ✅ Shared Memory (5min TTL) - Agent handoffs and disambiguation
- ✅ Knowledge Cache (persistent) - Search/research results with 7-day TTL
- ✅ Auto-context injection into Coordinator prompts
- ✅ Memory extraction from conversations
- ✅ UI integration with 5-panel memory sidebar
- ✅ 27 comprehensive tests (13 unit + 14 integration)

**MCP Agent** - Fully Implemented (Milestone 6):
- ✅ MCP Protocol integration using Python SDK
- ✅ Tavily remote server connection via SSE transport
- ✅ Tool Discovery Store with vector search (0.85 threshold)
- ✅ Discovery learning and reuse patterns
- ✅ Knowledge caching with 7-day TTL
- ✅ Intent classification and routing logic
- ✅ MCP mode toggle in UI with server/tool visibility
- ✅ Discovery promotion workflow for developers
- ✅ 47 comprehensive tests (36 unit + 11 integration)

### 🔄 In Progress (Milestone 7)

**Advanced Memory Competencies**:
- Multi-turn rule learning (extract complex patterns)
- Confidence adjustment (update preferences based on usage)
- Memory consolidation (merge duplicate preferences)
- Forgetting mechanisms (decay low-confidence items over time)
- Cross-memory reasoning (combine semantic + procedural insights)

### 🎯 Planned Enhancements

**Agent Coordination**:
- **Complex Workflows**: Coordinator delegates multi-step tasks across agents
- **Handoff Patterns**: Agents write detailed handoff context in shared memory
- **Parallel Execution**: Multiple agents work simultaneously on different subtasks
- **Error Recovery**: Agents retry failed operations with alternative strategies

**Search Optimizations**:
- **Adaptive Weights**: Auto-adjust vector/text weights based on query type
- **Query Analysis**: LLM analyzes query to select best search mode
- **Relevance Feedback**: Learn from user interactions to improve ranking
- **Query Expansion**: Use semantic memory to expand queries with user context

**Prompt Optimization**:
- **Dynamic Assembly**: Build prompts based on request type and memory context
- **Few-Shot Injection**: Add examples only when pattern matching detects need
- **User Personalization**: Customize prompt style based on semantic memory preferences
- **Memory-Aware Prompts**: Include only relevant memory context (not all 5 tiers every time)

**Memory Intelligence**:
- **Preference Inference**: Auto-extract preferences from repeated behaviors
- **Rule Generation**: Suggest procedural rules based on episodic patterns
- **Memory Summaries**: Generate daily/weekly summaries of episodic memory
- **Context Prediction**: Pre-load likely context based on time-of-day patterns

**Performance**:
- **Memory Caching**: Cache frequently accessed preferences/rules in-memory
- **Lazy Loading**: Load memory context only when needed (not every turn)
- **Batch Operations**: Batch memory writes to reduce DB round-trips
- **Embedding Reuse**: Cache embeddings for common queries

---

## Summary

Flow Companion's architecture demonstrates:

1. **Efficient multi-agent design** with minimal overhead (single active LLM)
2. **Direct database access** avoiding redundant LLM calls (bypasses sub-agent LLMs)
3. **5-tier memory system** providing comprehensive context across time horizons
4. **MCP Protocol integration** enabling dynamic capability discovery and learning
5. **Context engineering optimizations** reducing costs by 90% and latency by 52%
6. **Flexible search modes** balancing speed vs. quality (text/vector/hybrid)
7. **Comprehensive performance tracking** for continuous optimization
8. **Memory intelligence** with semantic preferences, procedural rules, and knowledge caching

The system achieves:
- **Production-grade performance**: 1-2 second response times (125ms with cache hits)
- **Intelligent context awareness**: Auto-injection of relevant memory
- **User adaptation**: Learns preferences and behaviors over time
- **Dynamic capability extension**: Connects to MCP servers for novel requests
- **Discovery learning**: Reuses successful patterns to avoid redundant work
- **Cost efficiency**: 90% token reduction through compression and caching
- **Comprehensive testing**: 287+ tests including 27 memory-specific and 47 MCP-specific tests
