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
□ Run demo reset script (clears + seeds + verifies):
  python scripts/demo/reset_demo.py --force

□ Verify output shows:
  ✓ Cleared 6-7 collections
  ✓ Seeded data (3 projects, 15 tasks, memories)
  ✓ GTM Roadmap Template: EXISTS
  ✓ Project Alpha: EXISTS (4 tasks)
  🎬 Ready for demo!

□ Alternative: Just verify current state:
  python scripts/demo/reset_demo.py --verify-only

□ If verification fails:
  □ Re-run reset script
  □ Check .env configuration
  □ Verify MongoDB connection
```

### Demo Practice

```
□ Run through full demo 3 times (see 09-demo-dry-run.md)
□ Verify all 7 commands work consistently:
  1. /tasks
  2. "What was completed on Project Alpha?"
  3. "I'm focusing on Project Alpha"
  4. "What should I work on next?"
  5. [Toggle Working Memory OFF] → "What should I work on next?"
  6. [Toggle MCP Mode ON] → "Research gaming market and create GTM project with tasks"
  7. "What do you know about gaming?"
□ Time the demo: should complete in 20-25 minutes
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
□ Start app: streamlit run ui/streamlit_app.py --server.port 8501
□ Verify app loads without errors
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

### Part 1: Baseline (2 min)

| # | Command | Expected Result | Duration |
|---|---------|----------------|----------|
| 1 | `/tasks` | Shows all 15 tasks | <200ms |

**Talking Point:** "Direct MongoDB query - our baseline speed"

### Part 2: Memory Engineering (10 min)

| # | Command | Memory Type | Expected |
|---|---------|-------------|----------|
| 2 | "What was completed on Project Alpha?" | Episodic | Shows completed tasks from action history |
| 3 | "I'm focusing on Project Alpha" | Semantic | Stores preference, Memory Stats +1 |
| 4 | "What should I work on next?" | Working | Suggests Project Alpha tasks (uses context) |
| 5a | [Toggle Working Memory OFF] | - | Toggle shows unchecked |
| 5b | "What should I work on next?" | - | Context lost - shows ALL tasks or asks "which project?" |
| 5c | [Toggle Working Memory ON] | - | Toggle shows checked |

**Talking Points:**
- Episodic: Persistent action history
- Semantic: Learned preferences
- Working: Session context
- Toggle contrast: Clear before/after value demonstration

### Part 3: MCP Agent & Multi-Step (10 min) ⭐ NEW

| # | Command | Feature | Expected |
|---|---------|---------|----------|
| 6a | [Toggle MCP Mode ON] | MCP Agent | "MCP Servers: 1 connected (Tavily)" |
| 6b | "Research gaming market and create GTM project with tasks" | Multi-step workflow | 3-step execution (~10s) |
| 7 | "What do you know about gaming?" | Knowledge Cache | Cache hit (~0.5s), "📚 Source: Knowledge Cache" |

**Expected 6b Output:**
```
Step 1/3: Research gaming market trends
  → Routing to MCP Agent (Tavily)...
  → ✓ Research completed

Step 2/3: Create GTM project for gaming
  → Detected GTM project
  → Loading template: GTM Roadmap Template
  → ✓ Project created: Gaming Market

Step 3/3: Generate tasks from template
  → Phase: Research (4 tasks)
  → Phase: Strategy (4 tasks)
  → Phase: Execution (4 tasks)
  → ✓ Generated 12 tasks across 3 phases
```

**Talking Points:**
- Procedural Memory: GTM template auto-loaded
- MCP Agent: Dynamic Tavily integration
- Multi-step: Automatic orchestration
- Knowledge Cache: 7-day TTL, 90% faster on reuse

### Part 4: Wrap-up (3 min)

**Key Takeaways:**
1. 5-tier memory architecture (Working, Episodic, Semantic, Procedural, Shared)
2. Context engineering: 40-60% latency reduction
3. MCP Agent: Dynamic tool discovery (Milestone 6)
4. Multi-step workflows: Automatic orchestration
5. MongoDB Atlas: Unified memory layer with vector search
6. Production-ready: 47 tests, 90% coverage

**Q&A Ready**

---

## Troubleshooting During Demo

| Issue | Quick Fix | Fallback |
|-------|-----------|----------|
| Query stuck/slow | "First query warming up" - wait | Refresh page, retry |
| Memory not updating | Check toggle is ON | Show backup screenshots |
| MCP Mode fails | Check Tavily API key | Skip to next section |
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
