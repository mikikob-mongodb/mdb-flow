# Flow Companion Evals Framework

## Overview

Comprehensive evaluation framework for testing LLM optimization strategies and search mode performance in Flow Companion. Enables systematic comparison of different configurations to measure real-world impact on latency, token usage, and accuracy.

## Architecture

```
evals/
├── configs.py          # Optimization configuration definitions
├── test_suite.py       # 46 test queries across 6 categories
├── result.py           # Pydantic models for test results
├── runner.py           # Multi-config test execution engine
└── storage.py          # MongoDB persistence layer
```

## Test Suite Structure

### Total Tests: 46 queries across 6 sections

#### 1. Slash Commands (Tests 1-10)
Direct database queries that bypass the LLM entirely.

**Examples:**
- `/tasks` - List all tasks
- `/tasks status:in_progress` - Filter by status
- `/tasks priority:high` - Filter by priority
- `/projects` - List all projects
- `/search debugging` - Hybrid search

**Expected Performance:** ~90-100ms
**Optimization Impact:** None (bypasses LLM)

---

#### 2. Text Queries (Tests 11-18)
Natural language queries requiring LLM interpretation.

**Examples:**
- "What tasks do I have?"
- "Show me incomplete tasks"
- "What am I working on?"
- "Find tasks related to debugging"

**Expected Performance:**
- Baseline: 20-30s
- Optimized: 7-15s
**Optimization Impact:** High (50-65% reduction)

---

#### 3. Text Actions (Tests 19-28)
Natural language commands that modify data.

**Examples:**
- "Create a task for testing the new search feature"
- "Mark task X as in progress"
- "Add a note to task Y: Fixed bug"
- "Update priority of task Z to high"

**Expected Performance:**
- Baseline: 15-25s
- Optimized: 8-12s
**Optimization Impact:** High (40-55% reduction)

---

#### 4. Multi-Turn Context (Tests 29-33)
Queries that reference previous conversation context.

**Examples:**
- Turn 1: "What tasks am I working on?"
- Turn 2: "Mark the first one as done"
- Turn 3: "Add a note to it: Completed successfully"

**Expected Performance:**
- Baseline: 25-35s
- Optimized: 10-15s
**Optimization Impact:** Very High (60-70% reduction due to caching)

---

#### 5. Voice Input (Tests 34-40)
Voice commands using Whisper transcription.

**Examples:**
- 🎤 "Create a task for debugging"
- 🎤 "What tasks are in progress?"
- 🎤 "Mark the authentication task as done"

**Expected Performance:**
- Baseline: 22-32s (includes Whisper transcription ~2s)
- Optimized: 9-16s
**Optimization Impact:** High (similar to text queries)

**Note:** Voice tests currently not fully implemented in test suite.

---

#### 6. Search Mode Variants (Tests 41-46)
Compare hybrid, vector-only, and text-only search performance.

**Vector Search Tests (41-43):**
- `/tasks search vector debugging`
- `/tasks search vector memory`
- `/projects search vector agent`

**Text Search Tests (44-46):**
- `/tasks search text debugging`
- `/tasks search text checkpointer`
- `/projects search text AgentOps`

**Expected Performance:**
- Text search: ~180ms (fastest, keyword only)
- Vector search: ~280ms (semantic understanding)
- Hybrid search: ~420ms (best quality, combines both)

**Optimization Impact:** None (all bypass LLM)

---

## Optimization Configurations

### 1. Baseline
No optimizations - establishes performance baseline.

**Settings:**
- Compress tool results: OFF
- Streamlined prompt: OFF
- Prompt caching: OFF

**Use Case:** Baseline for comparison

---

### 2. Compress
Tool result compression only.

**Settings:**
- Compress tool results: ON
- Streamlined prompt: OFF
- Prompt caching: OFF

**Impact:** ~20-25% latency reduction
**Best For:** Large result sets, list operations

---

### 3. Streamlined
Streamlined system prompt only.

