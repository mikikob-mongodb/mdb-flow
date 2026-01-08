# Flow Companion

**Version 3.1 (Milestone 3 - Evals Dashboard)**

A conversational TODO app powered by AI agents, MongoDB Atlas vector search, and Claude API. Features voice input, context engineering optimizations, and a comprehensive evaluation dashboard for measuring performance.

## Features

### Core Functionality (Milestone 1)
- **Conversational Task Management** - Natural language interface for creating and managing tasks
- **Multi-Agent System** - Coordinator routes requests to specialized agents:
  - **Worklog Agent** - Handles task/project CRUD operations
  - **Retrieval Agent** - Performs semantic search and analytics
- **Semantic Search** - Find tasks and projects by meaning using vector embeddings
- **Activity Tracking** - Automatic logging of all changes with timestamps
- **Project Organization** - Group related tasks under projects
- **Rich Context** - Store detailed context, notes, decisions, and methods
- **Progress Tracking** - Monitor project completion and task statistics

### Voice Input (Milestone 2)
- **Voice Commands** - Speak to manage tasks with OpenAI Whisper transcription
- **Audio Recording** - Built-in browser audio capture
- **Slash Commands** - Fast direct queries bypassing LLM (`/tasks`, `/projects`, `/search`)
- **Task List Sidebar** - Visual task management with status indicators

### Context Engineering (Milestone 2)
- **Tool Result Compression** - Reduce context size by 60-70% while preserving key information
- **Streamlined Prompts** - Directive-based system prompts for faster response
- **Prompt Caching** - Cache system prompts with Anthropic API for reduced latency
- **Configurable Toggles** - Enable/disable optimizations in real-time

### Evals Dashboard (Milestone 3)
- **Multi-Config Comparison** - Test different optimization configurations side-by-side
- **46-Test Suite** - Comprehensive test queries across slash commands, text queries, actions, multi-turn, voice, and search modes
- **Performance Metrics** - Track latency, token usage, cache hits, and accuracy
- **Visual Analytics** - Interactive Plotly charts showing impact analysis
- **Search Mode Testing** - Compare hybrid, vector, and text search performance
- **MongoDB Persistence** - Save and load comparison runs for historical analysis
- **JSON Export** - Export results for slides and reports

### Agent Memory System (Milestone 4)
- **Session Context** - Track current project, task, and user preferences across conversations
- **Preferences Learning** - Automatically extract and apply user preferences ("I'm focusing on Project X")
- **Disambiguation Resolution** - Store numbered options and resolve "the first one" references
- **Rule Learning** - User-defined shortcuts that trigger automatically ("when I say done, complete the task")
- **Action History** - Persistent record of all task operations with temporal queries
- **Cross-Agent Handoffs** - Share state between coordinator and specialized agents

## Tech Stack

- **UI**: Streamlit (main app + evals dashboard)
- **AI**: Claude API (Sonnet 4.5) for agent reasoning
- **Voice**: OpenAI Whisper API for speech-to-text
- **Embeddings**: Voyage AI (voyage-3) for semantic search
- **Database**: MongoDB Atlas (operational DB + vector store)
- **Charts**: Plotly for interactive visualizations
- **Language**: Python 3.13+

## Project Structure

