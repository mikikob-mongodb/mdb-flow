# Upcoming Architecture Improvements

**Date:** 2026-01-14
**Status:** ✅ Planning for Post-Demo Enhancement

## Current State

The system is working well and ready for demo. This document outlines opportunities to enhance maintainability, testability, and scalability for future development.

### Agent Landscape

```
coordinator.py:  3,375 lines (148 KB)  45% of all agent code
retrieval.py:    1,853 lines ( 67 KB)  25% of all agent code
worklog.py:      1,522 lines ( 58 KB)  20% of all agent code
mcp_agent.py:      711 lines ( 27 KB)  10% of all agent code
─────────────────────────────────────
TOTAL:           7,461 lines
```

## Coordinator Capabilities

The coordinator currently handles multiple responsibilities effectively:

### 1. **Request Routing** (4 Tiers)
```python
# TIER 1: Pattern matching (greetings, help)
# TIER 2: Slash commands (/search, /task)
# TIER 3: LLM with built-in tools (tasks, projects, search)
# TIER 4: MCP external tools (Tavily, MongoDB MCP)
```

### 2. **Intent Classification**
- `_classify_intent()` - Categorize user requests
- `_classify_multi_step_intent()` - Detect complex workflows
- `_can_static_tools_handle()` - Route to appropriate tier

### 3. **Context Management**
- `_build_context_injection()` - Build system prompts with context
- `_extract_context_from_turn()` - Extract working memory
- Session state management
- Rule checking and triggers

### 4. **Tool Orchestration**
- `_get_available_tools()` - Build tool registry (28 tools)
- `_execute_tool()` - Execute individual tools
- Tool result compression
- Timing/debug tracking

### 5. **Multi-Step Workflows**
- `_execute_multi_step()` - Async workflow execution
- Project creation workflows
- Complex task orchestration

### 6. **Response Formatting**
- `_format_mcp_response()` - Format MCP results
- `_format_multi_step_response()` - Format workflow results
- `_summarize_output()` - Truncate long outputs
- `_truncate()` - Text truncation

### 7. **MCP Management**
- `enable_mcp_mode()` - Initialize MCP connections
- `disable_mcp_mode()` - Teardown
- `_ensure_event_loop()` - Async event loop management
- `_run_async()` - Execute async operations

### 8. **Streaming**
- `process_stream()` - Stream responses to UI
- Token-by-token streaming
- Tool call interruptions

### 9. **Memory Integration**
- Procedural memory retrieval
- Semantic knowledge lookups
- Action recording

### 10. **Tool Definitions**
- 28 tool definitions providing comprehensive functionality
- Task tools, project tools, search tools, memory tools

## Opportunities for Enhancement

### Specialized Agents

The other agents demonstrate focused, single-purpose design:

**Retrieval Agent (1,853 lines)**
- Scope: Search operations
- Hybrid search, vector search, temporal queries
- Well-focused on retrieval operations

**Worklog Agent (1,522 lines)**
- Scope: Task/Project CRUD
- Create/update/delete tasks and projects
- Well-focused on work management

**MCP Agent (711 lines)**
- Scope: External tool discovery
- MCP protocol handling, tool discovery, caching
- Well-focused on external tools

## Proposed Improvements

### Option 1: Service Extraction (Minimal)

Create focused service classes to improve modularity:

```
coordinator/
  ├── coordinator.py          (routing only, ~800 lines)
  ├── intent_classifier.py    (intent detection)
  ├── context_builder.py      (system prompt building)
  ├── response_formatter.py   (format responses)
  └── tool_executor.py        (execute tools)
```

**Benefits:**
- ✅ Easier to test individual components
- ✅ Clearer separation of concerns
- ✅ Simpler code navigation
- ✅ More flexible for future changes

**Considerations:**
- More files to manage
- Migration effort required

### Option 2: Agent-Based Delegation (Moderate)

Expand agent ecosystem with specialized capabilities:

```
agents/
  ├── coordinator.py          (routing only, ~600 lines)
  ├── intent_agent.py         (classify intents)
  ├── workflow_agent.py       (multi-step orchestration)
  ├── context_agent.py        (build context)
  ├── worklog.py              (tasks/projects) ✅ already exists
  ├── retrieval.py            (search) ✅ already exists
  └── mcp_agent.py            (external tools) ✅ already exists
```

**Benefits:**
- ✅ Consistent agent pattern across system
- ✅ Each component independently testable and maintainable
- ✅ Easier to add new capabilities
- ✅ Better scalability for complex features

