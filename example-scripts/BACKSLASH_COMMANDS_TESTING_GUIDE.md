# Backslash Commands Test Specification
## Automated Testing for Flow Companion Slash Commands

Use this document to test all slash commands and verify they return correct results.

---

## Test Runner Instructions

For each test:
1. Run the command
2. Verify the result matches expected output
3. Check for empty columns that should have data
4. Report PASS/FAIL with details

```python
def run_slash_command_tests():
    """Run all slash command tests and report results"""
    results = []
    for test in TESTS:
        result = execute_slash_command(test["command"])
        passed = validate_result(result, test["expected"])
        results.append({
            "command": test["command"],
            "passed": passed,
            "details": result
        })
    return results
```

---

## Test Suite

### SECTION 1: /tasks - Basic Queries

#### Test 1.1: List all tasks
```
Command: /tasks
Expected:
  - Returns list of tasks (40-50 based on sample data)
  - Table has columns: #, Title, Status, Priority, Project, Last Activity
  - NO columns should be empty when data exists
  - Priority column should show "high", "medium", "low" or "-" (not blank)
  - Project column should show project NAME (not ID, not blank)
  - Last Activity should show readable date (e.g., "Jan 03")
Validate:
  - result["count"] > 0
  - All tasks have "title" field populated
  - Tasks with project_id have project_name resolved
  - Tasks with priority field show priority value
```

#### Test 1.2: Filter by status - todo
```
Command: /tasks status:todo
Expected:
  - Returns ONLY tasks where status == "todo"
  - Count should be less than total tasks
  - Every row in result has status "todo"
Validate:
  - All returned tasks have status == "todo"
  - result["count"] < total_task_count
  - result["count"] should be approximately 25-30
```

#### Test 1.3: Filter by status - in_progress
```
Command: /tasks status:in_progress
Expected:
  - Returns ONLY tasks where status == "in_progress"
  - Count should be approximately 10-15
Validate:
  - All returned tasks have status == "in_progress"
```

#### Test 1.4: Filter by status - done
```
Command: /tasks status:done
Expected:
  - Returns ONLY tasks where status == "done"
  - Count should be approximately 10-15
Validate:
  - All returned tasks have status == "done"
```

#### Test 1.5: Filter by priority - high
```
Command: /tasks priority:high
Expected:
  - Returns ONLY tasks where priority == "high"
  - Count should be approximately 10-15
  - Every row shows "high" in Priority column
Validate:
  - All returned tasks have priority == "high"
  - result["count"] < total_task_count
```

#### Test 1.6: Filter by priority - medium
```
Command: /tasks priority:medium
Expected:
  - Returns ONLY tasks where priority == "medium"
Validate:
  - All returned tasks have priority == "medium"
```

#### Test 1.7: Filter by project
```
Command: /tasks project:AgentOps
Expected:
  - Returns ONLY tasks belonging to AgentOps project
  - Count should be approximately 5-8
  - Every row shows "AgentOps" (or full name) in Project column
Validate:
  - All returned tasks have project_name containing "AgentOps"
  - result["count"] should be 5-10
```

#### Test 1.8: Filter by project with spaces
```
Command: /tasks project:"Voice Agent"
Expected:
  - Returns ONLY tasks belonging to Voice Agent project
  - Handles quoted project name correctly
Validate:
  - All returned tasks have project_name containing "Voice Agent"
```

#### Test 1.9: Combined filters - status + priority
```
Command: /tasks status:in_progress priority:high
Expected:
  - Returns tasks that are BOTH in_progress AND high priority
  - Count should be less than either filter alone
Validate:
  - All tasks have status == "in_progress" AND priority == "high"
  - result["count"] < /tasks status:in_progress count
  - result["count"] < /tasks priority:high count
```

#### Test 1.10: Combined filters - project + status
```
Command: /tasks project:AgentOps status:todo
Expected:
  - Returns tasks in AgentOps that are todo
  - Count should be 1-3
Validate:
  - All tasks have project containing "AgentOps" AND status == "todo"
```

---

### SECTION 2: /tasks search - Hybrid Search

#### Test 2.1: Search for debugging
```
Command: /tasks search debugging
Expected:
  - Returns 3-10 tasks related to debugging
  - Results should include "Create debugging methodologies doc"
  - Results should have relevance scores
  - Sorted by score descending
Validate:
  - result["count"] > 0 and result["count"] < 15
  - At least one result contains "debug" in title
  - Results have "score" field
```

#### Test 2.2: Search for voice agent
```
Command: /tasks search voice agent app
Expected:
  - Returns tasks related to voice/agent
  - Should include "Build voice agent reference app"
Validate:
  - At least one result contains "voice" in title
```

