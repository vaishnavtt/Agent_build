from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler
from app.engine.types import ExecutionContext, NodeExecutionError


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
        config = node.get("config", {})
        node_id = node.get("id", "")
        node_name = node.get("name", "Condition Node")

        variable = config.get("variable")
        operator = str(config.get("operator", "==")).lower().strip()
        expected_val = config.get("value")

        # Extract actual left-hand value
        actual_val = None
        if variable:
            if variable in incoming_data:
                actual_val = incoming_data[variable]
            elif variable in context.variables:
                actual_val = context.variables[variable]

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
        # Normalize types for numbers where applicable
        if actual is not None and expected is not None:
            try:
                num_actual = float(actual)
                num_expected = float(expected)
                actual_cmp = num_actual
                expected_cmp = num_expected
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
        elif operator == "is_empty":
            return not bool(actual)
        elif operator == "is_not_empty":
            return bool(actual)
        elif operator in ("is_true", "true"):
            return bool(actual) is True
        elif operator in ("is_false", "false"):
            return bool(actual) is False
        else:
            raise NodeExecutionError(
                f"Unsupported condition operator '{operator}' on node '{node_name}'.",
                node_id=node_id,
            )
