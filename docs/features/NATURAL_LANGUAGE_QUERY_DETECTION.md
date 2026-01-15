# Natural Language Query Detection

## Overview

The Flow Companion demo app uses a **hybrid architecture** that combines fast pattern matching with LLM-powered agents to provide the best of both worlds: instant responses for common queries and flexible reasoning for complex requests.

## The Problem

Before implementing natural language query detection, users encountered this frustrating flow:

```
User: "What's in progress?"
System: I don't have a built-in tool for this request.
        Enable Experimental MCP Mode to let me try to figure it out.
```

This created a poor user experience for simple queries that should "just work" instantly.

## Architecture: Two Parallel Systems

The demo app has two distinct query processing systems:

### 1. Slash Commands (Fast Path)
- **Direct MongoDB queries** that bypass the LLM entirely
- **Instant execution** (~0ms latency, $0 cost)
- **Deterministic results** - same input always produces same output
- Examples: `/tasks status:in_progress`, `/projects`, `/search memory`

### 2. MCP Agents (Flexible Path)
- **LLM-powered reasoning** through the coordinator agent
- **Variable latency** (~500-2000ms, ~$0.001-0.01 per query)
- **Adaptive behavior** - can handle ambiguous or novel requests
- Requires explicit "Experimental MCP Mode" opt-in

**Key Limitation**: These systems are parallel, not integrated. The coordinator has access to MCP agent tools, but **cannot invoke slash commands**. Slash commands aren't exposed as tools to the LLM.

## The Solution: Natural Language Query Detection

We implemented a **pattern matching layer** that sits before both systems:

```
User Input
    ↓
Natural Language Detection (regex patterns)
    ↓
    ├─ Match found? → Convert to slash command → Execute instantly
    └─ No match? → Route to LLM coordinator (if MCP mode enabled)
```

### How It Works

The `detect_natural_language_query()` function uses regex patterns to detect common query patterns and convert them to equivalent slash commands:

**Status Queries**
- "What's in progress?" → `/tasks status:in_progress`
- "What's done?" → `/tasks status:done`
- "What's todo?" → `/tasks status:todo`

**Priority Queries**
- "What's high priority?" → `/tasks priority:high`
- "What's urgent?" → `/tasks priority:high`

**Project-Specific Queries**
- "What's in the Voice Agent project?" → `/tasks project:Voice Agent`
- Pattern extracts project name and constructs proper command

**General Status**
- "What's going on?" → `/tasks`
- "Status update" → `/tasks`

**Search Queries**
- "Find tasks about architecture" → `/search architecture`
- Pattern extracts search terms automatically

### Implementation Details

**Location**: `ui/slash_commands.py:detect_natural_language_query()`

```python
def detect_natural_language_query(user_input: str) -> Optional[str]:
    """
    Detect natural language queries that map to slash commands.
    Returns the equivalent slash command string, or None if no match.
    """
    import re
    query_lower = user_input.lower().strip()

    # Status queries
    if re.search(r'\b(what[\'s\s]+|show\s+|list\s+)?(in progress|in-progress|ongoing|current|working on)\b', query_lower):
        return "/tasks status:in_progress"

    # ... more patterns

    return None
```

**Integration Point**: `ui/demo_app.py:handle_input()`

```python
def handle_input(prompt: str):
    # First, try to detect natural language queries that map to slash commands
    nl_command = detect_natural_language_query(prompt)
    if nl_command:
        parsed_command = parse_slash_command(nl_command)
        # Execute slash command instantly
    else:
        # Fall back to explicit slash command parsing or MCP agents
```

## Why Not Let the Coordinator Handle This?

You might wonder: "Why not just teach the coordinator LLM to handle these queries?" Here's why this pattern-matching approach is better:

### 1. **No MCP Mode Opt-In Required**
Common queries should work immediately, without requiring users to enable experimental features.

