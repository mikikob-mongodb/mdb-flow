# Flow Companion - Scripts Directory

Comprehensive collection of setup, maintenance, and demo preparation scripts for Flow Companion.

---

## 🚀 Quick Start (New Developer)

**If you've just cloned this repository:**

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run all-in-one setup (creates .env, initializes DB, verifies)
python scripts/setup.py

# 3. Create vector search indexes in Atlas UI (see output for instructions)

# 4. Start the app
streamlit run streamlit_app.py
```

**If preparing for a demo:**

```bash
# Reset to clean demo state
python scripts/reset_demo.py --force

# Verify ready
python scripts/reset_demo.py --verify-only
```

---

## 📚 Script Categories

### 🎯 First-Time Setup
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **setup.py** | All-in-one initialization | First time setup, new developers |
| **init_db.py** | Create collections + indexes | Database initialization, schema updates |
| **verify_setup.py** | Health check all components | After setup, before demos, troubleshooting |

### 🎬 Demo & Data
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **reset_demo.py** | Complete demo reset (clear + seed + verify) | Before demos, presentations |
| **seed_demo_data.py** | Seed presentation-ready demo data | Demo preparation, testing memory system |
| **seed_memory_demo_data.py** | Seed memory collections only | Memory-specific demos |
| **load_sample_data.py** | Load sample tasks/projects | General testing, development |

### 🔧 Maintenance & Testing
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **setup_database.py** | Create indexes (legacy, use init_db.py instead) | Manual index creation |
| **cleanup_database.py** | Clean test data, duplicates, orphans | Regular maintenance |
| **test_memory_system.py** | Test 5-tier memory system | Development, verification |

### 🐛 Debug Tools
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **debug/debug_agent.py** | Test agent vs direct DB queries | Debugging agent behavior |
| **debug/test_hybrid_search.py** | Test hybrid search | Search debugging |
| **debug/test_tool_coordinator.py** | Test coordinator | Coordinator debugging |
| **debug/test_voice_flow.py** | Test voice processing | Voice feature debugging |

---

## 📖 Detailed Documentation

### setup.py - All-in-One Setup ⭐

**Purpose:** Complete first-time setup for new developers. Orchestrates all setup steps.

**Usage:**
```bash
# Interactive setup (recommended)
python scripts/setup.py

# Non-interactive (requires existing .env)
python scripts/setup.py --non-interactive

# Skip demo data
python scripts/setup.py --no-demo-data

# Quick verification only
python scripts/setup.py --quick

# Full reset (DANGEROUS)
python scripts/setup.py --reset
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

**Purpose:** Create all MongoDB collections and indexes. Foundation for database setup.

**Usage:**
```bash
# Initialize everything
python scripts/init_db.py

# Collections only
python scripts/init_db.py --collections-only

# Indexes only
python scripts/init_db.py --indexes-only

# Check existing setup
python scripts/init_db.py --check

# Show vector index instructions
python scripts/init_db.py --vector-instructions

# Force recreate (DANGEROUS - drops data!)
python scripts/init_db.py --force
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

**Purpose:** Comprehensive verification that everything is configured correctly.

**Usage:**
```bash
# Full verification
python scripts/verify_setup.py

# Quick check (env + MongoDB only)
python scripts/verify_setup.py --quick

# Skip API tests (faster)
python scripts/verify_setup.py --skip-api

# Verbose output
python scripts/verify_setup.py --verbose
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

**Purpose:** Complete demo preparation (teardown + seed + verify). Use before presentations.

**Usage:**
```bash
# Full reset (recommended before demos)
python scripts/reset_demo.py --force

# Just verify current state
python scripts/reset_demo.py --verify-only

# Just clear collections
python scripts/reset_demo.py --teardown-only

# Preview what would be deleted
python scripts/reset_demo.py --dry-run

# Skip embeddings (faster)
python scripts/reset_demo.py --skip-embeddings
```

**Phases:**
1. **TEARDOWN:** Clear 7 collections (projects, tasks, all memories)
2. **SETUP:** Call seed_demo_data.py to seed fresh data
3. **VERIFY:** Check GTM template, Project Alpha, Q3 GTM exist

**⚠️  WARNING:** Deletes all demo data. DO NOT use with production data.

**Exit codes:** 0 = ready for demo, 1 = verification failed

---

### seed_demo_data.py - Presentation Demo Data ⭐

**Purpose:** Seed realistic, interconnected data for showcasing 5-tier memory system.

**Usage:**
```bash
# Seed demo data (idempotent)
python scripts/seed_demo_data.py

# Clear and reseed
python scripts/seed_demo_data.py --clean

# Verify data exists
python scripts/seed_demo_data.py --verify

# Skip embeddings (faster, but no semantic search)
python scripts/seed_demo_data.py --skip-embeddings
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

### Other Scripts (Existing)

#### setup_database.py (Legacy - Use init_db.py instead)

Creates indexes for tasks, projects, memory collections.

```bash
python scripts/setup_database.py
python scripts/setup_database.py --standard  # Standard indexes only
python scripts/setup_database.py --memory    # Memory indexes only
python scripts/setup_database.py --list      # List existing
```

#### cleanup_database.py

Remove test data, duplicates, orphaned records.

```bash
python scripts/cleanup_database.py --status          # Show status
python scripts/cleanup_database.py --mark --delete   # Clean test data
python scripts/cleanup_database.py --full            # Full cleanup
```

#### test_memory_system.py

Test 5-tier memory system.

```bash
python scripts/test_memory_system.py                # All tests
python scripts/test_memory_system.py --long-term    # Long-term only
python scripts/test_memory_system.py --performance  # Performance tests
```

#### load_sample_data.py

Load sample tasks/projects for general development.

```bash
python scripts/load_sample_data.py
python scripts/load_sample_data.py --skip-embeddings
```

#### seed_memory_demo_data.py

Seed memory collections (separate from seed_demo_data.py).

```bash
python scripts/seed_memory_demo_data.py
python scripts/seed_memory_demo_data.py --with-sample-data
python scripts/seed_memory_demo_data.py --skip-embeddings
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
python scripts/setup.py

# 3. Create vector search indexes in Atlas UI
python scripts/init_db.py --vector-instructions
# Then create indexes manually in Atlas

# 4. Verify everything works
python scripts/verify_setup.py

# 5. Start app
streamlit run streamlit_app.py
```

### Demo Preparation

```bash
# Night before
python scripts/reset_demo.py --force

# Morning of demo (15 min before)
python scripts/reset_demo.py --verify-only
streamlit run streamlit_app.py
# Use demo user: demo-user
```

### Database Schema Update

```bash
# After pulling new code
git pull

# Update indexes
python scripts/init_db.py --indexes-only

# Verify
python scripts/verify_setup.py

# Optionally reseed demo data
python scripts/seed_demo_data.py --clean
```

### Troubleshooting

```bash
# 1. Quick health check
python scripts/verify_setup.py --quick

# 2. Full verification
python scripts/verify_setup.py --verbose

# 3. If database issues
python scripts/init_db.py

# 4. If data issues
python scripts/seed_demo_data.py --clean

# 5. Full reset (last resort)
python scripts/setup.py --reset
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

**Last Updated:** January 9, 2026
**Version:** 3.0 (Milestone 6 - MCP Agent)
