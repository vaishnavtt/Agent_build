from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.testing import TestCaseSchema, TestCategory
from app.services.validation.node_catalog import get_node_definition
from app.services.validation.workflow_validator import (
    _extract_node_config,
    _extract_node_label,
    _extract_node_type,
)


def _normalize_input_type(raw_input_type: Any) -> str:
    """Normalize Input node inputType to canonical values: text, json, or file_url."""
    if not isinstance(raw_input_type, str) or not raw_input_type.strip():
        return "text"
    val = raw_input_type.strip().lower()
    if val in ("text", "json", "file_url"):
        return val
    if "file" in val or "pdf" in val or "doc" in val or "url" in val:
        return "file_url"
    if "json" in val or "object" in val or "struct" in val:
        return "json"
    return "text"


class TestCaseGenerator:
    """Generates deterministic Normal, Invalid, and Edge test cases for validated workflows."""

    def generate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        requirement: Optional[str] = None,
        workflow_name: str = "Workflow",
        categories: Optional[List[TestCategory]] = None,
    ) -> Tuple[List[TestCaseSchema], str, str, bool]:
        """Generate test cases from workflow requirement, Input node config, and downstream nodes.

        Returns:
            (test_cases, requirement_used, input_type_detected, input_required)
        """
        selected_categories: Set[TestCategory] = (
            set(categories) if categories else {"normal", "invalid", "edge"}
        )

        input_node = self._find_input_node(nodes)
        input_config = _extract_node_config(input_node) if input_node else {}
        input_type = _normalize_input_type(input_config.get("inputType"))
        input_required = bool(input_config.get("required", True))
        input_field = str(input_config.get("inputField") or "input")

        downstream_types = self._collect_downstream_types(nodes)
        condition_nodes = [n for n in nodes if _extract_node_type(n) == "Condition"]
        doc_reader_nodes = [n for n in nodes if _extract_node_type(n) == "Document Reader"]
        output_nodes = [n for n in nodes if _extract_node_type(n) == "Output"]

        requirement_used = self._resolve_requirement(
            requirement=requirement,
            workflow_name=workflow_name,
            input_type=input_type,
            downstream_types=downstream_types,
        )

        output_format = "markdown"
        if output_nodes:
            out_cfg = _extract_node_config(output_nodes[0])
            output_format = str(out_cfg.get("outputFormat") or out_cfg.get("format") or "markdown")

        test_cases: List[TestCaseSchema] = []

        if "normal" in selected_categories:
            test_cases.extend(
                self._generate_normal_cases(
                    input_type=input_type,
                    input_required=input_required,
                    input_field=input_field,
                    requirement_used=requirement_used,
                    downstream_types=downstream_types,
                    doc_reader_nodes=doc_reader_nodes,
                    condition_nodes=condition_nodes,
                    output_format=output_format,
                )
            )

        if "invalid" in selected_categories:
            test_cases.extend(
                self._generate_invalid_cases(
                    input_type=input_type,
                    input_required=input_required,
                    input_field=input_field,
                )
            )

        if "edge" in selected_categories:
            test_cases.extend(
                self._generate_edge_cases(
                    input_type=input_type,
                    input_required=input_required,
                    input_field=input_field,
                    condition_nodes=condition_nodes,
                    doc_reader_nodes=doc_reader_nodes,
                )
            )

        return test_cases, requirement_used, input_type, input_required

    def _find_input_node(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for node in nodes:
            if _extract_node_type(node) == "Input":
                return node
        return None

    def _collect_downstream_types(self, nodes: List[Dict[str, Any]]) -> List[str]:
        seen: List[str] = []
        for node in nodes:
            ntype = _extract_node_type(node)
            if ntype and ntype not in seen:
                seen.append(ntype)
        return seen

    def _resolve_requirement(
        self,
        requirement: Optional[str],
        workflow_name: str,
        input_type: str,
        downstream_types: List[str],
    ) -> str:
        if isinstance(requirement, str) and requirement.strip():
            return requirement.strip()
        pipeline = " -> ".join(downstream_types) if downstream_types else "Input -> Output"
        return (
            f"Inferred requirement for '{workflow_name}': Accept '{input_type}' input "
            f"and process through pipeline ({pipeline})."
        )

    def _generate_normal_cases(
        self,
        input_type: str,
        input_required: bool,
        input_field: str,
        requirement_used: str,
        downstream_types: List[str],
        doc_reader_nodes: List[Dict[str, Any]],
        condition_nodes: List[Dict[str, Any]],
        output_format: str,
    ) -> List[TestCaseSchema]:
        cases: List[TestCaseSchema] = []
        has_approval = "Human Approval" in downstream_types
        approval_note = " Pauses at Human Approval gate for sign-off." if has_approval else ""

        if input_type == "text":
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-normal-1",
                    name="Valid Standard Text Input",
                    description=(
                        f"Verifies normal end-to-end execution with valid text matching requirement: "
                        f"{requirement_used[:120]}"
                    ),
                    category="normal",
                    sample_input={
                        input_field: (
                            f"Sample request aligned with workflow requirement: {requirement_used[:160]}"
                        )
                    },
                    expected_behavior=(
                        f"Workflow processes text input successfully through {len(downstream_types)} "
                        f"component stage(s) and produces '{output_format}' output.{approval_note}"
                    ),
                    status="NOT_RUN",
                )
            )
        elif input_type == "json":
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-normal-1",
                    name="Valid Structured JSON Input",
                    description="Verifies normal execution with a well-formed JSON object payload.",
                    category="normal",
                    sample_input={
                        input_field: {
                            "query": requirement_used[:120],
                            "priority": "normal",
                            "metadata": {"source": "automated_test"},
                        }
                    },
                    expected_behavior=(
                        f"Workflow parses structured JSON input and returns valid '{output_format}' output."
                        f"{approval_note}"
                    ),
                    status="NOT_RUN",
                )
            )
        elif input_type == "file_url":
            doc_def = get_node_definition("Document Reader") or {}
            supported_exts = doc_def.get("defaultConfig", {}).get(
                "supportedExtensions", [".pdf", ".txt", ".md", ".docx"]
            )
            ext = supported_exts[0] if supported_exts else ".pdf"
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-normal-1",
                    name=f"Valid Document URL Input ({ext})",
                    description=f"Verifies normal execution with a valid {ext} document reference.",
                    category="normal",
                    sample_input={
                        input_field: f"https://example.com/documents/sample_input{ext}",
                        "mime_type": "application/pdf" if ext == ".pdf" else "text/plain",
                    },
                    expected_behavior=(
                        f"Workflow ingests the {ext} document, processes content, and delivers "
                        f"'{output_format}' output.{approval_note}"
                    ),
                    status="NOT_RUN",
                )
            )

        if not input_required:
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-normal-2",
                    name="Optional Input Omitted",
                    description="Verifies workflow handles omitted input gracefully when required=False.",
                    category="normal",
                    sample_input={},
                    expected_behavior=(
                        "Workflow proceeds using default Input configuration without raising a missing-input error."
                    ),
                    status="NOT_RUN",
                )
            )

        if condition_nodes:
            cond_cfg = _extract_node_config(condition_nodes[0])
            cond_label = _extract_node_label(condition_nodes[0])
            left_op = cond_cfg.get("leftOperand") or cond_cfg.get("fieldToCheck") or "status"
            right_op = cond_cfg.get("rightOperand") or cond_cfg.get("targetValue") or "success"
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-normal-{len(cases) + 1}",
                    name=f"Condition True-Branch Match ({cond_label})",
                    description=f"Verifies normal routing when '{left_op}' satisfies target '{right_op}'.",
                    category="normal",
                    sample_input={
                        input_field: (
                            {str(left_op): right_op}
                            if input_type == "json"
                            else f"Input expected to satisfy {left_op}={right_op}"
                        )
                    },
                    expected_behavior=f"Condition node '{cond_label}' evaluates to true branch and completes.",
                    status="NOT_RUN",
                )
            )

        return cases

    def _generate_invalid_cases(
        self,
        input_type: str,
        input_required: bool,
        input_field: str,
    ) -> List[TestCaseSchema]:
        cases: List[TestCaseSchema] = []

        if input_required:
            empty_val: Any = {} if input_type == "json" else ""
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-invalid-{len(cases) + 1}",
                    name="Empty Required Input",
                    description="Verifies that an empty input is rejected when Input node has required=True.",
                    category="invalid",
                    sample_input={input_field: empty_val},
                    expected_behavior="Workflow rejects empty required input with a clear validation error.",
                    status="NOT_RUN",
                )
            )

        cases.append(
            TestCaseSchema(
                test_case_id=f"tc-invalid-{len(cases) + 1}",
                name="Null Input Value",
                description="Verifies safe error handling when input value is null/None.",
                category="invalid",
                sample_input={input_field: None},
                expected_behavior="Workflow rejects or safely handles null input without unhandled exceptions.",
                status="NOT_RUN",
            )
        )

        if input_type == "text":
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-invalid-{len(cases) + 1}",
                    name="Incorrect Data Type (Numeric Instead of Text)",
                    description="Verifies type validation when a number is supplied instead of text.",
                    category="invalid",
                    sample_input={input_field: 987654321},
                    expected_behavior="Workflow rejects non-string input or reports an input type mismatch error.",
                    status="NOT_RUN",
                )
            )
        elif input_type == "json":
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-invalid-{len(cases) + 1}",
                    name="Malformed JSON String Instead of Object",
                    description="Verifies error handling when malformed JSON text is passed instead of a JSON object.",
                    category="invalid",
                    sample_input={input_field: "{invalid_json: [1, 2,"},
                    expected_behavior="Workflow rejects malformed JSON payload with a structured parse/validation error.",
                    status="NOT_RUN",
                )
            )
        elif input_type == "file_url":
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-invalid-{len(cases) + 1}",
                    name="Invalid / Non-URL File Reference",
                    description="Verifies rejection of a malformed file URL or unsupported protocol.",
                    category="invalid",
                    sample_input={input_field: "not_a_valid_url_or_path"},
                    expected_behavior="Workflow rejects invalid file URL and reports an ingestion error.",
                    status="NOT_RUN",
                )
            )

        return cases

    def _generate_edge_cases(
        self,
        input_type: str,
        input_required: bool,
        input_field: str,
        condition_nodes: List[Dict[str, Any]],
        doc_reader_nodes: List[Dict[str, Any]],
    ) -> List[TestCaseSchema]:
        cases: List[TestCaseSchema] = []

        if input_type == "text":
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-edge-1",
                    name="Very Short Single-Character Input",
                    description="Tests minimum non-empty text boundary (1 character).",
                    category="edge",
                    sample_input={input_field: "a"},
                    expected_behavior="Workflow handles minimal text gracefully without crashing.",
                    status="NOT_RUN",
                )
            )
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-edge-2",
                    name="Very Long Text Payload",
                    description="Tests handling of a large 5,000-character text payload.",
                    category="edge",
                    sample_input={input_field: "Long workflow input segment. " * 175},
                    expected_behavior="Workflow processes or chunks large text within timeout without truncation errors.",
                    status="NOT_RUN",
                )
            )
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-edge-3",
                    name="Special & Unicode Characters",
                    description="Tests resilience against punctuation, symbols, and multi-byte Unicode/emoji text.",
                    category="edge",
                    sample_input={
                        input_field: "Résumé — 日本語テスト 🚀 <script> & symbols: !@#$%^&*()"
                    },
                    expected_behavior="Workflow preserves UTF-8 encoding and escapes special characters safely.",
                    status="NOT_RUN",
                )
            )
        elif input_type == "json":
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-edge-1",
                    name="Deeply Nested JSON with Unicode Values",
                    description="Tests nested JSON structure with special characters and boundary numeric values.",
                    category="edge",
                    sample_input={
                        input_field: {
                            "level1": {"level2": {"score": 0, "max_val": 999999999}},
                            "unicode_note": "Résumé — 日本語テスト 🚀",
                        }
                    },
                    expected_behavior="Workflow traverses nested JSON keys and preserves Unicode values safely.",
                    status="NOT_RUN",
                )
            )
            if not input_required:
                cases.append(
                    TestCaseSchema(
                        test_case_id="tc-edge-2",
                        name="Empty JSON Object (Optional Input)",
                        description="Tests boundary empty JSON object `{}` when input is optional.",
                        category="edge",
                        sample_input={input_field: {}},
                        expected_behavior="Workflow handles empty JSON object using defaults without failing.",
                        status="NOT_RUN",
                    )
                )
        elif input_type == "file_url":
            cases.append(
                TestCaseSchema(
                    test_case_id="tc-edge-1",
                    name="URL with Query Params & Encoded Characters",
                    description="Tests document URL containing query strings and percent-encoded spaces.",
                    category="edge",
                    sample_input={
                        input_field: "https://example.com/files/sample%20report%20v2.pdf?download=1&token=abc"
                    },
                    expected_behavior="Workflow parses encoded URL query parameters and locates the document.",
                    status="NOT_RUN",
                )
            )
            if doc_reader_nodes:
                cases.append(
                    TestCaseSchema(
                        test_case_id="tc-edge-2",
                        name="Large Document Boundary (Chunking Stress)",
                        description="Tests Document Reader chunking behavior on a large multi-page document URL.",
                        category="edge",
                        sample_input={
                            input_field: "https://example.com/files/large_100page_document.pdf"
                        },
                        expected_behavior="Document Reader chunks content according to chunkSize and chunkOverlap.",
                        status="NOT_RUN",
                    )
                )

        if condition_nodes:
            cond_cfg = _extract_node_config(condition_nodes[0])
            cond_label = _extract_node_label(condition_nodes[0])
            right_op = cond_cfg.get("rightOperand") or cond_cfg.get("targetValue") or "0"
            cases.append(
                TestCaseSchema(
                    test_case_id=f"tc-edge-{len(cases) + 1}",
                    name=f"Condition Boundary Value ({cond_label})",
                    description=f"Tests exact boundary threshold '{right_op}' on Condition node '{cond_label}'.",
                    category="edge",
                    sample_input={
                        input_field: (
                            {"boundary_value": right_op}
                            if input_type == "json"
                            else f"Boundary test value: {right_op}"
                        )
                    },
                    expected_behavior=f"Condition node '{cond_label}' deterministically routes boundary value.",
                    status="NOT_RUN",
                )
            )

        return cases
