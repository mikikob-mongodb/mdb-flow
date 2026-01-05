# Flow Companion Test Suite

Comprehensive test suite for MDB Flow implementing all 210 tests from `FULL_COMPANION_TEST_SUITE_GUIDE.md`.

## Current Status

**Implemented: ~146 / 210 tests (70%)**

### Completed Sections
- ✅ **Section 1: Database & Connection** (8/8 tests) - `unit/test_database.py`
- ✅ **Section 2: Retrieval Agent** (18/18 tests) - `agents/test_retrieval_agent.py`
- ✅ **Section 3: Worklog Agent** (12/12 tests) - `agents/test_worklog_agent.py`
- ✅ **Section 4: Vector Search** (10/10 tests) - `search/test_vector_search.py`
- ✅ **Section 5: Hybrid Search** (12/12 tests) - `search/test_hybrid_search.py`
- ✅ **Section 6: Coordinator Agent** (20/20 tests) - `agents/test_coordinator.py`
- ✅ **Section 9: Multi-turn Conversations** (12/12 tests) - `integration/test_multiturn_conversations.py`
- ✅ **Section 14: Backslash Commands** (34/40 tests) - `ui/test_slash_commands.py`
- ✅ **Section 15: Performance/Latency** (12/12 tests) - `performance/test_latency.py`
- ✅ **Critical Regression Tests** (6/8 tests) - `regression/test_critical_regressions.py`

### In Progress / TODO
- 🔄 **Section 7: Text Input** (0/15 tests) - `integration/test_text_input_flow.py` - TODO
- 🔄 **Section 8: Voice Input** (0/15 tests) - `integration/test_voice_input_flow.py` - TODO
- 🔄 **Section 10: Temporal Queries** (0/10 tests) - `search/test_temporal_queries.py` - TODO
- 🔄 **Section 11: Confirmation Flow** (0/8 tests) - `integration/test_confirmation_flow.py` - TODO
- 🔄 **Section 12: Response Formatting** (0/8 tests) - `ui/test_response_formatting.py` - TODO
- 🔄 **Section 13: Debug Panel** (0/10 tests) - `ui/test_debug_panel.py` - TODO
- 🔄 **Section 16: Error Handling** (0/10 tests) - `integration/test_error_handling.py` - TODO
- 🔄 **Unit Tests** - Models (0/5), Embeddings (0/3), Audio (0/4), LLM Service (0/6)

## Directory Structure

