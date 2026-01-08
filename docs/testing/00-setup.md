# 00 - Pre-Test Setup

**Time:** 5 minutes  
**Priority:** Required before any testing

---

## 1. Start the Applications

```bash
# Terminal 1: Main app
cd /path/to/flow-companion
streamlit run streamlit_app.py --server.port 8501

# Terminal 2: Evals dashboard (optional)
streamlit run evals_app.py --server.port 8502
```

---

## 2. Verify Services

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

## 3. Reset Test State

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

## 4. Default Toggle Settings

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
```

### Comparison Testing (Baseline OFF)

For testing "without memory" comparisons:
```
Memory Engineering:
☐ Enable Memory: OFF
```

---

## 5. Test Environment Checklist

| Item | Check | Notes |
|------|-------|-------|
| Browser | Chrome/Safari | Avoid Firefox for voice |
| Network | Stable connection | MongoDB Atlas + Voyage API |
| Screen | Large enough for debug panel | 1280x800 minimum |
| Audio | Microphone access | For voice tests |

---

## 6. Known Environment Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| MongoDB timeout | First query slow | Wait for connection pool |
| Embedding cold start | First search slow | Run a warm-up search |
| Voice permission | No audio capture | Check browser permissions |
| Memory not updating | Stats don't change | Check MongoDB write permissions |

---

## Next Steps

Once setup is verified, proceed to:
- [01-slash-commands.md](01-slash-commands.md) - Test direct DB path
- [02-text-queries.md](02-text-queries.md) - Test LLM queries
- [06-memory-engineering.md](06-memory-engineering.md) - Test memory system

---

*Setup Guide v2.0*
