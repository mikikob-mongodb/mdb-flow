# Multi-Step Intent Classification

**Feature**: Automatic detection and parsing of multi-step user requests
**Added**: January 9, 2026
**Location**: `agents/coordinator.py:_classify_multi_step_intent()`

## Overview

The multi-step intent classifier enables Flow Companion to detect when a user request contains multiple sequential actions and parse them into discrete steps for execution.

This powers the **presentation finale** where complex requests like:
```
"Research the gaming market and create a GTM project with tasks"
```

Are automatically parsed into:
1. Research gaming market trends
2. Create GTM project for gaming
3. Generate tasks from GTM template

## How It Works

### 1. **Pattern Detection**

The method first uses keyword pattern matching to detect potential multi-step requests:

**Sequential Indicators**:
- " and "
- " then "
- ", then "
- " and then "
- " followed by "
- " after that "

**Common Patterns**:
- Research + Create
- Look up + Make
- Find information + Add

### 2. **LLM-Based Parsing**

If patterns are detected, the method uses Claude (temperature=0.0 for consistency) to parse the request into structured steps:

```python
{
    "steps": [
        {"intent": "research", "description": "Research gaming market trends"},
        {"intent": "create_project", "description": "Create GTM project"},
        {"intent": "generate_tasks", "description": "Generate tasks from template"}
    ]
}
```

### 3. **Intent Types**

Supported intents for each step:
- `research` - Web search or information gathering
- `create_project` - Create a new project
- `generate_tasks` - Generate tasks (typically from a template)
- `create_task` - Create individual tasks
- `update_task` - Update existing tasks
- `other` - Fallback for unrecognized intents

## Method Signature

```python
def _classify_multi_step_intent(self, user_message: str) -> dict:
    """
    Detect if message contains multiple intents that need sequential execution.

    Args:
        user_message: User's message

    Returns:
        {
            "is_multi_step": bool,
            "steps": [
                {"intent": "research", "description": "Research gaming market"},
                {"intent": "create_project", "description": "Create GTM project"},
                {"intent": "generate_tasks", "description": "Generate tasks from template"}
            ]
        }
    """
```

## Example Usage

```python
from agents.coordinator import CoordinatorAgent

# Initialize coordinator
coordinator = CoordinatorAgent(memory_manager=memory, db=db)
coordinator.user_id = "user-123"
coordinator.session_id = "session-456"

# Classify multi-step intent
result = coordinator._classify_multi_step_intent(
    "Research the gaming market and create a GTM project with tasks"
)

if result["is_multi_step"]:
    print(f"Found {len(result['steps'])} steps:")
    for step in result["steps"]:
        print(f"  - [{step['intent']}] {step['description']}")
```

**Output**:
```
Found 3 steps:
  - [research] Research gaming market trends and opportunities
  - [create_project] Create GTM project for gaming market
  - [generate_tasks] Generate tasks from GTM template
```

## Test Cases

### Multi-Step Requests (Detected ✓)

1. **"Research the gaming market and create a GTM project with tasks"**
   ```json
   {
       "is_multi_step": true,
       "steps": [
           {"intent": "research", "description": "Research gaming market trends and opportunities"},
           {"intent": "create_project", "description": "Create GTM project for gaming market"},
           {"intent": "generate_tasks", "description": "Generate tasks from GTM template"}
       ]
   }
   ```

2. **"Look up MongoDB features then make a project for it"**
   ```json
   {
       "is_multi_step": true,
       "steps": [
           {"intent": "research", "description": "Research MongoDB features and capabilities"},
           {"intent": "create_project", "description": "Create project for MongoDB integration"}
       ]
   }
   ```

3. **"Find information about AI trends and then create tasks"**
   ```json
   {
       "is_multi_step": true,
       "steps": [
           {"intent": "research", "description": "Find information about AI trends"},
           {"intent": "generate_tasks", "description": "Create tasks based on AI trends research"}
       ]
   }
   ```

### Single-Step Requests (Not Detected ✗)

1. **"Create a new GTM project"**
   ```json
   {
       "is_multi_step": false,
       "steps": []
   }
   ```