```
tests/
├── conftest.py                          # Global fixtures and test configuration
├── README.md                            # This file
├── FULL_COMPANION_TEST_SUITE_GUIDE.md  # Complete test specification
│
├── unit/                                # Unit tests for individual components
│   ├── __init__.py
│   ├── test_database.py                 # ✅ Section 1: Database & Connection (8 tests)
│   ├── test_models.py                   # TODO: Model validation (5 tests)
│   ├── test_embeddings.py               # TODO: Embedding generation (3 tests)
│   ├── test_audio.py                    # TODO: Audio transcription (4 tests)
│   └── test_llm_service.py              # TODO: LLM API integration (6 tests)
│
├── agents/                              # Agent-level tests
│   ├── __init__.py
│   ├── test_retrieval_agent.py          # ✅ Section 2: Retrieval Agent (18 tests)
│   ├── test_worklog_agent.py            # ✅ Section 3: Worklog Agent (12 tests)
│   ├── test_coordinator.py              # ✅ Section 6: Coordinator Agent (20 tests)
│   └── test_coordinator_routing.py      # TODO: Tool selection (8 tests)
│
├── search/                              # Search functionality tests
│   ├── __init__.py
│   ├── test_vector_search.py            # ✅ Section 4: Vector Search (10 tests)
│   ├── test_hybrid_search.py            # ✅ Section 5: Hybrid Search (12 tests)
│   ├── test_fuzzy_matching.py           # TODO: Fuzzy matching (6 tests)
│   └── test_temporal_queries.py         # TODO: Section 10: Temporal Queries (10 tests)
│
├── integration/                         # End-to-end integration tests
│   ├── __init__.py
│   ├── test_text_input_flow.py          # TODO: Section 7: Text Input (15 tests)
│   ├── test_voice_input_flow.py         # TODO: Section 8: Voice Input (15 tests)
│   ├── test_confirmation_flow.py        # TODO: Section 11: Confirmation Flow (8 tests)
│   ├── test_multiturn_conversations.py  # ✅ Section 9: Multi-turn (12 tests)
│   └── test_error_handling.py           # TODO: Section 16: Error Handling (10 tests)
│
├── ui/                                  # UI and interface tests
│   ├── __init__.py
│   ├── test_slash_commands.py           # ✅ Section 14: Backslash Commands (34/40 tests)
│   ├── README_SLASH_TESTS.md            # Slash command test documentation
│   ├── test_response_formatting.py      # TODO: Section 12: Formatting (8 tests)
│   └── test_debug_panel.py              # TODO: Section 13: Debug Panel (10 tests)
│
├── performance/                         # Performance and benchmark tests
│   ├── __init__.py
│   ├── test_latency.py                  # ✅ Section 15: Performance/Latency (12 tests)
│   └── test_benchmarks.py               # TODO: Additional benchmarks
│
├── regression/                          # Critical regression tests
│   ├── __init__.py
│   └── test_critical_regressions.py     # ✅ 8 critical bug prevention tests
│
└── fixtures/                            # Test data and fixtures
    ├── __init__.py
    ├── sample_audio_files/              # Sample WAV files for voice tests
    ├── mock_data.py                     # ✅ Mock data factories
    └── test_helpers.py                  # ✅ Shared test utilities
```

## Running Tests

### Run All Tests
```bash
# Run entire test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

### Run Specific Sections
```bash
# Unit tests only
pytest tests/unit/

# Database tests
pytest tests/unit/test_database.py

# Retrieval agent tests
pytest tests/agents/test_retrieval_agent.py

# Slash command tests
pytest tests/ui/test_slash_commands.py

# Run specific test class
pytest tests/agents/test_retrieval_agent.py::TestBasicTaskQueries

# Run specific test
pytest tests/unit/test_database.py::TestMongoDBConnection::test_mongodb_connection
```

### Run by Priority
```bash
# Priority 1 (CRITICAL) tests
pytest tests/unit/test_database.py tests/agents/test_retrieval_agent.py

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/
```

## Test Fixtures

### Database Fixtures (Session-scoped)
- `db_client` - MongoDB client
- `db` - flow_companion database
- `tasks_collection` - Tasks collection
- `projects_collection` - Projects collection

### Agent Fixtures (Session-scoped)
- `coordinator_instance` - Coordinator agent
- `retrieval_agent` - Retrieval agent
- `worklog_agent` - Worklog agent
- `executor` - SlashCommandExecutor

### Test Data Creation Fixtures
**IMPORTANT: Always use these fixtures when creating test data**

- `create_test_task(title, project_id=None, **kwargs)` - Create task marked as test data
  - Automatically sets `is_test=True` flag
  - Returns task ID
  - Example: `task_id = create_test_task("Test task", project_id=project_id, status="todo")`

- `create_test_project(name, **kwargs)` - Create project marked as test data
  - Automatically sets `is_test=True` flag
  - Returns project ID
  - Example: `project_id = create_test_project("Test Project", description="Test")`

### Mock Data Factories
- `task_factory` - Create test tasks
- `project_factory` - Create test projects
- `conversation_factory` - Create conversation histories
- `activity_log_factory` - Create activity log entries

### Test Helpers
- `assert_all_have_field` - Assert all items have field
- `assert_all_match` - Assert all items match condition
- `assert_sorted_by` - Assert items are sorted
- `measure_execution_time` - Measure function execution time
- `assert_execution_time_under` - Assert function executes within threshold

## Writing New Tests

### Test File Template
```python
"""
<Component> Tests

Section X from FULL_COMPANION_TEST_SUITE_GUIDE.md
Tests: N total

Covers:
- Feature 1
- Feature 2
"""

