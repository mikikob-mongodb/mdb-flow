# Flow Companion Complete Test Guide
## Milestones 1 & 2: Text + Voice Integration Testing

This guide walks you through testing Flow Companion systematically, alternating between text and voice inputs to verify all functionality works correctly.

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

**Expected sidebar state:** You should see 10 projects with tasks listed.

---

## Phase 1: Basic Text Queries (Milestone 1 Core)

Start with text input to verify the foundation works.

### 1.1 Simple Retrieval

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 1 | Text | `What tasks do I have?` | Lists all tasks across projects |
| 2 | Text | `Show me all my projects` | Lists 10 projects with descriptions |
| 3 | Text | `What tasks are in progress?` | Filters to only in_progress tasks |
| 4 | Text | `Show me completed tasks` | Shows tasks with status "done" |

**✓ Checkpoint:** If these fail, check MongoDB connection and collection names.

### 1.2 Project-Specific Queries

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 5 | Text | `What's in the AgentOps Framework project?` | Shows 5 tasks for AgentOps |
| 6 | Text | `Show me the Voice Agent Architecture tasks` | Shows 5 voice agent tasks |
| 7 | Text | `What's the status of LangGraph Integration?` | Shows project + 4 tasks with statuses |

### 1.3 Semantic Search (Vector Search)

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 8 | Text | `Find tasks about debugging` | Returns debugging methodologies doc + related |
| 9 | Text | `Show me tasks related to memory` | Returns memory-related tasks across projects |
| 10 | Text | `Tasks about real-time or streaming` | Returns audio pipeline, WebSocket tasks |

**✓ Checkpoint:** If semantic search returns nothing, verify:
- Vector index name in Atlas matches code (`vector_index`)
- Tasks have embeddings (check MongoDB for `embedding` field)
- Voyage AI key is valid

---

## Phase 2: Text-Based Task Management (Milestone 1 Actions)

### 2.1 Creating Tasks

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 11 | Text | `Create a task called "Review PR feedback" in the AgentOps Framework project` | Task created, confirmation shown |
| 12 | Text | `Add a new task: Write unit tests for coordinator` | Task created (may ask which project) |

**Verify:** Check sidebar refreshes with new task.

### 2.2 Updating Task Status

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 13 | Text | `Mark "Review PR feedback" as in progress` | Status changes to in_progress |
| 14 | Text | `Start working on the unit tests task` | Status changes to in_progress |
| 15 | Text | `Complete the "Review PR feedback" task` | Status changes to done |

### 2.3 Adding Notes

| # | Type | Input | Expected Result |
|---|------|-------|-----------------|
| 16 | Text | `Add a note to the LangGraph checkpointer task: Need to handle connection pooling` | Note appended to task |
| 17 | Text | `Note on voice agent app: Tested with 3 concurrent sessions successfully` | Note added with timestamp |

---

## Phase 3: Voice Input Basics (Milestone 2 Foundation)

Now test voice input. Speak naturally — the system should handle informal language.

### 3.1 Voice Transcription Test

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 18 | 🎤 Voice | "Hello, can you hear me?" | Transcription appears with 🎤 icon |

**✓ Checkpoint:** If transcription fails:
- Check OPENAI_API_KEY in .env
- Verify OpenAI API credits (separate from ChatGPT Plus)
- Check browser microphone permissions

### 3.2 Simple Voice Queries

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 19 | 🎤 Voice | "What are my tasks?" | Same result as text query |
| 20 | 🎤 Voice | "Show me the AgentOps project" | Project details returned |
| 21 | 🎤 Voice | "Any high priority tasks?" | Filters to high priority |

---

## Phase 4: Voice Task Updates (Milestone 2 Core)

This is where voice gets powerful — natural language task management.

### 4.1 Marking Tasks Complete

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 22 | 🎤 Voice | "I just finished the debugging methodologies doc" | Task marked complete, confirmation shown |
| 23 | 🎤 Voice | "Done with the checkpointer documentation" | Task marked complete |
| 24 | 🎤 Voice | "I completed the evaluation framework task" | Task marked complete |

**Expected behavior:**
- High confidence match (>0.8): Auto-completes
- Medium confidence (0.5-0.8): Asks "Did you mean X?"
- Low confidence (<0.5): Shows options to choose from

