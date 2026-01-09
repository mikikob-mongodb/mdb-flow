# Scripts Directory

Utility scripts for Flow Companion database management, testing, and maintenance.

## Overview

This directory contains consolidated scripts for common operations:
- **setup_database.py** - Database setup (indexes + memory collections)
- **cleanup_database.py** - Database cleanup and maintenance
- **test_memory_system.py** - Memory system testing
- **load_sample_data.py** - Sample projects and tasks loading
- **seed_memory_demo_data.py** - Memory collections seeding (action history, session context)
- **seed_demo_data.py** - ⭐ Presentation-ready demo dataset (complete 5-tier memory showcase)
- **debug/** - Debug and diagnostic scripts

## Database Setup

### setup_database.py

Creates all necessary MongoDB indexes for Flow Companion.

**Usage:**
```bash
# Setup everything (standard + text search + memory indexes)
python scripts/setup_database.py

# Setup standard indexes only (tasks, projects, settings)
python scripts/setup_database.py --standard

# Setup text search indexes only
python scripts/setup_database.py --text

# Setup memory indexes only (short-term, long-term, shared)
python scripts/setup_database.py --memory

# List all existing indexes
python scripts/setup_database.py --list

# Show vector index creation instructions
python scripts/setup_database.py --vector-instructions
```

**What it creates:**

1. **Standard Indexes:**
   - Tasks: project_id, status, created_at, last_worked_on, activity_timestamp, compound indexes
   - Projects: status, created_at, last_activity
   - Settings: user_id (unique)

2. **Text Search Indexes:**
   - Tasks: title (weight 10), context (weight 5), notes (weight 2)
   - Projects: name (weight 10), description (weight 7), context (weight 5), decisions (weight 4), methods (weight 3), notes (weight 2)

3. **Memory Indexes:**
   - short_term_memory: 6 indexes including TTL (2-hour expiration)
   - long_term_memory: 8 indexes including vector search support
   - shared_memory: 9 indexes including TTL (5-minute expiration)

**Vector Search Indexes:**
- Must be created manually in MongoDB Atlas UI
- The script provides detailed instructions
- Required for semantic search to work

## Database Cleanup

### cleanup_database.py

Comprehensive database cleanup for removing test data, duplicates, and orphaned records.

**Usage:**
```bash
# Show current database status
python scripts/cleanup_database.py --status

# Mark test data (safe, doesn't delete)
python scripts/cleanup_database.py --mark

# Delete all marked test data
python scripts/cleanup_database.py --delete

# Mark and delete in one command
python scripts/cleanup_database.py --mark --delete

# Full cleanup (mark + delete + show status)
python scripts/cleanup_database.py --full

# Remove specific duplicates
python scripts/cleanup_database.py --remove-duplicates "Review documentation"

# Remove duplicates in specific project
python scripts/cleanup_database.py --remove-duplicates "Review documentation" --project AgentOps
```

**What it cleans:**

1. **Test Data Patterns:**
   - Tasks/projects starting with "Test"
   - Malformed tasks (starting with -t, -p, --)
   - Common test titles ("Write unit tests", "Review documentation")

2. **Orphaned Records:**
   - Tasks with no project_id
   - Tasks with invalid project_id (project doesn't exist)

3. **Duplicate Records:**
   - Keeps oldest, deletes rest
   - Can filter by title pattern and project

**Safety Features:**
- --mark operation is safe (doesn't delete)
- --full prompts for confirmation
- Shows counts before and after
- Can undo by querying {is_test: true}

## Memory System Testing

### test_memory_system.py

Comprehensive testing for the three-tier agent memory system.

**Usage:**
```bash
# Test all memory systems
python scripts/test_memory_system.py

# Test specific memory type
python scripts/test_memory_system.py --short-term
python scripts/test_memory_system.py --long-term
python scripts/test_memory_system.py --shared

# Test coordinator integration
python scripts/test_memory_system.py --coordinator

# Test all agents have memory access
python scripts/test_memory_system.py --agents

# Test memory performance (latency)
python scripts/test_memory_system.py --performance
```

**What it tests:**

1. **Short-term Memory:**
   - Session context read/write
   - 2-hour TTL expiration
   - Session isolation

2. **Long-term Memory:**
   - Action history recording
   - Vector search with embeddings
   - Access tracking and strength calculation

3. **Shared Memory:**
   - Agent-to-agent handoffs
   - Atomic consumption (can't read twice)
   - 5-minute TTL expiration

4. **Integration:**
   - Coordinator has memory manager
   - All agents have memory access
   - Embedding function configured

5. **Performance:**
   - Read/write latency < 50ms
   - Vector search latency ~300-400ms
   - Total memory overhead < 5%

**Exit Codes:**
- 0: All tests passed
- 1: Some tests failed

## Sample Data Loading

### load_sample_data.py

Loads sample tasks and projects into the database for testing and demos.

**Usage:**
```bash
# Load with embeddings (recommended)
python scripts/load_sample_data.py

# Skip embeddings for faster loading
python scripts/load_sample_data.py --skip-embeddings
```

**Creates:**
- 10 sample projects (AgentOps, Voice Agent, LangGraph, etc.)
- ~44 sample tasks across multiple statuses and priorities
- Realistic activity logs and timestamps
- Embeddings for vector search (1024-dim Voyage AI)

### seed_memory_demo_data.py

Seeds the memory collections with realistic demo data, making the UI demo-ready on first load.

**Usage:**
```bash
# Seed memory only (assumes projects/tasks already loaded)
python scripts/seed_memory_demo_data.py

# Load sample data first, then seed memory
python scripts/seed_memory_demo_data.py --with-sample-data

# Skip embeddings for faster seeding
python scripts/seed_memory_demo_data.py --skip-embeddings

# Seed specific memory types only
python scripts/seed_memory_demo_data.py --short-term-only
python scripts/seed_memory_demo_data.py --long-term-only

# Include handoff examples (future multi-agent support)
python scripts/seed_memory_demo_data.py --include-handoffs
```

**Creates:**

1. **Short-term Memory:**
   - Session context for demo user (current_project, current_task, last_action)
   - User preferences (focus_project, default_priority, auto_timestamp)
   - User-defined rules (always add notes, update context, tag tasks)
   - Sample disambiguation (multiple search results)
   - Agent working memory for retrieval and worklog agents

2. **Long-term Memory:**
   - 40-60 realistic actions over past 7 days
   - Action types: complete, start, create, update, search
   - Realistic timestamps during working hours (9am-6pm weekdays)
   - Embeddings for semantic search
   - Attributed to demo_user

3. **Shared Memory (optional):**
   - Sample handoff chain (coordinator → retrieval → worklog)
   - Demonstrates multi-agent workflow patterns

**Recommended Setup:**
```bash
# Full demo setup
python scripts/load_sample_data.py
python scripts/seed_memory_demo_data.py

# Or combined
python scripts/seed_memory_demo_data.py --with-sample-data
```

### seed_demo_data.py

**⭐ Presentation-Ready Demo Dataset** - Seeds a complete, interconnected dataset specifically designed for presenting the 5-tier memory system.

**Usage:**
```bash
# Seed all demo data (idempotent)
python scripts/seed_demo_data.py

# Clear existing demo data and reseed
python scripts/seed_demo_data.py --clean

# Verify demo data exists
python scripts/seed_demo_data.py --verify

# Skip embeddings for faster seeding
python scripts/seed_demo_data.py --skip-embeddings
```

**Creates:**

1. **Projects (3):**
   - Project Alpha (active) - Infrastructure modernization with 7 tasks
   - Q3 Fintech GTM (completed) - Past successful GTM project
   - AI Developer Outreach (completed) - Another past GTM project

2. **Tasks (7):**
   - All associated with Project Alpha
   - Mix of statuses: 2 done, 1 in_progress, 4 todo
   - Various priorities demonstrating active work

3. **Procedural Memory (2):**
   - **GTM Roadmap Template** (⭐ key for presentation finale) - 12 tasks across 3 phases
   - Market Research Questions checklist - 6 standard due diligence questions

4. **Semantic Memory (4):**
   - User preferences: default_priority, communication_style, focus_area, work_style
   - Varying confidence levels (0.75-0.9) based on usage frequency
   - Times_used tracking (8-25 uses)

5. **Episodic Memory (3):**
   - Created Q3 Fintech GTM using GTM Template (90 days ago)
   - Completed Q3 Fintech GTM successfully (45 days ago)
   - Applied GTM Template to AI Developer Outreach (120 days ago)

**Key Feature:**
The GTM Template is learned from past projects and can be automatically applied to new GTM projects, demonstrating the system's ability to learn and reuse successful patterns.

**Demo User ID:** `demo-user`

**See:** `scripts/README_SEED_DEMO.md` for detailed documentation and presentation flow.

## Debug Scripts

Located in `scripts/debug/`, these are diagnostic tools for development:

### debug_agent.py
Tests agent behavior vs direct database queries.

### test_hybrid_search.py
Test hybrid search directly without the full agent stack.

**Usage:**
```bash
python scripts/debug/test_hybrid_search.py
```

### test_tool_coordinator.py
Test the tool-based coordinator with various queries.

**Usage:**
```bash
python scripts/debug/test_tool_coordinator.py
```

### test_voice_flow.py
Test voice input processing and transcription.

**Usage:**
```bash
python scripts/debug/test_voice_flow.py
```

## Migration Notes

This directory has been reorganized and consolidated:

### Removed (Merged into Consolidated Scripts)

**Cleanup Scripts (3 → 1):**
- ~~cleanup_duplicate_tasks.py~~ → cleanup_database.py --remove-duplicates
- ~~cleanup_test_data.py~~ → cleanup_database.py --mark --delete
- ~~cleanup_test_pollution.py~~ → cleanup_database.py --full

**Memory Test Scripts (3 → 1):**
- ~~test_memory.py~~ → test_memory_system.py
- ~~test_long_term_memory.py~~ → test_memory_system.py --long-term
- ~~test_shared_memory.py~~ → test_memory_system.py --shared

**Setup Scripts (2 → 1):**
- ~~setup_indexes.py~~ → setup_database.py --standard --text
- ~~setup_memory_indexes.py~~ → setup_database.py --memory

### Benefits of Consolidation

1. **Fewer Files**: 8 scripts → 3 scripts (62.5% reduction)
2. **Clear Purpose**: Each script has a single, clear responsibility
3. **Better CLI**: Argparse with --help documentation
4. **Consistent Interface**: All scripts follow similar patterns
5. **Easier Maintenance**: Changes only needed in one place
6. **Better Documentation**: Comprehensive help text built-in

## Quick Reference

### First Time Setup
```bash
# 1. Setup database indexes
python scripts/setup_database.py

# 2. Load sample data (projects and tasks)
python scripts/load_sample_data.py

# 3. Seed memory with demo data (action history, session context)
python scripts/seed_memory_demo_data.py

# 4. Verify everything works
python scripts/test_memory_system.py

# Or combined (steps 2-3)
python scripts/seed_memory_demo_data.py --with-sample-data
```

### Presentation Setup (5-Tier Memory Demo)
```bash
# Complete presentation-ready dataset
python scripts/seed_demo_data.py --clean

# Verify all data loaded correctly
python scripts/seed_demo_data.py --verify

# Launch the UI
streamlit run ui/streamlit_app.py
# Select user: demo-user
```

### Regular Maintenance
```bash
# Check database status
python scripts/cleanup_database.py --status

# Clean up test data
python scripts/cleanup_database.py --full

# List all indexes
python scripts/setup_database.py --list
```

### Development/Debugging
```bash
# Test memory system
python scripts/test_memory_system.py

# Test specific memory type
python scripts/test_memory_system.py --long-term --performance

# Debug hybrid search
python scripts/debug/test_hybrid_search.py

# Debug coordinator
python scripts/debug/test_tool_coordinator.py
```

## Environment Requirements

All scripts require:
- Python 3.9+
- Virtual environment activated
- MongoDB connection (MONGODB_URI in .env)

Some scripts additionally require:
- ANTHROPIC_API_KEY (for coordinator tests)
- VOYAGE_API_KEY (for embedding/vector search tests)
- OPENAI_API_KEY (for voice transcription tests)

## See Also

- **Database Schema**: `shared/models.py`
- **Database Helpers**: `shared/db.py`
- **Memory System**: `memory/` directory
- **Test Suite**: `tests/` directory
- **Documentation**: `docs/` directory
