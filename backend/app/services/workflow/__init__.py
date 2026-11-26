"""
AgentForge AI - Workflow Generation & Component Management (Member 3)
Exposes the Component Library, Generation Engine, Validator, Versioning, and Modifier.
"""

from app.services.workflow.components import (
    ComponentCategory,
    ComponentDefinition,
    ComponentLibrary,
    component_library,
    InputNodeConfig,
    LLMNodeConfig,
    DocumentReaderNodeConfig,
    ToolNodeConfig,
    ConditionNodeConfig,
    HumanApprovalNodeConfig,
    OutputNodeConfig,
)
from app.services.workflow.generator import (
    ExecutionPlan,
    ExecutionPlanStep,
    WorkflowGenerator,
    workflow_generator,
)
from app.services.workflow.validator import (
    ValidationSeverity,
    ValidationCategory,
    ValidationIssue,
    ValidationMetrics,
    ValidationResult,
    WorkflowValidator,
    workflow_validator,
)
from app.services.workflow.versioning import (
    NodeDiff,
    EdgeDiff,
    WorkflowDiff,
    increment_version,
    compare_workflows,
    restore_version,
    rollback_to_version,
    WorkflowHistory,
)
from app.services.workflow.modifier import (
    WorkflowModifier,
    workflow_modifier,
)
from app.services.workflow.fixtures import (
    create_simple_execution_workflow,
    create_conditional_branching_workflow,
    create_branch_joins_workflow,
    create_human_approval_workflow,
)

__all__ = [
    # Components
    "ComponentCategory",
    "ComponentDefinition",
    "ComponentLibrary",
    "component_library",
    "InputNodeConfig",
    "LLMNodeConfig",
    "DocumentReaderNodeConfig",
    "ToolNodeConfig",
    "ConditionNodeConfig",
    "HumanApprovalNodeConfig",
    "OutputNodeConfig",
    # Generator
    "ExecutionPlan",
    "ExecutionPlanStep",
    "WorkflowGenerator",
    "workflow_generator",
    # Validator
    "ValidationSeverity",
    "ValidationCategory",
    "ValidationIssue",
    "ValidationMetrics",
    "ValidationResult",
    "WorkflowValidator",
    "workflow_validator",
    # Versioning
    "NodeDiff",
    "EdgeDiff",
    "WorkflowDiff",
    "increment_version",
    "compare_workflows",
    "restore_version",
    "rollback_to_version",
    "WorkflowHistory",
    # Modifier
    "WorkflowModifier",
    "workflow_modifier",
    # Shared Fixtures
    "create_simple_execution_workflow",
    "create_conditional_branching_workflow",
    "create_branch_joins_workflow",
    "create_human_approval_workflow",
]