**Considerations:**
- Inter-agent coordination needs design
- Larger migration effort

### Option 3: Iterative Enhancement

Gradually improve architecture while maintaining stability:

**Benefits:**
- ✅ No disruption to working system
- ✅ Incremental, low-risk improvements
- ✅ Can prioritize based on actual needs

## Specific Enhancement Opportunities

### 1. Intent Classification Service

**Current:** 200+ lines integrated in coordinator

**Enhancement:**
```python
# intent_classifier.py
class IntentClassifier:
    def classify(self, user_message: str) -> Intent:
        # Intent logic here

    def requires_mcp(self, intent: Intent) -> bool:
        # MCP routing decision
```

**Benefits:** Easier to test, enhance with ML models, reuse in other contexts

### 2. Context Building Service

**Current:** 125+ lines integrated in coordinator

**Enhancement:**
```python
# context_builder.py
class ContextBuilder:
    def build_system_prompt(self, session, memory) -> str:
        # Context building logic
```

**Benefits:** Easier to test different prompt strategies, A/B testing

### 3. Workflow Orchestration Agent

**Current:** 300+ lines integrated in coordinator

**Enhancement:**
```python
# workflow_agent.py
class WorkflowAgent:
    async def execute(self, steps: List[Step]) -> Result:
        # Workflow execution
```

**Benefits:** Complex multi-step workflows easier to manage and test

### 4. Response Formatting Service

**Current:** Scattered across coordinator methods

**Enhancement:**
```python
# response_formatter.py
class ResponseFormatter:
    def format_mcp(self, result) -> str:
    def format_workflow(self, result) -> str:
    def summarize(self, text) -> str:
```

**Benefits:** Consistent formatting, easier to customize for different UIs

### 5. Distributed Tool Definitions

**Current:** 28 tools defined in coordinator

**Enhancement:**
```python
# Each agent owns its tools
class WorklogAgent:
    def get_tools(self) -> List[Tool]:
        return [create_task, update_task, ...]

class RetrievalAgent:
    def get_tools(self) -> List[Tool]:
        return [search_tasks, search_projects, ...]

# Coordinator aggregates
all_tools = (
    worklog.get_tools() +
    retrieval.get_tools() +
    memory.get_tools()
)
```

**Benefits:** Tools colocated with implementation, easier to maintain

## Implementation Approach

### Phase 1: Service Extraction (Low Risk)
- Create new service classes
- Coordinator delegates to services
- No API changes
- Incremental, testable migration

### Phase 2: Tool Distribution (Medium Risk)
- Each agent defines own tools
- Coordinator aggregates tools
- Comprehensive tool registration tests

### Phase 3: Agent Expansion (Planned Enhancement)
- New workflow agent
- New intent agent
- Event-driven coordination patterns

## Target Architecture

### Current Architecture (Working Well)
```
┌─────────────────────────────────────┐
│         Coordinator                 │
│  • Routing (4 tiers)                │
│  • Intent classification            │
│  • Context building                 │
│  • Tool execution                   │
│  • Response formatting              │
│  • Multi-step workflows             │
│  • MCP management                   │
│  • Streaming                        │
│  • Session management               │
│  3,375 lines                        │
└─────┬───────────────────────────────┘
      │
      ├─► Worklog Agent (tasks/projects)
      ├─► Retrieval Agent (search)
      └─► MCP Agent (external tools)
```

### Enhanced Architecture (Future)
```
┌─────────────────┐
│  Coordinator    │  ~600 lines
│  • Routing only │
└────────┬────────┘
         │
         ├─► Intent Classifier
         ├─► Context Builder
         ├─► Workflow Agent
         ├─► Response Formatter
         ├─► Worklog Agent
         ├─► Retrieval Agent
         └─► MCP Agent
```

## Design Considerations

### Granularity
- Balance between too many small classes (overhead) and too few large ones (maintainability)
- Target: 500-800 lines per component

### Orchestration
- Coordinator remains primary router
- Consider event-driven patterns for complex workflows
- Maintain clean interfaces between components

### Shared State
- Memory manager for cross-agent state
- Session state for user context
- MCP connections for external tools

### Testing Strategy
- Unit tests for extracted components
- Integration tests for coordinator routing
- End-to-end tests for user flows
- Gradual improvement in coverage

## Migration Strategy

**Timing:** Post-demo, spread over 2-3 iterations

**Approach:**
1. ✅ Document current architecture (this doc)
2. Extract intent classification first (highest benefit, lowest risk)
3. Move tool definitions to respective agents
4. Extract context building
5. Monitor and iterate based on results

