# 06 - Memory Engineering

**Time:** 35 minutes
**Priority:** P0 - Core demo feature
**Updated:** January 9, 2026 (Milestone 6 - Knowledge Cache & GTM Templates)

---

## Overview

Flow Companion implements a 5-tier memory architecture based on MongoDB's Agent Memory Framework. Each memory type serves a distinct purpose and is evaluated across 4 capabilities.

---

## Memory Framework

### 5 Memory Types

| Type | Collection | TTL | Purpose | Example |
|------|------------|-----|---------|---------|
| **Working Memory** | short_term | 2hr | Current context, task focus | "Currently viewing AgentOps project" |
| **Episodic Memory** | long_term | ∞ | Action history (what happened) | "Completed debugging task at 2pm" |
| **Semantic Memory** | long_term | 7d* | Preferences + Knowledge cache* | "User prefers Voice Agent" + "AI news from Tavily" |
| **Procedural Memory** | long_term | ∞ | Rules + Templates* | "done→complete" + "GTM template" |
| **Shared Memory** | shared | 5min | Agent handoffs, coordination | "Retrieval found task X → Worklog" |

*New in Milestone 6: Knowledge cache (semantic.knowledge) and templates (procedural.template)

### 4 Capabilities (AR, TTL, LRU, CR)

| Capability | Abbreviation | What It Tests | Difficulty |
|------------|--------------|---------------|------------|
| **Accurate Retrieval** | AR | Find specific info from memory | Medium |
| **Test-Time Learning** | TTL | Learn new rules/preferences during conversation | Medium |
| **Long-Range Understanding** | LRU | Summarize across many turns/sessions | Hard |
| **Conflict Resolution** | CR | Handle contradictory/updated info | Very Hard |

**Research Finding:** Multi-hop conflict resolution is hardest (<7% accuracy in benchmarks).

---

## Test Cases by Memory Type

### 6.1 Working Memory (Session Context)

**Purpose:** Remember context within a conversation session. Resets on session end.

#### Test 6.1.1: Accurate Retrieval - Single-Hop (AR-SH)

```
Settings:
☑ Working Memory: ON
☑ Context Injection: ON
```

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "Show me the AgentOps project" | Shows AgentOps | Setup | □ |
| 2 | "What's high priority?" | Filters to AgentOps high-priority | AR | □ |
| 3 | Check debug panel | "Context injected: ✅" | Verify | □ |

#### Test 6.1.2: Accurate Retrieval - Multi-Hop (AR-MH)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "Show me AgentOps" | Context: AgentOps | Setup | □ |
| 2 | "Start the debugging task" | Context: AgentOps + task | Setup | □ |
| 3 | "What am I working on?" | "debugging task in AgentOps" | AR-MH | □ |

#### Test 6.1.3: Conflict Resolution - Single-Hop (CR-SH)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "Show me AgentOps" | Context: AgentOps | Setup | □ |
| 2 | "Actually, switch to Voice Agent" | Context updated | CR | □ |
| 3 | "What's high priority?" | Voice Agent priorities | CR-SH | □ |

#### Test 6.1.4: Context Lost (Memory OFF)

```
Settings:
☐ Working Memory: OFF
☐ Context Injection: OFF
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Clear memory, refresh | Clean state | □ |
| 2 | "Show me AgentOps" | Shows AgentOps | □ |
| 3 | "What's high priority?" | ALL high-priority OR asks "which project?" | □ |

**Key Insight:** Difference between 6.1.3 and 6.1.4 demonstrates Working Memory value.

---

### 6.2 Episodic Memory (Action History)

**Purpose:** Remember actions across sessions for history queries. Persistent.

#### Test 6.2.1: Recording Actions

```
Settings:
☑ Episodic Memory: ON
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "Mark the debugging task as done" | Completes task | □ |
| 2 | Check debug panel | Shows "Episodic Memory write" | □ |
| 3 | Check Memory Stats | Episodic count increased | □ |

#### Test 6.2.2: Accurate Retrieval - Recent (AR)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "What did I complete today?" | Lists today's completions | AR | □ |
| 2 | Check tool call | `get_action_history` called | Verify | □ |

#### Test 6.2.3: Long-Range Understanding (LRU)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "What have I been working on this week?" | Summary of actions | LRU | □ |
| 2 | "Summarize my recent activity" | Narrative summary | LRU | □ |

#### Test 6.2.4: History Unavailable (Memory OFF)

