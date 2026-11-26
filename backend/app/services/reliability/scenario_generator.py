from typing import Any, Dict, List, Optional, Tuple

from app.schemas.reliability import (
    ExpectedHandling,
    ReliabilityCategory,
    ReliabilityScenario,
)
from app.services.testing.test_case_generator import TestCaseGenerator
from app.services.validation.workflow_validator import (
    _extract_node_config,
    _extract_node_type,
)


def _infer_stress_vector(name: str, category: str) -> str:
    """Assign a deterministic stress vector tag based on scenario name and category."""
    low = name.lower()
    if "empty" in low:
        return "EMPTY_INPUT"
    if "null" in low:
        return "NULL_INPUT"
    if "malformed json" in low:
        return "MALFORMED_JSON"
    if "incorrect data type" in low or "numeric" in low:
        return "DATA_TYPE_MISMATCH"
    if "invalid / non-url" in low:
        return "INVALID_URL_FORMAT"
    if "short" in low:
        return "MIN_LENGTH_BOUNDARY"
    if "long" in low or "large" in low:
        return "MAX_PAYLOAD_BOUNDARY"
    if "unicode" in low or "special" in low:
        return "UNICODE_AND_SPECIAL_CHARS"
    if "boundary" in low:
        return "CONDITION_THRESHOLD_BOUNDARY"
    if "optional" in low:
        return "OPTIONAL_OMISSION"
    if "condition" in low:
        return "CONDITIONAL_BRANCH_NORMAL"
    if category == "normal":
        return "BASELINE_VALID_INPUT"
    return "GENERAL_STRESS"


class ReliabilityScenarioGenerator:
    """Builds Normal, Robustness, and Edge reliability scenarios by extending Stage 2A TestCaseGenerator."""

    def __init__(self) -> None:
        self._base_generator = TestCaseGenerator()

    def generate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        requirement: Optional[str] = None,
        workflow_name: str = "Workflow",
    ) -> Tuple[Dict[ReliabilityCategory, List[ReliabilityScenario]], str, bool]:
        base_cases, _, input_type, input_required = self._base_generator.generate(
            nodes=nodes,
            edges=edges,
            requirement=requirement,
            workflow_name=workflow_name,
        )

        input_node = next((n for n in nodes if _extract_node_type(n) == "Input"), None)
        input_config = _extract_node_config(input_node) if input_node else {}
        input_field = str(input_config.get("inputField") or "input")

        grouped: Dict[ReliabilityCategory, List[ReliabilityScenario]] = {
            "normal": [],
            "robustness": [],
            "edge": [],
        }

        counters: Dict[ReliabilityCategory, int] = {
            "normal": 0,
            "robustness": 0,
            "edge": 0,
        }

        for tc in base_cases:
            if tc.category == "normal":
                rel_cat: ReliabilityCategory = "normal"
                expected_handling: ExpectedHandling = "SUCCESS"
            elif tc.category == "invalid":
                rel_cat = "robustness"
                expected_handling = "SAFE_REJECTION"
            else:
                rel_cat = "edge"
                expected_handling = "GRACEFUL_HANDLING"

            counters[rel_cat] += 1
            prefix = "norm" if rel_cat == "normal" else ("rob" if rel_cat == "robustness" else "edge")
            grouped[rel_cat].append(
                ReliabilityScenario(
                    scenario_id=f"rel-{prefix}-{counters[rel_cat]}",
                    name=tc.name,
                    description=tc.description,
                    category=rel_cat,
                    stress_vector=_infer_stress_vector(tc.name, rel_cat),
                    sample_input=tc.sample_input,
                    expected_handling=expected_handling,
                    status="NOT_RUN",
                )
            )

        # Add targeted Robustness scenario: Unexpected Object Structure
        counters["robustness"] += 1
        unexpected_payload: Dict[str, Any]
        if input_type == "json":
            unexpected_payload = {
                input_field: {
                    "__unexpected_schema__": True,
                    "nested_array": [1, "mixed", None],
                }
            }
        else:
            unexpected_payload = {
                input_field: {"unexpected_object": "dict_passed_instead_of_scalar"}
            }

        grouped["robustness"].append(
            ReliabilityScenario(
                scenario_id=f"rel-rob-{counters['robustness']}",
                name="Unexpected Object Structure",
                description=(
                    f"Verifies safe rejection when an unexpected object structure is supplied "
                    f"for '{input_type}' Input node."
                ),
                category="robustness",
                stress_vector="UNEXPECTED_OBJECT_STRUCTURE",
                sample_input=unexpected_payload,
                expected_handling="SAFE_REJECTION",
                status="NOT_RUN",
            )
        )

        # Add targeted Edge scenario: Bounded Large Payload / Inert Special Strings
        counters["edge"] += 1
        if input_type == "json":
            bounded_payload: Dict[str, Any] = {
                input_field: {
                    "items": [{"index": i, "label": f"item-{i}"} for i in range(50)],
                    "inert_text": "SELECT * FROM items; <script>inert</script>",
                }
            }
            edge_desc = "Tests bounded 50-item JSON array with inert special strings."
        elif input_type == "file_url":
            bounded_payload = {
                input_field: (
                    "https://example.com/documents/"
                    + ("nested/" * 15)
                    + "bounded_report_2026.pdf?ref=reliability_lab"
                )
            }
            edge_desc = "Tests long but bounded nested document URL path."
        else:
            bounded_payload = {
                input_field: (
                    "Inert security-like text: <script>inert</script> ' OR '1'='1' -- "
                    + ("bounded_segment " * 100)
                ).strip()
            }
            edge_desc = "Tests bounded payload containing inert HTML/SQL-like characters."

        grouped["edge"].append(
            ReliabilityScenario(
                scenario_id=f"rel-edge-{counters['edge']}",
                name="Bounded Stress Payload with Inert Strings",
                description=edge_desc,
                category="edge",
                stress_vector="BOUNDED_LARGE_PAYLOAD",
                sample_input=bounded_payload,
                expected_handling="GRACEFUL_HANDLING",
                status="NOT_RUN",
            )
        )

        return grouped, input_type, input_required
