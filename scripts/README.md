# Flow Companion - Scripts Directory

Comprehensive collection of setup, maintenance, and demo preparation scripts for Flow Companion.

**Reorganized:** January 12, 2026 - Scripts now organized by category in subdirectories.

---

## 📁 Directory Structure

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
├── dev/             # Development & debug tools
│   ├── test_memory_system.py
│   ├── test_multi_step_intent.py
│   └── debug/
│       ├── debug_agent.py
│       ├── test_hybrid_search.py
│       ├── test_tool_coordinator.py
│       └── test_voice_flow.py
└── deprecated/      # Old scripts (see deprecated/README.md)
    ├── setup_database.py
    ├── load_sample_data.py
    └── seed_memory_demo_data.py
```

---

## 🚀 Quick Start (New Developer)

**If you've just cloned this repository:**

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run all-in-one setup (creates .env, initializes DB, verifies)
python scripts/setup/setup.py

# 3. Create vector search indexes in Atlas UI (see output for instructions)

# 4. Start the app
streamlit run ui/streamlit_app.py
```

**If preparing for a demo:**

```bash
# Reset to clean demo state
python scripts/demo/reset_demo.py

# Verify ready
python scripts/demo/reset_demo.py --verify-only
```

---

## 📚 Script Categories

### 🎯 First-Time Setup (`scripts/setup/`)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **setup.py** | All-in-one initialization | First time setup, new developers |
| **init_db.py** | Create collections + indexes | Database initialization, schema updates |
| **verify_setup.py** | Health check all components | After setup, before demos, troubleshooting |
| **utils.py** | Shared utilities module | Import in other scripts for common functionality |

### 🎬 Demo & Data (`scripts/demo/`)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **reset_demo.py** | Complete demo reset (clear + seed + verify) | Before demos, presentations |
| **seed_demo_data.py** | Seed presentation-ready demo data | Demo preparation, testing memory system |

### 🔧 Maintenance (`scripts/maintenance/`)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **cleanup_database.py** | Clean test data, duplicates, orphans | Regular maintenance |

### 🛠️ Development Tools (`scripts/dev/`)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **test_memory_system.py** | Test 5-tier memory system | Development, verification |
| **test_multi_step_intent.py** | Test multi-step intent classification | Coordinator debugging |
| **debug/debug_agent.py** | Test agent vs direct DB queries | Debugging agent behavior |
| **debug/test_hybrid_search.py** | Test hybrid search | Search debugging |
| **debug/test_tool_coordinator.py** | Test coordinator | Coordinator debugging |
| **debug/test_voice_flow.py** | Test voice processing | Voice feature debugging |

### 🗑️ Deprecated (`scripts/deprecated/`)
| Script | Status | Replacement |
|--------|--------|-------------|
| ~~setup_database.py~~ | Deprecated | Use `scripts/setup/init_db.py` |
| ~~load_sample_data.py~~ | Deprecated | Use `scripts/demo/seed_demo_data.py` |
| ~~seed_memory_demo_data.py~~ | Deprecated | Use `scripts/demo/seed_demo_data.py` |

**Note:** See `scripts/deprecated/README.md` for migration guide.

---

## 📖 Detailed Documentation

### setup.py - All-in-One Setup ⭐

**Location:** `scripts/setup/setup.py`

**Purpose:** Complete first-time setup for new developers. Orchestrates all setup steps.

**Usage:**
```bash
# Interactive setup (recommended)
python scripts/setup/setup.py

# Skip demo data seeding
python scripts/setup/setup.py --skip-seed

# Force re-run even if already set up
python scripts/setup/setup.py --force
```

**What it does:**
1. ✅ Checks Python 3.9+ and dependencies
2. ✅ Creates/validates .env file (interactive)
3. ✅ Calls `init_db.py` to create collections and indexes
4. ✅ Calls `verify_setup.py` for health checks
5. ✅ Optionally calls `seed_demo_data.py` for demo data

**Exit codes:** 0 = success, 1 = failure

---

### init_db.py - Database Initialization

**Location:** `scripts/setup/init_db.py`

**Purpose:** Create all MongoDB collections and indexes. Foundation for database setup.

**Usage:**
```bash
# Initialize everything
python scripts/setup/init_db.py

# Verify existing setup
python scripts/setup/init_db.py --verify

# Drop and recreate (DANGEROUS!)
python scripts/setup/init_db.py --drop-first
```

**Creates:**

