# Flow Companion - Testing Guides

**Version:** 2.0  
**Demo Date:** January 15, 2026  
**Last Updated:** January 8, 2026

---

## Testing Guide Index

| Guide | Description | Time | Priority |
|-------|-------------|------|----------|
| [00-setup.md](00-setup.md) | Pre-test setup, services, reset state | 5 min | Required |
| [01-slash-commands.md](01-slash-commands.md) | Direct DB commands (fast path) | 15 min | P0 |
| [02-text-queries.md](02-text-queries.md) | LLM-routed read queries | 15 min | P0 |
| [03-text-actions.md](03-text-actions.md) | LLM-routed write actions | 15 min | P0 |
| [04-voice-input.md](04-voice-input.md) | Voice-to-text integration | 10 min | P1 |
| [05-context-engineering.md](05-context-engineering.md) | Optimization toggles | 20 min | P1 |
| [06-memory-engineering.md](06-memory-engineering.md) | 5 memory types + 4 capabilities | 30 min | P0 |
| [07-multi-turn.md](07-multi-turn.md) | Conversation flows | 15 min | P1 |
| [08-error-handling.md](08-error-handling.md) | Edge cases & graceful degradation | 10 min | P2 |
| [09-demo-dry-run.md](09-demo-dry-run.md) | Full demo rehearsal | 20 min | P0 |

**Total Time:** ~2.5 hours for full testing suite

---

## Quick Reference

### Test Order for Demo Readiness

```
Day 1: Core Functionality
├── 00-setup.md (5 min)
├── 01-slash-commands.md (15 min)
├── 02-text-queries.md (15 min)
└── 03-text-actions.md (15 min)

Day 2: Memory & Polish
├── 06-memory-engineering.md (30 min)
├── 07-multi-turn.md (15 min)
└── 09-demo-dry-run.md (20 min)

Day 3: Nice-to-haves
├── 04-voice-input.md (10 min)
├── 05-context-engineering.md (20 min)
└── 08-error-handling.md (10 min)
```

---

## Memory Framework Quick Reference

### 5 Memory Types

| Type | Collection | TTL | Purpose |
|------|------------|-----|---------|
| **Working Memory** | short_term | 2hr | Current task/project context |
| **Episodic Memory** | long_term | ∞ | Action history (what happened) |
| **Semantic Memory** | long_term | ∞ | Preferences (what I know) |
| **Procedural Memory** | long_term | ∞ | Rules (how to act) |
| **Shared Memory** | shared | 5min | Agent handoffs |

### 4 Capabilities (AR, TTL, LRU, CR)

| Capability | Abbreviation | What It Tests |
|------------|--------------|---------------|
| Accurate Retrieval | AR | Find specific info from memory |
| Test-Time Learning | TTL | Learn new rules during conversation |
| Long-Range Understanding | LRU | Summarize across many turns |
| Conflict Resolution | CR | Handle contradictory/updated info |

---

## Expected Latencies

| Operation | Target | Max Acceptable |
|-----------|--------|----------------|
| Slash commands | <200ms | <500ms |
| LLM queries (optimized) | 6-12s | 15s |
| LLM queries (baseline) | 15-25s | 30s |
| Memory read | <30ms | <100ms |
| Memory write | <50ms | <100ms |

---

## Bug Tracking Template

When you find issues, record them:

```markdown
### Bug: [Short Description]
- **Guide:** 0X-filename.md
- **Test ID:** X.X
- **Steps:** 
- **Expected:**
- **Actual:**
- **Severity:** P0/P1/P2
```

---

*Flow Companion v3.0 - Modular Testing Guides*
