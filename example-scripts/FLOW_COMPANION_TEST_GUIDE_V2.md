# Flow Companion Complete Test Guide v2
## Milestones 1 & 2: Text + Voice + Performance Testing

This guide walks you through testing Flow Companion systematically, including latency benchmarks and multi-turn conversation flows.

---

## Pre-Flight Checklist

Before testing, verify your setup:

```bash
# 1. App is running
streamlit run ui/streamlit_app.py

# 2. Environment variables set
cat .env | grep -E "ANTHROPIC|VOYAGE|OPENAI|MONGODB"

# 3. Sample data loaded
python scripts/load_sample_data.py
```

**Expected sidebar state:** You should see projects with tasks listed.

---

## Performance Benchmarks

Use the Agent Debug panel to verify these latency targets:

| Operation | Target | Acceptable | Too Slow |
|-----------|--------|------------|----------|
| `get_tasks` | <200ms | <500ms | >1000ms |
| `get_projects` | <200ms | <500ms | >1000ms |
| `search_tasks` (hybrid) | <800ms | <1500ms | >3000ms |
| `search_projects` (hybrid) | <800ms | <1500ms | >3000ms |
| `complete_task` | <500ms | <1000ms | >2000ms |
| `start_task` | <500ms | <1000ms | >2000ms |
| `add_note_to_task` | <500ms | <1000ms | >2000ms |
| Full query (with LLM) | <3000ms | <5000ms | >8000ms |

