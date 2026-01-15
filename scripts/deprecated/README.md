# Deprecated Scripts

This directory contains scripts that have been superseded by newer implementations.

**⚠️ DO NOT USE THESE SCRIPTS FOR NEW WORK**

These files are preserved temporarily for reference but will be removed in a future cleanup.

---

## Deprecated Scripts

### setup_database.py
**Deprecated:** January 12, 2026
**Replaced by:** `scripts/setup/init_db.py`

**Reason for deprecation:**
- Only creates indexes, doesn't create collections
- `init_db.py` provides comprehensive database initialization (collections + indexes)
- Functionality is fully covered by the replacement
- Adds unnecessary complexity with multiple CLI flags

**Migration path:**
```bash
# Old (deprecated)
python scripts/setup_database.py --memory

# New (recommended)
python scripts/setup/init_db.py
```

---

### load_sample_data.py
**Deprecated:** January 12, 2026
**Replaced by:** `scripts/demo/seed_demo_data.py`

**Reason for deprecation:**
- Creates 10 generic projects not suitable for demos
- No memory system data (procedural, semantic, episodic)
- `seed_demo_data.py` provides curated demo data with full memory system
- Demo-focused data is more useful for testing and presentations

**Migration path:**
```bash
# Old (deprecated)
python scripts/load_sample_data.py

# New (recommended)
python scripts/demo/seed_demo_data.py
```

**Key differences:**
| Feature | load_sample_data.py | seed_demo_data.py |
|---------|---------------------|-------------------|
| Projects | 10 generic | 3 realistic demo projects |
| Tasks | 44 mixed | 7 focused on Project Alpha |
| Memory | None | Full 5-tier memory system |
| Purpose | Generic testing | Demo presentations |
| Embeddings | Optional | Integrated |

---

### seed_memory_demo_data.py
**Deprecated:** January 12, 2026
**Replaced by:** `scripts/demo/seed_demo_data.py`

**Reason for deprecation:**
- Redundant with `seed_demo_data.py` memory seeding functions
- `seed_demo_data.py` already has comprehensive memory seeding:
  - `seed_procedural_memory()`
  - `seed_semantic_memory()`
  - `seed_episodic_memory()`
- Maintaining two separate memory seeders creates inconsistency
- No unique functionality that isn't in the replacement

**Migration path:**
```bash
# Old (deprecated)
python scripts/seed_memory_demo_data.py

# New (recommended)
python scripts/demo/seed_demo_data.py
```

**Programmatic usage:**
```python
# Old (deprecated)
from scripts import seed_memory_demo_data
seed_memory_demo_data.seed_all(db)

# New (recommended)
from scripts.demo import seed_demo_data
seed_demo_data.seed_procedural_memory(db)
seed_demo_data.seed_semantic_memory(db)
seed_demo_data.seed_episodic_memory(db)
```

---

### cleanup_old_collections.py & cleanup_old_collections_auto.py
**Deprecated:** January 14, 2026
**Migration Status:** Complete (one-time use)

**Reason for deprecation:**
- These were one-time migration scripts for the January 2026 memory collection migration
- Dropped old collections: memory_short_term, memory_long_term, memory_shared
- Migration is now complete, scripts no longer needed
- New memory architecture uses: memory_episodic, memory_semantic, memory_procedural

**No replacement needed** - This was a one-time migration task that is now complete.

---

### migrate_memory_collections.py
**Deprecated:** January 14, 2026
**Migration Status:** Complete (guide document)

**Reason for deprecation:**
- This was a migration guide/reference script for the January 2026 memory migration
- Documented the mapping from old to new collection structure
- Migration is complete as of January 13, 2026 (commit eaf3d61)
- Code is now fully migrated to new memory architecture

**No replacement needed** - Migration is complete.

**Reference:**
- See `docs/archive/MIGRATION_STATUS_2026-01-13.md` for complete migration details
- See `docs/archive/SESSION_SUMMARY_2026-01-13.md` for full session documentation

---

### add_workflow_patterns.py
**Deprecated:** January 14, 2026
**Replaced by:** Data already seeded in `scripts/demo/seed_demo_data.py`

**Reason for deprecation:**
- One-time script to add 5 additional workflow patterns to procedural memory
- These workflows are now included in the standard demo data seed
- Running this script would create duplicates
- No longer needed for new setups

**Migration path:**
```bash
# Old (deprecated)
python scripts/add_workflow_patterns.py

# New (recommended) - Workflows already included
python scripts/demo/seed_demo_data.py
```

**Workflows added (now in seed_demo_data.py):**
- Reassign Task Workflow
- Create Project with Standard Tasks
- Clone Project Structure
- Handoff All Tasks
- Escalate Blocked Tasks

---

### seed_demo_templates.py
**Deprecated:** January 14, 2026
**Replaced by:** Data already seeded in `scripts/demo/seed_demo_data.py`

**Reason for deprecation:**
- One-time script to add 3 demo templates to procedural memory
- These templates are now included in the standard demo data seed
- Running this script would create duplicates
- No longer needed for new setups

**Migration path:**
```bash
# Old (deprecated)
python scripts/seed_demo_templates.py

# New (recommended) - Templates already included
python scripts/demo/seed_demo_data.py
```

**Templates added (now in seed_demo_data.py):**
- PRD Template
- Roadmap Template
- Market Research Template

---

## Removal Timeline

**Phase 1 (Current):** Scripts moved to `deprecated/` directory
- Scripts are preserved but clearly marked as deprecated
- Documentation updated to reference new scripts
- Warning added to prevent new usage

**Phase 2 (After 1 sprint):** Verification period
- Monitor for any lingering dependencies
- Ensure no breakage from reorganization
- Gather feedback from team

**Phase 3 (Future cleanup):** Complete removal
- Delete scripts from repository
- Remove this directory entirely
- Update git history if needed

---

## If You Need These Scripts

If you absolutely need these deprecated scripts for some reason:

1. **Don't use them directly** - They may have import errors due to reorganization
2. **Check the replacement first** - The new scripts likely do what you need
3. **Ask for help** - Reach out to the team if unsure
4. **Consider migration** - Update your workflow to use new scripts

---

## Questions?

If you have questions about:
- Why a script was deprecated
- How to migrate to the replacement
- Whether to delete this directory

See:
- [Reorganization Plan](../../REORGANIZATION_PLAN.md)
- [Scripts README](../README.md)
- Git commit history for this directory
