"""
AgentForge AI - Shared Workflow Fixtures (Member 3 & Member 4 Contract)
Canonical workflow fixtures verifying end-to-end compatibility between
Member 3 (Workflow Generation & Component Management) and
Member 4 (Execution Engine).

Covers:
1. Simple execution (Input -> Output)
2. Conditional branching (Input -> Condition -> [true: LLM, false: Tool] -> Output)
3. Branch joins (Input -> Condition -> [Tool A, Tool B] -> Join at LLM -> Output)
4. Human approval gate (Input -> Document Reader -> Human Approval -> Output)
"""

from typing import Dict, Any
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowNodeSchema,
    WorkflowEdgeSchema,
    NodePosition,
    WorkflowConfigurationSchema,
)


def create_simple_execution_workflow() -> WorkflowCreate:
    """Fixture 1: Simple linear execution pipeline (Input -> Output)."""
    nodes = [
        WorkflowNodeSchema(
            id="node_input_1",
            type="Input",
            name="User Query Ingestion",
            position=NodePosition(x=100.0, y=150.0),
            config={"inputType": "text", "required": True, "defaultValue": "Hello AgentForge"},
            inputHandles=[],
            outputHandles=["output"],
        ),
        WorkflowNodeSchema(
            id="node_output_1",
            type="Output",
            name="Workflow Result",
            position=NodePosition(x=400.0, y=150.0),
            config={"outputFormat": "json", "includeExecutionMetrics": True},
            inputHandles=["input"],
            outputHandles=[],
        ),
    ]
    edges = [
        WorkflowEdgeSchema(
            id="edge_in_to_out",
            source="node_input_1",
            target="node_output_1",
            sourceHandle="output",
            targetHandle="input",
        )
    ]
    return WorkflowCreate(
        name="Simple Execution Pipeline",
        description="Linear Input to Output execution contract fixture",
        version="1.0.0",
        configuration=WorkflowConfigurationSchema(timeoutSeconds=60, collectMetrics=True),
        nodes=nodes,
        edges=edges,
        tags=["fixture", "member4_compat"],
    )


def create_conditional_branching_workflow() -> WorkflowCreate:
    """Fixture 2: Conditional branching pipeline (Input -> Condition -> [LLM / Tool] -> Output)."""
    nodes = [
        WorkflowNodeSchema(
            id="node_input_1",
            type="Input",
            name="Transaction Ingestion",
            position=NodePosition(x=50.0, y=200.0),
            config={"inputType": "json", "required": True},
            inputHandles=[],
            outputHandles=["output"],
        ),
        WorkflowNodeSchema(
            id="node_condition_1",
            type="Condition",
            name="Risk Level Check",
            position=NodePosition(x=300.0, y=200.0),
            config={
                "operator": "equals",
                "leftOperand": "status",
                "rightOperand": "high_risk",
                "variable": "status",
                "value": "high_risk",
            },
            inputHandles=["input"],
            outputHandles=["true", "false"],
        ),
        WorkflowNodeSchema(
            id="node_llm_1",
            type="LLM",
            name="AI Fraud Analysis (True Branch)",
            position=NodePosition(x=600.0, y=100.0),
            config={
                "model": "gemini-1.5-pro",
                "temperature": 0.2,
                "systemPrompt": "Analyze transaction risk factors thoroughly.",
                "prompt": "Evaluate this suspicious activity.",
            },
            inputHandles=["prompt", "context"],
            outputHandles=["response", "tokens"],
        ),
        WorkflowNodeSchema(
            id="node_tool_1",
            type="Tool",
            name="Quick Audit Logger (False Branch)",
            position=NodePosition(x=600.0, y=300.0),
            config={
                "toolName": "web_search",
                "tool": "web_search",
                "method": "POST",
                "timeoutSeconds": 15,
            },
            inputHandles=["params"],
            outputHandles=["result", "error"],
        ),
        WorkflowNodeSchema(
            id="node_output_1",
            type="Output",
            name="Audit Decision Report",
            position=NodePosition(x=900.0, y=200.0),
            config={"outputFormat": "markdown", "includeExecutionMetrics": True},
            inputHandles=["input"],
            outputHandles=[],
        ),
    ]
    edges = [
        WorkflowEdgeSchema(
            id="e_in_to_cond",
            source="node_input_1",
            target="node_condition_1",
            sourceHandle="output",
            targetHandle="input",
        ),
        WorkflowEdgeSchema(
            id="e_cond_true_to_llm",
            source="node_condition_1",
            target="node_llm_1",
            sourceHandle="true",
            targetHandle="prompt",
            condition="true",
        ),
        WorkflowEdgeSchema(
            id="e_cond_false_to_tool",
            source="node_condition_1",
            target="node_tool_1",
            sourceHandle="false",
            targetHandle="params",
            condition="false",
        ),
        WorkflowEdgeSchema(
            id="e_llm_to_out",
            source="node_llm_1",
            target="node_output_1",
            sourceHandle="response",
            targetHandle="input",
        ),
        WorkflowEdgeSchema(
            id="e_tool_to_out",
            source="node_tool_1",
            target="node_output_1",
            sourceHandle="result",
            targetHandle="input",
        ),
    ]
    return WorkflowCreate(
        name="Conditional Branching Pipeline",
        description="Branching fixture evaluating condition and routing to alternative handlers",
        version="1.0.0",
        configuration=WorkflowConfigurationSchema(timeoutSeconds=120, collectMetrics=True),
        nodes=nodes,
        edges=edges,
        tags=["fixture", "member4_compat", "branching"],
    )