import pytest


class TestFeatureGroup:
    """Test specific feature group."""

    def test_specific_behavior(self, required_fixtures):
        """
        Test description.
        
        Scenario:
            <Describe the test scenario>
        
        Expected:
            <Expected behavior>
        
        Edge cases:
            - Edge case 1
            - Edge case 2
        """
        # Arrange
        # Act
        # Assert
```

### Test Naming Convention
```python
# Pattern: test_<component>_<scenario>_<expected_result>
test_retrieval_get_tasks_by_status_returns_filtered_results()
test_voice_input_informal_reference_finds_correct_task()
test_confirmation_single_match_asks_for_confirmation()
```

### Using Test Data Fixtures
```python
def test_with_test_data(create_test_task, create_test_project):
    """Example test using test data fixtures."""
    # Create test project (automatically marked is_test=True)
    project_id = create_test_project(
        name="Test Project",
        description="Test project description"
    )

    # Create test task (automatically marked is_test=True)
    task_id = create_test_task(
        title="Test Task",
        project_id=project_id,
        status="in_progress",
        priority="high"
    )

    # Test logic here...
    # Production queries will automatically exclude this test data
```

## Test Coverage Goals

### By Component
- **Database & Models:** 95%+ coverage
- **Agents:** 90%+ coverage
- **Search:** 85%+ coverage
- **Integration Flows:** 80%+ coverage
- **UI:** 75%+ coverage

### By Section (from Guide)
- ✅ Section 1: Database & Connection (8/8 = 100%)
- ✅ Section 2: Retrieval Agent (18/18 = 100%)
- ✅ Section 3: Worklog Agent (12/12 = 100%)
- ✅ Section 4: Vector Search (10/10 = 100%)
- ✅ Section 5: Hybrid Search (12/12 = 100%)
- ✅ Section 6: Coordinator Agent (20/20 = 100%)
- ⬜ Section 7: Text Input (0/15 = 0%)
- ⬜ Section 8: Voice Input (0/15 = 0%)
- ✅ Section 9: Multi-turn (12/12 = 100%)
- ⬜ Section 10: Temporal Queries (0/10 = 0%)
- ⬜ Section 11: Confirmation Flow (0/8 = 0%)
- ⬜ Section 12: Response Formatting (0/8 = 0%)
- ⬜ Section 13: Debug Panel (0/10 = 0%)
- ✅ Section 14: Backslash Commands (34/40 = 85%)
- ✅ Section 15: Performance (12/12 = 100%)
- ⬜ Section 16: Error Handling (0/10 = 0%)

**Total: 146/210 tests (70%)**

### Critical Regression Tests
- ✅ LLM message format bug prevention (extra fields stripped)
- ✅ Voice input JSON cleanup bug prevention (markdown stripping)
- ✅ Vector search index name bug prevention
- ✅ Coordinator input_type parameter acceptance
- ✅ Conversation history threading
- ✅ Tool-use message format validation

## Next Steps

### Priority 1 (CRITICAL)
Implement these tests next to achieve core functionality coverage:

1. **agents/test_worklog_agent.py** (12 tests)
   - Status updates (complete, start, stop)
   - Activity logging
   - Note management
   - Task creation

2. **agents/test_coordinator_agent.py** (20 tests)
   - Tool selection logic
   - Query parsing
   - Voice vs text parity
   - Error handling

3. **integration/test_voice_input_flow.py** (15 tests)
   - Audio transcription
   - Voice queries
   - Informal references
   - Confirmation flow

4. **integration/test_confirmation_flow.py** (8 tests)
   - Single/multiple match handling
   - User selections
   - Cancellation

5. **integration/test_error_handling.py** (10 tests)
   - Invalid input
   - Not found scenarios
   - API errors

### Priority 2
Once Priority 1 is complete:

1. **search/test_vector_search.py** (10 tests)
2. **search/test_hybrid_search.py** (12 tests)
3. **integration/test_text_input_flow.py** (15 tests)
4. **integration/test_multiturn_conversations.py** (12 tests)
5. **search/test_temporal_queries.py** (10 tests)

### Priority 3
Final sections for complete coverage:

1. **performance/test_latency.py** (12 tests)
2. **ui/test_response_formatting.py** (8 tests)
3. **ui/test_debug_panel.py** (10 tests)
4. **unit/** remaining tests (18 tests)

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Test Suite
  run: |
    pytest tests/ -v --cov=. --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Test Data Management

### Test Data Isolation

All test data is automatically isolated from production data using the `is_test` flag:

- **Tasks and Projects models** have an `is_test: bool` field (defaults to `False`)
- **Production queries** automatically filter out test data with `{"is_test": {"$ne": True}}`
- **Test fixtures** (`create_test_task`, `create_test_project`) always set `is_test=True`

### Benefits

1. **No Pollution**: Tests can create data freely without affecting production queries
2. **Automatic Filtering**: All production code automatically excludes test data
3. **Easy Cleanup**: Simple query to remove all test data
4. **Debugging**: Can toggle test data visibility when needed

### Cleaning Up Test Data

To remove test data created during testing:

```bash
# Mark test-like data and optionally delete
python scripts/cleanup_test_data.py
```

The script will:
1. Mark test-like patterns, orphans, and invalid references with `is_test=True`
2. Ask for confirmation before deleting
3. Show counts of production vs test data

Manual cleanup:
```python
# In MongoDB shell or Python
db.tasks.delete_many({"is_test": True})
db.projects.delete_many({"is_test": True})
```

### Writing Tests with Test Data

**Always use the test fixtures:**

```python
def test_example(create_test_task, create_test_project):
    """Example showing proper test data creation."""
    # Create test project (automatically marked is_test=True)
    project_id = create_test_project("Test Project")

    # Create test task (automatically marked is_test=True)
    task_id = create_test_task(
        "Test Task",
        project_id=project_id,
        status="todo",
        priority="high"
    )

    # Your test logic here...
    # Production queries will NOT see this test data
