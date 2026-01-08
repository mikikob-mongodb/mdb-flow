"""
Memory Competency Test Suite for Flow Companion.

Based on MemoryAgentBench (Hu et al., 2025) and MEMORY_EVALUATION_METHODOLOGY.md.

Tests 4 core competencies:
- AR: Accurate Retrieval (single-hop, multi-hop, temporal)
- TTL: Test-Time Learning (context, rules, procedural)
- LRU: Long-Range Understanding (summarization, patterns)
- CR: Conflict Resolution (single-hop, multi-hop)

Each test compares memory-enabled vs memory-disabled configurations.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class Competency(Enum):
    """Memory competency types."""
    AR_SH = "ar_sh"  # Accurate Retrieval - Single Hop
    AR_MH = "ar_mh"  # Accurate Retrieval - Multi Hop
    AR_T = "ar_t"    # Accurate Retrieval - Temporal
    TTL_C = "ttl_c"  # Test-Time Learning - Context
    TTL_R = "ttl_r"  # Test-Time Learning - Rules
    TTL_P = "ttl_p"  # Test-Time Learning - Procedural
    LRU_S = "lru_s"  # Long-Range Understanding - Summarization
    LRU_P = "lru_p"  # Long-Range Understanding - Patterns
    CR_SH = "cr_sh"  # Conflict Resolution - Single Hop
    CR_MH = "cr_mh"  # Conflict Resolution - Multi Hop

@dataclass
class MemoryTest:
    """Memory competency test definition."""
    id: int
    competency: Competency
    name: str
    turns: List[str]  # Conversation turns
    expected_behavior: str  # What should happen with memory enabled
    baseline_behavior: str  # What happens with memory disabled
    success_criteria: Dict[str, Any]  # How to judge success
    depends_on: Optional[int] = None  # Test dependency

# ============================================================================
# AR: ACCURATE RETRIEVAL TESTS
# ============================================================================

AR_TESTS = [
    # AR-SH: Single-Hop Retrieval
    MemoryTest(
        id=1,
        competency=Competency.AR_SH,
        name="Direct project context recall",
        turns=[
            "I'm working on the Voice Agent project",
            "What project am I working on?"
        ],
        expected_behavior="Retrieves 'Voice Agent' from session context",
        baseline_behavior="No memory - LLM cannot answer",
        success_criteria={
            "memory_enabled": {
                "must_contain": ["Voice Agent"],
                "tool_called": None,  # Direct context recall
                "context_read": True
            },
            "memory_disabled": {
                "must_contain": ["don't know", "haven't mentioned", "context"],
                "context_read": False
            }
        }
    ),
    MemoryTest(
        id=2,
        competency=Competency.AR_SH,
        name="Direct task context recall",
        turns=[
            "I'm working on implementing WebSocket streaming",
            "What task am I working on?"
        ],
        expected_behavior="Retrieves task from session context",
        baseline_behavior="No memory - cannot recall",
        success_criteria={
            "memory_enabled": {
                "must_contain": ["WebSocket streaming"],
                "context_read": True
            },
            "memory_disabled": {
                "must_contain": ["don't know", "haven't"],
                "context_read": False
            }
        }
    ),
    MemoryTest(
        id=3,
        competency=Competency.AR_SH,
        name="Direct preference recall",
        turns=[
            "I prefer high priority tasks",
            "What's my preference?"
        ],
        expected_behavior="Retrieves preference from session context",
        baseline_behavior="No memory - cannot recall",
        success_criteria={
            "memory_enabled": {
                "must_contain": ["high priority"],
                "context_read": True
            },
            "memory_disabled": {
                "must_contain": ["don't know", "haven't"],
                "context_read": False
            }
        }
    ),

    # AR-MH: Multi-Hop Retrieval
    MemoryTest(
        id=4,
        competency=Competency.AR_MH,
        name="Project + status context (2-hop)",
        turns=[
            "Show me the Voice Agent project",
            "What's high priority?"
        ],
        expected_behavior="Filters to Voice Agent high-priority tasks (combines project + priority)",
        baseline_behavior="Shows all high-priority tasks (no project context)",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_tasks",
                "tool_params_must_include": {"project_name": "Voice Agent", "priority": "high"},
                "context_read": True
            },
            "memory_disabled": {
                "tool_called": "get_tasks",
                "tool_params_missing": "project_name",  # No project context
                "context_read": False
            }
        }
    ),
    MemoryTest(
        id=5,
        competency=Competency.AR_MH,
        name="Project + task + action (3-hop)",
        turns=[
            "Show me AgentOps",
            "Start the debugging task",
            "What am I working on now?"
        ],
        expected_behavior="Retrieves 'debugging task in AgentOps' (3 pieces of context)",
        baseline_behavior="No context - cannot answer",
        success_criteria={
            "memory_enabled": {
                "must_contain": ["debugging", "AgentOps"],
                "context_read": True
            },
            "memory_disabled": {
                "must_contain": ["don't know", "haven't"],
                "context_read": False
            }
        }
    ),
    MemoryTest(
        id=6,
        competency=Competency.AR_MH,
        name="Disambiguation resolution (multi-hop)",
        turns=[
            "Find MCP tasks",
            "Mark the first one as done"
        ],
        expected_behavior="Resolves 'the first one' via disambiguation context + executes action",
        baseline_behavior="Cannot resolve 'the first one' - asks for clarification",
        success_criteria={
            "memory_enabled": {
                "tool_called": "resolve_disambiguation",
                "then_tool_called": "complete_task",
                "context_read": True
            },
            "memory_disabled": {
                "must_contain": ["which", "clarify", "specific"],
                "context_read": False
            }
        }
    ),

    # AR-T: Temporal Retrieval
    MemoryTest(
        id=7,
        competency=Competency.AR_T,
        name="Action history - today",
        turns=[
            "What did I do today?"
        ],
        expected_behavior="Retrieves today's actions from long-term memory",
        baseline_behavior="No action history - cannot answer",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "tool_params_must_include": {"time_range": "today"},
                "result_must_have": "actions"
            },
            "memory_disabled": {
                "tool_called": None,  # Tool not available
                "must_contain": ["don't have", "can't track", "history"]
            }
        }
    ),
    MemoryTest(
        id=8,
        competency=Competency.AR_T,
        name="Action history - this week",
        turns=[
            "What tasks did I complete this week?"
        ],
        expected_behavior="Retrieves completed actions from this week",
        baseline_behavior="No action history available",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "tool_params_must_include": {"time_range": "this_week", "action_type": "complete"}
            },
            "memory_disabled": {
                "tool_called": None,
                "must_contain": ["don't have", "can't track"]
            }
        }
    ),
    MemoryTest(
        id=9,
        competency=Competency.AR_T,
        name="Semantic search over history",
        turns=[
            "Find my work related to debugging"
        ],
        expected_behavior="Semantic search over action history embeddings",
        baseline_behavior="No action history - cannot search",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "tool_params_must_include": {"semantic_query": "debugging"},
                "result_must_have": "actions"
            },
            "memory_disabled": {
                "tool_called": None,
                "must_contain": ["don't have", "can't search history"]
            }
        }
    ),
]

# ============================================================================
# TTL: TEST-TIME LEARNING TESTS
# ============================================================================

TTL_TESTS = [
    # TTL-C: Context Learning (Preferences)
    MemoryTest(
        id=10,
        competency=Competency.TTL_C,
        name="Project preference learning",
        turns=[
            "I'm focusing on Memory Engineering today",
            "What are my tasks?"
        ],
        expected_behavior="Applies focus_project preference to filter tasks",
        baseline_behavior="Shows all tasks (no preference)",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_tasks",
                "tool_params_must_include": {"project_name": "Memory Engineering"},
                "context_written": True  # Preference stored
            },
            "memory_disabled": {
                "tool_called": "get_tasks",
                "tool_params_missing": "project_name",
                "context_written": False
            }
        }
    ),
    MemoryTest(
        id=11,
        competency=Competency.TTL_C,
        name="Priority preference learning",
        turns=[
            "Show me high priority tasks",
            "What should I work on?"
        ],
        expected_behavior="Applies priority preference automatically",
        baseline_behavior="Shows all tasks (no preference)",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_tasks",
                "tool_params_must_include": {"priority": "high"},
                "context_written": True
            },
            "memory_disabled": {
                "tool_called": "get_tasks",
                "tool_params_missing": "priority"
            }
        }
    ),
    MemoryTest(
        id=12,
        competency=Competency.TTL_C,
        name="Preference persistence across turns",
        turns=[
            "I'm focusing on Voice Agent",
            "What are my tasks?",
            "What should I do next?"  # 3rd turn - preference should persist
        ],
        expected_behavior="Preference persists across multiple turns",
        baseline_behavior="No preference - each turn independent",
        success_criteria={
            "memory_enabled": {
                "turn_2": {"tool_params_must_include": {"project_name": "Voice Agent"}},
                "turn_3": {"tool_params_must_include": {"project_name": "Voice Agent"}},
                "context_read": True
            },
            "memory_disabled": {
                "turn_3": {"tool_params_missing": "project_name"}
            }
        }
    ),

    # TTL-R: Rule Learning
    MemoryTest(
        id=13,
        competency=Competency.TTL_R,
        name="Simple rule extraction",
        turns=[
            "When I say done, complete the current task",
            "done"
        ],
        expected_behavior="Extracts rule + executes when triggered",
        baseline_behavior="No rule learning - 'done' not interpreted as action",
        success_criteria={
            "memory_enabled": {
                "turn_1": {"context_written": True},  # Rule stored
                "turn_2": {"rule_triggered": "done", "tool_called": "complete_task"}
            },
            "memory_disabled": {
                "turn_1": {"context_written": False},
                "turn_2": {"must_contain": ["clarify", "which task"]}
            }
        }
    ),
    MemoryTest(
        id=14,
        competency=Competency.TTL_R,
        name="Multiple rule learning",
        turns=[
            "When I say done, complete the current task",
            "When I say break, stop the current task",
            "done"
        ],
        expected_behavior="Stores multiple rules + executes correct one",
        baseline_behavior="No rule learning",
        success_criteria={
            "memory_enabled": {
                "turn_3": {"rule_triggered": "done", "tool_called": "complete_task"}
            },
            "memory_disabled": {
                "turn_3": {"must_contain": ["clarify", "which"]}
            }
        }
    ),

    # TTL-P: Procedural Learning
    MemoryTest(
        id=15,
        competency=Competency.TTL_P,
        name="Multi-step procedure learning",
        turns=[
            "Whenever I complete a task, always add a note with the completion date",
            "Mark the debugging task as done"
        ],
        expected_behavior="Completes task + automatically adds note per learned procedure",
        baseline_behavior="Only completes task (no automatic note)",
        success_criteria={
            "memory_enabled": {
                "turn_1": {"context_written": True},  # Procedure stored
                "turn_2": {"tool_called": ["complete_task", "add_note_to_task"]}
            },
            "memory_disabled": {
                "turn_2": {"tool_called": "complete_task", "tool_not_called": "add_note_to_task"}
            }
        }
    ),
]

# ============================================================================
# LRU: LONG-RANGE UNDERSTANDING TESTS
# ============================================================================

LRU_TESTS = [
    # LRU-S: Summarization
    MemoryTest(
        id=16,
        competency=Competency.LRU_S,
        name="Activity summarization",
        turns=[
            "Summarize my activity this week"
        ],
        expected_behavior="Generates summary from action history",
        baseline_behavior="No action history - cannot summarize",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "tool_params_must_include": {"summarize": True, "time_range": "this_week"},
                "result_must_have": "narrative",  # Pre-formatted narrative
                "must_contain": ["actions", "completed", "started"]
            },
            "memory_disabled": {
                "tool_called": None,
                "must_contain": ["don't have", "can't track"]
            }
        }
    ),
    MemoryTest(
        id=17,
        competency=Competency.LRU_S,
        name="Project-specific summarization",
        turns=[
            "Summarize my work on Voice Agent this month"
        ],
        expected_behavior="Filters to Voice Agent + generates summary",
        baseline_behavior="No action history available",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "result_must_have": "narrative",
                "must_contain": ["Voice Agent"]
            },
            "memory_disabled": {
                "tool_called": None
            }
        }
    ),

    # LRU-P: Pattern Recognition
    MemoryTest(
        id=18,
        competency=Competency.LRU_P,
        name="Project workload patterns",
        turns=[
            "Which projects have I been most active on?"
        ],
        expected_behavior="Analyzes action history for project patterns",
        baseline_behavior="No action history - cannot analyze",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "tool_params_must_include": {"summarize": True},
                "result_must_have": "by_project",  # Project breakdown
                "must_contain": ["most active", "project"]
            },
            "memory_disabled": {
                "tool_called": None
            }
        }
    ),
    MemoryTest(
        id=19,
        competency=Competency.LRU_P,
        name="Action type patterns",
        turns=[
            "What types of actions do I perform most?"
        ],
        expected_behavior="Analyzes action history for action type patterns",
        baseline_behavior="No action history available",
        success_criteria={
            "memory_enabled": {
                "tool_called": "get_action_history",
                "result_must_have": "by_type",  # Action type breakdown
                "must_contain": ["complete", "start", "create"]
            },
            "memory_disabled": {
                "tool_called": None
            }
        }
    ),
]

# ============================================================================
# CR: CONFLICT RESOLUTION TESTS
# ============================================================================

CR_TESTS = [
    # CR-SH: Single-Hop Conflict
    MemoryTest(
        id=20,
        competency=Competency.CR_SH,
        name="Direct project switch",
        turns=[
            "I'm working on AgentOps",
            "Actually, I'm working on Voice Agent now",
            "What project am I working on?"
        ],
        expected_behavior="Updates context - returns Voice Agent (latest)",
        baseline_behavior="No memory - cannot track or update",
        success_criteria={
            "memory_enabled": {
                "turn_3": {"must_contain": ["Voice Agent"], "must_not_contain": ["AgentOps"]},
                "context_updated": True  # Context overwritten
            },
            "memory_disabled": {
                "turn_3": {"must_contain": ["don't know", "haven't"]}
            }
        }
    ),
    MemoryTest(
        id=21,
        competency=Competency.CR_SH,
        name="Direct preference change",
        turns=[
            "I prefer high priority tasks",
            "Never mind, show me all tasks",
            "What are my tasks?"
        ],
        expected_behavior="Clears priority preference - shows all tasks",
        baseline_behavior="No preference tracking",
        success_criteria={
            "memory_enabled": {
                "turn_3": {"tool_params_missing": "priority"},  # Preference cleared
                "context_updated": True
            },
            "memory_disabled": {
                "turn_3": {"tool_params_missing": "priority"}  # Never had preference
            }
        }
    ),

    # CR-MH: Multi-Hop Conflict (HARDEST)
    MemoryTest(
        id=22,
        competency=Competency.CR_MH,
        name="Project switch with filtered query",
        turns=[
            "Show me AgentOps",
            "What's high priority?",  # Combines AgentOps + high priority
            "Actually, switch to Voice Agent",
            "What's high priority now?"  # Should be Voice Agent + high priority
        ],
        expected_behavior="Updates project context + applies priority filter to NEW project",
        baseline_behavior="No context tracking - each turn independent",
        success_criteria={
            "memory_enabled": {
                "turn_2": {"tool_params_must_include": {"project_name": "AgentOps", "priority": "high"}},
                "turn_4": {"tool_params_must_include": {"project_name": "Voice Agent", "priority": "high"}},
                "context_updated": True
            },
            "memory_disabled": {
                "turn_2": {"tool_params_missing": "project_name"},
                "turn_4": {"tool_params_missing": "project_name"}
            }
        }
    ),
    MemoryTest(
        id=23,
        competency=Competency.CR_MH,
        name="Task status update affects queries",
        turns=[
            "What tasks are in progress?",
            "Mark the debugging task as done",
            "What tasks are in progress?"  # Should no longer include debugging task
        ],
        expected_behavior="Task status updated in DB - subsequent query excludes it",
        baseline_behavior="Status updated but context-independent queries",
        success_criteria={
            "memory_enabled": {
                "turn_3": {"must_not_contain": ["debugging"]},  # Task no longer in_progress
                "action_recorded": True  # Action recorded in long-term memory
            },
            "memory_disabled": {
                "turn_3": {"must_not_contain": ["debugging"]},  # Same behavior (DB updated regardless)
                "action_recorded": False  # But no action history
            }
        }
    ),
    MemoryTest(
        id=24,
        competency=Competency.CR_MH,
        name="Disambiguation with preference update",
        turns=[
            "I'm focusing on Voice Agent",
            "Find streaming tasks",  # Multiple matches
            "Actually, I'm on AgentOps now",
            "Mark the first one as done"  # Should still resolve to Voice Agent tasks (disambiguation stored before switch)
        ],
        expected_behavior="Resolves disambiguation from PREVIOUS context (Voice Agent), not current (AgentOps)",
        baseline_behavior="No disambiguation or preference tracking",
        success_criteria={
            "memory_enabled": {
                "turn_4": {
                    "tool_called": "resolve_disambiguation",
                    "completed_task_from_project": "Voice Agent"  # Original disambiguation context
                }
            },
            "memory_disabled": {
                "turn_4": {"must_contain": ["clarify", "which"]}
            }
        }
    ),
]

# ============================================================================
# SUITE AGGREGATION
# ============================================================================

MEMORY_COMPETENCY_SUITE: List[MemoryTest] = (
    AR_TESTS + TTL_TESTS + LRU_TESTS + CR_TESTS
)

def get_tests_by_competency(competency: Competency) -> List[MemoryTest]:
    """Get all tests for a specific competency."""
    return [t for t in MEMORY_COMPETENCY_SUITE if t.competency == competency]

def get_test_by_id(test_id: int) -> Optional[MemoryTest]:
    """Get a specific test by ID."""
    return next((t for t in MEMORY_COMPETENCY_SUITE if t.id == test_id), None)

def get_competency_counts() -> Dict[Competency, int]:
    """Get count of tests per competency."""
    counts = {}
    for test in MEMORY_COMPETENCY_SUITE:
        counts[test.competency] = counts.get(test.competency, 0) + 1
    return counts

def get_total_tests() -> int:
    """Get total number of tests."""
    return len(MEMORY_COMPETENCY_SUITE)

# Research-based target metrics (from MEMORY_EVALUATION_METHODOLOGY.md)
COMPETENCY_TARGETS = {
    Competency.AR_SH: {"accuracy": 0.85, "baseline": 0.75},  # Single-hop retrieval
    Competency.AR_MH: {"accuracy": 0.60, "baseline": 0.45},  # Multi-hop retrieval
    Competency.AR_T: {"accuracy": 0.70, "baseline": 0.55},   # Temporal retrieval
    Competency.TTL_C: {"accuracy": 0.80, "baseline": 0.65},  # Context learning
    Competency.TTL_R: {"accuracy": 0.80, "baseline": 0.65},  # Rule learning
    Competency.TTL_P: {"accuracy": 0.75, "baseline": 0.60},  # Procedural learning
    Competency.LRU_S: {"accuracy": 0.70, "baseline": 0.55},  # Summarization
    Competency.LRU_P: {"accuracy": 0.70, "baseline": 0.55},  # Pattern recognition
    Competency.CR_SH: {"accuracy": 0.70, "baseline": 0.60},  # Single-hop conflict
    Competency.CR_MH: {"accuracy": 0.30, "baseline": 0.07},  # Multi-hop conflict (HARD!)
}

if __name__ == "__main__":
    print("Memory Competency Test Suite")
    print("=" * 60)
    print(f"Total tests: {get_total_tests()}")
    print("\nTests per competency:")
    for competency, count in get_competency_counts().items():
        target = COMPETENCY_TARGETS[competency]["accuracy"] * 100
        print(f"  {competency.value.upper()}: {count} tests (target: {target}% accuracy)")

    print("\n" + "=" * 60)
    print("Test IDs:")
    for test in MEMORY_COMPETENCY_SUITE:
        print(f"  {test.id:2d}. [{test.competency.value.upper()}] {test.name}")
