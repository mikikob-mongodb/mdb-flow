# Changelog

All notable changes to Flow Companion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-01-05

### Milestone - Context Engineering Optimizations Complete

All three context engineering optimizations implemented and integrated:
- Tool result compression: ~80% reduction in context size for large result sets
- Streamlined prompt: ~60% reduction in system prompt tokens
- Prompt caching: ~40-50% latency reduction on subsequent calls

All optimizations are toggleable from the Streamlit sidebar for A/B testing and performance analysis.

**Test Coverage:** 203/213 tests passing (95.3%)

## [2.3.0] - 2026-01-05

### Added - Prompt Caching Toggle

- **Anthropic Prompt Caching API**: Integrated beta API for caching system prompts and tool definitions
- **Cache Performance Logging**: Logs cache HIT/MISS with token counts in debug output
- **Beta Header Support**: Includes `anthropic-beta: prompt-caching-2024-07-31` header
- **Performance Improvement**: ~40-50% latency reduction on subsequent API calls within 5-minute cache window
- **Toggleable via Sidebar**: Enable/disable caching through UI (default: ON)

**Implementation Files:**
- `shared/llm.py`: Added `cache_prompts` parameter to `generate_with_tools()`
- `agents/coordinator.py`: Passes caching toggle to LLM calls
- `ui/streamlit_app.py`: Prompt Caching toggle in sidebar

## [2.2.0] - 2026-01-05

### Added - Streamlined Prompt Toggle

- **Streamlined System Prompt**: Concise directive-based prompt (~200 words) vs verbose detailed prompt (~500 words)
- **60% Token Reduction**: Streamlined prompt reduces system prompt tokens by ~60%
- **Pattern-Based Instructions**: Uses explicit patterns for common actions (e.g., "I finished X" → search → confirm → complete)
- **Toggleable via Sidebar**: Switch between verbose and streamlined prompts (default: streamlined)
- **Logging**: Shows prompt type and estimated token count in debug output

**Implementation Files:**
- `config/prompts.py`: Defines both VERBOSE_SYSTEM_PROMPT and STREAMLINED_SYSTEM_PROMPT
- `agents/coordinator.py`: Dynamically selects prompt based on toggle
- `ui/streamlit_app.py`: Streamlined Prompt toggle in sidebar

## [2.1.0] - 2026-01-04

### Added - Tool Result Compression Toggle

- **Context Engineering**: Intelligent compression of large tool results to reduce context size
- **80% Reduction**: Compresses 50-task lists to summary + top 5 (from ~5000 tokens to ~1000 tokens)
- **Toggleable via Sidebar**: Enable/disable compression through UI (default: ON)
- **Compression Rules**:
  - `get_tasks`: >10 tasks → summary with status breakdown + top 5
  - `search_tasks`: Essential fields only (id, title, score, project, status)
  - `get_projects`: >5 projects → summary + top 5
- **Test Coverage**: 20 new tests (16 unit + 4 integration, all passing)

**Implementation Files:**
- `utils/context_engineering.py`: Compression logic
- `agents/coordinator.py`: Applies compression before LLM calls
- `ui/streamlit_app.py`: Context Engineering toggles in sidebar

## [2.0.0] - 2026-01-04

### Milestone 2 Release - Voice Input & Tool Calling Foundation

Merged `milestone-2-voice-input` branch into main.

#### Voice Input System
- **Native Audio Recording**: Streamlit's `st.audio_input()` for microphone access
- **OpenAI Whisper Transcription**: Speech-to-text with automatic error handling
- **Voice Message Display**: 🎤 icon indicates voice messages in chat history
- **Temporary File Management**: Automatic cleanup of audio files after transcription
- **Unified Processing**: Voice and text use identical coordinator flow

#### Tool Calling & Hallucination Prevention
- **20 Coordinator Tools**: Expanded from 8 to 20 tools for comprehensive task/project management
- **Explicit Tool Enforcement**: System prompt requires tool use, prevents LLM hallucination
- **Search → Confirm → Execute Pattern**: Prevents accidental task updates
- **Comprehensive Test Coverage**: 203 tests including hallucination prevention tests

#### New Tools Added
- `create_task`, `update_task`, `stop_task`, `get_task`
- `create_project`, `update_project`, `get_project`
- `add_note_to_project`, `add_context_to_project`, `add_decision_to_project`, `add_method_to_project`
- `add_context_to_task`

#### Critical Fixes
- **DateTime Serialization**: Fixed `datetime.datetime is not JSON serializable` error
- **Conversation History**: Proper serialization of ObjectId and datetime objects

### Changed
- Removed `/bench`, `/debug`, `/db`, `/help` commands to simplify demo experience
- Updated system prompt to enforce tool usage and prevent hallucination

## [1.0.0] - 2026-01-02

### Added - Milestone 1 Release

#### Core Features
- **Multi-Agent System**: Coordinator agent that routes requests to specialized agents
  - WorklogAgent: 13 tools for task/project CRUD operations
  - RetrievalAgent: 5 tools for semantic search and analytics
