# Flow Companion Memory System

**Last Updated:** January 8, 2026

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Memory Types](#memory-types)
- [Implementation](#implementation)
- [Testing](#testing)
- [Usage Guide](#usage-guide)
- [Component Status](#component-status)

---

## Overview

Flow Companion implements a **5-tier memory system** inspired by cognitive science research, enabling the agent to:
- Remember current work context (Working Memory)
- Learn from past actions (Episodic Memory)
- Store user preferences (Semantic Memory)
- Remember behavioral rules (Procedural Memory)
- Coordinate between agents (Shared Memory)

### Key Features
- ✅ **Persistent personalization**: Preferences and rules survive beyond session lifetime
- ✅ **Automatic learning**: Extracts preferences and rules from natural language
- ✅ **Context-aware**: Injects relevant memory into each agent interaction
- ✅ **Multi-agent coordination**: Shared memory enables handoffs between agents
- ✅ **Vector search**: Semantic search over action history

---

## Architecture

### Memory Tiers

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SHORT-TERM (2hr TTL)          LONG-TERM (Persistent)      │
│  ┌─────────────────┐           ┌──────────────────────┐    │
│  │ Working Memory  │           │ Episodic Memory      │    │
│  │ - current task  │           │ - action history     │    │
│  │ - current proj  │           │ - timestamps         │    │
│  │ - last action   │           │ - vector embeddings  │    │
│  └─────────────────┘           └──────────────────────┘    │
│                                                             │
│  SHARED (5min TTL)             LONG-TERM (Persistent)      │
│  ┌─────────────────┐           ┌──────────────────────┐    │
│  │ Shared Memory   │           │ Semantic Memory      │    │
│  │ - handoffs      │           │ - preferences        │    │
│  │ - disambiguation│           │ - confidence scores  │    │
│  └─────────────────┘           └──────────────────────┘    │
│                                                             │
│                                LONG-TERM (Persistent)      │
│                                ┌──────────────────────┐    │
│                                │ Procedural Memory    │    │
│                                │ - rules/triggers     │    │
│                                │ - usage counts       │    │
│                                └──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Collections

**MongoDB Collections:**
- `short_term_memory` - Working memory (2hr TTL)
- `long_term_memory` - Episodic, Semantic, Procedural (persistent)
- `shared_memory` - Agent handoffs (5min TTL)

**Indexes:**
- `expires_at` - TTL indexes for auto-cleanup
- `user_id + memory_type` - Fast filtering by type
- `trigger_pattern` - Rule lookup (procedural memory)
- `vector_embedding` - Semantic search (episodic memory)

---

## Memory Types

### 1. Working Memory (Short-term)
**Purpose**: Track current session context
**TTL**: 2 hours
**Storage**: `short_term_memory` collection

**Schema:**
```javascript
{
  session_id: "uuid",
  current_project: "Voice Agent",
  current_task: "Implement speech recognition",
  current_task_id: "task-123",
  last_action: "start",
  expires_at: ISODate("2026-01-08T12:00:00Z")
}
```

**Usage:**
```python
# Update context
memory.update_session_context(session_id, {
    "current_project": "AgentOps",
    "current_task": "Write tests"
})

# Read context
context = memory.read_session_context(session_id)
```

---

### 2. Episodic Memory (Long-term)
**Purpose**: Store action history with timestamps
**TTL**: None (persistent)
**Storage**: `long_term_memory` collection (memory_type="episodic")

**Schema:**
```javascript
{
  user_id: "user-123",
  session_id: "uuid",
  memory_type: "episodic",  // Not "semantic" or "procedural"
  action_type: "complete",
  entity_type: "task",
  entity: {
    task_id: "task-123",
    task_title: "Write documentation",
    project_name: "Flow Companion"
  },
  timestamp: ISODate("2026-01-08T10:30:00Z"),
  vector_embedding: [0.1, 0.2, ...],  // 1024-dim
  created_at: ISODate("2026-01-08T10:30:00Z")
}
```

**Usage:**
```python
# Record action
memory.record_action(
    user_id="user-123",
    session_id=session_id,
    action_type="complete",
    entity_type="task",
    entity={"task_title": "Write tests"},
    generate_embedding=True
)

# Get history
history = memory.get_action_history(
    user_id="user-123",
    time_range="today",
    limit=10
)

# Semantic search
results = memory.search_history(
    user_id="user-123",
    query="What did I work on yesterday?",
    limit=5
)
```

---

### 3. Semantic Memory (Long-term)
**Purpose**: Store learned preferences
**TTL**: None (persistent)
**Storage**: `long_term_memory` collection (memory_type="semantic")

**Schema:**
```javascript
{
  user_id: "user-123",
  memory_type: "semantic",
  semantic_type: "preference",
  key: "focus_project",
  value: "Voice Agent",
  source: "explicit",  // or "inferred"
  confidence: 0.9,
  times_used: 5,
  created_at: ISODate("2026-01-08T09:00:00Z"),
  updated_at: ISODate("2026-01-08T11:00:00Z")
}
```

**Usage:**
```python
# Record preference
memory.record_preference(
    user_id="user-123",
    key="focus_project",
    value="Voice Agent",
    source="explicit",
    confidence=0.9
)

# Get preferences
prefs = memory.get_preferences(
    user_id="user-123",
    min_confidence=0.5
)

# Get specific preference
pref = memory.get_preference(user_id="user-123", key="focus_project")
```

**Extraction Patterns:**
- "I'm focusing on X" → `focus_project: X` (explicit, confidence=0.9)
- "Working on X" → `focus_project: X` (inferred, confidence=0.7)
- "Show me high priority tasks" → `priority_filter: high` (explicit, confidence=0.85)

---

### 4. Procedural Memory (Long-term)
**Purpose**: Store learned behavioral rules
**TTL**: None (persistent)
**Storage**: `long_term_memory` collection (memory_type="procedural")

**Schema:**
```javascript
{
  user_id: "user-123",
  memory_type: "procedural",
  trigger_pattern: "done",  // Normalized (lowercase)
  action_type: "complete_current_task",
  parameters: {},
  source: "explicit",
  confidence: 0.85,
  times_used: 12,
  created_at: ISODate("2026-01-08T09:00:00Z"),
  updated_at: ISODate("2026-01-08T11:30:00Z")
}
```

**Usage:**
```python
# Record rule
memory.record_rule(
    user_id="user-123",
    trigger="done",
    action="complete_current_task",
    source="explicit",
    confidence=0.85
)

# Get rules
rules = memory.get_rules(
    user_id="user-123",
    min_confidence=0.5
)

# Match trigger
rule = memory.get_rule_for_trigger(user_id="user-123", trigger="done")
# Auto-increments times_used
```

**Extraction Patterns:**
- "When I say 'done', complete my current task" → trigger="done", action="complete_current_task"
- "If I say 'next', start the next task" → trigger="next", action="start_next_task"

**Action Types:**
- `complete_current_task`
- `start_next_task`
- `stop_current_task`
- `skip_current_task`

---

### 5. Shared Memory (Agent handoffs)
**Purpose**: Coordinate between agents
**TTL**: 5 minutes
**Storage**: `shared_memory` collection

**Schema:**
```javascript
{
  session_id: "uuid",
  from_agent: "coordinator",
  to_agent: "retrieval",
  handoff_type: "search_results",
  payload: {
    query: "tasks for AgentOps",
    results: [...]
  },
  expires_at: ISODate("2026-01-08T10:05:00Z"),
  created_at: ISODate("2026-01-08T10:00:00Z")
}
```

**Usage:**
```python
# Create handoff
memory.create_handoff(
    session_id=session_id,
    from_agent="coordinator",
    to_agent="retrieval",
    handoff_type="search_results",
    payload={...}
)

# Read pending handoffs
handoffs = memory.read_all_pending(session_id, "retrieval")

# Consume handoff
memory.consume_handoff(handoff_id)
```

---

## Implementation

### MemoryManager (`memory/manager.py`)

**Key Methods:**

**Working Memory:**
- `update_session_context(session_id, updates)` - Update short-term context
- `read_session_context(session_id)` - Read short-term context
- `clear_session(session_id)` - Clear session data

**Episodic Memory:**
- `record_action(user_id, session_id, action_type, entity_type, entity, generate_embedding=True)`
- `get_action_history(user_id, time_range="today", action_type=None, limit=10)`
- `search_history(user_id, query, limit=5)` - Vector search

**Semantic Memory:**
- `record_preference(user_id, key, value, source="inferred", confidence=0.8)`
- `get_preferences(user_id, min_confidence=0.0)` - Returns sorted by confidence
- `get_preference(user_id, key)`
- `delete_preference(user_id, key)`

**Procedural Memory:**
- `record_rule(user_id, trigger, action, parameters=None, source="explicit", confidence=0.8)`
- `get_rules(user_id, min_confidence=0.0)` - Returns sorted by times_used
- `get_rule_for_trigger(user_id, trigger)` - Auto-increments times_used
- `delete_rule(user_id, trigger)`

**Shared Memory:**
- `create_handoff(session_id, from_agent, to_agent, handoff_type, payload)`
- `read_all_pending(session_id, to_agent)`
- `consume_handoff(handoff_id)`

**Statistics:**
- `get_memory_stats(session_id, user_id)` - Returns counts by type
- `get_user_memory_profile(user_id)` - Combined profile

---

### Coordinator Integration (`agents/coordinator.py`)

**Context Extraction (`_extract_context_from_turn`)**:
```python
# Working Memory - from tool calls
if tool_name == "get_tasks":
    updates["current_project"] = tool_input.get("project_name")

# Semantic Memory - from user message
if "focusing on" in user_message:
    memory.record_preference(user_id, "focus_project", project_name, source="explicit")

# Procedural Memory - from user message
if "when i say done" in user_message:
    memory.record_rule(user_id, trigger="done", action="complete_current_task")
```

**Context Injection (`_build_context_injection`)**:
```python
# Load from all memory types
session_context = memory.read_session_context(session_id)  # Working
preferences = memory.get_preferences(user_id, min_confidence=0.5)  # Semantic
rules = memory.get_rules(user_id, min_confidence=0.5)  # Procedural
disambiguation = memory.get_pending_disambiguation(session_id)  # Shared

# Inject into system prompt
return f"""
<memory_context>
Current project: {session_context['current_project']}

User preferences (Semantic Memory):
  • focus_project: Voice Agent

User rules (Procedural Memory):
  • When user says "done" → complete the current task
</memory_context>
"""
```

**Rule Trigger Checking (`_check_rule_triggers`)**:
```python
rules = memory.get_rules(user_id, min_confidence=0.5)
for rule in rules:
    if rule['trigger_pattern'] in user_message.lower():
        return {"matched": True, "action": rule['action_type']}
```

---

## Testing

### Unit Tests (`tests/test_memory_types.py`)
**13 tests covering all 5 memory types:**

**TestSemanticMemory** (6 tests):
- `test_record_preference_new`
- `test_record_preference_update`
- `test_get_preferences_sorted`
- `test_get_preferences_min_confidence`
- `test_delete_preference`

**TestProceduralMemory** (6 tests):
- `test_record_rule_new`
- `test_record_rule_normalizes_trigger`
- `test_record_rule_update`
- `test_get_rule_for_trigger`
- `test_get_rules_sorted_by_usage`
- `test_delete_rule`

**TestMemoryStats** (1 test):
- `test_memory_stats_by_type`

**Run tests:**
```bash
pytest tests/test_memory_types.py -v
```

### Integration Tests (`tests/integration/memory/`)
**14 comprehensive integration tests:**

- `test_action_recording.py` - Episodic memory recording
- `test_coordinator_context.py` - Working memory extraction
- `test_coordinator_semantic_procedural.py` - Preference/rule extraction
- `test_context_injection.py` - Context injection from all types
- `test_disambiguation_flow.py` - Shared memory disambiguation
- `test_memory_competencies.py` - 10 competency tests
- `test_narrative_generation.py` - Narrative summaries
- `test_preferences_flow.py` - End-to-end preference flow
- `test_rule_triggers.py` - Rule trigger matching
- `test_rules_flow.py` - End-to-end rule flow
- `test_semantic_procedural_memory.py` - Direct memory methods
- `test_semantic_procedural_memory_simple.py` - Simplified tests
- `test_semantic_search_history.py` - Vector search
- `test_ui_memory.py` - UI integration

**Run integration tests:**
```bash
# All memory integration tests
pytest tests/integration/memory/ -v

# Specific test
pytest tests/integration/memory/test_preferences_flow.py -v
```

---

## Usage Guide

### For End Users

**1. Enable Memory** (in Streamlit sidebar):
- ✅ Enable Memory
- ✅ Working (short-term)
- ✅ Long-term (episodic, semantic, procedural)
- ✅ Shared (handoffs)
- ✅ Inject (context injection)

**2. Set Preferences**:
```
I'm focusing on Voice Agent today
```
→ Stored in Semantic Memory, applied to future queries

**3. Teach Rules**:
```
When I say "done", complete my current task
```
→ Stored in Procedural Memory, triggered automatically

**4. View Memory** (Streamlit sidebar):
- **💭 Working Memory** - Current project/task
- **📝 Episodic Memory** - Recent actions
- **🎯 Semantic Memory** - Learned preferences
- **⚙️ Procedural Memory** - Learned rules
- **🤝 Shared Memory** - Pending handoffs
- **📊 Memory Stats** - Counts by type

**5. Use Disambiguation**:
```
Show me tasks for AgentOps
```
(Multiple results)
```
Start the first one
```
→ Resolves using shared memory

---

### For Developers

**Initialize Memory:**
```python
from shared.db import MongoDB
from memory.manager import MemoryManager

mongodb = MongoDB()
db = mongodb.get_database()
memory = MemoryManager(db)
```

**Record Actions:**
```python
memory.record_action(
    user_id="user-123",
    session_id=session_id,
    action_type="complete",
    entity_type="task",
    entity={"task_title": "Write tests"},
    generate_embedding=True
)
```

**Store Preferences:**
```python
memory.record_preference(
    user_id="user-123",
    key="focus_project",
    value="Voice Agent",
    source="explicit",
    confidence=0.9
)
```

**Store Rules:**
```python
memory.record_rule(
    user_id="user-123",
    trigger="done",
    action="complete_current_task",
    source="explicit",
    confidence=0.85
)
```

**Query Memory:**
```python
# Get action history
history = memory.get_action_history(user_id="user-123", time_range="today")

# Get preferences
prefs = memory.get_preferences(user_id="user-123", min_confidence=0.5)

# Get rules
rules = memory.get_rules(user_id="user-123", min_confidence=0.5)

# Search history
results = memory.search_history(
    user_id="user-123",
    query="What did I work on yesterday?"
)
```

---

## Component Status

**Last Audit:** January 7, 2026

| Component | Status | Location |
|-----------|--------|----------|
| **Memory Manager** | ✅ Complete | `memory/manager.py` |
| **Coordinator Integration** | ✅ Complete | `agents/coordinator.py` |
| **Streamlit UI** | ✅ Complete | `ui/streamlit_app.py` |
| **Unit Tests** | ✅ Complete | `tests/test_memory_types.py` |
| **Integration Tests** | ✅ Complete | `tests/integration/memory/` |
| **Database Indexes** | ✅ Complete | `scripts/setup_database.py` |
| **Demo Data Seed** | ✅ Complete | `scripts/seed_memory_demo_data.py` |
| **Evaluation Suite** | ✅ Complete | `evals/test_memory_competencies.py` |
| **Documentation** | ✅ Complete | This file |

### Coverage Summary
- **5/5 Memory Types**: Implemented and tested
- **13 Unit Tests**: All passing
- **14 Integration Tests**: All passing
- **10 Competencies**: All verified
- **UI Integration**: Complete with 5-panel sidebar
- **Vector Search**: Atlas Search integration working

### Known Gaps
- ❌ Interactive demo script for memory features
- ⚠️ End-to-end user walkthrough document

---

## References

**Related Documentation:**
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Overall system architecture
- [TESTING.md](./TESTING.md) - Testing methodology
- [MEMORY_EVALUATION_METHODOLOGY.md](./MEMORY_EVALUATION_METHODOLOGY.md) - Eval framework

**Research Foundation:**
- MemoryAgentBench - Long-term memory evaluation framework
- Cognitive science: Episodic vs Semantic vs Procedural memory
- RAG patterns: Semantic search over action history

**Implementation Details:**
- MongoDB TTL indexes for auto-expiration
- Atlas Vector Search for semantic queries
- Confidence scoring for preference reliability
- Usage tracking for rule optimization
