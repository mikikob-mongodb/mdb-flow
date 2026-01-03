# Flow Companion — Sample Data & Test Queries

This document describes the sample dataset and provides test queries to verify your Flow Companion installation.

---

## Loading Sample Data

The sample data loader creates realistic projects and tasks for testing all Flow Companion features.

### Run the Loader

```bash
# Full load with embeddings (required for semantic search)
python scripts/load_sample_data.py

# Quick load without embeddings (faster, but search won't work)
python scripts/load_sample_data.py --skip-embeddings
```

### What Gets Created

| Type | Count | Description |
|------|-------|-------------|
| **Projects** | 10 | Various statuses (active, archived) |
| **Tasks** | 44 | Mix of todo, in_progress, done |
| **Activity Logs** | ~150 | Timestamped entries for temporal queries |
| **Embeddings** | 54 | Vector embeddings for semantic search |

### Sample Projects

| Project | Status | Tasks | Description |
|---------|--------|-------|-------------|
| AgentOps Framework | active | 5 | Observability and debugging frameworks |
| Memory Engineering Content | active | 4 | Technical content and documentation |
| LangGraph Integration | active | 4 | Framework code contributions |
| Voice Agent Architecture | active | 5 | Real-time audio pipeline |
| Gaming NPC Demo | active | 6 | Domain-specific hero demo |
| AWS re:Invent Prep | active | 4 | Conference preparation |
| CrewAI Memory Patterns | active | 3 | Framework contribution |
| Education Adaptive Tutoring Demo | active | 4 | Domain-specific demo |
| Q4 FY25 Deliverables | archived | 4 | Completed past work |
| Developer Webinar Series | active | 5 | Monthly webinars |

---

## Test Queries

### Basic Task Management

```
What tasks do I have?
```

```
Show me all my projects
```

```
What tasks are in progress?
```

```
What tasks are marked as todo?
```

```
What's done?
```

---

### Project-Specific Queries

```
What's the progress on AgentOps Framework?
```

```
Show me tasks in the LangGraph Integration project
```

```
What's left to do on the Gaming NPC Demo?
```

```
How's the Voice Agent Architecture project going?
```

```
What tasks are in the AWS re:Invent Prep project?
```

```
Show me the CrewAI Memory Patterns project
```

---

### Temporal Queries

```
What did I work on today?
```

```
What did I do yesterday?
```

```
What did I work on this week?
```

```
What didn't I finish this week?
```

```
What tasks have I completed recently?
```

---

### Semantic Search

These queries use vector similarity to find related content:

```
Show me tasks related to voice agents
```

```
What am I doing with LangGraph?
```

```
Find tasks about memory
```

```
What's related to webinars?
```

```
Show me anything about documentation
```

```
Tasks related to frameworks or integrations
```

```
What involves demos or presentations?
```

---

### Priority & Status Queries

```
What are my high priority tasks?
```

```
Show me high priority tasks that aren't done yet
```

```
What medium priority items are in progress?
```

```
What low priority tasks can I pick up?
```

---

### Context & Notes Queries

```
What do I know about the checkpointer implementation?
```

```
What did my manager suggest about the re:Invent talk?
```

```
Show me tasks with notes about testing
```

```
What decisions have been made on AgentOps Framework?
```

---

### Task Management Actions

```
Mark the "Practice run-through" task as in progress
```

```
Complete the "Design MongoDB memory backend" task
```

```
Add a note to the voice agent reference app task: Added interruption handling logic
```

```
Create a task for writing the LlamaIndex integration guide in LangGraph Integration
```

```
Update the multimodal demo task to high priority
```

---

### Project Management Actions

```
Add a decision to Voice Agent Architecture: Using Deepgram for STT
```

```
Add a method to Gaming NPC Demo: Unity WebGL
```

```
Add a note to AgentOps Framework: Need to coordinate with DevRel on launch timing
```

---

### Complex Queries

```
What high priority tasks are still in progress across all projects?
```

```
Show me tasks related to content creation that aren't done
```

```
What's blocking the AWS re:Invent presentation?
```

```
What framework contributions am I working on?
```

```
Show me all demo-related tasks and their status
```

---

### Conversational Flow Test

Run these in sequence to test context retention:

```
Show me the Developer Webinar Series project
```

```
What tasks are in progress there?
```

```
Add a note to the February webinar task: Confirmed guest speaker for RAG section
```

```
Mark it as done
```

```
What's next for that project?
```

---

### Edge Cases

```
Show me archived projects
```

```
What's in Q4 FY25 Deliverables?
```

```
Create a new project called API Documentation
```

```
Add a task for writing the quickstart guide
```

```
Set it to high priority with context: Blocking developer onboarding
```

---

## Quick Verification Checklist

Run these 10 queries to verify your installation:

| # | Query | Tests |
|---|-------|-------|
| 1 | `What projects do I have?` | Basic retrieval |
| 2 | `What's the progress on AgentOps Framework?` | Project progress |
| 3 | `Show me tasks related to voice` | Semantic search |
| 4 | `What high priority tasks are in progress?` | Filtered queries |
| 5 | `What did I work on this week?` | Temporal queries |
| 6 | `Create a task for reviewing PR feedback in LangGraph Integration` | Task creation |
| 7 | `Mark it as in progress` | Context retention + update |
| 8 | `Add a note: Addressing code review comments from framework team` | Adding notes |
| 9 | `What's left on LangGraph Integration?` | Project queries |
| 10 | `What tasks are still todo?` | Status filtering |

---

## Expected Behaviors

### Conversational Context

The agent should remember context within a conversation:

```
User: Create a task for updating the README
Agent: Created task 'Updating the README'. Want to add it to a project?

User: Yes, add it to LangGraph Integration
Agent: Added to LangGraph Integration. Priority?

User: High, and add a note that it's blocking the PR
Agent: Updated:
       • Priority: High
       • Note: Blocking the PR
```

### Follow-up Questions

The agent should ask clarifying questions when helpful:

```
User: Create a task for the bug fix
Agent: Created 'Bug fix'. Which project should I add it to?
       • AgentOps Framework
       • LangGraph Integration
       • Voice Agent Architecture
       • ...
```

### Activity Logging

All changes should be logged. Verify with:

```
Show me the activity log for the AgentOps Framework project
```

```
What's the history of the checkpointer task?
```

---

## Troubleshooting

### "No results found" for semantic search

- Ensure you ran the loader **without** `--skip-embeddings`
- Verify Voyage API key is set in `.env`
- Check that vector search indexes exist in MongoDB Atlas

### Temporal queries return nothing

- Sample data uses randomized dates in the past 60 days
- Try "this week" or "this month" instead of "today"

### Agent doesn't understand context

- Make sure conversation history is being passed to the coordinator
- Check that session state is maintained in Streamlit

---

## Resetting Data

To reload sample data:

```bash
# This clears existing data and reloads
python scripts/load_sample_data.py
```

To clear all data without reloading:

```python
from shared.db import get_db
db = get_db()
db.projects.delete_many({})
db.tasks.delete_many({})
db.settings.delete_many({})
```