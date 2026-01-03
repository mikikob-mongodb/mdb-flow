# Flow Companion Test Suite
## Complete Testing for Milestones 1 & 2

---

## Test Categories Overview

| Category | M1 | M2 | Count |
|----------|----|----|-------|
| Database & Connection | ✓ | | 8 |
| Retrieval Agent | ✓ | | 18 |
| Worklog Agent | ✓ | | 12 |
| Coordinator Agent | ✓ | ✓ | 20 |
| Vector Search | ✓ | | 10 |
| Hybrid Search | ✓ | ✓ | 12 |
| Text Input | ✓ | | 15 |
| Voice Input | | ✓ | 15 |
| Multi-turn Conversations | ✓ | ✓ | 12 |
| Temporal Queries | ✓ | | 10 |
| Task Confirmation Flow | | ✓ | 8 |
| Response Formatting | ✓ | | 8 |
| Debug Panel | ✓ | ✓ | 10 |
| Backslash Commands | ✓ | | 40 |
| Performance / Latency | ✓ | ✓ | 12 |
| Error Handling | ✓ | ✓ | 10 |
| **TOTAL** | | | **~210** |

---

## SECTION 1: Database & Connection Tests

### 1.1 MongoDB Connection
```python
def test_mongodb_connection():
    """Verify MongoDB Atlas connection works"""
    # Expected: Connection successful, no timeout
    assert db.command("ping")["ok"] == 1

def test_database_exists():
    """Verify flow_companion database exists"""
    assert "flow_companion" in client.list_database_names()

def test_collections_exist():
    """Verify required collections exist"""
    collections = db.list_collection_names()
    assert "tasks" in collections
    assert "projects" in collections
```

### 1.2 Indexes
```python
def test_vector_index_tasks():
    """Verify vector search index on tasks"""
    # Check index exists and is READY
    
def test_vector_index_projects():
    """Verify vector search index on projects"""

def test_text_index_tasks():
    """Verify full-text search index on tasks"""

def test_text_index_projects():
    """Verify full-text search index on projects"""
```

### 1.3 Sample Data
```python
def test_tasks_have_data():
    """Verify tasks collection has documents"""
    count = db.tasks.count_documents({})
    assert count >= 40

def test_projects_have_data():
    """Verify projects collection has documents"""
    count = db.projects.count_documents({})
    assert count >= 10

def test_tasks_have_embeddings():
    """Verify tasks have embedding field"""
    task = db.tasks.find_one({"embedding": {"$exists": True}})
    assert task is not None
    assert len(task["embedding"]) == 1024  # Voyage embedding size
```

---

## SECTION 2: Retrieval Agent Tests

### 2.1 Basic Queries
```python
def test_get_all_tasks():
    """Get all tasks without filters"""
    tasks = retrieval.get_tasks()
    assert len(tasks) > 0
    assert all("title" in t for t in tasks)

def test_get_tasks_by_status_todo():
    """Filter tasks by status=todo"""
    tasks = retrieval.get_tasks(status="todo")
    assert all(t["status"] == "todo" for t in tasks)

def test_get_tasks_by_status_in_progress():
    """Filter tasks by status=in_progress"""
    tasks = retrieval.get_tasks(status="in_progress")
    assert all(t["status"] == "in_progress" for t in tasks)

def test_get_tasks_by_status_done():
    """Filter tasks by status=done"""
    tasks = retrieval.get_tasks(status="done")
    assert all(t["status"] == "done" for t in tasks)

def test_get_tasks_by_priority():
    """Filter tasks by priority"""
    tasks = retrieval.get_tasks(priority="high")
    assert all(t.get("priority") == "high" for t in tasks)

def test_get_tasks_by_project():
    """Filter tasks by project"""
    tasks = retrieval.get_tasks(project_name="AgentOps")
    assert len(tasks) > 0
    assert len(tasks) < 10  # Should be subset

def test_get_tasks_combined_filters():
    """Filter tasks by multiple criteria"""
    tasks = retrieval.get_tasks(status="in_progress", priority="high")
    assert all(t["status"] == "in_progress" and t.get("priority") == "high" for t in tasks)
```

