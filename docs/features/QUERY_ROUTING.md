# Query Routing Architecture

## Overview

The Flow Companion demo app uses a **4-tier routing system** that intelligently decides how to handle user input. This architecture optimizes for speed, cost, and user experience by using the right tool for each type of query.

## The Four Tiers

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
│ TIER 3: LLM Agent with Built-in Tools (ALWAYS AVAILABLE)  │
│ - Claude-powered coordinator                               │
│ - Built-in agents: worklog, retrieval, memory             │
│ - Reasoning and tool use                                   │
│ - Latency: ~500-2000ms | Cost: ~$0.001-0.01 | Adaptive    │
│ - NO toggle required - always available                    │
└─────────────────────────────────────────────────────────────┘
    ↓ (if needs external tools like web search or advanced queries)
┌─────────────────────────────────────────────────────────────┐
│ TIER 4: MCP Agent - External Tool Discovery               │
│ - Tavily: Web search and research                         │
│ - MongoDB MCP: Advanced query generation, aggregations    │
│ - Dynamic tool discovery                                   │
│ - Latency: ~1000-3000ms | Cost: ~$0.01-0.05 | Flexible    │
│ - Requires "Experimental MCP Mode" toggle enabled          │
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

## Tier 3: LLM Agent with Built-in Tools

### Purpose
Handle complex, ambiguous, or novel queries using Claude's reasoning with built-in tools. This tier provides intelligent task management, search, and memory operations WITHOUT requiring external tool discovery.

### How It Works
The coordinator agent receives the query and:
1. Analyzes intent using Claude
2. Selects appropriate built-in tools
3. Executes operations using built-in agents
4. Uses memory system for context
5. Returns synthesized response

### Built-in Agents (Always Available)
- **worklog_agent**: Task and project management operations (create, update, complete, list)
- **retrieval_agent**: Hybrid search across tasks and projects (vector + text)
- **memory system**: Context injection, rules, preferences, session memory

### Examples That Route to Tier 3

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
"Update all tasks in the Voice Agent project to high priority"
```

**Reasoning Required**:
```
"What's blocking the AgentOps project?"
"Which tasks should I delegate?"
"What's the critical path for shipping this feature?"
```

**Novel/Creative Requests**:
```
"Explain how my tasks are organized"
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
- **User Experience**: Natural conversation, explanations, reasoning
- **Limitations**: Cannot access external data (web search, etc.)
- **Flexibility**: High (handles most queries with built-in tools)
- **Power**: Reasoning, multi-step, adaptive within built-in capabilities
- **Availability**: **ALWAYS ON** - no toggle required

### When This Tier Catches Queries
- No pattern match in Tier 1
- Doesn't start with `/` (Tier 2)
- Doesn't require external tools (Tier 4)
- This is the DEFAULT fallback for unmatched queries

### When Queries Fall Through to Tier 4
- Explicit research/web search requests
- Requests for external information not in the database

## Tier 4: MCP Agent - External Tool Discovery

### Purpose
Handle requests that require EXTERNAL tools and data sources beyond the built-in capabilities. This includes:
- Web search and research
- Advanced MongoDB query generation via MCP
- Dynamic tool discovery via Model Context Protocol (MCP) servers

### How It Works
The MCP agent:
1. Connects to external MCP servers (e.g., Tavily for web search, MongoDB for advanced queries)
2. Dynamically discovers available tools
3. Selects appropriate external tools for the request
4. Executes external tool calls
5. Synthesizes results from multiple sources
6. Returns comprehensive response

### External Tools Available (When MCP Mode Enabled)
- **Tavily**: Web search and research for current/external information
- **MongoDB MCP Server**: Advanced query generation, aggregation pipelines, complex database operations
- **Custom MCP Servers**: Any MCP-compatible tool servers

### Examples That Route to Tier 4

**Research/Web Search**:
```
"Research the latest trends in AI agents"
"Look up MongoDB best practices for 2025"
"What's the current state of RAG systems?"
"Find information about prompt caching"
```

**Advanced MongoDB Query Generation** (via MongoDB MCP):
```
"Generate an aggregation pipeline to find tasks by complexity over time"
"Create a query that finds projects with the most overdue high-priority tasks"
"Build a MongoDB query to analyze task completion rates by project"
"Generate an aggregation to calculate average time-to-completion by priority"
"Create a complex join query across tasks and projects with time-series analysis"
```

**External Data Needs**:
```
"What are the top task management frameworks right now?"
"Compare MongoDB Atlas vs self-hosted MongoDB"
"What's new in Claude 4?"
```

**Multi-Step with Research**:
```
"Research the gaming market and create a GTM project with tasks"
"Look up MongoDB features then make a project for it"
"Find information about AI trends and create tasks"
```

