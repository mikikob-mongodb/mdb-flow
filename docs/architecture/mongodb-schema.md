# MongoDB Schema & Architecture

**Last Updated:** January 12, 2026
**Database:** flow_companion
**Collections:** 8
**Indexes:** 68 (⚠️ EXCESSIVE - see analysis below)

---

## Overview

Flow Companion uses MongoDB Atlas as its primary database with a schema designed around:
- Task and project management
- Multi-tier memory system (short-term, long-term, shared)
- MCP tool discovery and learning
- Evaluation tracking

---

## Collections (8)

### 1. `tasks`
**Purpose:** User tasks with activity logging
**Indexes:** 12
**Est. Size:** Small-Medium (100s-1000s of documents per user)

**Schema:**
```javascript
{
  _id: ObjectId,
  user_id: String,           // User identifier
  project_id: ObjectId,      // Reference to project
  title: String,
  description: String,
  status: String,            // "todo", "in_progress", "done"
  priority: String,          // "low", "medium", "high"
  created_at: Date,
  updated_at: Date,
  last_worked_on: Date,
  completed_at: Date,
  activity_log: [{           // Activity history
    timestamp: Date,
    action: String,
    agent: String
  }],
  context: String,           // Additional context
  notes: String,
  embedding: [Float],        // 1024-dim vector (Voyage AI)
  tags: [String]
}
```

**Indexes:**
```
1. _id_                                          (automatic)
2. user_id_1
3. project_id_1
4. status_1
5. priority_1
6. created_at_-1
7. last_worked_on_-1
8. activity_log.timestamp_-1
9. user_id_1_project_id_1                       (compound)
10. project_id_1_status_1                        (compound)
11. status_1_priority_1                          (compound)
12. user_id_1_status_1_priority_1                (compound)
13. title_text_context_text_notes_text           (text search)
```

---

### 2. `projects`
**Purpose:** User projects with activity tracking
**Indexes:** 7
**Est. Size:** Small (10s-100s of documents per user)

**Schema:**
```javascript
{
  _id: ObjectId,
  user_id: String,
  name: String,
  description: String,
  status: String,            // "active", "completed", "archived"
  created_at: Date,
  updated_at: Date,
  last_activity: Date,
  context: String,
  notes: String,
  methods: String,
  decisions: String,
  embedding: [Float],        // 1024-dim vector
  tags: [String]
}
```

**Indexes:**
```
1. _id_                                          (automatic)
2. user_id_1
3. status_1
4. created_at_-1
5. last_activity_-1
6. user_id_1_status_1                           (compound)
7. user_id_1_last_activity_-1                   (compound)
8. name_text                                     (text search on name, description, context, notes, methods, decisions)
```

---

### 3. `settings`
**Purpose:** User settings and current context
**Indexes:** 1
**Est. Size:** Tiny (1 document per user)

