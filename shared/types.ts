/**
 * AgentForge AI - Shared Type Definitions
 * Used across Frontend, Backend, and AI agents.
 */

export type NodeType =
  | 'Input'
  | 'LLM'
  | 'Document Reader'
  | 'Tool'
  | 'Condition'
  | 'Human Approval'
  | 'Output';

export interface NodePosition {
  x: number;
  y: number;
}

export interface WorkflowNode<TConfig = Record<string, unknown>> {
  id: string;
  type: NodeType;
  name: string;
  position: NodePosition;
  config: TConfig;
  inputHandles?: string[];
  outputHandles?: string[];
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  condition?: string;
}

export interface WorkflowMetadata {
  id: string;
  name: string;
  description?: string;
  version: string;
  tags?: string[];
  author?: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowConfiguration {
  timeoutSeconds?: number;
  maxRetries?: number;
  autoRepairEnabled?: boolean;
  executionMode?: 'sequential' | 'dag' | 'langgraph';
}

export interface WorkflowDefinition {
  schemaVersion: '1.0.0';
  metadata: WorkflowMetadata;
  configuration?: WorkflowConfiguration;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface NodeTypeDefinition {
  type: NodeType;
  displayName: string;
  category: 'IO' | 'AI' | 'Data' | 'Action' | 'Logic' | 'Control';
  description: string;
  icon: string;
  defaultInputs: string[];
  defaultOutputs: string[];
  defaultConfig: Record<string, unknown>;
  configFields?: Array<{
    name: string;
    label: string;
    type: string;
    options?: string[];
    default?: unknown;
    min?: number;
    max?: number;
    step?: number;
  }>;
}