def create_branch_joins_workflow() -> WorkflowCreate:
    """
    Fixture 3: Branch join pipeline.
    (Input -> Condition -> [Tool A, Tool B] -> Joins at LLM -> Output)
    """
    nodes = [
        WorkflowNodeSchema(
            id="node_input_1",
            type="Input",
            name="Investigation Subject",
            position=NodePosition(x=50.0, y=200.0),
            config={"inputType": "text", "defaultValue": "Quantum Computing Trends"},
            inputHandles=[],
            outputHandles=["output"],
        ),
        WorkflowNodeSchema(
            id="node_condition_1",
            type="Condition",
            name="Source Router",
            position=NodePosition(x=280.0, y=200.0),
            config={
                "operator": "equals",
                "leftOperand": "source_type",
                "rightOperand": "academic",
                "variable": "source_type",
                "value": "academic",
            },
            inputHandles=["input"],
            outputHandles=["true", "false"],
        ),
        WorkflowNodeSchema(
            id="node_tool_academic",
            type="Tool",
            name="Academic Search Tool",
            position=NodePosition(x=520.0, y=100.0),
            config={"toolName": "web_search", "timeoutSeconds": 20},
            inputHandles=["params"],
            outputHandles=["result"],
        ),
        WorkflowNodeSchema(
            id="node_tool_web",
            type="Tool",
            name="General Web Search Tool",
            position=NodePosition(x=520.0, y=300.0),
            config={"toolName": "web_search", "timeoutSeconds": 20},
            inputHandles=["params"],
            outputHandles=["result"],
        ),
        WorkflowNodeSchema(
            id="node_llm_join",
            type="LLM",
            name="Synthesis & Convergence Node",
            position=NodePosition(x=780.0, y=200.0),
            config={
                "model": "gemini-1.5-pro",
                "temperature": 0.4,
                "systemPrompt": "Synthesize the gathered findings from the active branch.",
            },
            inputHandles=["prompt", "context"],
            outputHandles=["response"],
        ),
        WorkflowNodeSchema(
            id="node_output_1",
            type="Output",
            name="Synthesized Report Output",
            position=NodePosition(x=1050.0, y=200.0),
            config={"outputFormat": "markdown"},
            inputHandles=["input"],
            outputHandles=[],
        ),
    ]
    edges = [
        WorkflowEdgeSchema(
            id="e_in_to_cond",
            source="node_input_1",
            target="node_condition_1",
            sourceHandle="output",
            targetHandle="input",
        ),
        WorkflowEdgeSchema(
            id="e_cond_true_to_acad",
            source="node_condition_1",
            target="node_tool_academic",
            sourceHandle="true",
            targetHandle="params",
            condition="true",
        ),
        WorkflowEdgeSchema(
            id="e_cond_false_to_web",
            source="node_condition_1",
            target="node_tool_web",
            sourceHandle="false",
            targetHandle="params",
            condition="false",
        ),
        # Both branches join into node_llm_join
        WorkflowEdgeSchema(
            id="e_acad_to_join",
            source="node_tool_academic",
            target="node_llm_join",
            sourceHandle="result",
            targetHandle="context",
        ),
        WorkflowEdgeSchema(
            id="e_web_to_join",
            source="node_tool_web",
            target="node_llm_join",
            sourceHandle="result",
            targetHandle="context",
        ),
        WorkflowEdgeSchema(
            id="e_join_to_out",
            source="node_llm_join",
            target="node_output_1",
            sourceHandle="response",
            targetHandle="input",
        ),
    ]
    return WorkflowCreate(
        name="Branch Join Convergence Pipeline",
        description="Fixture demonstrating parallel divergent branches joining into a unified downstream node",
        version="1.0.0",
        configuration=WorkflowConfigurationSchema(timeoutSeconds=180, collectMetrics=True),
        nodes=nodes,
        edges=edges,
        tags=["fixture", "member4_compat", "branch_join"],
    )


