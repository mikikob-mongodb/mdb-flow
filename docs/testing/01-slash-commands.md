# 01 - Tier 1 & 2: Slash Commands + Natural Language Patterns

**Time:** 15 minutes
**Priority:** P0 - Core functionality
**Version:** v3.2 (Updated tier ordering for logical presentation)

---

## Overview

This guide covers the first two tiers of Flow Companion's 4-tier query routing architecture:

- **Tier 1: Explicit Slash Commands** - Direct MongoDB queries with full user control (0ms, $0)
- **Tier 2: Natural Language Pattern Detection** - Regex-based patterns that convert natural language to slash commands (0ms, $0)

Both tiers are **instant (<500ms)** and free, regardless of optimization settings.

**Key Point:** Debug panel should show NO LLM time for Tier 1 & 2 queries.

**Logical Flow:** Tier 1 (most explicit) → Tier 2 (natural language helper) → Tier 3 (LLM reasoning) → Tier 4 (external tools)

---

## Tier 1: Explicit Slash Commands

Slash commands provide direct MongoDB access with full user control. They offer the most explicit interface - users know exactly what will execute.

**Characteristics:**
- **Control**: Maximum precision and predictability
- **Speed**: Instant (~0ms)
- **Cost**: Free ($0)
- **Syntax**: Requires learning command structure
- **Use Case**: Power users, automation, scripting

---

## Command Reference

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ SLASH COMMAND REFERENCE                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ /tasks [flags]                                                                   │
│ ├── (no flags)              → All tasks, grouped by status                      │
│ ├── status:<value>          → Filter by status                                  │
│ │   ├── status:todo                                                             │
│ │   ├── status:in_progress                                                      │
│ │   └── status:done                                                             │
│ ├── priority:<value>        → Filter by priority                                │
│ │   ├── priority:high                                                           │
│ │   ├── priority:medium                                                         │
│ │   └── priority:low                                                            │
│ ├── project:<name>          → Filter by project                                 │
│ │   └── project:AgentOps                                                        │
│ ├── assignee:<name>         → Filter by assignee                                │
│ │   └── assignee:Mike Chen                                                      │
│ ├── blocked                 → Show only blocked tasks                           │
│ ├── overdue                 → Show only overdue tasks                           │
│ ├── due:<filter>            → Filter by due date                                │
│ │   ├── due:today           → Due today                                         │
│ │   ├── due:week            → Due this week                                     │
│ │   └── due:next-week       → Due next week                                     │
│ ├── limit:<n>               → Limit results (default: 50)                       │
│ │   └── limit:10                                                                │
│ └── (combinable)            → Multiple flags work together                      │
│     └── status:in_progress priority:high assignee:Mike                          │
│                                                                                  │
│ /projects [name|flags]                                                           │
│ ├── (no args)               → All projects with task counts                     │
│ ├── <name>                  → Single project with its tasks                     │
│ │   └── /projects AgentOps                                                      │
│ ├── stakeholder:<name>      → Filter by stakeholder                             │
│ │   └── stakeholder:Mike Chen                                                   │
│ └── status:<value>          → Filter by status                                  │
│     ├── status:active                                                           │
│     ├── status:planned                                                          │
│     ├── status:completed                                                        │
│     └── status:archived                                                         │
│                                                                                  │
│ /search [mode] [target] <query>                                                 │
│ ├── (default)               → Hybrid search on tasks                            │
│ │   └── /search debugging                                                       │
│ ├── mode:                                                                       │
│ │   ├── vector              → Semantic search (Voyage embeddings)               │
│ │   ├── text                → Keyword search (MongoDB text index)               │
│ │   └── hybrid              → Combined vector + text (default)                  │
│ ├── target:                                                                     │
│ │   ├── tasks               → Search tasks (default)                            │
│ │   └── projects            → Search projects                                   │
│ └── examples:                                                                   │
│     ├── /search debugging                    (hybrid, tasks)                    │
│     ├── /search vector debugging             (vector only, tasks)               │
│     ├── /search text debugging               (text only, tasks)                 │
│     └── /search projects memory              (hybrid, projects)                 │
│                                                                                  │
│ /do <action> <target> [args]                                                    │
│ ├── complete "<task>"       → Mark task as done                                 │
│ │   └── /do complete "debugging doc"                                            │
│ ├── start "<task>"          → Mark task as in_progress                          │
│ │   └── /do start "checkpointer"                                                │
│ ├── stop "<task>"           → Mark task as todo                                 │
│ │   └── /do stop "checkpointer"                                                 │
│ └── note "<task>" "<note>"  → Add note to task                                  │
│     └── /do note "voice agent" "WebSocket working"                              │
│                                                                                  │
│ /help [command]                                                                  │
│ ├── (no args)               → Show all commands                                 │
│ └── <command>               → Show help for specific command                    │
│     └── /help search                                                            │
│                                                                                  │
│ /bench [target]                                                                  │
│ ├── all                     → Benchmark all operations                          │
│ ├── search                  → Benchmark search variants                         │
│ └── queries                 → Benchmark common queries                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tier 2: Natural Language Pattern Detection

