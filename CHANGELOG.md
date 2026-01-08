# Changelog

All notable changes to Flow Companion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-01-08

### Milestone 5 - Semantic & Procedural Memory Complete

Major release introducing persistent user personalization through semantic and procedural memory.

#### Added - Memory System Enhancement
- **Semantic Memory (Preferences)** - Long-term storage of user preferences
  - Automatic extraction from natural language ("I'm focusing on X")
  - Confidence scoring (0.0-1.0) with explicit vs inferred source tracking
  - Sorted by confidence (highest first)
  - Min confidence filtering (default: 0.5)
  - Persistent storage (no TTL) in `long_term_memory` collection
  - Methods: `record_preference()`, `get_preferences()`, `get_preference()`, `delete_preference()`

- **Procedural Memory (Rules)** - Long-term storage of behavioral rules
  - Automatic extraction from natural language ("When I say done, complete my task")
  - Trigger normalization (case-insensitive)
  - Usage tracking (times_used auto-increments on match)
  - Sorted by usage count (most used first)
  - Persistent storage (no TTL) in `long_term_memory` collection
  - Methods: `record_rule()`, `get_rules()`, `get_rule_for_trigger()`, `delete_rule()`

- **5-Panel Memory UI** - Streamlit sidebar now shows all 5 memory types:
  - 💭 **Working Memory** - Current project/task/action (2hr TTL)
  - 📝 **Episodic Memory** - Action history (persistent)
  - 🎯 **Semantic Memory** - Learned preferences (persistent)
  - ⚙️ **Procedural Memory** - Learned rules (persistent)
  - 🤝 **Shared Memory** - Agent handoffs (5min TTL)

- **Memory Statistics** - Stats breakdown by all 5 types:
  - Working, Episodic, Semantic, Procedural, Shared counts
  - Visual metrics grid in sidebar
  - Enhanced debug panel with memory type indicators

#### Added - Testing & Documentation
- **Unit Tests** (`tests/test_memory_types.py`) - 13 tests:
  - Semantic memory CRUD operations (6 tests)
  - Procedural memory CRUD operations (6 tests)
  - Memory stats by type (1 test)

- **Integration Tests** (`tests/integration/memory/`) - 14 tests:
  - Context injection from all 5 memory types
  - Coordinator extraction (preferences & rules)
  - Rule trigger matching
  - End-to-end flows for preferences and rules
  - Memory competencies validation

- **Comprehensive Documentation** (`docs/MEMORY.md`):
  - 5-tier memory architecture overview
  - Complete API reference for all memory types
  - Schema definitions with examples
  - Usage guide for developers and end users
  - Testing methodology

#### Changed - Coordinator Integration
- **Context Extraction** - `_extract_context_from_turn()` completely rewritten:
  - Working memory extracted from tool calls (current project/task)
  - Preferences extracted via `record_preference()` to long-term
  - Rules extracted via `record_rule()` to long-term
  - No longer stores preferences/rules in session_context

- **Context Injection** - `_build_context_injection()` updated:
  - Loads working memory from `session_context` (short-term)
  - Loads preferences from `get_preferences()` (long-term)
  - Loads rules from `get_rules()` (long-term)
  - Loads disambiguation from shared memory
  - Changed XML tag from `<session_context>` to `<memory_context>`

- **Rule Trigger Checking** - `_check_rule_triggers()` updated:
  - Reads from long-term procedural memory instead of session_context
  - Case-insensitive matching
  - Auto-increments times_used on match

#### Added - Database & Indexes
- **MongoDB Indexes**:
  - `user_id + memory_type + semantic_type + key` - Semantic memory lookups
  - `user_id + memory_type + trigger_pattern` - Procedural memory lookups
  - Index creation wrapped in try-except for graceful conflict handling

- **Memory Type Constants** - `LONG_TERM_TYPES` mapping:
  - episodic → action (what happened)
  - semantic → preference (what I know)
  - procedural → rule (how to act)

#### Fixed
- **Index Conflicts** - Wrapped all `create_index()` calls in try-except to handle existing indexes
- **Regex Patterns** - Fixed rule trigger extraction to stop at commas

#### Project Organization
- **Test Scripts Relocated** - Moved 14 test scripts from root to `tests/integration/memory/`
- **Documentation Consolidated** - Created comprehensive `docs/MEMORY.md`, archived old memory docs
- **Session Summaries Organized** - Created `session_summaries/archive/` for older summaries
- **README Updates** - Updated main README and all sub-directory READMEs

### Technical Details
**Total Tests:** 240+ (13 new unit tests + 14 existing integration tests organized)
**New Files:** 3 (MEMORY.md, test_memory_types.py, session_summaries/README.md)
**Modified Files:** 5 (manager.py, coordinator.py, streamlit_app.py, README.md, tests/README.md)
**Lines Added:** ~2,500
**Commits:** 7 major commits in Milestone 5

