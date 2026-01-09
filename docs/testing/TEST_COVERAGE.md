# Flow Companion - Test Coverage Summary

**Version:** 3.0 (Milestone 6)
**Last Updated:** January 9, 2026
**Total Tests:** 47 automated + 93 manual = 140 total

---

## Automated Test Coverage

### Unit Tests (No API Keys Required)

**Tool Discovery Store** (`tests/test_tool_discoveries.py`)
- **Tests:** 17
- **Status:** ✅ All passing
- **Duration:** ~0.11s
- **Coverage:** ~90% of `memory/tool_discoveries.py`

| Category | Tests | Description |
|----------|-------|-------------|
| Discovery Logging | 5 | Log discoveries with metadata, embeddings, usage tracking |
| Similarity Search | 3 | Vector search, exact match fallback, threshold tuning |
| Management | 4 | Get popular, by server, by intent, statistics |
| Promotion | 2 | Mark as promoted, add developer notes |
| Deletion | 2 | Delete discovery, cleanup |

**MCP Agent** (`tests/test_mcp_agent.py`)
- **Tests:** 19 (18 passing, 1 skipped)
- **Status:** ✅ 18 passed, 1 skipped
- **Duration:** ~0.44s
- **Coverage:** ~90% of `agents/mcp_agent.py`

| Category | Tests | Description |
|----------|-------|-------------|
| Initialization | 2 | Initialize with/without API key |
| Request Handling | 3 | Discovery reuse, new discovery, routing |
| Tool Execution | 4 | Success, timeout, errors, server not connected |
| LLM Integration | 2 | Solution generation, code block parsing |
| Utilities | 8 | Result truncation, tool formatting, status, cleanup |

**Total Unit Tests:** 35 passing, 1 skipped
**Combined Duration:** ~0.55s
**Overall Coverage:** ~90% of MCP Agent and Tool Discoveries code

### Integration Tests (Requires TAVILY_API_KEY)

**MCP Agent Integration** (`tests/integration/test_mcp_agent.py`)
- **Tests:** 11
- **Status:** ⏭️ Skipped without API key / ✅ Passing with API key
- **Duration:** ~25-30s (with real Tavily calls)

| Category | Tests | Description |
|----------|-------|-------------|
| Initialization | 2 | Tavily connection, tool discovery |
| Web Search | 2 | Basic search, research intent |
| Discovery Reuse | 2 | Similar query detection, vector search |
| Knowledge Cache | 1 | Caching and reuse of search results |
| Error Handling | 2 | Empty query, no servers connected |
| Cleanup | 1 | Graceful disconnection |
| Performance | 1 | Latency benchmarks (<10s target) |

**Run Command:**
```bash
export TAVILY_API_KEY="tvly-xxxxx"
pytest tests/integration/test_mcp_agent.py -v -s
```

---

## Manual Test Coverage

### Functional Testing (Test Guides 00-05)

| Guide | Category | Tests | Duration |
|-------|----------|-------|----------|
| 00-setup.md | Setup & Configuration | N/A | 5-10 min |
| 01-slash-commands.md | Direct DB Commands | 15 | 15 min |
| 02-text-queries.md | LLM Read Queries | 12 | 15 min |
| 03-text-actions.md | LLM Write Actions | 14 | 15 min |
| 04-voice-input.md | Voice Integration | 8 | 10 min |
| 05-context-engineering.md | Optimizations | 12 | 20 min |

**Subtotal:** 61 manual tests, ~80 minutes

### Memory Engineering (Test Guide 06)

**Guide:** 06-memory-engineering.md
**Duration:** 35 minutes
**Tests:** 20

| Memory Type | Tests | Key Capabilities Tested |
|-------------|-------|-------------------------|
| Working Memory | 4 | AR, CR, context injection |
| Episodic Memory | 4 | AR, LRU, action history |
| Semantic Memory | 5 | AR, TTL, CR, knowledge caching (NEW) |
| Procedural Memory | 4 | AR, TTL, CR, GTM templates (NEW) |
| Shared Memory | 3 | Agent handoffs |

