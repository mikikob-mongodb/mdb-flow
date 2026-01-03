# Flow Companion Test Suite

Comprehensive test suite for MDB Flow implementing all 210 tests from `FULL_COMPANION_TEST_SUITE_GUIDE.md`.

## Current Status

**Implemented: ~60 / 210 tests (29%)**

### Completed Sections
- ✅ **Section 1: Database & Connection** (8/8 tests) - `unit/test_database.py`
- ✅ **Section 2: Retrieval Agent** (18/18 tests) - `agents/test_retrieval_agent.py`  
- ✅ **Section 14: Backslash Commands** (34/40 tests) - `ui/test_slash_commands.py`

### In Progress
- 🔄 **Section 3: Worklog Agent** (0/12 tests) - `agents/test_worklog_agent.py` - TODO
- 🔄 **Section 6: Coordinator Agent** (0/20 tests) - `agents/test_coordinator_agent.py` - TODO
- 🔄 **Section 4-5: Vector & Hybrid Search** (0/22 tests) - `search/` - TODO
- 🔄 **Section 8: Voice Input** (0/15 tests) - `integration/test_voice_input_flow.py` - TODO
- 🔄 **Section 11: Confirmation Flow** (0/8 tests) - `integration/test_confirmation_flow.py` - TODO
- 🔄 **Section 16: Error Handling** (0/10 tests) - `integration/test_error_handling.py` - TODO

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
│   ├── test_worklog_agent.py            # TODO: Section 3: Worklog Agent (12 tests)
│   ├── test_coordinator_agent.py        # TODO: Section 6: Coordinator Agent (20 tests)
│   └── test_coordinator_routing.py      # TODO: Tool selection (8 tests)
│
├── search/                              # Search functionality tests
│   ├── __init__.py
│   ├── test_vector_search.py            # TODO: Section 4: Vector Search (10 tests)
│   ├── test_hybrid_search.py            # TODO: Section 5: Hybrid Search (12 tests)
│   ├── test_fuzzy_matching.py           # TODO: Fuzzy matching (6 tests)
│   └── test_temporal_queries.py         # TODO: Section 10: Temporal Queries (10 tests)
│
├── integration/                         # End-to-end integration tests
│   ├── __init__.py
│   ├── test_text_input_flow.py          # TODO: Section 7: Text Input (15 tests)
│   ├── test_voice_input_flow.py         # TODO: Section 8: Voice Input (15 tests)
│   ├── test_confirmation_flow.py        # TODO: Section 11: Confirmation Flow (8 tests)
│   ├── test_multiturn_conversations.py  # TODO: Section 9: Multi-turn (12 tests)
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
│   ├── test_latency.py                  # TODO: Section 15: Performance (12 tests)
│   └── test_benchmarks.py               # TODO: Additional benchmarks
│
├── regression/                          # Critical regression tests
│   ├── __init__.py
│   └── test_critical_regressions.py     # TODO: From test_core_functionality.py
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

### Using Factories
```python
def test_with_mock_data(task_factory, projects_collection):
    """Example test using factories."""
    # Create test data
    project = project_factory.create(name="Test Project")
    projects_collection.insert_one(project)
    
    task = task_factory.create_with_project(
        project, 
        title="Test Task",
        status="in_progress"
    )
    tasks_collection.insert_one(task)
    
    # Test logic here...
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
- ⬜ Section 3: Worklog Agent (0/12 = 0%)
- ⬜ Section 4: Vector Search (0/10 = 0%)
- ⬜ Section 5: Hybrid Search (0/12 = 0%)
- ⬜ Section 6: Coordinator Agent (0/20 = 0%)
- ⬜ Section 7: Text Input (0/15 = 0%)
- ⬜ Section 8: Voice Input (0/15 = 0%)
- ⬜ Section 9: Multi-turn (0/12 = 0%)
- ⬜ Section 10: Temporal Queries (0/10 = 0%)
- ⬜ Section 11: Confirmation Flow (0/8 = 0%)
- ⬜ Section 12: Response Formatting (0/8 = 0%)
- ⬜ Section 13: Debug Panel (0/10 = 0%)
- ✅ Section 14: Backslash Commands (34/40 = 85%)
- ⬜ Section 15: Performance (0/12 = 0%)
- ⬜ Section 16: Error Handling (0/10 = 0%)

**Total: 60/210 tests (29%)**

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

## Test Philosophy

1. **Independent Tests**: Each test can run in any order
2. **Deterministic**: Same input always produces same output
3. **Fast**: Unit tests < 100ms, integration tests < 1s
4. **Clear**: Every test has docstring explaining scenario
5. **Edge Cases**: Critical edge cases are documented and tested

## References

- **Test Specification**: `FULL_COMPANION_TEST_SUITE_GUIDE.md`
- **Slash Command Tests**: `ui/README_SLASH_TESTS.md`
- **Mock Data**: `fixtures/mock_data.py`
- **Test Helpers**: `fixtures/test_helpers.py`
- **pytest Documentation**: https://docs.pytest.org/