**Settings:**
- Compress tool results: OFF
- Streamlined prompt: ON
- Prompt caching: OFF

**Impact:** ~30-35% latency reduction
**Best For:** Simple queries with clear intent

---

### 4. Caching
Prompt caching only.

**Settings:**
- Compress tool results: OFF
- Streamlined prompt: OFF
- Prompt caching: ON

**Impact:** ~40-50% latency reduction (after cache warm-up)
**Best For:** Multi-turn conversations, repeated queries

---

### 5. All Context Engineering
All optimizations combined.

**Settings:**
- Compress tool results: ON
- Streamlined prompt: ON
- Prompt caching: ON

**Impact:** ~50-65% latency reduction
**Best For:** Production use, maximum performance

---

## Running Evals

### Starting the Dashboard

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Run evals dashboard
streamlit run evals_app.py --server.port 8502
```

The dashboard opens at `http://localhost:8502`

---

### Running a Comparison

1. **Select Configurations**
   - Check boxes for 2+ configs (e.g., "Baseline" + "All Context Engineering")
   - Select at least one to enable "Run Comparison" button

2. **Click "Run Comparison"**
   - Tests execute in sequence for each config
   - Progress bar shows execution status
   - Takes ~5-10 minutes for full 46-test suite

3. **View Results**
   - **Summary Section**: Average metrics across all tests
   - **Comparison Matrix**: Test-by-test breakdown with best config highlighted
   - **Impact Analysis**: 5 interactive charts showing optimization impact

4. **Export Results** (Optional)
   - Click "Export Results to JSON"
   - Download results for presentations/reports

---

## Dashboard Sections

### 1. Summary Metrics

High-level comparison across all selected configs:

- **Average Latency** - Mean response time
- **Total Tokens** - Combined input + output tokens
- **Cache Hits** - Number of prompt cache hits (if caching enabled)
- **Accuracy** - Percentage of successful test completions

**Key Insights:**
- Compare baseline vs optimized latency
- Identify most effective optimization strategy
- Track token usage for cost analysis

---

### 2. Comparison Matrix

Test-by-test breakdown showing:

- **Test ID & Description** - What's being tested
- **Intent Group** - Category (slash, text query, action, etc.)
- **Latency per Config** - Response time for each config
- **Best Config** - Fastest configuration (or "⚡ Direct DB" for slash commands)

**Visual Indicators:**
- 🟢 Green highlighting: Best performing config
- Gray italic `*90ms*`: Slash commands (optimization not applicable)
- Color coding: Faster (green) to slower (red)

**Sorting:**
- Click column headers to sort
- Default: Sorted by test ID

---

### 3. Impact Analysis Charts

#### Chart 1: Optimization Waterfall
Shows progressive impact of stacked optimizations on LLM queries only.

**Excludes:** Slash commands (they bypass LLM)
**Shows:** Base → Compress → Streamlined → Caching → All

**Typical Pattern:**
- Baseline: 20-30s
- Compress: 15-22s (-24%)
- Streamlined: 13-19s (-35%)
- Caching: 10-15s (-50%)
- All Context: 7-12s (-64%)

---

#### Chart 2: LLM vs MongoDB Time Breakdown
Pie chart showing where time is spent during query execution.

**Categories:**
- 🧠 LLM Thinking: Claude API response time
- 🍃 MongoDB Execution: Database query time

**Key Insight:**
- LLM: ~96% of total time
- MongoDB: ~4% of total time
- **Conclusion:** MongoDB is fast! Optimize LLM, not DB.

---

#### Chart 3: Search Mode Comparison
Compares performance of hybrid, vector, and text search modes.

**Shows:**
- Hybrid (Default): ~420ms
- Vector Only: ~280ms (33% faster than hybrid)
- Text Only: ~180ms (57% faster than hybrid)

**Key Insight:**
- 2.3x performance difference between fastest (text) and slowest (hybrid)
- Quality vs speed tradeoff: Text is fast but keyword-only, Hybrid is comprehensive but slower

---

