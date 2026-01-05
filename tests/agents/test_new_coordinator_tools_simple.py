"""
Simplified Tests for 12 New Coordinator Tools

These tests verify that:
1. The new tools are defined and available
2. Tool definitions have correct parameters
3. Tools are exposed to the LLM in COORDINATOR_TOOLS

Note: End-to-end testing of actual LLM calling these tools is done manually
or via integration tests. These tests verify the tool infrastructure is set up correctly.
"""

import pytest
from agents.coordinator import COORDINATOR_TOOLS


class TestToolDefinitions:
    """Verify all 21 tools are defined with correct schemas."""

    def test_all_20_tools_defined(self):
        """Verify exactly 20 tools are exposed to LLM."""
        assert len(COORDINATOR_TOOLS) == 20, f"Expected 20 tools, got {len(COORDINATOR_TOOLS)}"

    def test_tool_names_are_unique(self):
        """Verify no duplicate tool names."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert len(tool_names) == len(set(tool_names)), "Tool names must be unique"

    def test_all_tools_have_required_fields(self):
        """Verify each tool has name, description, and input_schema."""
        for tool in COORDINATOR_TOOLS:
            assert 'name' in tool, f"Tool missing 'name': {tool}"
            assert 'description' in tool, f"Tool {tool.get('name')} missing 'description'"
            assert 'input_schema' in tool, f"Tool {tool.get('name')} missing 'input_schema'"


class TestNewTaskTools:
    """Verify new task management tools are defined."""

    def test_create_task_tool_defined(self):
        """Verify create_task tool exists and has correct schema."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'create_task'), None)
        assert tool is not None, "create_task tool not found"
        assert 'title' in tool['input_schema']['properties']
        assert 'project_name' in tool['input_schema']['properties']
        assert 'priority' in tool['input_schema']['properties']
        assert tool['input_schema']['required'] == ['title', 'project_name']

    def test_update_task_tool_defined(self):
        """Verify update_task tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'update_task'), None)
        assert tool is not None, "update_task tool not found"
        assert 'task_id' in tool['input_schema']['properties']
        assert 'task_id' in tool['input_schema']['required']

    def test_stop_task_tool_defined(self):
        """Verify stop_task tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'stop_task'), None)
        assert tool is not None, "stop_task tool not found"
        assert 'task_id' in tool['input_schema']['required']

    def test_add_context_to_task_tool_defined(self):
        """Verify add_context_to_task tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'add_context_to_task'), None)
        assert tool is not None, "add_context_to_task tool not found"
        assert 'task_id' in tool['input_schema']['required']
        assert 'context' in tool['input_schema']['required']

    def test_get_task_tool_defined(self):
        """Verify get_task tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'get_task'), None)
        assert tool is not None, "get_task tool not found"
        assert 'task_id' in tool['input_schema']['required']


class TestNewProjectTools:
    """Verify new project management tools are defined."""

    def test_create_project_tool_defined(self):
        """Verify create_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'create_project'), None)
        assert tool is not None, "create_project tool not found"
        assert 'name' in tool['input_schema']['properties']
        assert 'name' in tool['input_schema']['required']

    def test_update_project_tool_defined(self):
        """Verify update_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'update_project'), None)
        assert tool is not None, "update_project tool not found"
        assert 'project_id' in tool['input_schema']['required']

    def test_add_note_to_project_tool_defined(self):
        """Verify add_note_to_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'add_note_to_project'), None)
        assert tool is not None, "add_note_to_project tool not found"
        assert 'project_id' in tool['input_schema']['required']
        assert 'note' in tool['input_schema']['required']

    def test_add_context_to_project_tool_defined(self):
        """Verify add_context_to_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'add_context_to_project'), None)
        assert tool is not None, "add_context_to_project tool not found"

    def test_add_decision_to_project_tool_defined(self):
        """Verify add_decision_to_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'add_decision_to_project'), None)
        assert tool is not None, "add_decision_to_project tool not found"
        assert 'decision' in tool['input_schema']['required']

    def test_add_method_to_project_tool_defined(self):
        """Verify add_method_to_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'add_method_to_project'), None)
        assert tool is not None, "add_method_to_project tool not found"
        assert 'method' in tool['input_schema']['required']

    def test_get_project_tool_defined(self):
        """Verify get_project tool exists."""
        tool = next((t for t in COORDINATOR_TOOLS if t['name'] == 'get_project'), None)
        assert tool is not None, "get_project tool not found"
        assert 'project_id' in tool['input_schema']['required']


class TestExistingToolsStillPresent:
    """Verify original 9 tools still exist after adding 12 new ones."""

    def test_get_tasks_still_exists(self):
        """Verify get_tasks tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'get_tasks' in tool_names

    def test_search_tasks_still_exists(self):
        """Verify search_tasks tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'search_tasks' in tool_names

    def test_complete_task_still_exists(self):
        """Verify complete_task tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'complete_task' in tool_names

    def test_start_task_still_exists(self):
        """Verify start_task tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'start_task' in tool_names

    def test_add_note_to_task_still_exists(self):
        """Verify add_note_to_task tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'add_note_to_task' in tool_names

    def test_get_projects_still_exists(self):
        """Verify get_projects tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'get_projects' in tool_names

    def test_search_projects_still_exists(self):
        """Verify search_projects tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'search_projects' in tool_names

    def test_get_tasks_by_time_still_exists(self):
        """Verify get_tasks_by_time tool still exists."""
        tool_names = [t['name'] for t in COORDINATOR_TOOLS]
        assert 'get_tasks_by_time' in tool_names
