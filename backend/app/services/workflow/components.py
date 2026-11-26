"""
AgentForge AI - Workflow Component Library
Defines the canonical catalog of the 7 supported visual workflow node types,
their Pydantic configuration schemas, handle contracts, and validation rules.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Type, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ComponentCategory(str, Enum):
    IO = "IO"
    AI = "AI"
    DATA = "Data"
    ACTION = "Action"
    LOGIC = "Logic"
    CONTROL = "Control"


# ---------------------------------------------------------------------------
# Pydantic Schemas for Node-Specific Configurations
# ---------------------------------------------------------------------------

class InputNodeConfig(BaseModel):
    """Configuration for Input Node."""
    inputType: Literal["text", "json", "file_url"] = "text"
    defaultValue: Any = ""
    required: bool = True
    placeholder: str = "Enter initial prompt or JSON payload..."

    @field_validator("inputType")
    @classmethod
    def validate_input_type(cls, v: str) -> str:
        allowed = {"text", "json", "file_url"}
        if v not in allowed:
            raise ValueError(f"Invalid inputType '{v}'. Allowed: {allowed}")
        return v


class LLMNodeConfig(BaseModel):
    """Configuration for LLM Node (Gemini & Multi-model)."""
    model: str = "gemini-1.5-pro"
    systemPrompt: str = "You are a helpful and precise assistant."
    prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    maxOutputTokens: int = Field(default=2048, ge=1, le=8192)
    responseFormat: Literal["text", "json_object"] = "text"

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Model name must not be empty.")
        return v.strip()


class DocumentReaderNodeConfig(BaseModel):
    """Configuration for Document Reader Node."""
    chunkSize: int = Field(default=1000, ge=50, le=10000)
    chunkOverlap: int = Field(default=200, ge=0, le=2000)
    extractTables: bool = False
    supportedExtensions: List[str] = Field(
        default_factory=lambda: [".pdf", ".txt", ".md", ".docx"]
    )

    @model_validator(mode="after")
    def validate_overlap(self) -> "DocumentReaderNodeConfig":
        if self.chunkOverlap >= self.chunkSize:
            raise ValueError(
                f"chunkOverlap ({self.chunkOverlap}) must be less than chunkSize ({self.chunkSize})."
            )
        return self


class ToolNodeConfig(BaseModel):
    """Configuration for Tool Node."""
    toolName: str = "web_search"
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    endpoint: str = ""
    timeoutSeconds: int = Field(default=30, ge=1, le=300)
    headers: Dict[str, str] = Field(default_factory=dict)

    @field_validator("toolName")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("toolName must not be empty.")
        return v.strip()


class ConditionNodeConfig(BaseModel):
    """Configuration for Condition Node."""
    operator: Literal[
        "equals", "not_equals", "contains", "greater_than", "less_than", "regex_match"
    ] = "equals"
    leftOperand: str = "status"
    rightOperand: Any = "success"

    @field_validator("leftOperand")
    @classmethod
    def validate_left_operand(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("leftOperand (variable/path) must not be empty.")
        return v.strip()


class HumanApprovalNodeConfig(BaseModel):
    """Configuration for Human Approval Node."""
    promptMessage: str = "Please review and approve this step to continue."
    timeoutMinutes: int = Field(default=60, ge=1, le=1440)
    defaultAction: Literal["reject", "escalate", "proceed"] = "reject"

    @field_validator("promptMessage")
    @classmethod
    def validate_prompt_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("promptMessage must not be empty.")
        return v.strip()


class OutputNodeConfig(BaseModel):
    """Configuration for Output Node."""
    outputFormat: Literal["markdown", "json", "raw_text", "file_download"] = "markdown"
    includeExecutionMetrics: bool = True


# ---------------------------------------------------------------------------
# Component Definition & Registry
# ---------------------------------------------------------------------------

class FieldDefinition(BaseModel):
    name: str
    label: str
    type: str  # text, select, number, slider, boolean, textarea
    default: Any = None
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    description: Optional[str] = None


class ComponentDefinition(BaseModel):
    """Definition of a visual workflow component in the library."""
    type: str
    displayName: str
    category: ComponentCategory
    description: str
    icon: str
    defaultInputs: List[str]
    defaultOutputs: List[str]
    configModel: Type[BaseModel]
    defaultConfig: Dict[str, Any]
    configFields: List[FieldDefinition] = Field(default_factory=list)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration dict against the component's Pydantic model."""
        validated = self.configModel(**config)
        return validated.model_dump()


