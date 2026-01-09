# Flow Companion - Testing Documentation

**Version:** 3.0 (Milestone 6)
**Demo Date:** January 15, 2026
**Last Updated:** January 9, 2026

---

## Overview

This directory contains comprehensive testing guides for Flow Companion, covering setup, functional testing, memory engineering, and demo preparation.

**Key Stats:**
- **47 total tests** (35 unit, 11 integration, 1 skipped)
- **~90% code coverage** (MCP Agent + Tool Discoveries)
- **5-tier memory architecture** (Working, Episodic, Semantic, Procedural, Shared)
- **Milestone 6 features**: MCP Agent, multi-step workflows, knowledge caching

---

## Testing Guide Index

| Guide | Description | Time | Priority | Updated |
|-------|-------------|------|----------|---------|
| [00-setup.md](00-setup.md) | Environment setup, .env config, seed data | 5-10 min | Required | v3.0 |
| [01-slash-commands.md](01-slash-commands.md) | Direct DB commands (fast path) | 15 min | P0 | v2.0 |
| [02-text-queries.md](02-text-queries.md) | LLM-routed read queries | 15 min | P0 | v2.0 |
| [03-text-actions.md](03-text-actions.md) | LLM-routed write actions | 15 min | P0 | v2.0 |
| [04-voice-input.md](04-voice-input.md) | Voice-to-text integration | 10 min | P1 | v2.0 |
| [05-context-engineering.md](05-context-engineering.md) | Optimization toggles | 20 min | P1 | v2.0 |
| [06-memory-engineering.md](06-memory-engineering.md) | 5 memory types + knowledge cache + GTM templates | 35 min | P0 | v3.0 |
| [07-multi-turn.md](07-multi-turn.md) | Multi-turn conversations + multi-step workflows | 20 min | P1 | v3.0 |
| [08-error-handling.md](08-error-handling.md) | Edge cases + MCP error scenarios | 15 min | P2 | v3.0 |
| [09-demo-dry-run.md](09-demo-dry-run.md) | Full demo rehearsal (7-command sequence) | 25 min | P0 | v3.0 |

**Total Time:** ~3 hours for full testing suite

---

## Quick Start

### For Demo Preparation (Night Before)

```bash
# 1. Environment setup
source venv/bin/activate
python scripts/seed_demo_data.py  # Seed database with demo data

# 2. Verify .env configuration
TAVILY_API_KEY=tvly-xxxxx  # Required for MCP demos
ANTHROPIC_API_KEY=sk-ant-xxxxx
VOYAGE_API_KEY=pa-xxxxx
MONGODB_URI=mongodb+srv://...

# 3. Start app
streamlit run streamlit_app.py --server.port 8501

# 4. Run through full demo 3 times
# Follow: docs/testing/09-demo-dry-run.md
```

### For Comprehensive Testing

Follow guides in this order:

```
Day 1: Core Functionality (Setup + Basic Features)
├── 00-setup.md           → Environment & seed data (10 min)
├── 01-slash-commands.md  → Direct DB path (15 min)
├── 02-text-queries.md    → LLM queries (15 min)
└── 03-text-actions.md    → LLM actions (15 min)

Day 2: Memory Architecture (Core Demo Value)
├── 06-memory-engineering.md  → 5 memory types (35 min)
├── 07-multi-turn.md          → Multi-step workflows (20 min)
└── 09-demo-dry-run.md        → Full rehearsal (25 min)

Day 3: Polish & Edge Cases
├── 04-voice-input.md           → Voice integration (10 min)
├── 05-context-engineering.md   → Optimizations (20 min)
└── 08-error-handling.md        → MCP errors (15 min)
```

---

## Running Tests

### Unit Tests (No API Keys Required)

```bash
# All unit tests
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py -v

# Expected: 35 passed, 1 skipped
# Time: ~0.6s
```

### Integration Tests (Requires TAVILY_API_KEY)

```bash
# Set API key
export TAVILY_API_KEY="tvly-xxxxx"

# Run integration tests
pytest tests/integration/test_mcp_agent.py -v -s

# Expected: 11 passed
# Time: ~25-30s
```

### Coverage Report

```bash
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py \
  --cov=agents.mcp_agent \
  --cov=memory.tool_discoveries \
  --cov-report=html

open htmlcov/index.html
```

See: [tests/README_MCP_TESTS.md](../../tests/README_MCP_TESTS.md) for complete testing guide.

---

## Memory Framework Quick Reference

### 5 Memory Types (Milestone 5 & 6)

| Type | Collection | TTL | Purpose | Milestone 6 Updates |
|------|------------|-----|---------|---------------------|
| **Working Memory** | short_term | 2hr | Current task/project context | - |
| **Episodic Memory** | long_term | ∞ | Action history (what happened) | - |
| **Semantic Memory** | long_term | 7d* | Preferences + **Knowledge cache** | **Knowledge cache added** |
| **Procedural Memory** | long_term | ∞ | Rules + **Templates** | **GTM templates added** |
| **Shared Memory** | shared | 5min | Agent handoffs | - |

*New: Knowledge cache in semantic memory with 7-day TTL

### 4 Capabilities (AR, TTL, LRU, CR)