**Collections (8):**
- tasks, projects, settings
- short_term_memory, long_term_memory, shared_memory
- tool_discoveries, eval_comparison_runs

**Indexes:**
- Standard indexes (user_id, status, timestamps)
- Compound indexes (user_id + status, etc.)
- Text search indexes (weighted full-text search)
- TTL indexes (auto-expiration: 2hr for short-term, 5min for shared)

**Vector Search Indexes (Manual in Atlas UI):**
1. tasks.vector_index
2. projects.vector_index
3. long_term_memory.memory_embeddings
4. long_term_memory.vector_index
5. tool_discoveries.discovery_vector_index

All 1024 dimensions (Voyage AI voyage-3), cosine similarity.

Run `--vector-instructions` for full JSON definitions.

---

### verify_setup.py - Health Check

**Location:** `scripts/setup/verify_setup.py`

**Purpose:** Comprehensive verification that everything is configured correctly.

**Usage:**
```bash
# Full verification
python scripts/setup/verify_setup.py

# Quick check (env + MongoDB only)
python scripts/setup/verify_setup.py --quick

# Verbose output with detailed diagnostics
python scripts/setup/verify_setup.py --verbose
```

**Checks:**
- ✅ Environment (.env file, required/optional variables)
- ✅ MongoDB (connection, database access, write permissions)
- ✅ Collections (all 8 required collections exist)
- ✅ Indexes (standard, text search, TTL, vector search)
- ✅ APIs (Anthropic, Voyage AI, OpenAI, Tavily)
- ✅ Operations (INSERT, QUERY, UPDATE, DELETE)

**Exit codes:** 0 = all passed, 1 = some failed

---

### reset_demo.py - Demo Reset

**Location:** `scripts/demo/reset_demo.py`

**Purpose:** Complete demo preparation (teardown + seed + verify). Use before presentations.

**Usage:**
```bash
# Full reset (recommended before demos)
python scripts/demo/reset_demo.py

# Just verify current state
python scripts/demo/reset_demo.py --verify-only

# Just clear collections (requires --force)
python scripts/demo/reset_demo.py --teardown-only --force

# Just seed (no teardown)
python scripts/demo/reset_demo.py --seed-only

# Skip embeddings (faster)
python scripts/demo/reset_demo.py --skip-embeddings
```

**Phases:**
1. **TEARDOWN:** Clear 6 collections (projects, tasks, all memories, tool_discoveries)
2. **SETUP:** Calls seed_demo_data.py functions directly to seed fresh data
3. **VERIFY:** Check GTM template, Project Alpha, Q3 GTM, user preferences exist

**Safety Features:**
- Detects production URIs (production/prod/live keywords) and requires extra confirmation
- Requires --force flag for --teardown-only
- Confirmation prompts for destructive operations
- Clean output format with counts

**Output Format:**
```
🔄 Resetting Flow Companion Demo Data...

🗑️  Teardown:
  projects: 3 deleted
  tasks: 7 deleted
  long_term_memory: 9 deleted

🌱 Seeding:
  projects: 3 inserted
  tasks: 7 inserted
  procedural memory: 2 inserted
  semantic memory: 4 inserted
  episodic memory: 3 inserted
  embeddings: 5 generated

✅ Verification:
  GTM Roadmap Template: ✅ EXISTS
  Project Alpha: ✅ EXISTS (7 tasks)
  Q3 Fintech GTM: ✅ EXISTS (completed)
  User preferences: ✅ EXISTS (4 preferences)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Ready for demo!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**⚠️  WARNING:** Deletes all demo data. DO NOT use with production data.

**Exit codes:** 0 = ready for demo, 1 = verification failed

---

### seed_demo_data.py - Presentation Demo Data ⭐

**Location:** `scripts/demo/seed_demo_data.py`

**Purpose:** Seed realistic, interconnected data for showcasing 5-tier memory system.

**Usage:**
```bash
# Seed demo data (idempotent)
python scripts/demo/seed_demo_data.py

# Clear and reseed
python scripts/demo/seed_demo_data.py --clean

# Verify data exists
python scripts/demo/seed_demo_data.py --verify

