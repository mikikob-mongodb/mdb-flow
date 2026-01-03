# Slash Commands Test Suite

Comprehensive automated testing for all slash commands in the MDB Flow system.

## Overview

This test suite validates that all slash commands work correctly, return expected results, and have properly formatted output tables. Tests are based on the specification in `example-scripts/BACKSLASH_COMMANDS_TESTING_GUIDE.md`.

## Test Structure

### Test Files

- `test_slash_commands.py` - Main test suite with all slash command tests
- `conftest.py` - Pytest fixtures and test utilities

### Test Sections

1. **Section 1: Basic /tasks Queries** - Filter tests (status, priority, project)
2. **Section 2: /tasks search** - Hybrid search functionality
3. **Section 3: Temporal Queries** - today, yesterday, week, completed, stale
4. **Section 4: /projects Queries** - List all, get specific project
5. **Section 5: /projects search** - Project hybrid search
6. **Section 6: /search** - Direct search commands
7. **Section 7: /bench** - Benchmark commands
8. **Section 8: Column Validation** - Verify table formatting
9. **Section 9: Utility Commands** - Help and other utilities

## Running Tests

### Quick Start

```bash
# Run all slash command tests
./scripts/test_slash_commands.sh

# Run with verbose output
./scripts/test_slash_commands.sh -v

# Run with coverage report
./scripts/test_slash_commands.sh --cov
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/test_slash_commands.py

# Run with verbose output
pytest tests/test_slash_commands.py -v

# Run specific test class
pytest tests/test_slash_commands.py::TestTasksBasicQueries

# Run specific test
pytest tests/test_slash_commands.py::TestTasksBasicQueries::test_list_all_tasks

# Run tests matching keyword
pytest tests/test_slash_commands.py -k "search"

# Run with coverage
pytest tests/test_slash_commands.py --cov=ui.slash_commands --cov-report=term-missing
```

### Test Runner Options

```bash
./scripts/test_slash_commands.sh [options]

Options:
  -v, --verbose          Verbose output
  -vv, --very-verbose    Very verbose output
  --cov, --coverage      Run with coverage report
  -k, --keyword EXPR     Run tests matching keyword expression
  -m, --marker MARKER    Run tests with specific marker
  --help                 Show help message

Examples:
  ./scripts/test_slash_commands.sh -v
  ./scripts/test_slash_commands.sh --cov
  ./scripts/test_slash_commands.sh -k test_filter
  ./scripts/test_slash_commands.sh -k TestTasksSearch
```

## Fixtures

### Core Fixtures

- `coordinator_instance` - Initialized coordinator (session scope)
- `executor` - SlashCommandExecutor instance (session scope)
- `execute_command` - Function to execute slash commands and return results

### Validation Fixtures

- `validate_table_columns` - Validate table has expected columns
- `validate_count_range` - Validate result count is within expected range

## Test Coverage

The test suite covers:

- ✅ All /tasks filter combinations (status, priority, project)
- ✅ Hybrid search for tasks and projects
- ✅ Temporal queries (today, yesterday, week, completed, stale)
- ✅ Project listing and detail views
- ✅ Direct /search commands
- ✅ Benchmark commands
- ✅ Column validation for proper formatting
- ✅ Help and utility commands

## Expected Results

Based on sample data, expected counts are:

| Query | Expected Count |
|-------|----------------|
| /tasks | 45-50 |
| /tasks status:todo | 25-30 |
| /tasks status:in_progress | 10-15 |
| /tasks status:done | 10-15 |
| /tasks priority:high | 10-15 |
| /tasks project:AgentOps | 5-8 |
| /projects | 10 |
| /projects search memory | 2-4 |
| /tasks search debugging | 3-8 |

## Continuous Integration

### Pre-commit Hook (Optional)

To run tests automatically before committing changes to slash command logic:

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run slash command tests if related files changed

# Check if slash command files were modified
if git diff --cached --name-only | grep -E "(ui/slash_commands.py|ui/formatters.py)"; then
    echo "Running slash command tests..."
    ./scripts/test_slash_commands.sh
    
    if [ $? -ne 0 ]; then
        echo "Tests failed. Commit aborted."
        exit 1
    fi
fi
EOF

chmod +x .git/hooks/pre-commit
```

### GitHub Actions (Optional)

Add to `.github/workflows/test.yml`:

```yaml
- name: Test Slash Commands
  run: |
    source venv/bin/activate
    pytest tests/test_slash_commands.py -v
```

## Writing New Tests

### Basic Test Structure

```python
def test_my_slash_command(execute_command):
    """Test description."""
    result = execute_command("/my-command arg1 arg2")
    
    assert result["success"], f"Command failed: {result.get('error')}"
    
    data = result.get("result", [])
    # Add assertions...
```

### With Validation Fixtures

```python
def test_with_validation(execute_command, validate_count_range):
    """Test with count validation."""
    result = execute_command("/tasks")
    
    assert result["success"]
    assert validate_count_range(result, min_count=40, max_count=60)
```

## Troubleshooting

### Tests Fail with Import Errors

Ensure you're in the project root and virtual environment is activated:

```bash
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### MongoDB Connection Issues

Ensure MongoDB is running and `MONGODB_URI` is set in `.env`:

```bash
# Check MongoDB connection
python -c "from shared.db import get_collection; print('Connected!')"
```

### Coordinator Not Initialized

The coordinator is initialized once per session. If tests fail, check:

1. `.env` file has all required keys (OPENAI_API_KEY, MONGODB_URI)
2. MongoDB collections exist (tasks, projects)
3. Sample data is loaded

## Maintenance

### When to Update Tests

Update tests when:

- Adding new slash commands
- Modifying command behavior
- Changing table formatting
- Adding new filters or query options
- Fixing bugs in slash command logic

### Test Philosophy

- Tests should be **independent** - order doesn't matter
- Tests should be **deterministic** - same input = same output
- Tests should be **fast** - use session-scoped fixtures
- Tests should **validate behavior**, not implementation details

## References

- Test Specification: `example-scripts/BACKSLASH_COMMANDS_TESTING_GUIDE.md`
- Slash Commands Implementation: `ui/slash_commands.py`
- Table Formatters: `ui/formatters.py`
- pytest Documentation: https://docs.pytest.org/
