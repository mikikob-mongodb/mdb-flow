# Memory Evaluation Methodology

**Flow Companion - Agent Memory System Evaluation Framework**

This document describes the evaluation methodology used to test and validate the memory capabilities of Flow Companion's multi-agent system. Our approach is grounded in recent research on LLM agent memory systems and adapted for practical task management scenarios.

---

## Table of Contents

1. [Overview](#overview)
2. [Memory Competencies Framework](#memory-competencies-framework)
3. [Test Scenarios](#test-scenarios)
4. [Evaluation Metrics](#evaluation-metrics)
5. [Memory Architecture](#memory-architecture)
6. [Benchmarks & Baselines](#benchmarks--baselines)
7. [Research Citations](#research-citations)
8. [Running the Evaluations](#running-the-evaluations)

---

## Overview

### Why Memory Evaluation Matters

Traditional LLM benchmarks focus on reasoning, planning, and execution capabilities. However, **memory**—how agents store, retrieve, update, and reason over long-term information—is equally critical for real-world applications yet significantly under-evaluated.

Flow Companion implements a three-tier memory system:
- **Short-term Memory**: Session context and working memory
- **Long-term Memory**: Action history and learned facts
- **Shared Memory**: Agent-to-agent handoffs

Our evaluation framework tests each memory tier across four core competencies identified by recent research.

### Key Research Insights

Based on MemoryAgentBench (Hu et al., 2025) and related work:

| Finding | Implication |
|---------|-------------|
| RAG excels at retrieval but fails at global understanding | Need multiple memory types |
| Long-context models win at learning but fail at scale | Need efficient memory management |
| **All methods fail multi-hop conflict resolution (<7%)** | This is the hardest problem |
| Commercial memory agents (Mem0, MemGPT) underperform | Room for improvement |
| Simpler approaches often beat complex graphs | Don't over-engineer |

---

## Memory Competencies Framework

We evaluate four core competencies essential for memory agents, as defined by MemoryAgentBench:

### 1. Accurate Retrieval (AR)

**Definition:** The ability to locate and extract precise information from conversation history.

| Sub-type | Description | Example |
|----------|-------------|---------|
| **Single-hop (AR-SH)** | Direct fact recall from one source | "What project did I mention?" |
| **Multi-hop (AR-MH)** | Inference over multiple facts | "What's the status of the task in my current project?" |
| **Temporal (AR-T)** | Time-based retrieval | "What did I complete yesterday?" |

**Why it matters:** Users expect agents to remember what was discussed without repeating themselves.

**Research basis:** LoCoMo benchmark (Xu et al., 2024), RULER-QA (Hsieh et al., 2024)

---

### 2. Test-Time Learning (TTL)

**Definition:** The ability to learn new rules, preferences, or context during a conversation without parameter updates.

| Sub-type | Description | Example |
|----------|-------------|---------|
| **Context Learning** | Remember stated preferences | "I'm focusing on Voice Agent today" |
| **Rule Learning** | Apply user-defined rules | "Always prioritize high-priority tasks" |
| **Procedural Learning** | Learn multi-step procedures | "When I say 'done', complete the last task" |

**Why it matters:** Users want to teach the agent their workflow without repeating instructions.

**Research basis:** InfBench classification tasks, LongMemEval (Wang et al., 2024)

---

### 3. Long-Range Understanding (LRU)

**Definition:** The ability to form coherent summaries or global views over extended interactions.

| Sub-type | Description | Example |
|----------|-------------|---------|
| **Summarization** | Compress many turns into summary | "What have I been working on?" |
| **Pattern Recognition** | Identify recurring themes | "What projects need attention?" |
| **Global Context** | Understand overall state | "Give me a productivity summary" |

**Why it matters:** Users need high-level insights, not just fact retrieval.

**Research basis:** InfBench summarization, NovelQA (Wang et al., 2024)

---

### 4. Conflict Resolution (CR)

**Definition:** The ability to handle contradictory or updated information correctly.

| Sub-type | Description | Example |
|----------|-------------|---------|
| **Single-hop (CR-SH)** | Direct update | "Actually, I'm on VoiceAgent now, not AgentOps" |
| **Multi-hop (CR-MH)** | Update affecting derived facts | Change project → ask filtered question |
| **Temporal Priority** | Later info overrides earlier | Complete task → status should show "done" |

**Why it matters:** Information changes. Agents must track the latest state.

**Research basis:** FactConsolidation dataset (Hu et al., 2025), MQUAKE (Zhong et al., 2023)

**⚠️ Critical Finding:** This is the hardest competency. Best models achieve <10% accuracy on multi-hop conflict resolution.

---

## Test Scenarios

### Short-Term Memory Tests

#### ST-1: Context Carryover (AR-SH)
```
User: "Show me the AgentOps project"
Agent: [displays AgentOps tasks]
User: "What's high priority?"
Expected: Filters to AgentOps high-priority tasks (not all projects)
Validates: Single-hop retrieval from session context
```

#### ST-2: Multi-Hop Context (AR-MH)
```
User: "Show me AgentOps"
Agent: [stores context: project=AgentOps]
User: "Start the debugging task"
Agent: [stores context: project=AgentOps, task=debugging]
User: "What am I working on?"
Expected: "The debugging task in AgentOps"
Validates: Multi-hop retrieval combining project + task context
```

#### ST-3: Context Learning (TTL)
```
User: "I'm focusing on Voice Agent today"
Agent: [stores preference]
User: "What should I do next?"
Expected: Suggests Voice Agent tasks specifically
Validates: Test-time learning of user preference
```

#### ST-4: Context Switch (CR-SH)
```
User: "Show me AgentOps"
User: "Actually, switch to Voice Agent"
User: "What's high priority?"
Expected: Shows Voice Agent priorities (not AgentOps)
Validates: Single-hop conflict resolution
```

#### ST-5: Baseline (Memory OFF)
```
[Disable short-term memory]
User: "Show me AgentOps"
User: "What's high priority?"
Expected: Shows ALL high-priority OR asks "which project?"
Validates: Memory is actually being used (not just luck)
```

---

### Long-Term Memory Tests

#### LT-1: Action Recording
```
User: "Mark the debugging task as done"
Agent: [completes task, writes to long-term memory]
Verify: Memory stats show increased long-term count
Validates: Write operations work
```

#### LT-2: Temporal Retrieval (AR-T)
```
[After completing several tasks over time]
User: "What did I complete today?"
Expected: Lists today's completions with timestamps
User: "What did I do yesterday?"
Expected: Lists yesterday's actions
User: "What have I done this week?"
Expected: Weekly summary
Validates: Time-based retrieval from action history
```

#### LT-3: Summarization (LRU)
```
[After many actions across multiple sessions]
User: "Summarize my activity"
Expected: High-level summary (not just a list)
User: "What projects have I been working on?"
Expected: Project list derived from action history
Validates: Long-range understanding
```

#### LT-4: Status Updates (CR-S)
```
User: "Complete the debugging task"
Agent: [marks done]
User: "Is the debugging task done?"
Expected: "Yes, you completed it at [time]"
User: "Start the debugging task again"
Agent: [marks in_progress]
User: "What's the status of debugging task?"
Expected: "In progress" (not "done")
Validates: Conflict resolution with status changes
```

#### LT-5: Baseline (Memory OFF)
```
[Disable long-term memory]
User: "What did I do last week?"
Expected: "I don't have access to historical data" or similar
Validates: Memory is actually required
```

---

### Shared Memory Tests (Agent Handoff)

#### SH-1: Basic Handoff
```
User: "I finished the checkpointer task"
Flow:
  1. Retrieval agent searches for "checkpointer"
  2. Retrieval writes best_match to shared memory
  3. Worklog agent reads from shared memory
  4. Worklog completes the correct task (no re-search)
Expected: Task completed with single search operation
Validates: Agent-to-agent context transfer
```

#### SH-2: Handoff Accuracy
```
Verify in debug panel:
- Retrieval found correct task
- Shared memory contains task_id
- Worklog read from shared (didn't re-search)
- Correct task was completed
- "Agent Handoff: ✅" indicator shown
```

#### SH-3: Ambiguous Handoff (CR-MH)
```
User: "Complete the MCP task"
Agent: [finds multiple matches]
Agent: "Which one? 1) MCP integration 2) MCP testing"
User: "The first one"
Expected: Correct task completed via handoff
Validates: Multi-hop conflict resolution in handoff
```

---

## Evaluation Metrics

### Primary Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | Correct answer / Total questions | >80% |
| **F1 Score** | Harmonic mean of precision and recall | >75% |
| **SubEM** | Exact substring match | >70% |
| **Recall@5** | Correct item in top 5 retrievals | >90% |

### Efficiency Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Memory Read Latency** | Time to read from memory | <30ms |
| **Memory Write Latency** | Time to write to memory | <50ms |
| **Token Efficiency** | Tokens used vs. baseline | <30% of baseline |
| **Memory Overhead** | % of total response time | <5% |

### Competency Scores

| Competency | Metric | Industry Baseline | Our Target |
|------------|--------|-------------------|------------|
| AR (Single-hop) | Accuracy | 70-85% | >85% |
| AR (Multi-hop) | Accuracy | 40-60% | >60% |
| AR (Temporal) | Accuracy | 50-70% | >70% |
| TTL | Accuracy | 60-80% | >80% |
| LRU | GPT-4 Judge F1 | 50-70% | >70% |
| CR (Single-hop) | Accuracy | 50-70% | >70% |
| CR (Multi-hop) | Accuracy | **<10%** | >30% |

**Note:** Multi-hop conflict resolution is an open research problem. Industry baselines are very low.

---

## Memory Architecture

### Three-Tier Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                      Flow Companion                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Short-Term     │  │   Long-Term     │  │   Shared     │ │
│  │  Memory         │  │   Memory        │  │   Memory     │ │
│  ├─────────────────┤  ├─────────────────┤  ├──────────────┤ │
│  │ TTL: 2 hours    │  │ TTL: Persistent │  │ TTL: 5 min   │ │
│  │ Scope: Session  │  │ Scope: User     │  │ Scope: Turn  │ │
│  │ Use: Context    │  │ Use: History    │  │ Use: Handoff │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│           │                    │                   │         │
│           └────────────────────┼───────────────────┘         │
│                                │                             │
│                    ┌───────────▼───────────┐                 │
│                    │    MongoDB Atlas      │                 │
│                    │  (Unified Backend)    │                 │
│                    └───────────────────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Memory Operations

| Operation | Short-Term | Long-Term | Shared |
|-----------|------------|-----------|--------|
| Read | Before LLM call | On history query | On agent handoff |
| Write | After each turn | After actions | After search |
| Update | Upsert pattern | Append-only | Consume on read |
| TTL | 2 hours | Never expires | 5 minutes |

### Why Separate Collections?

MongoDB Atlas doesn't support multiple TTL indexes on a single collection. Each memory type has different lifecycle requirements:

- **Short-term**: Expires after session ends (2 hours of inactivity)
- **Long-term**: Never expires (user's action history)
- **Shared**: Expires quickly (agent handoff is ephemeral)

---

## Benchmarks & Baselines

### Comparison with Existing Systems

| System | AR-SH | AR-MH | TTL | LRU | CR-SH | CR-MH |
|--------|-------|-------|-----|-----|-------|-------|
| MemGPT | 65% | 45% | 60% | 55% | 50% | 6% |
| Mem0 | 70% | 40% | 55% | 45% | 45% | 4% |
| Long-Context (GPT-4) | 75% | 50% | 80% | 70% | 60% | 7% |
| RAG (Dense) | 80% | 35% | 40% | 30% | 40% | 3% |
| **Flow Companion** | TBD | TBD | TBD | TBD | TBD | TBD |

*Baselines from MemoryAgentBench (Hu et al., 2025)*

### Datasets Used

| Dataset | Competency | Size | Source |
|---------|------------|------|--------|
| LoCoMo | AR, TTL | 300 turns/conv | Xu et al., 2024 |
| RULER-QA | AR (multi-hop) | 10K questions | Hsieh et al., 2024 |
| InfBench | TTL, LRU | 5K examples | Zhang et al., 2024 |
| FactConsolidation | CR | 6K-262K tokens | Hu et al., 2025 |
| **Flow Companion Evals** | All | Custom | This project |

---

## Research Citations

### Core Memory Systems Papers

1. **MemGPT: Towards LLMs as Operating Systems**
   - Packer, C., Fang, V., et al. (2023)
   - UC Berkeley
   - Introduced hierarchical memory management for LLMs
   - https://arxiv.org/abs/2310.08560

2. **Generative Agents: Interactive Simulacra of Human Behavior**
   - Park, J.S., O'Brien, J.C., et al. (2023)
   - Stanford University
   - Memory streams, reflection, and retrieval for agents
   - https://arxiv.org/abs/2304.03442

3. **A-Mem: Agentic Memory for LLM Agents**
   - (2025)
   - Achieved 85-93% token reduction vs. MemGPT/Mem0
   - https://arxiv.org/abs/2502.12110

4. **MIRIX: Multi-Agent Memory System for LLM-Based Agents**
   - Wang, X., Chen, Y. (2025)
   - Six memory types: Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault
   - https://arxiv.org/abs/2507.07957

### Evaluation Benchmarks

5. **MemoryAgentBench: Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions**
   - Hu, Y., Wang, Y., McAuley, J. (2025)
   - Defined 4 core competencies: AR, TTL, LRU, CR
   - https://arxiv.org/abs/2507.05257

6. **MemBench: Comprehensive Evaluation of Memory in LLM-based Agents**
   - Tan, H., Zhang, Z., et al. (2025)
   - ACL 2025 Findings
   - https://aclanthology.org/2025.findings-acl.989/

7. **LoCoMo: Evaluating Very Long-Term Conversational Memory**
   - Xu, J., et al. (2024)
   - ACL 2024
   - 300 turns, 9K tokens per conversation
   - https://aclanthology.org/2024.acl-long.747

### Context Engineering Papers

8. **LLMLingua: Compressing Prompts for Accelerated Inference**
   - Jiang, H., et al. (2023)
   - Microsoft Research
   - 2-10x compression with minimal performance loss
   - https://arxiv.org/abs/2310.05736

9. **Lost in the Middle: How Language Models Use Long Contexts**
   - Liu, N.F., et al. (2023)
   - Stanford/UC Berkeley
   - LLMs struggle with information in middle of context
   - https://arxiv.org/abs/2307.03172

10. **Reflexion: Language Agents with Verbal Reinforcement Learning**
    - Shinn, N., et al. (2023)
    - Agents that learn from stored past experiences
    - https://arxiv.org/abs/2303.11366

### Multi-Agent Systems

11. **AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation**
    - Wu, Q., et al. (2023)
    - Microsoft Research
    - Multi-agent coordination patterns
    - https://arxiv.org/abs/2308.08155

12. **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework**
    - Hong, S., et al. (2023)
    - Shared memory/blackboard for agent coordination
    - https://arxiv.org/abs/2308.00352

---

## Running the Evaluations

### Quick Start

```bash
# Run all memory tests
python -m evals.runner --config all_memory_context

# Run specific competency tests
python -m evals.runner --tests "memory_ar_single,memory_ar_multi"

# Run with comparison
python -m evals.runner --compare baseline,all_memory_context
```

### Eval Dashboard

```bash
# Start the evaluation dashboard
streamlit run evals_app.py --server.port 8502

# Access at http://localhost:8502
```

### Test Configuration

```python
# evals/test_suite.py
MEMORY_TESTS = [
    # Accurate Retrieval
    {"id": "memory_ar_single", "query": "What's high priority?", "setup": "Show me AgentOps"},
    {"id": "memory_ar_multi", "query": "What am I working on?", "setup": ["Show me AgentOps", "Start debugging"]},
    {"id": "memory_ar_temporal", "query": "What did I complete today?"},
    
    # Test-Time Learning
    {"id": "memory_ttl_context", "query": "What should I do?", "setup": "I'm focusing on Voice Agent"},
    
    # Long-Range Understanding
    {"id": "memory_lru_summary", "query": "Summarize my activity"},
    
    # Conflict Resolution
    {"id": "memory_cr_single", "query": "What's priority?", "setup": ["Show AgentOps", "Switch to Voice"]},
    {"id": "memory_cr_multi", "query": "Complete MCP task", "clarify": "The first one"},
]
```

### Memory Configs

```python
# evals/configs.py
MEMORY_CONFIGS = {
    "short_term_only": {
        "short_term": True,
        "long_term": False,
        "shared": False,
        "context_injection": True,
    },
    "long_term_only": {
        "short_term": False,
        "long_term": True,
        "shared": False,
        "context_injection": False,
    },
    "all_memory": {
        "short_term": True,
        "long_term": True,
        "shared": True,
        "context_injection": True,
    },
}
```

---

## Contributing

We welcome contributions to improve the memory evaluation framework:

1. **New test scenarios**: Add tests for edge cases
2. **Benchmark comparisons**: Run against other memory systems
3. **Metric improvements**: Propose new evaluation metrics
4. **Bug fixes**: Report issues with existing tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

This evaluation framework builds on research from:
- UC Berkeley (MemGPT, Letta)
- Stanford (Generative Agents, Lost in the Middle)
- Microsoft Research (LLMLingua, AutoGen)
- MemoryAgentBench team (UCSD)

Special thanks to the open-source memory systems community.