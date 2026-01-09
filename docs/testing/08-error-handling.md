# 08 - Error Handling

**Time:** 15 minutes
**Priority:** P2 - Edge cases
**Updated:** January 9, 2026 (Milestone 6 - MCP Error Scenarios)

---

## Overview

Test how the system handles errors, edge cases, and unexpected input gracefully.

---

## Test Cases

### 8.1 Not Found Errors

| ID | Query | Expected Response | Pass |
|----|-------|-------------------|------|
| 8.1 | "Show me the Kubernetes project" | "I couldn't find a project called Kubernetes" | □ |
| 8.2 | "Complete the blockchain task" | "I couldn't find a task matching 'blockchain'" | □ |
| 8.3 | `/tasks project:NonExistent` | "No tasks found for project 'NonExistent'" | □ |
| 8.4 | "What's the status of the GraphQL task?" | "I couldn't find a task about GraphQL" | □ |

**Verification:**
```
□ Error messages are helpful, not technical
□ Suggestions provided when possible
□ No stack traces or raw errors shown
```

### 8.2 Invalid Input

| ID | Input | Expected Response | Pass |
|----|-------|-------------------|------|
| 8.5 | "" (empty) | Prompts for input | □ |
| 8.6 | `/invalid` | Shows available commands | □ |
| 8.7 | "asdfghjkl" | Asks for clarification | □ |
| 8.8 | "/tasks status:invalid" | Shows valid status values | □ |

### 8.3 Graceful Degradation

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.9 | Memory disabled mid-conversation | Works without memory | □ |
| 8.10 | Very long query (500+ chars) | Handles gracefully | □ |
| 8.11 | Special characters in query | Handles or sanitizes | □ |
| 8.12 | Emoji in query 🎉 | Handles gracefully | □ |

### 8.4 Edge Cases

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.13 | Empty task list | "No tasks found" message | □ |
| 8.14 | Empty project | "Project exists but has no tasks" | □ |
| 8.15 | Search with no results | "No results found for..." | □ |
| 8.16 | Complete already-done task | "Task is already complete" | □ |

### 8.5 Concurrent Actions

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.17 | Rapid consecutive queries | Handles queue properly | □ |
| 8.18 | Cancel mid-query | Cancels gracefully | □ |

### 8.6 MCP Error Scenarios (Milestone 6)

**Purpose:** Test error handling for MCP Agent and Tavily integration.

**Setup: Enable MCP Mode with TAVILY_API_KEY**

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.19 | MCP Mode OFF + research query | "Enable MCP Mode to handle this request" | □ |
| 8.20 | Invalid TAVILY_API_KEY | "MCP connection failed" (graceful message) | □ |
| 8.21 | Tavily timeout (simulate slow network) | Request times out after 30s with error message | □ |
| 8.22 | Tavily returns empty results | "No results found" (not error) | □ |
| 8.23 | Multi-step: Research fails | Shows research error, skips remaining steps | □ |

**MCP Connection Testing:**

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.24 | Enable MCP without TAVILY_API_KEY | "Tavily API key not configured" in debug | □ |
| 8.25 | Check MCP status sidebar | Shows "MCP Servers: 0 connected" | □ |
| 8.26 | Add valid key + toggle MCP ON | Shows "MCP Servers: 1 connected (Tavily)" | □ |

**Knowledge Cache Edge Cases:**

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.27 | Query with cache expired (>7 days) | Fresh Tavily search, not cache | □ |
| 8.28 | Clear knowledge cache mid-session | Next query creates new cache entry | □ |

**Tool Discovery Errors:**

| ID | Scenario | Expected | Pass |
|----|----------|----------|------|
| 8.29 | MCP returns invalid JSON response | Logs error, returns graceful message | □ |
| 8.30 | Discovery vector search fails | Falls back to exact match search | □ |

---

## Verification Checklist

**General:**
```
□ No raw errors or stack traces shown to user
□ Error messages are helpful and actionable
□ System recovers gracefully from errors
□ Invalid input doesn't crash the app
□ Edge cases handled with appropriate messages
□ Memory failures don't break core functionality
```

**MCP-Specific (NEW):**
```
□ MCP mode disabled prompts user to enable
□ Tavily connection errors show graceful message
□ Timeouts handled with 30s limit
□ Multi-step workflows fail gracefully per step
□ Knowledge cache expiration handled correctly
□ Tool discovery fallback works (vector → exact match)
□ Debug panel shows MCP connection status clearly
```

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Not Found | 4 | __ | __ |
| Invalid Input | 4 | __ | __ |
| Graceful Degradation | 4 | __ | __ |
| Edge Cases | 4 | __ | __ |
| Concurrent | 2 | __ | __ |
| **MCP Errors (NEW)** | **12** | __ | __ |
| **Total** | **30** | __ | __ |

---

*Error Handling Testing Guide v3.0*
*Updated for Milestone 6 - MCP Error Scenarios*