**Success Metrics:**
- Improved test coverage (target: 80%+)
- Reduced coordinator size (target: <1000 lines)
- Faster development velocity for new features
- Easier onboarding for new developers

## Benefits of Enhancement

### For Development
- ✅ Easier to understand individual components
- ✅ Faster to add new features
- ✅ Less risk when making changes
- ✅ Better code reuse

### For Testing
- ✅ Smaller, focused test suites
- ✅ Easier to mock dependencies
- ✅ Higher test coverage achievable
- ✅ Faster test execution

### For Scalability
- ✅ Easy to add new agent types
- ✅ Plugin architecture possible
- ✅ Event-driven workflows feasible
- ✅ Horizontal scaling opportunities

### For Maintenance
- ✅ Clearer ownership of components
- ✅ Easier code navigation
- ✅ Reduced merge conflicts
- ✅ Simpler debugging

## Next Steps

**Immediate (Post-Demo):**
1. Set up comprehensive test suite for coordinator
2. Document current behavior before changes
3. Create intent classifier prototype

**Short-term (Next Month):**
4. Extract intent classification
5. Move tool definitions to agents
6. Extract context builder
7. Measure improvements

**Long-term (Future Roadmap):**
8. Workflow agent implementation
9. Event-driven architecture exploration
10. Plugin system for dynamic capabilities
11. Agent registry for centralized management

## Memory System Evaluation Framework

### Current State: Removed from Evals Dashboard

**Date Removed:** 2026-01-14

We temporarily removed memory evaluation features from the evals dashboard to:
- ✅ Eliminate performance overhead during context engineering benchmarks
- ✅ Focus dashboard on single-purpose: context optimization analysis
- ✅ Prevent session management calls from contaminating benchmark results

### What Was Removed

#### 1. From `evals/runner.py`
```python
# Removed session management overhead:
- _start_new_session() method
- UUID session ID generation per test
- coordinator.set_session() calls (40+ tests × 5 configs = 200+ calls)
- memory.clear_session() calls hitting MongoDB
- disable_memory parameter and config save/restore logic
```

**Performance Impact:** Each test was making 3+ database calls even with memory disabled, adding ~50-100ms overhead per test.

#### 2. From `evals/configs.py`
```python
# Removed memory comparison configs:
"memory_disabled": {
    "name": "Memory Disabled (Baseline)",
    "short": "No Memory",
    "memory_config": {
        "short_term": False,
        "long_term": False,
        "shared": False,
        "context_injection": False
    }
}

"memory_enabled": {
    "name": "Memory Enabled (Full)",
    "short": "Memory",
    "memory_config": {
        "short_term": True,
        "long_term": True,
        "shared": True,
        "context_injection": True
    }
}
```

#### 3. From `evals_app.py`
```python
# Removed entire Memory Competencies tab (~350 lines):
- render_memory_competencies_tab()
- run_memory_evaluation()
- render_memory_results()
- Imports from evals.memory_competency_suite
- Imports from evals.memory_metrics
```

### What Needs to Be Added Back (Future)

When ready to evaluate memory system performance, create a **separate dedicated app**:

#### Proposed: `memory_evals_app.py`

**Purpose:** Evaluate memory system across MemoryAgentBench competency dimensions

**Key Features:**
```python
# Test suite structure
MEMORY_COMPETENCY_TESTS = [
    # AR: Accurate Retrieval (4 tests)
    # - Single-hop, Multi-hop, Temporal, Cloze

    # TTL: Test-Time Learning (6 tests)
    # - Contradictions, Updates, Noise, Novel concepts

    # LRU: Long-Range Understanding (6 tests)
    # - Session boundaries, Topic drift, Interruptions

    # CR: Conflict Resolution (4 tests)
    # - Source priority, Temporal ordering
]

# Each test compares:
memory_enabled vs memory_disabled

# Metrics to track:
- Accuracy per competency
- Retrieval latency
- Memory storage overhead
- Context injection impact
```

#### Storage Schema
```python
# MongoDB collection: memory_evaluation_runs
{
    "run_id": "mem-eval-20260114-xyz",
    "timestamp": "2026-01-14T...",
    "competency_scores": {
        "AR_SH": {"accuracy": 0.95, "target": 0.90, ...},
        "AR_MH": {"accuracy": 0.85, "target": 0.85, ...},
        # ... all 20 competencies
    },
    "overall_metrics": {
        "overall_accuracy": 0.88,
        "avg_improvement_over_baseline": 45.2,
        "competencies_met": 17,
        "total_competencies": 20
    },
    "test_results": [
        {
            "test_id": 1,
            "competency": "AR_SH",
            "memory_enabled": {
                "passed": true,
                "latency_ms": 1234,
                "memory_retrieved": ["task-123", "project-456"]
            },
            "memory_disabled": {
                "passed": false,
                "latency_ms": 1100,
                "error": "No context available"
            }
        },
        # ... all test results
    ]
}
```