**Schema:**
```javascript
{
  _id: ObjectId,
  user_id: String,           // UNIQUE
  current_context: {
    active_project_id: ObjectId,
    focus_mode: Boolean,
    working_hours: String
  },
  preferences: {
    default_priority: String,
    auto_archive: Boolean
  },
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
```
1. _id_                     (automatic)
2. user_id_1                (unique)
```

---

### 4. `short_term_memory`
**Purpose:** Session context with 2-hour TTL
**Indexes:** 6
**Est. Size:** Small (temporary, auto-deleted)

**Schema:**
```javascript
{
  _id: ObjectId,
  session_id: String,
  agent: String,             // "coordinator", "retrieval", "worklog"
  memory_type: String,       // "context", "working"
  content: Object,
  created_at: Date,
  expires_at: Date           // TTL index (2 hours)
}
```

**Indexes:**
```
1. _id_                                (automatic)
2. session_id_1
3. agent_1
4. memory_type_1
5. expires_at_ttl                      (TTL - auto-delete)
6. session_id_1_memory_type_1          (compound)
7. session_id_1_agent_1                (compound)
```

---

### 5. `long_term_memory`
**Purpose:** Persistent memory (episodic, semantic, procedural)
**Indexes:** 15 (⚠️ MOST INDEXES)
**Est. Size:** Medium-Large (grows over time)

**Schema:**
```javascript
{
  _id: ObjectId,
  user_id: String,
  memory_type: String,       // "episodic", "semantic", "procedural"

  // Episodic (events/actions)
  action_type: String,
  timestamp: Date,
  context: Object,
  source_agent: String,

  // Semantic (preferences/facts)
  semantic_type: String,     // "preference", "fact", "rule"
  key: String,
  value: String,

  // Procedural (templates/patterns)
  rule_type: String,
  trigger_pattern: String,
  response_template: String,

  embedding: [Float],        // 1024-dim vector
  created_at: Date
}
```

**Indexes:**
```
1. _id_                                          (automatic)
2. user_id_1
3. memory_type_1
4. timestamp_-1
5. action_type_1
6. source_agent_1
7. semantic_type_1
8. key_1
9. rule_type_1
10. trigger_pattern_1
11. user_id_1_memory_type_1                      (compound)
12. user_id_1_timestamp_-1                       (compound)
13. user_id_1_action_type_1                      (compound)
14. user_id_1_source_agent_1                     (compound)
15. semantic_lookup                              (compound: user_id + memory_type + semantic_type + key)
16. procedural_lookup                            (compound: user_id + memory_type + trigger_pattern)
```

---

### 6. `shared_memory`
**Purpose:** Agent handoffs with 5-minute TTL
**Indexes:** 8
**Est. Size:** Tiny (temporary, auto-deleted)

**Schema:**
```javascript
{
  _id: ObjectId,
  session_id: String,
  from_agent: String,
  to_agent: String,
  handoff_id: String,        // UNIQUE
  chain_id: String,
  status: String,            // "pending", "completed"
  content: Object,
  created_at: Date,
  expires_at: Date           // TTL index (5 minutes)
}
```

**Indexes:**
```
1. _id_                                          (automatic)
2. session_id_1
3. from_agent_1
4. to_agent_1
5. status_1
6. handoff_id_1                                  (unique)
7. chain_id_1
8. expires_at_ttl                                (TTL - auto-delete)
9. session_id_1_to_agent_1_status_1              (compound)
```

---

### 7. `tool_discoveries`
**Purpose:** MCP tool usage learning and reuse
**Indexes:** 8
**Est. Size:** Small-Medium (grows with tool usage)

**Schema:**
```javascript
{
  _id: ObjectId,
  user_id: String,
  user_request: String,
  solution: {
    mcp_server: String,
    tool_used: String,
    parameters: Object
  },
  times_used: Number,
  success: Boolean,
  promoted_to_static: Boolean,
  timestamp: Date,
  request_embedding: [Float]  // 1024-dim vector
}
```

**Indexes:**
```
1. _id_                                          (automatic)
2. user_id_1
3. times_used_-1
4. success_1
5. promoted_to_static_1
6. timestamp_-1
7. promoted_to_static_1_times_used_-1            (compound)
8. mcp_server_1_tool_used_1                      (compound)
9. user_unpromoted_popular                       (compound: user_id + promoted_to_static + times_used)
```

---

### 8. `eval_comparison_runs`
**Purpose:** Evaluation comparison run results
**Indexes:** 2
**Est. Size:** Small (grows with eval runs)

**Schema:**
```javascript
{
  _id: ObjectId,
  run_name: String,
  timestamp: Date,
  results: Object,
  metrics: Object
}
```

**Indexes:**
```
1. _id_                     (automatic)
2. timestamp_-1
3. run_name_1
```

---

## Index Analysis

### Total Index Count
- **Automatic (_id_):** 8 (one per collection)
- **Explicit Indexes:** 60
- **Total:** 68 indexes

### Index Breakdown by Collection
```
Collection              Indexes    % of Total
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
long_term_memory         15         22%
tasks                    12         18%
shared_memory             8         12%
tool_discoveries          8         12%
projects                  7         10%
short_term_memory         6          9%
eval_comparison_runs      2          3%
settings                  1          1%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                    68        100%
```

---

## ⚠️ Index Analysis: EXCESSIVE

### Problem
**68 indexes is EXCESSIVE** for a database of this size. This creates:
- ❌ **Write penalty** - Every insert/update must update multiple indexes
- ❌ **Storage bloat** - Indexes can be larger than the data itself
- ❌ **Memory pressure** - Atlas loads frequently-used indexes into RAM
- ❌ **Maintenance overhead** - More complexity for no benefit

### Root Cause Analysis

Looking at the index definitions in `scripts/setup/init_db.py`, the excessive indexes come from:

**1. Over-indexing in `long_term_memory` (15 indexes)**
- Many single-field indexes that are covered by compound indexes
- Example: `user_id_1` is redundant if we have `user_id_1_memory_type_1`
- Indexes on optional fields (`action_type`, `semantic_type`, `rule_type`) that aren't always present

**2. Compound indexes for rare queries**
- `tasks.user_id_1_status_1_priority_1` - 3-field compound for rare use case
- `shared_memory.session_id_1_to_agent_1_status_1` - complex handoff routing
- These likely have low selectivity and aren't used often

**3. Text indexes with heavy weights**
- `projects.name_text` indexes 6 fields with different weights
- `tasks.title_text_context_text_notes_text` indexes 3 fields
- MongoDB text indexes are expensive

**4. Indexes on low-cardinality fields**
- `tasks.status_1` - only 3 values ("todo", "in_progress", "done")
- `tasks.priority_1` - only 3 values ("low", "medium", "high")
- `shared_memory.status_1` - only 2 values ("pending", "completed")
- Low-cardinality indexes rarely improve performance

---

## Recommended Index Reduction

### Phase 1: Remove Obviously Redundant (Immediate - Safe)

Remove **22 indexes** that are clearly redundant or unnecessary:

**long_term_memory (remove 8):**
```
❌ user_id_1                          → Covered by user_id_1_memory_type_1
❌ memory_type_1                      → Covered by user_id_1_memory_type_1
❌ action_type_1                      → Sparse field, covered by user_id_1_action_type_1
❌ source_agent_1                     → Covered by user_id_1_source_agent_1
❌ semantic_type_1                    → Covered by semantic_lookup
❌ key_1                              → Covered by semantic_lookup
❌ rule_type_1                        → Rarely used
❌ trigger_pattern_1                  → Covered by procedural_lookup
```

**tasks (remove 5):**
```
❌ project_id_1                       → Covered by user_id_1_project_id_1
❌ status_1                           → Low cardinality, covered by compound indexes
❌ priority_1                         → Low cardinality, covered by compound indexes
❌ status_1_priority_1                → Low selectivity compound
❌ user_id_1_status_1_priority_1      → Overly specific, rarely used
```

**projects (remove 2):**
```
❌ status_1                           → Low cardinality
❌ created_at_-1                      → Covered by user_id_1_last_activity_-1 for most queries
```

**short_term_memory (remove 3):**
```
❌ agent_1                            → Covered by session_id_1_agent_1
❌ memory_type_1                      → Covered by session_id_1_memory_type_1
❌ session_id_1_agent_1               → Redundant with session_id_1_memory_type_1
```

**shared_memory (remove 3):**
```
❌ from_agent_1                       → Rarely queried alone
❌ to_agent_1                         → Covered by session_id_1_to_agent_1_status_1
❌ status_1                           → Low cardinality, covered by compound
```

**tool_discoveries (remove 1):**
```
❌ success_1                          → Low cardinality, rarely queried alone
```

**New total: 68 - 22 = 46 indexes** (32% reduction)

---

### Phase 2: Evaluate Text Indexes (Monitor & Decide)

**Consider removing or simplifying:**
- `projects.name_text` - Very expensive (6 fields). Consider single-field or remove entirely if full-text search isn't critical
- `tasks.title_text_context_text_notes_text` - Could simplify to just `title_text`

**Potential savings: 2 text indexes**

---

### Phase 3: Monitor Actual Query Patterns (Data-Driven)

After Phase 1, enable MongoDB slow query logging and monitor for 1-2 weeks:

```javascript
// Enable profiling
db.setProfilingLevel(1, { slowms: 100 })