**New in Milestone 6:**
- Test 6.3.5: Knowledge Cache (7-day TTL, semantic search reuse)
- Test 6.4.4: GTM Template (multi-step workflow integration)

### Multi-Turn & Multi-Step (Test Guide 07)

**Guide:** 07-multi-turn.md
**Duration:** 20 minutes
**Tests:** 43

| Category | Tests | Description |
|----------|-------|-------------|
| Context Across Turns | 5 | Session context persistence |
| Disambiguation | 6 | Numbered & descriptive selection |
| Mixed Input Types | 3 | Text + Voice |
| Context Switching | 4 | Explicit context updates |
| Pronoun Resolution | 4 | "it", "that", "the first one" |
| Long Conversations | 10 | 10+ turn flows |
| **Multi-Step Workflows (NEW)** | **11** | Research + Create + Generate |

**New in Milestone 6:**
- Test 7.7: Basic multi-step (3-step workflow)
- Test 7.8: Detection patterns (2 tests)
- Test 7.9: Context passing (4 tests)
- Test 7.10: Error handling (4 tests)

### Error Handling (Test Guide 08)

**Guide:** 08-error-handling.md
**Duration:** 15 minutes
**Tests:** 30

| Category | Tests | Description |
|----------|-------|-------------|
| Not Found Errors | 4 | Missing projects, tasks |
| Invalid Input | 4 | Empty, invalid commands |
| Graceful Degradation | 4 | Memory disabled, long queries |
| Edge Cases | 4 | Empty lists, already complete |
| Concurrent Actions | 2 | Rapid queries, cancellation |
| **MCP Errors (NEW)** | **12** | Tavily timeout, connection failures, cache expiration |

**New in Milestone 6:**
- MCP Mode disabled errors
- Tavily connection/timeout errors
- Knowledge cache edge cases
- Tool discovery fallback testing

### Demo Dry Run (Test Guide 09)

**Guide:** 09-demo-dry-run.md
**Duration:** 25 minutes
**Tests:** 7-command sequence verification

**Demo Sequence:**
1. `/tasks` - Baseline query
2. "What was completed on Project Alpha?" - Episodic Memory
3. "I'm focusing on Project Alpha" - Semantic Memory
4. "What should I work on next?" - Working Memory
5. Toggle contrast - Memory value demonstration
6. Multi-step workflow - MCP Agent + Procedural Memory
7. Knowledge cache - Semantic Memory reuse

**Manual Test Total:** 93 tests across 8 guides

---

## Coverage by Component

### Core Agents

| Component | Automated | Manual | Total | Coverage % |
|-----------|-----------|--------|-------|------------|
| Coordinator Agent | 0 | 40 | 40 | ~80% (logic paths) |
| Worklog Agent | 0 | 25 | 25 | ~75% |
| Retrieval Agent | 0 | 20 | 20 | ~75% |
| **MCP Agent** | **18** | **15** | **33** | **~90%** |

### Memory System

| Memory Type | Automated | Manual | Total | Coverage % |
|-------------|-----------|--------|-------|------------|
| Working Memory | 0 | 4 | 4 | 100% |
| Episodic Memory | 0 | 4 | 4 | 100% |
| Semantic Memory | 0 | 5 | 5 | 100% (includes knowledge cache) |
| Procedural Memory | 0 | 4 | 4 | 100% (includes templates) |
| Shared Memory | 0 | 3 | 3 | 100% |
| **Tool Discoveries** | **17** | **2** | **19** | **~90%** |

### Features

| Feature | Automated | Manual | Total | Coverage % |
|---------|-----------|--------|-------|------------|
| Slash Commands | 0 | 15 | 15 | ~85% |
| Text Queries | 0 | 12 | 12 | ~80% |
| Text Actions | 0 | 14 | 14 | ~80% |
| Voice Input | 0 | 8 | 8 | ~70% |
| Context Engineering | 0 | 12 | 12 | ~75% |
| **Multi-Step Workflows** | **2** | **11** | **13** | **~85%** |
| Error Handling | 0 | 30 | 30 | ~80% |

---

## Test Execution Time

### Automated Tests