```
Settings:
☐ Episodic Memory: OFF
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "What did I do last week?" | Can't access history | □ |
| 2 | Check debug panel | `get_action_history` NOT available | □ |

---

### 6.3 Semantic Memory (Preferences)

**Purpose:** Learn and remember user preferences. Persistent across sessions.

#### Test 6.3.1: Test-Time Learning - Preference (TTL)

```
Settings:
☑ Semantic Memory: ON
```

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "I'm focusing on Voice Agent today" | Stores preference | TTL | □ |
| 2 | Check Memory Stats | Semantic Memory increased | Verify | □ |
| 3 | "What should I do next?" | Suggests Voice Agent tasks | TTL | □ |

#### Test 6.3.2: Preference Application

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "I usually work on high priority first" | Stores preference | TTL | □ |
| 2 | Clear Working Memory, refresh | New session | Setup | □ |
| 3 | "What should I work on?" | High priority tasks (from Semantic) | AR | □ |

#### Test 6.3.3: Conflict Resolution - Preference Update (CR)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "I'm focusing on AgentOps" | Stores preference | Setup | □ |
| 2 | "Actually, I changed my mind. Voice Agent is the priority" | Updates preference | CR | □ |
| 3 | "What's my current focus?" | Voice Agent (not AgentOps) | CR | □ |

#### Test 6.3.4: Preferences Unavailable (Memory OFF)

```
Settings:
☐ Semantic Memory: OFF
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "I'm focusing on Voice Agent" | Acknowledged but not stored | □ |
| 2 | New session | - | □ |
| 3 | "What's my current focus?" | Doesn't know | □ |

#### Test 6.3.5: Knowledge Caching (Milestone 6)

**Purpose:** Cache MCP search results to avoid redundant API calls (7-day TTL).

```
Settings:
☑ Semantic Memory: ON
☑ MCP Mode: ON (requires TAVILY_API_KEY)
```

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "What are the latest MongoDB features?" | Tavily search, results cached | Setup | □ |
| 2 | Check Memory Stats | Knowledge cache: 1 entry | Verify | □ |
| 3 | "MongoDB features 2026" (similar query) | Uses cache (~0.5s, no API call) | AR | □ |
| 4 | Check response | Shows "📚 Source: Knowledge Cache" | Verify | □ |

**Verification:**
- Debug panel shows "Knowledge Cache HIT" for step 3
- Response time <1s (vs 3-5s for fresh Tavily search)
- Tool Discoveries count stays same (no new discovery)

---

### 6.4 Procedural Memory (Rules)

**Purpose:** Learn workflows and rules. Persistent across sessions.

#### Test 6.4.1: Test-Time Learning - Rule (TTL)

```
Settings:
☑ Procedural Memory: ON
```

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "When I say 'done', mark my current task as complete" | Stores rule | TTL | □ |
| 2 | "Start the checkpointer task" | Sets current task | Setup | □ |
| 3 | "Done" | Completes checkpointer (rule triggered) | TTL | □ |

#### Test 6.4.2: Rule Persistence

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | Establish rule in session 1 | Rule stored | Setup | □ |
| 2 | New session | Fresh Working Memory | Setup | □ |
| 3 | Trigger rule | Rule still works | AR | □ |

#### Test 6.4.3: Conflict Resolution - Rule Update (CR)

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | "When I say 'done', complete my task" | Stores rule | Setup | □ |
| 2 | "Actually, when I say 'done', just add a 'completed' note" | Updates rule | CR | □ |
| 3 | "Start task X" then "Done" | Adds note (not complete) | CR | □ |

#### Test 6.4.4: GTM Template (Milestone 6)

**Purpose:** Use procedural templates for multi-step workflows (see 07-multi-turn.md).

```
Settings:
☑ Procedural Memory: ON
☑ MCP Mode: ON (for research step)
```

| Step | Action | Expected | Capability | Pass |
|------|--------|----------|------------|------|
| 1 | Verify GTM template exists | Check Memory Stats → Procedural: 1+ | Setup | □ |
| 2 | "Research gaming market and create GTM project with tasks" | Multi-step workflow triggers | Setup | □ |
| 3 | Check project created | "Gaming Market" project exists | Verify | □ |
| 4 | Check tasks | 12 tasks across 3 phases (Research, Strategy, Execution) | AR | □ |
| 5 | Verify template usage | Template `times_used` incremented | Verify | □ |

**Template Structure Verified:**
- Phase 1: Research (4 tasks)
- Phase 2: Strategy (4 tasks)
- Phase 3: Execution (4 tasks)
- Each task prefixed with phase name: `[Research] Market size analysis`

---

### 6.5 Shared Memory (Agent Handoffs)

**Purpose:** Allow agents to pass context without re-searching. Short TTL (5 min).

#### Test 6.5.1: Agent Handoff

