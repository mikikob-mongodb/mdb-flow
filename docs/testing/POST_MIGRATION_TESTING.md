# TODO List - Application Testing & Verification
**For**: January 14, 2026 (Tomorrow)
**Branch**: demo-stabilization
**Context**: Memory collection migration completed - need to verify app works end-to-end

---

## 🎯 Primary Goal
Verify the application works correctly with the new memory architecture across all components.

---

## ✅ Pre-Flight Checklist (Do First)

### 1. Verify Git Status
```bash
cd /Users/mikiko.b/Github/mdb-flow
git status
git log --oneline -5
```
**Expected**: Should be on demo-stabilization branch, commits eaf3d61 visible

### 2. Verify Database State
```bash
venv/bin/python scripts/setup/verify_setup.py
```
**Expected**:
- ✅ All 6 collections exist (tasks, projects, memory_episodic, memory_semantic, memory_procedural, tool_discoveries)
- ❌ memory_short_term, memory_long_term, memory_shared should NOT exist

### 3. Check Environment Variables
```bash
cat .env | grep MONGODB
```
**Expected**:
- MONGODB_URI should be set
- MONGODB_DATABASE should be "flow_companion" or your DB name

---

## 🧪 Testing Plan (In Order)

### Phase 1: Database & Setup (15 min)

#### Test 1.1: Database Collections
```bash
# Verify collections exist
venv/bin/python -c "
from shared.db import MongoDB
db = MongoDB().get_database()
collections = db.list_collection_names()
print('Collections:', collections)
print('✅ memory_episodic' if 'memory_episodic' in collections else '❌ memory_episodic missing')
print('✅ memory_semantic' if 'memory_semantic' in collections else '⚠️  memory_semantic (will be created on first use)')
print('✅ memory_procedural' if 'memory_procedural' in collections else '❌ memory_procedural missing')
print('❌ OLD FOUND' if any(c in collections for c in ['memory_short_term', 'memory_long_term', 'memory_shared']) else '✅ Old collections removed')
"
```

**Expected Outcome**:
- ✅ memory_episodic exists
- ✅ memory_procedural exists
- ⚠️  memory_semantic might not exist yet (created on first use)
- ✅ Old collections NOT present

**If Failed**: Re-run `venv/bin/python scripts/cleanup_old_collections_auto.py`

#### Test 1.2: Unit Tests
```bash
PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/pytest tests/unit/test_memory_types.py -v
```

**Expected Outcome**: All 13 tests pass
- TestSemanticMemory: 5/5 ✅
- TestProceduralMemory: 6/6 ✅
- TestMemoryStats: 1/1 ✅
- TestUserMemoryProfile: 1/1 ✅

**If Failed**: Check error messages - likely DB connection or collection issues

---

### Phase 2: Core Memory System (20 min)

#### Test 2.1: Memory Manager Initialization
```bash
venv/bin/python -c "
from shared.db import MongoDB
from memory.manager import MemoryManager

db = MongoDB().get_database()
memory = MemoryManager(db)

print('✅ MemoryManager initialized')
print(f'✅ Episodic collection: {memory.episodic.name}')
print(f'✅ Semantic collection: {memory.semantic.name}')
print(f'✅ Procedural collection: {memory.procedural.name}')
print(f'✅ In-memory dicts created: {len(memory._session_contexts)} sessions, {len(memory._handoffs)} handoffs')
"
```

**Expected Outcome**:
- ✅ No errors
- ✅ All collections initialized
- ✅ In-memory dicts exist (counts will be 0)

**If Failed**: Check memory/manager.py imports and _setup_collections()

#### Test 2.2: Test Each Memory Type

**A. Test Episodic Memory (Actions)**
```bash
venv/bin/python -c "
from shared.db import MongoDB
from memory.manager import MemoryManager

db = MongoDB().get_database()
memory = MemoryManager(db)

# Record an action
action_id = memory.record_action(
    user_id='test-user-tomorrow',
    session_id='test-session-tomorrow',
    action_type='test',
    entity_type='task',
    entity={'task_title': 'Test Action'},
    generate_embedding=False
)
print(f'✅ Action recorded: {action_id}')

# Retrieve it
history = memory.get_action_history('test-user-tomorrow', limit=1)
print(f'✅ Action retrieved: {len(history)} actions')
print(f'   Action type: {history[0][\"action_type\"]}')

# Cleanup
db.memory_episodic.delete_many({'user_id': 'test-user-tomorrow'})
print('✅ Cleanup complete')
"
```

