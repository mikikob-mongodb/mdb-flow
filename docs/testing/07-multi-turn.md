# 07 - Multi-Turn Conversations

**Time:** 15 minutes  
**Priority:** P1 - Important for realistic demo

---

## Overview

Multi-turn conversations test how well the system maintains context across multiple exchanges. This combines Working Memory with natural conversation flow.

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

## Verification Checklist

```
□ Context persists across turns without explicit mention
□ Pronouns ("it", "that", "the first one") resolve correctly
□ Disambiguation options can be selected by number or description
□ Mixed input types (text/voice) maintain context
□ Context switches when explicitly requested
□ Long conversations don't lose early context
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
| **Total** | **32** | __ | __ |

---

*Multi-Turn Conversation Testing Guide v2.0*