### 4.2 Starting Work (Progress Updates)

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 25 | 🎤 Voice | "I'm starting work on the real-time audio pipeline" | Status → in_progress |
| 26 | 🎤 Voice | "Working on the February webinar now" | Status → in_progress |
| 27 | 🎤 Voice | "Picking up the NPC memory task" | Status → in_progress |

### 4.3 Adding Notes via Voice

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 28 | 🎤 Voice | "Quick note on the voice agent app — got WebSocket streaming working" | Note added to task |
| 29 | 🎤 Voice | "Note for the gaming demo: tested with Unity, works great" | Note added |
| 30 | 🎤 Voice | "Just a heads up on the auth task, I figured out the cookie issue" | Note added |

---

## Phase 5: Natural Voice Updates (Stream of Consciousness)

Test the system's ability to parse rambling, natural speech.

### 5.1 Multi-Part Updates

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 31 | 🎤 Voice | "Okay so I finished the debugging doc, and I'm now working on the scaling guide. Oh, and I need to remember to test the checkpointer with concurrent writes." | Parses 3 actions: 1 completion, 1 progress update, 1 note |
| 32 | 🎤 Voice | "Made good progress today. The audio pipeline is done, started on interruption handling, probably won't get to the NPC stuff until next week." | Parses: 1 completion, 1 progress, 1 deferral |

### 5.2 Context and Decisions

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 33 | 🎤 Voice | "Decision on the LangGraph integration — we're going with Redis for the checkpointer backend instead of MongoDB, better fit for their use case" | Decision logged to project |
| 34 | 🎤 Voice | "Talked to the team, we're pushing the March webinar to April because of the conference conflict" | Context update captured |

### 5.3 Corrections and Clarifications

| # | Type | Say This | Expected Result |
|---|------|----------|-----------------|
| 35 | 🎤 Voice | "Actually wait, I meant the January webinar not February" | Should ask for clarification or correct |
| 36 | 🎤 Voice | "The auth task — no wait, I mean the session handling one" | Should handle mid-sentence correction |

---

## Phase 6: Mixed Mode Workflow

Real usage alternates between text and voice. Test the handoff.

### 6.1 Voice → Text Follow-up

| # | Sequence | Input | Expected |
|---|----------|-------|----------|
| 37a | 🎤 Voice | "Show me the AgentOps project" | Project displayed |
| 37b | Text | `What's the highest priority task there?` | Remembers context, answers about AgentOps |

### 6.2 Text → Voice Follow-up

| # | Sequence | Input | Expected |
|---|----------|-------|----------|
| 38a | Text | `Show me all in-progress tasks` | List displayed |
| 38b | 🎤 Voice | "Mark the first one as done" | Should complete task (may ask which one) |

### 6.3 Full Workflow Simulation

Simulate a real standup update:

| Step | Type | Input |
|------|------|-------|
| 39a | Text | `What did I work on yesterday?` |
| 39b | 🎤 Voice | "So today I'm planning to finish the debugging doc and start on the scaling guide" |
| 39c | Text | `Create a task for writing the changelog` |
| 39d | 🎤 Voice | "Actually, add that to the AgentOps project" |
| 39e | Text | `What's left in AgentOps now?` |

---

## Phase 7: Edge Cases and Error Handling

### 7.1 Ambiguous References

| # | Type | Input | Expected |
|---|------|-------|----------|
| 40 | 🎤 Voice | "I finished the doc" | Should ask: "Which doc?" with options |
| 41 | 🎤 Voice | "The webinar task" | Should ask: "Which webinar?" (Jan/Feb/March) |
| 42 | Text | `Complete the task` | Should ask which task |

### 7.2 Non-Existent Items

| # | Type | Input | Expected |
|---|------|-------|----------|
| 43 | Text | `Show me the Kubernetes project` | "No project found" or offers to create |
| 44 | 🎤 Voice | "I finished the blockchain integration" | "I couldn't find that task" |

### 7.3 Malformed Input

| # | Type | Input | Expected |
|---|------|-------|----------|
| 45 | 🎤 Voice | "Um... uh... yeah so..." | Gracefully handles filler words |
| 46 | 🎤 Voice | (5 seconds of silence) | Handles empty/minimal audio |
| 47 | Text | `` (empty) | No crash, asks for input |