**Expected Outcome**:
- ✅ Action recorded with ID
- ✅ Action retrieved successfully
- ✅ Cleanup successful

**B. Test Semantic Memory (Preferences)**
```bash
venv/bin/python -c "
from shared.db import MongoDB
from memory.manager import MemoryManager

db = MongoDB().get_database()
memory = MemoryManager(db)

# Record a preference
pref_id = memory.record_preference(
    user_id='test-user-tomorrow',
    key='test_pref',
    value='test_value'
)
print(f'✅ Preference recorded: {pref_id}')

# Retrieve it
pref = memory.get_preference('test-user-tomorrow', 'test_pref')
print(f'✅ Preference retrieved: {pref[\"key\"]} = {pref[\"value\"]}')

# Cleanup
db.memory_semantic.delete_many({'user_id': 'test-user-tomorrow'})
print('✅ Cleanup complete')
"
```

**Expected Outcome**:
- ✅ Preference recorded
- ✅ Preference retrieved correctly
- ✅ Cleanup successful

**C. Test Working Memory (In-Memory)**
```bash
venv/bin/python -c "
from shared.db import MongoDB
from memory.manager import MemoryManager

db = MongoDB().get_database()
memory = MemoryManager(db)

# Update session context
memory.update_session_context('test-session-tomorrow', {'test': 'value'})
print('✅ Session context updated')

# Retrieve it
context = memory.read_session_context('test-session-tomorrow')
print(f'✅ Session context retrieved: {context}')

# Clear it
memory.clear_session_context('test-session-tomorrow')
context_after = memory.read_session_context('test-session-tomorrow')
print(f'✅ Session cleared: {context_after is None}')
"
```

**Expected Outcome**:
- ✅ Context stored in memory
- ✅ Context retrieved correctly
- ✅ Context cleared successfully

**If Any Failed**: Check memory/manager.py method implementations

#### Test 2.3: Memory Stats
```bash
venv/bin/python -c "
from shared.db import MongoDB
from memory.manager import MemoryManager

db = MongoDB().get_database()
memory = MemoryManager(db)

stats = memory.get_memory_stats('test-session', 'demo-user')
print('✅ Memory stats retrieved')
print(f'   Working memory: {stats[\"by_type\"][\"working_memory\"]}')
print(f'   Episodic memory: {stats[\"by_type\"][\"episodic_memory\"]}')
print(f'   Semantic memory: {stats[\"by_type\"][\"semantic_memory\"]}')
print(f'   Procedural memory: {stats[\"by_type\"][\"procedural_memory\"]}')
print(f'   Handoffs pending: {stats[\"by_type\"][\"handoffs_pending\"]}')
"
```

**Expected Outcome**:
- ✅ Stats returned without errors
- ✅ All memory types show counts (may be 0)
- ✅ No field errors

**If Failed**: Check field names in get_memory_stats() match UI expectations

---

### Phase 3: Integration Tests (15 min)

#### Test 3.1: Run Integration Tests
```bash
# Test action recording
PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/pytest tests/integration/memory/test_action_recording.py -v -s

# Test preferences flow
PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/pytest tests/integration/memory/test_preferences_flow.py -v -s

# If time permits, run all
PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/pytest tests/integration/memory/ -v
```

**Expected Outcome**:
- ✅ Most tests pass
- ⚠️  Some tests may fail if they depend on specific demo data

**If Failed**: Check error messages - likely coordinator integration issues

---

### Phase 4: Demo Data & Application (30 min)

#### Test 4.1: Seed Demo Data
```bash
# IMPORTANT: This will clear existing data!
venv/bin/python scripts/demo/seed_demo_data.py --clean --skip-embeddings
```

**Expected Outcome**:
- ✅ Projects seeded (should see count)
- ✅ Tasks seeded (should see count)
- ✅ Procedural memory seeded (templates/workflows)
- ✅ Semantic memory seeded (preferences)
- ✅ Episodic memory seeded (actions)
- ✅ All verification checks pass

**If Failed**:
- Check error messages for collection name issues
- Verify database connection
- Check seed data structure matches new schema

#### Test 4.2: Verify Seeded Data
```bash
venv/bin/python scripts/demo/seed_demo_data.py --verify-only
```

**Expected Outcome**:
- ✅ All critical items exist
- ✅ Counts match expected (projects, tasks, memory entries)
- ✅ No missing items