2. **"Research the healthcare market"**
   ```json
   {
       "is_multi_step": false,
       "steps": []
   }
   ```

## Testing

Run the test suite:

```bash
source venv/bin/activate
python scripts/test_multi_step_intent.py
```

**Expected Output**:
```
======================================================================
Multi-Step Intent Classification Test
======================================================================

Test Case 1: Research the gaming market and create a GTM project with tasks
  ✓ PASSED

Test Case 2: Look up MongoDB features then make a project for it
  ✓ PASSED

Test Case 3: Find information about AI trends and then create tasks
  ✓ PASSED

Test Case 4: Create a new GTM project
  ✓ PASSED

Test Case 5: Research the healthcare market
  ✓ PASSED

======================================================================
✅ ALL TESTS PASSED
```

## Implementation Details

### Early Return Optimization

If no multi-step indicators are found, the method returns immediately without calling the LLM:

```python
if not (has_sequential_indicator and research_create_pattern):
    return {"is_multi_step": False, "steps": []}
```

This avoids unnecessary API calls for simple requests.

### Deterministic Parsing

The LLM is called with `temperature=0.0` to ensure consistent parsing:

```python
response = self.llm.generate(
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0,  # Deterministic parsing
    max_tokens=1000
)
```

### JSON Cleaning

The method handles markdown code blocks that Claude might include:

```python
# Clean the response - remove markdown code blocks if present
response_clean = response.strip()
if response_clean.startswith("```"):
    # Remove ```json or ``` markers
    lines = response_clean.split("\n")
    response_clean = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
```

### Error Handling

Graceful fallback on parsing errors:

```python
try:
    parsed = json.loads(response_clean)
    # ... process steps
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse multi-step response as JSON: {e}")
    return {"is_multi_step": False, "steps": []}
except Exception as e:
    logger.error(f"Error parsing multi-step intent: {e}")
    return {"is_multi_step": False, "steps": []}
```

## Performance

### Timing

- **Pattern matching**: < 1ms
- **LLM parsing** (if needed): ~2-3 seconds
- **Total** (multi-step detected): ~2-3 seconds
- **Total** (single-step): < 1ms

### Cost

- **Pattern matching**: Free
- **LLM call**: ~400 input tokens, ~100 output tokens
- **Cost per multi-step detection**: ~$0.0025 (Claude Sonnet 4.5)

## Multi-Step Execution

### `_execute_multi_step()` Method

The coordinator now includes a complete multi-step execution engine:

```python
async def _execute_multi_step(
    self,
    steps: List[dict],
    original_request: str,
    user_id: str
) -> dict:
    """
    Execute multiple steps sequentially, passing context between them.

    Returns combined results from all steps.
    """
```

**Features**:
- ✅ Sequential step execution with context passing
- ✅ Automatic GTM template detection and loading
- ✅ Research via MCP Agent (Tavily)
- ✅ Project creation via Worklog Agent
- ✅ Task generation from procedural memory templates
- ✅ Template usage tracking (increments `times_used`)
- ✅ Comprehensive logging and error handling
- ✅ Progress tracking with step-by-step results

### Step Handlers

#### **1. Research (`intent: "research"`)**
- Routes to MCP Agent for web search
- Requires MCP mode enabled
- Stores results in context for subsequent steps
- Tracks source (knowledge_cache, discovery_reuse, new_discovery)

#### **2. Create Project (`intent: "create_project"`)**
- Detects GTM projects automatically (keywords: "gtm", "go-to-market")
- Loads GTM template from procedural memory if detected
- Extracts project name intelligently from description
- Creates project via Worklog Agent
- Stores project info in context for task generation

#### **3. Generate Tasks (`intent: "generate_tasks"`)**
- Requires template and project from previous steps
- Iterates through template phases (Research → Strategy → Execution)
- Creates tasks with phase prefixes: `[Research] Market size analysis`
- Updates template `times_used` and `last_used` timestamps
- Returns task count and preview

### Execution Flow Example

**User Request**: "Research the gaming market and create a GTM project with tasks"

**Parsed Steps**:
1. `{"intent": "research", "description": "Research gaming market trends"}`
2. `{"intent": "create_project", "description": "Create GTM project for gaming"}`
3. `{"intent": "generate_tasks", "description": "Generate tasks from template"}`

**Execution**:

```
Step 1/3: research - Research gaming market trends
  → Routing to MCP Agent...
  → ✓ Research completed via tavily-search
  → Cached results in context

