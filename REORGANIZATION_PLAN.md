# Scripts & Tests Reorganization Plan

**Date:** 2026-01-12
**Branch:** demo-stabilization
**Purpose:** Clean up and reorganize scripts/, example-scripts/, and tests/ directories

---

## Current State Analysis

### scripts/ Directory (17 files)
**Problems:**
- 3 deprecated/redundant scripts taking up space
- Debug scripts mixed with production scripts
- No clear separation between setup vs. demo vs. testing scripts

**Files:**
- Active: setup.py, init_db.py, verify_setup.py, seed_demo_data.py, reset_demo.py, cleanup_database.py, utils.py
- Deprecated: setup_database.py, load_sample_data.py, seed_memory_demo_data.py
- Debug: debug/debug_agent.py, debug/test_*.py, test_memory_system.py, test_multi_step_intent.py

### example-scripts/ Directory (2 files)
**Problems:**
- References deprecated load_sample_data.py script
- Should contain demo scripts but has documentation instead
- Unclear purpose vs. docs/testing/

**Files:**
- SAMPLE_DATA.md - References load_sample_data.py (deprecated)
- VOICE_TEST_SCRIPTS.md - Voice testing guidance

### tests/ Directory (45 files)
**Problems:**
- test_mcp_agent.py exists in BOTH root and integration/ (duplicate)
- test_memory_types.py and test_tool_discoveries.py in root (should be in unit/)
- 14 memory tests in integration/memory/ - should some be unit tests?

**Structure:**
```
tests/
├── agents/          (5 tests)
├── fixtures/        (helpers)
├── integration/     (17 tests)
│   └── memory/      (14 memory tests)
├── performance/     (1 test)
├── regression/      (1 test)
├── search/          (2 tests)
├── ui/              (1 test)
├── unit/            (1 test)
├── utils/           (1 test)
└── ROOT LEVEL       (3 misplaced tests)
```

---

## Reorganization Strategy

### Phase 1: scripts/ Directory

#### 1.1 Create New Structure
```
scripts/
├── setup/           # First-time setup & verification
│   ├── setup.py
│   ├── init_db.py
│   ├── verify_setup.py
│   └── utils.py
├── demo/            # Demo preparation & data
│   ├── seed_demo_data.py
│   └── reset_demo.py
├── maintenance/     # Database cleanup & utilities
│   └── cleanup_database.py
├── deprecated/      # Old scripts (to be removed)
│   ├── setup_database.py
│   ├── load_sample_data.py
│   └── seed_memory_demo_data.py
└── dev/             # Development/debug scripts
    ├── test_memory_system.py
    ├── test_multi_step_intent.py
    └── debug/
        ├── debug_agent.py
        ├── test_hybrid_search.py
        ├── test_tool_coordinator.py
        └── test_voice_flow.py
```

#### 1.2 Update Import Paths
- Update setup.py imports: `from scripts.demo.seed_demo_data import ...`
- Update reset_demo.py imports
- Update documentation references

### Phase 2: example-scripts/ Directory

**Decision: DEPRECATE this directory**

**Rationale:**
- SAMPLE_DATA.md references deprecated load_sample_data.py
- VOICE_TEST_SCRIPTS.md is demo documentation, not executable scripts
- Content belongs in docs/testing/ or docs/demo/

**Actions:**
1. Move VOICE_TEST_SCRIPTS.md → docs/testing/voice-testing.md
2. Update SAMPLE_DATA.md → docs/testing/demo-data.md (reference seed_demo_data.py instead)
3. Delete example-scripts/ directory
4. Update any references to example-scripts/ in documentation

### Phase 3: tests/ Directory

#### 3.1 Fix Misplaced Tests
```
Move:
├── tests/test_mcp_agent.py → DELETE (duplicate of integration/test_mcp_agent.py)
├── tests/test_memory_types.py → tests/unit/test_memory_types.py
└── tests/test_tool_discoveries.py → tests/unit/test_tool_discoveries.py
```

#### 3.2 Final Structure (Clean)
```
tests/
├── agents/          # Agent-specific tests (5)
├── fixtures/        # Test fixtures & helpers
├── integration/     # Integration tests (17)
│   └── memory/      # Memory system integration (14)
├── performance/     # Performance benchmarks (1)
├── regression/      # Regression tests (1)
├── search/          # Search functionality (2)
├── ui/              # UI tests (1)
├── unit/            # Unit tests (4) ← FIXED
└── utils/           # Utility tests (1)
```