**If Failed**: Re-run seed with --clean flag

#### Test 4.3: Start Demo App (UI)
```bash
venv/bin/streamlit run ui/demo_app.py
```

**Manual Testing Checklist**:
- [ ] App starts without errors
- [ ] Memory stats panel shows counts
  - [ ] Working memory count displayed
  - [ ] Episodic memory count displayed
  - [ ] Semantic memory count displayed
  - [ ] Procedural memory count displayed
  - [ ] Handoffs pending count displayed (not "memory_shared")
- [ ] Can create a new task
- [ ] Can view projects
- [ ] Can send a message to coordinator
- [ ] Memory panel updates after actions

**Expected Outcome**:
- ✅ App loads successfully
- ✅ All memory stats display correctly
- ✅ Can perform CRUD operations
- ✅ No console errors related to memory collections

**If Failed**:
- Check browser console for errors
- Check terminal for Python errors
- Verify ui/demo_app.py uses correct field names

#### Test 4.4: Test Coordinator with Memory
```bash
venv/bin/python -c "
from agents.coordinator import coordinator
from shared.db import MongoDB
from memory import MemoryManager

# Initialize
mongodb = MongoDB()
db = mongodb.get_database()
memory = MemoryManager(db)
coordinator.memory = memory

# Set session
session_id = 'test-coordinator-session'
coordinator.set_session(session_id, user_id='demo-user')

# Test query
response = coordinator.process(
    user_message='What projects do I have?',
    session_id=session_id,
    turn_number=1,
    optimizations={'memory_long_term': True}
)

print('✅ Coordinator responded')
print(f'Response: {response[\"assistant_message\"][:200]}...')
"
```

**Expected Outcome**:
- ✅ Coordinator processes message
- ✅ Returns response
- ✅ No memory-related errors

**If Failed**:
- Check coordinator memory configuration
- Verify coordinator.py doesn't reference old collections directly

---

### Phase 5: End-to-End Workflow (20 min)

#### Test 5.1: Complete Demo Flow
Run through the full demo scenario:

1. **Start Streamlit app**:
   ```bash
   venv/bin/streamlit run ui/demo_app.py
   ```

2. **Execute demo flow** (in UI):
   - [ ] Set context: "I'm focusing on building a gaming demo"
   - [ ] Check: Session context appears in memory stats
   - [ ] Search knowledge: "What do we know about MongoDB for gaming?"
   - [ ] Check: Semantic memory count increases
   - [ ] List templates: "What templates do I have?"
   - [ ] Check: Shows procedural memory templates
   - [ ] Create project: "Create a project called Test Gaming Project"
   - [ ] Check: Episodic memory count increases
   - [ ] View memory stats panel
   - [ ] Check: All counts are > 0

**Expected Outcome**:
- ✅ All steps complete without errors
- ✅ Memory stats update correctly
- ✅ Data persists in database
- ✅ No console errors

**If Failed**:
- Note which step fails
- Check that specific memory type (episodic/semantic/procedural/working)
- Review logs for collection reference errors

---

## 🚨 Common Issues & Solutions

### Issue 1: "Collection not found" errors
**Symptom**: Errors about memory_short_term, memory_long_term, or memory_shared

**Solution**:
```bash
# Check if old collections still exist
venv/bin/python -c "from shared.db import MongoDB; print(MongoDB().get_database().list_collection_names())"

# If old collections found, run cleanup
venv/bin/python scripts/cleanup_old_collections_auto.py
```

### Issue 2: Memory stats show wrong field names
**Symptom**: UI shows "memory_shared" instead of "Handoffs Pending"

**Solution**:
- Check ui/demo_app.py line 168
- Should reference `handoffs_pending` not `memory_shared`
- Check ui/streamlit_app.py line 372

### Issue 3: Tests fail with collection errors
**Symptom**: Tests try to access old collections

**Solution**:
```bash
# Verify test file updates
grep -n "memory_long_term\|memory_short_term\|memory_shared" tests/unit/test_memory_types.py

# Should return no results
# If it does, re-apply test updates from commit f47b7b4
```

### Issue 4: Coordinator doesn't save actions
**Symptom**: Episodic memory count doesn't increase

**Solution**:
- Check that `memory_long_term` optimization flag is enabled
- Verify coordinator.memory is initialized
- Check memory.record_action() is being called
- Verify actions are written to `memory_episodic` collection

### Issue 5: Empty semantic memory
**Symptom**: memory_semantic collection doesn't exist or is empty

