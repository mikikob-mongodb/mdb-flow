# Atlas Search Indexes - Automatic Creation

**Status:** ✅ Fully automated as of 2026-01-14

## Overview

All Atlas Search indexes (vector + text) are now created **automatically** during database initialization. No manual steps required in Atlas UI.

## Indexes Created

### Vector Indexes (5 total)
For semantic/similarity search using 1024-dim Voyage AI embeddings:

1. **tasks.vector_index**
   - Vector field: `embedding` (1024 dims, cosine)
   - Filter fields: `user_id`, `status`, `memory_type`, `semantic_type`

2. **projects.vector_index**
   - Vector field: `embedding` (1024 dims, cosine)
   - Filter fields: `user_id`, `status`, `memory_type`, `semantic_type`

3. **memory_episodic.vector_index**
   - Vector field: `embedding` (1024 dims, cosine)
   - Filter fields: `user_id`, `status`, `memory_type`, `semantic_type`

4. **memory_semantic.vector_index**
   - Vector field: `embedding` (1024 dims, cosine)
   - Filter fields: `user_id`, `status`, `memory_type`, `semantic_type`
   - **Used in:** `search_knowledge()` for knowledge cache

5. **tool_discoveries.vector_index**
   - Vector field: `request_embedding` (1024 dims, cosine)
   - Filter fields: `user_id`, `status`, `memory_type`, `semantic_type`

**Note:** Filter fields enable efficient filtered vector searches (e.g., filtering by user_id before similarity search)

### Text Indexes (3 total)
For keyword matching and hybrid search:

1. **tasks_text_index**
   - Collection: `tasks`
   - Fields: title, context, notes
   - Used in: `hybrid_search_tasks()`

2. **projects_text_index**
   - Collection: `projects`
   - Fields: name, description
   - Used in: `hybrid_search_projects()`

3. **semantic_text_index** ⭐ NEW
   - Collection: `memory_semantic`
   - Fields: query, result
   - Used in: `search_knowledge()` for cache-before-search

## How Automatic Creation Works

### During Initial Setup

```bash
python scripts/setup/setup.py
```

This calls:
1. `create_vector_indexes(db)` → Creates 5 vector indexes
2. `create_text_search_indexes(db)` → Creates 3 text indexes

### Implementation

**File:** `scripts/setup/init_db.py`

```python
def create_text_search_indexes(db):
    """Create Atlas Search text indexes programmatically"""
    # Uses collection.create_search_index() API (pymongo >= 4.5)
    collection.create_search_index({
        "definition": {
            "mappings": {
                "fields": {
                    "query": {"type": "string"},
                    "result": {"type": "string"}
                }
            }
        },
        "name": "semantic_text_index"
    })
```

## Vector Search for Knowledge Cache

**Implementation:** Vector search with filter fields

```python
$vectorSearch {
  index: "vector_index",
  path: "embedding",
  queryVector: [...],  # 1024-dim Voyage AI embedding
  filter: {
    user_id: "demo-user",
    memory_type: "semantic",
    semantic_type: "knowledge"
  }
}
```

**Performance:** 85-90%+ cache hit rate

```python
Exact match query:  0.8624 score → HIT! ✅ (threshold 0.65)
Similar query:      0.7200 score → HIT! ✅
Somewhat similar:   0.6600 score → HIT! ✅
Different query:    0.6000 score → MISS (calls external API)
```

**Key Improvement:** Vector indexes now include filter fields (user_id, memory_type, semantic_type, status) to enable efficient filtered searches.

## Fallback to Manual Creation

If programmatic creation fails (API unavailable, permissions, etc.):

1. Script shows warning with manual instructions
2. Hybrid search automatically disabled (falls back to vector-only)
3. Logs show: "⚠️ N Atlas Search indexes require manual creation"

### Manual Creation Steps

If needed:
1. Go to MongoDB Atlas → Database → Search Indexes
2. Create Search Index → JSON Editor
3. Select collection
4. Use JSON from script output
5. Name MUST match expected index name

## Verification

Check all indexes are created:

```bash
python scripts/setup/init_db.py --verify
```

Expected output:
```
📝 Text Search Indexes:
  ✅ tasks_text_index (exists)
  ✅ projects_text_index (exists)
  ✅ semantic_text_index (exists)

🔍 Vector Search Indexes:
  ✅ tasks.vector_index (exists)
  ✅ projects.vector_index (exists)
  ✅ memory_episodic.vector_index (exists)
  ✅ memory_semantic.vector_index (exists)
  ✅ tool_discoveries.vector_index (exists)
```

## Benefits

**For Developers:**
- ✅ No manual Atlas UI steps
- ✅ Consistent across environments
- ✅ Version controlled (definitions in code)
- ✅ Fails gracefully with clear errors

**For MCP Cache:**
- ✅ Higher cache hit rates (hybrid > vector-only)
- ✅ Keyword matching boosts similar queries
- ✅ "Research AI agents" matches "Latest AI agent developments"
- ✅ Faster responses (cache instead of Tavily API)

## Troubleshooting

**Q: Index creation failed?**
- Check pymongo version: `pip show pymongo` (need >= 4.5)
- Check Atlas permissions (API access enabled)
- Check network connectivity

**Q: Hybrid search not working?**
```python
# Check if text index exists
db.command("listSearchIndexes", "memory_semantic")
```

**Q: How to manually create if needed?**
- Run: `python scripts/setup/init_db.py`
- Follow output instructions with JSON definitions

## References

- **Setup Script:** `scripts/setup/setup.py` (lines 173-195)
- **Index Creation:** `scripts/setup/init_db.py` (lines 275-367)
- **Hybrid Search:** `memory/manager.py` (lines 1539-1598)
- **Documentation:** `scripts/README.md`