#### Test 2.3: Search for checkpointer
```
Command: /tasks search checkpointer
Expected:
  - Returns tasks related to checkpointer
  - Should include LangGraph checkpointer task
Validate:
  - At least one result contains "checkpointer" in title
```

#### Test 2.4: Search for memory
```
Command: /tasks search memory patterns
Expected:
  - Returns tasks related to memory
  - Should find memory-related tasks across projects
Validate:
  - Results contain memory-related tasks
  - result["count"] > 0
```

---

### SECTION 3: /tasks - Temporal Queries

#### Test 3.1: Tasks today
```
Command: /tasks today
Expected:
  - Returns tasks with activity_log entries from today
  - Uses correct date (current date, not future)
  - Last Activity column shows today's date
Validate:
  - All returned tasks have activity within today
  - Dates are not in the future
  - If no activity today, returns empty with message
```

#### Test 3.2: Tasks yesterday
```
Command: /tasks yesterday
Expected:
  - Returns tasks with activity_log entries from yesterday
Validate:
  - All returned tasks have activity from yesterday
```

#### Test 3.3: Tasks this week
```
Command: /tasks this_week
Expected:
  - Returns tasks with activity since Monday of current week
Validate:
  - All returned tasks have activity within this week
```

#### Test 3.4: Completed today
```
Command: /tasks completed:today
Expected:
  - Returns tasks where activity_log has action="completed" today
  - Only shows tasks completed TODAY, not all completed tasks
Validate:
  - All returned tasks have completion activity today
  - result["count"] <= total done tasks
```

#### Test 3.5: Completed this week
```
Command: /tasks completed:this_week
Expected:
  - Returns tasks completed this week only
Validate:
  - All returned tasks have completion activity this week
```

#### Test 3.6: Stale tasks
```
Command: /tasks stale
Expected:
  - Returns tasks that are "in_progress" for more than 7 days
  - Does NOT return todo or done tasks
Validate:
  - All returned tasks have status == "in_progress"
  - All returned tasks have been in_progress > 7 days
```

---

### SECTION 4: /projects - Basic Queries

#### Test 4.1: List all projects
```
Command: /projects
Expected:
  - Returns all 10 projects
  - Table has columns: #, Name, Description, Todo, In Progress, Done, Total
  - Task counts are accurate
Validate:
  - result["count"] == 10
  - Each project has task counts that sum to Total
```

#### Test 4.2: Get specific project - AgentOps
```
Command: /projects AgentOps
Expected:
  - Returns ONLY AgentOps project details
  - Shows project info + its tasks
  - Does NOT return all 10 projects
Validate:
  - Returns single project
  - Project name contains "AgentOps"
  - Includes list of tasks belonging to that project
```

#### Test 4.3: Get specific project - quoted name
```
Command: /projects "Voice Agent"
Expected:
  - Returns Voice Agent project details
  - Handles spaces in name correctly
Validate:
  - Returns single project with "Voice Agent" in name
```

#### Test 4.4: Get specific project - LangGraph
```
Command: /projects LangGraph
Expected:
  - Returns LangGraph project
Validate:
  - Returns single project containing "LangGraph"
```

#### Test 4.5: Project stats
```
Command: /projects AgentOps stats
Expected:
  - Returns AgentOps with detailed statistics
  - NOT all 10 projects
Validate:
  - Returns single project stats
  - Includes todo/in_progress/done counts
```

---

### SECTION 5: /projects search - Hybrid Search

#### Test 5.1: Search projects - memory
```
Command: /projects search memory
Expected:
  - Returns projects related to memory
  - Should find "Memory Engineering Content" and possibly "CrewAI Memory Patterns"
  - Does NOT return all 10 projects
  - Table shows project columns (Name, Description) not task columns
Validate:
  - result["count"] < 10
  - Results contain "memory" in name or description
  - Columns are: #, Name, Description, Status, Score (NOT Title, Priority, Project)
```

#### Test 5.2: Search projects - webinar
```
Command: /projects search webinar
Expected:
  - Returns projects related to webinar
  - Should find "Developer Webinar Series"
Validate:
  - Results contain "webinar" in name or description
  - result["count"] < 5
```

#### Test 5.3: Search projects - voice
```
Command: /projects search voice
Expected:
  - Returns projects related to voice
  - Should find "Voice Agent Architecture" or similar
Validate:
  - Results contain "voice" in name or description
```

---

### SECTION 6: /search - Direct Search