```
Settings:
☑ Shared Memory: ON
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "I finished the checkpointer task" | Completes task | □ |
| 2 | Check debug panel shows: | | |
| | - search_tasks (Retrieval Agent) | | □ |
| | - Shared Memory write | | □ |
| | - complete_task (Worklog Agent) | | □ |
| | - Shared Memory read | | □ |
| | - "Agent Handoff: ✅" | | □ |

#### Test 6.5.2: Handoff Diagram

Debug panel should show:
```
┌──────────┐    ┌──────────────┐    ┌──────────┐
│Retrieval │───▶│Shared Memory │───▶│ Worklog  │
│  Agent   │    │   (5min TTL) │    │  Agent   │
└──────────┘    └──────────────┘    └──────────┘
```

#### Test 6.5.3: Handoff Without Shared Memory

```
Settings:
☐ Shared Memory: OFF
```

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "Complete the checkpointer task" | Still works | □ |
| 2 | Check debug panel | Worklog re-searches (no handoff) | □ |
| 3 | Compare latency | Slightly slower without handoff | □ |

---

## Memory Toggle Combinations

| Working | Episodic | Semantic | Procedural | Shared | Expected Behavior |
|---------|----------|----------|------------|--------|-------------------|
| ✅ | ✅ | ✅ | ✅ | ✅ | Full memory, best experience |
| ✅ | ❌ | ❌ | ❌ | ✅ | Context works, no learning |
| ❌ | ✅ | ✅ | ✅ | ❌ | No session context, has history |
| ❌ | ❌ | ❌ | ❌ | ❌ | Stateless, every turn fresh |

---

## Memory Timing Overhead

Record memory operation times:

| Operation | Expected | Actual | Pass |
|-----------|----------|--------|------|
| Working Memory read | <20ms | ___ms | □ |
| Working Memory write | <20ms | ___ms | □ |
| Episodic Memory read | <30ms | ___ms | □ |
| Episodic Memory write | <50ms | ___ms | □ |
| Semantic Memory read | <30ms | ___ms | □ |
| Semantic Memory write | <50ms | ___ms | □ |
| Procedural Memory read | <30ms | ___ms | □ |
| Procedural Memory write | <50ms | ___ms | □ |
| Shared Memory read | <15ms | ___ms | □ |
| Shared Memory write | <15ms | ___ms | □ |

**Key Insight:** Memory overhead should be negligible compared to LLM time (6-12s).

---

## Capability Summary Matrix

| Memory Type | AR | TTL | LRU | CR |
|-------------|----|----|-----|-----|
| Working | ✅ | - | - | ✅ |
| Episodic | ✅ | - | ✅ | - |
| Semantic | ✅ | ✅ | - | ✅ |
| Procedural | ✅ | ✅ | - | ✅ |
| Shared | - | - | - | - |

---

## Demo Script Integration

### Memory Demo Sequence (for 09-demo-dry-run.md)

```
□ "Show me AgentOps"              → Working Memory stores context
□ "What's high priority?"         → Working Memory filters (AR)

□ [Toggle Working Memory OFF]
□ "What's high priority?"         → Context lost, shows all

□ [Toggle Working Memory ON]
□ "I'm focusing on Voice Agent"   → Semantic Memory stores preference (TTL)
□ "What should I do?"             → Uses preference

□ "What did I complete today?"    → Episodic Memory query (LRU)

□ "I finished the checkpointer"   → Watch Shared Memory handoff
```

---

## Results Summary

| Memory Type | Tests | Passed | Failed |
|-------------|-------|--------|--------|
| Working Memory | 4 | __ | __ |
| Episodic Memory | 4 | __ | __ |
| Semantic Memory | 5 | __ | __ |
| Procedural Memory | 4 | __ | __ |
| Shared Memory | 3 | __ | __ |
| **Total** | **20** | __ | __ |

| Capability | Tests | Passed | Failed |
|------------|-------|--------|--------|
| Accurate Retrieval (AR) | 6 | __ | __ |
| Test-Time Learning (TTL) | 4 | __ | __ |
| Long-Range Understanding (LRU) | 2 | __ | __ |
| Conflict Resolution (CR) | 4 | __ | __ |
| **Total** | **16** | __ | __ |

---

## Demo Numbers Template

```
┌─────────────────────────────────────────────────────────┐
│ MEMORY ENGINEERING RESULTS                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 5 Memory Types:                                          │
│   • Working Memory:     Session context (2hr TTL)       │
│   • Episodic Memory:    Action history (persistent)     │
│   • Semantic Memory:    Preferences (persistent)        │
│   • Procedural Memory:  Rules (persistent)              │
│   • Shared Memory:      Agent handoffs (5min TTL)       │
│                                                          │
│ 4 Capabilities Evaluated:                                │
│   • Accurate Retrieval (AR):      ___% pass             │
│   • Test-Time Learning (TTL):     ___% pass             │
│   • Long-Range Understanding:     ___% pass             │
│   • Conflict Resolution (CR):     ___% pass             │
│                                                          │
│ Memory Overhead: <___ms (vs ___s LLM time)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

*Memory Engineering Testing Guide v3.0*
*Updated for Milestone 6: Knowledge Cache & GTM Templates*
*Based on MongoDB Agent Memory Framework*