#### Chart 4: Token Usage by Config
Bar chart showing total tokens (input + output) per configuration.

**Key Insight:**
- Streamlined prompt reduces input tokens by ~60%
- Compression reduces output tokens by ~60-70% for large results
- Combined effect: Significant token reduction = cost savings

---

#### Chart 5: Cache Hit Rate
Shows cache hit percentage for configurations with prompt caching enabled.

**Key Insight:**
- First query: Cache MISS (builds cache)
- Subsequent queries within 5 min: Cache HIT (~50% latency reduction)
- Multi-turn conversations benefit most from caching

---

## Storage & History

### MongoDB Persistence

Comparison results are stored in MongoDB for historical analysis:

```python
# Collection: eval_results
{
  "comparison_id": "2026-01-06_14-30-15",
  "timestamp": datetime,
  "configs": ["baseline", "all_context"],
  "results": {
    "baseline": [TestResult, ...],
    "all_context": [TestResult, ...]
  },
  "summary": {
    "avg_latency": {...},
    "total_tokens": {...},
    ...
  }
}
```

### Loading Previous Results

1. Select "Load Previous Results" in dashboard
2. Choose comparison run from dropdown
3. View historical data without re-running tests

---

## Expected Results

### Slash Commands
- **Latency:** 80-120ms (varies by DB load)
- **Optimization Impact:** None (bypasses LLM)
- **Variation:** ±20ms (MongoDB network/query noise)

### Text Queries
- **Baseline:** 20-30s
- **All Optimizations:** 7-15s
- **Improvement:** 50-65% reduction
- **Key Driver:** LLM thinking time reduction

### Text Actions
- **Baseline:** 15-25s
- **All Optimizations:** 8-12s
- **Improvement:** 40-55% reduction
- **Key Driver:** Streamlined prompt + compression

### Multi-Turn Context
- **Baseline:** 25-35s
- **All Optimizations:** 10-15s
- **Improvement:** 60-70% reduction
- **Key Driver:** Prompt caching (warm cache)

### Search Mode Variants
- **Text Search:** 180ms (keyword matching)
- **Vector Search:** 280ms (semantic, requires embedding)
- **Hybrid Search:** 420ms (combines both with $rankFusion)
- **Optimization Impact:** None (all bypass LLM)

---

## Key Insights from Evals

### 1. Slash vs Text Tradeoff
- **Slash commands:** 42x faster (~100ms vs ~7s)
- **Limitation:** Predefined syntax only
- **Benefit:** No LLM interpretation needed
- **Use Case:** Power users, frequent operations

### 2. Optimization Impact on LLM Queries
- **Context engineering:** 50-65% latency reduction
- **Combination works best:** All optimizations stack effectively
- **No silver bullet:** Each optimization contributes 20-35%

### 3. MongoDB Performance
- **Only 4% of total time** - already fast!
- **Don't optimize prematurely** - focus on LLM bottleneck
- **Network noise:** ±20ms variation is normal

### 4. Search Mode Tradeoffs
- **Text search:** Fastest (180ms) but keyword-only
- **Vector search:** Medium speed (280ms), semantic understanding
- **Hybrid search:** Slowest (420ms), best quality
- **Choose based on use case:** Speed vs comprehensiveness

### 5. Prompt Caching ROI
- **First query:** No benefit (builds cache)
- **Subsequent queries:** 40-50% faster
- **Best for:** Multi-turn conversations, repeated patterns
- **Cache TTL:** 5 minutes

### 6. Token Usage & Cost
- **Streamlined prompt:** 60% fewer input tokens
- **Compression:** 60-70% fewer output tokens
- **Cost impact:** Significant savings at scale
- **Cache hits:** Count as reduced-price tokens

---

## Troubleshooting

### Tests Taking Too Long
- **Expected:** 5-10 minutes for full 46-test suite
- **If longer:** Check MongoDB connection, API keys
- **Optimization:** Run fewer configs at once

