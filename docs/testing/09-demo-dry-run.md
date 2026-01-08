# 09 - Demo Dry Run

**Time:** 20 minutes  
**Priority:** P0 - Demo rehearsal

---

## Overview

This is the full demo script. Run through it 3x before the actual demo to ensure consistency.

---

## Pre-Demo Setup

```
□ App running on localhost:8501
□ Evals dashboard on localhost:8502 (optional)
□ All toggles ON (Context Engineering + Memory)
□ Memory cleared (clean state)
□ Browser in presentation mode (hide bookmarks, etc.)
□ Backup video ready (in case of live issues)
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

### Memory Patterns (9-15 min)

This is the core demo section - show memory value.

#### Working Memory Demo

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "Show me AgentOps" | Context stored | □ |
| 2 | "What's high priority?" | Filtered to AgentOps | □ |
| 3 | Check Memory Stats | Working Memory: 1 | □ |

**Talking Point:** Working Memory maintains session context.

#### Working Memory OFF

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | [Toggle Working Memory OFF] | | □ |
| 2 | "What's high priority?" | ALL high priority OR asks "which project?" | □ |

**Talking Point:** Without Working Memory, context is lost.

#### Working Memory ON + Semantic Memory

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | [Toggle Working Memory ON] | | □ |
| 2 | "I'm focusing on Voice Agent" | Preference stored | □ |
| 3 | Check Memory Stats | Semantic Memory: 1 | □ |
| 4 | "What should I do next?" | Suggests Voice Agent tasks | □ |

**Talking Point:** Semantic Memory learns preferences.

#### Episodic Memory Demo

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | "What did I complete today?" | Shows history | □ |
| 2 | [Toggle Episodic Memory OFF] | | □ |
| 3 | "What did I complete today?" | Can't access history | □ |

**Talking Point:** Episodic Memory provides action history.

#### Shared Memory Demo

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | [All toggles ON] | | □ |
| 2 | "I finished the checkpointer task" | Complete flow | □ |
| 3 | Check debug panel | Handoff visible | □ |

**Talking Point:** Shared Memory enables agent coordination.

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

### Wrap-up (17-20 min)

```
□ Debug panel shows clear breakdown
□ Latency numbers support narrative
□ Memory toggles demonstrated value
□ Q&A ready
```

**Key Takeaways:**
1. Context Engineering: 40-60% latency reduction
2. Memory Engineering: 5 types, 4 capabilities
3. MongoDB as unified memory layer
4. Systematic evaluation approach

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
│ FLOW COMPANION - DEMO QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ SLASH COMMANDS (fast, direct DB):                       │
│   /tasks                    All tasks                    │
│   /tasks status:X           Filter by status             │
│   /search <query>           Hybrid search                │
│   /projects                 All projects                 │
│                                                          │
│ TEXT QUERIES (LLM):                                      │
│   "What are my tasks?"                                   │
│   "Show me the AgentOps project"                        │
│   "Find tasks about debugging"                           │
│                                                          │
│ ACTIONS:                                                 │
│   "I finished the X task"   Complete                     │
│   "Start the X task"        Start                        │
│   "Add a note to X: ..."    Add note                     │
│                                                          │
│ MEMORY DEMOS:                                            │
│   Working:   "Show me AgentOps" → "What's high priority?"│
│   Semantic:  "I'm focusing on Voice Agent"              │
│   Episodic:  "What did I complete today?"               │
│   Shared:    "I finished X" → watch debug for handoff   │
│                                                          │
│ EXPECTED LATENCIES:                                      │
│   Slash commands: <500ms                                 │
│   LLM queries: 6-12s (optimized)                        │
│   Memory operations: <50ms                               │
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

*Demo Dry Run Guide v2.0*
*MongoDB Developer Day - January 15, 2026*