### 2.2 Project Queries
```python
def test_get_all_projects():
    """Get all projects"""
    projects = retrieval.get_projects()
    assert len(projects) == 10

def test_get_project_by_name():
    """Get specific project by name"""
    project = retrieval.get_project_by_name("AgentOps")
    assert project is not None
    assert "AgentOps" in project["name"]

def test_get_project_with_tasks():
    """Get project with its tasks"""
    result = retrieval.get_project_with_tasks("AgentOps")
    assert "project" in result
    assert "tasks" in result
    assert len(result["tasks"]) > 0

def test_get_projects_with_stats():
    """Get projects with task counts"""
    projects = retrieval.get_projects_with_stats()
    assert all("todo_count" in p for p in projects)
    assert all("in_progress_count" in p for p in projects)
    assert all("done_count" in p for p in projects)
```

### 2.3 Task-Project Joins
```python
def test_tasks_include_project_name():
    """Tasks should have project_name resolved from project_id"""
    tasks = retrieval.get_tasks_with_project_names()
    tasks_with_project = [t for t in tasks if t.get("project_id")]
    assert all("project_name" in t for t in tasks_with_project)
```

---

## SECTION 3: Worklog Agent Tests

### 3.1 Status Updates
```python
def test_complete_task():
    """Mark a task as complete"""
    task = db.tasks.find_one({"status": "in_progress"})
    result = worklog.complete_task(task["_id"])
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert updated["status"] == "done"

def test_start_task():
    """Mark a task as in_progress"""
    task = db.tasks.find_one({"status": "todo"})
    result = worklog.start_task(task["_id"])
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert updated["status"] == "in_progress"

def test_stop_task():
    """Mark a task back to todo"""
    task = db.tasks.find_one({"status": "in_progress"})
    result = worklog.stop_task(task["_id"])
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert updated["status"] == "todo"
```

### 3.2 Notes
```python
def test_add_note():
    """Add a note to a task"""
    task = db.tasks.find_one({})
    original_notes = len(task.get("notes", []))
    worklog.add_note(task["_id"], "Test note")
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert len(updated.get("notes", [])) == original_notes + 1

def test_note_has_timestamp():
    """Notes should have timestamps"""
    task = db.tasks.find_one({})
    worklog.add_note(task["_id"], "Test note with timestamp")
    updated = db.tasks.find_one({"_id": task["_id"]})
    latest_note = updated["notes"][-1]
    assert "timestamp" in latest_note or "created_at" in latest_note
```

### 3.3 Activity Log
```python
def test_activity_log_on_complete():
    """Completing a task adds activity log entry"""
    task = db.tasks.find_one({"status": "in_progress"})
    worklog.complete_task(task["_id"])
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert any(a["action"] == "completed" for a in updated.get("activity_log", []))

def test_activity_log_on_start():
    """Starting a task adds activity log entry"""
    task = db.tasks.find_one({"status": "todo"})
    worklog.start_task(task["_id"])
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert any(a["action"] == "started" for a in updated.get("activity_log", []))

def test_activity_log_on_note():
    """Adding a note adds activity log entry"""
    task = db.tasks.find_one({})
    worklog.add_note(task["_id"], "Test note")
    updated = db.tasks.find_one({"_id": task["_id"]})
    assert any(a["action"] == "note_added" for a in updated.get("activity_log", []))

def test_activity_log_has_timestamp():
    """Activity log entries have timestamps"""
    task = db.tasks.find_one({"activity_log": {"$exists": True, "$ne": []}})
    assert all("timestamp" in a for a in task["activity_log"])
```

### 3.4 Task Creation
```python
def test_create_task():
    """Create a new task"""
    result = worklog.create_task(
        title="Test Task",
        project_id=None,
        priority="medium"
    )
    assert result is not None
    task = db.tasks.find_one({"title": "Test Task"})
    assert task is not None

def test_create_task_with_project():
    """Create task associated with a project"""
    project = db.projects.find_one({})
    result = worklog.create_task(
        title="Test Task with Project",
        project_id=project["_id"]
    )
    task = db.tasks.find_one({"title": "Test Task with Project"})
    assert task["project_id"] == project["_id"]
```

---

## SECTION 4: Vector Search Tests

### 4.1 Basic Vector Search
```python
def test_vector_search_tasks():
    """Vector search returns results"""
    results = retrieval.vector_search_tasks("debugging")
    assert len(results) > 0

def test_vector_search_returns_scores():
    """Vector search results have scores"""
    results = retrieval.vector_search_tasks("debugging")
    assert all("score" in r for r in results)

def test_vector_search_sorted_by_score():
    """Results sorted by relevance score descending"""
    results = retrieval.vector_search_tasks("debugging")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_vector_search_respects_limit():
    """Vector search respects limit parameter"""
    results = retrieval.vector_search_tasks("debugging", limit=3)
    assert len(results) <= 3
```

