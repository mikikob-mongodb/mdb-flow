# Debug Scripts

Manual testing and debugging scripts moved from /tests directory.

These are NOT automated tests - they're interactive debugging tools.

## Scripts

- **debug_agent.py** - Test agent behavior vs direct database queries
- **test_hybrid_search.py** - Manually test hybrid search with specific queries
- **test_voice_flow.py** - Manually test voice input processing
- **test_tool_coordinator.py** - Manually test coordinator with voice/text input

## Usage

```bash
# Run from project root
python scripts/debug/debug_agent.py
python scripts/debug/test_hybrid_search.py
python scripts/debug/test_voice_flow.py
python scripts/debug/test_tool_coordinator.py
```

## Note

For automated testing, see `/tests` directory with pytest-based test suite.