**If operations exceed "Too Slow" thresholds:**
- Check if embeddings are being generated on read (they shouldn't be)
- Verify `{"embedding": 0}` projection is used in queries
- Check for N+1 query problems
- Ensure MongoDB indexes exist on `status` and `project_id`

---

## Phase 1: Basic Text Queries + Latency

### 1.1 Simple Retrieval (Target: <500ms tool time)

| # | Input | Expected Tool | Target Latency |
|---|-------|---------------|----------------|
| 1 | `What tasks do I have?` | `get_tasks` | <200ms |
| 2 | `Show me all my projects` | `get_projects` | <200ms |
| 3 | `What tasks are in progress?` | `get_tasks` (status filter) | <200ms |
| 4 | `Show me completed tasks` | `get_tasks` (status filter) | <200ms |

**✓ Checkpoint:** All queries should use `get_tasks`/`get_projects`, not `search_tasks`.

### 1.2 Project-Specific Queries

| # | Input | Expected Tool | Target Latency |
|---|-------|---------------|----------------|
| 5 | `What's in the AgentOps project?` | `get_tasks` (project filter) | <300ms |
| 6 | `Show me the Voice Agent tasks` | `search_tasks` or `get_tasks` | <800ms |
| 7 | `LangGraph Integration status` | `search_projects` | <800ms |

### 1.3 Semantic/Hybrid Search (Target: <1500ms tool time)

| # | Input | Expected Tool | Target Latency |
|---|-------|---------------|----------------|
| 8 | `Find tasks about debugging` | `search_tasks` | <1000ms |
| 9 | `Show me memory-related tasks` | `search_tasks` | <1000ms |
| 10 | `Tasks about real-time streaming` | `search_tasks` | <1000ms |

**✓ Checkpoint:** Verify debug panel shows `search_tasks` with `$rankFusion` (hybrid search).

---

## Phase 2: Task Management + Latency

### 2.1 Completing Tasks

| # | Input | Expected Tools | Target Latency |
|---|-------|----------------|----------------|
| 11 | `I finished the debugging doc` | `search_tasks` → `complete_task` | <2000ms total |
| 12 | `Mark the checkpointer task as done` | `search_tasks` → `complete_task` | <2000ms total |
| 13 | `Complete "Review PR feedback"` | `search_tasks` → `complete_task` | <2000ms total |

**Expected flow in debug panel:**
```
Call 1: search_tasks (500-800ms)
  Input: {"query": "debugging doc"}
  Output: 3 tasks returned

Call 2: complete_task (300-500ms)
  Input: {"task_id": "..."}
  Output: Success
```

### 2.2 Starting Tasks

| # | Input | Expected Tools | Target Latency |
|---|-------|----------------|----------------|
| 14 | `I'm starting work on the audio pipeline` | `search_tasks` → `start_task` | <2000ms |
| 15 | `Working on the February webinar now` | `search_tasks` → `start_task` | <2000ms |
| 16 | `Pick up the NPC memory task` | `search_tasks` → `start_task` | <2000ms |

### 2.3 Adding Notes

| # | Input | Expected Tools | Target Latency |
|---|-------|----------------|----------------|
| 17 | `Add a note to the voice agent app: WebSocket streaming working` | `search_tasks` → `add_note_to_task` | <2000ms |
| 18 | `Note on checkpointer: need to handle connection pooling` | `search_tasks` → `add_note_to_task` | <2000ms |

---

## Phase 3: Voice Input + Latency

### 3.1 Voice Transcription (Target: <2000ms)

| # | Type | Say This | Expected |
|---|------|----------|----------|
| 19 | 🎤 | "Hello, can you hear me?" | Transcription appears |

**Check:** Whisper transcription time in logs (should be <2000ms for short clips).

### 3.2 Voice Queries (Same path as text)

| # | Type | Say This | Expected Tool | Target Latency |
|---|------|----------|---------------|----------------|
| 20 | 🎤 | "What are my tasks?" | `get_tasks` | <200ms |
| 21 | 🎤 | "Show me the AgentOps project" | `get_tasks` or `search_projects` | <800ms |
| 22 | 🎤 | "Find tasks about memory" | `search_tasks` | <1000ms |

**✓ Checkpoint:** Voice and text should produce identical tool calls and similar latency.

### 3.3 Voice Task Updates

| # | Type | Say This | Expected Tools | Target Latency |
|---|------|----------|----------------|----------------|
| 23 | 🎤 | "I just finished the debugging doc" | `search_tasks` → `complete_task` | <2500ms |
| 24 | 🎤 | "I'm starting work on the evaluation framework" | `search_tasks` → `start_task` | <2500ms |
| 25 | 🎤 | "Quick note on voice agent: got interruption handling working" | `search_tasks` → `add_note_to_task` | <2500ms |

---

## Phase 4: Multi-Turn Conversations

These tests verify context is maintained across turns.

### 4.1 Project Context Persistence

| Turn | Input | Expected Behavior |
|------|-------|-------------------|
| 1 | `Show me the AgentOps project` | Lists AgentOps tasks |
| 2 | `What's the highest priority one?` | Answers about AgentOps (not all projects) |
| 3 | `Mark it as in progress` | Updates the high-priority AgentOps task |
| 4 | `Add a note: started implementation` | Adds note to same task |

**✓ Checkpoint:** Agent remembers we're talking about AgentOps without re-stating it.

### 4.2 Task Context Persistence

| Turn | Input | Expected Behavior |
|------|-------|-------------------|
| 1 | `Find the checkpointer task` | Shows checkpointer task(s) |
| 2 | `What's its current status?` | Shows status of checkpointer |
| 3 | `Change it to in progress` | Updates checkpointer status |
| 4 | `What project is it in?` | Answers about checkpointer's project |

### 4.3 Disambiguation Flow

| Turn | Input | Expected Behavior |
|------|-------|-------------------|
| 1 | `I finished the webinar task` | Asks: "Which webinar? 1. January 2. February 3. March" |
| 2 | `The February one` | Completes February webinar task |
| 3 | `What about March?` | Shows March webinar task status |
| 4 | `Start that one` | Starts March webinar task |

### 4.4 Mixed Voice/Text Multi-Turn

| Turn | Type | Input | Expected |
|------|------|-------|----------|
| 1 | Text | `Show me the Voice Agent project` | Lists project tasks |
| 2 | 🎤 | "What's still in progress?" | Filters to in_progress (remembers project) |
| 3 | Text | `Complete the reference app task` | Completes task in Voice Agent project |
| 4 | 🎤 | "What's left to do?" | Shows remaining Voice Agent tasks |

### 4.5 Correction and Backtracking

| Turn | Input | Expected Behavior |
|------|-------|-------------------|
| 1 | `Mark the debugging doc as done` | Confirms completion |
| 2 | `Wait, I meant the scaling guide` | Should undo debugging doc, complete scaling guide (or ask to confirm) |
| 3 | `Actually, neither - show me both` | Shows both tasks |
| 4 | `The debugging one is done, scaling is in progress` | Updates both correctly |

### 4.6 Long Conversation (10+ turns)

Test that context doesn't degrade over many turns:

| Turn | Input |
|------|-------|
| 1 | `What projects do I have?` |
| 2 | `Show me AgentOps` |
| 3 | `What's in progress?` |
| 4 | `Any high priority?` |
| 5 | `Add a note to the first one: need to review` |
| 6 | `What about LangGraph project?` |
| 7 | `Compare progress between AgentOps and LangGraph` |
| 8 | `Which has more completed tasks?` |
| 9 | `Go back to AgentOps` |
| 10 | `What was that note I just added?` |
| 11 | `Mark that task as done` |
| 12 | `Summary of what we did today` |

**✓ Checkpoint:** Agent should track context through all 12 turns without confusion.

---

## Phase 5: Temporal Queries

Test the system's ability to understand and filter by time references.

### 5.1 Relative Time References

| # | Input | Expected Behavior |
|---|-------|-------------------|
| 26 | `What did I work on today?` | Tasks with activity_log entries from today |
| 27 | `What did I complete yesterday?` | Tasks marked done yesterday |
| 28 | `Show me tasks from this week` | Tasks with recent activity |
| 29 | `What's been in progress for more than a week?` | Stale in_progress tasks |

### 5.2 Activity-Based Temporal Queries

| # | Input | Expected Behavior |
|---|-------|-------------------|
| 30 | `What tasks did I start this week?` | Tasks changed to in_progress this week |
| 31 | `What notes did I add today?` | Tasks with notes added today |
| 32 | `Show me recently completed tasks` | Tasks marked done in last 7 days |
| 33 | `What haven't I touched in a while?` | Tasks with no recent activity_log entries |

### 5.3 Due Date Queries (if implemented)

| # | Input | Expected Behavior |
|---|-------|-------------------|
| 34 | `What's due this week?` | Tasks with due_date in current week |
| 35 | `Any overdue tasks?` | Tasks with due_date < today and status != done |
| 36 | `What's coming up next month?` | Tasks with due_date in next 30 days |

### 5.4 Combined Temporal + Filter Queries

| # | Input | Expected Behavior |
|---|-------|-------------------|
| 37 | `What high priority tasks did I complete this week?` | Priority + status + time filter |
| 38 | `Show me AgentOps tasks I worked on yesterday` | Project + time filter |
| 39 | `What's been in progress the longest?` | Sort by time in current status |
| 40 | `Tasks I started but haven't finished this week` | Started this week, still in_progress |

### 5.5 Temporal Multi-Turn

| Turn | Input | Expected Behavior |
|------|-------|-------------------|
| 1 | `What did I do yesterday?` | Lists yesterday's activity |
| 2 | `What about the day before?` | Lists 2 days ago (context: time) |
| 3 | `Compare that to today` | Compares activity across days |
| 4 | `Which day was more productive?` | Summarizes comparison |

### 5.6 Natural Language Time Expressions

| # | Input | Time Interpretation |
|---|-------|---------------------|
| 41 | `last week` | 7-14 days ago |
| 42 | `this morning` | Today before noon |
| 43 | `recently` | Last 7 days |
| 44 | `a few days ago` | 2-4 days ago |
| 45 | `the past month` | Last 30 days |
| 46 | `since Monday` | From most recent Monday |

**✓ Checkpoint:** Agent should understand natural time expressions, not just exact dates.

---

## Phase 6: Edge Cases and Error Handling

### 6.1 Ambiguous References

| # | Input | Expected |
|---|-------|----------|
| 47 | `I finished the doc` | Shows options: "Which doc? 1. Debugging doc 2. Scaling doc..." |
| 48 | `The webinar task` | Shows options: "Which webinar? 1. January 2. February 3. March" |
| 49 | `Complete the task` | Asks: "Which task would you like to complete?" |

### 6.2 Non-Existent Items

| # | Input | Expected |
|---|-------|----------|
| 50 | `Show me the Kubernetes project` | "I couldn't find a project matching 'Kubernetes'" |
| 51 | `Complete the blockchain task` | "I couldn't find a task matching 'blockchain'" |

### 6.3 Invalid Operations

| # | Input | Expected |
|---|-------|----------|
| 52 | `Complete the task that's already done` | Graceful handling or skip |
| 53 | `Start the completed task` | Either warns or allows (depending on design) |

### 6.4 Minimal/Malformed Input

| # | Type | Input | Expected |
|---|------|-------|----------|
| 54 | Text | (empty string) | Asks for input |
| 55 | 🎤 | "um..." | Gracefully handles |
| 56 | Text | `?` | Asks what they need help with |

---

## Phase 7: Formatting Verification

### 7.1 Task List Formatting

Query: `What are my tasks?`

**Expected format:**
```markdown
Here are your tasks:

## In Progress (X tasks)
1. **Task name** (High priority) - Project Name
2. **Task name** (Medium priority) - Project Name

## To Do (X tasks)
1. **Task name** (Priority) - Project Name

## Done (X tasks)
1. **Task name** ✓ - Project Name
```

**Not acceptable:**
- Wall of text with no line breaks
- Missing headers
- No priority/project info

### 7.2 Search Results Formatting

Query: `Find tasks about debugging`

**Expected format:**
```markdown
I found 3 tasks matching "debugging":

1. **Create debugging methodologies doc** (High) - AgentOps
   Context: Document common debugging patterns...
   
2. **Debug memory leaks** (Medium) - Voice Agent
   Context: Investigate memory issues...
```

### 7.3 Confirmation Formatting

Query: `I finished the voice agent app`

**Expected format:**
```markdown
✓ Marked "Build voice agent reference app" as complete.

This was a high-priority task in the Voice & Multimodal AI Apps project.
```

---

## Phase 8: Performance Stress Tests

### 8.1 Rapid Fire Queries

Send these quickly (within 30 seconds):

1. `What are my tasks?`
2. `Show me AgentOps`
3. `Find debugging tasks`
4. `Complete the first one`
5. `What's left?`

**✓ Checkpoint:** No timeouts, no errors, responses stay consistent.

### 8.2 Large Result Sets

| # | Query | Expected |
|---|-------|----------|
| 57 | `Show me ALL tasks` | Should paginate or summarize (not crash) |
| 58 | `List every project with all their tasks` | Should handle gracefully |

### 8.3 Complex Queries

| # | Query | Target Latency |
|---|-------|----------------|
| 59 | `What high priority tasks are in progress across all projects?` | <3000ms |
| 60 | `Compare AgentOps and LangGraph projects - which has more todos?` | <4000ms |
| 61 | `Find all tasks I worked on this week and summarize progress` | <5000ms |

---

## Quick Regression Test (5 minutes)

Run before any PR merge:

| # | Type | Test | Tool | Latency OK? | Pass? |
|---|------|------|------|-------------|-------|
| 1 | Text | "What are my tasks?" | `get_tasks` | <500ms | ☐ |
| 2 | Text | "Find tasks about debugging" | `search_tasks` | <1500ms | ☐ |
| 3 | Text | "I finished the debugging doc" | `search_tasks` → `complete_task` | <2500ms | ☐ |
| 4 | Text | "Show me AgentOps" | `get_tasks`/`search_projects` | <1000ms | ☐ |
| 5 | Text | "What did I complete this week?" | Temporal query | <1500ms | ☐ |
| 6 | 🎤 | "What are my tasks?" | `get_tasks` | <500ms | ☐ |
| 7 | 🎤 | "Quick note on voice agent: test" | `search_tasks` → `add_note` | <2500ms | ☐ |
| 8 | Multi | "Show AgentOps" → "What's high priority?" | Context maintained | - | ☐ |
| 9 | Multi | "Find webinar task" → "The February one" | Disambiguation works | - | ☐ |
| 10 | Multi | "What did I do yesterday?" → "What about today?" | Temporal context | - | ☐ |
| 11 | - | Check formatting (headers, bullets) | Readable output | - | ☐ |
| 12 | - | No errors in terminal | Clean logs | - | ☐ |
| 9 | - | Check formatting (headers, bullets) | Readable output | - | ☐ |
| 10 | - | No errors in terminal | Clean logs | - | ☐ |

---

## Latency Debugging Checklist

If operations are slow:

### get_tasks slow (>500ms)
- [ ] Check `{"embedding": 0}` projection is used
- [ ] Verify no embedding generation on read
- [ ] Check MongoDB index on `status` field
- [ ] Check MongoDB index on `project_id` field

### search_tasks slow (>2000ms)
- [ ] Verify Atlas Search indexes are "READY"
- [ ] Check `vector_index` exists and is active
- [ ] Check `tasks_text_index` exists and is active
- [ ] Verify Voyage API isn't being called multiple times

### complete_task / start_task slow (>1000ms)
- [ ] Should be simple `update_one()` - no LLM calls
- [ ] No embedding regeneration
- [ ] Check if full document is being returned unnecessarily

### Full query slow (>5000ms)
- [ ] Check LLM response time in logs
- [ ] Multiple tool calls adding up?
- [ ] Network latency to Anthropic API?

---

## Troubleshooting

### Voice Not Transcribing
- Check OPENAI_API_KEY in .env
- Verify OpenAI API credits
- Check browser mic permissions

### Same Query Different Results (Voice vs Text)
- Should be identical now with unified tool architecture
- If different, check that voice path sends transcript to same `process()` method

### Context Not Maintained in Multi-Turn
- Check conversation history is being passed to LLM
- Verify history format matches Anthropic API spec
- Check history isn't being truncated

### Hybrid Search Returns Wrong Results
- Test text search separately
- Test vector search separately
- Check index field names match code

### "Tool not found" Errors
- Verify all tools are registered in COORDINATOR_TOOLS
- Check tool names match exactly

---

## Success Criteria

### Milestone 1 ✓
- [ ] Text queries return correct results
- [ ] `get_tasks` < 500ms
- [ ] Semantic search works
- [ ] Task CRUD operations work
- [ ] Formatting is clean and readable

### Milestone 2 ✓
- [ ] Voice transcription works
- [ ] Voice and text use same code path
- [ ] Voice queries < text queries + 2000ms (transcription overhead)
- [ ] "I finished X" flow works end-to-end
- [ ] Hybrid search matches informal references

### Temporal Queries ✓
- [ ] "What did I do today/yesterday?" returns correct tasks
- [ ] "This week" / "last week" interpreted correctly
- [ ] Activity-based queries work (started, completed, notes added)
- [ ] Combined temporal + filter queries work
- [ ] Temporal context maintained in multi-turn

### Multi-Turn ✓
- [ ] Context maintained for 5+ turns
- [ ] Disambiguation flow works
- [ ] Mixed voice/text conversations work
- [ ] Corrections and backtracking handled
- [ ] Temporal context carries across turns

### Performance ✓
- [ ] All tool calls within target latency
- [ ] No operations > 5 seconds
- [ ] Debug panel shows accurate timing

---

*Last updated: January 2026*
*Flow Companion v2.0 - Milestones 1 & 2 + Performance + Temporal*