### 4.2 Semantic Relevance
```python
def test_vector_search_semantic_match():
    """Vector search finds semantically related results"""
    results = retrieval.vector_search_tasks("observability tools")
    # Should find debugging/monitoring related tasks
    titles = [r["title"].lower() for r in results]
    assert any("debug" in t or "monitor" in t or "observ" in t for t in titles)

def test_vector_search_synonym():
    """Vector search handles synonyms"""
    results = retrieval.vector_search_tasks("documentation")
    titles = [r["title"].lower() for r in results]
    assert any("doc" in t for t in titles)
```

### 4.3 Embedding Generation
```python
def test_embed_text():
    """Embedding generation works"""
    embedding = retrieval.embed_text("test query")
    assert len(embedding) == 1024
    assert all(isinstance(x, float) for x in embedding)

def test_embed_text_different_inputs():
    """Different inputs produce different embeddings"""
    emb1 = retrieval.embed_text("debugging")
    emb2 = retrieval.embed_text("webinar")
    assert emb1 != emb2
```

---

## SECTION 5: Hybrid Search Tests

### 5.1 Basic Hybrid Search
```python
def test_hybrid_search_tasks():
    """Hybrid search returns results"""
    results = retrieval.hybrid_search_tasks("debugging doc")
    assert len(results) > 0

def test_hybrid_search_projects():
    """Hybrid search on projects works"""
    results = retrieval.hybrid_search_projects("memory")
    assert len(results) > 0

def test_hybrid_search_uses_rankfusion():
    """Verify $rankFusion is being used (check query plan or timing)"""
    # This is more of an integration test
    pass
```

### 5.2 Hybrid vs Vector vs Text
```python
def test_hybrid_finds_exact_match():
    """Hybrid search finds exact text matches"""
    results = retrieval.hybrid_search_tasks("checkpointer")
    titles = [r["title"].lower() for r in results]
    assert any("checkpointer" in t for t in titles)

def test_hybrid_finds_semantic_match():
    """Hybrid search finds semantic matches"""
    results = retrieval.hybrid_search_tasks("monitoring and observability")
    # Should find debugging-related even without exact word match
    assert len(results) > 0

def test_text_only_search():
    """Text-only search returns exact matches"""
    results = retrieval.text_search_tasks("checkpointer")
    titles = [r["title"].lower() for r in results]
    assert all("checkpointer" in t for t in titles)

def test_vector_only_search():
    """Vector-only search returns semantic matches"""
    results = retrieval.vector_search_tasks("how to find bugs")
    assert len(results) > 0
```

### 5.3 Informal References (M2)
```python
def test_hybrid_matches_informal_reference():
    """Hybrid search matches informal task references"""
    # "the debugging doc" should match "Create debugging methodologies doc"
    results = retrieval.hybrid_search_tasks("the debugging doc")
    assert any("debugging" in r["title"].lower() for r in results)

def test_hybrid_matches_partial_name():
    """Hybrid search matches partial task names"""
    results = retrieval.hybrid_search_tasks("checkpointer task")
    assert any("checkpointer" in r["title"].lower() for r in results)

def test_hybrid_matches_project_reference():
    """Hybrid search matches informal project references"""
    results = retrieval.hybrid_search_projects("voice stuff")
    assert any("voice" in r["name"].lower() for r in results)
```

---

## SECTION 6: Coordinator Agent Tests

### 6.1 Tool Selection
```python
def test_coordinator_selects_get_tasks():
    """Coordinator uses get_tasks for list queries"""
    result = coordinator.process("What are my tasks?", [])
    # Check debug panel shows get_tasks was called
    assert "get_tasks" in get_last_tool_calls()

def test_coordinator_selects_search_tasks():
    """Coordinator uses search_tasks for search queries"""
    result = coordinator.process("Find tasks about debugging", [])
    assert "search_tasks" in get_last_tool_calls()

def test_coordinator_selects_complete_task():
    """Coordinator uses complete_task for completion requests"""
    result = coordinator.process("Mark the debugging doc as done", [])
    assert "search_tasks" in get_last_tool_calls()  # First searches
    # Then completes (may require confirmation)

def test_coordinator_selects_add_note():
    """Coordinator uses add_note for note requests"""
    result = coordinator.process("Add a note to voice agent: test note", [])
    assert "add_note" in get_last_tool_calls()
```

