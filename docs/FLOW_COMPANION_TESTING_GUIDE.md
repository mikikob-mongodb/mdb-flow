# Flow Companion - Manual Testing Guide

**Version:** 1.0  
**Demo Date:** January 8, 2026  
**Last Updated:** January 6, 2026

---

## Table of Contents

1. [Pre-Test Setup](#1-pre-test-setup)
2. [Section 1: Slash Commands (Direct DB)](#2-section-1-slash-commands-direct-db)
3. [Section 2: Text Queries (LLM)](#3-section-2-text-queries-llm)
4. [Section 3: Text Actions (LLM)](#4-section-3-text-actions-llm)
5. [Section 4: Voice Input](#5-section-4-voice-input)
6. [Section 5: Context Engineering Optimizations](#6-section-5-context-engineering-optimizations)
7. [Section 6: Memory Engineering](#7-section-6-memory-engineering)
8. [Section 7: Multi-Turn Conversations](#8-section-7-multi-turn-conversations)
9. [Section 8: Error Handling](#9-section-8-error-handling)
10. [Section 9: Demo Dry Run](#10-section-9-demo-dry-run)

---

## 1. Pre-Test Setup

### 1.1 Start the Applications

```bash
# Terminal 1: Main app
streamlit run streamlit_app.py --server.port 8501

# Terminal 2: Evals dashboard (optional)
streamlit run evals_app.py --server.port 8502
```

### 1.2 Verify Services

| Service | Check | Expected |
|---------|-------|----------|
| Streamlit | http://localhost:8501 | App loads, no errors |
| MongoDB | Sidebar shows connection | "Connected to MongoDB Atlas" |
| Memory | Sidebar shows memory panel | "🧠 Memory Settings" visible |

### 1.3 Reset Test State

Before each test session:

```
□ Click "🗑️ Clear Session Memory" in sidebar
□ Refresh the page (Cmd+R / Ctrl+R)
□ Verify "Memory Stats" shows 0 entries for short-term
```

### 1.4 Default Toggle Settings

For baseline testing, start with:

```
Context Engineering:
☑ Compress Results: ON
☑ Streamlined Prompt: ON
☑ Prompt Caching: ON

Memory Engineering:
☑ Enable Memory: ON
☑ Short-term Memory: ON
☑ Long-term Memory: ON
☑ Shared Memory: ON
☑ Context Injection: ON
```

---

## 2. Section 1: Slash Commands (Direct DB)

Slash commands bypass the LLM and query MongoDB directly. They should be **fast (<500ms)** regardless of optimization settings.

### 2.1 Command Reference

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
│ ├── limit:<n>               → Limit results (default: 50)                       │
│ │   └── limit:10                                                                │
│ └── (combinable)            → Multiple flags work together                      │
│     └── status:in_progress priority:high project:AgentOps                       │
│                                                                                  │
│ /projects [name]                                                                 │
│ ├── (no args)               → All projects with task counts                     │
│ └── <name>                  → Single project with its tasks                     │
│     └── /projects AgentOps                                                      │
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
│     ├── /search projects memory              (hybrid, projects)                 │
│     ├── /search vector projects agent        (vector, projects)                 │
│     └── /search text tasks checkpointer      (text, tasks)                      │
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

### 2.2 Task List Commands

| # | Command | Expected Result | Expected Latency |
|---|---------|-----------------|------------------|
| 1.1 | `/tasks` | All tasks, grouped by status | <200ms |
| 1.2 | `/tasks status:todo` | Only todo tasks | <150ms |
| 1.3 | `/tasks status:in_progress` | Only in-progress tasks | <150ms |
| 1.4 | `/tasks status:done` | Only completed tasks | <150ms |
| 1.5 | `/tasks priority:high` | High priority tasks only | <150ms |
| 1.6 | `/tasks priority:medium` | Medium priority tasks | <150ms |
| 1.7 | `/tasks priority:low` | Low priority tasks | <150ms |
| 1.8 | `/tasks project:AgentOps` | Tasks in AgentOps project | <200ms |
| 1.9 | `/tasks project:VoiceAgent` | Tasks in Voice Agent project | <200ms |
| 1.10 | `/tasks limit:5` | First 5 tasks only | <150ms |
| 1.11 | `/tasks status:in_progress priority:high` | In-progress AND high priority | <150ms |
| 1.12 | `/tasks status:todo project:AgentOps` | Todo tasks in AgentOps | <150ms |

**Test Procedure:**
```
□ Type command in chat
□ Verify results match expected filter
□ Check debug panel shows latency < target
□ Verify NO LLM time shown (direct DB)
□ Verify combined flags work (AND logic)
```

### 2.3 Project Commands

| # | Command | Expected Result | Expected Latency |
|---|---------|-----------------|------------------|
| 1.13 | `/projects` | All projects with task counts | <200ms |
| 1.14 | `/projects AgentOps` | AgentOps project with its tasks | <200ms |
| 1.15 | `/projects VoiceAgent` | Voice Agent project details | <200ms |

### 2.4 Search Commands - Mode Variants

| # | Command | Search Type | Expected Result | Expected Latency |
|---|---------|-------------|-----------------|------------------|
| 1.16 | `/search debugging` | Hybrid (default) | Best combined results | <500ms |
| 1.17 | `/search vector debugging` | Vector only | Semantic matches | <400ms |
| 1.18 | `/search text debugging` | Text only | Keyword matches | <200ms |
| 1.19 | `/search hybrid debugging` | Hybrid (explicit) | Same as default | <500ms |

**Search Mode Comparison:**

| Mode | Uses Embedding | Uses Text Index | Best For | Speed |
|------|----------------|-----------------|----------|-------|
| `hybrid` | ✅ | ✅ | Best overall results | Slowest |
| `vector` | ✅ | ❌ | Conceptual/semantic queries | Medium |
| `text` | ❌ | ✅ | Exact keyword matches | Fastest |

### 2.5 Search Commands - Target Variants

| # | Command | Target | Expected Result | Expected Latency |
|---|---------|--------|-----------------|------------------|
| 1.20 | `/search debugging` | Tasks (default) | Task search results | <500ms |
| 1.21 | `/search tasks debugging` | Tasks (explicit) | Task search results | <500ms |
| 1.22 | `/search projects memory` | Projects | Project search results | <500ms |
| 1.23 | `/search projects agent` | Projects | Agent-related projects | <500ms |

### 2.6 Search Commands - Combined Mode + Target

| # | Command | Mode | Target | Expected Latency |
|---|---------|------|--------|------------------|
| 1.24 | `/search vector tasks memory` | Vector | Tasks | <400ms |
| 1.25 | `/search text tasks checkpointer` | Text | Tasks | <200ms |
| 1.26 | `/search vector projects agent` | Vector | Projects | <400ms |
| 1.27 | `/search text projects ops` | Text | Projects | <200ms |

**Test Procedure for Search:**
```
□ Type search command
□ Verify results are relevant to query
□ Check debug panel shows breakdown:
  - Embedding time (for vector/hybrid) - should be 0 for text-only
  - MongoDB time
  - Search type indicator
□ Compare results across modes (vector vs text vs hybrid)
□ Verify text search is fastest, hybrid has best results
```

### 2.7 Action Commands (/do)

| # | Command | Expected Result | Expected Latency |
|---|---------|-----------------|------------------|
| 1.28 | `/do complete "debugging doc"` | Task marked done | <300ms |
| 1.29 | `/do start "checkpointer"` | Task marked in_progress | <300ms |
| 1.30 | `/do stop "checkpointer"` | Task marked todo | <300ms |
| 1.31 | `/do note "voice agent" "WebSocket working"` | Note added to task | <300ms |

**Test Procedure for Actions:**
```
□ Execute action command
□ Verify task status/content changed
□ Check activity_log updated on task
□ Verify works with partial task names (fuzzy match)
```

### 2.8 Help & Utility Commands

| # | Command | Expected Result |
|---|---------|-----------------|
| 1.32 | `/help` | Shows all available commands |
| 1.33 | `/help tasks` | Shows /tasks command usage |
| 1.34 | `/help search` | Shows /search command with modes |
| 1.35 | `/bench all` | Runs benchmarks, shows timing |

### 2.9 Error Cases

| # | Command | Expected Result |
|---|---------|-----------------|
| 1.36 | `/invalid` | "Unknown command. Try /help" |
| 1.37 | `/tasks status:invalid` | "Invalid status. Use: todo, in_progress, done" |
| 1.38 | `/tasks project:NonExistent` | "No tasks found for project 'NonExistent'" |
| 1.39 | `/search` (no query) | "Usage: /search [mode] [target] <query>" |
| 1.40 | `/do complete` (no task) | "Usage: /do complete <task>" |

### 2.10 Slash Command Verification Checklist

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

### 2.11 Search Mode Comparison Test

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

## 3. Section 2: Text Queries (LLM)

Text queries use the LLM to interpret intent and call appropriate tools.

### 3.1 Basic Queries

| # | Query | Expected Tool(s) | Expected Behavior |
|---|-------|------------------|-------------------|
| 2.1 | "What are my tasks?" | `get_tasks` | Returns all tasks, formatted nicely |
| 2.2 | "What's in progress?" | `get_tasks(status=in_progress)` | Filtered to in-progress only |
| 2.3 | "Show me todo items" | `get_tasks(status=todo)` | Filtered to todo only |
| 2.4 | "What's high priority?" | `get_tasks(priority=high)` | Filtered to high priority |
| 2.5 | "Show me the AgentOps project" | `get_project(AgentOps)` | Project details + tasks |
| 2.6 | "What's in the Voice Agent project?" | `get_project(Voice Agent)` | Project details + tasks |

**Test Procedure:**
```
□ Type query naturally
□ Verify correct tool called (check debug panel)
□ Verify response answers the question
□ Note latency for optimization comparison
```

### 3.2 Search Queries

| # | Query | Expected Tool(s) | Expected Behavior |
|---|-------|------------------|-------------------|
| 2.7 | "Find tasks about debugging" | `search_tasks` | Semantic search results |
| 2.8 | "Search for memory-related tasks" | `search_tasks` | Relevant results |
| 2.9 | "Look for checkpointer" | `search_tasks` | Finds checkpointer task |
| 2.10 | "Find projects related to agents" | `search_projects` | Relevant projects |

### 3.3 Expected Latency Ranges

| Optimization State | Expected Latency |
|--------------------|------------------|
| All OFF (Baseline) | 15-25 seconds |
| Compress Only | 10-18 seconds |
| Streamlined Only | 12-20 seconds |
| Caching Only | 12-20 seconds (faster on 2nd+ query) |
| All ON | 6-12 seconds |

---

## 4. Section 3: Text Actions (LLM)

Actions modify data and typically require search → confirm → execute flow.

### 4.1 Complete Task

| # | Query | Expected Flow | Expected Behavior |
|---|-------|---------------|-------------------|
| 3.1 | "I finished the debugging doc" | search → confirm → complete | Finds task, asks confirmation, completes |
| 3.2 | "Mark the checkpointer task as done" | search → confirm → complete | Finds task, completes it |
| 3.3 | "Complete the voice agent task" | search → confirm → complete | Finds and completes |

**Test Procedure:**
```
□ Say completion phrase
□ Agent should search for task
□ Agent shows match and asks for confirmation
□ Confirm with "yes" or "that's the one"
□ Verify task status changes to "done"
□ Check debug panel shows tool sequence
```

### 4.2 Start Task

| # | Query | Expected Flow | Expected Behavior |
|---|-------|---------------|-------------------|
| 3.4 | "I'm starting work on the checkpointer" | search → confirm → start | Changes status to in_progress |
| 3.5 | "Begin the documentation task" | search → confirm → start | Changes status to in_progress |

### 4.3 Add Note

| # | Query | Expected Flow | Expected Behavior |
|---|-------|---------------|-------------------|
| 3.6 | "Add a note to voice agent: WebSocket working" | search → add_note | Adds note to task |
| 3.7 | "Note on debugging task: found the bug" | search → add_note | Adds note to task |

### 4.4 Create Task

| # | Query | Expected Flow | Expected Behavior |
|---|-------|---------------|-------------------|
| 3.8 | "Create a task: Review PR #123" | create_task | Creates new task |
| 3.9 | "Add a new task for testing in AgentOps" | create_task | Creates task in project |

### 4.5 Action Verification Checklist

```
□ Agent searches before acting (doesn't guess)
□ Agent asks for confirmation on destructive actions
□ Agent handles "no" / "cancel" gracefully
□ Multiple matches show numbered options
□ Can select by number ("2") or description ("the second one")
□ Activity log updated on task after action
```

---

## 5. Section 4: Voice Input

Voice input should produce identical results to text input.

### 5.1 Voice Query Tests

| # | Speak | Expected | Same as Text? |
|---|-------|----------|---------------|
| 4.1 | "What are my tasks?" | Task list | ✓ Match text query 2.1 |
| 4.2 | "What's in progress?" | Filtered tasks | ✓ Match text query 2.2 |
| 4.3 | "Show me the AgentOps project" | Project details | ✓ Match text query 2.5 |
| 4.4 | "Find tasks about debugging" | Search results | ✓ Match text query 2.7 |

### 5.2 Voice Action Tests

| # | Speak | Expected | Same as Text? |
|---|-------|----------|---------------|
| 4.5 | "I finished the debugging doc" | Complete flow | ✓ Match text action 3.1 |
| 4.6 | "Add a note to voice agent: testing complete" | Add note flow | ✓ Match text action 3.6 |

### 5.3 Voice-Specific Tests

| # | Test | Expected Behavior |
|---|------|-------------------|
| 4.7 | Speak with filler words: "Um, what are, uh, my tasks?" | Should still understand |
| 4.8 | Speak quickly | Transcription accurate |
| 4.9 | Speak with background noise | Reasonable transcription |

**Test Procedure:**
```
□ Click microphone button
□ Speak query clearly
□ Verify transcription appears correctly
□ Verify response matches equivalent text query
□ Check debug panel shows same tools called
```

---

## 6. Section 5: Context Engineering Optimizations

Test each optimization individually to verify impact.

### 5.0 Research Background & Citations

Each optimization technique is grounded in published research. Understanding the "why" helps interpret test results.

#### Compress Results

**Technique:** Summarize tool outputs before including in context, reducing token count while preserving key information.

**Research Basis:**
- **LLMLingua** (Jiang et al., 2023) - "LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models"
  - Microsoft Research showed 2-10x compression with minimal performance loss
  - Key insight: LLMs are robust to information-dense compressed prompts
  - Paper: https://arxiv.org/abs/2310.05736

- **LongLLMLingua** (Jiang et al., 2023) - "LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios"
  - Extended compression for long contexts (RAG, tool results)
  - Showed improved performance by removing "noise" tokens
  - Paper: https://arxiv.org/abs/2310.06839

- **Learning to Compress Prompts** (Wingate et al., 2022) - "Learning to Compress Prompts with Gist Tokens"
  - Demonstrated 26x compression possible with learned compression
  - Paper: https://arxiv.org/abs/2304.08467

**Expected Impact:** 30-40% token reduction, 10-15% latency improvement

---

#### Streamlined Prompt

**Technique:** Use concise, directive system prompts instead of verbose instructions.

**Research Basis:**
- **Lost in the Middle** (Liu et al., 2023) - "Lost in the Middle: How Language Models Use Long Contexts"
  - Stanford/UC Berkeley showed LLMs struggle with information in middle of context
  - Shorter prompts = less "lost" information
  - Paper: https://arxiv.org/abs/2307.03172

- **Principled Instructions** (Zhou et al., 2023) - "Large Language Models Are Human-Level Prompt Engineers"
  - Showed concise, direct prompts often outperform verbose ones
  - Paper: https://arxiv.org/abs/2211.01910

- **Anthropic Prompt Engineering Guide** (2024)
  - "Be direct" - Claude responds well to clear, concise instructions
  - Verbose prompts can introduce ambiguity
  - Docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering

**Expected Impact:** 50-60% system prompt token reduction, 10-15% latency improvement, equivalent or better accuracy

---

#### Prompt Caching

**Technique:** Cache static portions of prompts (system prompt, tool definitions) to avoid reprocessing.

**Research Basis:**
- **Anthropic Prompt Caching** (2024) - Official feature documentation
  - Caches prompt prefixes for reuse across requests
  - Up to 90% reduction in latency for cached portions
  - Up to 50% cost reduction
  - Docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

- **Efficient Transformers Survey** (Tay et al., 2022) - "Efficient Transformers: A Survey"
  - Covers KV-cache optimization techniques
  - Foundational work on attention caching
  - Paper: https://arxiv.org/abs/2009.06732

- **PagedAttention / vLLM** (Kwon et al., 2023) - "Efficient Memory Management for Large Language Model Serving"
  - UC Berkeley work on KV-cache paging
  - Enables efficient prompt caching at inference time
  - Paper: https://arxiv.org/abs/2309.06180

**Expected Impact:** 20-30% latency reduction on subsequent requests, cache hits visible in debug panel

---

#### Combined Optimizations ("All Context Engineering")

**Research Basis:**
- **Context Engineering** (emerging field, 2024)
  - Term popularized by AI engineering community
  - Refers to systematic optimization of what goes into context window
  - Key practitioners: Anthropic, LangChain, LlamaIndex

- **RAG Optimization Studies** (various, 2023-2024)
  - Multiple studies show combining compression + caching + retrieval optimization yields multiplicative benefits
  - Example: RAPTOR (Sarthi et al., 2024) - recursive summarization for RAG

**Expected Combined Impact:** 40-60% latency reduction, 70-90% token reduction vs baseline

---

### 5.0.1 Memory Engineering Research

#### Short-Term Memory (Session Context)

**Research Basis:**
- **MemGPT** (Packer et al., 2023) - "MemGPT: Towards LLMs as Operating Systems"
  - UC Berkeley introduced hierarchical memory for LLMs
  - Main context = working memory, external storage = long-term
  - Paper: https://arxiv.org/abs/2310.08560

- **Generative Agents** (Park et al., 2023) - "Generative Agents: Interactive Simulacra of Human Behavior"
  - Stanford's influential paper on memory architectures
  - Introduced reflection, retrieval, and memory streams
  - Paper: https://arxiv.org/abs/2304.03442

**Expected Impact:** Context carryover within session, reduced redundant tool calls

---

#### Long-Term Memory (Episodic/Semantic)

**Research Basis:**
- **Reflexion** (Shinn et al., 2023) - "Reflexion: Language Agents with Verbal Reinforcement Learning"
  - Agents that learn from past experiences stored in memory
  - Paper: https://arxiv.org/abs/2303.11366

- **Cognitive Architectures for Language Agents** (Sumers et al., 2023)
  - Survey of memory systems in LLM agents
  - Categorizes episodic vs semantic memory approaches
  - Paper: https://arxiv.org/abs/2309.02427

- **RET-LLM** (Modarressi et al., 2023) - "RET-LLM: Towards a General Read-Write Memory for Large Language Models"
  - Explicit read/write memory operations
  - Paper: https://arxiv.org/abs/2305.14322

**Expected Impact:** Cross-session persistence, action history recall

---

#### Shared Memory (Agent Handoff)

**Research Basis:**
- **AutoGen** (Wu et al., 2023) - "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"
  - Microsoft Research on multi-agent coordination
  - Agents share context through conversation/memory
  - Paper: https://arxiv.org/abs/2308.08155

- **MetaGPT** (Hong et al., 2023) - "MetaGPT: Meta Programming for Multi-Agent Collaborative Framework"
  - Shared memory/blackboard for agent coordination
  - Paper: https://arxiv.org/abs/2308.00352

- **CAMEL** (Li et al., 2023) - "CAMEL: Communicative Agents for Mind Exploration"
  - Role-playing agents with shared context
  - Paper: https://arxiv.org/abs/2303.17760

**Expected Impact:** Seamless agent-to-agent handoffs, reduced redundant searches

---

### 5.0.2 Citation Summary Table

| Technique | Key Paper | Authors | Year | Key Finding |
|-----------|-----------|---------|------|-------------|
| Compress | LLMLingua | Jiang et al. | 2023 | 2-10x compression, minimal loss |
| Compress | LongLLMLingua | Jiang et al. | 2023 | Works for RAG/tool results |
| Streamlined | Lost in the Middle | Liu et al. | 2023 | LLMs struggle with long contexts |
| Caching | Anthropic Docs | Anthropic | 2024 | 90% latency reduction possible |
| Caching | vLLM/PagedAttention | Kwon et al. | 2023 | Efficient KV-cache management |
| Short-term | MemGPT | Packer et al. | 2023 | Hierarchical memory for LLMs |
| Long-term | Generative Agents | Park et al. | 2023 | Memory streams + reflection |
| Long-term | Reflexion | Shinn et al. | 2023 | Learning from past experiences |
| Shared | AutoGen | Wu et al. | 2023 | Multi-agent coordination |
| Shared | MetaGPT | Hong et al. | 2023 | Blackboard architecture |

---

### 6.1 Baseline (All OFF)

```
Settings:
☐ Compress Results: OFF
☐ Streamlined Prompt: OFF  
☐ Prompt Caching: OFF
```

| Test | Query | Record |
|------|-------|--------|
| 5.1 | "What are my tasks?" | Latency: ___s, Tokens In: ___ |
| 5.2 | "Show me AgentOps" | Latency: ___s, Tokens In: ___ |
| 5.3 | "Find debugging tasks" | Latency: ___s, Tokens In: ___ |

### 6.2 Compress Results Only

```
Settings:
☑ Compress Results: ON
☐ Streamlined Prompt: OFF
☐ Prompt Caching: OFF
```

**Expected Impact:**
- Tokens In: ↓ 30-40% (tool results compressed)
- Latency: ↓ 10-15%

| Test | Query | Record | vs Baseline |
|------|-------|--------|-------------|
| 5.4 | "What are my tasks?" | Latency: ___s, Tokens: ___ | ↓___% |
| 5.5 | "Show me AgentOps" | Latency: ___s, Tokens: ___ | ↓___% |

### 6.3 Streamlined Prompt Only

```
Settings:
☐ Compress Results: OFF
☑ Streamlined Prompt: ON
☐ Prompt Caching: OFF
```

**Expected Impact:**
- System prompt: ↓ 60% fewer tokens
- Latency: ↓ 10-15%
- Same accuracy (directive patterns work)

| Test | Query | Record | vs Baseline |
|------|-------|--------|-------------|
| 5.6 | "What are my tasks?" | Latency: ___s | ↓___% |
| 5.7 | "Complete the debugging doc" | Works correctly? Y/N | |

### 6.4 Prompt Caching Only

```
Settings:
☐ Compress Results: OFF
☐ Streamlined Prompt: OFF
☑ Prompt Caching: ON
```

**Expected Impact:**
- First query: Normal speed
- Subsequent queries: ↓ 20-30% (cache hit)

| Test | Query | Record | Cache Hit? |
|------|-------|--------|------------|
| 5.8 | "What are my tasks?" (1st) | Latency: ___s | ❌ Miss |
| 5.9 | "What's in progress?" (2nd) | Latency: ___s | ✅ Hit |
| 5.10 | "Show me AgentOps" (3rd) | Latency: ___s | ✅ Hit |

### 6.5 All Context Engineering ON

```
Settings:
☑ Compress Results: ON
☑ Streamlined Prompt: ON
☑ Prompt Caching: ON
```

**Expected Impact:**
- Combined: ↓ 40-60% latency vs baseline
- Tokens In: ↓ 70-90%
- Same or better accuracy

| Test | Query | Record | vs Baseline |
|------|-------|--------|-------------|
| 5.11 | "What are my tasks?" | Latency: ___s, Tokens: ___ | ↓___% |
| 5.12 | "Show me AgentOps" | Latency: ___s, Tokens: ___ | ↓___% |
| 5.13 | "Complete debugging doc" | Works correctly? Y/N | |

### 6.6 Optimization Comparison Summary

Fill in after testing:

| Config | Avg Latency | Avg Tokens In | vs Baseline |
|--------|-------------|---------------|-------------|
| Baseline | ___s | ___ | - |
| Compress | ___s | ___ | ↓___% |
| Streamlined | ___s | ___ | ↓___% |
| Caching | ___s | ___ | ↓___% |
| All Context | ___s | ___ | ↓___% |

---

## 7. Section 6: Memory Engineering

### 6.0 Memory Competencies Framework

Based on research from MemoryAgentBench, MemGPT, and other memory evaluation frameworks, we test four core competencies:

| Competency | Abbreviation | What It Tests | Difficulty |
|------------|--------------|---------------|------------|
| **Accurate Retrieval** | AR | Find specific info from history | Medium |
| **Test-Time Learning** | TTL | Learn new rules/context during conversation | Medium |
| **Long-Range Understanding** | LRU | Summarize across many turns | Hard |
| **Conflict Resolution** | CR | Handle contradictory/updated info | Very Hard |

**Key Research Finding:** All existing methods fail multi-hop conflict resolution (<7% accuracy). This is the hardest category.

---

### 6.1 Short-Term Memory (Session Context)

**Purpose:** Remember context within a conversation session.

#### Test 6.1.1: Accurate Retrieval - Single-Hop (AR-SH)

```
Settings:
☑ Short-term Memory: ON
☑ Context Injection: ON
```

| Step | Action | Expected | Competency |
|------|--------|----------|------------|
| 1 | "Show me the AgentOps project" | Shows AgentOps | Setup |
| 2 | "What's high priority?" | Filters to AgentOps high-priority | AR (single-hop) |
| 3 | Check debug panel | "Context injected: ✅" | Verify |

#### Test 6.1.2: Accurate Retrieval - Multi-Hop (AR-MH)

| Step | Action | Expected | Competency |
|------|--------|----------|------------|
| 1 | "Show me AgentOps" | Context: AgentOps | Setup |
| 2 | "Start the debugging task" | Context: AgentOps + debugging task | Setup |
| 3 | "What am I working on?" | "debugging task in AgentOps" | AR (multi-hop) |

#### Test 6.1.3: Test-Time Learning (TTL)

| Step | Action | Expected | Competency |
|------|--------|----------|------------|
| 1 | "I'm focusing on Voice Agent today" | Stores preference | TTL |
| 2 | "What should I do next?" | Suggests Voice Agent tasks | TTL |

#### Test 6.1.4: Conflict Resolution - Single-Hop (CR-SH)

| Step | Action | Expected | Competency |
|------|--------|----------|------------|
| 1 | "Show me AgentOps" | Context: AgentOps | Setup |
| 2 | "Actually, switch to Voice Agent" | Context updated to Voice Agent | CR |
| 3 | "What's high priority?" | Shows Voice Agent priorities | CR (single-hop) |

#### Test 6.1.5: Context Lost (Memory OFF)

```
Settings:
☐ Short-term Memory: OFF
☐ Context Injection: OFF
```

| Step | Action | Expected | Competency |
|------|--------|----------|------------|
| 1 | Clear memory, refresh | Clean state | Setup |
| 2 | "Show me AgentOps" | Shows AgentOps | - |
| 3 | "What's high priority?" | ALL high-priority OR asks "which project?" | Baseline |

**Key Insight:** The difference between 6.1.4 and 6.1.5 demonstrates memory value!

---

### 6.2 Long-Term Memory (Action History)

#### Test 6.1: Context Carryover (Memory ON)

```
Settings:
☑ Short-term Memory: ON
☑ Context Injection: ON
```

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Say: "Show me the AgentOps project" | Shows AgentOps | □ |
| 2 | Check sidebar "Current Context" | Shows "Project: AgentOps" | □ |
| 3 | Say: "What's high priority?" | Filters to AgentOps high-priority | □ |
| 4 | Check debug panel | Shows "Context injected: ✅" | □ |

#### Test 6.2: Context Lost (Memory OFF)

```
Settings:
☐ Short-term Memory: OFF
☐ Context Injection: OFF
```

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Clear memory, refresh page | Clean state | □ |
| 2 | Say: "Show me the AgentOps project" | Shows AgentOps | □ |
| 3 | Say: "What's high priority?" | Shows ALL high-priority OR asks "which project?" | □ |
| 4 | Check debug panel | NO "Context injected" indicator | □ |

**Key Insight:** The difference between 6.1 and 6.2 demonstrates memory value!

### 7.2 Long-Term Memory (Action History)

**Purpose:** Remember actions across sessions for history queries.

#### Test 6.3: Recording Actions (Memory ON)

```
Settings:
☑ Long-term Memory: ON
```

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Say: "Mark the debugging task as done" | Completes task | □ |
| 2 | Check debug panel | Shows memory write | □ |
| 3 | Check sidebar "Memory Stats" | Long-term count increased | □ |

#### Test 6.4: Recalling History (Memory ON)

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Say: "What did I complete today?" | Calls get_action_history tool | □ |
| 2 | Verify response | Lists the task you completed | □ |
| 3 | Say: "What have I been working on this week?" | Shows action history | □ |

#### Test 6.5: History Unavailable (Memory OFF)

```
Settings:
☐ Long-term Memory: OFF
```

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Say: "What did I do last week?" | Agent says it can't access history | □ |
| 2 | Check debug panel | get_action_history tool NOT available | □ |

### 7.3 Shared Memory (Agent Handoff)

**Purpose:** Allow agents to pass context to each other without re-searching.

#### Test 6.6: Agent Handoff (Memory ON)

```
Settings:
☑ Shared Memory: ON
```

| Step | Action | Expected | Check |
|------|--------|----------|-------|
| 1 | Say: "I finished the checkpointer task" | Completes task | □ |
| 2 | Check debug panel | Shows: | |
| | | - search_tasks (Retrieval) | □ |
| | | - Shared memory write | □ |
| | | - complete_task (Worklog) | □ |
| | | - Shared memory read | □ |
| | | - "Agent Handoff: ✅" | □ |

#### Test 6.7: Agent Handoff Diagram

Debug panel should show:
```
┌──────────┐    ┌──────────────┐    ┌──────────┐
│Retrieval │───▶│Shared Memory │───▶│ Worklog  │
└──────────┘    └──────────────┘    └──────────┘
```

### 7.4 Memory Toggle Combinations

| Short-term | Long-term | Shared | Expected Behavior |
|------------|-----------|--------|-------------------|
| ✅ | ✅ | ✅ | Full memory, best experience |
| ✅ | ❌ | ✅ | Context works, no history |
| ❌ | ✅ | ✅ | No context, has history |
| ❌ | ❌ | ❌ | Stateless, every turn fresh |

### 7.5 Memory Timing Overhead

Record memory operation times:

| Operation | Expected | Actual |
|-----------|----------|--------|
| Short-term read | <20ms | ___ms |
| Short-term write | <20ms | ___ms |
| Long-term read | <30ms | ___ms |
| Long-term write | <50ms | ___ms |
| Shared read | <15ms | ___ms |
| Shared write | <15ms | ___ms |

**Verify:** Memory overhead is negligible compared to LLM time.

---

## 8. Section 7: Multi-Turn Conversations

### 7.1 Context Across Turns

| Turn | Query | Expected | Check |
|------|-------|----------|-------|
| 1 | "Show me AgentOps" | Project info | □ |
| 2 | "What's in progress?" | AgentOps in-progress tasks | □ |
| 3 | "Any high priority?" | AgentOps high-priority tasks | □ |
| 4 | "Complete the first one" | Completes from context | □ |
| 5 | "What did I just do?" | Recalls the completion | □ |

### 7.2 Disambiguation

| Turn | Query | Expected | Check |
|------|-------|----------|-------|
| 1 | "Complete the webinar task" | Shows numbered options (multiple webinars) | □ |
| 2 | "The February one" | Selects correct task | □ |

Alternative:
| Turn | Query | Expected | Check |
|------|-------|----------|-------|
| 1 | "Complete the doc task" | Shows numbered options | □ |
| 2 | "2" | Selects second option | □ |

### 7.3 Mixed Input Types

| Turn | Type | Query | Expected | Check |
|------|------|-------|----------|-------|
| 1 | Text | "Show me AgentOps" | Project info | □ |
| 2 | Voice | "What's high priority?" | Filtered results | □ |
| 3 | Text | "Complete the first one" | Completes task | □ |

---

## 9. Section 8: Error Handling

### 8.1 Not Found Errors

| # | Query | Expected Response |
|---|-------|-------------------|
| 8.1 | "Show me the Kubernetes project" | "I couldn't find a project called Kubernetes" |
| 8.2 | "Complete the blockchain task" | "I couldn't find a task matching 'blockchain'" |
| 8.3 | `/tasks project:NonExistent` | "No tasks found for project 'NonExistent'" |

### 8.2 Invalid Input

| # | Input | Expected Response |
|---|-------|-------------------|
| 8.4 | "" (empty) | Prompts for input |
| 8.5 | `/invalid` | Shows available commands |
| 8.6 | "asdfghjkl" | Asks for clarification |

### 8.3 Graceful Degradation

| # | Scenario | Expected |
|---|----------|----------|
| 8.7 | Memory disabled mid-conversation | Works without memory |
| 8.8 | Very long query (500+ chars) | Handles gracefully |
| 8.9 | Special characters in query | Handles or sanitizes |

---

## 10. Section 9: Demo Dry Run

Run through the exact demo script from FLOW_COMPANION_MILESTONES.md.

### Demo Checklist (20 minutes)

#### Intro (0-2 min)
```
□ Slides ready
□ App open and loaded
□ All toggles ON
```

#### Raw Speed - Slash Commands (2-4 min)
```
□ /tasks                          Works, <200ms
□ /tasks status:in_progress       Works, <150ms
□ /tasks search debugging         Works, <500ms
□ /projects AgentOps              Works, <200ms
```

#### LLM Queries (4-7 min)
```
□ "What are my tasks?"            Tool called, formatted response
□ "Show me the AgentOps project"  Tool called, filtered response
□ "I finished the debugging doc"  Search → Confirm → Complete
```

#### Voice (7-9 min)
```
□ 🎤 "What's in progress?"        Same result as text
□ 🎤 "Add a note to voice agent: WebSocket working"   Note added
```

#### Memory Patterns (9-15 min)
```
□ "Show me AgentOps"              Context stored
□ "What's high priority?"         Context used (filtered)

□ [Toggle short-term OFF]
□ "What's high priority?"         Context lost (all or asks)

□ [Toggle short-term ON]
□ "What did I complete last week?" Long-term works

□ [Toggle long-term OFF]
□ "What did I complete last week?" No history available

□ [Toggle all ON]
□ "I finished the checkpointer task"  Handoff visible in debug
```

#### Wrap-up (15-17 min)
```
□ Debug panel shows clear breakdown
□ Latency numbers support narrative
□ Memory toggles visible for demo
```

### Final Verification

```
□ No console errors
□ No UI glitches
□ All queries work consistently
□ Demo can run 3x without issues
□ Backup plan ready (pre-recorded video)
```

---

## Quick Reference Card

Print this for demo day:

```
┌─────────────────────────────────────────────────────────────┐
│ FLOW COMPANION - QUICK REFERENCE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ SLASH COMMANDS (fast, direct DB):                          │
│   /tasks                    All tasks                       │
│   /tasks status:X           Filter by status                │
│   /tasks project:X          Filter by project               │
│   /search <query>           Hybrid search                   │
│   /projects                 All projects                    │
│                                                             │
│ TEXT QUERIES (LLM):                                         │
│   "What are my tasks?"                                      │
│   "Show me the AgentOps project"                           │
│   "Find tasks about debugging"                              │
│                                                             │
│ ACTIONS:                                                    │
│   "I finished the X task"   Complete                        │
│   "Start the X task"        Start                           │
│   "Add a note to X: ..."    Add note                        │
│                                                             │
│ MEMORY DEMOS:                                               │
│   "Show me AgentOps" → "What's high priority?" (context)   │
│   "What did I complete today?" (history)                   │
│   "I finished X" → watch debug for handoff                 │
│                                                             │
│ EXPECTED LATENCIES:                                         │
│   Slash commands: <500ms                                    │
│   LLM queries: 6-12s (optimized), 15-25s (baseline)        │
│   Memory operations: <50ms                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Flow Companion v3.0 - Manual Testing Guide*
*MongoDB Developer Day - January 8, 2026*