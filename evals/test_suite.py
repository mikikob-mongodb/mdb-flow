"""
Test suite for Flow Companion evals.
46 queries across 6 sections (including search mode variants).
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class InputType(Enum):
    SLASH = "slash"
    TEXT = "text"
    VOICE = "voice"

class Section(Enum):
    SLASH_COMMANDS = "slash_commands"
    TEXT_QUERIES = "text_queries"
    TEXT_ACTIONS = "text_actions"
    MULTI_TURN = "multi_turn"
    VOICE = "voice"

@dataclass
class TestQuery:
    id: int
    section: Section
    query: str
    input_type: InputType
    expected: str
    depends_on: Optional[int] = None  # For multi-turn and confirmations
    is_confirmation: bool = False

# Test Suite Definition
TEST_SUITE: List[TestQuery] = [
    # === Section 1: Slash Commands (10) ===
    TestQuery(1, Section.SLASH_COMMANDS, "/tasks", InputType.SLASH,
              "All tasks, <200ms"),
    TestQuery(2, Section.SLASH_COMMANDS, "/tasks status:in_progress", InputType.SLASH,
              "Filtered to in_progress only"),
    TestQuery(3, Section.SLASH_COMMANDS, "/tasks status:todo", InputType.SLASH,
              "Filtered to todo only"),
    TestQuery(4, Section.SLASH_COMMANDS, "/tasks priority:high", InputType.SLASH,
              "High priority tasks only"),
    TestQuery(5, Section.SLASH_COMMANDS, "/tasks project:AgentOps", InputType.SLASH,
              "Tasks in AgentOps project"),
    TestQuery(6, Section.SLASH_COMMANDS, "/tasks search debugging", InputType.SLASH,
              "Hybrid search with scores"),
    TestQuery(7, Section.SLASH_COMMANDS, "/tasks search voice agent", InputType.SLASH,
              "Semantic match on voice-related"),
    TestQuery(8, Section.SLASH_COMMANDS, "/projects", InputType.SLASH,
              "All projects with task counts"),
    TestQuery(9, Section.SLASH_COMMANDS, '/projects "Voice Agent"', InputType.SLASH,
              "Single project detail"),
    TestQuery(10, Section.SLASH_COMMANDS, "/projects search memory", InputType.SLASH,
              "Projects matching memory"),

    # === Section 2: Text Queries (8) ===
    TestQuery(11, Section.TEXT_QUERIES, "What are my tasks?", InputType.TEXT,
              "Formatted task list, tool called"),
    TestQuery(12, Section.TEXT_QUERIES, "What tasks are in progress?", InputType.TEXT,
              "Filtered list"),
    TestQuery(13, Section.TEXT_QUERIES, "Show me high priority tasks", InputType.TEXT,
              "Priority filter applied"),
    TestQuery(14, Section.TEXT_QUERIES, "Show me the AgentOps project", InputType.TEXT,
              "Project with its tasks"),
    TestQuery(15, Section.TEXT_QUERIES, "What's in the Voice Agent project?", InputType.TEXT,
              "Different project"),
    TestQuery(16, Section.TEXT_QUERIES, "Find tasks about debugging", InputType.TEXT,
              "Hybrid search, ranked results"),
    TestQuery(17, Section.TEXT_QUERIES, "Search for memory-related tasks", InputType.TEXT,
              "Semantic search"),
    TestQuery(18, Section.TEXT_QUERIES, "What did I work on recently?", InputType.TEXT,
              "Activity-based query"),

    # === Section 3: Text Actions (10) ===
    TestQuery(19, Section.TEXT_ACTIONS, "I finished the debugging doc", InputType.TEXT,
              "Search → confirm flow"),
    TestQuery(20, Section.TEXT_ACTIONS, "Yes", InputType.TEXT,
              "complete_task called", depends_on=19, is_confirmation=True),
    TestQuery(21, Section.TEXT_ACTIONS, "Mark the checkpointer task as done", InputType.TEXT,
              "Search → confirm flow"),
    TestQuery(22, Section.TEXT_ACTIONS, "Yes, that one", InputType.TEXT,
              "complete_task called", depends_on=21, is_confirmation=True),
    TestQuery(23, Section.TEXT_ACTIONS, "Start working on the voice agent app", InputType.TEXT,
              "Search → confirm → start"),
    TestQuery(24, Section.TEXT_ACTIONS, "Yes", InputType.TEXT,
              "start_task called", depends_on=23, is_confirmation=True),
    TestQuery(25, Section.TEXT_ACTIONS, "Add a note to voice agent: WebSocket streaming working", InputType.TEXT,
              "Search → confirm → add_note"),
    TestQuery(26, Section.TEXT_ACTIONS, "Correct", InputType.TEXT,
              "add_note called", depends_on=25, is_confirmation=True),
    TestQuery(27, Section.TEXT_ACTIONS, "Create a task for testing MCP integration in AgentOps", InputType.TEXT,
              "create_task called directly"),
    TestQuery(28, Section.TEXT_ACTIONS, "Create a high priority task for demo prep in AgentOps", InputType.TEXT,
              "create_task with priority"),

    # === Section 4: Multi-Turn Context (5) ===
    TestQuery(29, Section.MULTI_TURN, "Show me AgentOps", InputType.TEXT,
              "Sets context to AgentOps"),
    TestQuery(30, Section.MULTI_TURN, "What's high priority?", InputType.TEXT,
              "Filters within AgentOps", depends_on=29),
    TestQuery(31, Section.MULTI_TURN, "Any in progress?", InputType.TEXT,
              "Still within AgentOps", depends_on=30),
    TestQuery(32, Section.MULTI_TURN, "Show me Voice Agent project", InputType.TEXT,
              "Switches context"),
    TestQuery(33, Section.MULTI_TURN, "What's not started?", InputType.TEXT,
              "Filters within Voice Agent", depends_on=32),

    # === Section 5: Voice (7) ===
    TestQuery(34, Section.VOICE, "What are my tasks?", InputType.VOICE,
              "Same as text query #11"),
    TestQuery(35, Section.VOICE, "What's in progress?", InputType.VOICE,
              "Same as text query #12"),
    TestQuery(36, Section.VOICE, "Show me the AgentOps project", InputType.VOICE,
              "Same as text query #14"),
    TestQuery(37, Section.VOICE, "Find tasks about debugging", InputType.VOICE,
              "Same as text query #16"),
    TestQuery(38, Section.VOICE, "I finished the checkpointer documentation", InputType.VOICE,
              "Search → confirm flow"),
    TestQuery(39, Section.VOICE, "Yes", InputType.VOICE,
              "complete_task called", depends_on=38, is_confirmation=True),
    TestQuery(40, Section.VOICE, "Add a note to voice agent: audio input tested", InputType.VOICE,
              "Full action flow"),

    # === Section 6: Search Mode Variants (6) ===
    # Vector-only search tests (semantic/conceptual)
    TestQuery(41, Section.SLASH_COMMANDS, "/tasks search vector debugging", InputType.SLASH,
              "Vector-only semantic search"),
    TestQuery(42, Section.SLASH_COMMANDS, "/tasks search vector memory", InputType.SLASH,
              "Vector-only for conceptual match"),
    TestQuery(43, Section.SLASH_COMMANDS, "/projects search vector agent", InputType.SLASH,
              "Vector-only project search"),

    # Text-only search tests (keyword/exact match)
    TestQuery(44, Section.SLASH_COMMANDS, "/tasks search text debugging", InputType.SLASH,
              "Text-only keyword search"),
    TestQuery(45, Section.SLASH_COMMANDS, "/tasks search text checkpointer", InputType.SLASH,
              "Text-only exact match"),
    TestQuery(46, Section.SLASH_COMMANDS, "/projects search text AgentOps", InputType.SLASH,
              "Text-only project search"),
]

def get_tests_by_section(section: Section) -> List[TestQuery]:
    """Get all tests for a specific section."""
    return [t for t in TEST_SUITE if t.section == section]

def get_test_by_id(test_id: int) -> Optional[TestQuery]:
    """Get a specific test by ID."""
    return next((t for t in TEST_SUITE if t.id == test_id), None)

def get_section_counts() -> dict:
    """Get count of tests per section."""
    counts = {}
    for section in Section:
        counts[section.value] = len(get_tests_by_section(section))
    return counts

# Section display names
SECTION_NAMES = {
    Section.SLASH_COMMANDS: "Slash Commands",
    Section.TEXT_QUERIES: "Text Queries",
    Section.TEXT_ACTIONS: "Text Actions",
    Section.MULTI_TURN: "Multi-Turn Context",
    Section.VOICE: "Voice",
}