---

## Phase 8: Data Integrity Checks

After running tests, verify data wasn't corrupted.

### 8.1 Verify via Text Queries

```
What tasks did I complete today?
Show me all activity on the AgentOps project
List tasks with notes added today
```

### 8.2 Verify in MongoDB

```javascript
// Run in MongoDB shell or Compass

// Check task statuses updated
db.tasks.find({ status: "done" }).count()

// Check notes were added
db.tasks.find({ "notes.0": { $exists: true } }).count()

// Check activity logs exist
db.tasks.find({ "activity_log.action": "voice_update" }).count()

// Verify no corrupted embeddings
db.tasks.find({ embedding: { $size: 1024 } }).count()
```

---

## Quick Regression Test (5 minutes)

Run this sequence before any PR merge:

| # | Type | Test | Pass? |
|---|------|------|-------|
| 1 | Text | "What are my tasks?" | ☐ |
| 2 | Text | "Show me the AgentOps project" | ☐ |
| 3 | Text | "Find tasks about memory" | ☐ |
| 4 | Text | "Create a task called 'Test task' in AgentOps" | ☐ |
| 5 | Text | "Mark 'Test task' as done" | ☐ |
| 6 | 🎤 Voice | "What are my high priority tasks?" | ☐ |
| 7 | 🎤 Voice | "Quick note on the voice agent app: testing voice" | ☐ |
| 8 | 🎤 Voice | "I finished the debugging doc" | ☐ |
| 9 | Text | "Delete the test task" (or manual cleanup) | ☐ |
| 10 | Both | No errors in terminal | ☐ |

---

## Troubleshooting

### Voice Not Transcribing
```bash
# Test OpenAI key
python -c "from openai import OpenAI; c = OpenAI(); print('OK')"
```
- Check browser mic permissions
- Try different browser
- Check OpenAI API credits

### "Didn't find any specific actions"
- Voice parsing works but coordinator isn't routing to worklog
- Check logs for `parse_voice_input()` output
- Verify `_process_voice_input()` calls worklog methods

### Semantic Search Returns Nothing
- Check Atlas index name matches code: `vector_index`
- Verify index status is "READY" in Atlas UI
- Confirm tasks have `embedding` field with 1024 dimensions

### Duplicate Messages Appearing
- Streamlit audio input triggering twice
- Add session state deduplication

### API Error: "Extra inputs not permitted"
- `input_type` being passed to Anthropic API
- Clean messages before API call in `llm.py`

### Task Not Found (Fuzzy Match Failing)
- Check `fuzzy_match_task()` threshold (default 0.7)
- Verify task exists in database
- Check project context is being passed

---

## Sample Data Reference

Your test database contains:

| Project | Tasks | Status Mix |
|---------|-------|------------|
| AgentOps Framework | 5 | Mixed |
| Memory Engineering Content | 4 | Mixed |
| LangGraph Integration | 4 | Mixed |
| Voice Agent Architecture | 5 | Mixed |
| Gaming NPC Demo | 6 | Mixed |
| AWS re:Invent Prep | 4 | Mixed |
| CrewAI Memory Patterns | 3 | Mixed |
| Education Adaptive Tutoring | 4 | Mixed |
| Q4 FY25 Deliverables | 4 | Archived |
| Developer Webinar Series | 5 | Mixed |

**Total:** 10 projects, 44 tasks

---

## Success Criteria

### Milestone 1 Complete ✓
- [ ] Text queries return correct results
- [ ] Semantic search finds related tasks
- [ ] Task CRUD operations work
- [ ] Conversation history maintained

### Milestone 2 Complete ✓
- [ ] Voice transcription works
- [ ] Voice queries return same results as text
- [ ] "I finished X" marks task complete
- [ ] "I'm working on X" marks task in_progress
- [ ] "Note on X: Y" adds note to task
- [ ] Fuzzy matching handles informal references
- [ ] Ambiguous references prompt clarification
- [ ] Activity logs capture voice updates with raw transcript

---

*Last updated: January 2026*
*Flow Companion v2.0 - Milestones 1 & 2*