---

## Implementation Steps

### Step 1: Backup Current State
```bash
git status  # Ensure clean working tree
git checkout -b reorganize-scripts
```

### Step 2: Reorganize scripts/
```bash
# Create new directories
mkdir -p scripts/{setup,demo,maintenance,deprecated,dev}
mkdir -p scripts/dev/debug

# Move active scripts
mv scripts/setup.py scripts/setup/
mv scripts/init_db.py scripts/setup/
mv scripts/verify_setup.py scripts/setup/
mv scripts/utils.py scripts/setup/

mv scripts/seed_demo_data.py scripts/demo/
mv scripts/reset_demo.py scripts/demo/

mv scripts/cleanup_database.py scripts/maintenance/

# Move deprecated scripts
mv scripts/setup_database.py scripts/deprecated/
mv scripts/load_sample_data.py scripts/deprecated/
mv scripts/seed_memory_demo_data.py scripts/deprecated/

# Move dev/debug scripts
mv scripts/test_memory_system.py scripts/dev/
mv scripts/test_multi_step_intent.py scripts/dev/
mv scripts/debug/* scripts/dev/debug/
rmdir scripts/debug
```

### Step 3: Update Import Paths
Update files that import from moved scripts:
- scripts/setup/setup.py
- scripts/demo/reset_demo.py
- Any test files

### Step 4: Reorganize example-scripts/
```bash
# Move to docs
mv example-scripts/VOICE_TEST_SCRIPTS.md docs/testing/voice-testing.md

# Create updated demo data guide
# (Manual: create docs/testing/demo-data.md referencing seed_demo_data.py)

# Remove directory
rm -rf example-scripts/
```

### Step 5: Fix tests/
```bash
# Remove duplicate
rm tests/test_mcp_agent.py  # Keep integration/test_mcp_agent.py

# Move misplaced unit tests
mv tests/test_memory_types.py tests/unit/
mv tests/test_tool_discoveries.py tests/unit/
```

### Step 6: Update Documentation
Files to update:
- README.md - Update setup instructions
- scripts/README.md - Update script references
- docs/testing/00-setup.md - Update paths
- docs/testing/DEMO_CHECKLIST.md - Update script paths

### Step 7: Add Deprecation Notices
Create scripts/deprecated/README.md explaining why scripts are deprecated

---

## Files Requiring Updates

### Import Updates Needed:
1. **scripts/setup/setup.py**
   - Change: `from seed_demo_data import seed_all` → `from scripts.demo.seed_demo_data import seed_all`
   - Change: `from init_db import initialize_database` → Same directory import

2. **scripts/demo/reset_demo.py**
   - Change: `from seed_demo_data import seed_all, clear_collections, verify_seed`
   - Change: `from verify_setup import ...`

3. **Documentation Files:**
   - README.md (lines mentioning scripts/)
   - scripts/README.md (all script references)
   - docs/testing/*.md (setup paths)

---

## Verification Checklist

After reorganization:
- [ ] python scripts/setup/setup.py works
- [ ] python scripts/demo/reset_demo.py works
- [ ] python scripts/setup/verify_setup.py works
- [ ] All tests pass: pytest tests/
- [ ] Documentation paths are correct
- [ ] No broken imports
- [ ] scripts/deprecated/README.md created
- [ ] example-scripts/ removed
- [ ] tests/ has no root-level test files

---

## Rollback Plan

If reorganization causes issues:
```bash
git checkout demo-stabilization
git branch -D reorganize-scripts
```

---

## Benefits

### Improved Organization
- Clear separation: setup vs. demo vs. maintenance vs. dev
- Easy to find relevant scripts
- Deprecated scripts isolated but preserved

### Better Developer Experience
- New developers know exactly where to look
- Setup scripts in one place
- Debug scripts clearly marked as dev tools

### Maintainability
- Easier to remove deprecated scripts later
- Clear ownership of script categories
- Better documentation organization

---

## Next Steps After Completion

1. Create commit: "Reorganize scripts, tests, and deprecate example-scripts"
2. Update CI/CD if paths are hardcoded
3. After 1 sprint, delete scripts/deprecated/ if no issues
4. Consider moving scripts/dev/debug/ tests to tests/manual/ or tests/exploratory/