Step 2/3: create_project - Create GTM project for gaming
  → Detected GTM project
  → Loading template from procedural memory...
  → ✓ Found template: GTM Roadmap Template
  → Extracting project name: Gaming Market
  → Creating project...
  → ✓ Project created: Gaming Market

Step 3/3: generate_tasks - Generate tasks from template
  → Generating tasks from template: GTM Roadmap Template
  → Phase: Research
    ✓ Created: [Research] Market size and growth analysis
    ✓ Created: [Research] Competitor landscape mapping
    ✓ Created: [Research] Target customer persona development
    ✓ Created: [Research] Pricing strategy research
  → Phase: Strategy
    ✓ Created: [Strategy] Value proposition refinement
    ✓ Created: [Strategy] Channel strategy definition
    ✓ Created: [Strategy] Partnership opportunity identification
    ✓ Created: [Strategy] Go-to-market timeline creation
  → Phase: Execution
    ✓ Created: [Execution] Marketing collateral development
    ✓ Created: [Execution] Sales enablement materials
    ✓ Created: [Execution] Launch event planning
    ✓ Created: [Execution] Success metrics definition
  → ✓ Generated 12 tasks across 3 phases

Multi-step execution complete: 3/3 steps successful
```

**Result**:
```json
{
    "success": true,
    "steps_completed": 3,
    "total_steps": 3,
    "results": [
        {
            "step": 1,
            "type": "research",
            "success": true,
            "source": "tavily-search",
            "preview": "Gaming market trends show..."
        },
        {
            "step": 2,
            "type": "create_project",
            "success": true,
            "project_name": "Gaming Market",
            "project_id": "507f1f77bcf86cd799439011",
            "template_loaded": true
        },
        {
            "step": 3,
            "type": "generate_tasks",
            "success": true,
            "tasks_created": 12,
            "template_used": "GTM Roadmap Template",
            "phases": 3,
            "tasks_preview": ["[Research] Market size...", ...]
        }
    ],
    "context": {
        "project_created": "Gaming Market",
        "project_id": "507f1f77bcf86cd799439011",
        "research_cached": true,
        "research_source": "tavily-search",
        "template_used": "GTM Roadmap Template",
        "tasks_generated": 12
    }
}
```

## Integration with Coordinator

**Status**: ✅ **FULLY INTEGRATED** into main process flow

The multi-step workflow is now integrated into `CoordinatorAgent.process()` (lines 2246-2269):

```python
# MULTI-STEP ROUTING: Check if request contains multiple steps
multi_step = self._classify_multi_step_intent(user_message)

if multi_step["is_multi_step"]:
    logger.info(f"🔄 Detected multi-step request with {len(multi_step['steps'])} steps")

    # Execute multi-step workflow
    import asyncio
    result = asyncio.run(self._execute_multi_step(
        steps=multi_step["steps"],
        original_request=user_message,
        user_id=self.user_id
    ))

    # Format response for user
    formatted = self._format_multi_step_response(result)

    if return_debug:
        return formatted
    else:
        return formatted["response"]

# Continue with normal single-step routing...
```

**Integration Details**:
- Runs BEFORE MCP routing and normal intent classification
- Early exit if multi-step detected (no normal processing needed)
- Uses `asyncio.run()` to execute async _execute_multi_step from sync process()
- Returns formatted response directly to user

## Response Formatting

### `_format_multi_step_response()` Method

Location: `agents/coordinator.py` (lines 1498-1582)

Formats execution results into user-friendly markdown:

**Success Response Example**:
```
✅ Multi-step workflow completed (3/3 steps)

**1. Research completed** (via tavily-search)
   Gaming market trends show rapid growth in cloud gaming, with an estimated
   CAGR of 22% through 2027...

**2. Project created**: Gaming Market
   📋 Template detected and loaded