# Skip embeddings (faster, but no semantic search)
python scripts/demo/seed_demo_data.py --skip-embeddings
```

**Creates:**

**Projects (3):**
- Project Alpha (active) - Infrastructure modernization, 7 tasks
- Q3 Fintech GTM (completed) - Past successful GTM
- AI Developer Outreach (completed) - Another past GTM

**Tasks (7):** All for Project Alpha (2 done, 1 in_progress, 4 todo)

**Procedural Memory (2):**
- **GTM Roadmap Template** ⭐ - 12 tasks across 3 phases (key for demos!)
- Market Research Questions - 6 standard questions

**Semantic Memory (4 preferences):**
- default_priority = high, communication_style = concise, etc.

**Episodic Memory (3 actions):**
- Created Q3 Fintech GTM, Completed it, Applied template to AI Outreach

**Demo User:** `demo-user`

**Embeddings:** 2 procedural + 3 episodic (1024-dim Voyage AI)

**Features:**
- Idempotent (can run multiple times safely)
- Realistic interconnected data
- Demonstrates template learning and reuse

---

### Other Scripts

#### cleanup_database.py

**Location:** `scripts/maintenance/cleanup_database.py`

Remove test data, duplicates, orphaned records.

```bash
python scripts/maintenance/cleanup_database.py --status          # Show status
python scripts/maintenance/cleanup_database.py --mark --delete   # Clean test data
python scripts/maintenance/cleanup_database.py --full            # Full cleanup
```

#### test_memory_system.py

**Location:** `scripts/dev/test_memory_system.py`

Test 5-tier memory system.

```bash
python scripts/dev/test_memory_system.py                # All tests
python scripts/dev/test_memory_system.py --long-term    # Long-term only
python scripts/dev/test_memory_system.py --performance  # Performance tests
```

---

## 🔄 Common Workflows

### New Developer Onboarding

```bash
# 1. Clone and setup environment
git clone <repo>
cd mdb-flow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run all-in-one setup
python scripts/setup/setup.py

# 3. Verify everything works
python scripts/setup/verify_setup.py

# 4. Start app
streamlit run ui/streamlit_app.py
```

### Demo Preparation

```bash
# Night before
python scripts/demo/reset_demo.py

# Morning of demo (15 min before)
python scripts/demo/reset_demo.py --verify-only
streamlit run ui/streamlit_app.py
# Use demo user: demo-user
```

### Database Schema Update

```bash
# After pulling new code
git pull

# Re-initialize database
python scripts/setup/init_db.py

# Verify
python scripts/setup/verify_setup.py

# Optionally reseed demo data
python scripts/demo/seed_demo_data.py --clean
```

### Troubleshooting

```bash
# 1. Quick health check
python scripts/setup/verify_setup.py --quick

# 2. Full verification
python scripts/setup/verify_setup.py --verbose

# 3. If database issues
python scripts/setup/init_db.py

# 4. If data issues
python scripts/demo/seed_demo_data.py --clean

# 5. Full reset (re-run setup)
python scripts/setup/setup.py --force
```

---

## 🔐 Environment Variables

### Required (App won't start without these)
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx       # Claude API
VOYAGE_API_KEY=pa-xxxxx              # Embeddings
OPENAI_API_KEY=sk-xxxxx              # Whisper (voice)
MONGODB_URI=mongodb+srv://...        # MongoDB connection
MONGODB_DATABASE=flow_companion       # Database name
```

### Optional (Enable specific features)
```bash
TAVILY_API_KEY=tvly-xxxxx            # Web search (MCP)
MONGODB_MCP_ENABLED=false            # MongoDB MCP (future)
MCP_MODE_ENABLED=false               # MCP mode toggle
LOG_LEVEL=INFO                       # Logging
DEBUG=false                          # Debug mode
```

### Where to Get Keys
- Anthropic: https://console.anthropic.com/
- Voyage AI: https://dash.voyageai.com/
- OpenAI: https://platform.openai.com/api-keys
- MongoDB Atlas: https://cloud.mongodb.com/
- Tavily: https://tavily.com/

---

## ⚠️ Safety & Best Practices

### DO ✅
- Run `verify_setup.py` after configuration changes
- Use `reset_demo.py --force` before demos
- Keep `.env` file secure (never commit)
- Create vector search indexes after running `init_db.py`
- Test scripts in development first
- Use `--dry-run` to preview changes

### DON'T ❌
- Run `--force` or `--reset` in production
- Share API keys or `.env` files
- Skip vector search index creation
- Run `reset_demo.py` with real user data
- Use `--clean` without understanding it deletes data

---

## 📊 Script Comparison Matrix

