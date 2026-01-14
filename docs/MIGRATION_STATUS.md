# Memory Collection Migration Status

**Date**: January 13, 2026
**Branch**: demo-stabilization

## Overview

Migrating from 3 old MongoDB collections to 2 persistent + in-memory storage:

**OLD** (being removed):
- `memory_long_term` → Split to `memory_episodic` + `memory_semantic`
- `memory_short_term` → In-memory dicts
- `memory_shared` → In-memory dicts

**NEW** (current):
- `memory_episodic` - Persistent actions/events
- `memory_semantic` - Persistent knowledge cache + preferences
- `memory_procedural` - Persistent templates/workflows (unchanged)
- In-memory dicts - Session context, agent working memory, handoffs, disambiguation

---

## ✅ Completed

### Core Memory System
- [x] **memory/manager.py** - Full migration complete
  - Action methods → `self.episodic`
  - Preference methods → `self.semantic`
  - Knowledge cache methods → `self.semantic`
  - Session context → `self._session_contexts` dict
  - Agent working memory → `self._agent_working` dict
  - Disambiguation → `self._disambiguations` dict
  - Handoff methods → `self._handoffs` dict
  - Stats methods → Updated to count from in-memory + new collections
  - clear_session() → Clears all in-memory dicts
  - Commits: 47932f3, 3012e41

### UI Files
- [x] **ui/demo_app.py** - Updated stats field names
  - `memory_shared` → `handoffs_pending`
- [x] **ui/streamlit_app.py** - Updated stats display
  - Label changed to "Handoffs Pending"
  - Commit: 47f60d3

### Documentation
- [x] **docs/DEMO_READINESS_SUMMARY.md** - Updated for new implementations
- [x] **scripts/migrate_memory_collections.py** - Migration guide created
- [x] **docs/MIGRATION_STATUS.md** - This file

---

## ⏳ Remaining Work

### Setup Scripts (HIGH PRIORITY)
These scripts create collections and indexes for new databases:

- [ ] **scripts/setup/init_db.py** (301 lines, ~25 references)
  - Remove `memory_short_term` collection creation (lines 163-182)
  - Remove `memory_long_term` collection creation (lines 187-220)
  - Remove `memory_shared` collection creation (lines 223-244)
  - Add `memory_episodic` collection creation (copy from manager.py)
  - Add `memory_semantic` collection creation (copy from manager.py)
  - Update vector index instructions (line 301, 373, 381)
  - Update stats reporting (lines 520-624)

- [ ] **scripts/setup/utils.py** (lines 421-423)
  - Update `MEMORY_COLLECTIONS` list to `["memory_episodic", "memory_semantic", "memory_procedural"]`

- [ ] **scripts/setup/verify_setup.py** (lines 64-66, 228)
  - Update expected collections list
  - Update vector index checks

- [ ] **scripts/setup/setup.py** (line 221)
  - Update embedding count query from `memory_long_term` to `memory_episodic` + `memory_semantic`

### Demo Scripts
- [ ] **scripts/demo/seed_demo_data.py** - Check if it seeds old collections
- [ ] **scripts/demo/reset_demo.py** - Update collection references

### Files to Delete
- [ ] **memory/setup.py** - No longer needed (only used by deprecated scripts)
- [ ] **scripts/deprecated/seed_memory_demo_data.py** - Already deprecated
- [ ] **scripts/deprecated/load_sample_data.py** - Already deprecated
- [ ] **scripts/deprecated/setup_database.py** - Already deprecated

### Test Files (10+ files)
All files in `tests/integration/memory/` need updating:
- [ ] test_rules_flow.py
- [ ] test_preferences_flow.py
- [ ] test_disambiguation_flow.py
- [ ] test_semantic_procedural_memory_simple.py
- [ ] test_ui_memory.py
- [ ] test_action_recording.py
- [ ] test_narrative_generation.py
- [ ] test_semantic_procedural_memory.py
- [ ] test_semantic_search_history.py
- [ ] tests/unit/test_memory_types.py

**Test Updates Needed:**
- Update collection names in assertions
- Update expected field names in stats
- Tests may fail until database collections are manually dropped

### Manual Database Cleanup (CRITICAL)
- [ ] Drop old collections from Atlas:
  ```javascript
  use mdb_flow;
  db.memory_short_term.drop();
  db.memory_long_term.drop();
  db.memory_shared.drop();
  ```
- [ ] Run updated setup scripts to create new collections
- [ ] Verify vector indexes on `memory_episodic` and `memory_semantic`

---

## Testing Plan

### Phase 1: Code Validation
1. Update all setup scripts
2. Update all test files
3. Run unit tests (may need mock adjustments)
4. Fix any import/reference errors

### Phase 2: Database Migration
1. **BACKUP DATABASE FIRST**
2. Drop old collections manually in Atlas
3. Run `scripts/setup/init_db.py` to create new collections
4. Verify indexes with `scripts/setup/verify_setup.py`
5. Seed demo data with `scripts/demo/seed_demo_data.py`

### Phase 3: Integration Testing
1. Run all integration tests
2. Test UI (both demo_app.py and streamlit_app.py)
3. Test coordinator with memory enabled
4. Verify all memory types function correctly

---

## Known Impacts

### What Still Works
- ✅ All memory API methods (manager.py migrated)
- ✅ UI displays (stats field names updated)
- ✅ Coordinator optimization flags (unchanged, just feature toggles)

### What Won't Work Until Completed
- ❌ Fresh database setup (old collection names in scripts)
- ❌ Tests (expecting old collection names)
- ❌ Demo data seeding (may reference old collections)

### Breaking Changes
- Database schema change (3 collections → 2 + in-memory)
- Stats API field names changed:
  - `short_term_count` → `working_memory_count`
  - `shared_pending` → `handoff_pending`
  - `by_type.memory_shared` → `by_type.handoffs_pending`

---

## Next Steps (Priority Order)

1. **Update setup scripts** (init_db.py, utils.py, verify_setup.py, setup.py)
2. **Delete obsolete files** (memory/setup.py, scripts/deprecated/*)
3. **Update test files** (all integration/memory/* and unit tests)
4. **Test with clean database** (drop old, create new, seed, verify)
5. **Run full test suite**
6. **Update demo scripts if needed**

---

## Rollback Plan

If issues arise:
1. Revert commits: `git revert 47f60d3 3012e41 47932f3`
2. Old collections still exist in database (not dropped yet)
3. Code will work with old collection names again

---

## Progress Summary

**Files Modified**: 5
**Files Remaining**: 20+
**Completion**: ~20%

**Core migration complete**, remaining work is mostly:
- Setup/initialization scripts
- Test updates
- Manual database cleanup