**3. Tasks generated**: 12 tasks across 3 phases
   Preview:
   • [Research] Market size and growth analysis
   • [Research] Competitor landscape mapping
   • [Research] Target customer persona development
   • [Research] Pricing strategy research
   • [Strategy] Value proposition refinement

📚 Template: GTM Roadmap Template
🔍 Research source: tavily-search

---
💡 Next steps:
• View project tasks: Show me tasks for Gaming Market
• Start working: Start the first task
```

**Failure Response Example**:
```
⚠️ Workflow partially completed (2/3 steps successful).

❌ Issue at step 3: No template available from previous steps
```

## Use Cases

### 1. Presentation Finale

**User**: "Research the gaming market and create a GTM project with tasks"

**System**:
1. Enables MCP mode (if not already enabled)
2. Executes Tavily web search for gaming market research
3. Creates "Gaming Market GTM" project
4. Detects GTM pattern → applies GTM Roadmap Template
5. Generates 12 tasks across Research/Strategy/Execution phases
6. Shows learning from past GTM projects

### 2. Research-Driven Projects

**User**: "Look up the latest React features then create a project for migration"

**System**:
1. Web search for React features
2. Create "React Migration" project
3. Optionally generate migration tasks based on findings

### 3. Information to Action

**User**: "Find MongoDB pricing tiers and then create evaluation tasks"

**System**:
1. Research MongoDB pricing
2. Generate evaluation tasks based on pricing tiers found

## Future Enhancements

1. **Step Execution Engine**: Implement sequential execution of parsed steps
2. **Progress Tracking**: Show user which step is currently executing
3. **Step Dependencies**: Allow steps to reference data from previous steps
4. **Conditional Steps**: Support "if X then Y" logic
5. **Parallel Steps**: Detect steps that can run in parallel
6. **User Confirmation**: Ask user to confirm parsed steps before execution
7. **Step Templates**: Learn common step sequences and suggest them

## Helper Methods

### `_extract_project_name(description, context)`

Intelligently extracts project name from step description:

**Patterns**:
- "create project for X" → "X"
- "make project for X" → "X"
- "create X project" → "X"

**Fallback**: Uses capitalized words from original request

**Example**:
```python
description = "Create GTM project for gaming market"
# Returns: "Gaming Market"

description = "Create project for MongoDB integration"
# Returns: "MongoDB Integration"
```

### `_truncate(text, max_length)`

Truncates text for display with ellipsis:

```python
text = "Very long research results..."
preview = self._truncate(text, 200)
# Returns: "Very long research res..."
```

## Related Files

- **Implementation**:
  - `agents/coordinator.py:process()` - Main integration (lines 2246-2269)
  - `agents/coordinator.py:_classify_multi_step_intent()` (lines 1064-1189)
  - `agents/coordinator.py:_execute_multi_step()` (lines 1190-1434)
  - `agents/coordinator.py:_extract_project_name()` (lines 1436-1482)
  - `agents/coordinator.py:_truncate()` (lines 1484-1488)
  - `agents/coordinator.py:_format_multi_step_response()` (lines 1498-1582)
- **Test Script**: `scripts/test_multi_step_intent.py`
- **Documentation**: `docs/features/MULTI_STEP_INTENTS.md` (this file)
- **Demo Data**: `scripts/seed_demo_data.py` (GTM template)

## Logging

The method logs key events:

```python
logger.info(f"Detected potential multi-step request: {user_message}")
logger.info(f"Parsed {len(parsed['steps'])} steps from multi-step request")
logger.info("LLM did not identify multiple steps")
logger.error(f"Failed to parse multi-step response as JSON: {e}")
```

Check logs for multi-step classification activity:
```bash
grep "multi-step" logs/flow_companion.log
```

## Summary

The multi-step intent classifier enables Flow Companion to:
- ✅ Detect complex, multi-action user requests
- ✅ Parse them into discrete sequential steps
- ✅ Identify the intent of each step
- ✅ Provide structured data for sequential execution

This is a **key enabler** for the presentation finale, allowing natural language requests like "research X and create Y with Z" to be automatically decomposed and executed step-by-step.