### Unexpected Latency Spikes
- **Cause:** API rate limiting, network issues
- **Solution:** Wait and re-run, check API status
- **Variation:** ±20-30% is normal for LLM calls

### Cache Not Hitting
- **Cause:** Cache TTL expired (5 minutes)
- **Solution:** Run tests in quick succession
- **Verify:** Check debug output for "cache_read_tokens"

### Slash Commands Slower Than Expected
- **Normal range:** 80-120ms
- **If >200ms:** Check MongoDB Atlas region, network latency
- **Variation:** Load-dependent, not a bug

### Missing Test Results
- **Cause:** Test execution error
- **Check:** Dashboard logs, MongoDB connection
- **Solution:** Re-run comparison, verify test suite IDs

---

## Best Practices

### Running Comparisons
1. **Baseline first:** Always include baseline for reference
2. **Incremental testing:** Test one optimization at a time to isolate impact
3. **Combined testing:** Run "All Context" to see cumulative effect
4. **Multiple runs:** Run 2-3 times and average for stability

### Interpreting Results
1. **Focus on trends:** Look for consistent patterns across tests
2. **Ignore outliers:** Single slow tests may be network noise
3. **Context matters:** Multi-turn tests show caching benefits best
4. **Slash ≠ LLM:** Don't expect optimization impact on slash commands

### Using for Demos
1. **Pre-run tests:** Have fresh data ready before presenting
2. **Export JSON:** Backup results for offline analysis
3. **Highlight key charts:** Optimization Waterfall, LLM vs MongoDB breakdown
4. **Tell the story:** Speed vs flexibility, optimization ROI, tradeoffs

---

## Development

### Adding New Tests

Edit `evals/test_suite.py`:

```python
TestQuery(
    id=47,
    description="New test description",
    query_text="/tasks status:done",
    intent_group="Slash Commands",
    expected_behavior="Should list all completed tasks",
    is_voice=False
)
```

### Adding New Configs

Edit `evals/configs.py`:

```python
EvalConfig(
    id="new_config",
    name="New Configuration",
    description="Description of what this config tests",
    compress_tool_results=True,
    use_streamlined_prompt=False,
    use_prompt_caching=True
)
```

### Modifying Charts

Edit `evals_app.py` chart rendering functions:

```python
def render_new_chart(results: ComparisonResults):
    # Create Plotly figure
    fig = go.Figure(...)
    st.plotly_chart(fig, use_container_width=True)
```

---

## Future Enhancements

### Planned Features
- [ ] Automated pass/fail checking (accuracy scoring)
- [ ] Regression detection (alert if performance degrades)
- [ ] Cost tracking (token usage → API cost calculation)
- [ ] A/B testing framework for prompt variants
- [ ] Automated nightly eval runs
- [ ] Export to CSV for external analysis
- [ ] Compare multiple runs over time (trend analysis)
- [ ] Custom test suite builder (UI for creating tests)

### Potential Improvements
- [ ] Parallel test execution (faster runs)
- [ ] Real-time results streaming (watch tests execute)
- [ ] Statistical significance testing
- [ ] Confidence intervals for latency measurements
- [ ] Integration with CI/CD pipeline
- [ ] Slack/email notifications for regression alerts

---

## Resources

### Documentation
- Main README: `/README.md`
- Architecture: `/docs/ARCHITECTURE.md`
- Slash Commands: `/docs/SLASH_COMMANDS.md`

### Related Files
- Main App: `ui/streamlit_app.py` (port 8501)
- Evals Dashboard: `evals_app.py` (port 8502)
- Test Suite: `evals/test_suite.py`
- Config Definitions: `evals/configs.py`

### External References
- [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [MongoDB Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [Voyage AI Embeddings](https://docs.voyageai.com/docs/embeddings)

---

## Contact & Support

For questions or issues with the evals framework:
- Open an issue in the repository
- Check the troubleshooting section above
- Review test suite and config definitions

---

**Last Updated:** January 6, 2026
**Version:** 3.1.10
**Test Count:** 46 queries across 6 sections
