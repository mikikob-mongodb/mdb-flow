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

## Conclusion

The current architecture is **working well and ready for demo**. These enhancements represent **opportunities for improvement**, not critical issues. The proposed changes will make the system more maintainable, testable, and scalable for future growth.

**Recommended Approach:** Incremental, post-demo improvements that build on current success while preparing for scale.