### 6.2 Query Handling
```python
def test_coordinator_handles_status_filter():
    """Coordinator correctly filters by status"""
    result = coordinator.process("Show me tasks in progress", [])
    # Result should only contain in_progress tasks

def test_coordinator_handles_project_filter():
    """Coordinator correctly filters by project"""
    result = coordinator.process("What's in the AgentOps project?", [])
    # Result should only contain AgentOps tasks

def test_coordinator_handles_priority_filter():
    """Coordinator correctly filters by priority"""
    result = coordinator.process("Show me high priority tasks", [])
    # Result should only contain high priority tasks

def test_coordinator_handles_combined_query():
    """Coordinator handles multiple filters"""
    result = coordinator.process("High priority tasks in AgentOps", [])
    # Result should match both filters
```

### 6.3 Action Handling
```python
def test_coordinator_completes_task():
    """Coordinator can complete a task end-to-end"""
    # Setup: ensure task exists
    result = coordinator.process("Complete the test task", [])
    # Verify task status changed

def test_coordinator_starts_task():
    """Coordinator can start a task"""
    result = coordinator.process("Start working on the test task", [])
    # Verify task status is in_progress

def test_coordinator_adds_note():
    """Coordinator can add a note"""
    result = coordinator.process("Add a note to test task: this is a test", [])
    # Verify note was added
```

### 6.4 Voice vs Text Parity (M2)
```python
def test_voice_and_text_same_result():
    """Voice and text input produce same results"""
    text_result = coordinator.process("What are my tasks?", [], input_type="text")
    voice_result = coordinator.process("What are my tasks?", [], input_type="voice")
    # Both should return task list

def test_voice_query_uses_same_tools():
    """Voice queries use same tool path as text"""
    coordinator.process("Show me AgentOps", [], input_type="voice")
    voice_tools = get_last_tool_calls()
    coordinator.process("Show me AgentOps", [], input_type="text")
    text_tools = get_last_tool_calls()
    assert voice_tools == text_tools
```

---

## SECTION 7: Text Input Tests (M1)

### 7.1 Basic Queries
```python
def test_text_what_are_my_tasks():
    result = coordinator.process("What are my tasks?", [])
    assert "task" in result.lower()

def test_text_show_projects():
    result = coordinator.process("Show me all my projects", [])
    assert "project" in result.lower()

def test_text_tasks_in_progress():
    result = coordinator.process("What tasks are in progress?", [])
    assert "in progress" in result.lower() or "in_progress" in result.lower()
```

### 7.2 Semantic Queries
```python
def test_text_find_related():
    result = coordinator.process("Find tasks related to memory", [])
    assert len(result) > 0

def test_text_search_debugging():
    result = coordinator.process("Show me debugging tasks", [])
    assert "debug" in result.lower()
```

### 7.3 Action Requests
```python
def test_text_complete_request():
    result = coordinator.process("I finished the debugging doc", [])
    # Should either complete or ask for confirmation

def test_text_start_request():
    result = coordinator.process("I'm starting work on the checkpointer", [])
    # Should either start or ask for confirmation

def test_text_note_request():
    result = coordinator.process("Add a note to voice agent: WebSocket working", [])
    # Should add note or ask for confirmation
```

---

## SECTION 8: Voice Input Tests (M2)

### 8.1 Transcription
```python
def test_transcription_works():
    """Audio transcription returns text"""
    audio_bytes = load_test_audio("hello_test.wav")
    transcript = transcribe_audio(audio_bytes)
    assert len(transcript) > 0

def test_transcription_accuracy():
    """Transcription is reasonably accurate"""
    audio_bytes = load_test_audio("what_are_my_tasks.wav")
    transcript = transcribe_audio(audio_bytes)
    assert "task" in transcript.lower()
```

### 8.2 Voice Queries
```python
def test_voice_query_tasks():
    """Voice query for tasks works"""
    result = coordinator.process("What are my tasks?", [], input_type="voice")
    assert "task" in result.lower()

def test_voice_query_project():
    """Voice query for project works"""
    result = coordinator.process("Show me the AgentOps project", [], input_type="voice")
    assert "agentops" in result.lower()

def test_voice_search():
    """Voice search works"""
    result = coordinator.process("Find tasks about debugging", [], input_type="voice")
    assert len(result) > 0
```

