# Memory System Test Plan

## Overview
This document outlines test scenarios for the three-tier memory system (short-term, long-term, shared) in Flow Companion.

---

## Prerequisites
1. Ensure MongoDB is running with memory collections created:
   ```bash
   # Setup all indexes (including memory)
   python scripts/setup_database.py

   # Or setup memory indexes only
   python scripts/setup_database.py --memory
   ```

2. Start the Streamlit app:
   ```bash
   streamlit run ui/streamlit_app.py
   ```

3. Enable memory in the sidebar UI:
   - Toggle "Enable Memory" ON
   - Verify all sub-toggles are ON:
     - Short-term ✓
     - Long-term ✓
     - Shared ✓
     - Ctx Inject ✓

---

## Test 1: Long-term Memory (Action History)

**Purpose:** Verify that completed tasks are recorded and can be retrieved via action history.

### Steps:
1. Complete a task:
   ```
   Mark the "Create debugging documentation" task as done
   ```

2. Verify recording:
   - Check debug panel for memory write operation
   - Check Memory Stats expander (should show +1 action)

3. Query action history:
   ```
   What tasks did I complete today?
   ```

4. Expected result:
   - LLM calls `get_action_history` tool (visible in debug panel)
   - Response includes "Create debugging documentation"
   - Debug panel shows memory read timing

---

## Test 2: Shared Memory (Agent Handoff)

**Purpose:** Verify that retrieval agent can hand off task context to worklog agent.

### Steps:
1. Ask about a task using informal reference:
   ```
   Add a note to the debugging doc task: "Added section on memory system"
   ```

2. Expected flow:
   - Retrieval agent searches for "debugging doc"
   - Writes handoff to shared memory
   - Worklog agent reads handoff
   - Adds note without re-searching

3. Verify in debug panel:
   - Should see "🤝 Agent Handoff" visualization
   - Should show "Shared Memory Used" indicator
   - Memory stats should show +1 shared memory (then consumed)

---

## Test 3: Short-term Memory (Session Context)

**Purpose:** Verify that session context is maintained across queries.

### Steps:
1. Set project context:
   ```
   I'm working on the AgentOps project
   ```

2. Verify context storage:
   - Check "📍 Current Context" expander
   - Should show "Project: AgentOps"

3. Create task using context:
   ```
   Create a task to optimize the agent response time
   ```

4. Expected result:
   - Task should be automatically assigned to AgentOps project
   - Context injection indicator in debug panel

---

## Test 4: Memory Toggle Effects

**Purpose:** Verify that disabling memory features removes capabilities.

### Test 4a: Disable Long-term Memory
1. Turn OFF "Long-term" toggle
2. Ask: `What did I complete today?`
3. Expected: LLM cannot use `get_action_history` tool (not available)

### Test 4b: Disable Shared Memory
1. Turn OFF "Shared" toggle
2. Ask: `Add a note to the debugging doc`
3. Expected: Retrieval agent searches, but no handoff occurs (searches twice)

### Test 4c: Disable All Memory
1. Turn OFF "Enable Memory" master toggle
2. Verify all sub-toggles disabled
3. Ask memory-dependent query: `What did I work on?`
4. Expected: LLM has no memory tools available

---

## Test 5: Clear Session Memory

**Purpose:** Verify that clearing memory works correctly.

### Steps:
1. Complete a task (to create memory entries)
2. Click "🗑️ Clear Session Memory" button
3. Verify:
   - Success message appears
   - Current Context expander is empty
   - Memory Stats shows 0 short-term entries
   - Session ID remains same (doesn't create new session)

---

## Test 6: Memory Stats Display

**Purpose:** Verify that memory statistics are accurate.

### Steps:
1. With memory enabled, expand "📊 Memory Stats"
2. Complete a task
3. Verify stats update:
   - Short-term: +1 entry (session context)
   - Long-term: +1 action
   - Shared: 0 pending (consumed immediately)
4. Refresh page and verify:
   - Short-term: 0 (new session)
   - Long-term: Persistent (still shows previous actions)

---

## Test 7: Debug Panel Memory Display

**Purpose:** Verify that memory operations are visible in debug panel.

### Steps:
1. Perform action that uses memory (complete task)
2. Expand the turn in debug panel
3. Verify "🧠 Memory" section shows:
   - Read timing (if context was read)
   - Write timing (if action was recorded)
   - Total timing
   - Context injection status
   - Handoff visualization (if shared memory used)

---

## Performance Benchmarks

### Expected Memory Timings:
- **Short-term Read**: ~5-10ms (simple document lookup)
- **Short-term Write**: ~10-15ms (document insert/update)
- **Long-term Write**: ~200-250ms (includes embedding generation)
- **Long-term Read**: ~5-10ms (simple query)
- **Long-term Search**: ~300-400ms (vector search + embedding)
- **Shared Write**: ~10-15ms (atomic find_and_update)
- **Shared Read**: ~5-10ms (atomic find_and_update)

### Memory Overhead:
- Memory operations should add < 50ms for simple read/write
- Vector embeddings add ~200ms (Voyage AI API call)
- Total overhead typically < 5% of LLM thinking time

---

## Troubleshooting

### Memory not recording
- Check that memory toggle is ON
- Verify MongoDB connection in logs
- Run `python scripts/setup_memory_indexes.py` to ensure collections exist

### Memory stats showing 0
- Check that actions are completing successfully
- Verify session_id is being passed to coordinator
- Check MongoDB directly: `db.long_term_memory.find()`

### Agent handoff not working
- Verify "Shared" toggle is ON
- Check that both retrieval and worklog agents have memory manager
- Look for "set_session" calls in coordinator logs

### Memory timing not showing in debug panel
- Verify memory operations occurred (check logs)
- Ensure debug panel is expanded for the relevant turn
- Check that `render_memory_debug()` is being called

---

## Success Criteria

✅ **All memory features should:**
1. Record actions correctly
2. Retrieve history accurately
3. Enable agent handoffs
4. Show timing in debug panel
5. Update stats in real-time
6. Respect toggle states
7. Clear when requested
8. Maintain session isolation

✅ **Performance should:**
- Memory overhead < 5% of total request time
- No significant impact on LLM latency
- MongoDB operations fast (< 20ms typically)

✅ **UI should:**
- Show current context clearly
- Display accurate memory stats
- Render debug information
- Toggle features on/off smoothly