#### Test 6.1: Default search (hybrid)
```
Command: /search debugging
Expected:
  - Hybrid search across tasks
  - Returns results with scores
Validate:
  - Returns results with relevance scores
```

#### Test 6.2: Tasks search
```
Command: /search tasks checkpointer
Expected:
  - Searches tasks collection only
Validate:
  - Results are tasks
```

#### Test 6.3: Projects search
```
Command: /search projects gaming
Expected:
  - Searches projects collection only
Validate:
  - Results are projects (have "name" field not "title")
```

#### Test 6.4: Vector only search
```
Command: /search vector observability
Expected:
  - Uses vector search only (no text matching)
  - May find semantically related results
Validate:
  - Returns results
  - Should find conceptually related items
```

#### Test 6.5: Text only search
```
Command: /search text checkpointer
Expected:
  - Uses text search only (no vector/semantic)
  - Exact/fuzzy text matching
Validate:
  - Results contain "checkpointer" in text
```

---

### SECTION 7: /do - Task Actions

#### Test 7.1: Complete a task
```
Command: /do complete debugging doc
Expected:
  - Finds task matching "debugging doc"
  - Marks it as complete
  - Shows confirmation with project name
Validate:
  - Task status changed to "done"
  - Confirmation shows task title and project
  - Activity log updated with "completed" action
```

#### Test 7.2: Start a task
```
Command: /do start checkpointer
Expected:
  - Finds task matching "checkpointer"
  - Marks it as in_progress
Validate:
  - Task status changed to "in_progress"
  - Activity log updated with "started" action
```

#### Test 7.3: Add a note
```
Command: /do note voice agent "WebSocket streaming implemented"
Expected:
  - Finds task matching "voice agent"
  - Adds note to task
Validate:
  - Note added to task's notes array
  - Activity log has "note_added" entry
```

#### Test 7.4: Ambiguous task reference
```
Command: /do complete webinar
Expected:
  - Multiple webinar tasks exist
  - Should ask for clarification OR show options
  - Should NOT complete random task
Validate:
  - Either asks "which one?" or shows numbered options
  - Does not auto-complete without confirmation
```

---

### SECTION 8: /bench - Benchmarks

#### Test 8.1: Benchmark all
```
Command: /bench all
Expected:
  - Runs benchmarks for all operations
  - Shows table with Avg, Min, Max, P95
  - Operations: get_tasks, get_projects, search_tasks, complete_task
Validate:
  - All operations have timing data
  - get_tasks avg < 200ms
  - search_tasks avg < 1000ms
```

#### Test 8.2: Benchmark specific operation
```
Command: /bench get_tasks
Expected:
  - Runs benchmark for get_tasks only
  - Shows detailed timing (10 runs by default)
Validate:
  - Shows avg, min, max times
  - avg < 200ms
```

#### Test 8.3: Benchmark with custom runs
```
Command: /bench get_tasks runs:20
Expected:
  - Runs 20 iterations instead of default 10
Validate:
  - Reports based on 20 runs
```

#### Test 8.4: Compare search methods
```
Command: /bench compare voice agent
Expected:
  - Compares vector vs text vs hybrid search
  - Shows timing for each method
  - Shows result count for each
Validate:
  - Three rows: Vector, Text, Hybrid
  - Each has timing and result count
```

---

### SECTION 9: /debug - Diagnostics

#### Test 9.1: Debug status
```
Command: /debug status
Expected:
  - Shows MongoDB connection status
  - Shows index status
  - Shows API key status
Validate:
  - MongoDB shows connected
  - Indexes show READY status
```

#### Test 9.2: Debug timings
```
Command: /debug timings
Expected:
  - Shows recent operation timings
  - Lists last N operations
Validate:
  - Shows timing history
```

---

### SECTION 10: /db - Direct Database

#### Test 10.1: Database stats
```
Command: /db stats
Expected:
  - Shows collection statistics
  - Document counts for tasks, projects
Validate:
  - Shows tasks count ~49
  - Shows projects count ~10
```

#### Test 10.2: Count with filter
```
Command: /db count tasks status:done
Expected:
  - Counts tasks where status is done
Validate:
  - Returns number (not full documents)
```

---

## Column Validation Rules

### Tasks Table Columns
| Column | Source | Required | Notes |
|--------|--------|----------|-------|
| # | row index | Yes | Sequential number |
| Title | task.title | Yes | Never empty |
| Status | task.status | Yes | "todo", "in_progress", "done" |
| Priority | task.priority | Show if exists | "high", "medium", "low", or "-" |
| Project | projects.name via task.project_id | Show if exists | Requires $lookup join |
| Last Activity | task.activity_log[-1].timestamp | Yes | Format: "Jan 03" |

