import re
from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler, get_node_meta
from app.engine.types import ExecutionContext, NodeExecutionError


def _resolve_dotted(container: Any, path: str) -> Any:
    """Resolves a dotted key path (e.g. 'candidate.score') inside nested dicts."""
    if not isinstance(container, dict):
        return None
    if path in container:
        return container[path]
    curr: Any = container
    for part in path.split("."):
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr


class ConditionNodeHandler(BaseNodeHandler):
    """Evaluates safe logical comparison operators and routes conditional branch flows."""

    def __init__(self):
        super().__init__("Condition")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        node_id, node_name, config = get_node_meta(node, "Condition Node")

        # Support both Member 4 (variable/value) and Member 3 (leftOperand/rightOperand) schemas
        variable = config.get("variable") or config.get("leftOperand")
        operator = str(config.get("operator", "==")).lower().strip()
        expected_val = config.get("value")
        if expected_val is None and "rightOperand" in config:
            expected_val = config.get("rightOperand")

        # Extract actual left-hand value
        actual_val = None
        if variable:
            actual_val = _resolve_dotted(incoming_data, str(variable))
            if actual_val is None:
                actual_val = _resolve_dotted(context.variables, str(variable))
            if actual_val is None and isinstance(incoming_data.get("output"), dict):
                actual_val = _resolve_dotted(incoming_data["output"], str(variable))

        if actual_val is None:
            # Fall back to primary input/output from upstream
            if "output" in incoming_data:
                actual_val = incoming_data["output"]
            elif "result" in incoming_data:
                actual_val = incoming_data["result"]
            elif "data" in incoming_data:
                actual_val = incoming_data["data"]
            elif "text" in incoming_data:
                actual_val = incoming_data["text"]
            elif len(incoming_data) == 1:
                actual_val = next(iter(incoming_data.values()))

        condition_met = self._evaluate_condition(actual_val, operator, expected_val, node_name, node_id)

        branch = "true" if condition_met else "false"
        context.variables[f"{node_id}_result"] = condition_met

        return {
            "result": condition_met,
            "condition": condition_met,
            "branch": branch,
            "value": actual_val,
            "operator": operator,
        }

    def _evaluate_condition(
        self, actual: Any, operator: str, expected: Any, node_name: str, node_id: str
    ) -> bool:
        if operator == "is_empty":
            return not bool(actual)
        elif operator == "is_not_empty":
            return bool(actual)
        elif operator in ("is_true", "true"):
            if isinstance(actual, str):
                return actual.strip().lower() == "true"
            return bool(actual) is True
        elif operator in ("is_false", "false"):
            if isinstance(actual, str):
                return actual.strip().lower() == "false"
            return bool(actual) is False

        # Normalize types for numbers where applicable
        if actual is not None and expected is not None:
            try:
                num_actual = float(actual)
                num_expected = float(expected)
                actual_cmp: Any = num_actual
                expected_cmp: Any = num_expected
            except (ValueError, TypeError):
                actual_cmp = str(actual)
                expected_cmp = str(expected)
        else:
            actual_cmp = actual
            expected_cmp = expected

        if operator in ("==", "equals", "eq", "is"):
            return actual_cmp == expected_cmp
        elif operator in ("!=", "not_equals", "neq", "is_not"):
            return actual_cmp != expected_cmp
        elif operator in (">", "greater_than", "gt"):
            return actual_cmp > expected_cmp
        elif operator in ("<", "less_than", "lt"):
            return actual_cmp < expected_cmp
        elif operator in (">=", "greater_than_or_equal", "gte"):
            return actual_cmp >= expected_cmp
        elif operator in ("<=", "less_than_or_equal", "lte"):
            return actual_cmp <= expected_cmp
        elif operator in ("contains", "in"):
            return str(expected).lower() in str(actual).lower()
        elif operator in ("not_contains", "not_in"):
            return str(expected).lower() not in str(actual).lower()
        elif operator == "starts_with":
            return str(actual).startswith(str(expected))
        elif operator == "ends_with":
            return str(actual).endswith(str(expected))
        elif operator == "regex":
            pattern = str(expected or "")
            if len(pattern) > 200:
                raise NodeExecutionError(
                    f"Regex pattern too long on node '{node_name}'.",
                    node_id=node_id,
                )
            try:
                return bool(re.search(pattern, str(actual or "")))
            except re.error as exc:
                raise NodeExecutionError(
                    f"Invalid regex pattern on node '{node_name}': {exc}",
                    node_id=node_id,
                )
        else:
            raise NodeExecutionError(
                f"Unsupported condition operator '{operator}' on node '{node_name}'.",
                node_id=node_id,
            )