### Characteristics
- **Speed**: Variable (~1000-3000ms, slower due to external calls)
- **Cost**: Per query (~$0.01-0.05, higher due to external API costs)
- **User Experience**: Comprehensive research, up-to-date information
- **Limitations**: Requires MCP mode toggle enabled
- **Flexibility**: Maximum (can discover and use new tools)
- **Power**: External data access, real-time information, research capabilities
- **Availability**: **REQUIRES TOGGLE** - "Experimental MCP Mode" must be enabled

### When This Tier Catches Queries
- Intent classified as "research", "web_search", "find_information", "advanced_mongodb_query"
- User has enabled "Experimental MCP Mode" toggle
- Query explicitly requests external/current information OR advanced MongoDB query generation

### When Queries Are Blocked
- MCP mode not enabled → Show message: "I don't have access to external research tools for this request. Enable Experimental MCP Mode to let me search the web and discover new tools."
- Note: Advanced MongoDB query generation via MongoDB MCP server requires the MCP toggle enabled

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

    # TIER 3: Route to LLM Agent with built-in tools (ALWAYS available)
    # Coordinator classifies intent and decides routing
    intent = coordinator.classify_intent(prompt)

    if intent requires external tools (research, web_search):
        # TIER 4: Check if MCP mode enabled for external tools
        if st.session_state.get("mcp_enabled", False):
            response = coordinator.route_to_mcp_agent(prompt, intent)
            display_response(response)
        else:
            show_message("Enable MCP Mode for external research tools")
    else:
        # TIER 3: Use LLM with built-in tools (worklog, retrieval, memory)
        response = coordinator.process_with_builtin_tools(prompt)
        display_response(response)
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
    └─ Route to Coordinator
        │
        ├─ Classify Intent
        │
        ├─ Needs external tools? ──YES──> Tier 4: Check MCP enabled
        │                                      │
        │                                      ├─ MCP ON → Use MCP Agent → DONE
        │                                      │
        │                                      └─ MCP OFF → Show "Enable MCP" → DONE
        │
        └─ Use built-in tools? ──YES──> Tier 3: LLM with built-in agents → DONE
                                         (ALWAYS AVAILABLE - NO TOGGLE)
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

### Tier 3 Catches (LLM Agent with Built-in Tools - Always Available)

| Query | Why Tier 3? | Tools Used |
|-------|-------------|------------|
| "What should I work on?" | Requires reasoning | worklog_agent, retrieval_agent |
| "Summarize my progress" | Multi-step analysis | retrieval_agent, memory system |
| "Why is X taking so long?" | Causal reasoning | worklog_agent, retrieval_agent |
| "Create task and assign it" | Multi-step operation | worklog_agent |
| "Tell me more" | Conversational context | memory system, retrieval_agent |
| "How are my tasks organized?" | Explanation needed | worklog_agent, LLM reasoning |

### Tier 4 Catches (MCP Agent - Requires Toggle)

| Query | Why Tier 4? | External Tool Used |
|-------|-------------|-------------------|
| "Research AI agent trends" | Needs current web data | Tavily web search |
| "Look up MongoDB best practices" | External information | Tavily web search |
| "What's new in Claude 4?" | Up-to-date info needed | Tavily web search |
| "Generate aggregation pipeline for task complexity" | Advanced MongoDB query | MongoDB MCP server |
| "Build query to analyze completion rates" | Complex aggregation needed | MongoDB MCP server |
| "Research market and create project" | Multi-step with external data | Tavily + worklog_agent |

### Falls Through (MCP Mode Disabled for External Tools)

| Query | Why Blocked? | Message Shown |
|-------|--------------|---------------|
| "Research AI trends" | Needs external tools, MCP disabled | "Enable MCP Mode for external research tools" |
| "Look up best practices" | Needs web search, MCP disabled | "Enable MCP Mode for external research tools" |
| "What's the latest news?" | Needs current data, MCP disabled | "Enable MCP Mode for external research tools" |

## Performance Comparison

| Tier | Avg Latency | Cost Per Query | Success Rate | Availability | Use Case |
|------|-------------|----------------|--------------|--------------|----------|
| Tier 1 | ~0ms | $0 | ~40-60% of common queries | Always | Natural language patterns |
| Tier 2 | ~0ms | $0 | 100% (valid syntax) | Always | Power user commands |
| Tier 3 | 500-2000ms | $0.001-0.01 | ~90% (with built-in tools) | **Always** | Complex queries, reasoning |
| Tier 4 | 1000-3000ms | $0.01-0.05 | ~85% (depends on external APIs) | Requires toggle | Research, web search, external data |

## Design Rationale

### Why This Architecture?

**Tier 1 (Pattern Matching) First**:
- Catches majority of common queries instantly
- No LLM cost for routine questions
- Better UX than requiring slash command syntax
- 40-60% of queries handled at zero cost

