"""Validation Agent - Verifies workflow graph correctness, topology, and component configuration completeness.
Computes mathematically weighted readiness score and generates requirement test cases.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ValidationAgent:
    """Specialized AI agent for graph validation, schema checking, and readiness scoring."""

    def __init__(self):
        self.role = "Workflow Validator"

    def validate_workflow(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validates graph topology, connections, and parameter completeness.
        Returns validation issues, readiness score, and metrics.
        """
        issues: List[Dict[str, Any]] = []

        # 1. Structural Checks
        if not nodes:
            issues.append(
                {
                    "id": "err-no-nodes",
                    "category": "structural",
                    "severity": "error",
                    "title": "No Components in Workflow",
                    "description": "The workflow contains no building blocks.",
                    "suggestedFix": "Add at least one START block and one FINISH block.",
                }
            )

        # Entry (Input) node check
        has_entry = any(
            self._get_component_type(n) == "Input"
            or n.get("data", {}).get("label", "").lower() in ["start", "upload resume", "customer ticket", "receive invoice"]
            for n in nodes
        )
        if nodes and not has_entry:
            issues.append(
                {
                    "id": "warn-no-start",
                    "category": "structural",
                    "severity": "warning",
                    "title": "Missing Entry Component",
                    "description": "Your agent does not have a designated entry step (Input node).",
                    "suggestedFix": "Add a START (Input) block to capture incoming payloads.",
                }
            )

        # Terminal (Output) node check
        has_exit = any(
            self._get_component_type(n) == "Output"
            or "output" in n.get("data", {}).get("label", "").lower()
            or "report" in n.get("data", {}).get("label", "").lower()
            for n in nodes
        )
        if nodes and not has_exit:
            issues.append(
                {
                    "id": "warn-no-exit",
                    "category": "structural",
                    "severity": "warning",
                    "title": "Missing Exit Component",
                    "description": "Your agent does not have a designated terminal step (Output node).",
                    "suggestedFix": "Add an Output block to present final results.",
                }
            )

        # 2. Connection and Connectivity Checks
        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e.get("source"))
            connected_node_ids.add(e.get("target"))

        if len(nodes) > 1:
            disconnected = [n for n in nodes if n.get("id") not in connected_node_ids]
            for d in disconnected:
                label = d.get("data", {}).get("label") or d.get("id")
                issues.append(
                    {
                        "id": f"conn-{d.get('id')}",
                        "nodeId": d.get("id"),
                        "category": "connection",
                        "severity": "warning",
                        "title": f"'{label}' is Disconnected",
                        "description": "This step is not linked to any other step in the workflow.",
                        "suggestedFix": "Drag a connector line to link this step into your agent's flow.",
                    }
                )

        # 3. Component Configuration Checks
        missing_configs = 0
        for n in nodes:
            ctype = self._get_component_type(n)
            config = n.get("data", {}).get("config", {}) or n.get("config", {})
            label = n.get("data", {}).get("label") or n.get("id")

            if ctype == "LLM":
                instructions = config.get("instructions", "").strip()
                if not instructions:
                    missing_configs += 1
                    issues.append(
                        {
                            "id": f"config-{n.get('id')}",
                            "nodeId": n.get("id"),
                            "category": "configuration",
                            "severity": "error",
                            "title": f"Missing Instructions in '{label}'",
                            "description": "The AI Assistant component requires instructions before it can generate prompt responses.",
                            "suggestedFix": "Configure instructions or rubric in the component parameters panel.",
                        }
                    )
            elif ctype == "Condition":
                rule = config.get("rule", "").strip()
                if not rule:
                    missing_configs += 1
                    issues.append(
                        {
                            "id": f"config-{n.get('id')}",
                            "nodeId": n.get("id"),
                            "category": "configuration",
                            "severity": "error",
                            "title": f"Missing Rule in '{label}'",
                            "description": "The Condition component requires a boolean rule expression.",
                            "suggestedFix": "Specify a rule (e.g., 'score >= 7') in the configuration panel.",
                        }
                    )

        # 4. Mathematically Weighted Dynamic Readiness Score Calculation
        # Formula: Structural (30%) + Configuration (40%) + Connection (30%)
        structural_score = 0
        if has_entry:
            structural_score += 15
        if has_exit:
            structural_score += 15

        config_score = 40
        config_deduction = missing_configs * 20
        config_score = max(0, config_score - config_deduction)

        connection_score = 30
        disconnected_count = len([n for n in nodes if n.get("id") not in connected_node_ids]) if len(nodes) > 1 else 0
        connection_score = max(0, connection_score - (disconnected_count * 15))

        total_score = structural_score + config_score + connection_score
        readiness_score = max(10, min(100, total_score)) if nodes else 0

        is_valid = not any(i["severity"] == "error" for i in issues)

        return {
            "is_valid": is_valid,
            "readiness_score": readiness_score,
            "issues": issues,
            "metrics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "structural_score": structural_score,
                "config_score": config_score,
                "connection_score": connection_score,
                "errors_count": sum(1 for i in issues if i["severity"] == "error"),
                "warnings_count": sum(1 for i in issues if i["severity"] == "warning"),
            },
        }

    def _get_component_type(self, node: Dict[str, Any]) -> str:
        data = node.get("data", {})
        if isinstance(data, dict) and "componentType" in data:
            return data["componentType"]
        return node.get("type", "Input")
