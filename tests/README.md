# Test Suite for mdb-flow

This directory contains the test suite for the mdb-flow project, ensuring core functionality works correctly and preventing regressions.

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_core_functionality.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

### 1. LLM Integration Tests
- ✅ Basic generation
- ✅ Conversation history
- ✅ **CRITICAL**: Message format validation (prevents BadRequestError from extra fields like `input_type`)
- ✅ Tool-based generation

### 2. Model Tests
- ✅ Task model creation and serialization
- ✅ Project model creation and serialization
- ✅ ActivityLogEntry with voice-specific fields

### 3. Voice Parsing Tests (Milestone 2)
- ✅ JSON cleanup (handles markdown-wrapped responses)
- ✅ Completion extraction
- ✅ Task reference matching

### 4. Audio Transcription Tests
- ✅ Successful transcription (mocked)
- ✅ Empty audio handling
- ✅ Missing API key handling

### 5. Fuzzy Matching Tests
- ✅ Text similarity scoring
- ✅ Informal reference matching ("debugging doc" → "Create debugging methodologies doc")

### 6. Integration Tests
- ✅ Coordinator accepts `input_type` parameter
- ✅ Conversation history maintenance

### 7. Critical Regression Tests
- ✅ **Vector search index name** (prevents 0-results bug from index name mismatch)
- ✅ Session state structure documentation

## Critical Tests for Regression Prevention

These tests prevent specific bugs that occurred during development:

### Test: `test_llm_messages_format`
**Prevents**: `anthropic.BadRequestError: messages.0.input_type: Extra inputs are not permitted`

Ensures only `role` and `content` fields are sent to the Anthropic API by verifying the message cleanup logic in `shared/llm.py`.

### Test: `test_vector_search_index_name`
**Prevents**: Vector search returning 0 results due to incorrect index names

Verifies that the retrieval agent uses the correct Atlas index name `vector_index` instead of incorrect names like `task_embedding_index` or `project_embedding_index`.

### Test: `test_parse_voice_input_json_cleanup`
**Prevents**: JSON parsing errors when Claude returns markdown-wrapped responses

Ensures the voice parsing logic can handle responses wrapped in ` ```json ... ``` ` blocks.

## Test Fixtures (conftest.py)

- `sample_task`: Standard task for testing
- `sample_completed_task`: Completed task
- `sample_project`: Standard project
- `mock_tasks_collection`: Mocked MongoDB tasks collection
- `mock_projects_collection`: Mocked MongoDB projects collection
- `mock_llm_service`: Mocked LLM for testing without API calls
- `mock_embedding_service`: Mocked Voyage AI embeddings
- `mock_whisper_client`: Mocked OpenAI Whisper client

## Adding New Tests

When adding new features:

1. Add tests to `test_core_functionality.py` or create a new test file
2. Use existing fixtures from `conftest.py` where possible
3. Mock external API calls (Anthropic, Voyage AI, OpenAI)
4. Run tests before committing: `pytest tests/ -v`

## CI/CD Integration

These tests should run automatically before any PR merge to prevent regressions.

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```