### Projects Table Columns
| Column | Source | Required | Notes |
|--------|--------|----------|-------|
| # | row index | Yes | Sequential number |
| Name | project.name | Yes | Never empty |
| Description | project.description | Yes | Truncate if long |
| Todo | count from tasks | Yes | Number |
| In Progress | count from tasks | Yes | Number |
| Done | count from tasks | Yes | Number |
| Total | sum of counts | Yes | Number |

### Search Results Columns
| Column | Source | Required | Notes |
|--------|--------|----------|-------|
| # | row index | Yes | Sequential number |
| Title/Name | task.title or project.name | Yes | Depends on collection |
| Score | $meta.score | Yes | Relevance score 0-1 |
| Status | status field | Yes | |
| Project | projects.name (for tasks) | If task | |
| Priority | priority field (for tasks) | If task | |

---

## Known Data Points for Validation

Based on sample data, these counts should be approximately:

| Query | Expected Count |
|-------|---------------|
| /tasks | 45-50 |
| /tasks status:todo | 25-30 |
| /tasks status:in_progress | 10-15 |
| /tasks status:done | 10-15 |
| /tasks priority:high | 10-15 |
| /tasks project:AgentOps | 5-8 |
| /projects | 10 |
| /projects search memory | 2-4 |
| /tasks search debugging | 3-8 |

---

## Test Execution Script

```python
def test_slash_commands():
    """Execute all slash command tests"""
    
    tests = [
        # Section 1: Basic task queries
        {"cmd": "/tasks", "validate": lambda r: r["count"] > 40},
        {"cmd": "/tasks status:todo", "validate": lambda r: all(t["status"] == "todo" for t in r["tasks"])},
        {"cmd": "/tasks status:in_progress", "validate": lambda r: all(t["status"] == "in_progress" for t in r["tasks"])},
        {"cmd": "/tasks priority:high", "validate": lambda r: all(t.get("priority") == "high" for t in r["tasks"])},
        {"cmd": "/tasks project:AgentOps", "validate": lambda r: all("AgentOps" in t.get("project_name", "") for t in r["tasks"])},
        
        # Section 2: Search
        {"cmd": "/tasks search debugging", "validate": lambda r: r["count"] > 0 and r["count"] < 15},
        {"cmd": "/tasks search voice agent", "validate": lambda r: any("voice" in t["title"].lower() for t in r["tasks"])},
        
        # Section 3: Temporal
        {"cmd": "/tasks today", "validate": lambda r: True},  # Manual validation needed
        {"cmd": "/tasks stale", "validate": lambda r: all(t["status"] == "in_progress" for t in r.get("tasks", []))},
        
        # Section 4: Projects
        {"cmd": "/projects", "validate": lambda r: r["count"] == 10},
        {"cmd": "/projects AgentOps", "validate": lambda r: r.get("project", {}).get("name", "").find("AgentOps") >= 0},
        {"cmd": "/projects search memory", "validate": lambda r: r["count"] < 10},
        
        # Section 5: Benchmarks
        {"cmd": "/bench get_tasks", "validate": lambda r: r.get("avg_ms", 9999) < 500},
    ]
    
    results = []
    for test in tests:
        try:
            result = execute_command(test["cmd"])
            passed = test["validate"](result)
            results.append({"cmd": test["cmd"], "passed": passed, "result": result})
        except Exception as e:
            results.append({"cmd": test["cmd"], "passed": False, "error": str(e)})
    
    # Print report
    print("=" * 60)
    print("SLASH COMMAND TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    for r in results:
        status = "✓ PASS" if r["passed"] else "✗ FAIL"
        print(f"{status}: {r['cmd']}")
        if not r["passed"]:
            print(f"       Error: {r.get('error', 'Validation failed')}")
    
    print("=" * 60)
    print(f"TOTAL: {passed} passed, {failed} failed")
    
    return results
```

---

## Empty Column Checklist

Run `/tasks` and verify these columns are NOT empty when data exists:

- [ ] Priority shows "high"/"medium"/"low" (not blank) for tasks that have priority set
- [ ] Project shows project NAME (not blank, not ObjectId) for tasks with project_id
- [ ] Last Activity shows date for tasks with activity_log entries

If columns are blank, the issue is likely:
1. **Priority**: Field name mismatch or not being read from document
2. **Project**: Missing $lookup join to projects collection  
3. **Last Activity**: activity_log not being parsed or timestamp format issue

---

*Flow Companion v2.0 — Slash Command Test Specification*