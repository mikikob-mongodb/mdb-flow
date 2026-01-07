# MongoDB World Talk Demo Script

## Talk Title: Building an AI Agent with MongoDB - Speed vs Flexibility Tradeoffs

---

## Introduction (2 min)

**Opening:**
"Today I'll show you Flow Companion, an AI agent built with Claude and MongoDB that helps developers manage tasks and projects. More importantly, I'll show you the fundamental tradeoffs we discovered and how we measured them."

**Key Question:**
"When building AI agents, you face a critical choice: Do you want speed or flexibility? Let me show you what I mean."

---

## 1. The Fundamental Tradeoff: Speed vs Flexibility (5 min)

### Demo: Slash Commands (Speed)

**Type in main app:**
```
/tasks status:in_progress
```

**Point out:**
- ⚡ Response time: ~85ms
- Direct MongoDB query - bypasses LLM entirely
- Shows results immediately

**Explain:**
"This is fast because we go straight to MongoDB with a predefined query. But there's a catch..."

**Show limitation:**
```
/tasks status:in_progress priority:high project:AgentOps
```

**Point out:**
"Slash commands only support specific, predefined filters. What if the user asks something slightly different?"

---

### Demo: Text Queries (Flexibility)

**Type in main app:**
```
What tasks am I currently working on?
```

**Point out:**
- 🤖 Response time: ~7.2s (with optimizations)
- LLM interprets natural language
- Generates appropriate MongoDB queries
- Shows results

**Show the power:**
```
Show me high priority tasks for AgentOps that I'm working on
```

**Explain:**
"Same information, completely different phrasing. The LLM understands intent and generates the right query. But it's **42x slower**."

**Key Insight:**
> "This is the core tradeoff: slash commands are 42x faster but limited to predefined patterns. Text queries are infinitely flexible but require LLM thinking time."

---

## 2. Measuring Optimization Impact with Evals (5 min)

### Switch to Evals Dashboard (localhost:8502)

**Explain the framework:**
"We built an evaluation framework to measure optimization strategies across 46 different queries. Let me show you what we learned."

---

### Show: Comparison Matrix

**Point out the key patterns:**

1. **Slash Commands (gray italic with asterisks):**
   - All optimizations show: `*90ms*`, `*88ms*`, `*86ms*`
   - "Best" column shows: "⚡ Direct DB"
   - Explain: "See the asterisks? These values are gray and italic because optimizations don't apply - slash commands bypass the LLM entirely. The variation is just MongoDB noise."

2. **Text Queries:**
   - Base: 20.1s
   - Compress: 15.2s
   - All Context: 7.2s
   - **Improvement: -64%**
   - Explain: "For text queries, context optimizations cut latency by 50-65%!"

**Key Insight:**
> "Optimizations only help when you're using the LLM. Direct database operations are already fast."

---

### Show: Optimization Waterfall

**Point out:**
- Chart excludes slash commands
- Shows progression: 20s → 15s → 10s → 7s
- Each optimization stacks on previous ones

**Explain:**
"This waterfall shows the *true* impact of optimizations on LLM queries. We exclude slash commands because they don't benefit from LLM optimizations."

**Key Numbers:**
- Compress: -24% (removes markdown formatting)
- Streamlined: -35% (removes redundant context)
- Caching: -50% (caches tool definitions)
- All Context: -64% (combines all strategies)

---

### Show: LLM vs MongoDB Time Breakdown

**Point out the pie chart:**
- 🧠 LLM Thinking: 96% of time
- 🍃 MongoDB Execution: 4% of time

**Explain:**
"MongoDB is incredibly fast! In our agent, MongoDB operations take only 4% of the total time. The bottleneck is LLM thinking time, which is why our optimizations focus there."

**Key Insight:**
> "Don't optimize what isn't slow. MongoDB was already performant - we focused on reducing LLM latency."

---

## 3. Search Mode Tradeoffs: Quality vs Performance (4 min)

### Explain the context:

"Even within MongoDB queries, there are tradeoffs. We implemented three search modes using different MongoDB features. Let's compare them."

---

### Show: Search Mode Comparison Chart (Evals Dashboard)

**Point out the three bars:**
1. **Hybrid Search (Default): ~420ms**
   - Uses `$rankFusion` to combine vector + text search
   - Best quality - finds both semantic and keyword matches
   - Slowest

2. **Vector Search: ~280ms**
   - Uses `$vectorSearch` with Voyage embeddings
   - Good for conceptual queries
   - Medium speed

3. **Text Search: ~180ms**
   - Uses MongoDB text index
   - Fast keyword matching only
   - 57% faster than hybrid, but less comprehensive

**Explain:**
"All three use MongoDB, but the approach changes performance by 2.3x. Quality vs speed - you choose based on your use case."

---

### Demo: Live Search Comparison (Switch to Main App)

**Type each command and show debug panel:**

```
/search debugging
```
**Show debug panel:**
- Search Mode: 🔄 Hybrid (Default)
- Latency: ~420ms
- Breakdown: Embedding 200ms + $rankFusion 220ms

```
/search vector debugging
```
**Show debug panel:**
- Search Mode: 🧠 Vector Only (Semantic)
- Latency: ~280ms
- Breakdown: Embedding 200ms + $vectorSearch 80ms

