# 09 - Demo Dry Run

**Time:** 25 minutes
**Priority:** P0 - Demo rehearsal
**Updated:** January 9, 2026 (Milestone 6 - Current Demo Script)

---

## Overview

This is the full demo script. Run through it 3x before the actual demo to ensure consistency.

---

## Pre-Demo Setup (Night Before)

```
□ Run seed_demo_data.py to populate database
□ Verify .env has TAVILY_API_KEY
□ Test all demo commands 3x
□ Prepare backup plan (screenshots, video)
□ Charge laptop, test WiFi
```

## Day-Of Setup (15 min before)

```
□ App running on localhost:8501
□ All toggles ON: Context Engineering + Memory
□ MCP Mode: OFF (will toggle during demo)
□ Memory cleared (🗑️ Clear Session Memory)
□ Browser in presentation mode (hide bookmarks, dev tools)
□ Debug panel visible at bottom
□ Slides ready, synced with demo flow
```

---

## Demo Script (20 minutes)

### Intro (0-2 min)

```
□ Slides ready
□ App open and loaded
□ All toggles visible in sidebar
□ Memory Stats showing 0/0/0
```

**Talking Points:**
- Flow Companion: AI-powered task management
- Built on MongoDB Atlas + Claude
- Demonstrates Context Engineering + Memory Engineering

---

### Raw Speed - Slash Commands (2-4 min)

Show that slash commands bypass LLM and hit MongoDB directly.

| Command | Expected | Latency | Pass |
|---------|----------|---------|------|
| `/tasks` | All tasks | <200ms | □ |
| `/tasks status:in_progress` | Filtered | <150ms | □ |
| `/search debugging` | Search results | <500ms | □ |
| `/projects AgentOps` | Project details | <200ms | □ |

**Talking Points:**
- Direct to MongoDB - no LLM overhead
- Sub-second response times
- Good for power users

---

### LLM Queries (4-7 min)

Show natural language understanding with tool calling.

| Query | Expected | Pass |
|-------|----------|------|
| "What are my tasks?" | Tool called, formatted response | □ |
| "Show me the AgentOps project" | Tool called, filtered response | □ |
| "I finished the debugging doc" | Search → Confirm → Complete | □ |

**Talking Points:**
- Natural language interface
- LLM interprets intent, calls tools
- Same MongoDB data, different interface

---

### Voice (7-9 min)

Show voice input produces same results.

| Speak | Expected | Pass |
|-------|----------|------|
| 🎤 "What's in progress?" | Same as text | □ |
| 🎤 "Add a note to voice agent: WebSocket working" | Note added | □ |

**Talking Points:**
- Speech-to-text with Whisper/Deepgram
- Same LLM processing as text
- Hands-free operation

---

### Memory Engineering Demo (9-17 min) ⭐ CORE SECTION

**This is the main demo - show 5-tier memory architecture value.**

#### Step 1: Baseline Query (Slash Command)

| Action | Expected | Latency | Pass |
|--------|----------|---------|------|
| `/tasks` | Shows all tasks (15 from seed data) | <200ms | □ |

**Talking Point:** Direct MongoDB query - our baseline.

#### Step 2: Episodic Memory (Action History)

| Action | Expected | Pass |
|--------|----------|------|
| "What was completed on Project Alpha?" | Shows completed tasks from history | □ |
| Check debug panel | `get_action_history` tool called | □ |

**Talking Point:** Episodic Memory tracks what happened - persistent action history.

#### Step 3: Semantic Memory (Preferences)

| Action | Expected | Pass |
|--------|----------|------|
| "I'm focusing on Project Alpha" | Stores preference | □ |
| Check Memory Stats | Semantic Memory: 1 entry | □ |

**Talking Point:** Semantic Memory learns user preferences - stored permanently.

#### Step 4: Working Memory (Session Context)

| Action | Expected | Pass |
|--------|----------|------|
| "What should I work on next?" | Suggests Project Alpha tasks (uses preference) | □ |
| Check Memory Stats | Working Memory: 1 entry (current focus) | □ |

**Talking Point:** Working Memory maintains conversation context - knows "next" refers to Project Alpha.

#### Step 5: Memory Contrast (Toggle OFF)

| Action | Expected | Pass |
|--------|----------|------|
| [Toggle Working Memory OFF in sidebar] | Toggle shows unchecked | □ |
| "What should I work on next?" | Shows ALL tasks OR asks "which project?" | □ |

**Talking Point:** Without Working Memory, context is lost - system doesn't remember our focus.

**[Toggle Working Memory back ON]**

#### Step 6: MCP Agent (Web Search) - NEW in Milestone 6

| Action | Expected | Pass |
|--------|----------|------|
| [Toggle MCP Mode ON in Experimental section] | Shows "MCP Servers: 1 connected (Tavily)" | □ |
| "Research gaming market and create GTM project with tasks" | Multi-step workflow executes | □ |

**Expected Execution Flow:**
```
Step 1/3: Research gaming market trends
  → Routing to MCP Agent (Tavily)...
  → ✓ Research completed via tavily-search

Step 2/3: Create GTM project for gaming
  → Detected GTM project
  → Loading template from procedural memory...
  → ✓ Found template: GTM Roadmap Template
  → ✓ Project created: Gaming Market

Step 3/3: Generate tasks from template
  → Phase: Research (4 tasks)
  → Phase: Strategy (4 tasks)
  → Phase: Execution (4 tasks)
  → ✓ Generated 12 tasks across 3 phases

Multi-step execution complete: 3/3 steps successful
```

