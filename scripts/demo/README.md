# Flow Companion — Demo Data Guide

This document describes the demo dataset and how to seed it for testing and presentations.

---

## Loading Demo Data

The demo data loader creates a realistic, interconnected dataset specifically designed for Flow Companion demos and presentations. It includes projects, tasks, and all 5 memory types.

### Quick Start

```bash
# First-time setup (includes demo data)
python scripts/setup/setup.py

# Reset demo data before a presentation
python scripts/demo/reset_demo.py

# Just verify demo data exists
python scripts/demo/seed_demo_data.py --verify
```

---

## What Gets Created

The demo dataset is carefully crafted to showcase Flow Companion's memory system and capabilities.

| Type | Count | Description |
|------|-------|-------------|
| **Projects** | 3 | Realistic projects with varied statuses |
| **Tasks** | 7 | Mix of todo, in_progress, and done |
| **Procedural Memory** | 2 | GTM Template + Due Diligence Checklist |
| **Semantic Memory** | 4 | User preferences and rules |
| **Episodic Memory** | 9 | Past actions with timestamps |
| **Embeddings** | ~8 | Vector embeddings for semantic search |

---

## Demo Projects

### 1. Project Alpha (Active)
**Status:** Active
**Tasks:** 7 (2 done, 1 in progress, 4 todo)
**Description:** Enterprise infrastructure modernization project

**Tasks:**
- ✅ Review infrastructure audit report
- ✅ Schedule stakeholder alignment meeting
- 🔄 Draft migration timeline (in progress)
- ⬜ Identify vendor dependencies
- ⬜ Cost-benefit analysis
- ⬜ Security compliance review
- ⬜ Draft communication plan

### 2. Q3 Fintech GTM (Completed)
**Status:** Completed
**Description:** Go-to-market strategy for fintech vertical

### 3. AI Developer Outreach (Completed)
**Status:** Completed
**Description:** Developer relations and community building

---

## Memory System Demo Data

### Procedural Memory (Templates & Checklists)

**1. GTM Roadmap Template**
- 6-phase go-to-market template
- Includes: Market Research, Positioning, Collateral, Channel Strategy, Launch Plan, Post-Launch

**2. Market Research Questions**
- Due diligence checklist
- 10 standard questions for market validation

### Semantic Memory (User Preferences)

- `default_priority = high` - Default task priority
- `communication_style = concise` - Preferred communication style
- `focus_area = AI and developer tools` - Current focus area
- `work_style = strategic planning` - Working style preference

### Episodic Memory (Past Actions)

9 timestamped events showing:
- 3 project creations (Oct 2025)
- 3 template applications (Sep 2025)
- 3 project completions (Nov 2025)

All events are backdated to create a realistic timeline.

---

## Seeding Options

### Full Reset (Recommended for Demos)

```bash
# Complete teardown → setup → verify cycle
python scripts/demo/reset_demo.py

# What it does:
# 1. Clears all demo collections
# 2. Re-seeds all data
# 3. Verifies everything is correct
```

### Partial Seeding

```bash
# Seed without clearing (idempotent)
python scripts/demo/seed_demo_data.py

# Clear and re-seed
python scripts/demo/seed_demo_data.py --clean

# Skip embeddings (faster, but search won't work)
python scripts/demo/seed_demo_data.py --skip-embeddings

# Just verify data exists
python scripts/demo/seed_demo_data.py --verify
```

### Programmatic Usage

```python
from scripts.demo import seed_demo_data

# Seed all data
results = seed_demo_data.seed_all(db, clean=True, skip_embeddings=False)

# Clear collections
counts = seed_demo_data.clear_collections(db)

# Verify seed data
verification = seed_demo_data.verify_seed(db)
if verification["success"]:
    print("All critical data exists")
```

---

## Demo Test Queries

Once data is seeded, test these queries in the Streamlit app:

### Slash Commands (Direct MongoDB)

```
/tasks
/tasks status:in_progress
/projects
/search Project Alpha
```

**Expected:** Sub-200ms response times

### Natural Language Queries

```
What was completed on Project Alpha?
What should I work on next?
Show me high priority tasks
```

**Expected:** LLM-powered responses with tool calling

### Memory System Tests

```
I'm focusing on Project Alpha
→ (Stores semantic memory preference)

What should I work on next?
→ (Uses stored preference to filter suggestions)

What did I complete recently?
→ (Retrieves episodic memory)
```

---

## Verification

After seeding, verify the data:

```bash
# Verify complete setup
python scripts/setup/verify_setup.py

# Verify just the demo data
python scripts/demo/seed_demo_data.py --verify
```

**Expected output:**
```
✅ Projects: 3
✅ Tasks: 7
✅ Procedural Memory: 2
✅ Semantic Memory: 4
✅ Episodic Memory: 9
```

---

## Troubleshooting

### No embeddings generated

**Problem:** Search doesn't work
**Cause:** Seeded with `--skip-embeddings`
**Solution:** Re-seed without the flag

```bash
python scripts/demo/seed_demo_data.py --clean
```

### Data already exists

**Problem:** "Skipping existing" messages
**Cause:** Idempotent seeding (won't create duplicates)
**Solution:** Use `--clean` flag to clear first

```bash
python scripts/demo/seed_demo_data.py --clean
```

### MongoDB connection failed

**Problem:** Can't connect to database
**Solution:** Check .env file

```bash
# Verify environment
python scripts/setup/verify_setup.py

# Check specific variables
echo $MONGODB_URI
echo $MONGODB_DATABASE
```

---

## Related Documentation

- [Setup Guide](00-setup.md) - First-time setup
- [Demo Checklist](DEMO_CHECKLIST.md) - Pre-demo preparation
- [Demo Dry Run](09-demo-dry-run.md) - Full demo script
- [Voice Testing](voice-testing.md) - Voice input test scripts

---

## Notes

- All demo data uses `user_id: "demo-user"`
- Timestamps are backdated to create realistic history
- Embeddings are generated for procedural and episodic memory
- Data is idempotent - safe to run multiple times
- Reset script includes safety checks for production databases