Natural language patterns automatically convert common queries to slash commands using regex matching. This provides a natural language interface without LLM costs.

**Characteristics:**
- **UX**: Natural, beginner-friendly
- **Speed**: Instant (~0ms)
- **Cost**: Free ($0)
- **Flexibility**: Limited to predefined patterns
- **Use Case**: Common queries, casual users

### Pattern Examples

| Natural Language Query | Detected Pattern | Resulting Command |
|------------------------|------------------|-------------------|
| "What's urgent?" | High priority pattern | `/tasks priority:high status:todo,in_progress` |
| "What's in progress?" | Status pattern | `/tasks status:in_progress` |
| "What's done?" | Status pattern | `/tasks status:done` |
| "What's todo?" | Status pattern | `/tasks status:todo` |
| "Show me AgentOps" | Project pattern | `/projects AgentOps` |
| "What's in the Voice Agent project?" | Project-specific tasks | `/tasks project:Voice Agent` |

**Recent Updates (v3.2):**
- Urgent/important queries now filter by status (exclude completed tasks)
- Support for comma-separated status values in slash commands
- "What's urgent?" returns only `todo` or `in_progress` high-priority tasks

---

## Test Cases

### 0. Tier 1: Explicit Slash Commands

Test slash command syntax and execution.

### 0.1 Task List Commands

| ID | Command | Expected Result | Target Latency | Pass |
|----|---------|-----------------|----------------|------|
| 1.1 | `/tasks` | All tasks, grouped by status | <200ms | □ |
| 1.2 | `/tasks status:todo` | Only todo tasks | <150ms | □ |
| 1.3 | `/tasks status:in_progress` | Only in-progress tasks | <150ms | □ |
| 1.4 | `/tasks status:done` | Only completed tasks | <150ms | □ |
| 1.5 | `/tasks priority:high` | High priority tasks only | <150ms | □ |
| 1.6 | `/tasks priority:medium` | Medium priority tasks | <150ms | □ |
| 1.7 | `/tasks priority:low` | Low priority tasks | <150ms | □ |
| 1.8 | `/tasks project:AgentOps` | Tasks in AgentOps project | <200ms | □ |
| 1.9 | `/tasks project:VoiceAgent` | Tasks in Voice Agent project | <200ms | □ |
| 1.10 | `/tasks limit:5` | First 5 tasks only | <150ms | □ |
| 1.11 | `/tasks status:in_progress priority:high` | In-progress AND high priority | <150ms | □ |
| 1.12 | `/tasks status:todo project:AgentOps` | Todo tasks in AgentOps | <150ms | □ |
| 1.13 | `/tasks assignee:Mike Chen` | Tasks assigned to Mike Chen | <150ms | □ |
| 1.14 | `/tasks blocked` | Only tasks with blockers | <150ms | □ |
| 1.15 | `/tasks overdue` | Only overdue tasks (not done) | <150ms | □ |
| 1.16 | `/tasks due:today` | Tasks due today | <150ms | □ |
| 1.17 | `/tasks due:week` | Tasks due this week | <150ms | □ |
| 1.18 | `/tasks due:next-week` | Tasks due next week | <150ms | □ |
| 1.19 | `/tasks assignee:Mike Chen status:in_progress` | Mike's in-progress tasks | <150ms | □ |

**Verification:**
```
□ Type command in chat
□ Verify results match expected filter
□ Check debug panel shows latency < target
□ Verify NO LLM time shown (direct DB)
□ Verify combined flags work (AND logic)
```

### 1.2 Project Commands

| ID | Command | Expected Result | Target Latency | Pass |
|----|---------|-----------------|----------------|------|
| 1.20 | `/projects` | All projects with task counts | <200ms | □ |
| 1.21 | `/projects AgentOps` | AgentOps project with its tasks | <200ms | □ |
| 1.22 | `/projects VoiceAgent` | Voice Agent project details | <200ms | □ |
| 1.23 | `/projects stakeholder:Mike Chen` | Projects with Mike as stakeholder | <150ms | □ |
| 1.24 | `/projects status:active` | Active projects only | <150ms | □ |
| 1.25 | `/projects stakeholder:Sarah status:active` | Sarah's active projects | <150ms | □ |