- **Conversational Interface**: Streamlit chat UI with natural language interaction
- **Task Management**: Create, update, complete, and list tasks with rich context
- **Project Organization**: Group related tasks under projects with context, notes, decisions, and methods
- **Activity Tracking**: Automatic logging of all changes with timestamps
- **Semantic Search**: Find tasks and projects by meaning using Voyage AI embeddings (1024 dimensions)
- **Vector Search**: MongoDB Atlas vector search with cosine similarity
- **Status Tracking**: todo, in_progress, done with automatic timestamp management
- **Priority Levels**: high, medium, low priority assignment
- **Rich Context**: Store detailed context, notes, decisions, and methods for tasks and projects

#### Data Models
- **Task Model**: Full schema with embedding support, activity logs, and temporal tracking
- **Project Model**: Complete project management with status, notes, decisions, methods
- **Settings Model**: Application settings storage
- **Activity Logs**: Automatic timestamped entries for all operations

#### Database & Search
- **MongoDB Atlas Integration**: Operational database with PyMongo
- **Vector Search Indexes**: 1024-dimensional embeddings for semantic search
- **Standard Indexes**: Optimized queries on status, priority, dates, project relationships
- **Text Search Indexes**: Full-text search capabilities

#### AI & Embeddings
- **Claude API Integration**: Sonnet 4.5 for agent reasoning and intent classification
- **Voyage AI Embeddings**: voyage-3 model for semantic search
- **Tool Use**: Native Claude tool calling with agentic loops

#### UI Components
- **Chat Interface**: Clean, minimal chat experience with message history
- **Task Sidebar**: Live view of all projects and tasks with status icons and priority badges
- **Expandable Task Details**: Click to view full task information
- **Status Icons**: ○ todo, ◐ in_progress, ✓ done
- **Priority Badges**: 🔴 high, 🟡 medium, 🟢 low

#### Scripts & Tools
- **Index Setup Script**: Automated creation of MongoDB indexes
- **Sample Data Loader**: Load 10 realistic projects with 44 tasks for testing
- **Debug Tools**: Agent debugging and diagnostics scripts

#### Documentation
- **Comprehensive README**: Complete setup instructions, architecture overview, usage examples
- **Sample Data Guide**: Test queries and verification checklist
- **API Documentation**: Pydantic models with full docstrings
- **Setup Instructions**: Step-by-step guide with environment setup, database configuration

### Fixed

#### Agent Routing
- **Coordinator Intent Classification**: Improved routing logic to distinguish between simple list queries and complex searches
  - List/show queries now route to WorklogAgent (uses list_tasks/list_projects)
  - Search/analytics queries route to RetrievalAgent (uses semantic search)
  - Fixed issue where "What tasks do I have?" incorrectly routed to vector search

#### Compatibility
- **Pydantic v2 Support**: Fixed ObjectId validation using Annotated[ObjectId, BeforeValidator] pattern
  - Replaced deprecated `__get_validators__()` class method
  - Compatible with Pydantic 2.12.5+

#### Embedding Generation
- **Sample Data Loader**: Updated to use `embed_document()` function (not `embed_text()`)
- **Proper Input Types**: Uses "document" type for embeddings, "query" type for searches

### Developer Experience
- **Debug Logging**: Added comprehensive logging to coordinator and agents for troubleshooting
- **Virtual Environment**: Added venv setup instructions throughout README
- **Error Messages**: Clear error handling with informative messages
- **Type Hints**: Full type annotations using Python typing module

### Technical Details

#### Dependencies
- streamlit: Web interface
- pymongo: MongoDB driver
- anthropic: Claude API client
- voyageai: Embedding generation
- pydantic>=2.1.0: Data validation
- pydantic-settings>=2.1.0: Settings management
- python-dotenv: Environment variable loading

#### Project Statistics
- **Total Lines of Code**: ~3,800
- **Agent Code**: ~1,700 lines
- **Shared Utilities**: ~970 lines
- **UI Code**: ~208 lines
- **Scripts**: ~1,260 lines
- **Sample Projects**: 10
- **Sample Tasks**: 44
- **Sample Activity Logs**: ~150

#### Architecture
- **Collection Names**: tasks, projects, settings
- **Vector Index Names**: task_embedding_index, project_embedding_index
- **Embedding Dimensions**: 1024 (Voyage AI voyage-3)
- **Similarity Metric**: Cosine similarity
- **Max Tool Iterations**: 5 per agent

### Known Limitations

- Vector search indexes must be created manually in MongoDB Atlas UI
- Requires API keys for Anthropic (Claude) and Voyage AI
- Session state is per-browser-tab (no cross-tab sync)
- Conversation history not persisted to database

### Migration Notes

This is the initial release (v1.0.0), no migration needed.

---

## Future Enhancements (Planned for v2.0+)

- Real-time collaboration and multi-user support
- File attachments for tasks and projects
- Calendar integration and scheduling
- Recurring tasks
- Advanced analytics dashboard
- Mobile app
- Notification system
- Task dependencies and blocking relationships
- Custom fields and templates
- API endpoints for external integrations
