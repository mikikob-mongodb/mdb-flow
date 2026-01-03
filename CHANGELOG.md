# Changelog

All notable changes to Flow Companion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
