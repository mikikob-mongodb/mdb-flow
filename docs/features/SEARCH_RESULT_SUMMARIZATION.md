# Search Result Summarization

**Date:** 2026-01-14
**Status:** ✅ Implemented

## Problem

Tavily search results were being returned as massive walls of text (9,000+ characters) that:

1. **Bloated conversation context** - Added to history on every subsequent turn
2. **Wasted tokens** - Increased API costs significantly
3. **Poor UX** - Hard for users to extract key insights
4. **Not optimal for LLM** - Raw search results aren't in best format for reasoning

## Solution

Added automatic summarization of search results using Claude before returning to user and adding to conversation history.

### Flow

```
User Query → MCP Agent → Tavily Search (9,428 chars)
                ↓
        MCP Agent Summarizes (async, once)
                ↓
        Cache BOTH:
        - Full Results (reference)
        - Summary (display)
                ↓
        Return Summary → Coordinator → User
                ↓
        Summary Added to Conversation History

On Cache Hit:
        Cache Lookup → Return Pre-Computed Summary (no re-summarization!)
```

## Implementation

### 1. Summarization Function (`agents/mcp_agent.py`)

```python
async def _summarize_search_results(self, search_results: str, query: str) -> str:
    """
    Summarize search results using Claude to extract key insights.

    Only summarizes if results > 800 characters.
    Returns structured summary with:
    - Key Findings (2-4 bullets)
    - Main Sources (2-3 with URLs)
    - Quick Answer (1-2 sentences)
    """
```

**Prompt Strategy:**
- Max 800 tokens output
- Temperature 0.3 (focused, consistent)
- First 6000 chars of results (to stay within limits)
- Structured format for easy scanning

### 2. Integration in Caching (`agents/mcp_agent.py`)

```python
# When caching Tavily results
if len(result_text) > 800:
    summary = await self._summarize_search_results(result_text, user_request)

self.memory.cache_knowledge(
    user_id=user_id,
    query=user_request,
    results=result_text,      # Full results
    summary=summary,           # Pre-computed summary
    source=f"mcp_{solution['mcp_server']}"
)
```

**Benefits:**
- ✅ Summarize once when caching (not on every retrieval)
- ✅ Cache hits return pre-computed summaries instantly
- ✅ Full results preserved for reference

### 3. Retrieval (`memory/manager.py`)

```python
# search_knowledge() returns both:
{
    "query": "...",
    "result": "...",    # Full results
    "summary": "...",   # Pre-computed summary
    "score": 0.86
}
```

### 4. Display (`agents/coordinator.py`)

```python
# In _format_mcp_response()
if mcp_result.get("source") == "knowledge_cache" and mcp_result.get("summary"):
    formatted_result = mcp_result.get("summary")  # Use pre-computed summary
else:
    formatted_result = str(result_content)  # Use full content
```

## Example

### Before (9,428 characters):
```
Detailed Results:

Title: The future of AI agents: Key trends to watch in 2026 - Salesmate CRM
URL: https://www.salesmate.io/blog/future-of-ai-agents/
Content: In this article, we'll explore the latest AI agent trends for 2026, examining how these technologies are evolving from reactive tools to proactive decision-makers.

## AI agents at a glance

Before diving into emerging trends, let's first understand the current reality of ai agents.

AI agents operate by combining powerful AI tools, including large language models, generative AI, and advanced natural language processing, to analyze data, identify patterns, and make informed decisions.

[... 9000 more characters ...]
```

### After (~600 characters):
```
🆕 Here's what I found:

**Key Findings:**
- AI agents in 2026 are evolving from reactive tools to proactive decision-makers with advanced reasoning capabilities
- Major trends include multi-agent systems, enhanced personalization, and integration with IoT devices
- Enterprise adoption is accelerating, with companies like Genentech using agent ecosystems for complex research workflows
- Foundation models enable agents to process multimodal information and perform complex decision-making with minimal human intervention

**Main Sources:**
- [The future of AI agents: Key trends to watch in 2026](https://www.salesmate.io/blog/future-of-ai-agents/) - Salesmate CRM
- [Latest AI News and Breakthroughs](https://example.com/ai-news) - Industry analysis

**Quick Answer:**
AI agents in 2026 are becoming more autonomous and intelligent, with capabilities spanning from automated workflows to complex decision-making across industries.

*💾 Full search results cached for reference*
```

## Benefits

### For Context Management
- **Before:** 9,428 chars added to every subsequent turn
- **After:** ~600 chars added to history
- **Savings:** 93% reduction in context bloat

### For User Experience
- **Before:** Wall of text, hard to extract insights
- **After:** Structured summary with key findings
- **Benefit:** Quick scanning, actionable information

### For Costs
- **Before:** ~3,000 tokens per search in context × every turn
- **After:** ~200 tokens per search in context
- **Savings:** ~93% reduction in ongoing token costs

### For Cache
- **Before:** N/A (wasn't working)
- **After:** Full results stored in cache, summary returned
- **Benefit:** Reference available if needed, context stays lean

## Edge Cases Handled

1. **Short Results (<800 chars):** Not summarized, returned as-is
2. **Summarization Failure:** Fallback to truncated results (first 1500 chars)
3. **Cache Hits:** Also summarized if long (same UX as fresh results)
4. **Missing Query:** Uses fallback 'search query' label

## Performance Impact

- **Summarization Time:** ~1-2 seconds (Claude API call)
- **Total Search Time:** Still <8 seconds (vs 6s Tavily + 1-2s summary)
- **Cache Hit Time:** Still <500ms (includes summarization)
- **Net Benefit:** Worth it for context savings

## Future Enhancements

1. **Streaming Summarization:** Stream summary as it's generated
2. **User Preferences:** Let users toggle summarization on/off
3. **Summary Caching:** Cache summaries separately to avoid re-summarizing
4. **Format Options:** Bullet points, table, narrative, etc.
5. **Source Selection:** Let LLM choose most relevant sources to include

## Files Modified

- **`agents/mcp_agent.py`** (lines 411-493)
  - Added `_summarize_search_results()` async method
  - Updated caching to summarize before storing
  - Returns pre-computed summary on cache hits

- **`memory/manager.py`** (lines 1367-1575)
  - Added `summary` parameter to `cache_knowledge()`
  - Updated `search_knowledge()` projection to include summary field
  - Stores both full results and summary in MongoDB

- **`agents/coordinator.py`** (lines 1848-1890)
  - Updated `_format_mcp_response()` to use cached summary
  - Removed redundant summarization logic

## Testing

### Test Summarization:
1. Run query: "Research latest AI agent developments"
2. Check response is ~600 chars (not 9KB)
3. Verify key findings are present
4. Check full results are cached
5. Run same query again (cache hit) - should still get summary

### Verify Context:
```python
# Check conversation history size
len(st.session_state.messages[-1]["content"])  # Should be ~600, not 9000
```

## Metrics to Track

- Average summary length vs original length
- User satisfaction with summaries
- Token cost savings per session
- Time to summarize vs original API call time
