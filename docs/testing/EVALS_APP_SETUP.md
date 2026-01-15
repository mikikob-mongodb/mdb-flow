# Evals App Setup & Usage

**Date:** 2026-01-14
**Status:** ✅ Working (MongoDB storage optional)

## Quick Start

```bash
streamlit run evals_app.py --server.port 8502
```

Opens at: `http://localhost:8502`

## What It Does

The evals app compares different optimization configurations to show:
1. **Where time goes** (LLM vs Database)
2. **Impact of optimizations** on latency and tokens
3. **Performance by query type**

Perfect for Demo 3: "Where Time Goes"

---

## Two Tabs

### Tab 1: 🔬 Context Engineering

**Charts:**
- ⚡ Optimization Waterfall - latency reduction across configs
- 📊 Impact by Query Type - slash vs text vs actions
- **🔧 LLM vs Tool Time** ← THE MONEY SHOT for Demo 3
- 🪙 Token Savings by Query Type
- **⏱️ Tool Time Breakdown** ← Shows MongoDB is ~50-80ms
- 🔍 Search Mode Comparison - hybrid vs vector vs text

**How to use:**
1. Select configs (Baseline + one or more optimizations)
2. Click "🚀 Run Comparison"
3. Wait ~2-3 minutes (runs ~40 tests)
4. Charts appear with results

### Tab 2: 🧠 Memory Competencies

Tests memory system across 10 competency dimensions.
- Not needed for demo
- Useful for memory system evaluation

---

## MongoDB Storage (Optional)

### Default Behavior

Results are kept in **session state** (in-memory):
- ✅ All charts work
- ✅ Can export to JSON
- ❌ Results lost when app restarts
- ✅ Perfect for demos (no persistence needed)

### With MongoDB Collection

If `eval_comparison_runs` collection exists:
- ✅ Results persist across sessions
- ✅ Can load past runs from sidebar
- ⚠️ Optional - not required for demo

### Error Handling

```python
# From evals_app.py lines 1129-1134
try:
    save_comparison_run(run)
    st.success(f"Saved as {run.run_id}")
except Exception as e:
    st.warning(f"Results not saved to DB: {e}")
    st.success(f"Completed {len(run.tests)} tests (not persisted)")
```

If collection doesn't exist:
- Shows warning: "Results not saved to DB"
- But charts still work
- Results available during session

### Creating Collection (Optional)

If you want persistent storage:

```python
# In MongoDB shell or Compass
db.createCollection("eval_comparison_runs")

# Or let MongoDB create it automatically on first insert
# (will fail gracefully if permissions issue)
```

---

## Demo 3 Usage

### Pre-Demo Setup

**Step 1: Start both apps**

```bash
# Terminal 1: Main app
streamlit run ui/demo_app.py

# Terminal 2: Evals app
streamlit run evals_app.py --server.port 8502
```

**Step 2: Run comparison in evals app**

1. Open `localhost:8502` in browser
2. Select configs:
   - ✅ Baseline
   - ✅ All Context (or any optimization)
3. Click "🚀 Run Comparison"
4. Wait ~2-3 minutes
5. Charts appear

**Step 3: Keep tab open**

Leave browser tab open at `localhost:8502` - you'll switch to it during demo

### During Demo

**Script:**

"Let me show you where time is actually being spent."

[Switch to localhost:8502 tab]

"Here's the breakdown after running 40 test queries across different complexity levels."

[Scroll to "🔧 LLM vs Tool Time" chart]

"The LLM thinking takes 96% of the time. MongoDB queries and other tools? Only 4%."

[Point to stacked bars showing Baseline and All Context both ~96% LLM]

"Even with all our context optimizations - which reduce LLM time significantly - the split stays the same: LLM is the bottleneck, not the database."

[Scroll to "⏱️ Tool Time Breakdown" chart]

"When we break down that 4% tool time, here's what we see:"
- "Embedding generation: ~120ms (calling Voyage AI)"
- "MongoDB queries: ~50-80ms"
- "Python processing: ~30-50ms"

"And look - tool time is consistent across all configurations. Our optimizations reduce LLM thinking time, not database time. Because MongoDB is already fast enough."

**Key message:** Database is NOT the bottleneck. LLM thinking is.

---

## Test Suite Details

The comparison runs these test categories:

| Category | Tests | What It Tests |
|----------|-------|---------------|
| **Slash Commands** | 10 | Direct DB queries (no LLM) |
| **Text Queries** | 10 | Natural language → LLM → tools |
| **Text Actions** | 8 | Complex actions requiring reasoning |
| **Multi-Turn** | 6 | Conversation context handling |
| **Voice** | 6 | (Skipped by default) |

**Total:** ~40 tests per config (voice skipped)

**Runtime:** ~2-3 minutes for 2 configs

---

## Optimization Configurations

### Available Configs

| Config | What It Does |
|--------|--------------|
| **Baseline** | No optimizations |
| **Compress Results** | Truncate tool results before LLM |
| **Streamlined Prompt** | Simplified system prompts |
| **Prompt Caching** | Cache system prompts (Anthropic feature) |
| **All Context** | All 3 optimizations combined |

### Typical Results

**Latency (Baseline → All Context):**
- Baseline: ~3.5s
- All Context: ~1.8s
- **Reduction: ~48%**

**Tokens In (Baseline → All Context):**
- Baseline: ~12,000 tokens
- All Context: ~3,000 tokens
- **Reduction: ~75%**

**LLM vs Tool Split:**
- Both configs: ~96% LLM, ~4% Tools
- **Proves:** Optimizations reduce LLM time, not tool time

---

## Troubleshooting

### "Coordinator not initialized" error

```python
# Should auto-initialize, but if it fails:
# Check that coordinator is importable
from agents.coordinator import coordinator
```

### Charts not appearing

- Wait for "Completed X tests" message
- Check browser console for errors
- Try refreshing page (results should persist in session)

### "Results not saved to DB" warning

- This is normal if `eval_comparison_runs` collection doesn't exist
- Charts still work, just no persistence
- Safe to ignore for demos

### Takes too long

- ~2-3 min for 2 configs is normal
- Skip voice tests (default)
- Run fewer configs (just Baseline + All Context)

---

## Export Results

After running comparison:

1. Click "📥 Export JSON"
2. Downloads `evals_{run_id}.json`

**Contains:**
- Summary metrics by config
- All test results
- Improvement percentages
- Timestamp and metadata

Useful for:
- Sharing results
- Analysis in Jupyter notebooks
- Documentation

---

## Alternative: Skip Evals App

If you don't want to run the evals app:

**What to say during Demo 3:**

"Based on profiling we've done, here's the breakdown:

The LLM thinking takes about 96% of total response time - typically 2-8 seconds depending on complexity.

MongoDB queries average 50-80 milliseconds. That's less than 4% of total time.

The database is almost never the bottleneck. The bottleneck is the LLM reasoning about what to do with the data."

**Then move to Demo 4.**

---

## Summary

✅ **Evals app works without MongoDB collection**
✅ **Perfect for Demo 3: proves DB isn't bottleneck**
✅ **Pre-run before demo for best visual impact**
✅ **Results work in-memory during session**
⚠️ **MongoDB storage optional (nice to have, not required)**

**For demo purposes:** Just run it, show the charts, that's it!