---

## [3.1.10] - 2026-01-06

### Added
- Search mode variants in main app (hybrid, vector, text)
- Four new search methods in retrieval agent:
  - `vector_search_tasks()` - Vector-only semantic search (~280ms)
  - `text_search_tasks()` - Text-only keyword search (~180ms)
  - `vector_search_projects()` - Vector search for projects
  - `text_search_projects()` - Text search for projects
- Debug panel now shows search mode metadata (mode, target, query, results)
- Updated slash command handler to parse mode and target from args

### Changed
- Search commands now support mode specification:
  - `/search <query>` - Hybrid (default)
  - `/search vector <query>` - Vector-only
  - `/search text <query>` - Text-only
- Enhanced `mongodb_op_type_map` for search operation display in debug panel

## [3.1.9] - 2026-01-06

### Added
- Search mode variant tests (IDs 41-46) to evals test suite
  - Tests 41-43: Vector-only search variants
  - Tests 44-46: Text-only search variants
- Search Mode Comparison chart in Impact Analysis section
- Two new intent groups in Comparison Matrix:
  - "Search: Vector Only (Semantic)"
  - "Search: Text Only (Keyword)"
- `render_search_mode_comparison()` function for visualizing search performance

### Changed
- Test suite expanded from 40 to 46 queries
- Added sixth section: Search Mode Variants

## [3.1.8] - 2026-01-06

### Changed
- Moved optimization asterisks from column headers to slash command values
- Slash command values in optimization columns now display as: `*90ms*`, `*86ms*`
- Updated footnote to reference value asterisks instead of column asterisks
- Cleaner column headers in Comparison Matrix (removed `<sup>*</sup>` tags)

## [3.1.7] - 2026-01-06

### Added
- Visual indicators showing optimizations don't apply to slash commands
- Gray italic formatting for slash command values in optimization columns
- Asterisks around slash values to mark them as "not applicable"
- Explanatory footnote in Comparison Matrix

### Changed
- Enhanced visual distinction between LLM queries and direct DB operations
- Improved dashboard clarity for optimization impact analysis

## [3.1.6] - 2026-01-05

### Fixed
- Removed misleading optimization "improvements" for slash commands
- Slash commands now show "⚡ Direct DB" in Best column instead of fake optimization configs
- Optimization Waterfall now excludes slash commands (shows only LLM query optimization)
- Updated waterfall tooltip to clarify it excludes slash commands

### Changed
- Comparison Matrix no longer highlights slash command values (variation is MongoDB noise, not optimization)
- Dashboard now accurately shows optimization impact only on LLM queries
- True optimization gains visible: text queries improved 50-65% with context optimizations

## [3.1.0] - 2025-12-XX

### Milestone 3 - Evals Dashboard Complete

Major release introducing comprehensive evaluation framework for measuring optimization impact.

#### Added - Evaluation System
- **Separate Evals Dashboard App** (`evals_app.py`) running on port 8502
- **46-Query Test Suite** covering:
  - Slash commands (10 tests)
  - Text queries (8 tests)
  - Text actions (10 tests)
  - Multi-turn context (5 tests)
  - Voice input (7 tests)
  - Search mode variants (6 tests)
- **Multi-Config Comparison** - Run same tests across different optimization configurations
- **MongoDB Persistence** - Save/load comparison runs for historical analysis
- **JSON Export** - Export results for presentations and reports

#### Added - Visual Analytics
- **Comparison Matrix** - Side-by-side test results with best config highlighting
- **Optimization Waterfall** - Progressive impact of stacked optimizations
- **LLM vs MongoDB Time Breakdown** - Pie chart showing where time is spent
- **Search Mode Comparison** - Performance comparison of hybrid/vector/text search
- **Impact Analysis Charts** - Interactive Plotly visualizations

#### Added - Configuration System
- **5 Optimization Configs**:
  - Baseline: No optimizations
  - Compress: Tool result compression only
  - Streamlined: Streamlined prompt only
  - Caching: Prompt caching only
  - All Context: All optimizations combined
- **Config Toggle System** - Dynamic optimization switching
- **Performance Tracking** - Latency, tokens, cache hits, MongoDB time

#### Technical Implementation
- **New Module**: `evals/` with configs, test_suite, runner, storage, result classes
- **Test Execution**: Parallel test running with progress tracking
- **Result Storage**: MongoDB collection for historical comparison
- **Data Models**: Pydantic models for type-safe result handling

#### Key Insights Revealed
- **Slash Commands**: ~100ms, bypass LLM (no optimization benefit)
- **Text Queries**: 20-30s → 7-15s with optimizations (-50% to -65%)
- **MongoDB Performance**: Only 4% of total time (already fast)
- **LLM Bottleneck**: 96% of time spent in LLM thinking
- **Search Mode Tradeoffs**: Text (180ms) < Vector (280ms) < Hybrid (420ms)

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