// Check slow queries after 1 week
db.system.profile.find({ millis: { $gt: 100 } }).sort({ ts: -1 }).limit(20)
```

Remove indexes that:
- Don't appear in query plans
- Have low `nReturned` / `totalKeysExamined` ratio
- Are only used for queries that run <1 time per day

**Potential target: 35-40 total indexes** (40% reduction from current)

---

## Recommended Minimal Index Set

For a production deployment, this is the **essential** set:

### tasks (6 indexes - down from 12)
```
✅ _id_                              (automatic)
✅ user_id_1_project_id_1            (primary query pattern)
✅ project_id_1_status_1             (project task lists)
✅ created_at_-1                     (recent tasks)
✅ last_worked_on_-1                 (active work)
✅ activity_log.timestamp_-1         (activity feed)
✅ title_text                        (simplified text search)
```

### projects (4 indexes - down from 7)
```
✅ _id_                              (automatic)
✅ user_id_1
✅ last_activity_-1                  (recent projects)
✅ user_id_1_status_1                (user project lists)
```

### settings (2 indexes - unchanged)
```
✅ _id_                              (automatic)
✅ user_id_1                         (unique)
```

### short_term_memory (3 indexes - down from 6)
```
✅ _id_                              (automatic)
✅ session_id_1_memory_type_1        (primary query pattern)
✅ expires_at_ttl                    (TTL cleanup)
```

### long_term_memory (7 indexes - down from 15)
```
✅ _id_                              (automatic)
✅ user_id_1_memory_type_1           (primary query pattern)
✅ user_id_1_timestamp_-1            (recent memory)
✅ semantic_lookup                   (semantic memory lookups)
✅ procedural_lookup                 (procedural memory lookups)
✅ timestamp_-1                      (global timeline - consider removing if not needed)
```

### shared_memory (4 indexes - down from 8)
```
✅ _id_                              (automatic)
✅ session_id_1_to_agent_1_status_1  (handoff routing)
✅ handoff_id_1                      (unique lookup)
✅ expires_at_ttl                    (TTL cleanup)
```

### tool_discoveries (5 indexes - down from 8)
```
✅ _id_                              (automatic)
✅ user_id_1
✅ times_used_-1                     (popularity)
✅ timestamp_-1                      (recent discoveries)
✅ user_unpromoted_popular           (candidate promotion)
```

### eval_comparison_runs (3 indexes - unchanged)
```
✅ _id_                              (automatic)
✅ timestamp_-1
✅ run_name_1
```

**Total minimal set: 34 indexes** (50% reduction from current 68)

---

## Vector Search Indexes (Separate)

Vector search indexes are **created manually in Atlas UI** (not via Python driver):

**Required Vector Indexes (4):**
1. `tasks.embedding` - Task semantic search
2. `projects.embedding` - Project semantic search
3. `long_term_memory.embedding` - Memory semantic search
4. `tool_discoveries.request_embedding` - Tool discovery matching

**Configuration (all 4 use same settings):**
```json
{
  "fields": [
    {
      "path": "embedding",
      "type": "vector",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

---

## Implementation Plan

### Step 1: Create Index Cleanup Script
```bash
# Create new script
touch scripts/maintenance/cleanup_indexes.py
```

**Script should:**
1. Connect to MongoDB
2. List all current indexes
3. Drop redundant indexes (from Phase 1 list above)
4. Verify remaining indexes
5. Log changes

### Step 2: Run in Development First
```bash
# Backup first!
mongodump --uri="$MONGODB_URI" --out=backup_before_index_cleanup

# Run cleanup
python scripts/maintenance/cleanup_indexes.py --dry-run  # See what would be removed
python scripts/maintenance/cleanup_indexes.py           # Execute
```

### Step 3: Monitor Performance
- Check query performance before/after
- Look for any queries that got slower
- If needed, add back specific indexes

### Step 4: Update init_db.py
Once confirmed working, update `scripts/setup/init_db.py` to only create the minimal index set.

---

## Storage Impact Estimate

**Current storage (estimated):**
- Data: ~100 MB (assuming 10K tasks, 1K projects, 50K memory entries)
- Indexes: ~150-200 MB (68 indexes, many compound)
- **Total: ~250-300 MB**

**After cleanup (34 indexes):**
- Data: ~100 MB (unchanged)
- Indexes: ~75-100 MB (50% reduction)
- **Total: ~175-200 MB**

**Savings: ~25-33% total storage reduction**

---

## Performance Impact

**Write Performance:**
- Current: Every insert/update touches ~8-12 indexes per collection
- After cleanup: ~4-6 indexes per collection
- **Expected improvement: 30-40% faster writes**

**Query Performance:**
- Well-designed queries: No impact (still using optimal indexes)
- Poorly-designed queries: May get slightly slower (but these should be rewritten anyway)
- **Overall: Neutral to positive**

**Memory Usage:**
- MongoDB loads "working set" of indexes into RAM
- Fewer indexes = more data can stay in RAM
- **Expected improvement: Better cache hit ratio**

---

## Best Practices Going Forward

### Index Design Principles

**1. Start with queries, not schema**
```
❌ DON'T: Create index because field exists
✅ DO: Create index to optimize specific query pattern
```

**2. Compound indexes from left-to-right**
```
❌ WRONG: user_id_1, then user_id_1_status_1 (redundant)
✅ RIGHT: user_id_1_status_1 covers both user_id alone AND user_id+status
```

**3. High-cardinality first in compounds**
```
❌ WRONG: status_1_user_id_1 (status has 3 values)
✅ RIGHT: user_id_1_status_1 (user_id is unique)
```

**4. Avoid indexing low-cardinality fields**
```
❌ WRONG: Index on 'status' (3 values: todo/in_progress/done)
✅ RIGHT: Only index if part of highly selective compound
```

**5. Monitor before adding**
```
1. Identify slow query
2. Use .explain() to see query plan
3. Create index ONLY if it helps that specific query
4. Monitor for 1 week to ensure it's used
```

### Monitoring Commands

```javascript
// Check index sizes
db.tasks.stats().indexSizes

// See which indexes are actually used
db.tasks.aggregate([{ $indexStats: {} }])

// Find unused indexes (requires MongoDB 4.4+)
db.tasks.aggregate([
  { $indexStats: {} },
  { $match: { "accesses.ops": { $lt: 10 } } }
])
```

---

## Summary

**Current State:**
- 8 collections ✅ (appropriate)
- 68 indexes ❌ (excessive - 2-3x more than needed)

**Recommended Action:**
1. **Immediate:** Remove 22 obviously redundant indexes (Phase 1)
2. **Short-term:** Monitor queries and remove 10-12 more (Phase 2-3)
3. **Target:** 34-40 indexes total (50% reduction)

**Expected Benefits:**
- 30-40% faster writes
- 25-33% storage savings
- Better RAM utilization
- Simpler maintenance

**Created:** January 12, 2026
**Next Review:** After index cleanup implementation
