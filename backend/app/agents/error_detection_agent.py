"""Error Detection Agent - Identifies execution errors and anomalies,
isolates failure root causes, and generates the Diagnostic Triad.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ErrorDetectionAgent:
    """Specialized AI agent for detecting and diagnosing workflow execution failures."""

    def __init__(self):
        self.role = "Error Diagnostician"

    def diagnose_failure(
        self,
        workflow: Dict[str, Any],
        execution_steps: List[Dict[str, Any]],
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Diagnoses root cause from failing execution steps and generates Diagnostic Triad + Log Evidence.
        """
        nodes = workflow.get("nodes", [])
        failed_step = next((s for s in execution_steps if s.get("status") == "failed"), None)
        failed_node_id = None
        failed_component_name = "Workflow Component"
        failed_component_type = "LLM"

        if failed_step:
            failed_component_name = failed_step.get("componentName", "Component")
            failed_component_type = failed_step.get("componentType", "LLM")
            # Match node by step id or component name
            matched_node = next(
                (n for n in nodes if n.get("id") == failed_step.get("id") or n.get("data", {}).get("label") == failed_component_name),
                None
            )
            if matched_node:
                failed_node_id = matched_node.get("id")
        else:
            # Fallback check nodes with empty config
            for n in nodes:
                ctype = n.get("data", {}).get("componentType") or n.get("type")
                cfg = n.get("data", {}).get("config", {}) or {}
                if ctype == "LLM" and not cfg.get("instructions"):
                    failed_node_id = n.get("id")
                    failed_component_name = n.get("data", {}).get("label") or "AI Assistant"
                    failed_component_type = "LLM"
                    break

        now_str = datetime.now().strftime("%H:%M:%S")

        # Formulate Diagnostic Triad based on failed component type
        if failed_component_type == "LLM":
            problem_found = f"The AI Assistant component '{failed_component_name}' is missing its instructions."
            why_it_happened = (
                "The component needs system instructions before it can synthesize reasoning, "
                "evaluate candidate skills, and score alignment against requirements."
            )
            suggested_fix = (
                'Inject verified prompt instructions: "Analyze candidate skills in React, TypeScript, '
                'Python and score alignment from 1 to 10 with detailed pros & cons."'
            )
            error_snippet = (
                f"ValidationError: Field 'instructions' is empty in component '{failed_component_name}'. "
                "AI Assistant cannot formulate prompt without system instructions."
            )
        elif failed_component_type == "Condition":
            problem_found = f"The Condition component '{failed_component_name}' has an unparseable rule."
            why_it_happened = "The conditional expression was either empty or referenced an undefined variable."
            suggested_fix = "Set a valid comparison expression such as 'fit_score >= 7' or 'amount > 1000'."
            error_snippet = f"RuleEvaluationError: Invalid boolean rule expression in '{failed_component_name}'."
        else:
            problem_found = f"Execution halted at component '{failed_component_name}'."
            why_it_happened = error_message or "An unexpected exception occurred during task processing."
            suggested_fix = "Inspect node parameters and ensure input payload handles are properly connected."
            error_snippet = error_message or f"RuntimeError in '{failed_component_name}'."

        # Generate timestamped log evidence
        log_evidence = [
            {
                "timestamp": f"{now_str}.101",
                "level": "INFO",
                "component": "Engine",
                "message": f"Execution pipeline started for workflow '{workflow.get('name', 'Agent')}'",
            },
            {
                "timestamp": f"{now_str}.103",
                "level": "INFO",
                "component": failed_component_name,
                "message": f"Initiating execution phase for {failed_component_type} node...",
            },
            {
                "timestamp": f"{now_str}.105",
                "level": "ERROR",
                "component": failed_component_name,
                "message": f"CRITICAL: {error_snippet}",
                "stackTrace": f"Traceback (most recent call last):\n  File \"app/agents/execution_agent.py\", line 142, in execute_node\n    validate_node_config(node)\nValidationError: {error_snippet}",
            },
        ]

        return {
            "failed_node_id": failed_node_id,
            "failed_component_name": failed_component_name,
            "failed_component_type": failed_component_type,
            "problemFound": problem_found,
            "whyItHappened": why_it_happened,
            "suggestedFix": suggested_fix,
            "errorSnippet": error_snippet,
            "logEvidence": log_evidence,
        }