| Capability | Abbreviation | What It Tests | Difficulty |
|------------|--------------|---------------|------------|
| **Accurate Retrieval** | AR | Find specific info from memory | Medium |
| **Test-Time Learning** | TTL | Learn new rules during conversation | Medium |
| **Long-Range Understanding** | LRU | Summarize across many turns | Hard |
| **Conflict Resolution** | CR | Handle contradictory/updated info | Very Hard |

---

## Expected Latencies

| Operation | Target | Max Acceptable | Notes |
|-----------|--------|----------------|-------|
| Slash commands | <200ms | <500ms | Direct MongoDB queries |
| LLM queries (optimized) | 6-12s | 15s | With context engineering |
| LLM queries (baseline) | 15-25s | 30s | Without optimizations |
| MCP + Multi-step (3 steps) | ~10s | 15s | Tavily + create + generate |
| Knowledge cache hit | <1s | 2s | 90% faster than fresh search |
| Memory read | <30ms | <100ms | MongoDB query |
| Memory write | <50ms | <100ms | MongoDB insert/update |

---

## New in Milestone 6 (MCP Agent)

### Features Added

1. **MCP Agent** - Dynamic tool discovery with Tavily integration
2. **Multi-Step Workflows** - Automatic detection and orchestration
3. **Knowledge Cache** - 7-day TTL semantic cache for search results
4. **Tool Discoveries** - Learning system for MCP tool usage
5. **GTM Templates** - Procedural memory templates for complex workflows

### Testing Updates

- **20 new tests** in 06-memory-engineering.md (knowledge cache + GTM templates)
- **11 new tests** in 07-multi-turn.md (multi-step workflows)
- **12 new tests** in 08-error-handling.md (MCP error scenarios)
- **Updated demo script** in 09-demo-dry-run.md (7-command sequence)

### Key Demo Commands

```bash
# 1. Baseline
/tasks

# 2-4. Memory demonstration
"What was completed on Project Alpha?"
"I'm focusing on Project Alpha"
"What should I work on next?"

# 5. Memory toggle contrast
[Toggle Working Memory OFF]
"What should I work on next?"  # Context lost

# 6-7. MCP Agent + Multi-Step (NEW)
[Toggle MCP Mode ON]
"Research gaming market and create GTM project with tasks"
"What do you know about gaming?"  # Knowledge cache hit
```

---

## Documentation Structure

```
docs/testing/
├── README.md                    ← You are here (index + quick reference)
├── DEMO_CHECKLIST.md           ← Pre-demo + day-of checklists
├── TEST_COVERAGE.md            ← Coverage stats, what's tested
│
├── 00-setup.md                 ← Environment setup
├── 01-slash-commands.md        ← Direct DB commands
├── 02-text-queries.md          ← LLM queries
├── 03-text-actions.md          ← LLM actions
├── 04-voice-input.md           ← Voice integration
├── 05-context-engineering.md   ← Optimizations
├── 06-memory-engineering.md    ← 5 memory types (CORE)
├── 07-multi-turn.md            ← Multi-step workflows
├── 08-error-handling.md        ← Error scenarios
└── 09-demo-dry-run.md          ← Full demo rehearsal
```

---

## Related Documentation

### Architecture
- [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System architecture
- [docs/architecture/AGENT_ARCHITECTURE_AND_OPTIMIZATIONS.md](../architecture/AGENT_ARCHITECTURE_AND_OPTIMIZATIONS.md) - Agent system details
- [docs/architecture/MCP_ARCHITECTURE.md](../architecture/MCP_ARCHITECTURE.md) - MCP Agent architecture

### Features
- [docs/features/MEMORY.md](../features/MEMORY.md) - 5-tier memory system
- [docs/features/MCP_AGENT.md](../features/MCP_AGENT.md) - MCP Agent documentation
- [docs/features/MULTI_STEP_INTENTS.md](../features/MULTI_STEP_INTENTS.md) - Multi-step workflows

### Testing
- [tests/README_MCP_TESTS.md](../../tests/README_MCP_TESTS.md) - MCP test quick reference
- [docs/testing/MCP_AGENT_TEST_SUMMARY.md](MCP_AGENT_TEST_SUMMARY.md) - Detailed test coverage

---

## Bug Tracking Template

When you find issues during testing, record them:

```markdown
### Bug: [Short Description]
- **Guide:** 0X-filename.md
- **Test ID:** X.X
- **Steps to Reproduce:**
  1.
  2.
  3.
- **Expected:**
- **Actual:**
- **Severity:** P0/P1/P2
- **Environment:** Dev/Staging/Demo
```

---

## Quick Reference Commands

### Demo Day (Print This)

```bash
# Start app
streamlit run streamlit_app.py --server.port 8501

# Verify setup
✓ All toggles ON (except MCP Mode - toggle during demo)
✓ Memory cleared (🗑️ Clear Session Memory)
✓ Debug panel visible
✓ Tavily API key configured

# Demo sequence (7 commands - see 09-demo-dry-run.md)
1. /tasks
2. "What was completed on Project Alpha?"
3. "I'm focusing on Project Alpha"
4. "What should I work on next?"
5. [Toggle Working Memory OFF] → "What should I work on next?"
6. [Toggle MCP Mode ON] → "Research gaming market and create GTM project with tasks"
7. "What do you know about gaming?"
```

---

*Flow Companion Testing Documentation v3.0*
*Updated for Milestone 6: MCP Agent & Multi-Step Workflows*
*MongoDB Developer Day - January 15, 2026*
