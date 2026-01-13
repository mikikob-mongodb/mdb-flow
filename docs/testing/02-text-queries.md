# 02 - Tier 3: LLM Agents with Built-in Tools

**Time:** 15 minutes
**Priority:** P0 - Core functionality
**Version:** v3.1 (Updated for 4-tier routing)

---

## Overview

This guide covers **Tier 3** of Flow Companion's 4-tier query routing architecture:

**Tier 3: LLM Agent with Built-in Tools** (~8s, ~$0.01, Always Available)

Tier 3 queries use the LLM Coordinator to interpret intent and call built-in tools. This tier is **ALWAYS available** without requiring the MCP Mode toggle.

**Built-in Tools (Tier 3):**
- `get_tasks` - Retrieve tasks with filters
- `get_projects` - Retrieve project information
- `search_tasks` - Semantic search on tasks
- `search_projects` - Semantic search on projects
- `create_task` - Create new tasks
- `update_task_status` - Change task status
- Worklog Agent - Task activity and progress tracking
- Retrieval Agent - Memory-enhanced search
- Memory System - Working, episodic, semantic, procedural memory

**When Tier 3 is Used:**
- Complex queries not matched by Tier 1 patterns
- Queries requiring context or memory (e.g., "What should I work on next?")
- Queries combining multiple filters or conditions
- Queries requiring interpretation (e.g., "What's blocking me?")

**Key Point:** Debug panel should show LLM time + tool calls. If a query needs web search or external data, it requires Tier 4 (MCP Mode toggle).

---

## Test Cases

### 2.1 Basic Queries

| ID | Query | Expected Tool(s) | Expected Behavior | Pass |
|----|-------|------------------|-------------------|------|
| 2.1 | "What are my tasks?" | `get_tasks` | Returns all tasks, formatted nicely | □ |
| 2.2 | "What's in progress?" | `get_tasks(status=in_progress)` | Filtered to in-progress only | □ |
| 2.3 | "Show me todo items" | `get_tasks(status=todo)` | Filtered to todo only | □ |
| 2.4 | "What's high priority?" | `get_tasks(priority=high)` | Filtered to high priority | □ |
| 2.5 | "Show me the AgentOps project" | `get_project(AgentOps)` | Project details + tasks | □ |
| 2.6 | "What's in the Voice Agent project?" | `get_project(Voice Agent)` | Project details + tasks | □ |

**Verification:**
```
□ Type query naturally
□ Verify correct tool called (check debug panel)
□ Verify response answers the question
□ Note latency for optimization comparison
```

### 2.2 Search Queries

| ID | Query | Expected Tool(s) | Expected Behavior | Pass |
|----|-------|------------------|-------------------|------|
| 2.7 | "Find tasks about debugging" | `search_tasks` | Semantic search results | □ |
| 2.8 | "Search for memory-related tasks" | `search_tasks` | Relevant results | □ |
| 2.9 | "Look for checkpointer" | `search_tasks` | Finds checkpointer task | □ |
| 2.10 | "Find projects related to agents" | `search_projects` | Relevant projects | □ |

### 2.3 Filtered Queries

| ID | Query | Expected Tool(s) | Expected Behavior | Pass |
|----|-------|------------------|-------------------|------|
| 2.11 | "What's high priority in AgentOps?" | `get_tasks` with filters | High priority + project filter | □ |
| 2.12 | "Show me completed tasks from this week" | `get_tasks` + date filter | Done tasks, recent | □ |
| 2.13 | "What tasks are blocked?" | `search_tasks` | Semantic search for "blocked" in task content* | □ |

*Note: "Blocked" is not a status field (only todo/in_progress/done exist). The system searches task titles, context, and notes for mentions of "blocked".

### 2.4 Ambiguous Queries

| ID | Query | Expected Behavior | Pass |
|----|-------|-------------------|------|
| 2.14 | "Show me the project" | Asks "which project?" OR shows all | □ |
| 2.15 | "What about memory?" | Interprets as search OR asks | □ |
| 2.16 | "What's next?" | Suggests todo/high-priority tasks | □ |

---

## Expected Latency Ranges

| Optimization State | Expected Latency |
|--------------------|------------------|
| All OFF (Baseline) | 15-25 seconds |
| Compress Only | 10-18 seconds |
| Streamlined Only | 12-20 seconds |
| Caching Only | 12-20 seconds (faster on 2nd+) |
| All ON | 6-12 seconds |

---

## Verification Checklist

```
□ Natural language queries work (not just commands)
□ Variations of same query work ("tasks" vs "to-dos" vs "items")
□ Agent uses correct tool for query type
□ Results are formatted readably (not raw JSON)
□ Debug panel shows tool calls and timing
□ Memory injection visible when enabled (see 06-memory-engineering.md)
```

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Basic Queries | 6 | __ | __ |
| Search Queries | 4 | __ | __ |
| Filtered Queries | 3 | __ | __ |
| Ambiguous Queries | 3 | __ | __ |
| **Total** | **16** | __ | __ |

**Average Latency (All ON):** ___s

---

*Text Queries Testing Guide v2.0*
