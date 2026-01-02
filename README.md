# Flow Companion - Milestone 1

A conversational TODO app powered by AI agents, MongoDB Atlas vector search, and Claude API.

## Features

- **Conversational Task Management** - Natural language interface for creating and managing tasks
- **Multi-Agent System** - Coordinator routes requests to specialized agents:
  - **Worklog Agent** - Handles task/project CRUD operations
  - **Retrieval Agent** - Performs semantic search and analytics
- **Semantic Search** - Find tasks and projects by meaning using vector embeddings
- **Activity Tracking** - Automatic logging of all changes with timestamps
- **Project Organization** - Group related tasks under projects
- **Rich Context** - Store detailed context, notes, decisions, and methods
- **Progress Tracking** - Monitor project completion and task statistics

## Tech Stack

- **UI**: Streamlit chat interface
- **AI**: Claude API (Sonnet 4.5) for agent reasoning
- **Embeddings**: Voyage AI (voyage-3) for semantic search
- **Database**: MongoDB Atlas (operational DB + vector store)
- **Language**: Python 3.9+

## Project Structure

```
mdb-flow/
├── agents/
│   ├── coordinator.py      # Intent routing agent
│   ├── worklog.py         # Task/project management agent
│   └── retrieval.py       # Search & analytics agent
├── shared/
│   ├── config.py          # Environment configuration
│   ├── db.py              # MongoDB connection & helpers
│   ├── embeddings.py      # Voyage AI integration
│   ├── llm.py             # Claude API integration
│   └── models.py          # Pydantic data models
├── ui/
│   └── streamlit_app.py   # Chat interface
├── scripts/
│   └── setup_indexes.py   # Database index setup
├── requirements.txt
└── .env.example           # Environment variables template
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account (free tier works)
- Anthropic API key (for Claude)
- Voyage AI API key (for embeddings)

### 2. Clone and Install

```bash
git clone <repository-url>
cd mdb-flow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# VOYAGE_API_KEY=your_voyage_api_key_here
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
# MONGODB_DATABASE=flow_companion
```

### 4. Set Up MongoDB Atlas

#### Create a Cluster

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a free M0 cluster
3. Set up database access (create a user)
4. Set up network access (add your IP or allow all: 0.0.0.0/0)
5. Get your connection string and add it to `.env`

#### Create Database Indexes

Run the setup script to create standard and text search indexes:

```bash
python scripts/setup_indexes.py
```

#### Create Vector Search Indexes (Manual)

Vector search indexes must be created in the Atlas UI:

1. Go to your cluster in Atlas
2. Navigate to: **Database → Browse Collections → Search Indexes**
3. Click **"Create Index"** → **"JSON Editor"**
4. Create two indexes with these configurations:

**Tasks Vector Index:**
```json
{
  "name": "task_embedding_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embedding",
        "type": "vector",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
```

**Projects Vector Index:**
```json
{
  "name": "project_embedding_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embedding",
        "type": "vector",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
```

⚠️ **Important**: Index names must match exactly as shown above.

### 5. Run the Application

```bash
streamlit run ui/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Creating Tasks and Projects

Simply chat with the assistant in natural language:

```
"Create a new project called User Authentication with description: Implement JWT-based auth"

"Add a task to implement login endpoint with high priority"

"Create a task: Set up MongoDB connection"
```

### Managing Tasks

```
"Mark task <task_id> as in progress"

"Complete the login endpoint task"

"Add a note to task <task_id>: Fixed validation bug"

"Update priority of task <task_id> to high"
```

### Searching and Analytics

```
"Find all tasks related to authentication"

"What did I work on yesterday?"

"Show me incomplete tasks from last week"

"Show progress on the Authentication project"
```

### Task List Sidebar

The right sidebar shows all tasks grouped by project:
- **Status icons**: ○ todo, ◐ in_progress, ✓ done
- **Priority badges**: 🔴 high, 🟡 medium, 🟢 low
- Click task to expand and see details

## Data Models

### Task

```python
{
  "_id": ObjectId,
  "title": str,
  "status": "todo" | "in_progress" | "done",
  "priority": "low" | "medium" | "high" | null,
  "project_id": ObjectId | null,
  "context": str,
  "notes": [str],
  "activity_log": [{timestamp, action, note}],
  "created_at": datetime,
  "updated_at": datetime,
  "started_at": datetime,
  "completed_at": datetime,
  "last_worked_on": datetime,
  "embedding": [float] (1024 dimensions)
}
```

### Project

```python
{
  "_id": ObjectId,
  "name": str,
  "description": str,
  "status": "active" | "archived",
  "context": str,
  "notes": [str],
  "methods": [str],  # Technologies/approaches
  "decisions": [str],
  "activity_log": [{timestamp, action, note}],
  "created_at": datetime,
  "updated_at": datetime,
  "last_activity": datetime,
  "embedding": [float] (1024 dimensions)
}
```

## Agent Architecture

### Coordinator Agent
- Routes user requests to appropriate specialized agents
- Uses Claude to classify intent (worklog vs retrieval)
- Maintains conversation context

### Worklog Agent (13 tools)
- **Task Management**: create_task, update_task, complete_task, get_task, list_tasks
- **Project Management**: create_project, update_project, get_project, list_projects
- **Shared Operations**: add_note, add_context, add_decision, add_method

### Retrieval Agent (5 tools)
- **embed_query**: Generate embeddings for queries
- **search_semantic**: Vector search across tasks/projects
- **search_by_date**: Find activity on specific dates
- **search_incomplete**: Find stalled tasks
- **search_progress**: Get project statistics and progress

## Development

### Project Statistics

- **Total Lines of Code**: ~2,800
- **Agent Code**: 1,628 lines
- **Shared Utilities**: 970 lines
- **UI**: 208 lines

### Key Technologies

- **Pydantic**: Data validation and settings management
- **PyMongo**: MongoDB driver
- **Anthropic SDK**: Claude API client
- **Voyage AI SDK**: Embedding generation
- **Streamlit**: Web interface

## Troubleshooting

### Vector Search Not Working

- Ensure vector search indexes are created in Atlas UI
- Index names must match: `task_embedding_index` and `project_embedding_index`
- Wait a few minutes after creating indexes for them to be ready

### Connection Issues

- Check MongoDB URI in `.env`
- Verify network access in Atlas (IP whitelist)
- Ensure database user has read/write permissions

### API Key Errors

- Verify Anthropic API key is valid
- Verify Voyage AI API key is valid
- Check API key has sufficient credits

## Future Enhancements (Milestone 2+)

- Real-time collaboration
- File attachments
- Calendar integration
- Recurring tasks
- Advanced analytics dashboard
- Mobile app

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.