### 8.3 Voice Actions
```python
def test_voice_completion():
    """Voice task completion works"""
    result = coordinator.process("I just finished the debugging doc", [], input_type="voice")
    # Should search and ask for confirmation or complete

def test_voice_start_task():
    """Voice start task works"""
    result = coordinator.process("I'm working on the checkpointer now", [], input_type="voice")
    # Should search and ask for confirmation or start

def test_voice_add_note():
    """Voice note addition works"""
    result = coordinator.process("Quick note on voice agent app: got streaming working", [], input_type="voice")
    # Should add note or ask for confirmation
```

### 8.4 Informal References
```python
def test_voice_informal_task_reference():
    """Voice handles informal task names"""
    result = coordinator.process("I finished the debugging doc", [], input_type="voice")
    # Should find "Create debugging methodologies doc"

def test_voice_partial_name():
    """Voice handles partial task names"""
    result = coordinator.process("The checkpointer task is done", [], input_type="voice")
    # Should find checkpointer-related task

def test_voice_with_filler_words():
    """Voice handles filler words"""
    result = coordinator.process("Um, so I finished, uh, the debugging doc", [], input_type="voice")
    # Should still understand intent
```

---

## SECTION 9: Multi-turn Conversation Tests

### 9.1 Context Retention
```python
def test_context_project_retained():
    """Project context retained across turns"""
    coordinator.process("Show me the AgentOps project", [])
    result = coordinator.process("What's the highest priority task?", history)
    # Should answer about AgentOps, not all projects

def test_context_task_retained():
    """Task context retained across turns"""
    coordinator.process("Find the checkpointer task", [])
    result = coordinator.process("What's its status?", history)
    # Should answer about checkpointer

def test_context_5_turns():
    """Context maintained for 5+ turns"""
    history = []
    coordinator.process("Show me AgentOps", history)
    coordinator.process("What's in progress?", history)
    coordinator.process("Any high priority?", history)
    coordinator.process("Add a note to the first one: test", history)
    result = coordinator.process("What did I just do?", history)
    # Should remember the note was added
```

### 9.2 Disambiguation
```python
def test_disambiguation_multiple_matches():
    """Agent asks for clarification with multiple matches"""
    result = coordinator.process("I finished the webinar task", [])
    # Should ask which webinar (Jan, Feb, March)
    assert "which" in result.lower() or "1." in result

def test_disambiguation_followup():
    """Agent handles disambiguation followup"""
    coordinator.process("I finished the webinar task", [])
    result = coordinator.process("The February one", history)
    # Should complete February webinar task

def test_disambiguation_by_number():
    """Agent handles selection by number"""
    coordinator.process("Complete the doc task", [])
    result = coordinator.process("2", history)
    # Should complete second option
```

### 9.3 Mixed Voice/Text
```python
def test_mixed_voice_then_text():
    """Voice query followed by text works"""
    coordinator.process("Show me AgentOps", [], input_type="voice")
    result = coordinator.process("What's high priority?", history, input_type="text")
    # Context should be retained

def test_mixed_text_then_voice():
    """Text query followed by voice works"""
    coordinator.process("Show me AgentOps", [], input_type="text")
    result = coordinator.process("Complete the first task", history, input_type="voice")
    # Context should be retained
```

---

## SECTION 10: Temporal Query Tests

### 10.1 Relative Time
```python
def test_temporal_today():
    """Query for today's activity"""
    result = coordinator.process("What did I work on today?", [])
    # Should return tasks with today's activity

def test_temporal_yesterday():
    """Query for yesterday's activity"""
    result = coordinator.process("What did I do yesterday?", [])
    # Should return tasks with yesterday's activity

def test_temporal_this_week():
    """Query for this week's activity"""
    result = coordinator.process("Show me tasks from this week", [])
    # Should return tasks with this week's activity
```

### 10.2 Activity-Based
```python
def test_temporal_completed_today():
    """Query for tasks completed today"""
    result = coordinator.process("What did I complete today?", [])
    # Should return only tasks completed today

def test_temporal_started_this_week():
    """Query for tasks started this week"""
    result = coordinator.process("What tasks did I start this week?", [])
    # Should return tasks started this week

def test_temporal_stale():
    """Query for stale tasks"""
    result = coordinator.process("What tasks have been in progress for too long?", [])
    # Should return in_progress tasks > 7 days
```

