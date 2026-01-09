# 07 - Multi-Turn Conversations & Multi-Step Workflows

**Time:** 20 minutes
**Priority:** P1 - Important for realistic demo
**Updated:** January 9, 2026 (Milestone 6 - Multi-Step Workflows)

---

## Overview

This guide tests:
1. **Multi-turn conversations**: Context persistence across exchanges (Working Memory)
2. **Multi-step workflows** (NEW): Automatic detection and execution of complex requests

---

## Test Cases

### 7.1 Context Across Turns

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Show me AgentOps" | Project info | □ |
| 2 | "What's in progress?" | AgentOps in-progress tasks | □ |
| 3 | "Any high priority?" | AgentOps high-priority tasks | □ |
| 4 | "Complete the first one" | Completes from context | □ |
| 5 | "What did I just do?" | Recalls the completion | □ |

**Verification:**
```
□ Each turn uses context from previous turns
□ "First one" correctly references previous results
□ History query recalls recent action
□ No need to re-specify "AgentOps" after turn 1
```

### 7.2 Disambiguation Flow

**Scenario A: Numbered Selection**

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Complete the doc task" | Shows numbered options (multiple docs) | □ |
| 2 | "2" | Selects second option | □ |

**Scenario B: Descriptive Selection**

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Complete the webinar task" | Shows numbered options (multiple webinars) | □ |
| 2 | "The February one" | Selects by description | □ |

**Scenario C: Direct Disambiguation**

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Complete the doc task" | Shows options | □ |
| 2 | "The one about debugging" | Selects by content | □ |

### 7.3 Mixed Input Types

| Turn | Type | Query | Expected | Pass |
|------|------|-------|----------|------|
| 1 | Text | "Show me AgentOps" | Project info | □ |
| 2 | Voice | "What's high priority?" | Filtered results | □ |
| 3 | Text | "Complete the first one" | Completes task | □ |

### 7.4 Context Switching

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Show me AgentOps" | AgentOps context | □ |
| 2 | "What's in progress?" | AgentOps tasks | □ |
| 3 | "Switch to Voice Agent" | Context updated | □ |
| 4 | "What's in progress?" | Voice Agent tasks | □ |

### 7.5 Pronoun Resolution

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Show me the debugging task" | Shows task | □ |
| 2 | "Start it" | Starts debugging task | □ |
| 3 | "Add a note: making progress" | Adds note to same task | □ |
| 4 | "Complete it" | Completes same task | □ |

### 7.6 Long Conversation (10+ turns)

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | "Show me AgentOps" | Context set | □ |
| 2 | "What's todo?" | Filtered | □ |
| 3 | "Start the first one" | Task started | □ |
| 4 | "Add a note: beginning work" | Note added | □ |
| 5 | "What else is todo?" | Other todo tasks | □ |
| 6 | "Start that one too" | Second task started | □ |
| 7 | "What am I working on?" | Lists both tasks | □ |
| 8 | "Complete the first one" | First task done | □ |
| 9 | "What's still in progress?" | Second task only | □ |
| 10 | "Complete it" | Second task done | □ |

---

## Multi-Step Workflows (Milestone 6)

**Purpose:** Automatically detect and execute complex multi-step requests without explicit orchestration.

### 7.7 Basic Multi-Step: Research + Create + Generate

**Setup:**
```
☑ MCP Mode: ON (requires TAVILY_API_KEY)
☑ Procedural Memory: ON (for GTM template)
☑ Working Memory: ON
```

| Turn | Query/Action | Expected | Pass |
|------|-------------|----------|------|
| 1 | "Research the gaming market and create a GTM project with tasks" | Detects 3-step workflow | □ |
| 2 | **Step 1: Research** | Routes to Tavily MCP, gets market data | □ |
| 3 | **Step 2: Create** | Creates "Gaming Market" project, loads GTM template | □ |
| 4 | **Step 3: Generate** | Creates 12 tasks across 3 phases | □ |
| 5 | Check response | Shows all 3 steps completed with results | □ |

