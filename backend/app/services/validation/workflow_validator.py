from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.validation import (
    FullWorkflowValidationResponse,
    ScoreBreakdown,
    ValidationDetails,
    ValidationIssueDetail,
)
from app.services.validation.node_catalog import (
    get_node_definition,
    get_supported_node_types,
)


def _is_empty_value(value: Any) -> bool:
    """Return True if a configuration value is None, blank string, or empty collection."""
    if value is None:
        return True
    if isinstance(value, str):
        return len(value.strip()) == 0
    if isinstance(value, (list, dict, set, tuple)):
        return len(value) == 0
    return False


def _extract_node_type(node: Dict[str, Any]) -> Optional[str]:
    """Extract canonical component type from either React Flow node.data or top-level node.type."""
    data = node.get("data")
    if isinstance(data, dict):
        comp_type = data.get("componentType")
        if isinstance(comp_type, str) and comp_type.strip():
            return comp_type.strip()

    top_type = node.get("type")
    if isinstance(top_type, str) and top_type.strip() and top_type.strip() != "customWorkflow":
        return top_type.strip()

    return None


def _extract_node_config(node: Dict[str, Any]) -> Dict[str, Any]:
    """Merge node-level config and data.config, preferring explicit top-level keys."""
    merged: Dict[str, Any] = {}
    data = node.get("data")
    if isinstance(data, dict) and isinstance(data.get("config"), dict):
        merged.update(data["config"])
    if isinstance(node.get("config"), dict):
        merged.update(node["config"])
    return merged


def _extract_node_label(node: Dict[str, Any]) -> str:
    """Return a human-readable label for a node."""
    data = node.get("data")
    if isinstance(data, dict) and data.get("label"):
        return str(data["label"])
    if node.get("name"):
        return str(node["name"])
    return str(node.get("id", "unknown"))


