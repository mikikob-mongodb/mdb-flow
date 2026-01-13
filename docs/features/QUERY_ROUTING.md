# Query Routing Architecture

## Overview

The Flow Companion demo app uses a **3-tier routing system** that intelligently decides how to handle user input. This architecture optimizes for speed, cost, and user experience by using the right tool for each type of query.

## The Three Tiers

```
User Input: "What's in progress?"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Natural Language Pattern Detection                 │
│ - Regex pattern matching                                   │
│ - Converts to slash commands                               │
│ - Latency: ~0ms | Cost: $0 | Success Rate: High           │
└─────────────────────────────────────────────────────────────┘
    ↓ (if no match)
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Explicit Slash Commands                            │
│ - Direct MongoDB queries                                   │
│ - Power user syntax                                        │
│ - Latency: ~0ms | Cost: $0 | Success Rate: 100%           │
└─────────────────────────────────────────────────────────────┘
    ↓ (if no match)
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: MCP Agent System                                   │
│ - LLM-powered coordinator                                  │
│ - Reasoning and tool use                                   │
│ - Latency: ~500-2000ms | Cost: ~$0.001-0.01 | Adaptive    │
│ - Requires "Experimental MCP Mode" enabled                 │
└─────────────────────────────────────────────────────────────┘
```

## Tier 1: Natural Language Pattern Detection

### Purpose
Catch common natural language queries and convert them to slash commands for instant execution.

### How It Works
The `detect_natural_language_query()` function uses regex patterns to match common query patterns:

**Pattern Categories**:
1. **Status Queries**: "What's in progress?", "What's done?"
2. **Priority Queries**: "What's high priority?", "What's urgent?"
3. **Project Detail**: "Show me the AgentOps project"
4. **Project Tasks**: "What's in the Voice Agent project?"
5. **General Status**: "What's going on?", "Status update"
6. **Search**: "Find tasks about debugging"

### Examples

| User Input | Detected Pattern | Converted Command |
|------------|------------------|-------------------|
| "What's in progress?" | Status query | `/tasks status:in_progress` |
| "What's high priority?" | Priority query | `/tasks priority:high` |
| "Show me the AgentOps project" | Project detail | `/projects AgentOps` |
| "What's in the Voice Agent project?" | Project tasks | `/tasks project:Voice Agent` |
| "What's going on?" | General status | `/tasks` |
| "Find tasks about debugging" | Search | `/search debugging` |

### Characteristics
- **Speed**: Instant (~0ms)
- **Cost**: Free ($0)
- **User Experience**: Natural language "just works"
- **Limitations**: Only handles predefined patterns
- **Flexibility**: Low (deterministic pattern matching)

### When This Tier Catches Queries
- Simple, well-defined queries
- Common patterns with clear intent
- Queries that map cleanly to slash commands

### When Queries Fall Through
- Novel phrasing not matching any pattern
- Ambiguous or complex questions
- Multi-step requests
- Questions requiring reasoning

## Tier 2: Explicit Slash Commands

### Purpose
Provide power users with direct control over MongoDB queries using command-line style syntax.

### How It Works
The `parse_slash_command()` function checks if input starts with `/` and parses the command syntax.

### Available Commands

**Task Commands**:
- `/tasks` - List all tasks
- `/tasks status:in_progress` - Filter by status
- `/tasks priority:high` - Filter by priority
- `/tasks project:AgentOps` - Filter by project
- `/tasks status:todo priority:high` - Multiple filters
- `/tasks search debugging` - Hybrid search

**Project Commands**:
- `/projects` - List all projects
- `/projects AgentOps` - Get project details
- `/projects search voice` - Search projects

**Search Commands**:
- `/search debugging` - Hybrid search (default)
- `/search:vector memory` - Vector-only search
- `/search:text error` - Text-only search
- `/search tasks debugging` - Search tasks only
- `/search projects voice` - Search projects only

**Action Commands**:
- `/do complete task-name` - Complete a task
- `/do start task-name` - Start a task
- `/do stop task-name` - Stop a task
- `/do note task-name "note text"` - Add note to task
- `/do create Task title` - Create new task

**Help**:
- `/help` - Show all commands
- `/help tasks` - Help for specific command

### Examples

```bash
# Simple filters
/tasks status:in_progress
/tasks priority:high
/projects

# Complex filters
/tasks status:todo priority:high project:AgentOps

# Search with modes
/search:vector semantic memory
/search:text exact match

# Actions
/do complete voice agent architecture
/do create "Write documentation for routing"
```

### Characteristics
- **Speed**: Instant (~0ms)
- **Cost**: Free ($0)
- **User Experience**: Requires learning syntax
- **Limitations**: Must start with `/`
- **Flexibility**: High (combinable filters, multiple modes)
- **Power**: Maximum control over queries

### When This Tier Catches Queries
- Input starts with `/`
- Always catches (100% success rate for valid syntax)

### When Queries Fall Through
- Never (slash commands are terminal - either execute or error)

## Tier 3: MCP Agent System

