# Flow Companion — Demo Readiness Guide

**Version:** 3.0 (Milestone 6)
**Demo Date:** January 15, 2026
**Demo Length:** 25 minutes
**Audience:** Demo owner, future maintainers, DevRel peers

**Goal:** Reproducible, bug-bashed, narratable, confidence-inducing demo

---

## Table of Contents

**Part I: Strategic Planning (Monday-Wednesday)**
- [Core Principles](#core-principles)
- [Section 0: Define "Perfect Shape"](#section-0--define-perfect-shape-monday--30-min)
- [Section 1: Make Sure Everything Works](#section-1--make-sure-everything-works-monday--23-hrs)
- [Section 2: Bug Bash & Guardrails](#section-2--bug-bash--guardrails-mon-pm--tues)
- [Section 3: Command Test Matrix](#section-3--command-test-matrix-must-pass)
- [Section 4: Performance & Latency Gates](#section-4--performance--latency-gates)
- [Section 5: Refactor & Cleanup](#section-5--refactor--cleanup-tuesday-only-time-boxed)
- [Section 6: Documentation Pass](#section-6--documentation-pass-tuesday-pm)
- [Section 7: Wednesday Final Hardening](#section-7--wednesday-final-hardening)
- [Section 8: Live Failure Playbook](#section-8--live-failure-playbook-do-not-improvise)
- [Section 9: Final Gates](#section-9--final-gates-must-be-yes)

**Part II: Tactical Execution (Night Before & Day Of)**
- [Night Before Demo](#night-before-demo-january-14-2026)
- [Morning of Demo](#morning-of-demo-january-15-2026)
- [During Demo - Command Sequence](#during-demo---command-sequence)
- [Troubleshooting During Demo](#troubleshooting-during-demo)
- [Post-Demo](#post-demo)

---

# Part I: Strategic Planning

## Core Principles (read once, obey always)

- **Stabilize before beautify**

    Bug bash + reproducibility first. Refactors only after P0s are dead.

- **Demo path is sacred**

    Only the happy path(s) you will show on stage matter.

- **Timebox everything**

    Every block must end in a runnable state with notes.

- **Recovery beats perfection**

    Every risky step must have a known reset or fallback.


---

## SECTION 0 — Define "Perfect Shape" (Monday · 30 min)

### Deliverable: `docs/testing/DEMO_PLAN.md`

This document is your *triage rubric*.

Include:

1. **Primary demo flow** (7 commands, exact order, expected outputs)
2. **Optional extensions** (only if time permits)
3. **Critical features** (memory, MCP, knowledge cache)
4. **Explicitly out-of-scope features** (even if implemented)
5. **Supported environment** (Mac local demo, Streamlit, MongoDB Atlas)

✅ This locks scope and prevents last-minute feature panic.

---

## SECTION 1 — Make Sure Everything Works (Monday · 2–3 hrs)

### 1.1 Freeze the state

- Create branch: `demo-stabilization`
- Tag main: `pre-demo-stabilization`
- Pull latest and **stop feature development**

### 1.2 Clean-machine reproducibility test (do before touching code)

```bash
# Remove local artifacts
rm -rf venv __pycache__ .pytest_cache

# Recreate environment
python scripts/setup.py

```

Then:

- Start app
- Run demo flow once end-to-end

Record results in `docs/testing/qa/demo_regression.md`:

| Step | Expected | Actual | Notes | Severity |
| --- | --- | --- | --- | --- |

---

## SECTION 2 — Bug Bash & Guardrails (Mon PM → Tues)

### 2.1 Triage rules

- **P0:** breaks demo, crashes, wrong memory behavior
- **P1:** flaky, slow, confusing UX
- **P2:** polish, edge cases, refactors

### 2.2 Fix loop (for every P0/P1)

1. Reproduce (minimal steps written down)
2. Add logging/assertions
3. Fix
4. Add **one guardrail**:
    - test, smoke step, or startup validation

### 2.3 Smoke test (high-leverage)

Create (or verify) a script such as:

```bash
make smoke
# or
python scripts/reset_demo.py --force && streamlit run streamlit_app.py

```

Smoke test must:

- verify env vars
- boot app
- confirm at least one memory + MCP action

---

## SECTION 3 — Command Test Matrix (MUST PASS)

### A. Infrastructure / Setup Commands

Run and verify **exactly**:

```bash
python scripts/setup.py
python scripts/reset_demo.py --force
streamlit run streamlit_app.py --server.port 8501

```

### Tests

```bash
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py -v
# Expect: 35 passed, 1 skipped

export TAVILY_API_KEY="tvly-xxxxx"
pytest tests/integration/test_mcp_agent.py -v -s
# Expect: 11 passed

```

---

### B. Live Demo Commands (7-Command Sequence)

Run **3 times** (cold, warm, post-reset).

1. `/tasks`

    → fast direct DB read (<200ms)

2. `"What was completed on Project Alpha?"`

    → episodic memory recall (known completions)

3. `"I'm focusing on Project Alpha"`

    → working memory write + confirmation

4. `"What should I work on next?"`

    → context-aware suggestion (Alpha-specific)

5. **Toggle Working Memory OFF**

    `"What should I work on next?"`

    → context lost (generic response)

6. **Toggle MCP Mode ON**

    `"Research gaming market and create GTM project with tasks"`

    → multi-step MCP workflow:

    - Tavily research
    - GTM project creation
    - task generation
    - summarization
7. `"What do you know about gaming?"`

    → **knowledge cache hit** (faster, cached sources)


---

### C. Support UI Actions (demo killers if untested)

- 🗑️ **Clear Session Memory**
- Toggle **Working Memory ON/OFF**
- Toggle **MCP Mode ON/OFF**
- Context-engineering / optimization toggles
- Voice input path (if enabled)

Each must:

- apply immediately
- not corrupt long-term memory
- fail gracefully if unavailable

---

## SECTION 4 — Performance & Latency Gates

| Operation | Target | Max |
| --- | --- | --- |
| Slash command | <200ms | 500ms |
| Optimized LLM | 6–12s | 15s |
| MCP multi-step | ~10s | 15s |
| Knowledge cache hit | <1s | 2s |

If slower:

- add narration
- show debug trace
- or skip optional steps

---

## SECTION 5 — Refactor & Cleanup (Tuesday only, time-boxed)

### Allowed

- Remove confirmed dead code
- Centralize config
- Normalize logging & error messages
- Hide risky features behind flags

### Not allowed

- Architecture rewrites
- Dependency upgrades (unless demo-blocking)
- Large diffs without smoke coverage

Optional safety net:

```
DEMO_MODE=true

```

---

## SECTION 6 — Documentation Pass (Tuesday PM)

Minimum set (fast but sufficient):

1. `README.md`
    - What this demo shows
    - Prereqs
    - Setup
    - Run
    - Demo flow
    - Troubleshooting
2. `.env.example`
3. `docs/testing/DEMO.md` (live steps + failure notes)
4. `docs/architecture/ARCHITECTURE.md` (1 page)

---

## SECTION 7 — Wednesday Final Hardening

### 7.1 One-command start

Aim for:

```bash
make setup
make run
make smoke

```

### 7.2 Pin everything

- lockfiles committed
- Python version explicit
- DB target verified

### 7.3 Fresh-clone rehearsal

- clone into new directory
- follow README **exactly**
- run full demo flow
- fix docs until frictionless

---

## SECTION 8 — Live Failure Playbook (DO NOT IMPROVISE)

### MCP fails or is slow

- Toggle MCP OFF
- Continue memory demo
- Narrate tool discovery conceptually

### Memory looks wrong

- 🗑️ Clear Session Memory
- Re-run steps 1–4
- If needed: `reset_demo.py --force`

### Internet dies

- Switch hotspot
- Skip MCP steps 6–7
- Frame MCP as optional enrichment

---

## SECTION 9 — Final Gates (must be YES)

- [ ]  Fresh clone worked this week
- [ ]  All 7 commands passed 3×
- [ ]  Reset + recovery rehearsed
- [ ]  Backup narration prepared
- [ ]  Repo tagged: `demo-ready`

---
---

# Part II: Tactical Execution

## Night Before Demo (January 14, 2026)

### Environment Setup

```
□ Clone/pull latest code from main branch
□ Install all dependencies: pip install -r requirements.txt
□ Verify .env file has all required keys:
  □ ANTHROPIC_API_KEY
  □ VOYAGE_API_KEY
  □ OPENAI_API_KEY
  □ MONGODB_URI
  □ MONGODB_DATABASE
  □ TAVILY_API_KEY (for MCP demos)
□ Verify setup (optional):
  python scripts/setup/verify_setup.py
□ Test MongoDB connection
□ Test Tavily MCP connection (toggle MCP Mode ON)
```

### Database Reset & Seeding

```
□ Run demo data seeding script:
  PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/python scripts/demo/seed_demo_data.py --clean

□ Verify output shows:
  ✓ Cleared collections (projects, tasks, memory_*)
  ✓ 8 projects inserted (4 active, 2 completed, 2 planned)
  ✓ 38 tasks inserted across all projects
  ✓ 7 procedural memories (including GTM Roadmap Template)
  ✓ 4 semantic memories (user preferences)
  ✓ 11 episodic memories (past actions)
  ✓ 46 episodic summaries generated
  ✓ 57 embeddings generated (1024-dim Voyage AI)
  ✨ Demo data ready for presentation!

□ Verify GTM Template structure:
  python -c "from shared.db import MongoDB; db = MongoDB().get_database(); \
  gtm = db.memory_procedural.find_one({'name': 'GTM Roadmap Template'}); \
  print(f'GTM Template: {gtm[\"name\"]} - {len(gtm[\"template\"][\"phases\"])} phases, \
  {sum(len(p[\"tasks\"]) for p in gtm[\"template\"][\"phases\"])} tasks')"
  Expected: GTM Template: GTM Roadmap Template - 3 phases, 12 tasks

□ If seeding fails:
  □ Check .env has VOYAGE_API_KEY for embeddings
  □ Check MONGODB_URI connection
  □ Re-run with --skip-embeddings if embedding service is down
```

### Demo Practice

```
□ Run through full 4-demo sequence 3 times:

  Demo 1: Speed Comparison (4-5 min)
  □ /tasks                                    # Tier 1: 50ms
  □ What's urgent?                            # Tier 2: 50ms (regex)
  □ Find tasks related to memory              # Tier 3: 2-5s (LLM)
  □ [Toggle MCP ON] Research AI agent frameworks  # Tier 4: 6-8s (Tavily)

  Demo 2: Memory Types (5-6 min)
  □ What templates do I have?                 # Procedural: List templates
  □ Show me my Blog Post Template            # Procedural: 4 phases, 16 tasks (most used)
  □ What do you know about LangChain?         # Semantic: Knowledge cache
  □ What do you know about MongoDB vector search?  # Semantic: Knowledge (audience-relevant)
  □ I'm focusing on Voice Agent Architecture  # Working: Store context
  □ What should I work on next?               # Working: Apply context
  □ [Clear session] What should I work on?    # Working: Context cleared (contrast)

  Demo 3: Evals Dashboard (3-4 min)
  □ Open http://localhost:8502
  □ Select: Baseline + All Ctx
  □ Click: Run Comparison
  □ Show all charts highlighting improvements

  Demo 4: The Finale (8-10 min)
  □ Research warehouse robotics frameworks    # Tavily + cache
  □ What do you know about warehouse robotics?  # Cache hit
  □ Create "OpenFleet AI Framework Launch" project using my GTM Roadmap Template,
    incorporate the research we just did, and create tasks for each phase
  □ /tasks project:"OpenFleet AI Framework Launch"  # Show 12 tasks
  □ Find projects similar to OpenFleet         # Semantic similarity

□ Total demo time: 20-25 minutes
□ Record backup video (in case of live issues)
```

### Backup Plan

```
□ Take screenshots of successful demo runs
□ Record full demo walkthrough video
□ Export demo slides to PDF (offline access)
□ Have demo script printed (docs/testing/09-demo-dry-run.md)
□ Test WiFi connection at demo venue (if applicable)
```

### Equipment

```
□ Laptop fully charged
□ Backup power cable
□ WiFi credentials tested
□ Presentation remote (if using)
□ HDMI/adapter for projector
□ Mouse (optional, for easier navigation)
```

---

## Morning of Demo (January 15, 2026)

### 2 Hours Before

```
□ Laptop charged to 100%
□ Close all unnecessary applications
□ Disable notifications (Do Not Disturb mode)
□ Clear browser cache
□ Test WiFi connection
```

### 30 Minutes Before

```
□ Start MongoDB Atlas (verify connection)
□ Start demo app: PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/streamlit run ui/demo_app.py --server.port 8501
□ Start evals app: PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/streamlit run evals_app.py --server.port 8502
□ Verify both apps load without errors:
  □ Demo app: http://localhost:8501
  □ Evals app: http://localhost:8502
□ Browser in presentation mode:
  □ Hide bookmarks bar
  □ Close developer tools
  □ Full screen (F11 or Cmd+Ctrl+F)
  □ Zoom to comfortable reading size
```

### 15 Minutes Before

```
□ Clear session memory: Click "🗑️ Clear Session Memory"
□ Verify all toggles:
  ☑ Compress Results: ON
  ☑ Streamlined Prompt: ON
  ☑ Prompt Caching: ON
  ☑ Enable Memory: ON
  ☑ Working Memory: ON
  ☑ Episodic Memory: ON
  ☑ Semantic Memory: ON
  ☑ Procedural Memory: ON
  ☑ Shared Memory: ON
  ☑ Context Injection: ON
  ☐ MCP Mode: OFF (will toggle during demo)
□ Verify Memory Stats shows:
  - Working Memory: 0 entries
  - Episodic Memory: X entries (from seed data - OK)
  - Semantic Memory: 0 entries
  - Procedural Memory: X entries (rules + template - OK)
  - Shared Memory: 0 entries
□ Debug panel visible at bottom
□ Have demo script open in another tab/window
```

### 5 Minutes Before

```
□ Take deep breath 😊
□ Test first command: /tasks (verify it works)
□ Close test response, ready for live demo
□ Slides open and ready (if separate presentation)
□ Water nearby
□ Phone on silent
```

---

## During Demo - Command Sequence

### 🎬 Demo 1: Speed Comparison - 4-Tier Routing (4-5 min)

**Narrative:** "Let me show you how we route queries through 4 performance tiers"

| # | Command | Tier | Expected Result | Duration |
|---|---------|------|----------------|----------|
| 1 | `/tasks` | Tier 1: Slash Command | Shows all 38 tasks | ~50ms |
| 2 | "What's urgent?" | Tier 2: Regex-Matched | Converts to `/tasks priority:high status:todo,in_progress` | ~50ms |
| 3 | "Find tasks related to memory" | Tier 3: LLM Agent | Semantic search via LLM + built-in tools | 2-5s |
| 4a | [Toggle MCP Mode ON] | - | MCP status shows "1 connected (Tavily)" | - |
| 4b | "Research AI agent frameworks" | Tier 4: MCP External | Tavily web search | 6-8s |

**Talking Points:**
- **Tier 1:** Direct MongoDB (instant, free)
- **Tier 2:** Pattern matching (instant, free) - no LLM needed
- **Tier 3:** LLM with built-in tools (6-12s with optimizations)
- **Tier 4:** External MCP tools (dynamic discovery, web search)
- Progressive enhancement: Faster tiers handle simple queries, LLM only when needed

**Alternative Queries (if time permits):**
- Tier 1: `/tasks project:"Voice Agent Architecture"`, `/tasks blocked`
- Tier 2: "What's in progress?", "Show me Mike's tasks"
- Tier 3: "What tasks are blocked and overdue?"

---

### 🎬 Demo 2: Memory Types - 5-Tier Architecture (5-6 min)

**Narrative:** "Our memory system has 5 specialized tiers working together"

| # | Command | Memory Type | Expected Result |
|---|---------|-------------|----------------|
| 1 | "What templates do I have?" | Procedural | Lists 4 templates (GTM, Ref Arch, Blog Post, Market Research) |
| 2 | "Show me my Blog Post Template" | Procedural | Shows 4 phases, 16 tasks (Outline→Draft→Review→Publish) - Most used (5×) |
| 3 | "What do you know about LangChain?" | Semantic: Knowledge | Returns cached knowledge: framework for LLM apps with chains, agents, memory |
| 4 | "What do you know about MongoDB vector search?" | Semantic: Knowledge | Returns cached knowledge: Atlas Vector Search, hybrid search, HNSW indexing |
| 5 | "I'm focusing on Voice Agent Architecture" | Working | Stores session context, Memory Stats +1 |
| 6 | "What should I work on next?" | Working | Suggests Voice Agent tasks (uses context) |
| 7a | [Click 🗑️ Clear Session Memory] | - | Working Memory cleared |
| 7b | "What should I work on next?" | - | Context lost - generic response |

**Talking Points:**
- **Procedural:** Templates, workflows, checklists (persistent) - Blog Post template most used
- **Semantic Knowledge:** 27 AI/MongoDB/CV topics cached with 7-day TTL and embeddings
- **Semantic Preferences:** User preferences with confidence scoring (persistent)
- **Working:** Session context (2-hour TTL)
- **Shared:** Agent handoffs (5-minute TTL)
- Knowledge cache demonstrates value before Demo 4 research
- Contrast demo: Clear session to show value of working memory

**Alternative Knowledge Queries (choose based on audience):**
- "What do you know about RAG?" (Retrieval-Augmented Generation)
- "Tell me about CLIP" (Computer Vision + NLP)
- "What do you know about prompt caching?" (Ties to Demo 3 optimization)
- "What do you know about AgentOps?" (Relevant to sample project)
- "Tell me about YOLO object detection" (Computer Vision)
- "What do you know about multimodal LLMs?" (Cutting edge)

---

### 🎬 Demo 3: Evals Dashboard - Context Optimization (3-4 min)

**Narrative:** "Context engineering achieved 50-70% latency reduction"

| # | Action | Expected |
|---|--------|----------|
| 1 | Open http://localhost:8502 | Evals dashboard loads |
| 2 | Select configs: ✅ Baseline, ✅ All Ctx | 2 configs selected |
| 3 | Click "🚀 Run Comparison" | Progress bar starts, ~2-3 min run time |
| 4 | [While running] Explain charts | Overview of what we'll see |
| 5 | Show "📈 Summary" section | 50-70% latency reduction, 70-90% token reduction |
| 6 | Show "⚡ Optimization Waterfall" | Visual cascade: gray→purple→blue→amber→green |
| 7 | Show "🔧 LLM vs Tool Time" | LLM is 96% of time, tools only 4% |
| 8 | Show "🪙 Token Savings" | 70-90% token reduction per query type |

**Talking Points:**
- Three optimizations: Compress results, Streamlined prompts, Prompt caching
- LLM is the bottleneck (96%), not MongoDB (4%)
- Token reduction = cost reduction (70%+ API savings)
- All optimizations are combinable
- MongoDB performance stays fast regardless (~500ms avg)

**Key Metrics to Highlight:**
- Baseline: 15-25s latency, ~3000 tokens
- All Optimizations: 6-12s latency, ~500-800 tokens
- Cost savings: ~70% reduction in API costs
- Quality maintained: Pass rate stays 100%

---

### 🎬 Demo 4: The Finale - Multi-Step Orchestration (8-10 min)

**Narrative:** "Let's build a GTM launch plan using research, memory, and templates"

| # | Command | Feature | Expected Result |
|---|---------|---------|----------------|
| 1 | "Research warehouse robotics frameworks" | MCP + Semantic Cache | Tavily search (~6-8s), results cached |
| 2 | "What do you know about warehouse robotics?" | Semantic Cache Hit | <1s response, "📚 Source: Knowledge Cache" |
| 3 | "Create 'OpenFleet AI Framework Launch' project using my GTM Roadmap Template, incorporate the research we just did, and create tasks for each phase" | Multi-Step Workflow | Step 1: Load template<br>Step 2: Create project (research-enriched)<br>Step 3: Generate 12 tasks across 3 phases |
| 4 | `/tasks project:"OpenFleet AI Framework Launch"` | Verification | Shows 12 tasks organized by phase |
| 5 | "Find projects similar to OpenFleet" | Semantic Search | Returns similar projects with similarity scores |

**Expected Output for Step 3:**
```
Step 1/3: Load GTM Roadmap Template
  → Found template: 3 phases, 12 tasks
  → ✓ Template loaded from Procedural Memory

Step 2/3: Create project with research context
  → Incorporating warehouse robotics research
  → ✓ Project created: OpenFleet AI Framework Launch

Step 3/3: Generate tasks from template phases
  → Phase 1: Research (4 tasks)
    - Market size and growth analysis
    - Competitor landscape mapping
    - Target customer persona development
    - Pricing model research
  → Phase 2: Strategy (4 tasks)
    - Value proposition refinement
    - Channel strategy definition
    - Partnership opportunity identification
    - Go-to-market timeline
  → Phase 3: Execution (4 tasks)
    - Marketing collateral development
    - Sales enablement materials
    - Launch event planning
    - Success metrics definition
  → ✓ 12 tasks created across 3 phases
```

**Talking Points:**
- **MCP Agent:** Dynamic Tavily integration for web research
- **Knowledge Cache:** 7-day TTL, 90% faster on reuse
- **Procedural Memory:** GTM template with structured phases
- **Multi-Step Orchestration:** Automatic workflow coordination
- **Semantic Enrichment:** Research context incorporated into project/tasks
- **Vector Search:** Find similar projects using embeddings

**Fallback Research Topics (if warehouse robotics fails):**
- "Research AI gaming NPCs and memory systems"
- "Research personalized learning AI tutors"
- "Research latest MongoDB vector search features"

---

### Wrap-Up & Key Takeaways (2-3 min)

**Key Achievements:**
1. **4-Tier Routing:** Progressive enhancement from instant to AI-powered
2. **5-Tier Memory:** Working, Episodic, Semantic, Procedural, Shared
3. **Context Engineering:** 50-70% latency reduction, 70% cost savings
4. **MCP Agent:** Dynamic tool discovery and orchestration
5. **Multi-Step Workflows:** Automatic complex task execution
6. **MongoDB Atlas:** Unified memory layer with vector search
7. **Production-Ready:** 47 tests, 90% coverage, evals framework

**Q&A Ready**

---

## Troubleshooting During Demo

| Issue | Quick Fix | Fallback |
|-------|-----------|----------|
| Query stuck/slow | "First query warming up" - wait | Refresh page, retry |
| Memory not updating | Check toggle is ON | Show backup screenshots |
| MCP Mode fails | Check Tavily API key in .env | Skip Demo 4, go to wrap-up |
| Evals dashboard won't load | Check port 8502 running | Skip Demo 3, explain conceptually |
| Evals run fails | Stop run, retry with fewer configs | Show pre-recorded results |
| GTM template not found | Reseed: `python scripts/demo/seed_demo_data.py --clean` | Use simpler project creation |
| Research returns no results | Try alternative topic (gaming NPCs, tutors) | Skip research, use template only |
| Cache hit doesn't show | Check debug panel for cache indicator | Explain based on latency difference |
| Project creation fails | Break into 2 steps: create project, then add tasks | Show existing project with tasks |
| Voice not working | "Voice works similarly to text" | Use text queries instead |
| Tool error | "Let me try that differently" | Use slash command alternative |
| Complete failure | Apologize, switch to backup video | Have video ready |

---

## Post-Demo

```
□ Thank audience
□ Share slides/resources
□ Note any issues encountered
□ Update documentation based on learnings
□ Celebrate! 🎉
```

---

## Emergency Contacts

```
Backup Support: [Name/Email]
MongoDB Contact: [Name/Email]
Venue Tech Support: [Phone]
```

---

*Demo Readiness Guide v3.0*
*MongoDB Developer Day - January 15, 2026*
*Good luck! You've got this! 💪*