```
mdb-flow/
├── agents/
│   ├── coordinator.py      # Intent routing agent
│   ├── worklog.py          # Task/project management agent
│   └── retrieval.py        # Search & analytics agent
├── shared/
│   ├── config.py           # Environment configuration
│   ├── db.py               # MongoDB connection & helpers
│   ├── embeddings.py       # Voyage AI integration
│   ├── llm.py              # Claude API integration
│   └── models.py           # Pydantic data models
├── ui/
│   ├── streamlit_app.py    # Main chat interface (port 8501)
│   ├── slash_commands.py   # Direct DB query commands
│   └── formatters.py       # Result formatting utilities
├── evals/                  # NEW: Evaluation system
│   ├── configs.py          # Optimization configurations
│   ├── test_suite.py       # 46 test queries
│   ├── result.py           # Data classes for results
│   ├── runner.py           # Multi-config test execution
│   └── storage.py          # MongoDB persistence
├── evals_app.py            # NEW: Evals dashboard (port 8502)
├── utils/
│   └── audio.py            # Audio recording and transcription
├── scripts/
│   ├── setup_database.py     # Database setup (indexes + memory)
│   ├── cleanup_database.py   # Database cleanup utilities
│   ├── test_memory_system.py # Memory system testing
│   └── load_sample_data.py   # Sample data loader
├── docs/
│   ├── ARCHITECTURE.md     # System architecture
│   ├── TESTING.md          # Testing guide
│   └── SLASH_COMMANDS.md   # Slash command reference
├── requirements.txt
└── .env.example            # Environment variables template
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

# Create and activate virtual environment (IMPORTANT!)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

⚠️ **Important**: Always activate the virtual environment before running the app or installing packages:
```bash
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
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

Run the setup script to create standard, text search, and memory indexes:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run setup script (creates all indexes)
python scripts/setup_database.py

# Or setup specific index types
python scripts/setup_database.py --standard  # Standard indexes only
python scripts/setup_database.py --memory    # Memory indexes only
python scripts/setup_database.py --list      # List existing indexes
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

### 5. Load Sample Data (Optional but Recommended)

To get started quickly with realistic sample data:

```bash
# Activate virtual environment
source venv/bin/activate

# Load sample data (10 projects with 44 tasks)
python scripts/load_sample_data.py
```

This will:
- Clear any existing data
- Load 10 realistic projects (AgentOps, Memory Engineering, Voice Agents, etc.)
- Create 44 tasks across projects with various statuses
- Generate embeddings for semantic search
- Set up realistic activity logs and timestamps

**Options:**
```bash
# Skip embeddings for faster loading (semantic search won't work)
python scripts/load_sample_data.py --skip-embeddings
```

**Sample Projects Included:**
- AgentOps Framework (5 tasks)
- Memory Engineering Content (4 tasks)
- LangGraph Integration (4 tasks)
- Voice Agent Architecture (5 tasks)
- Gaming NPC Demo (6 tasks)
- AWS re:Invent Prep (4 tasks)
- CrewAI Memory Patterns (3 tasks)
- Education Adaptive Tutoring Demo (4 tasks)
- Q4 FY25 Deliverables (4 tasks - archived)
- Developer Webinar Series (5 tasks)

### 6. Run the Applications

Make sure your virtual environment is activated, then run:

#### Main Chat Interface

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Run the main app
streamlit run ui/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

#### Evals Dashboard (Optional)

In a separate terminal, run the evals dashboard to compare optimization configurations:

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux

# Run the evals dashboard
streamlit run evals_app.py --server.port 8502
```

The evals dashboard will open at `http://localhost:8502`

**Both apps can run simultaneously** and share the same MongoDB database.

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

### Voice Commands

Use the microphone button to speak your commands:

```
🎤 "Create a task for debugging in AgentOps"
🎤 "Mark the authentication task as done"
🎤 "What tasks are in progress?"
```

Voice input uses OpenAI Whisper for transcription and works identically to text input.

### Slash Commands (Fast Queries)

Bypass the LLM for instant results:

```
/tasks                           # All tasks
/tasks status:in_progress        # Filter by status
/tasks priority:high             # Filter by priority
/tasks project:"AgentOps"        # Filter by project
/tasks search debugging          # Hybrid search

/projects                        # All projects
/projects "Voice Agent"          # Single project
/projects search memory          # Search projects
```

### Search Modes

Flow Companion supports three search modes, each with different performance vs quality tradeoffs:

#### Hybrid Search (Default) - Best Quality
- **Command:** `/search <query>` or `/tasks search <query>`
- **Performance:** ~420ms
- **Method:** Combines vector embeddings + MongoDB text search using $rankFusion
- **Best for:** Most queries - provides best result quality with both semantic and keyword matching

**Example:**
```
/search debugging
/tasks search memory leaks
/projects search agent
```