### 1.3 Search Commands - Mode Variants

| ID | Command | Search Type | Target Latency | Pass |
|----|---------|-------------|----------------|------|
| 1.26 | `/search debugging` | Hybrid (default) | <500ms | □ |
| 1.27 | `/search vector debugging` | Vector only | <400ms | □ |
| 1.28 | `/search text debugging` | Text only | <200ms | □ |
| 1.29 | `/search hybrid debugging` | Hybrid (explicit) | <500ms | □ |

**Search Mode Comparison:**

| Mode | Uses Embedding | Uses Text Index | Best For | Speed |
|------|----------------|-----------------|----------|-------|
| `hybrid` | ✅ | ✅ | Best overall results | Slowest |
| `vector` | ✅ | ❌ | Conceptual/semantic queries | Medium |
| `text` | ❌ | ✅ | Exact keyword matches | Fastest |

### 1.4 Search Commands - Target Variants

| ID | Command | Target | Target Latency | Pass |
|----|---------|--------|----------------|------|
| 1.30 | `/search debugging` | Tasks (default) | <500ms | □ |
| 1.31 | `/search tasks debugging` | Tasks (explicit) | <500ms | □ |
| 1.32 | `/search projects memory` | Projects | <500ms | □ |
| 1.33 | `/search projects agent` | Projects | <500ms | □ |

### 1.5 Search Commands - Combined Mode + Target

| ID | Command | Mode | Target | Target Latency | Pass |
|----|---------|------|--------|----------------|------|
| 1.34 | `/search vector tasks memory` | Vector | Tasks | <400ms | □ |
| 1.35 | `/search text tasks checkpointer` | Text | Tasks | <200ms | □ |
| 1.36 | `/search vector projects agent` | Vector | Projects | <400ms | □ |
| 1.37 | `/search text projects ops` | Text | Projects | <200ms | □ |

**Search Verification:**
```
□ Type search command
□ Verify results are relevant to query
□ Check debug panel shows breakdown:
  - Embedding time (for vector/hybrid)
  - MongoDB time
  - Search type indicator
□ Compare results across modes
□ Verify text search is fastest, hybrid has best results
```

### 1.6 Action Commands (/do)

| ID | Command | Expected Result | Target Latency | Pass |
|----|---------|-----------------|----------------|------|
| 1.38 | `/do complete "debugging doc"` | Task marked done | <300ms | □ |
| 1.39 | `/do start "checkpointer"` | Task marked in_progress | <300ms | □ |
| 1.40 | `/do stop "checkpointer"` | Task marked todo | <300ms | □ |
| 1.41 | `/do note "voice agent" "WebSocket working"` | Note added to task | <300ms | □ |

**Action Verification:**
```
□ Execute action command
□ Verify task status/content changed
□ Check activity_log updated on task
□ Verify works with partial task names (fuzzy match)
```

### 1.7 Help & Utility Commands

| ID | Command | Expected Result | Pass |
|----|---------|-----------------|------|
| 1.42 | `/help` | Shows all available commands | □ |
| 1.43 | `/help tasks` | Shows /tasks command usage | □ |
| 1.44 | `/help search` | Shows /search command with modes | □ |
| 1.45 | `/bench all` | Runs benchmarks, shows timing | □ |

### 1.8 Error Cases

| ID | Command | Expected Result | Pass |
|----|---------|-----------------|------|
| 1.46 | `/invalid` | "Unknown command. Try /help" | □ |
| 1.47 | `/tasks status:invalid` | "Invalid status. Use: todo, in_progress, done" | □ |
| 1.48 | `/tasks project:NonExistent` | "No tasks found for project..." | □ |
| 1.49 | `/search` (no query) | "Usage: /search [mode] [target] <query>" | □ |
| 1.50 | `/do complete` (no task) | "Usage: /do complete <task>" | □ |

---

### 1. Tier 2: Natural Language Pattern Detection

Test that natural language queries are automatically converted to slash commands.