**Verification:**
```
□ Response includes research results from Tavily
□ Project created: "Gaming Market"
□ 12 tasks created with phase prefixes:
  - [Research] Market size and growth analysis
  - [Research] Competitor landscape mapping
  - [Research] Target customer persona development
  - [Research] Pricing strategy research
  - [Strategy] Value proposition refinement
  - [Strategy] Channel strategy definition
  - [Strategy] Partnership opportunity identification
  - [Strategy] Go-to-market timeline creation
  - [Execution] Marketing collateral development
  - [Execution] Sales enablement materials
  - [Execution] Launch event planning
  - [Execution] Success metrics definition
□ GTM template usage count incremented
□ Total time: ~7-11 seconds
```

### 7.8 Multi-Step Detection Patterns

Test these patterns to verify detection:

| Query | Expected Detection | Pass |
|-------|-------------------|------|
| "Research MongoDB features and create a project" | 2 steps: research + create_project | □ |
| "Look up AI trends then make tasks" | 2 steps: research + generate_tasks | □ |
| "Find gaming news and then create a GTM project with tasks" | 3 steps: research + create + generate | □ |

**Should NOT detect (single-step):**
| Query | Expected Behavior | Pass |
|-------|------------------|------|
| "Research the gaming market" | Single MCP call (not multi-step) | □ |
| "Create a GTM project" | Single create (no workflow) | □ |

### 7.9 Multi-Step Context Passing

**Purpose:** Verify context flows between steps.

| Turn | Query/Check | Expected | Pass |
|------|------------|----------|------|
| 1 | Run multi-step workflow (test 7.7) | All steps complete | □ |
| 2 | "What do you know about gaming?" | Uses cached research from step 1 | □ |
| 3 | "Show me the GTM project" | Shows the created project | □ |
| 4 | "List the research phase tasks" | Shows 4 research tasks | □ |

### 7.10 Multi-Step Error Handling

**Scenario A: MCP Mode Disabled**

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | Toggle MCP Mode OFF | - | □ |
| 2 | "Research gaming and create GTM project" | Error: "Enable MCP Mode for research" | □ |

**Scenario B: Missing Template**

| Turn | Query | Expected | Pass |
|------|-------|----------|------|
| 1 | Delete GTM template from database | - | □ |
| 2 | "Research X and create GTM project with tasks" | Research works, project created, but task generation skips | □ |
| 3 | Response | Shows warning about missing template | □ |

---

## Verification Checklist

**Multi-Turn Conversations:**
```
□ Context persists across turns without explicit mention
□ Pronouns ("it", "that", "the first one") resolve correctly
□ Disambiguation options can be selected by number or description
□ Mixed input types (text/voice) maintain context
□ Context switches when explicitly requested
□ Long conversations don't lose early context
```

**Multi-Step Workflows (NEW):**
```
□ Detects "Research X and create Y and generate Z" patterns
□ Executes steps sequentially (research → create → generate)
□ Passes context between steps (research results → project creation)
□ Loads GTM template from procedural memory
□ Creates 12 tasks with correct phase prefixes
□ Handles errors gracefully (MCP disabled, missing template)
□ Total execution time reasonable (~7-11s for 3 steps)
```

---

## Common Issues

| Issue | Symptom | Likely Cause |
|-------|---------|--------------|
| Lost context | Agent asks "which project?" after setting it | Working Memory not persisting |
| Wrong resolution | "it" refers to wrong item | Disambiguation storage issue |
| Slow accumulation | Later turns slower | Context injection growing large |
| History confusion | Mixes up recent actions | Episodic Memory query issue |

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Context Across Turns | 5 | __ | __ |
| Disambiguation | 6 | __ | __ |
| Mixed Input | 3 | __ | __ |
| Context Switching | 4 | __ | __ |
| Pronoun Resolution | 4 | __ | __ |
| Long Conversation | 10 | __ | __ |
| **Multi-Step Workflows (NEW)** | **11** | __ | __ |
| **Total** | **43** | __ | __ |

---

*Multi-Turn Conversation & Multi-Step Workflow Testing Guide v3.0*
*Updated for Milestone 6*