#### Implementation Approach

**Separate App Benefits:**
- ✅ No performance interference with context engineering evals
- ✅ Different test suite (competency-based vs latency/token optimization)
- ✅ Different metrics (accuracy/recall vs speed/cost)
- ✅ Can run memory evals independently
- ✅ Cleaner separation of concerns

**File Structure:**
```
evals/
├── configs.py                    # Context optimization configs only
├── runner.py                     # Clean, no memory overhead
├── result.py                     # Context engineering results
├── storage.py                    # Save to eval_comparison_runs
│
├── memory_competency_suite.py   # MemoryAgentBench test suite
├── memory_metrics.py            # Competency scoring logic
├── memory_runner.py             # Memory-specific test runner
├── memory_storage.py            # Save to memory_evaluation_runs
│
apps/
├── evals_app.py                 # Context engineering dashboard (port 8502)
└── memory_evals_app.py          # Memory competencies dashboard (port 8503)
```

### Design Lessons Learned

**Don't Mix Evaluation Types:**
- ❌ Context optimization (speed/cost) + Memory competency (accuracy) = Confused metrics
- ✅ Separate apps, separate collections, separate metrics

**Session Management:**
- ❌ Running session management when memory is disabled = Wasted overhead
- ✅ Only manage sessions when actually testing memory features

**Test Isolation:**
- ❌ Shared session state between tests = Contaminated results
- ✅ Clear session before each test, unique session IDs

### Future Work

**When to Re-Add Memory Evals:**
1. After memory system stabilizes (post-demo)
2. When ready to benchmark against MemoryAgentBench targets
3. When optimizing memory retrieval performance

**Success Metrics for Memory System:**
- AR (Accurate Retrieval): 90%+ accuracy
- TTL (Test-Time Learning): 85%+ accuracy
- LRU (Long-Range Understanding): 80%+ accuracy
- CR (Conflict Resolution): 90%+ accuracy
- Retrieval latency: <200ms average
- Context injection overhead: <500ms

**Integration Points:**
- Use same coordinator instance
- Share MongoDB connection
- Reuse memory competency test suite from `/evals`
- Export results to same format for comparison

---

## Automatic Bug Discovery and Analysis System

### Proposed Feature: LLM-Powered Error Tracking

**Purpose:** Automatically capture, analyze, and suggest fixes for runtime errors encountered during user interactions.

**Motivation:** During demo testing, errors occur that require manual analysis. An automated system could:
- Capture error context immediately
- Provide AI-powered fix suggestions
- Build a knowledge base of known issues
- Improve debugging velocity

### Implementation Design

#### MongoDB Collection: `bug_discoveries`

```python
{
    "bug_id": "bug-20260114-xyz",
    "timestamp": "2026-01-14T22:33:28Z",
    "user_id": "demo-user",
    "session_id": "session-abc",

    # Error context
    "error": {
        "type": "OperationFailure",
        "message": "limit should be less than or equal to numCandidates",
        "traceback": "...",
        "location": "agents/retrieval.py:1191"
    },

    # User context
    "user_query": "Show Nami's active projects",
    "tool_called": "hybrid_search_tasks",
    "tool_params": {
        "query": "Nami",
        "limit": 20,
        "assignee": "Nami"
    },

    # LLM analysis
    "analysis": {
        "root_cause": "limit * 10 (200) exceeds hardcoded numCandidates (100)",
        "suggested_fix": "Change numCandidates to max(100, search_limit)",
        "file_location": "agents/retrieval.py:1191",
        "severity": "high",
        "affects_demo": true
    },

    # Tracking
    "status": "identified",  # identified, fixed, ignored
    "fixed_in_commit": null,
    "occurrences": 2,
    "first_seen": "2026-01-14T22:33:28Z",
    "last_seen": "2026-01-14T22:33:32Z"
}
```

#### Error Capture Flow

```python
# In coordinator.py process() method
try:
    response = self._execute_tool(tool_name, tool_input)
except Exception as e:
    # Capture error context
    error_context = {
        "user_query": user_message,
        "tool_called": tool_name,
        "tool_params": tool_input,
        "error": {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    }

    # Async LLM analysis (non-blocking)
    asyncio.create_task(
        analyze_and_log_bug(error_context, session_id, user_id)
    )

    # Still raise/handle error normally
    raise
```

