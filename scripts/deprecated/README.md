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