### 2. **Latency & Cost**
- Pattern matching: ~0ms, $0
- LLM coordinator: ~500-2000ms, ~$0.001-0.01 per query

For simple queries like "What's in progress?", paying LLM costs and waiting is wasteful.

### 3. **Slash Commands Aren't Exposed to the Coordinator**
The coordinator has access to MCP agent tools (tasks_agent, projects_agent, etc.) but not slash commands. We'd need to:
- Expose slash commands as callable tools to the LLM
- Document all slash command syntax in the coordinator's system prompt
- Add logic to decide when to use slash commands vs. agents

This adds complexity and still has the latency/cost problem.

### 4. **Design Philosophy: Fast Path vs. Flexible Path**
The whole point of slash commands is instant, deterministic execution. Routing them through an LLM defeats that purpose.

### 5. **Common Pattern in Conversational UIs**
This hybrid approach mirrors successful patterns in other systems:
- **Alexa/Siri**: Wake word detection (fast) → Cloud LLM (flexible)
- **Search engines**: Direct answers (fast) → Web results (comprehensive)
- **IDEs**: Autocomplete (fast) → Copilot suggestions (flexible)

**Pattern matching for common cases → LLM for complex cases**

## Benefits of This Approach

### Speed
- Common queries execute instantly with no LLM overhead
- Users get immediate feedback for routine questions

### Cost Efficiency
- No LLM API calls for queries that can be pattern-matched
- Reserve expensive LLM processing for truly complex requests

### User Experience
- Natural language "just works" for common queries
- No need to learn slash command syntax
- No need to enable experimental modes for basic features

### Flexibility
- Still route to coordinator for ambiguous or complex queries
- Can easily extend patterns without touching LLM prompts
- Easy to debug and test (deterministic pattern matching)

## When to Use Each System

### Use Pattern Matching (This Feature) For:
- Common, well-defined queries with clear intent
- Status/filter queries: "What's in progress?", "Show high priority tasks"
- Project lookups: "What's in the X project?"
- Simple searches: "Find tasks about Y"

### Use Slash Commands Directly For:
- Power users who know the syntax
- Complex filters: `/tasks status:in_progress priority:high project:Alpha`
- Scripting or automation
- When you want explicit control

### Use MCP Agents (Coordinator) For:
- Ambiguous queries: "What should I work on next?"
- Multi-step operations: "Create a task and add it to the Voice Agent project"
- Questions requiring reasoning: "Which project has the most overdue tasks?"
- Novel requests that don't fit existing patterns

## Future Enhancements

Potential improvements to this system:

1. **Learning from Misses**: Log queries that don't match any pattern to identify new patterns to add

2. **Pattern Confidence Scores**: For ambiguous matches, could ask user to confirm or route to LLM

3. **Exposing Slash Commands to Coordinator**: Could make slash commands available as tools for the coordinator, creating a truly unified system

4. **Dynamic Pattern Generation**: Use an LLM offline to generate patterns from user queries, rather than hand-coding regex

5. **Multi-Language Support**: Extend patterns to support queries in different languages

## Testing

Natural language query detection is fully tested in `tests/ui/test_slash_commands.py`. The test suite verifies:
- Status query detection
- Priority query detection
- Project name extraction
- Search term extraction
- Proper slash command generation
- Integration with the slash command executor

All 57 tests pass, ensuring robust pattern matching behavior.

## Related Documentation

- [Slash Commands](SLASH_COMMANDS.md) - Direct MongoDB query system
- [MCP Agent](MCP_AGENT.md) - LLM-powered coordinator and agents
- [Multi-Step Intents](MULTI_STEP_INTENTS.md) - Complex multi-turn interactions

## Summary

Natural language query detection provides a smart routing layer that gives users the best of both worlds:
- **Fast, free responses** for common queries through pattern matching
- **Flexible, intelligent reasoning** for complex queries through LLM agents

This hybrid architecture is a proven pattern in conversational UIs, delivering superior UX compared to LLM-only or command-only approaches.