#### Vector Search - Semantic Understanding
- **Command:** `/search vector <query>` or `/tasks search vector <query>`
- **Performance:** ~280ms (33% faster than hybrid)
- **Method:** Voyage embeddings + MongoDB $vectorSearch
- **Best for:** Conceptual queries, finding semantically similar items, related topics

**Example:**
```
/search vector debugging
/tasks search vector memory issues
/projects search vector agent architecture
```

#### Text Search - Fastest
- **Command:** `/search text <query>` or `/tasks search text <query>`
- **Performance:** ~180ms (57% faster than hybrid)
- **Method:** MongoDB text index (keyword matching)
- **Best for:** Exact keyword matches, known terms, when speed matters most

**Example:**
```
/search text debugging
/tasks search text authentication
/projects search text AgentOps
```

**Performance Comparison:**
- Text search: ~180ms (fastest)
- Vector search: ~280ms (semantic)
- Hybrid search: ~420ms (most comprehensive)

All search modes support both tasks and projects. The debug panel shows which mode was used and the performance breakdown.

### Context Engineering Toggles

Configure optimizations in the sidebar:
- **📦 Compress Tool Results** - Reduce context size by 60-70%
- **⚡ Streamlined Prompt** - Use directive-based system prompt
- **💾 Prompt Caching** - Cache system prompt for faster response

### Task List Sidebar

The right sidebar shows all tasks grouped by project:
- **Status icons**: ○ todo, ◐ in_progress, ✓ done
- **Priority badges**: 🔴 high, 🟡 medium, 🟢 low
- Click task to expand and see details

### Evals Dashboard

Compare optimization configurations:

1. Open `http://localhost:8502`
2. Select 2+ configs (e.g., "Baseline" + "All Context Engineering")
3. Click "🚀 Run Comparison"
4. View results:
   - **Summary**: Avg latency, tokens, accuracy metrics
   - **Matrix**: Test-by-test comparison with best config highlighted
   - **Charts**: 5 interactive visualizations of performance impact
5. Export results to JSON for reports

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

## Milestone Roadmap

### ✅ Milestone 1: Core Functionality (Complete)
- Multi-agent system with coordinator
- Task and project management
- Semantic search with vector embeddings
- MongoDB Atlas integration
- Streamlit chat interface

### ✅ Milestone 2: Voice Input & Context Engineering (Complete)
- OpenAI Whisper integration for voice commands
- Slash commands for fast queries
- Tool result compression (60-70% reduction)
- Streamlined system prompts
- Prompt caching support
- Real-time optimization toggles

### ✅ Milestone 3: Evals Dashboard (Complete - v3.1)
- Separate evaluation dashboard app
- 46-test comprehensive suite
- Multi-config comparison with search mode variants
- Performance metrics tracking
- Interactive Plotly charts
- MongoDB persistence & history
- JSON export for reporting

### ✅ Milestone 4: Agent Memory System (Complete - v4.0)
- **Three-tier Memory**: Short-term (2hr TTL), Long-term (persistent), Shared (5min TTL)
- **Context Injection**: Automatic preference and state injection into prompts
- **Preferences System**: Extract and apply user preferences ("focusing on Project X")
- **Disambiguation**: Store and resolve "the first one" references with numbered options
- **Rule Learning**: User-defined shortcuts ("when I say done, complete the current task")
- **Action History**: Track all task operations with entity/metadata separation
- **Demo Data Seeding**: Realistic memory data for testing and demonstrations
- **Integration Tests**: Comprehensive test coverage for all memory features

### 🔮 Future Enhancements (Milestone 5+)
- **Real-time Collaboration** - Multi-user support
- **File Attachments** - Link documents to tasks
- **Calendar Integration** - Sync with Google Calendar
- **Recurring Tasks** - Automated task creation
- **Mobile App** - Native iOS/Android apps
- **Advanced Analytics** - Predictive insights and trends
- **Auto-Evaluation** - Automated pass/fail checking in evals
- **Cost Tracking** - Token usage and API cost monitoring

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.