### Purpose
Handle complex, ambiguous, or novel queries that require reasoning, multi-step operations, or adaptive behavior.

### How It Works
The coordinator agent receives the query and:
1. Analyzes intent
2. Selects appropriate specialized agents
3. Orchestrates multi-step workflows
4. Uses tools to access data and perform actions
5. Returns synthesized response

### Available Agents
- **tasks_agent**: Task management operations
- **projects_agent**: Project management operations
- **memory_agent**: Memory system queries
- **search_agent**: Advanced search and discovery

### Examples That Route to Agents

**Complex Questions**:
```
"What should I work on next?"
"Which project has the most overdue tasks?"
"Summarize my progress this week"
"Why is the Voice Agent project taking so long?"
"What are the dependencies for task X?"
```

**Multi-Step Operations**:
```
"Create a task for refactoring and add it to Project Alpha"
"Move all high priority tasks from Project A to Project B"
"Archive completed projects from last quarter"
"Update all tasks in the Voice Agent project to high priority"
```

**Reasoning Required**:
```
"What's blocking the AgentOps project?"
"Do I have time to finish the presentation before the demo?"
"Which tasks should I delegate?"
"What's the critical path for shipping this feature?"
```

**Novel/Creative Requests**:
```
"Explain the memory system architecture"
"How do I use the slash commands?"
"What patterns do you see in my work habits?"
"Suggest a project structure for X"
```

**Conversational Follow-ups**:
```
"Tell me more about that"
"Why?"
"Can you elaborate?"
"What else?"
```

### Characteristics
- **Speed**: Variable (~500-2000ms)
- **Cost**: Per query (~$0.001-0.01)
- **User Experience**: Natural conversation, explanations
- **Limitations**: Requires MCP mode enabled
- **Flexibility**: Maximum (handles anything)
- **Power**: Reasoning, multi-step, adaptive

### When This Tier Catches Queries
- No pattern match in Tier 1
- Doesn't start with `/` (Tier 2)
- User has enabled "Experimental MCP Mode"

### When Queries Are Blocked
- MCP mode not enabled → Show "Enable MCP Mode" message

## Routing Decision Flow

Here's the complete decision tree for how queries are routed:

```python
def handle_input(prompt: str):
    # TIER 1: Try natural language detection
    nl_command = detect_natural_language_query(prompt)
    if nl_command:
        # Pattern matched → Convert to slash command
        parsed_command = parse_slash_command(nl_command)
        execute_slash_command(parsed_command)
        return  # DONE - never reaches agents

    # TIER 2: Try explicit slash command
    if prompt.startswith("/"):
        parsed_command = parse_slash_command(prompt)
        if parsed_command:
            execute_slash_command(parsed_command)
            return  # DONE - never reaches agents
        else:
            show_error("Invalid slash command syntax")
            return

    # TIER 3: Check if MCP mode enabled
    if st.session_state.get("mcp_enabled", False):
        # Route to coordinator agent
        response = coordinator.run(prompt)
        display_response(response)
    else:
        # Show MCP mode opt-in message
        show_mcp_prompt()
```

## Decision Tree Visual

```
User Input
    │
    ├─ Matches NL pattern? ──YES──> Tier 1: Convert to slash → Execute → DONE
    │
    NO
    │
    ├─ Starts with "/"? ──YES──> Tier 2: Parse slash → Execute → DONE
    │
    NO
    │
    └─ MCP enabled? ──YES──> Tier 3: Route to coordinator → DONE
                      │
                      NO
                      │
                      └─> Show "Enable MCP Mode" message
```

## Examples By Tier

### Tier 1 Catches (Natural Language → Slash Command)

| Query | Why Tier 1? | Result |
|-------|-------------|--------|
| "What's in progress?" | Status pattern match | `/tasks status:in_progress` |
| "Show me the AgentOps project" | Project detail pattern | `/projects AgentOps` |
| "Find tasks about memory" | Search pattern | `/search memory` |
| "What's urgent?" | Priority pattern | `/tasks priority:high` |

### Tier 2 Catches (Explicit Slash Commands)

| Query | Why Tier 2? | Result |
|-------|-------------|--------|
| `/tasks` | Starts with `/` | Direct execution |
| `/projects AgentOps` | Starts with `/` | Direct execution |
| `/do complete voice app` | Starts with `/` | Direct execution |
| `/search:vector memory` | Starts with `/` | Direct execution |

### Tier 3 Catches (MCP Agents - If Enabled)

| Query | Why Tier 3? | Agent Used |
|-------|-------------|------------|
| "What should I work on?" | Requires reasoning | coordinator → tasks_agent |
| "Summarize my progress" | Multi-step analysis | coordinator → multiple agents |
| "Why is X taking so long?" | Causal reasoning | coordinator → tasks_agent |
| "Create task and assign it" | Multi-step operation | coordinator → tasks_agent |

### Falls Through (MCP Mode Disabled)

| Query | Why Blocked? | Message Shown |
|-------|--------------|---------------|
| "What should I work on?" | No pattern, MCP disabled | "Enable Experimental MCP Mode" |
| "Tell me more" | No pattern, MCP disabled | "Enable Experimental MCP Mode" |
| "How does this work?" | No pattern, MCP disabled | "Enable Experimental MCP Mode" |