---

## SECTION 11: Confirmation Flow Tests (M2)

### 11.1 Single Match
```python
def test_confirm_single_match():
    """Single match still asks for confirmation"""
    result = coordinator.process("Complete the MongoDB checkpointer task", [])
    # Should ask "Is this the task you want to complete?"

def test_confirm_yes():
    """Confirmation with 'yes' works"""
    coordinator.process("Complete the MongoDB checkpointer task", [])
    result = coordinator.process("Yes", history)
    # Should complete the task
```

### 11.2 Multiple Matches
```python
def test_confirm_multiple_shows_options():
    """Multiple matches shows numbered options"""
    result = coordinator.process("Complete the webinar task", [])
    assert "1." in result and "2." in result

def test_confirm_by_number():
    """Selection by number works"""
    coordinator.process("Complete the webinar task", [])
    result = coordinator.process("2", history)
    # Should complete second option

def test_confirm_by_name():
    """Selection by name works"""
    coordinator.process("Complete the webinar task", [])
    result = coordinator.process("The February one", history)
    # Should complete February webinar
```

### 11.3 Cancellation
```python
def test_confirm_cancel():
    """User can cancel action"""
    coordinator.process("Complete the debugging doc", [])
    result = coordinator.process("No, cancel", history)
    # Should not complete, acknowledge cancellation
```

---

## SECTION 12: Response Formatting Tests

### 12.1 Task List Format
```python
def test_format_task_list_headers():
    """Task list has proper headers"""
    result = coordinator.process("What are my tasks?", [])
    assert "In Progress" in result or "To Do" in result

def test_format_task_list_grouped():
    """Tasks grouped by status"""
    result = coordinator.process("What are my tasks?", [])
    # Should have sections for each status

def test_format_includes_project():
    """Task list shows project names"""
    result = coordinator.process("What are my tasks?", [])
    # Project names should appear
```

### 12.2 Confirmation Format
```python
def test_format_completion_confirmation():
    """Completion shows nice confirmation"""
    # After completing a task
    assert "✓" in result or "complete" in result.lower()

def test_format_shows_project_in_confirmation():
    """Confirmation includes project name"""
    # After completing a task
    assert "Project:" in result or project_name in result
```

---

## SECTION 13: Debug Panel Tests

### 13.1 Tool Call Tracking
```python
def test_debug_shows_tool_calls():
    """Debug panel shows tool calls"""
    coordinator.process("What are my tasks?", [])
    debug = get_debug_panel_data()
    assert len(debug["tool_calls"]) > 0

def test_debug_shows_timing():
    """Debug panel shows timing"""
    coordinator.process("What are my tasks?", [])
    debug = get_debug_panel_data()
    assert debug["tool_calls"][0]["duration_ms"] > 0

def test_debug_shows_input_output():
    """Debug panel shows input and output"""
    coordinator.process("What are my tasks?", [])
    debug = get_debug_panel_data()
    assert "input" in debug["tool_calls"][0]
    assert "output" in debug["tool_calls"][0]
```

### 13.2 Latency Breakdown
```python
def test_debug_shows_breakdown():
    """Debug panel shows latency breakdown"""
    coordinator.process("Find tasks about debugging", [])
    debug = get_debug_panel_data()
    breakdown = debug["tool_calls"][0].get("breakdown", {})
    assert "mongodb_query" in breakdown or "embedding" in breakdown

def test_debug_shows_llm_time():
    """Debug panel shows LLM thinking time"""
    coordinator.process("What are my tasks?", [])
    debug = get_debug_panel_data()
    assert debug.get("llm_time_ms", 0) > 0
```

### 13.3 Turn History
```python
def test_debug_tracks_turns():
    """Debug panel tracks conversation turns"""
    coordinator.process("What are my tasks?", [])
    coordinator.process("Show me AgentOps", history)
    debug = get_debug_panel_data()
    assert len(debug["turns"]) >= 2

def test_debug_clear_history():
    """Debug panel can clear history"""
    # Clear and verify
```

---

## SECTION 14: Backslash Command Tests

See separate file: SLASH_COMMAND_TESTS.md