class WorkflowValidator:
    """Comprehensive, deterministic validator for AgentForge AI workflow graphs."""

    SCORE_FORMULA = (
        "Deterministic score (0-100) = Structural (30) + Connection (30) + Configuration (40). "
        "Empty workflows score 0. Structural deducts 15 for missing Input, 15 for missing Output, "
        "10 for no path to Output, 10 per unsupported node (max 30), and 5 per disconnected/unreachable "
        "node (max 20). Connection deducts 10 per invalid edge (max 30) and 5 per missing required I/O "
        "(max 20). Configuration deducts 10 per missing/invalid required field (max 40) and 5 per warning."
    )

    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        workflow_id: Optional[str] = None,
    ) -> FullWorkflowValidationResponse:
        errors: List[ValidationIssueDetail] = []
        warnings: List[ValidationIssueDetail] = []

        total_nodes = len(nodes)
        total_connections = len(edges)

        if total_nodes == 0:
            errors.append(
                ValidationIssueDetail(
                    issue_type="EMPTY_WORKFLOW",
                    severity="error",
                    message="Workflow contains no nodes. Add at least an Input and an Output node.",
                )
            )
            details = ValidationDetails(
                score_breakdown=ScoreBreakdown(
                    structural_score=0,
                    connection_score=0,
                    configuration_score=0,
                    formula_description=self.SCORE_FORMULA,
                )
            )
            return FullWorkflowValidationResponse(
                workflow_id=workflow_id,
                is_valid=False,
                readiness_score=0,
                total_nodes=0,
                total_connections=total_connections,
                errors=errors,
                warnings=warnings,
                validation_details=details,
            )

        node_map: Dict[str, Dict[str, Any]] = {}
        node_types: Dict[str, Optional[str]] = {}
        unsupported_node_ids: List[str] = []
        supported_types = set(get_supported_node_types())

        # 1. Index nodes & detect unsupported node types
        for idx, node in enumerate(nodes):
            node_id = node.get("id")
            if not node_id or not isinstance(node_id, str):
                synthetic_id = f"node-index-{idx}"
                errors.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_NODE_ID",
                        severity="error",
                        message=f"Node at index {idx} is missing a valid string 'id'.",
                        affected_node_id=synthetic_id,
                    )
                )
                continue

            if node_id in node_map:
                errors.append(
                    ValidationIssueDetail(
                        issue_type="DUPLICATE_NODE_ID",
                        severity="error",
                        message=f"Duplicate node ID '{node_id}' found in workflow.",
                        affected_node_id=node_id,
                    )
                )
                continue

            node_map[node_id] = node
            comp_type = _extract_node_type(node)
            node_types[node_id] = comp_type

            if not comp_type or comp_type not in supported_types:
                unsupported_node_ids.append(node_id)
                errors.append(
                    ValidationIssueDetail(
                        issue_type="UNSUPPORTED_NODE_TYPE",
                        severity="error",
                        message=(
                            f"Node '{_extract_node_label(node)}' has unsupported type '{comp_type}'. "
                            f"Supported types: {', '.join(sorted(supported_types))}."
                        ),
                        affected_node_id=node_id,
                    )
                )

        # 2. Validate node configurations against shared/node_definitions.json
        config_error_count = 0
        config_warning_count = 0
        for node_id, node in node_map.items():
            comp_type = node_types.get(node_id)
            node_def = get_node_definition(comp_type)
            if not node_def:
                continue
            cfg_errs, cfg_warns = self._validate_node_configuration(node_id, node, comp_type, node_def)
            errors.extend(cfg_errs)
            warnings.extend(cfg_warns)
            config_error_count += len(cfg_errs)
            config_warning_count += len(cfg_warns)

        # 3. Validate connections (edges)
        valid_edges: List[Dict[str, Any]] = []
        invalid_connection_ids: List[str] = []
        incoming_valid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        outgoing_valid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for idx, edge in enumerate(edges):
            edge_id = str(edge.get("id") or f"edge-index-{idx}")
            edge_errs = self._validate_edge(edge_id, edge, node_map, node_types)
            if edge_errs:
                errors.extend(edge_errs)
                invalid_connection_ids.append(edge_id)
            else:
                valid_edges.append(edge)
                incoming_valid[edge["target"]].append(edge)
                outgoing_valid[edge["source"]].append(edge)

        # 4. Structural & Connectivity analysis (using only valid edges)
        input_node_ids = [nid for nid, t in node_types.items() if t == "Input"]
        output_node_ids = [nid for nid, t in node_types.items() if t == "Output"]
        has_input_node = len(input_node_ids) > 0
        has_output_node = len(output_node_ids) > 0

        if not has_input_node:
            errors.append(
                ValidationIssueDetail(
                    issue_type="MISSING_INPUT_NODE",
                    severity="error",
                    message="Workflow must contain at least one 'Input' node as an entry point.",
                )
            )

        if not has_output_node:
            errors.append(
                ValidationIssueDetail(
                    issue_type="MISSING_OUTPUT_NODE",
                    severity="error",
                    message="Workflow must contain at least one 'Output' node as a terminal step.",
                )
            )

        # Disconnected nodes (no valid incoming or outgoing edges when > 1 node)
        disconnected_node_ids: List[str] = []
        if len(node_map) > 1:
            for node_id in node_map:
                if not incoming_valid[node_id] and not outgoing_valid[node_id]:
                    disconnected_node_ids.append(node_id)
                    errors.append(
                        ValidationIssueDetail(
                            issue_type="DISCONNECTED_NODE",
                            severity="error",
                            message=f"Node '{_extract_node_label(node_map[node_id])}' is disconnected from the workflow.",
                            affected_node_id=node_id,
                        )
                    )

        # Reachability from Input nodes
        reachable_from_input: Set[str] = set()
        if has_input_node:
            queue = deque(input_node_ids)
            reachable_from_input.update(input_node_ids)
            while queue:
                curr = queue.popleft()
                for edge in outgoing_valid.get(curr, []):
                    tgt = edge["target"]
                    if tgt not in reachable_from_input:
                        reachable_from_input.add(tgt)
                        queue.append(tgt)

        unreachable_node_ids: List[str] = []
        if has_input_node:
            for node_id in node_map:
                if node_id not in reachable_from_input and node_id not in disconnected_node_ids:
                    unreachable_node_ids.append(node_id)
                    errors.append(
                        ValidationIssueDetail(
                            issue_type="UNREACHABLE_NODE",
                            severity="error",
                            message=(
                                f"Node '{_extract_node_label(node_map[node_id])}' cannot be reached "
                                "from any Input node."
                            ),
                            affected_node_id=node_id,
                        )
                    )

        has_path_to_output = bool(
            has_input_node and has_output_node and any(oid in reachable_from_input for oid in output_node_ids)
        )
        if has_input_node and has_output_node and not has_path_to_output:
            errors.append(
                ValidationIssueDetail(
                    issue_type="NO_PATH_TO_OUTPUT",
                    severity="error",
                    message="No valid execution path exists from any Input node to an Output node.",
                    affected_node_id=output_node_ids[0],
                )
            )

        # 5. Required Input and Output Validation per node
        io_issue_count = 0
        for node_id, node in node_map.items():
            comp_type = node_types.get(node_id)
            node_def = get_node_definition(comp_type)
            if not node_def:
                continue
            io_errs = self._validate_node_io(
                node_id=node_id,
                node=node,
                comp_type=comp_type,
                node_def=node_def,
                incoming_edges=incoming_valid[node_id],
                outgoing_edges=outgoing_valid[node_id],
            )
            errors.extend(io_errs)
            io_issue_count += len(io_errs)

        # 6. Deterministic Readiness Score
        structural_score = 30
        if not has_input_node:
            structural_score -= 15
        if not has_output_node:
            structural_score -= 15
        if has_input_node and has_output_node and not has_path_to_output:
            structural_score -= 10
        structural_score -= min(len(unsupported_node_ids) * 10, 30)
        structural_score -= min((len(disconnected_node_ids) + len(unreachable_node_ids)) * 5, 20)
        structural_score = max(0, structural_score)

        connection_score = 30
        connection_score -= min(len(invalid_connection_ids) * 10, 30)
        connection_score -= min(io_issue_count * 5, 20)
        connection_score = max(0, connection_score)

        configuration_score = 40
        configuration_score -= min(config_error_count * 10, 40)
        configuration_score -= min(config_warning_count * 5, 20)
        configuration_score = max(0, configuration_score)

        readiness_score = max(0, min(100, structural_score + connection_score + configuration_score))
        is_valid = len(errors) == 0

        details = ValidationDetails(
            disconnected_node_ids=disconnected_node_ids,
            unreachable_node_ids=unreachable_node_ids,
            unsupported_node_ids=unsupported_node_ids,
            invalid_connection_ids=invalid_connection_ids,
            has_input_node=has_input_node,
            has_output_node=has_output_node,
            has_path_to_output=has_path_to_output,
            score_breakdown=ScoreBreakdown(
                structural_score=structural_score,
                connection_score=connection_score,
                configuration_score=configuration_score,
                formula_description=self.SCORE_FORMULA,
            ),
        )

        return FullWorkflowValidationResponse(
            workflow_id=workflow_id,
            is_valid=is_valid,
            readiness_score=readiness_score,
            total_nodes=total_nodes,
            total_connections=total_connections,
            errors=errors,
            warnings=warnings,
            validation_details=details,
        )

    def _validate_node_configuration(
        self,
        node_id: str,
        node: Dict[str, Any],
        comp_type: str,
        node_def: Dict[str, Any],
    ) -> Tuple[List[ValidationIssueDetail], List[ValidationIssueDetail]]:
        errs: List[ValidationIssueDetail] = []
        warns: List[ValidationIssueDetail] = []
        config = _extract_node_config(node)
        label = _extract_node_label(node)

        # Validate configFields options / bounds defined in shared/node_definitions.json
        for field_spec in node_def.get("configFields", []):
            fname = field_spec.get("name")
            if not fname or fname not in config:
                continue
            val = config[fname]
            options = field_spec.get("options")
            if options and not _is_empty_value(val):
                # Allow friendly UI labels if they start with or match option, otherwise strict check
                if val not in options and not any(str(val).lower().startswith(opt.lower()) for opt in options):
                    warns.append(
                        ValidationIssueDetail(
                            issue_type="UNRECOGNIZED_CONFIG_OPTION",
                            severity="warning",
                            message=(
                                f"Node '{label}' ({comp_type}) has value '{val}' for '{fname}'. "
                                f"Expected one of: {', '.join(options)}."
                            ),
                            affected_node_id=node_id,
                        )
                    )

        # Type-specific required configuration validation
        if comp_type == "Input":
            if _is_empty_value(config.get("inputType")):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Input node '{label}' is missing required configuration field 'inputType'.",
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "LLM":
            if _is_empty_value(config.get("model")):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"LLM node '{label}' is missing required configuration field 'model'.",
                        affected_node_id=node_id,
                    )
                )
            prompt_val = config.get("systemPrompt")
            if _is_empty_value(prompt_val):
                prompt_val = config.get("instructions")
            if _is_empty_value(prompt_val):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_LLM_PROMPT",
                        severity="error",
                        message=f"LLM node '{label}' is missing required prompt ('systemPrompt' or 'instructions').",
                        affected_node_id=node_id,
                    )
                )
            temp = config.get("temperature")
            if temp is not None and isinstance(temp, (int, float)) and not (0.0 <= float(temp) <= 1.0):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_CONFIGURATION",
                        severity="error",
                        message=f"LLM node '{label}' has invalid temperature {temp}; must be between 0.0 and 1.0.",
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "Document Reader":
            chunk_size = config.get("chunkSize")
            chunk_overlap = config.get("chunkOverlap")
            has_extraction_mode = not _is_empty_value(config.get("extractionMode"))
            if chunk_size is None and not has_extraction_mode:
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Document Reader node '{label}' is missing 'chunkSize' configuration.",
                        affected_node_id=node_id,
                    )
                )
            elif chunk_size is not None and (not isinstance(chunk_size, (int, float)) or chunk_size <= 0):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_CONFIGURATION",
                        severity="error",
                        message=f"Document Reader node '{label}' must have a positive 'chunkSize'.",
                        affected_node_id=node_id,
                    )
                )
            if (
                chunk_overlap is not None
                and chunk_size is not None
                and isinstance(chunk_overlap, (int, float))
                and isinstance(chunk_size, (int, float))
                and (chunk_overlap < 0 or chunk_overlap >= chunk_size)
            ):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_CONFIGURATION",
                        severity="error",
                        message=(
                            f"Document Reader node '{label}' has invalid 'chunkOverlap' ({chunk_overlap}); "
                            "must be >= 0 and less than 'chunkSize'."
                        ),
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "Tool":
            tool_name = config.get("toolName")
            if _is_empty_value(tool_name):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Tool node '{label}' is missing required configuration field 'toolName'.",
                        affected_node_id=node_id,
                    )
                )
            elif tool_name == "http_request" and _is_empty_value(config.get("endpoint")):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Tool node '{label}' uses 'http_request' but is missing 'endpoint'.",
                        affected_node_id=node_id,
                    )
                )
            timeout = config.get("timeoutSeconds")
            if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_CONFIGURATION",
                        severity="error",
                        message=f"Tool node '{label}' must have a positive 'timeoutSeconds'.",
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "Condition":
            operator = config.get("operator") or config.get("rule")
            left_op = config.get("leftOperand") or config.get("fieldToCheck")
            right_op = config.get("rightOperand")
            if _is_empty_value(right_op):
                right_op = config.get("targetValue")

            if _is_empty_value(operator):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Condition node '{label}' is missing required 'operator'.",
                        affected_node_id=node_id,
                    )
                )
            if _is_empty_value(left_op):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Condition node '{label}' is missing required 'leftOperand'.",
                        affected_node_id=node_id,
                    )
                )
            if _is_empty_value(right_op):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Condition node '{label}' is missing required 'rightOperand'.",
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "Human Approval":
            prompt_msg = config.get("promptMessage") or config.get("approvalPrompt")
            if _is_empty_value(prompt_msg):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Human Approval node '{label}' is missing required 'promptMessage'.",
                        affected_node_id=node_id,
                    )
                )
            timeout_min = config.get("timeoutMinutes")
            if timeout_min is not None and (not isinstance(timeout_min, (int, float)) or timeout_min <= 0):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_CONFIGURATION",
                        severity="error",
                        message=f"Human Approval node '{label}' must have positive 'timeoutMinutes'.",
                        affected_node_id=node_id,
                    )
                )

        elif comp_type == "Output":
            out_fmt = config.get("outputFormat") or config.get("format")
            if _is_empty_value(out_fmt):
                errs.append(
                    ValidationIssueDetail(
                        issue_type="MISSING_CONFIGURATION",
                        severity="error",
                        message=f"Output node '{label}' is missing required 'outputFormat'.",
                        affected_node_id=node_id,
                    )
                )

        return errs, warns

    def _validate_edge(
        self,
        edge_id: str,
        edge: Dict[str, Any],
        node_map: Dict[str, Dict[str, Any]],
        node_types: Dict[str, Optional[str]],
    ) -> List[ValidationIssueDetail]:
        errs: List[ValidationIssueDetail] = []
        source_id = edge.get("source")
        target_id = edge.get("target")

        source_exists = isinstance(source_id, str) and source_id in node_map
        target_exists = isinstance(target_id, str) and target_id in node_map

        if not source_exists:
            errs.append(
                ValidationIssueDetail(
                    issue_type="INVALID_SOURCE_NODE",
                    severity="error",
                    message=f"Connection '{edge_id}' references non-existent source node '{source_id}'.",
                    affected_connection_id=edge_id,
                )
            )

        if not target_exists:
            errs.append(
                ValidationIssueDetail(
                    issue_type="INVALID_TARGET_NODE",
                    severity="error",
                    message=f"Connection '{edge_id}' references non-existent target node '{target_id}'.",
                    affected_connection_id=edge_id,
                )
            )

        if not source_exists or not target_exists:
            return errs

        if source_id == target_id:
            errs.append(
                ValidationIssueDetail(
                    issue_type="SELF_LOOP",
                    severity="error",
                    message=f"Connection '{edge_id}' connects node '{source_id}' to itself.",
                    affected_node_id=source_id,
                    affected_connection_id=edge_id,
                )
            )
            return errs

        source_type = node_types.get(source_id)
        target_type = node_types.get(target_id)
        source_def = get_node_definition(source_type)
        target_def = get_node_definition(target_type)

        # Output node cannot have outgoing connections; Input node cannot have incoming connections
        if source_type == "Output":
            errs.append(
                ValidationIssueDetail(
                    issue_type="INVALID_CONNECTION",
                    severity="error",
                    message=f"Connection '{edge_id}' cannot originate from terminal Output node '{source_id}'.",
                    affected_node_id=source_id,
                    affected_connection_id=edge_id,
                )
            )

        if target_type == "Input":
            errs.append(
                ValidationIssueDetail(
                    issue_type="INVALID_CONNECTION",
                    severity="error",
                    message=f"Connection '{edge_id}' cannot target entry Input node '{target_id}'.",
                    affected_node_id=target_id,
                    affected_connection_id=edge_id,
                )
            )

        # Validate sourceHandle if specified
        source_handle = edge.get("sourceHandle")
        if source_handle is not None and source_def:
            allowed_outputs = set(node_map[source_id].get("outputHandles") or []) | set(
                source_def.get("defaultOutputs", [])
            )
            if source_handle not in allowed_outputs:
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_SOURCE_HANDLE",
                        severity="error",
                        message=(
                            f"Connection '{edge_id}' uses invalid sourceHandle '{source_handle}' "
                            f"on {source_type} node '{source_id}'. Allowed: {sorted(allowed_outputs)}."
                        ),
                        affected_node_id=source_id,
                        affected_connection_id=edge_id,
                    )
                )

        # Validate targetHandle if specified
        target_handle = edge.get("targetHandle")
        if target_handle is not None and target_def:
            allowed_inputs = set(node_map[target_id].get("inputHandles") or []) | set(
                target_def.get("defaultInputs", [])
            )
            if target_handle not in allowed_inputs:
                errs.append(
                    ValidationIssueDetail(
                        issue_type="INVALID_TARGET_HANDLE",
                        severity="error",
                        message=(
                            f"Connection '{edge_id}' uses invalid targetHandle '{target_handle}' "
                            f"on {target_type} node '{target_id}'. Allowed: {sorted(allowed_inputs)}."
                        ),
                        affected_node_id=target_id,
                        affected_connection_id=edge_id,
                    )
                )

        return errs

    def _validate_node_io(
        self,
        node_id: str,
        node: Dict[str, Any],
        comp_type: str,
        node_def: Dict[str, Any],
        incoming_edges: List[Dict[str, Any]],
        outgoing_edges: List[Dict[str, Any]],
    ) -> List[ValidationIssueDetail]:
        errs: List[ValidationIssueDetail] = []
        label = _extract_node_label(node)
        expected_inputs = node_def.get("defaultInputs", [])
        expected_outputs = node_def.get("defaultOutputs", [])

        # Check required input availability for non-Input nodes
        if expected_inputs and len(incoming_edges) == 0:
            errs.append(
                ValidationIssueDetail(
                    issue_type="MISSING_REQUIRED_INPUT",
                    severity="error",
                    message=(
                        f"{comp_type} node '{label}' requires an incoming connection "
                        f"for input(s) {expected_inputs}, but has none."
                    ),
                    affected_node_id=node_id,
                )
            )

        # Check required output availability for non-Output nodes
        if expected_outputs and len(outgoing_edges) == 0:
            errs.append(
                ValidationIssueDetail(
                    issue_type="MISSING_REQUIRED_OUTPUT",
                    severity="error",
                    message=(
                        f"{comp_type} node '{label}' must route its output(s) {expected_outputs} "
                        "to a downstream node, but has no outgoing connections."
                    ),
                    affected_node_id=node_id,
                )
            )

        return errs
