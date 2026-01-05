# Flow Companion Backslash Commands
## Direct MongoDB Access — No LLM Overhead

---

## Command Tree

```
/
├── tasks
│   ├── (no args)                 → List all tasks
│   ├── status:<status>           → Filter by status
│   ├── project:<name>            → Filter by project
│   ├── priority:<level>          → Filter by priority
│   ├── search <query>            → Hybrid search
│   ├── today                     → Activity today
│   ├── yesterday                 → Activity yesterday
│   ├── this_week                 → Activity this week
│   ├── completed:<timeframe>     → Completed in timeframe
│   └── stale                     → In progress > 7 days
│
├── projects
│   ├── (no args)                 → List all projects
│   ├── <name>                    → Get project + tasks
│   ├── search <query>            → Hybrid search
│   └── <name> stats              → Project statistics
│
├── do
│   ├── complete <task>           → Mark task done
│   ├── start <task>              → Mark task in_progress
│   ├── stop <task>               → Mark task todo
│   ├── note <task> "<text>"      → Add note to task
│   └── create <title> [opts]     → Create new task
│
├── search
│   ├── <query>                   → Hybrid search (default)
│   ├── tasks <query>             → Search tasks only
│   ├── projects <query>          → Search projects only
│   ├── vector <query>            → Vector search only
│   └── text <query>              → Text search only
│
├── bench
│   ├── all                       → Run all benchmarks
│   ├── get_tasks                 → Benchmark get_tasks
│   ├── get_projects              → Benchmark get_projects
│   ├── search <query>            → Benchmark hybrid search
│   ├── compare <query>           → Compare vector vs text vs hybrid
│   └── mongodb                   → Raw MongoDB latency
│
├── debug
│   ├── status                    → Connection & index status
│   ├── indexes                   → List MongoDB indexes
│   ├── timings                   → Recent operation timings
│   ├── explain <command>         → Query execution plan
│   └── clear                     → Clear debug history
│
├── db
│   ├── stats                     → Collection statistics
│   ├── count <collection>        → Count documents
│   ├── sample <collection> <n>   → Random sample
│   └── find <collection> <json>  → Direct query
│
└── help
    ├── (no args)                 → List all commands
    └── <command>                 → Help for specific command
```

---

## Example Queries

### `/tasks` — Task Queries

```bash
# List all tasks
/tasks

# Filter by status
/tasks status:todo
/tasks status:in_progress
/tasks status:done

# Filter by project
/tasks project:AgentOps
/tasks project:"Voice Agent"

# Filter by priority
/tasks priority:high
/tasks priority:medium

# Combine filters
/tasks status:in_progress priority:high
/tasks project:AgentOps status:todo

# Hybrid search
/tasks search debugging
/tasks search voice agent app
/tasks search checkpointer implementation

# Temporal queries
/tasks today
/tasks yesterday
/tasks this_week
/tasks completed:today
/tasks completed:this_week
/tasks stale
```

### `/projects` — Project Queries

```bash
# List all projects
/projects

# Get specific project with tasks
/projects AgentOps
/projects "Voice Agent"
/projects LangGraph

# Search projects
/projects search memory
/projects search webinar

# Project statistics
/projects AgentOps stats
/projects "Gaming NPC" stats
```

### `/do` — Task Actions

```bash
# Complete a task
/do complete debugging doc
/do complete "Create debugging methodologies doc"
/do complete checkpointer

# Start a task
/do start voice agent app
/do start "Review PR feedback"

# Stop a task (back to todo)
/do stop audio pipeline

# Add notes
/do note debugging doc "Fixed edge case with null embeddings"
/do note voice agent "WebSocket streaming working"
/do note checkpointer "Need to handle connection pooling"

# Create new task
/do create "Write unit tests"
/do create "Review documentation" project:AgentOps priority:high
/do create "Fix memory leak" project:"Voice Agent" priority:medium
```

### `/search` — Direct Search

```bash
# Hybrid search (default)
/search debugging
/search voice agent
/search real-time streaming
/search memory patterns

# Tasks only
/search tasks checkpointer
/search tasks webinar content

# Projects only
/search projects gaming
/search projects voice

# Vector search only (semantic)
/search vector observability tools
/search vector how to debug agents

# Text search only (exact match)
/search text checkpointer
/search text "PR feedback"
```

### `/bench` — Benchmarking (Demo Commands!)

```bash
# Run all benchmarks
/bench all

# Benchmark specific operations
/bench get_tasks
/bench get_tasks runs:20
/bench get_projects
/bench search debugging

# Compare search methods (great for demos!)
/bench compare voice agent
/bench compare memory patterns
/bench compare checkpointer

# Raw MongoDB latency
/bench mongodb
```

### `/debug` — Debug & Diagnostics

```bash
# Check system status
/debug status

# List indexes
/debug indexes

# Recent timings
/debug timings

# Explain a query
/debug explain /tasks status:in_progress
/debug explain /search voice agent

# Clear history
/debug clear
```

### `/db` — Direct MongoDB Access

```bash
# Collection stats
/db stats

# Count documents
/db count tasks
/db count tasks status:done
/db count tasks status:in_progress
/db count projects

# Random sample
/db sample tasks 5
/db sample projects 3

# Direct find (JSON query)
/db find tasks {"status": "done"}
/db find tasks {"priority": "high", "status": "todo"}
/db find projects {"name": {"$regex": "Agent"}}
```

### `/help` — Help

```bash
# General help
/help

# Command-specific help
/help tasks
/help do
/help bench
/help search
```

---

## Demo Script

Run these in sequence to showcase MongoDB performance:

```bash
# 1. Show basic query speed
/tasks
# Expected: <100ms

# 2. Show filtered query speed  
/tasks status:in_progress project:AgentOps
# Expected: <100ms

# 3. Show hybrid search speed
/search voice agent reference app
# Expected: <500ms

# 4. Run full benchmark
/bench all
# Expected: get_tasks ~50ms, search ~400ms

# 5. Compare search methods
/bench compare debugging methodologies
# Shows: vector vs text vs hybrid latency

# 6. Prove MongoDB isn't the bottleneck
/debug timings
# Compare to LLM times in Agent Debug panel
```

**Key Talking Point:** MongoDB operations complete in <500ms. The LLM decision-making is what takes 1-3 seconds.

---

*Flow Companion v2.0 — Backslash Commands Reference*