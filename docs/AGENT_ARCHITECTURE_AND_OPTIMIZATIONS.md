# Agent Architecture and Optimizations

**Flow Companion - Multi-Agent System with Context Engineering**

*Version 3.1 - January 2026*

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Three-Agent System](#three-agent-system)
3. [Context Engineering Optimizations](#context-engineering-optimizations)
4. [Integration Between Agents and Optimizations](#integration-between-agents-and-optimizations)
5. [Performance Characteristics](#performance-characteristics)
6. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

Flow Companion uses a **coordinator pattern** where a single Coordinator Agent routes user requests to two specialized agents:

```
User Input (Voice/Text)
         ↓
   Coordinator Agent (17 tools)
    /              \
   ↓                ↓
Worklog Agent    Retrieval Agent
(13 tools)       (5 tools)
   ↓                ↓
   └────────────────┘
         ↓
    MongoDB Atlas
```

### Key Design Principles

1. **Single Entry Point**: All requests flow through the Coordinator Agent
2. **Tool-Based Architecture**: Agents use Claude's native tool calling (no LangChain)
3. **Stateless Agents**: Each agent instance can be reused across requests
4. **Direct Database Access**: Coordinator calls agent methods directly (bypassing LLM when possible)
5. **Shared Memory**: All agents share access to a Memory Manager for context

---

## Three-Agent System

### 1. Coordinator Agent

**File**: `agents/coordinator.py`
**Model**: Claude Sonnet 4.5
**Tools**: 17 tools (curated subset from specialized agents)

#### Responsibilities

- **Intent Classification**: Determine which agent should handle the request
- **Request Routing**: Call appropriate agent tools directly (no sub-agent LLM calls)
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

1. **Classifies intent** using Claude (Coordinator LLM)
2. **Calls agent methods directly** (e.g., `worklog_agent._create_task()`)
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

### Memory System (Milestone 4)

**Currently Implemented** (basic structure):
- Memory Manager initialized with embedding function
- Shared across all agents
- Long-term memory recording for significant actions

**Planned**:
- Short-term memory (session context) - 2-hour TTL
- Long-term memory (action history) - persistent with embeddings
- Shared memory (agent handoffs) - 5-minute TTL
- Auto-context injection into prompts

### Agent Coordination

**Currently**: Direct method calls (no LLM overhead)

**Planned**:
- Agent-to-agent handoffs via shared memory
- Coordinator delegates complex multi-step workflows
- Agents write handoff context for next agent

### Search Optimizations

**Currently**: Fixed search mode weights (60% vector, 40% text)

**Planned**:
- Adaptive weights based on query type
- Query analysis to auto-select best search mode
- Relevance feedback to improve ranking

### Prompt Optimization

**Currently**: Two prompt variants (verbose/streamlined)

**Planned**:
- Dynamic prompt assembly based on request type
- Few-shot examples injected only when needed
- User-specific prompt personalization

---

## Summary

Flow Companion's architecture demonstrates:

1. **Efficient multi-agent design** with minimal overhead
2. **Direct database access** avoiding redundant LLM calls
3. **Context engineering optimizations** reducing costs by 90%
4. **Flexible search modes** balancing speed vs. quality
5. **Comprehensive performance tracking** for continuous optimization

The system achieves **production-grade performance** (1-2 second response times) while maintaining **conversation quality** through intelligent prompt design and result compression.