```
/search text debugging
```
**Show debug panel:**
- Search Mode: 🔤 Text Only (Keyword)
- Latency: ~180ms
- Breakdown: $search (text index) 180ms

**Explain the results:**
"Notice how the results differ slightly? Hybrid gives the most comprehensive results. Vector finds semantically similar items. Text is fastest but only matches keywords exactly."

**Key Insight:**
> "Even with the same database, architectural choices create performance tradeoffs. MongoDB gives you the flexibility to choose based on your needs."

---

## 4. Practical Takeaways (3 min)

### Summary of Findings

**1. Speed vs Flexibility**
- Direct DB queries: ~100ms, limited to predefined operations
- LLM + DB queries: ~7s, unlimited flexibility
- **Choose based on use case, not ideology**

**2. Optimization Focus**
- Identify the bottleneck first (for us: LLM thinking, not DB)
- Our optimizations cut LLM latency by 50-65%
- MongoDB was already fast at 4% of total time

**3. Search Architecture**
- Hybrid: Best quality (~420ms)
- Vector: Semantic understanding (~280ms)
- Text: Fastest keyword matching (~180ms)
- **2.3x performance range within MongoDB**

**4. Measurement is Critical**
- Built 46-query eval suite to measure objectively
- Visual dashboard shows tradeoffs clearly
- Can't optimize what you don't measure

---

### Architecture Highlights

**What makes this work:**

1. **MongoDB's Flexibility**
   - Vector search for semantic understanding
   - Text indexes for keyword matching
   - $rankFusion for hybrid approaches
   - Fast enough for real-time agent interactions

2. **Structured Evaluation**
   - Automated test suite runs same queries across configs
   - Comparison matrix shows patterns
   - Impact charts quantify improvements

3. **Transparent Tradeoffs**
   - Users can choose slash (fast) vs text (flexible)
   - Users can choose search mode (quality vs speed)
   - Debug panel shows exactly where time is spent

---

## Q&A Preparation

### Expected Questions

**Q: Why not cache everything and make text queries fast?**
A: "Caching helps (we got 50% reduction), but natural language has infinite variations. 'Tasks I'm working on' vs 'My current tasks' vs 'What am I doing' - all need LLM interpretation. Slash commands work because the syntax is fixed."

**Q: Could you use a faster LLM?**
A: "Absolutely! We use Claude Sonnet for quality. You could use Haiku for 3-5x speedup at the cost of some accuracy. Again - tradeoffs based on your use case."

**Q: Why not use MongoDB aggregation for everything?**
A: "For predefined queries, we do! That's what slash commands are. But aggregation pipelines require knowing the structure upfront. LLM adds the ability to interpret arbitrary natural language."

**Q: How do you handle hallucinations?**
A: "The LLM only generates queries - it doesn't make up data. We validate query structure before execution. MongoDB returns real data, which prevents hallucinated results."

**Q: What's the user preference - slash or text?**
A: "Power users love slash commands for frequent operations. New users prefer text for discoverability. We provide both and let usage patterns emerge."

---

## Demo Checklist

### Before Talk:
- [ ] Verify main app running on localhost:8501
- [ ] Verify evals dashboard running on localhost:8502
- [ ] Clear any previous query history for clean demo
- [ ] Run evals comparison to have fresh data loaded
- [ ] Test all demo queries to ensure they work
- [ ] Ensure debug panel is visible in main app
- [ ] Bookmark key dashboard views for quick navigation

### During Demo:
- [ ] Start with simple slash command to show speed
- [ ] Follow with text query to show flexibility
- [ ] Show evals dashboard comparison matrix
- [ ] Show optimization waterfall chart
- [ ] Show LLM vs MongoDB breakdown
- [ ] Show search mode comparison
- [ ] Demo live search variants with debug panel
- [ ] Emphasize: measure, identify bottlenecks, optimize intentionally

### Backup Plans:
- Screenshots of key dashboard views (if live demo fails)
- Pre-recorded video of search mode comparison
- Static data export showing performance numbers

---

## Key Messages to Emphasize

1. **"Tradeoffs are real - embrace them, don't fight them"**
   - Speed vs flexibility is fundamental, not a bug
   - Choose based on use case, not dogma

2. **"Measure before optimizing"**
   - We found MongoDB was 4% of time - didn't need optimization
   - LLM was 96% - that's where we focused

3. **"MongoDB's flexibility enables agent architectures"**
   - Vector search for AI/semantic queries
   - Text indexes for keyword search
   - $rankFusion for hybrid approaches
   - Fast enough for real-time interactions

4. **"Users don't care about technology - they care about results"**
   - Provide both fast (slash) and flexible (text) options
   - Let users choose based on their workflow
   - Transparency builds trust (debug panel shows what's happening)

---

## Timing Breakdown (20 min total)

- Introduction: 2 min
- Speed vs Flexibility Demo: 5 min
- Evals Dashboard Walkthrough: 5 min
- Search Mode Comparison: 4 min
- Practical Takeaways: 3 min
- Q&A: 1 min buffer

Total: 19 minutes (1 min buffer for technical issues)