**Solution**:
- This is normal - collection is created on first use
- Record a preference or cache knowledge to trigger creation
- Run: `venv/bin/python scripts/demo/seed_demo_data.py --clean`

---

## 📋 Success Criteria

At the end of testing, you should have:

- ✅ All 13 unit tests passing
- ✅ Integration tests passing (most of them)
- ✅ Demo data seeded successfully
- ✅ UI starts and displays memory stats correctly
- ✅ Can create/update/delete data through UI
- ✅ Memory stats update in real-time
- ✅ No errors in console/logs about old collections
- ✅ Database contains only new collections (episodic, semantic, procedural)

---

## 📝 Issues Log

**Use this section to track any problems you find:**

### Issue #1:
- **What**: [Description]
- **When**: [Which test phase]
- **Error**: [Error message]
- **Fix**: [What you did]

### Issue #2:
- **What**:
- **When**:
- **Error**:
- **Fix**:

---

## 🎯 After Testing - Next Steps

### If All Tests Pass ✅
1. **Create PR to main branch**:
   ```bash
   gh pr create --title "Memory collection migration - episodic/semantic/procedural" \
     --body "Migrates from 3 old collections to new architecture. All tests passing."
   ```

2. **Tag the release**:
   ```bash
   git tag -a v1.0-memory-migration -m "Memory collection migration complete"
   git push origin v1.0-memory-migration
   ```

3. **Update main documentation**:
   - Update README.md with new memory architecture
   - Update API docs if any exist
   - Add migration notes to CHANGELOG.md

4. **Plan vector index creation**:
   - Go to MongoDB Atlas UI
   - Create vector indexes for memory_episodic and memory_semantic
   - Follow instructions in docs/MIGRATION_STATUS.md

### If Tests Fail ⚠️
1. **Document failures** in Issues Log above
2. **Check migration status**:
   ```bash
   cat docs/MIGRATION_STATUS.md
   ```
3. **Review recent commits**:
   ```bash
   git log --oneline -10
   ```
4. **Consider rollback if major issues**:
   ```bash
   # Only if absolutely necessary
   git revert eaf3d61 5474010 f47b7b4
   # Then restore old collections from backup
   ```

5. **Fix issues and re-test**:
   - Fix code
   - Commit fixes
   - Re-run test plan
   - Update this TODO list with fixes

---

## 🔗 Quick Reference Links

**Documentation**:
- Full migration details: `docs/MIGRATION_STATUS.md`
- Session summary: `docs/SESSION_SUMMARY.md`
- Demo readiness: `docs/DEMO_READINESS_SUMMARY.md`

**Key Files**:
- Memory manager: `memory/manager.py` (1851 lines)
- Setup script: `scripts/setup/init_db.py`
- Demo seeding: `scripts/demo/seed_demo_data.py`
- Unit tests: `tests/unit/test_memory_types.py`

**Useful Commands**:
```bash
# Check collections
venv/bin/python -c "from shared.db import MongoDB; print(MongoDB().get_database().list_collection_names())"

# Run unit tests
PYTHONPATH=/Users/mikiko.b/Github/mdb-flow venv/bin/pytest tests/unit/test_memory_types.py -v

# Seed demo data
venv/bin/python scripts/demo/seed_demo_data.py --clean --skip-embeddings

# Start UI
venv/bin/streamlit run ui/demo_app.py

# Verify setup
venv/bin/python scripts/setup/verify_setup.py
```

---

## ⏱️ Estimated Time

- Pre-flight checks: 5 min
- Phase 1 (Database & Setup): 15 min
- Phase 2 (Core Memory): 20 min
- Phase 3 (Integration Tests): 15 min
- Phase 4 (Demo Data & App): 30 min
- Phase 5 (E2E Workflow): 20 min
- **Total**: ~1.5 hours

---

## ✅ Final Checklist

Before considering the migration fully production-ready:

- [ ] All unit tests pass (13/13)
- [ ] Integration tests pass
- [ ] Demo data seeds successfully
- [ ] UI displays memory stats correctly
- [ ] Can perform full demo flow without errors
- [ ] No console errors about old collections
- [ ] Memory stats update in real-time
- [ ] Database contains only new collections
- [ ] Documentation is complete
- [ ] PR created to main branch
- [ ] Team has reviewed changes
- [ ] Vector indexes created in Atlas (optional but recommended)

---

**Good luck with testing! The migration is complete - just needs verification that everything works in practice.** ✅