class ComponentLibrary:
    """Registry managing the 7 canonical node component definitions."""

    def __init__(self):
        self._registry: Dict[str, ComponentDefinition] = {}
        self._register_default_components()

    def _register_default_components(self) -> None:
        # 1. Input Node
        self.register(
            ComponentDefinition(
                type="Input",
                displayName="Workflow Input",
                category=ComponentCategory.IO,
                description="Entry point for user input parameters, triggers, or payload data passed to start the workflow.",
                icon="FileInput",
                defaultInputs=[],
                defaultOutputs=["output"],
                configModel=InputNodeConfig,
                defaultConfig=InputNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="inputType",
                        label="Input Data Type",
                        type="select",
                        options=["text", "json", "file_url"],
                        default="text",
                    ),
                    FieldDefinition(
                        name="required",
                        label="Required",
                        type="boolean",
                        default=True,
                    ),
                    FieldDefinition(
                        name="placeholder",
                        label="Input Placeholder",
                        type="string",
                        default="Enter initial prompt or JSON payload...",
                    ),
                ],
            )
        )

        # 2. LLM Node
        self.register(
            ComponentDefinition(
                type="LLM",
                displayName="AI Model (Gemini)",
                category=ComponentCategory.AI,
                description="Executes prompts and reasoning chains against Google Gemini models with variable temperature and system instructions.",
                icon="Bot",
                defaultInputs=["prompt", "context"],
                defaultOutputs=["response", "tokens"],
                configModel=LLMNodeConfig,
                defaultConfig=LLMNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="model",
                        label="Model Variant",
                        type="select",
                        options=[
                            "gemini-1.5-pro",
                            "gemini-1.5-flash",
                            "gemini-2.0-flash-exp",
                            "gemini-2.5-pro",
                            "gemini-2.5-flash",
                        ],
                        default="gemini-1.5-pro",
                    ),
                    FieldDefinition(
                        name="systemPrompt",
                        label="System Instructions",
                        type="textarea",
                        default="You are a helpful and precise assistant.",
                    ),
                    FieldDefinition(
                        name="temperature",
                        label="Temperature (Creativity)",
                        type="slider",
                        min=0.0,
                        max=1.0,
                        step=0.1,
                        default=0.7,
                    ),
                    FieldDefinition(
                        name="maxOutputTokens",
                        label="Max Tokens",
                        type="number",
                        default=2048,
                    ),
                    FieldDefinition(
                        name="responseFormat",
                        label="Output Format",
                        type="select",
                        options=["text", "json_object"],
                        default="text",
                    ),
                ],
            )
        )

        # 3. Document Reader Node
        self.register(
            ComponentDefinition(
                type="Document Reader",
                displayName="Document Reader",
                category=ComponentCategory.DATA,
                description="Extracts, parses, and chunks content from PDF, Markdown, DOCX, and plain text files for context ingestion.",
                icon="FileText",
                defaultInputs=["filePath"],
                defaultOutputs=["content", "metadata"],
                configModel=DocumentReaderNodeConfig,
                defaultConfig=DocumentReaderNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="chunkSize",
                        label="Chunk Size (characters)",
                        type="number",
                        default=1000,
                    ),
                    FieldDefinition(
                        name="chunkOverlap",
                        label="Chunk Overlap",
                        type="number",
                        default=200,
                    ),
                    FieldDefinition(
                        name="extractTables",
                        label="Extract Tables",
                        type="boolean",
                        default=False,
                    ),
                ],
            )
        )

        # 4. Tool Node
        self.register(
            ComponentDefinition(
                type="Tool",
                displayName="External Tool / API",
                category=ComponentCategory.ACTION,
                description="Calls external APIs, Python script utilities, or pre-registered tools to perform actions in the workflow.",
                icon="Wrench",
                defaultInputs=["params"],
                defaultOutputs=["result", "error"],
                configModel=ToolNodeConfig,
                defaultConfig=ToolNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="toolName",
                        label="Tool Selection",
                        type="select",
                        options=["web_search", "python_interpreter", "http_request", "custom"],
                        default="web_search",
                    ),
                    FieldDefinition(
                        name="method",
                        label="HTTP Method",
                        type="select",
                        options=["GET", "POST", "PUT", "DELETE"],
                        default="POST",
                    ),
                    FieldDefinition(
                        name="endpoint",
                        label="Endpoint URL",
                        type="string",
                        default="",
                    ),
                    FieldDefinition(
                        name="timeoutSeconds",
                        label="Timeout (seconds)",
                        type="number",
                        default=30,
                    ),
                ],
            )
        )

        # 5. Condition Node
        self.register(
            ComponentDefinition(
                type="Condition",
                displayName="Branching Condition",
                category=ComponentCategory.LOGIC,
                description="Evaluates expressions or boolean statements to split workflow execution into alternative paths.",
                icon="GitFork",
                defaultInputs=["input"],
                defaultOutputs=["true", "false"],
                configModel=ConditionNodeConfig,
                defaultConfig=ConditionNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="operator",
                        label="Comparison Operator",
                        type="select",
                        options=[
                            "equals",
                            "not_equals",
                            "contains",
                            "greater_than",
                            "less_than",
                            "regex_match",
                        ],
                        default="equals",
                    ),
                    FieldDefinition(
                        name="leftOperand",
                        label="Variable / Path",
                        type="string",
                        default="status",
                    ),
                    FieldDefinition(
                        name="rightOperand",
                        label="Target Value",
                        type="string",
                        default="success",
                    ),
                ],
            )
        )

        # 6. Human Approval Node
        self.register(
            ComponentDefinition(
                type="Human Approval",
                displayName="Human-in-the-Loop Approval",
                category=ComponentCategory.CONTROL,
                description="Pauses workflow execution and generates an approval gate requiring human sign-off before proceeding.",
                icon="UserCheck",
                defaultInputs=["payload"],
                defaultOutputs=["approved", "rejected"],
                configModel=HumanApprovalNodeConfig,
                defaultConfig=HumanApprovalNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="promptMessage",
                        label="Approval Message for Reviewer",
                        type="string",
                        default="Please review and approve this step to continue.",
                    ),
                    FieldDefinition(
                        name="timeoutMinutes",
                        label="Timeout (minutes)",
                        type="number",
                        default=60,
                    ),
                    FieldDefinition(
                        name="defaultAction",
                        label="Action on Timeout",
                        type="select",
                        options=["reject", "escalate", "proceed"],
                        default="reject",
                    ),
                ],
            )
        )

        # 7. Output Node
        self.register(
            ComponentDefinition(
                type="Output",
                displayName="Workflow Output",
                category=ComponentCategory.IO,
                description="Terminal node aggregating final results, reports, or data artifacts delivered to the user or caller.",
                icon="FileOutput",
                defaultInputs=["input"],
                defaultOutputs=[],
                configModel=OutputNodeConfig,
                defaultConfig=OutputNodeConfig().model_dump(),
                configFields=[
                    FieldDefinition(
                        name="outputFormat",
                        label="Result Presentation Format",
                        type="select",
                        options=["markdown", "json", "raw_text", "file_download"],
                        default="markdown",
                    ),
                    FieldDefinition(
                        name="includeExecutionMetrics",
                        label="Include Latency / Cost Metrics",
                        type="boolean",
                        default=True,
                    ),
                ],
            )
        )

    def register(self, component: ComponentDefinition) -> None:
        """Register a component definition."""
        self._registry[component.type] = component

    def get(self, node_type: str) -> Optional[ComponentDefinition]:
        """Lookup component definition by node type."""
        return self._registry.get(node_type)

    def is_supported(self, node_type: str) -> bool:
        """Check if node type is registered and supported."""
        return node_type in self._registry

    def list_components(self) -> List[ComponentDefinition]:
        """Return list of all registered component definitions."""
        return list(self._registry.values())

    def list_types(self) -> List[str]:
        """Return list of supported node type names."""
        return list(self._registry.keys())

    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate config for a specific node type, returning canonical dict or raising ValueError."""
        comp = self.get(node_type)
        if not comp:
            raise ValueError(f"Unsupported node type '{node_type}'. Supported: {self.list_types()}")
        return comp.validate_config(config)


# Global singleton instance of the ComponentLibrary
component_library = ComponentLibrary()