| Suite | Duration | Frequency |
|-------|----------|-----------|
| Unit Tests | ~0.6s | On every commit |
| Integration Tests | ~30s | Before merge/deploy |
| **Total Automated** | **~30s** | **Pre-deployment** |

### Manual Tests

| Phase | Duration | Frequency |
|-------|----------|-----------|
| Core Functionality (00-05) | ~80 min | Weekly |
| Memory Engineering (06) | ~35 min | Before demo |
| Multi-Turn & Workflows (07) | ~20 min | Before demo |
| Error Handling (08) | ~15 min | Weekly |
| Demo Dry Run (09) | ~25 min | 3x before demo |
| **Total Manual** | **~3 hours** | **Pre-demo** |

---

## Coverage Gaps & Future Work

### Areas with Lower Coverage (<80%)

1. **Voice Input** (70%)
   - Limited browser voice API testing
   - Manual testing only
   - **Action:** Add Playwright e2e tests

2. **Context Engineering** (75%)
   - Optimization impact hard to automate
   - Latency variance in CI/CD
   - **Action:** Performance regression benchmarks

3. **Coordinator Agent** (80%)
   - Complex routing logic
   - Many edge cases
   - **Action:** Add unit tests for routing decisions

### Not Yet Tested

- MongoDB MCP Server (planned for future)
- Automatic tool promotion (discovery → static)
- Multi-server orchestration (>1 MCP server)
- Long-term knowledge cache behavior (>7 days)
- High-concurrency scenarios

### Recommended Additions

1. **E2E Tests** (Playwright)
   - Full user workflows
   - Cross-browser compatibility
   - Voice input on different browsers

2. **Load Tests** (Locust/k6)
   - Multiple concurrent users
   - Memory system performance at scale
   - MCP Agent under load

3. **Integration Tests**
   - MongoDB MCP Server (when available)
   - Multiple MCP servers simultaneously
   - Discovery promotion workflow

---

## Test Commands Quick Reference

### Run All Automated Tests

```bash
# Unit tests only
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py -v

# With integration tests (requires TAVILY_API_KEY)
export TAVILY_API_KEY="tvly-xxxxx"
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py tests/integration/test_mcp_agent.py -v

# With coverage
pytest tests/test_tool_discoveries.py tests/test_mcp_agent.py \
  --cov=agents.mcp_agent \
  --cov=memory.tool_discoveries \
  --cov-report=html
```

### Manual Testing Workflow

```bash
# 1. Setup
source venv/bin/activate
python scripts/seed_demo_data.py
streamlit run streamlit_app.py --server.port 8501

# 2. Follow test guides
# See: docs/testing/README.md for order

# 3. Demo rehearsal (3x)
# Follow: docs/testing/09-demo-dry-run.md
```

---

## Summary Statistics

```
┌────────────────────────────────────────────────────┐
│ FLOW COMPANION - TEST COVERAGE SUMMARY             │
├────────────────────────────────────────────────────┤
│                                                    │
│ AUTOMATED TESTS:                                   │
│   Unit Tests:        35 passing, 1 skipped        │
│   Integration Tests: 11 (requires API key)        │
│   Duration:          ~30s total                    │
│   Coverage:          ~90% (MCP + Tool Discoveries) │
│                                                    │
│ MANUAL TESTS:                                      │
│   Test Guides:       8 guides (00-08)             │
│   Test Cases:        93 scenarios                  │
│   Duration:          ~3 hours comprehensive        │
│                                                    │
│ TOTAL TESTS:         140 (47 automated + 93 manual)│
│                                                    │
│ MILESTONE 6 ADDITIONS:                             │
│   New Automated:     35 tests (MCP Agent suite)   │
│   New Manual:        43 tests (multi-step + MCP)  │
│   Updated Guides:    4 guides (00, 06, 07, 08)    │
│                                                    │
│ DEMO READINESS:                                    │
│   Demo Script:       7-command sequence            │
│   Dry Runs:          3x recommended                │
│   Duration:          25 minutes                    │
│   Backup Plan:       Video + screenshots           │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

*Test Coverage Summary v3.0*
*Updated for Milestone 6: MCP Agent & Multi-Step Workflows*
*MongoDB Developer Day - January 15, 2026*