Key tests:
- /tasks returns all tasks
- /tasks status:X filters correctly
- /tasks project:X filters correctly
- /tasks search X uses hybrid search
- /projects returns all projects
- /projects X returns single project
- /bench all returns timing data
- All commands return formatted tables (not JSON)
- No empty columns when data exists

---

## SECTION 15: Performance Tests

### 15.1 Latency Targets
```python
def test_latency_get_tasks():
    """get_tasks under 200ms"""
    start = time.time()
    retrieval.get_tasks()
    duration = (time.time() - start) * 1000
    assert duration < 200

def test_latency_get_projects():
    """get_projects under 200ms"""
    start = time.time()
    retrieval.get_projects()
    duration = (time.time() - start) * 1000
    assert duration < 200

def test_latency_hybrid_search():
    """hybrid_search under 1000ms"""
    start = time.time()
    retrieval.hybrid_search_tasks("debugging")
    duration = (time.time() - start) * 1000
    assert duration < 1000

def test_latency_complete_task():
    """complete_task under 500ms"""
    task = db.tasks.find_one({"status": "in_progress"})
    start = time.time()
    worklog.complete_task(task["_id"])
    duration = (time.time() - start) * 1000
    assert duration < 500
```

### 15.2 No Unnecessary Embedding
```python
def test_get_tasks_no_embedding():
    """get_tasks doesn't generate embeddings"""
    start = time.time()
    retrieval.get_tasks()
    duration = (time.time() - start) * 1000
    # Should be fast - no embedding generation
    assert duration < 200

def test_complete_task_no_embedding():
    """complete_task doesn't regenerate embeddings"""
    task = db.tasks.find_one({})
    start = time.time()
    worklog.complete_task(task["_id"])
    duration = (time.time() - start) * 1000
    assert duration < 500  # Would be 2000+ with embedding
```

---

## SECTION 16: Error Handling Tests

### 16.1 Invalid Input
```python
def test_empty_query():
    """Empty query handled gracefully"""
    result = coordinator.process("", [])
    # Should ask for input or provide help

def test_nonsense_query():
    """Nonsense query handled gracefully"""
    result = coordinator.process("asdfghjkl", [])
    # Should ask for clarification

def test_invalid_slash_command():
    """Invalid slash command handled"""
    result = execute_slash_command("/invalid")
    assert "error" in result.lower() or "unknown" in result.lower()
```

### 16.2 Not Found
```python
def test_task_not_found():
    """Non-existent task handled gracefully"""
    result = coordinator.process("Complete the blockchain migration task", [])
    assert "not found" in result.lower() or "couldn't find" in result.lower()

def test_project_not_found():
    """Non-existent project handled gracefully"""
    result = coordinator.process("Show me the Kubernetes project", [])
    assert "not found" in result.lower() or "couldn't find" in result.lower()
```

### 16.3 API Errors
```python
def test_handles_db_timeout():
    """Database timeout handled gracefully"""
    # Mock timeout and verify graceful handling

def test_handles_embedding_error():
    """Embedding API error handled gracefully"""
    # Mock error and verify graceful handling
```

---

## Test Execution Summary

```python
def run_all_tests():
    """Run complete test suite"""
    sections = [
        ("Database & Connection", test_database_section),
        ("Retrieval Agent", test_retrieval_section),
        ("Worklog Agent", test_worklog_section),
        ("Vector Search", test_vector_section),
        ("Hybrid Search", test_hybrid_section),
        ("Coordinator Agent", test_coordinator_section),
        ("Text Input", test_text_section),
        ("Voice Input", test_voice_section),
        ("Multi-turn", test_multiturn_section),
        ("Temporal Queries", test_temporal_section),
        ("Confirmation Flow", test_confirmation_section),
        ("Formatting", test_formatting_section),
        ("Debug Panel", test_debug_section),
        ("Backslash Commands", test_slash_section),
        ("Performance", test_performance_section),
        ("Error Handling", test_error_section),
    ]
    
    results = {}
    for name, test_fn in sections:
        results[name] = test_fn()
    
    # Print summary
    total_pass = sum(r["passed"] for r in results.values())
    total_fail = sum(r["failed"] for r in results.values())
    
    print(f"TOTAL: {total_pass} passed, {total_fail} failed")
    
    return results
```

---

*Flow Companion v2.0 — Complete Test Suite*
*Milestones 1 & 2*