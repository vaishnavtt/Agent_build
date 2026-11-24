export type PageView =
  | 'dashboard'
  | 'my-agents'
  | 'create-agent'
  | 'editor'
  | 'validation'
  | 'activity'
  | 'history'
  | 'templates'
  | 'settings';

export type ComponentType =
  | 'Input'
  | 'LLM'
  | 'Document Reader'
  | 'Tool'
  | 'Condition'
  | 'Human Approval'
  | 'Output';

export interface ComponentDefinition {
  type: ComponentType;
  displayName: string;
  category: 'IO' | 'AI' | 'Data' | 'Action' | 'Logic' | 'Control';
  description: string;
  iconName: string;
  color: string;
  defaultConfig: Record<string, any>;
  requiredFields: string[];
}

export interface WorkflowNodeData {
  label: string;
  componentType: ComponentType;
  description: string;
  status: 'ready' | 'needs-setup' | 'executing' | 'success' | 'failed';
  config: Record<string, any>;
  errorMessage?: string;
  executionOutput?: string;
}

export interface ValidationIssue {
  id: string;
  nodeId?: string;
  componentName: string;
  category: 'structural' | 'configuration' | 'connection' | 'coverage';
  severity: 'error' | 'warning' | 'info';
  title: string;
  description: string;
  suggestedFix: string;
  canAutoFix: boolean;
}

export interface StructuralCheck {
  id: string;
  title: string;
  description: string;
  passed: boolean;
  severity: 'error' | 'warning';
}

export interface RequirementCoverageItem {
  id: string;
  requirement: string;
  mappedComponent: string;
  covered: boolean;
  status: 'passed' | 'missing';
}

export interface TestCase {
  id: string;
  name: string;
  targetComponent: string;
  inputSample: string;
  expectedOutput: string;
  actualOutput: string;
  status: 'passed' | 'failed' | 'running' | 'pending';
  duration: string;
}

export interface ExecutionLogEntry {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
  component: string;
  message: string;
  stackTrace?: string;
}

export interface ExecutionStep {
  id: string;
  stepNumber: number;
  componentName: string;
  componentType: ComponentType;
  activity: string;
  status: 'completed' | 'processing' | 'failed' | 'waiting';
  timestamp: string;
  duration?: string;
  details?: string;
}

export interface ExecutionRecord {
  id: string;
  agentId: string;
  agentName: string;
  startedAt: string;
  duration: string;
  status: 'completed' | 'failed' | 'repaired' | 'running';
  triggerType: string;
  steps: ExecutionStep[];
  repaired?: boolean;
  repairAttempts?: number;
  errorSnippet?: string;
  logEvidence?: ExecutionLogEntry[];
}

export interface AutoRepairState {
  isActive: boolean;
  attemptCount: number;
  stage: 'idle' | 'identifying' | 'preparing' | 'applying' | 'checking' | 'retesting' | 'completed' | 'failed';
  problemFound: string;
  whyItHappened: string;
  logEvidence: ExecutionLogEntry[];
  suggestedFix: string;
  appliedCorrections: string[];
  revalidationStatus?: 'passed' | 'failed';
  retestStatus?: 'passed' | 'failed';
  finalStatus?: 'success' | 'failed';
}

export interface RepairReport {
  executionId: string;
  agentName: string;
  attemptNumber: number;
  maxAttempts: number;
  originalError: string;
  logEvidence: string;
  diagnosedReason: string;
  proposedCorrection: string;
  appliedCorrection: string;
  revalidationResult: string;
  retestResult: string;
  finalStatus: 'VERIFIED_SUCCESS' | 'FAILED';
  timestamp: string;
}

export interface AgentTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  componentCount: number;
  tags: string[];
  samplePrompt: string;
  nodes: any[];
  edges: any[];
}

export interface AgentSummary {
  id: string;
  name: string;
  description: string;
  lastUpdated: string;
  status: 'Ready' | 'Active' | 'Needs Review';
  runsCount: number;
  successRate: string;
  nodesCount: number;
  nodes: any[];
  edges: any[];
}

// ---------------------------------------------------------------------------
// Member 2: AI Requirement Analysis & Agent Architect Types
// ---------------------------------------------------------------------------
export interface TaskDecompositionItem {
  task_id: string;
  task_name: string;
  description: string;
  task_description?: string;
  component: ComponentType;
  component_type?: ComponentType;
  required_component?: ComponentType;
  input: string;
  expected_output: string;
  dependencies: string[];
  execution_order: number;
  component_config_hints?: Record<string, any>;
}

export interface RequirementsBreakdown {
  inputs: string[];
  processing: string[];
  outputs: string[];
  expected_outputs?: string[];
  tools: string[];
  constraints: string[];
  functional?: string[];
  non_functional?: string[];
}

export interface AcceptanceCriterion {
  id: string;
  requirement_id?: string;
  criteria: string;
  description?: string;
  pass_condition?: string;
}

export interface EdgeCaseScenario {
  scenario_id: string;
  description: string;
  input_condition: string;
  expected_behavior: string;
  expected_result?: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface TestScenario {
  test_id: string;
  requirement_id?: string;
  test_description: string;
  test_input: any;
  expected_output: any;
  expected_status: string;
  pass_fail_condition: string;
  scenario_type: 'positive' | 'negative' | 'edge_case';
}

export interface ClarificationQuestion {
  id: string;
  question: string;
  reason: string;
  category?: string;
}

export interface ExecutionPlanResponse {
  project_objective: string;
  status: 'ready' | 'needs_clarification';
  requirements: RequirementsBreakdown;
  tasks: TaskDecompositionItem[];
  execution_plan?: TaskDecompositionItem[];
  required_components: ComponentType[];
  components?: ComponentType[];
  clarification_questions: ClarificationQuestion[];
  acceptance_criteria?: AcceptanceCriterion[];
  edge_cases?: EdgeCaseScenario[];
  test_scenarios?: TestScenario[];
  assumptions?: string[];
  confidence_score: number;
  architecture_summary?: string;
  ai_provider: 'google-gemini' | 'deterministic_engine' | 'mock';
  model_used?: string;
  contract_version: string;
}

export interface AnalysisRequest {
  description: string;
  clarification_answers?: Record<string, string>;
  context?: Record<string, any>;
}