#### LLM Analysis Function

```python
async def analyze_and_log_bug(error_context: dict, session_id: str, user_id: str):
    """
    Analyze error using LLM and save to bug_discoveries collection.

    Non-blocking, fire-and-forget - doesn't affect user experience.
    """
    try:
        # Build analysis prompt
        prompt = f"""
        Analyze this error and suggest a fix:

        User Query: {error_context['user_query']}
        Tool Called: {error_context['tool_called']}
        Tool Params: {error_context['tool_params']}

        Error:
        {error_context['error']['traceback']}

        Provide:
        1. Root cause (1-2 sentences)
        2. Suggested fix (code change or config)
        3. Severity (low/medium/high/critical)
        4. Affects demo? (true/false)
        """

        # Call LLM (quick, haiku model)
        analysis = await llm_analyze_error(prompt)

        # Save to bug_discoveries
        db.bug_discoveries.update_one(
            {
                "error.message": error_context['error']['message'],
                "tool_called": error_context['tool_called']
            },
            {
                "$setOnInsert": {
                    "bug_id": f"bug-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                    "first_seen": datetime.utcnow(),
                    "occurrences": 0
                },
                "$set": {
                    "last_seen": datetime.utcnow(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": error_context['error'],
                    "user_query": error_context['user_query'],
                    "tool_called": error_context['tool_called'],
                    "tool_params": error_context['tool_params'],
                    "analysis": analysis,
                    "status": "identified"
                },
                "$inc": {"occurrences": 1}
            },
            upsert=True
        )

    except Exception as analysis_error:
        # Silently fail - don't cascade errors
        logger.warning(f"Bug analysis failed: {analysis_error}")
```

### Benefits

**For Development:**
- ✅ Automatic error documentation
- ✅ AI-powered fix suggestions
- ✅ Pattern recognition across similar errors
- ✅ Faster debugging for recurring issues

**For Demo/Testing:**
- ✅ Capture all issues encountered during testing
- ✅ Post-demo review of all errors with suggested fixes
- ✅ Priority ranking (severity, demo impact)
- ✅ No manual note-taking required

**For Production:**
- ✅ Build knowledge base of common errors
- ✅ Proactive issue detection
- ✅ User-facing error messages informed by analysis
- ✅ Trend analysis (which tools fail most often)

### Implementation Considerations

**Error Handling:**
- Analysis must be non-blocking (async, fire-and-forget)
- Analysis failures must not cascade to user
- Rate limiting to prevent LLM API abuse
- Deduplication by error signature

**Privacy:**
- Sanitize user data before logging
- Optional toggle to disable bug tracking
- Clear data retention policy

**Cost:**
- Use fast/cheap model (Haiku) for analysis
- Deduplicate identical errors
- Optional: Only analyze in dev/staging environments

**Integration Points:**
- Hook into coordinator error handling
- Hook into retrieval agent error handling
- Dashboard UI to view bug_discoveries
- Export to GitHub issues

### Phased Rollout

**Phase 1: Post-Demo (1-2 hours)**
- Basic error capture to `bug_discoveries`
- Manual analysis (no LLM)
- Simple logging with error signature deduplication

**Phase 2: Enhancement (2-3 hours)**
- Add LLM analysis for root cause and fixes
- Create simple dashboard to view bugs
- Priority and severity scoring

**Phase 3: Integration (future)**
- Auto-create GitHub issues for high-severity bugs
- Slack notifications for critical errors
- Trend analysis and reporting

### Example Use Case

**Scenario:** During demo, "Show Nami's active projects" fails

**Without Bug Discovery:**
1. User sees error
2. Demo continues (or crashes)
3. Post-demo: Manually review logs, find error, debug

**With Bug Discovery:**
1. User sees error
2. System captures error context
3. LLM analyzes: "Atlas Search limit constraint violated in retrieval.py:1191"
4. Suggested fix: "Change numCandidates to max(100, search_limit)"
5. Post-demo: Review bug_discoveries collection, see analysis, implement fix
6. All errors from demo session documented with AI suggestions

---

## Conclusion

The current architecture is **working well and ready for demo**. These enhancements represent **opportunities for improvement**, not critical issues. The proposed changes will make the system more maintainable, testable, and scalable for future growth.

**Recommended Approach:** Incremental, post-demo improvements that build on current success while preparing for scale.