## Performance Comparison

| Tier | Avg Latency | Cost Per Query | Success Rate | Use Case |
|------|-------------|----------------|--------------|----------|
| Tier 1 | ~0ms | $0 | ~40-60% of common queries | Natural language patterns |
| Tier 2 | ~0ms | $0 | 100% (valid syntax) | Power user commands |
| Tier 3 | 500-2000ms | $0.001-0.01 | ~90% (with context) | Complex/novel queries |

## Design Rationale

### Why This Architecture?

**Tier 1 (Pattern Matching) First**:
- Catches majority of common queries instantly
- No LLM cost for routine questions
- Better UX than requiring slash command syntax

**Tier 2 (Slash Commands) Second**:
- Provides power users with maximum control
- Deterministic, testable, scriptable
- No ambiguity in query interpretation

**Tier 3 (Agents) Last**:
- Reserve expensive LLM processing for truly complex cases
- Adaptive to novel requests
- Opt-in to manage costs and expectations

### Alternative Architectures Considered

**LLM-Only (No Tiers)**:
- ❌ High latency for simple queries
- ❌ High cost for routine operations
- ✅ Maximum flexibility

**Slash Commands Only**:
- ✅ Zero latency
- ✅ Zero cost
- ❌ Poor UX for beginners (must learn syntax)
- ❌ Can't handle complex queries

**Pattern Matching Only**:
- ✅ Zero latency
- ✅ Zero cost
- ❌ Can't handle novel queries
- ❌ Brittle (must predefine all patterns)

**Hybrid 3-Tier (Chosen)**:
- ✅ Zero latency for common queries (Tier 1 & 2)
- ✅ Zero cost for common queries (Tier 1 & 2)
- ✅ Good UX for beginners (Tier 1 natural language)
- ✅ Power for advanced users (Tier 2 slash commands)
- ✅ Flexible for complex cases (Tier 3 agents)
- ⚠️ More complex to implement

## Usage Guidelines

### For Application Developers

**When to add a Tier 1 pattern**:
- Query is common (appears frequently in usage logs)
- Maps cleanly to a single slash command
- Has clear, unambiguous intent
- Can be captured with regex

**When NOT to add a Tier 1 pattern**:
- Query is rare or edge case
- Requires context or reasoning
- Ambiguous phrasing
- Better handled by agent reasoning

**When to add a Tier 2 command**:
- Operation is well-defined
- Users need precise control
- Can be expressed in declarative syntax
- Useful for scripting/automation

**When to route to Tier 3**:
- Truly novel requests
- Multi-step workflows
- Requires reasoning about data
- Adaptive responses needed

### For Users

**Use natural language when**:
- You want quick answers to common questions
- Don't know the slash command syntax
- Asking simple status/search queries

**Use slash commands when**:
- You know the exact syntax
- Need complex filters or combinations
- Want deterministic, repeatable results
- Scripting or automating workflows

**Enable MCP mode when**:
- Asking complex, open-ended questions
- Need multi-step operations
- Want explanations or reasoning
- Exploring novel use cases

## Monitoring and Metrics

### Key Metrics to Track

**Tier 1 Performance**:
- Pattern match rate (% of queries caught)
- False positive rate (wrong pattern matched)
- Top unmatched patterns (candidates for new patterns)

**Tier 2 Usage**:
- Command usage distribution
- Error rate (invalid syntax)
- Most common command combinations

**Tier 3 Performance**:
- Average latency
- Cost per query
- Agent selection distribution
- Success rate

**Overall**:
- Queries per tier (distribution)
- Total cost per user session
- Average response time across all tiers

## Future Enhancements

### Short Term
1. Add more Tier 1 patterns based on usage analytics
2. Log unmatched queries to identify pattern gaps
3. A/B test pattern matching vs direct agent routing

### Medium Term
1. Pattern confidence scores (route low-confidence to agents)
2. User feedback loop (thumbs up/down on pattern matches)
3. Automatic pattern generation from agent conversations

### Long Term
1. Expose slash commands as tools to coordinator (unified system)
2. Machine learning for pattern matching (replace regex)
3. Personalized routing (learn user preferences over time)
4. Multi-language natural language support

## Related Documentation

- [Natural Language Query Detection](NATURAL_LANGUAGE_QUERY_DETECTION.md) - Deep dive on Tier 1
- [Slash Commands](SLASH_COMMANDS.md) - Tier 2 command reference
- [MCP Agent](MCP_AGENT.md) - Tier 3 agent architecture

## Summary

The 3-tier routing architecture provides optimal balance between speed, cost, and flexibility:

- **Tier 1** (Pattern Matching): Fast, free, beginner-friendly natural language
- **Tier 2** (Slash Commands): Fast, free, powerful for experts
- **Tier 3** (MCP Agents): Flexible, adaptive, handles complexity

This design follows proven patterns in conversational UIs and delivers superior user experience compared to single-approach architectures.
