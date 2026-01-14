"""
Workflow Execution Engine

Executes multi-step procedural workflows with:
- Parameter extraction from user messages
- Result capture between steps
- Variable substitution
- Error handling and rollback
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes procedural memory workflows step-by-step."""

    def __init__(self, tool_registry: Dict[str, Any]):
        """
        Initialize workflow executor.

        Args:
            tool_registry: Dict mapping action names to callable tools
        """
        self.tool_registry = tool_registry
        self.captured_results = {}  # Stores results from each step

    def execute_workflow(
        self,
        workflow: Dict,
        user_message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Execute a workflow by running each step sequentially.

        Args:
            workflow: Workflow document from procedural memory
            user_message: Original user message for parameter extraction
            context: Optional context dict with pre-extracted parameters

        Returns:
            {
                "success": bool,
                "workflow_name": str,
                "steps_completed": int,
                "total_steps": int,
                "results": [],
                "captured": {},  # All captured variables
                "error": str or None
            }
        """
        workflow_name = workflow.get("name", "Unknown Workflow")
        steps = workflow.get("workflow", {}).get("steps", [])
        total_steps = len(steps)

        logger.info(f"🔄 Executing workflow: {workflow_name} ({total_steps} steps)")

        self.captured_results = {}
        results = []
        context = context or {}

        for step in steps:
            step_num = step.get("step", "?")
            action = step.get("action")

            logger.info(f"  Step {step_num}/{total_steps}: {action}")

            try:
                # Execute step
                step_result = self._execute_step(
                    step=step,
                    user_message=user_message,
                    context=context
                )

                results.append({
                    "step": step_num,
                    "action": action,
                    "success": step_result.get("success", False),
                    "result": step_result.get("result")
                })

                # Capture result if specified
                capture_key = step.get("capture_result")
                if capture_key and step_result.get("success"):
                    captured_value = self._extract_capture_value(
                        step_result.get("result"),
                        capture_key
                    )
                    self.captured_results[f"step_{step_num}.{capture_key}"] = captured_value
                    logger.info(f"    ✓ Captured: {capture_key} = {captured_value}")

                # Check if step failed
                if not step_result.get("success", False):
                    logger.error(f"    ✗ Step failed: {step_result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "workflow_name": workflow_name,
                        "steps_completed": step_num - 1 if step_num > 1 else 0,
                        "total_steps": total_steps,
                        "results": results,
                        "captured": self.captured_results,
                        "error": f"Step {step_num} ({action}) failed: {step_result.get('error', 'Unknown error')}"
                    }

            except Exception as e:
                logger.exception(f"    ✗ Step {step_num} raised exception")
                return {
                    "success": False,
                    "workflow_name": workflow_name,
                    "steps_completed": step_num - 1 if step_num > 1 else 0,
                    "total_steps": total_steps,
                    "results": results,
                    "captured": self.captured_results,
                    "error": f"Step {step_num} ({action}) raised exception: {str(e)}"
                }

        logger.info(f"✅ Workflow completed successfully: {workflow_name}")

        return {
            "success": True,
            "workflow_name": workflow_name,
            "steps_completed": total_steps,
            "total_steps": total_steps,
            "results": results,
            "captured": self.captured_results,
            "error": None
        }

    def _execute_step(
        self,
        step: Dict,
        user_message: str,
        context: Dict
    ) -> Dict:
        """
        Execute a single workflow step.

        Args:
            step: Step definition from workflow
            user_message: Original user message
            context: Execution context

        Returns:
            {"success": bool, "result": any, "error": str or None}
        """
        action = step.get("action")

        # Get the tool function
        tool_fn = self.tool_registry.get(action)
        if not tool_fn:
            return {
                "success": False,
                "result": None,
                "error": f"Tool '{action}' not found in registry"
            }

        # Build parameters
        params = {}

        # Extract from user message if specified
        extract_fields = step.get("extract_from_user", [])
        if extract_fields:
            extracted = self._extract_parameters_from_message(
                user_message,
                extract_fields,
                context
            )
            params.update(extracted)

        # Use captured results from previous steps
        use_captured = step.get("use_captured", {})
        if use_captured:
            for param_name, capture_ref in use_captured.items():
                if capture_ref in self.captured_results:
                    params[param_name] = self.captured_results[capture_ref]
                else:
                    logger.warning(f"    ⚠️ Captured variable not found: {capture_ref}")

        # Static parameters from step definition
        static_params = step.get("parameters", {})
        params.update(static_params)

        # Execute tool
        try:
            result = tool_fn(**params)
            return {
                "success": True,
                "result": result,
                "error": None
            }
        except Exception as e:
            logger.exception(f"Tool '{action}' raised exception")
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }

    def _extract_parameters_from_message(
        self,
        user_message: str,
        field_names: List[str],
        context: Dict
    ) -> Dict:
        """
        Extract parameters from user message using pattern matching.

        Args:
            user_message: Original user message
            field_names: List of field names to extract
            context: Execution context with any pre-extracted values

        Returns:
            Dict of extracted parameters
        """
        extracted = {}

        # Check context first
        for field in field_names:
            if field in context:
                extracted[field] = context[field]

        # Pattern-based extraction for common fields
        msg_lower = user_message.lower()

        if "title" in field_names and "title" not in extracted:
            # Extract task/project title
            # Patterns: "create task for X", "create project called X"
            patterns = [
                r'(?:create|add|make)\s+(?:task|project)\s+(?:for|called|named)\s+["\']?([^"\',.]+)',
                r'["\']([^"\']+)["\']',  # Quoted text
            ]
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted["title"] = match.group(1).strip()
                    break

        if "project_name" in field_names and "project_name" not in extracted:
            # Extract project name
            patterns = [
                r'project\s+(?:called|named)\s+["\']?([^"\',.]+)',
                r'for\s+(?:the\s+)?([A-Z][A-Za-z\s]+?)(?:\s+project)?'
            ]
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted["project_name"] = match.group(1).strip()
                    break

        if "priority" in field_names and "priority" not in extracted:
            # Extract priority
            if any(word in msg_lower for word in ["critical", "urgent", "asap"]):
                extracted["priority"] = "critical"
            elif "high" in msg_lower:
                extracted["priority"] = "high"
            elif "low" in msg_lower:
                extracted["priority"] = "low"
            else:
                extracted["priority"] = "medium"

        if "assignee" in field_names and "assignee" not in extracted:
            # Extract assignee
            patterns = [
                r'assign(?:ed)?\s+to\s+(\w+)',
                r'for\s+(\w+)(?:\s+to\s+(?:work|handle|do))?'
            ]
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    extracted["assignee"] = match.group(1).capitalize()
                    break

        if "due_date" in field_names and "due_date" not in extracted:
            # Extract due date (simple patterns)
            if any(word in msg_lower for word in ["tomorrow", "tmrw"]):
                from datetime import timedelta
                extracted["due_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "next week" in msg_lower:
                from datetime import timedelta
                extracted["due_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        return extracted

    def _extract_capture_value(self, result: Any, capture_key: str) -> Any:
        """
        Extract the value to capture from a tool result.

        Args:
            result: Tool result (could be dict, object, primitive)
            capture_key: Key to extract (e.g., "task_id", "project_id")

        Returns:
            Captured value
        """
        # If result is a dict, try to get the key
        if isinstance(result, dict):
            # Try direct key
            if capture_key in result:
                return result[capture_key]
            # Try common variations
            if "id" in result and capture_key.endswith("_id"):
                return result["id"]
            if "_id" in result and capture_key.endswith("_id"):
                return result["_id"]

        # If result is an object with attributes
        if hasattr(result, capture_key):
            return getattr(result, capture_key)
        if hasattr(result, "id") and capture_key.endswith("_id"):
            return getattr(result, "id")

        # Return as-is if primitive
        if isinstance(result, (str, int, float, bool)):
            return result

        # Fallback: return the whole result
        logger.warning(f"Could not extract '{capture_key}' from result, returning whole result")
        return result