def create_human_approval_workflow() -> WorkflowCreate:
    """
    Fixture 4: Human-in-the-loop approval gate pipeline.
    (Input -> Document Reader -> Human Approval -> Output)
    """
    nodes = [
        WorkflowNodeSchema(
            id="node_input_1",
            type="Input",
            name="Contract Document Upload",
            position=NodePosition(x=50.0, y=150.0),
            config={"inputType": "file_url", "required": True},
            inputHandles=[],
            outputHandles=["output"],
        ),
        WorkflowNodeSchema(
            id="node_reader_1",
            type="Document Reader",
            name="Contract Parser",
            position=NodePosition(x=300.0, y=150.0),
            config={"chunkSize": 1500, "chunkOverlap": 100, "filePath": "contract.pdf", "file_path": "contract.pdf"},
            inputHandles=["filePath"],
            outputHandles=["content", "metadata"],
        ),
        WorkflowNodeSchema(
            id="node_approval_1",
            type="Human Approval",
            name="Legal Counsel Review Gate",
            position=NodePosition(x=580.0, y=150.0),
            config={
                "promptMessage": "Legal sign-off required: please inspect extracted contract clauses.",
                "prompt": "Legal sign-off required: please inspect extracted contract clauses.",
                "timeoutMinutes": 120,
                "defaultAction": "reject",
            },
            inputHandles=["payload"],
            outputHandles=["approved", "rejected"],
        ),
        WorkflowNodeSchema(
            id="node_output_1",
            type="Output",
            name="Executed Contract Artifact",
            position=NodePosition(x=860.0, y=150.0),
            config={"outputFormat": "markdown", "includeExecutionMetrics": True},
            inputHandles=["input"],
            outputHandles=[],
        ),
    ]
    edges = [
        WorkflowEdgeSchema(
            id="e_in_to_reader",
            source="node_input_1",
            target="node_reader_1",
            sourceHandle="output",
            targetHandle="filePath",
        ),
        WorkflowEdgeSchema(
            id="e_reader_to_approval",
            source="node_reader_1",
            target="node_approval_1",
            sourceHandle="content",
            targetHandle="payload",
        ),
        WorkflowEdgeSchema(
            id="e_approval_to_out",
            source="node_approval_1",
            target="node_output_1",
            sourceHandle="approved",
            targetHandle="input",
        ),
    ]
    return WorkflowCreate(
        name="Human In The Loop Approval Pipeline",
        description="Fixture demonstrating execution pausing at Human Approval gate",
        version="1.0.0",
        configuration=WorkflowConfigurationSchema(timeoutSeconds=300, collectMetrics=True),
        nodes=nodes,
        edges=edges,
        tags=["fixture", "member4_compat", "human_approval"],
    )