| ID | Natural Language Query | Expected Command | Expected Filters | Pass |
|----|------------------------|------------------|------------------|------|
| 2.1 | "What's urgent?" | `/tasks` | `priority:high status:todo,in_progress` | □ |
| 2.2 | "What's important?" | `/tasks` | `priority:high status:todo,in_progress` | □ |
| 2.3 | "What's in progress?" | `/tasks` | `status:in_progress` | □ |
| 2.4 | "What's done?" | `/tasks` | `status:done` | □ |
| 2.5 | "What's todo?" | `/tasks` | `status:todo` | □ |
| 2.6 | "Show me AgentOps" | `/projects` | AgentOps project | □ |
| 2.7 | "What's in the Voice Agent project?" | `/tasks` | `project:Voice Agent` | □ |
| 2.8 | "Show me Mike's tasks" | `/tasks` | `assignee:Mike` | □ |
| 2.9 | "What's Mike working on?" | `/tasks` | `assignee:Mike` | □ |
| 2.10 | "What is Sarah doing?" | `/tasks` | `assignee:Sarah` | □ |
| 2.11 | "What's blocked?" | `/tasks` | `blocked` | □ |
| 2.12 | "Show me blocked tasks" | `/tasks` | `blocked` | □ |
| 2.13 | "What's overdue?" | `/tasks` | `overdue` | □ |
| 2.14 | "What's late?" | `/tasks` | `overdue` | □ |
| 2.15 | "What's due today?" | `/tasks` | `due:today` | □ |
| 2.16 | "What's due this week?" | `/tasks` | `due:week` | □ |
| 2.17 | "Show me Mike's projects" | `/projects` | `stakeholder:Mike` | □ |
| 2.18 | "What projects is Sarah involved in?" | `/projects` | `stakeholder:Sarah` | □ |

**Critical Verification (ID 2.1 & 2.2):**
```
□ Query: "What's urgent?"
□ Debug panel shows: ⚡ /tasks priority:high status:todo,in_progress
□ Results include ONLY todo or in_progress tasks (no done tasks)
□ All results have priority=high
□ Executes in <200ms
□ No LLM time shown
```

**New Fields Verification (ID 2.8-2.18):**
```
□ Query: "Show me Mike's tasks"
□ Debug panel shows: ⚡ /tasks assignee:Mike
□ Results show tasks with assignee=Mike Chen (or Mike)
□ Task headers show 👤 Mike Chen badges
□ No LLM time shown (direct slash command conversion)

□ Query: "What's blocked?"
□ Debug panel shows: ⚡ /tasks blocked
□ Results show only tasks with blockers
□ Task headers show 🚧 blocker indicators
□ Blockers displayed when task expanded

□ Query: "What's overdue?"
□ Debug panel shows: ⚡ /tasks overdue
□ Results show tasks past due date and not done
□ Task headers show ⚠️ OVERDUE warnings in red

□ Query: "Show me Mike's projects"
□ Debug panel shows: ⚡ /projects stakeholder:Mike
□ Results show projects with Mike as stakeholder
□ Stakeholders list shown in project details
```

**Pattern Detection Verification:**
```
□ Natural language converts to slash command (see debug panel)
□ Command executes instantly (<200ms)
□ No LLM token usage shown
□ Results match expected filters
□ Completed/done tasks excluded from urgent queries (v3.2 fix)
□ Multi-word names supported (Mike Chen, Sarah Thompson)
```

---

## Search Mode Comparison Test

Run the same query with all three modes and compare:

| Query: "debugging" | Results | Latency | Notes |
|--------------------|---------|---------|-------|
| `/search debugging` (hybrid) | ___ results | ___ms | Best quality |
| `/search vector debugging` | ___ results | ___ms | Semantic |
| `/search text debugging` | ___ results | ___ms | Fastest |

**Expected:**
- Text: Fastest, finds exact "debugging" matches
- Vector: Finds conceptually related (monitoring, testing, etc.)
- Hybrid: Best of both, highest relevance ranking

---

## Final Verification Checklist

```
□ All commands return formatted tables (not raw JSON)
□ Empty results show helpful message (not error)
□ Invalid commands show usage help
□ Latency is consistent across multiple runs
□ Optimization toggles have NO effect on slash command speed
□ Combined flags work correctly (AND logic)
□ Search modes produce different results (vector vs text)
□ Partial task names work in /do commands
□ All commands work without LLM (check debug panel)
```

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Task Commands | 19 | __ | __ |
| Project Commands | 6 | __ | __ |
| Search Mode | 4 | __ | __ |
| Search Target | 4 | __ | __ |
| Search Combined | 4 | __ | __ |
| Action Commands | 4 | __ | __ |
| Help/Utility | 4 | __ | __ |
| Error Cases | 5 | __ | __ |
| Natural Language Patterns (Basic) | 7 | __ | __ |
| Natural Language Patterns (New Fields) | 11 | __ | __ |
| **Total** | **68** | __ | __ |

---

*Slash Commands Testing Guide v2.0*