```

**Don't manually insert test data:**
```python
# ❌ BAD - Creates production data during tests
tasks_collection.insert_one({"title": "Test", "status": "todo"})

# ✅ GOOD - Uses fixture that marks as test data
task_id = create_test_task("Test", status="todo")
```

## Test Philosophy

1. **Independent Tests**: Each test can run in any order
2. **Deterministic**: Same input always produces same output
3. **Fast**: Unit tests < 100ms, integration tests < 1s
4. **Clear**: Every test has docstring explaining scenario
5. **Edge Cases**: Critical edge cases are documented and tested
6. **Isolated Data**: All test data marked with `is_test=True` flag

## Migration from Old Test Files

The following files from the old flat structure have been reorganized:

### Extracted and Migrated
- **test_core_functionality.py** → Extracted to:
  - `regression/test_critical_regressions.py` (8 critical bug prevention tests)
  - Remaining tests planned for `unit/test_llm_service.py`, `unit/test_models.py`, `unit/test_audio.py`

### Moved to scripts/debug/
These were debug scripts, not proper tests:
- **debug_agent.py** → `scripts/debug/debug_agent.py`
- **test_hybrid_search.py** → `scripts/debug/test_hybrid_search.py`
- **test_voice_flow.py** → `scripts/debug/test_voice_flow.py`
- **test_tool_coordinator.py** → `scripts/debug/test_tool_coordinator.py`

### Reorganized
- **test_slash_commands.py** → `ui/test_slash_commands.py`
- **README_SLASH_TESTS.md** → `ui/README_SLASH_TESTS.md`

## References

- **Test Specification**: `FULL_COMPANION_TEST_SUITE_GUIDE.md`
- **Slash Command Tests**: `ui/README_SLASH_TESTS.md`
- **Mock Data**: `fixtures/mock_data.py`
- **Test Helpers**: `fixtures/test_helpers.py`
- **Debug Scripts**: `../scripts/debug/README.md`
- **pytest Documentation**: https://docs.pytest.org/