**Talking Points:**
- Procedural Memory: GTM template loaded automatically
- MCP Agent: Dynamic tool discovery (Tavily web search)
- Knowledge Cache: Research results cached for 7 days
- Multi-step workflows: Automatic orchestration

#### Step 7: Knowledge Cache (Memory Reuse)

| Action | Expected | Pass |
|--------|----------|------|
| "What do you know about gaming?" | Uses cached research (~0.5s, no new API call) | □ |
| Check response | Shows "📚 Source: Knowledge Cache" | □ |

**Talking Point:** Knowledge Cache (Semantic Memory) - avoids redundant API calls, 7-day TTL.

---

### Evals Dashboard (15-17 min) - Optional

Show metrics if time permits.

| Check | Expected | Pass |
|-------|----------|------|
| Dashboard loads | Shows 24 tests, 10 competencies | □ |
| Run eval | Tests execute | □ |
| Show metrics | Pass rates visible | □ |

**Talking Points:**
- Systematic evaluation framework
- 4 capabilities: AR, TTL, LRU, CR
- Quantified memory impact

---

### Wrap-up (17-25 min)

```
□ Debug panel shows clear breakdown
□ Latency numbers support narrative
□ All 5 memory types demonstrated
□ MCP Agent and multi-step workflows shown
□ Q&A ready
```

**Key Takeaways:**
1. **5-Tier Memory Architecture**: Working, Episodic, Semantic, Procedural, Shared
2. **Context Engineering**: 40-60% latency reduction through optimization
3. **MCP Agent (Milestone 6)**: Dynamic tool discovery with Tavily integration
4. **Multi-Step Workflows**: Automatic orchestration (Research → Create → Generate)
5. **Knowledge Cache**: 7-day TTL, 90% faster on repeated queries
6. **MongoDB Atlas**: Unified memory layer with vector search
7. **Production-Ready**: 47 tests, 90% coverage

---

## Final Verification

```
□ No console errors
□ No UI glitches
□ All queries work consistently
□ Demo runs 3x without issues
□ Backup plan ready (pre-recorded video)
□ Slides sync with demo flow
```

---

## Quick Reference Card

Print this for demo day:

```
┌─────────────────────────────────────────────────────────┐
│ FLOW COMPANION - DEMO QUICK REFERENCE (Jan 15, 2026)    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ EXACT DEMO SEQUENCE (8 Commands):                       │
│                                                          │
│ 1. /tasks                                                │
│    → Shows all 15 tasks (<200ms)                        │
│                                                          │
│ 2. "What was completed on Project Alpha?"               │
│    → Episodic Memory (action history)                   │
│                                                          │
│ 3. "I'm focusing on Project Alpha"                      │
│    → Semantic Memory (stores preference)                │
│                                                          │
│ 4. "What should I work on next?"                        │
│    → Working Memory (uses Project Alpha context)        │
│                                                          │
│ 5. [Toggle Working Memory OFF]                          │
│    → "What should I work on next?"                      │
│    → Shows context is lost                              │
│    [Toggle Working Memory back ON]                      │
│                                                          │
│ 6. [Toggle MCP Mode ON]                                 │
│    → "Research gaming market and create GTM project     │
│        with tasks"                                       │
│    → Multi-step workflow (3 steps, ~10s)                │
│    → Procedural Memory (GTM template)                   │
│    → MCP Agent (Tavily research)                        │
│    → 12 tasks created automatically                      │
│                                                          │
│ 7. "What do you know about gaming?"                     │
│    → Knowledge Cache hit (~0.5s, no API call)           │
│                                                          │
│ EXPECTED LATENCIES:                                      │
│   /tasks:            <200ms                              │
│   Text queries:      6-12s (optimized)                  │
│   MCP + multi-step:  ~10s (3 steps)                     │
│   Knowledge cache:   <1s (90% faster)                   │
│   Memory ops:        <50ms                               │
│                                                          │
│ STATS TO MENTION:                                        │
│   • 5-tier memory architecture                          │
│   • 47 tests, 90% coverage                              │
│   • 40-60% latency reduction (context engineering)      │
│   • 7-day knowledge cache TTL                           │
│   • Vector search: 1024-dim Voyage AI embeddings        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Query stuck | Refresh page, retry |
| Memory not updating | Check toggle is ON |
| Slow response | Mention "first query warming up" |
| Voice not working | Switch to text, "voice works similarly" |
| Tool error | "Let me try that differently" |

---

## Verification After Each Dry Run

```
□ All 7 demo commands executed successfully
□ Multi-step workflow created 12 tasks with correct phases
□ Knowledge cache showed "📚 Source: Knowledge Cache"
□ Memory toggles demonstrated clear before/after
□ Debug panel showed tool calls and timing
□ No errors in console
□ Backup plan ready if any step fails
```

---

*Demo Dry Run Guide v3.0*
*Updated for Milestone 6: MCP Agent & Multi-Step Workflows*
*MongoDB Developer Day - January 15, 2026*