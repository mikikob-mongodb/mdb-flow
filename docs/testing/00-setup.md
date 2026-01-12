# 00 - Pre-Test Setup

**Time:** 5-10 minutes
**Priority:** Required before any testing
**Updated:** January 9, 2026 (Milestone 6 - MCP Agent)

---

## 0. First-Time Setup (New Developers)

If this is your first time setting up Flow Companion, use the comprehensive setup script:

```bash
# One-command setup (checks environment, initializes DB, seeds data, verifies)
python scripts/setup/setup.py

# Alternative: Run individual setup steps
python scripts/setup/verify_setup.py  # Check environment and dependencies
python scripts/setup/init_db.py       # Initialize database collections and indexes
python scripts/demo/seed_demo_data.py # Seed demo data
```

**For existing setups**, skip to section 1 below.

---

## 1. Environment Configuration

### 1.1 Required Environment Variables

Create or verify `.env` file in project root:

```bash
# Required: AI & Embedding APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
VOYAGE_API_KEY=pa-xxxxx
OPENAI_API_KEY=sk-xxxxx  # For voice transcription

# Required: Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=flow_companion

# Optional: MCP Mode (Milestone 6)
MCP_MODE_ENABLED=false  # Toggle in UI instead
TAVILY_API_KEY=tvly-xxxxx  # Leave empty to disable Tavily

# Optional: Development
LOG_LEVEL=INFO
DEBUG=false
```

### 1.2 Seed Demo Data (Recommended)

For demonstration and testing, use the demo reset script for a clean state:

```bash
# Activate virtual environment
source venv/bin/activate

# RECOMMENDED: Full reset (clear + seed + verify)
python scripts/demo/reset_demo.py --force

# Alternative: Just seed without clearing
python scripts/demo/reset_demo.py --seed-only

# Alternative: Just seed (if already clean)
python scripts/demo/seed_demo_data.py

# Check current state
python scripts/demo/reset_demo.py --verify-only

# See what would be deleted (dry run)
python scripts/demo/reset_demo.py --dry-run
```

**What gets seeded:**
- 3 demo projects (Project Alpha, Beta, Marketing Website)
- 15 sample tasks with various statuses
- User preferences (working_hours, focus_mode)
- Procedural rules (shortcuts like "done" → complete task)
- GTM Roadmap Template (for multi-step workflow demos)

**reset_demo.py Features:**
- `--force` - Skip confirmation prompts (use for night before demo)
- `--teardown-only` - Just clear collections
- `--verify-only` - Check if demo data exists
- `--dry-run` - Show what would be deleted without doing it
- `--skip-embeddings` - Faster seeding (no vector search)

**Note:** Run reset script before each demo for consistent state.

---

## 2. Start the Applications

```bash
# Terminal 1: Main app
cd /path/to/flow-companion
streamlit run streamlit_app.py --server.port 8501

# Terminal 2: Evals dashboard (optional)
streamlit run evals_app.py --server.port 8502
```

---

## 3. Verify Services

| Service | Check | Expected |
|---------|-------|----------|
| Streamlit | http://localhost:8501 | App loads, no errors |
| MongoDB | Sidebar shows connection | "Connected to MongoDB Atlas" |
| Memory | Sidebar shows memory panel | "🧠 Memory Settings" visible |
| Embeddings | Run a search | Voyage API responds |

**Verification Checklist:**
```
□ Streamlit UI loads without errors
□ MongoDB connection indicator is green
□ Memory panel shows all 5 memory types
□ Debug panel is visible at bottom
```

---

## 4. Reset Test State

Before each test session:

```
□ Click "🗑️ Clear Session Memory" in sidebar
□ Refresh the page (Cmd+R / Ctrl+R)
□ Verify "Memory Stats" shows:
    - Working Memory: 0 entries
    - Episodic Memory: (may have historical data)
    - Semantic Memory: (may have preferences)
    - Procedural Memory: (may have rules)
    - Shared Memory: 0 entries
```

For a **completely clean state** (new user simulation):
```
□ Click "🆕 New Session" in sidebar
□ This clears ALL memory including long-term
```

---

## 5. Default Toggle Settings

### Baseline Testing (All ON)

```
Context Engineering:
☑ Compress Results: ON
☑ Streamlined Prompt: ON
☑ Prompt Caching: ON

Memory Engineering:
☑ Enable Memory: ON
☑ Working Memory: ON
☑ Episodic Memory: ON
☑ Semantic Memory: ON
☑ Procedural Memory: ON
☑ Shared Memory: ON
☑ Context Injection: ON

Experimental (Milestone 6):
☐ MCP Mode: OFF (default - enable when testing MCP features)
```

### Comparison Testing (Baseline OFF)

For testing "without memory" comparisons:
```
Memory Engineering:
☐ Enable Memory: OFF
```

---

## 6. Test Environment Checklist

| Item | Check | Notes |
|------|-------|-------|
| Browser | Chrome/Safari | Avoid Firefox for voice |
| Network | Stable connection | MongoDB Atlas + Voyage API |
| Screen | Large enough for debug panel | 1280x800 minimum |
| Audio | Microphone access | For voice tests |

---

## 7. Known Environment Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| MongoDB timeout | First query slow | Wait for connection pool |
| Embedding cold start | First search slow | Run a warm-up search |
| Voice permission | No audio capture | Check browser permissions |
| Memory not updating | Stats don't change | Check MongoDB write permissions |
| MCP connection fails | Tavily tools not available | Verify TAVILY_API_KEY in .env |
| MCP timeout | Request takes >30s | Network issue or Tavily API down |

---

## Next Steps

Once setup is verified, proceed to:
- [01-slash-commands.md](01-slash-commands.md) - Test direct DB path
- [02-text-queries.md](02-text-queries.md) - Test LLM queries
- [06-memory-engineering.md](06-memory-engineering.md) - Test memory system

---

## 8. MCP Mode Setup (Optional - Milestone 6)

To test MCP Agent features:

**1. Get Tavily API Key:**
- Sign up at https://tavily.com
- Get API key from dashboard
- Add to `.env`: `TAVILY_API_KEY=tvly-xxxxx`

**2. Enable in UI:**
- In sidebar under "🧪 Experimental"
- Toggle "MCP Mode" ON
- Verify: "MCP Servers: 1 connected (Tavily)" appears

**3. Test Connection:**
- Ask: "What are the latest AI developments?"
- Should route to Tavily for web search
- Response includes 🔌 MCP indicator

**Note:** MCP Mode is disabled by default. Only enable for testing web search and multi-step workflows.

---

*Setup Guide v3.0 - Updated for Milestone 6*