**Tier 2 (Slash Commands) Second**:
- Provides power users with maximum control
- Deterministic, testable, scriptable
- No ambiguity in query interpretation
- Zero latency, zero cost

**Tier 3 (LLM Agent with Built-in Tools) Third - ALWAYS AVAILABLE**:
- Handles complex queries that don't match patterns
- Uses Claude's reasoning with built-in tools (worklog, retrieval, memory)
- NO TOGGLE REQUIRED - always accessible for better UX
- Falls back gracefully for unmatched queries
- Provides flexibility without requiring external tool discovery

**Tier 4 (MCP External Tools) Last - REQUIRES TOGGLE**:
- Reserve external tool discovery for truly external data needs
- Only used for research, web search, and new tool discovery
- Opt-in toggle manages costs and external API usage
- Higher latency and cost justified by accessing real-time external data

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

**Hybrid 4-Tier (Chosen)**:
- ✅ Zero latency for common queries (Tier 1 & 2)
- ✅ Zero cost for common queries (Tier 1 & 2)
- ✅ Good UX for beginners (Tier 1 natural language, Tier 3 always-on LLM)
- ✅ Power for advanced users (Tier 2 slash commands)
- ✅ Flexible for complex cases (Tier 3 built-in agents, always available)
- ✅ External data access when needed (Tier 4 MCP, opt-in)
- ✅ Cost control via tiered approach and optional toggle
- ⚠️ More complex to implement (4 tiers vs 1-2)

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

**When to route to Tier 3** (built-in LLM agent):
- Novel requests that don't match patterns
- Multi-step workflows using built-in tools
- Requires reasoning about tasks/projects/data
- Conversational queries
- Adaptive responses needed
- DEFAULT FALLBACK for unmatched queries

**When to route to Tier 4** (external MCP tools):
- Explicit research or web search requests
- Needs current/external information
- Advanced MongoDB query generation (aggregation pipelines, complex analytics)
- Tool discovery required
- Real-time data needs

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

**Complex queries work automatically** (Tier 3 - no toggle needed):
- Asking complex, open-ended questions about your tasks/projects
- Need multi-step operations (create, update, analyze)
- Want explanations or reasoning about your work
- Exploring novel use cases with built-in tools
- Conversational follow-ups ("tell me more", "why?")

**Enable MCP mode when** (Tier 4 - requires toggle):
- Need to research current/external information
- Want web search results
- Looking for the latest trends or data
- Need advanced MongoDB query generation (complex aggregations, analytics)
- Require tools beyond the built-in capabilities

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

**Tier 3 Performance** (Built-in LLM Agent):
- Average latency (~500-2000ms)
- Cost per query (~$0.001-0.01)
- Tool selection distribution (worklog vs retrieval)
- Success rate (~90%)
- Usage frequency (should be high since it's always available)

**Tier 4 Performance** (External MCP Agent):
- Average latency (~1000-3000ms, higher due to external calls)
- Cost per query (~$0.01-0.05, higher due to external APIs)
- External tool usage (Tavily, etc.)
- Success rate (~85%, depends on external API availability)
- Toggle adoption rate (% of users enabling MCP mode)

**Overall**:
- Queries per tier (distribution across all 4 tiers)
- Total cost per user session
- Average response time across all tiers
- Tier 3 vs Tier 4 usage ratio

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
- Coordinator Agent Documentation - Tier 3 LLM agent with built-in tools
- [MCP Agent](MCP_AGENT.md) - Tier 4 external tool discovery architecture

## Summary

The 4-tier routing architecture provides optimal balance between speed, cost, flexibility, and user experience:

- **Tier 1** (Pattern Matching): Fast, free, beginner-friendly natural language
- **Tier 2** (Slash Commands): Fast, free, powerful for experts
- **Tier 3** (LLM Agent with Built-in Tools): Flexible, always available, handles complex queries with reasoning - **NO TOGGLE REQUIRED**
- **Tier 4** (MCP External Tools): Maximum flexibility, external data access (web search, advanced MongoDB queries), research capabilities - **REQUIRES TOGGLE**

### Key Architectural Decisions

1. **Tier 3 is ALWAYS available** - Users don't hit a wall when queries don't match patterns. The LLM with built-in agents provides graceful fallback for all unmatched queries.

2. **Tier 4 is OPT-IN** - External tool discovery (MCP) is only required for truly external data needs (web search, research, advanced MongoDB query generation). This manages costs and sets clear expectations.

3. **Progressive Enhancement** - The architecture progressively enhances capabilities:
   - Tier 1 & 2: Zero-cost, instant responses for common queries
   - Tier 3: Adds reasoning and flexibility for complex queries (always on)
   - Tier 4: Adds external data access (web search, advanced MongoDB analytics) when explicitly needed (opt-in)

This design follows proven patterns in conversational UIs and delivers superior user experience compared to single-approach architectures, while providing clear cost control and flexibility.