| Feature | setup.py | init_db.py | verify_setup.py | seed_demo_data.py | reset_demo.py |
|---------|----------|------------|-----------------|-------------------|---------------|
| Creates collections | ✓ (via init_db) | ✓ | - | - | - |
| Creates indexes | ✓ (via init_db) | ✓ | - | - | - |
| Checks environment | ✓ | - | ✓ | - | - |
| Checks collections | - | ✓ | ✓ | - | - |
| Checks indexes | - | - | ✓ | - | - |
| Checks APIs | - | - | ✓ | - | - |
| Seeds data | ✓ (optional) | - | - | ✓ | ✓ |
| Clears data | - | - | - | ✓ (--clean) | ✓ |
| Interactive | ✓ | - | - | - | ✓ (confirm) |
| Idempotent | ✓ | ✓ | ✓ | ✓ | - |
| **Use for** | First-time | DB setup | Verify | Demos | Before demos |

---

## utils.py - Shared Utilities Module

**Location:** `scripts/setup/utils.py`

**Purpose:** Common functionality for all setup scripts including database helpers, pretty output, verification, and API testing.

**Usage:**
```python
# Import utilities in your setup script
from scripts.setup.utils import (
    print_success, print_error, print_warning,
    test_connection, check_env_var, test_all_apis
)

# Database connection
success, error = test_connection()
if success:
    print_success("MongoDB connected")
else:
    print_error(f"Connection failed: {error}")

# Environment variable check
exists, preview = check_env_var("ANTHROPIC_API_KEY")
if exists:
    print_success(f"API key: {preview}")  # Shows: "sk-ant..."

# Test all APIs
results = test_all_apis()
for api, (success, details) in results.items():
    if success:
        print_success(f"{api}: {details}")
```

**Available Functions:**

**1. Database Connection:**
- `get_database()` - Get MongoDB connection
- `test_connection()` → `(success, error_message)`

**2. Pretty Output (with colorama):**
- `print_header(text)` - Formatted header with separators
- `print_success(text)` - Green ✅ + message
- `print_warning(text)` - Yellow ⚠️ + message
- `print_error(text)` - Red ❌ + message
- `print_info(text)` - Blue ℹ️ + message
- `print_step(num, total, text)` - Step 1/4 format
- `print_separator(length)` - Visual separator line

**3. Verification:**
- `check_env_var(name, required)` → `(exists, preview)`
- `check_collection_exists(db, name)` → `bool`
- `check_index_exists(db, collection, index)` → `bool`
- `get_collection_count(db, collection, filter)` → `int`

**4. API Testing:**
- `test_voyage_api()` → `(success, details)`
- `test_anthropic_api()` → `(success, details)`
- `test_tavily_mcp()` → `(success, details)`

**5. Convenience Functions:**
- `check_all_env_vars()` → `Dict[str, (exists, preview)]`
- `check_all_collections(db)` → `Dict[str, bool]`
- `test_all_apis()` → `Dict[str, (success, details)]`

**Features:**
- Auto-loads `.env` file on import
- Cross-platform colored output with colorama
- Graceful fallback if colorama not installed
- Masked env var previews for security (first 6 chars + ...)
- Can be run standalone for testing: `python scripts/utils.py`

**Example Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Flow Companion Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/4: Checking environment...
✅ ANTHROPIC_API_KEY: sk-ant... (in green)
✅ MongoDB connection successful (in green)
⚠️  Tavily API key not set (optional) (in yellow)
```

---

## 🛠️ Troubleshooting

### "Failed to connect to MongoDB"
```bash
# Check .env
cat .env | grep MONGODB

# Test connection
python -c "from shared.db import MongoDB; MongoDB().get_database(); print('OK')"
```

### "Collection does not exist"
```bash
# Initialize database
python scripts/init_db.py

# Verify
python scripts/init_db.py --check
```

### "Vector search index not found"
```bash
# Get instructions
python scripts/init_db.py --vector-instructions

# Then create indexes manually in Atlas UI
```

### "Missing required environment variables"
```bash
# Run setup to recreate .env
python scripts/setup.py

# Or manually edit .env
```

---

## 📚 Additional Resources

- **Main README:** `/README.md`
- **Architecture Docs:** `/docs/architecture/`
- **Testing Guide:** `/docs/testing/`
- **Demo Checklist:** `/docs/testing/DEMO_CHECKLIST.md`
- **Test Coverage:** `/docs/testing/TEST_COVERAGE.md`

---

**Last Updated:** January 12, 2026
**Version:** 3.1 (Reorganized structure - setup/, demo/, maintenance/, dev/, deprecated/)
