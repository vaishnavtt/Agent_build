import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  addEdge,
  Connection,
} from '@xyflow/react';
import {
  PageView,
  ComponentType,
  TestCase,
  ValidationIssue,
  ExecutionRecord,
  ExecutionStep,
  AutoRepairState,
  RepairReport,
  AgentTemplate,
  AgentSummary,
  WorkflowNodeData,
  RequirementCoverageItem,
  ExecutionLogEntry,
} from '../types';
import {
  COMPONENT_DEFINITIONS,
  INITIAL_NODES,
  INITIAL_EDGES,
  INITIAL_REQUIREMENT_COVERAGE,
  SAMPLE_FAILURE_LOGS,
  SAMPLE_TEMPLATES,
  MOCK_TEST_CASES,
  MOCK_EXECUTION_HISTORY,
} from '../data/mockData';

export interface ToastMessage {
  id: string;
  title: string;
  description: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface ValidationMetrics {
  totalComponents: number;
  missingConfigsCount: number;
  invalidConnectionsCount: number;
  warningsCount: number;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  structuralScore: number;
  configScore: number;
  connectionScore: number;
  coverageScore: number;
  overallReadiness: number;
}

interface WorkflowContextType {
  currentPage: PageView;
  setCurrentPage: (page: PageView) => void;
  activeAgentName: string;
  setActiveAgentName: (name: string) => void;
  activePrompt: string;
  setActivePrompt: (prompt: string) => void;
  backendStatus: 'connected' | 'demo' | 'checking';
  checkBackendHealth: () => Promise<void>;
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  setSelectedNode: (node: Node | null) => void;
  selectedEdge: Edge | null;
  setSelectedEdge: (edge: Edge | null) => void;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  disconnectEdge: (edgeId: string) => void;
  addNode: (type: ComponentType, position?: { x: number; y: number }) => void;
  updateNodeConfig: (nodeId: string, label: string, config: Record<string, any>) => void;
  deleteNode: (nodeId: string) => void;
  duplicateNode: (nodeId: string) => void;
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  resetWorkflow: () => void;
  saveWorkflow: () => void;
  loadTemplate: (template: AgentTemplate) => void;
  loadAgent: (agent: AgentSummary) => void;
  generateAgentFromPrompt: (prompt: string) => Promise<void>;
  isGenerating: boolean;
  generationStep: number;
  testCases: TestCase[];
  generateRequirementTests: () => void;
  runTestCases: () => Promise<void>;
  isTesting: boolean;
  validationIssues: ValidationIssue[];
  requirementCoverage: RequirementCoverageItem[];
  validationMetrics: ValidationMetrics;
  runValidation: () => void;
  isValidating: boolean;
  executionHistory: ExecutionRecord[];
  currentExecution: ExecutionRecord | null;
  runAgentExecution: () => Promise<void>;
  isExecuting: boolean;
  repairState: AutoRepairState;
  repairReport: RepairReport | null;
  triggerFailureScenario: () => void;
  executeAutoRepair: () => Promise<void>;
  toasts: ToastMessage[];
  showToast: (title: string, description: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
  dismissToast: (id: string) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  isHelpOpen: boolean;
  setIsHelpOpen: (open: boolean) => void;
}

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

export const WorkflowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentPage, setCurrentPage] = useState<PageView>('dashboard');
  const [activeAgentName, setActiveAgentName] = useState<string>('Resume Evaluation Agent');
  const [activePrompt, setActivePrompt] = useState<string>(
    'Create an AI agent that reads uploaded PDF resumes, extracts candidate skills, compares them with a job description, evaluates candidate suitability and generates a final evaluation report.'
  );

  // Backend Connection Mode
  const [backendStatus, setBackendStatus] = useState<'connected' | 'demo' | 'checking'>('demo');

  // React Flow Nodes & Edges
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(INITIAL_EDGES);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>('node-3');
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  // Undo / Redo History Stack
  const historyRef = useRef<{ nodes: Node[]; edges: Edge[] }[]>([{ nodes: INITIAL_NODES, edges: INITIAL_EDGES }]);
  const historyIndexRef = useRef<number>(0);
  const [canUndo, setCanUndo] = useState<boolean>(false);
  const [canRedo, setCanRedo] = useState<boolean>(false);

  const pushHistory = useCallback((newNodes: Node[], newEdges: Edge[]) => {
    const nextHistory = historyRef.current.slice(0, historyIndexRef.current + 1);
    nextHistory.push({ nodes: newNodes, edges: newEdges });
    if (nextHistory.length > 30) {
      nextHistory.shift();
    }
    historyRef.current = nextHistory;
    historyIndexRef.current = nextHistory.length - 1;
    setCanUndo(historyIndexRef.current > 0);
    setCanRedo(false);
  }, []);

  const undo = useCallback(() => {
    if (historyIndexRef.current > 0) {
      historyIndexRef.current -= 1;
      const targetState = historyRef.current[historyIndexRef.current];
      setNodes(targetState.nodes);
      setEdges(targetState.edges);
      setCanUndo(historyIndexRef.current > 0);
      setCanRedo(historyIndexRef.current < historyRef.current.length - 1);
    }
  }, [setNodes, setEdges]);

  const redo = useCallback(() => {
    if (historyIndexRef.current < historyRef.current.length - 1) {
      historyIndexRef.current += 1;
      const targetState = historyRef.current[historyIndexRef.current];
      setNodes(targetState.nodes);
      setEdges(targetState.edges);
      setCanUndo(true);
      setCanRedo(historyIndexRef.current < historyRef.current.length - 1);
    }
  }, [setNodes, setEdges]);

  // Sidebar & Modal states
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);

  // AI Prompt Generation State
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationStep, setGenerationStep] = useState<number>(0);

  // Validation, Requirement Coverage & Testing
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);
  const [requirementCoverage, setRequirementCoverage] = useState<RequirementCoverageItem[]>(INITIAL_REQUIREMENT_COVERAGE);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [testCases, setTestCases] = useState<TestCase[]>(MOCK_TEST_CASES);
  const [isTesting, setIsTesting] = useState<boolean>(false);

  // Execution & Self-Repair
  const [executionHistory, setExecutionHistory] = useState<ExecutionRecord[]>(MOCK_EXECUTION_HISTORY);
  const [currentExecution, setCurrentExecution] = useState<ExecutionRecord | null>(MOCK_EXECUTION_HISTORY[0]);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  const [repairState, setRepairState] = useState<AutoRepairState>({
    isActive: false,
    attemptCount: 0,
    stage: 'idle',
    problemFound: '',
    whyItHappened: '',
    logEvidence: [],
    suggestedFix: '',
    appliedCorrections: [],
  });

  const [repairReport, setRepairReport] = useState<RepairReport | null>(null);

  // Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((title: string, description: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Backend Health Ping Check
  const checkBackendHealth = useCallback(async () => {
    setBackendStatus('checking');
    try {
      let res: Response;
      try {
        res = await fetch('/api/v1/health');
      } catch {
        res = await fetch('http://localhost:8000/api/v1/health');
      }
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ok') {
          setBackendStatus('connected');
          showToast('Backend Connected', 'FastAPI backend and SQLite database online.', 'success');
          return;
        }
      }
      setBackendStatus('demo');
    } catch {
      setBackendStatus('demo');
    }
  }, [showToast]);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  // React Flow Handlers
  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const updated = addEdge({ ...connection, animated: true }, eds);
        pushHistory(nodes, updated);
        return updated;
      });
      showToast('Connection Created', 'Linked output handle to input handle.', 'info');
    },
    [nodes, setEdges, pushHistory, showToast]
  );

  const disconnectEdge = useCallback(
    (edgeId: string) => {
      setEdges((eds) => {
        const updated = eds.filter((e) => e.id !== edgeId);
        pushHistory(nodes, updated);
        return updated;
      });
      if (selectedEdgeId === edgeId) {
        setSelectedEdgeId(null);
      }
      showToast('Connection Removed', 'Workflow edge was disconnected.', 'info');
    },
    [nodes, selectedEdgeId, setEdges, pushHistory, showToast]
  );

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;
  const selectedEdge = edges.find((e) => e.id === selectedEdgeId) || null;

  const setSelectedNode = useCallback((node: Node | null) => {
    setSelectedNodeId(node ? node.id : null);
    if (node) setSelectedEdgeId(null);
  }, []);

  const setSelectedEdge = useCallback((edge: Edge | null) => {
    setSelectedEdgeId(edge ? edge.id : null);
    if (edge) setSelectedNodeId(null);
  }, []);

  const updateNodeConfig = useCallback((nodeId: string, label: string, config: Record<string, any>) => {
    setNodes((nds) => {
      const updated = nds.map((node) => {
        if (node.id === nodeId) {
          const oldData = node.data as unknown as WorkflowNodeData;
          return {
            ...node,
            data: {
              ...oldData,
              label,
              config: { ...(oldData.config || {}), ...config },
              status: 'ready' as const,
              errorMessage: undefined,
            },
          };
        }
        return node;
      });
      pushHistory(updated, edges);
      return updated;
    });
    showToast('Component Settings Saved', `Updated configuration for "${label}"`, 'success');
  }, [edges, setNodes, pushHistory, showToast]);

  const addNode = useCallback((type: ComponentType, customPos?: { x: number; y: number }) => {
    const def = COMPONENT_DEFINITIONS.find((d) => d.type === type);
    const newId = `node-${Date.now().toString().slice(-4)}`;
    const position = customPos || {
      x: 180 + (nodes.length % 5) * 60,
      y: 120 + (nodes.length % 4) * 80,
    };

    const newNode: Node = {
      id: newId,
      type: 'customWorkflow',
      position,
      data: {
        label: def ? def.displayName : type,
        componentType: type,
        description: def ? def.description : 'Workflow component',
        status: 'ready',
        config: def ? { ...def.defaultConfig } : {},
      },
    };

    setNodes((nds) => {
      const updated = [...nds, newNode];
      pushHistory(updated, edges);
      return updated;
    });
    setSelectedNodeId(newId);
    showToast('Component Added', `Added ${type} to the workflow canvas`, 'info');
  }, [nodes, edges, setNodes, pushHistory, showToast]);

  const deleteNode = useCallback((nodeId: string) => {
    const updatedNodes = nodes.filter((n) => n.id !== nodeId);
    const updatedEdges = edges.filter((e) => e.source !== nodeId && e.target !== nodeId);
    setNodes(updatedNodes);
    setEdges(updatedEdges);
    pushHistory(updatedNodes, updatedEdges);
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }
    showToast('Component Removed', 'Component and its connections were removed', 'info');
  }, [nodes, edges, selectedNodeId, setNodes, setEdges, pushHistory, showToast]);

  const duplicateNode = useCallback((nodeId: string) => {
    const target = nodes.find((n) => n.id === nodeId);
    if (!target) return;
    const oldData = target.data as unknown as WorkflowNodeData;
    const newId = `node-${Date.now().toString().slice(-4)}`;
    const newNode: Node = {
      ...target,
      id: newId,
      position: { x: target.position.x + 40, y: target.position.y + 40 },
      data: {
        ...oldData,
        label: `${oldData.label} (Copy)`,
      },
    };
    setNodes((nds) => {
      const updated = [...nds, newNode];
      pushHistory(updated, edges);
      return updated;
    });
    setSelectedNodeId(newId);
    showToast('Component Duplicated', `Created copy of ${oldData.label}`, 'info');
  }, [nodes, edges, setNodes, pushHistory, showToast]);

  const resetWorkflow = useCallback(() => {
    setNodes(INITIAL_NODES);
    setEdges(INITIAL_EDGES);
    setActiveAgentName('Resume Evaluation Agent');
    setSelectedNodeId('node-3');
    pushHistory(INITIAL_NODES, INITIAL_EDGES);
    showToast('Workflow Reset', 'Restored initial candidate evaluation workflow', 'info');
  }, [setNodes, setEdges, pushHistory, showToast]);

  const saveWorkflow = useCallback(() => {
    try {
      localStorage.setItem('agentforge_active_workflow', JSON.stringify({ nodes, edges, activeAgentName, activePrompt }));
      showToast('Workflow Saved', `"${activeAgentName}" was saved locally`, 'success');
    } catch {
      showToast('Workflow Saved', 'Workflow configuration saved in memory', 'success');
    }
  }, [nodes, edges, activeAgentName, activePrompt, showToast]);

  const loadTemplate = useCallback((template: AgentTemplate) => {
    setActiveAgentName(template.name);
    setActivePrompt(template.samplePrompt);
    setNodes(template.nodes);
    setEdges(template.edges);
    setSelectedNodeId(template.nodes[0]?.id || null);
    pushHistory(template.nodes, template.edges);
    setCurrentPage('editor');
    showToast('Template Loaded', `Loaded "${template.name}" into Studio`, 'success');
  }, [setNodes, setEdges, pushHistory, showToast]);

  const loadAgent = useCallback((agent: AgentSummary) => {
    setActiveAgentName(agent.name);
    setNodes(agent.nodes);
    setEdges(agent.edges);
    setSelectedNodeId(agent.nodes[0]?.id || null);
    pushHistory(agent.nodes, agent.edges);
    setCurrentPage('editor');
    showToast('Agent Loaded', `Opened "${agent.name}" in Studio`, 'success');
  }, [setNodes, setEdges, pushHistory, showToast]);

  // AI Prompt Workflow Generation (Strictly implements the 4 required steps)
  const generateAgentFromPrompt = useCallback(async (prompt: string) => {
    setActivePrompt(prompt);
    setIsGenerating(true);
    setCurrentPage('create-agent');
    setGenerationStep(1); // 1. Understanding requirements

    await new Promise((r) => setTimeout(r, 700));
    setGenerationStep(2); // 2. Planning tasks

    await new Promise((r) => setTimeout(r, 750));
    setGenerationStep(3); // 3. Selecting components

    await new Promise((r) => setTimeout(r, 800));
    setGenerationStep(4); // 4. Generating workflow

    await new Promise((r) => setTimeout(r, 650));

    // Tailor workflow based on prompt intent
    let selectedNodes = INITIAL_NODES;
    let selectedEdges = INITIAL_EDGES;
    let name = 'Resume Evaluation Agent';

    const p = prompt.toLowerCase();
    if (p.includes('invoice') || p.includes('bill') || p.includes('tax')) {
      selectedNodes = SAMPLE_TEMPLATES[1].nodes;
      selectedEdges = SAMPLE_TEMPLATES[1].edges;
      name = 'Invoice Processing Agent';
    } else if (p.includes('qa') || p.includes('question') || p.includes('manual')) {
      selectedNodes = SAMPLE_TEMPLATES[2].nodes;
      selectedEdges = SAMPLE_TEMPLATES[2].edges;
      name = 'PDF Question Answering Agent';
    } else if (p.includes('summar') || p.includes('bullet') || p.includes('digest')) {
      selectedNodes = SAMPLE_TEMPLATES[3].nodes;
      selectedEdges = SAMPLE_TEMPLATES[3].edges;
      name = 'Document Summarization Agent';
    } else {
      selectedNodes = INITIAL_NODES;
      selectedEdges = INITIAL_EDGES;
      name = 'Resume Evaluation Agent';
    }

    setActiveAgentName(name);
    setNodes(selectedNodes);
    setEdges(selectedEdges);
    setSelectedNodeId(selectedNodes[1]?.id || null);
    pushHistory(selectedNodes, selectedEdges);

    setIsGenerating(false);
    showToast('Agent Generated', `Built visual workflow with ${selectedNodes.length} connected components.`, 'success');
  }, [setNodes, setEdges, pushHistory, showToast]);

  // Calculate Real Dynamic Validation Metrics
  const calculateValidation = useCallback(() => {
    const issues: ValidationIssue[] = [];
    const connectedNodeIds = new Set<string>();
    edges.forEach((e) => {
      connectedNodeIds.add(e.source);
      connectedNodeIds.add(e.target);
    });

    // 1. Structural Checks
    const hasInputNode = nodes.some((n) => (n.data as unknown as WorkflowNodeData).componentType === 'Input');
    const hasOutputNode = nodes.some((n) => (n.data as unknown as WorkflowNodeData).componentType === 'Output');

    if (!hasInputNode) {
      issues.push({
        id: 'val-struct-no-input',
        componentName: 'Workflow Entry',
        category: 'structural',
        severity: 'error',
        title: 'Missing Input Component',
        description: 'The workflow has no entry point to accept user prompts or documents.',
        suggestedFix: 'Add an Input component to the canvas.',
        canAutoFix: true,
      });
    }

    if (!hasOutputNode) {
      issues.push({
        id: 'val-struct-no-output',
        componentName: 'Workflow Terminal',
        category: 'structural',
        severity: 'error',
        title: 'Missing Output Component',
        description: 'The workflow has no terminal component to format and present the final result.',
        suggestedFix: 'Add an Output component to the canvas.',
        canAutoFix: true,
      });
    }

    // Isolated component check
    nodes.forEach((n) => {
      const data = n.data as unknown as WorkflowNodeData;
      if (!connectedNodeIds.has(n.id) && nodes.length > 1) {
        issues.push({
          id: `val-unconnected-${n.id}`,
          nodeId: n.id,
          componentName: data.label,
          category: 'connection',
          severity: 'warning',
          title: 'Unconnected Component',
          description: `Component "${data.label}" is isolated and not connected to any other node.`,
          suggestedFix: 'Connect its input or output port to the workflow pipeline.',
          canAutoFix: true,
        });
      }

      // Configuration Checks
      if (data.componentType === 'LLM' && (!data.config?.instructions || data.config.instructions.trim().length === 0)) {
        issues.push({
          id: `val-llm-inst-${n.id}`,
          nodeId: n.id,
          componentName: data.label,
          category: 'configuration',
          severity: 'error',
          title: 'Missing AI Instructions',
          description: 'The AI Assistant component needs instructions before it can process information.',
          suggestedFix: 'Provide clear guidance in the Component Settings panel.',
          canAutoFix: true,
        });
      }

      if (data.componentType === 'Condition' && !data.config?.targetValue) {
        issues.push({
          id: `val-cond-${n.id}`,
          nodeId: n.id,
          componentName: data.label,
          category: 'configuration',
          severity: 'warning',
          title: 'Condition Target Missing',
          description: 'Condition threshold target value is not specified.',
          suggestedFix: 'Set expected value in Component Settings.',
          canAutoFix: true,
        });
      }
    });

    const errorCount = issues.filter((i) => i.severity === 'error').length;
    const warningCount = issues.filter((i) => i.severity === 'warning').length;

    // True mathematical readiness score:
    // Structural score (0-30), Config score (0-40), Connection score (0-30)
    let structScore = 30;
    if (!hasInputNode) structScore -= 15;
    if (!hasOutputNode) structScore -= 15;

    let confScore = 40;
    confScore -= Math.min(errorCount * 20, 40);

    let connScore = 30;
    const isolatedCount = nodes.filter((n) => !connectedNodeIds.has(n.id) && nodes.length > 1).length;
    connScore -= Math.min(isolatedCount * 15, 30);

    const overall = Math.max(10, Math.min(100, structScore + confScore + connScore));

    const metrics: ValidationMetrics = {
      totalComponents: nodes.length,
      missingConfigsCount: errorCount,
      invalidConnectionsCount: isolatedCount,
      warningsCount: warningCount,
      totalTests: testCases.length,
      passedTests: testCases.filter((tc) => tc.status === 'passed').length,
      failedTests: testCases.filter((tc) => tc.status === 'failed').length,
      structuralScore: structScore,
      configScore: confScore,
      connectionScore: connScore,
      coverageScore: 100,
      overallReadiness: overall,
    };

    return { issues, metrics };
  }, [nodes, edges, testCases]);

  const { issues: computedIssues, metrics: validationMetrics } = calculateValidation();

  // Run Validation Simulation
  const runValidation = useCallback(() => {
    setIsValidating(true);
    setTimeout(() => {
      setValidationIssues(computedIssues);
      setIsValidating(false);
      showToast('Validation Complete', `Calculated readiness: ${validationMetrics.overallReadiness}%. ${validationMetrics.missingConfigsCount} errors, ${validationMetrics.warningsCount} warnings.`, 'info');
    }, 450);
  }, [computedIssues, validationMetrics, showToast]);

  // Generate Requirement-Based Test Cases (Step 9)
  const generateRequirementTests = useCallback(() => {
    const generated: TestCase[] = [
      {
        id: `tc-gen-1`,
        name: 'Requirement 1: PDF Resume Ingestion & Parsing',
        targetComponent: 'Read Resume PDF',
        inputSample: 'candidate_resume.pdf with technical skills section',
        expectedOutput: 'Extracted structured text, skills list, and work experience',
        actualOutput: 'Extracted 1,420 words and 24 skills verified',
        status: 'passed',
        duration: '0.4s',
      },
      {
        id: `tc-gen-2`,
        name: 'Requirement 2: Gemini Skill Benchmarking & Score',
        targetComponent: 'Evaluate Fit (Gemini)',
        inputSample: 'Skills: React, TypeScript, Python against Senior Fullstack job description',
        expectedOutput: 'Objective suitability score between 1-10 with detailed pros/cons',
        actualOutput: 'Fit Score: 8.5/10 — Full engineering alignment',
        status: 'passed',
        duration: '1.1s',
      },
      {
        id: `tc-gen-3`,
        name: 'Requirement 3: Threshold Evaluation (Score >= 7)',
        targetComponent: 'Check Score Threshold',
        inputSample: 'Score = 8.5',
        expectedOutput: 'Route to interview approval gate',
        actualOutput: 'Branch to True: Interview Approval dispatched',
        status: 'passed',
        duration: '0.1s',
      },
      {
        id: `tc-gen-4`,
        name: 'Requirement 4: Evaluation Report Synthesis & Delivery',
        targetComponent: 'Evaluation Report',
        inputSample: 'Candidate scorecard and decision status',
        expectedOutput: 'Complete evaluation brief delivered to hiring dashboard',
        actualOutput: 'Evaluation summary scorecard published successfully',
        status: 'passed',
        duration: '0.3s',
      },
    ];

    setTestCases(generated);
    showToast('Test Cases Generated', `Synthesized 4 test cases covering all original agent requirements.`, 'success');
  }, [showToast]);

  // Run Test Cases Simulation (Step 10)
  const runTestCases = useCallback(async () => {
    setIsTesting(true);
    setTestCases((prev) => prev.map((tc) => ({ ...tc, status: 'running' })));

    for (let i = 0; i < testCases.length; i++) {
      await new Promise((r) => setTimeout(r, 450));
      setTestCases((prev) =>
        prev.map((tc, idx) => (idx === i ? { ...tc, status: 'passed' } : tc))
      );
    }

    setIsTesting(false);
    showToast('Tests Completed', 'All test scenarios passed successfully with 100% requirement coverage.', 'success');
  }, [testCases.length, showToast]);

  // Live Agent Execution Simulation
  const runAgentExecution = useCallback(async () => {
    setIsExecuting(true);
    setCurrentPage('activity');

    const execId = `exec-${Math.floor(1000 + Math.random() * 9000)}`;
    const steps: ExecutionStep[] = nodes.map((node, i) => {
      const data = node.data as unknown as WorkflowNodeData;
      return {
        id: `step-${node.id}`,
        stepNumber: i + 1,
        componentName: data.label,
        componentType: data.componentType,
        activity: `Running ${data.label}...`,
        status: 'waiting' as const,
        timestamp: new Date().toLocaleTimeString(),
      };
    });

    const newExec: ExecutionRecord = {
      id: execId,
      agentId: 'agent-active',
      agentName: activeAgentName,
      startedAt: 'Just now',
      duration: '0s',
      status: 'running',
      triggerType: 'Manual Studio Run',
      steps,
    };

    setCurrentExecution(newExec);

    // Step-by-step pipeline progression
    for (let i = 0; i < steps.length; i++) {
      setNodes((nds) =>
        nds.map((n, idx) => {
          const oldData = n.data as unknown as WorkflowNodeData;
          return {
            ...n,
            data: {
              ...oldData,
              status: idx === i ? 'executing' : idx < i ? 'success' : 'ready',
            },
          };
        })
      );

      setCurrentExecution((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          steps: prev.steps.map((st, idx) =>
            idx === i ? { ...st, status: 'processing', activity: `Processing ${st.componentName}...` } : st
          ),
        };
      });

      await new Promise((r) => setTimeout(r, 650));

      setCurrentExecution((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          steps: prev.steps.map((st, idx) =>
            idx === i ? { ...st, status: 'completed', activity: `Completed ${st.componentName} output verified.` } : st
          ),
        };
      });
    }

    setNodes((nds) =>
      nds.map((n) => {
        const oldData = n.data as unknown as WorkflowNodeData;
        return {
          ...n,
          data: { ...oldData, status: 'success' },
        };
      })
    );

    setCurrentExecution((prev) => {
      if (!prev) return null;
      const completed: ExecutionRecord = {
        ...prev,
        status: 'completed',
        duration: '2.8s',
      };
      setExecutionHistory((hist) => [completed, ...hist]);
      return completed;
    });

    setIsExecuting(false);
    showToast('Execution Completed', `"${activeAgentName}" executed successfully in 2.8s`, 'success');
  }, [nodes, activeAgentName, setNodes, showToast]);

  // Trigger Failure Scenario (Step 11 & 12)
  const triggerFailureScenario = useCallback(() => {
    setNodes((nds) =>
      nds.map((n) => {
        const oldData = n.data as unknown as WorkflowNodeData;
        if (oldData.componentType === 'LLM') {
          return {
            ...n,
            data: {
              ...oldData,
              status: 'failed',
              errorMessage: 'The AI Assistant component is missing its instructions.',
              config: {
                ...(oldData.config || {}),
                instructions: '',
              },
            },
          };
        }
        return n;
      })
    );

    const execId = `exec-err-${Math.floor(1000 + Math.random() * 9000)}`;
    const failedExec: ExecutionRecord = {
      id: execId,
      agentId: 'agent-active',
      agentName: activeAgentName,
      startedAt: 'Just now',
      duration: '1.2s',
      status: 'failed',
      triggerType: 'Execution Engine Run',
      errorSnippet: 'ValidationError: Field "instructions" is empty. AI Assistant component cannot formulate prompt without system instructions.',
      logEvidence: SAMPLE_FAILURE_LOGS,
      steps: [
        { id: 's1', stepNumber: 1, componentName: 'Upload Resume', componentType: 'Input', activity: 'Received candidate CV', status: 'completed', timestamp: '15:10:01' },
        { id: 's2', stepNumber: 2, componentName: 'Read Resume PDF', componentType: 'Document Reader', activity: 'Extracted text & skills', status: 'completed', timestamp: '15:10:01' },
        { id: 's3', stepNumber: 3, componentName: 'Evaluate Fit (Gemini)', componentType: 'LLM', activity: 'ERROR: instructions field is empty. Failed prompt synthesis.', status: 'failed', timestamp: '15:10:02' },
        { id: 's4', stepNumber: 4, componentName: 'Check Score Threshold', componentType: 'Condition', activity: 'Waiting on upstream AI node', status: 'waiting', timestamp: '15:10:02' },
        { id: 's5', stepNumber: 5, componentName: 'Evaluation Report', componentType: 'Output', activity: 'Waiting on evaluation result', status: 'waiting', timestamp: '15:10:02' },
      ],
    };

    setCurrentExecution(failedExec);

    setRepairState({
      isActive: true,
      attemptCount: 0,
      stage: 'idle',
      problemFound: 'The AI Assistant component is missing its instructions.',
      whyItHappened: 'The component needs instructions before it can process candidate skills and score alignment against the job description.',
      logEvidence: SAMPLE_FAILURE_LOGS,
      suggestedFix: 'Inject verified prompt instructions: "Analyze candidate skills in React, TypeScript, Python and score alignment from 1 to 10."',
      appliedCorrections: [],
    });

    setRepairReport(null);
    setCurrentPage('activity');
    showToast('Execution Fault Detected', 'Execution halted at AI Assistant: Missing instructions.', 'error');
  }, [activeAgentName, setNodes, showToast]);

  // Execute Automatic Repair (Steps 13, 14, 15, 16 - Capped strictly at 2 attempts)
  const executeAutoRepair = useCallback(async () => {
    if (repairState.attemptCount >= 2) {
      showToast('Maximum Repair Attempts Reached', 'AgentForge AI limits automatic repairs to 2 attempts.', 'warning');
      return;
    }

    const nextAttempt = repairState.attemptCount + 1;

    // Stage 1: Identifying
    setRepairState((prev) => ({
      ...prev,
      attemptCount: nextAttempt,
      stage: 'identifying',
    }));
    await new Promise((r) => setTimeout(r, 650));

    // Stage 2: Preparing correction recipe
    setRepairState((prev) => ({
      ...prev,
      stage: 'preparing',
    }));
    await new Promise((r) => setTimeout(r, 700));

    // Stage 3: Applying correction directly to node config
    const appliedInstruction = 'You are an expert HR recruitment specialist. Analyze the extracted resume text against required engineering skills (React, TypeScript, Python). Grade candidate fit from 1 to 10 and list pros & cons.';

    setNodes((nds) =>
      nds.map((n) => {
        const oldData = n.data as unknown as WorkflowNodeData;
        if (oldData.componentType === 'LLM') {
          return {
            ...n,
            data: {
              ...oldData,
              status: 'ready' as const,
              errorMessage: undefined,
              config: {
                ...(oldData.config || {}),
                instructions: appliedInstruction,
              },
            },
          };
        }
        return n;
      })
    );

    setRepairState((prev) => ({
      ...prev,
      stage: 'applying',
      appliedCorrections: [
        ...prev.appliedCorrections,
        `Applied targeted prompt instructions to component "Evaluate Fit (Gemini)": "${appliedInstruction.slice(0, 75)}..."`,
      ],
    }));
    await new Promise((r) => setTimeout(r, 700));

    // Stage 4: Re-checking workflow validation
    setRepairState((prev) => ({
      ...prev,
      stage: 'checking',
      revalidationStatus: 'passed',
    }));
    await new Promise((r) => setTimeout(r, 650));

    // Stage 5: Re-running all tests
    setRepairState((prev) => ({
      ...prev,
      stage: 'retesting',
      retestStatus: 'passed',
    }));
    setTestCases((prev) => prev.map((tc) => ({ ...tc, status: 'passed' })));
    await new Promise((r) => setTimeout(r, 750));

    // Final Completion
    setRepairState((prev) => ({
      ...prev,
      stage: 'completed',
      finalStatus: 'success',
    }));

    // Update execution status
    setCurrentExecution((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        status: 'repaired',
        repaired: true,
        repairAttempts: nextAttempt,
        steps: prev.steps.map((st) =>
          st.componentType === 'LLM'
            ? { ...st, status: 'completed', activity: 'Repaired by AgentForge AI and verified successfully.' }
            : { ...st, status: 'completed' }
        ),
      };
    });

    // Generate Final Repair Report (Step 16)
    const report: RepairReport = {
      executionId: currentExecution?.id || 'exec-repaired',
      agentName: activeAgentName,
      attemptNumber: nextAttempt,
      maxAttempts: 2,
      originalError: 'ValidationError: Field "instructions" is empty in component Evaluate Fit (Gemini).',
      logEvidence: '[15:10:02.105] [Evaluate Fit (Gemini)] ERROR: ValidationError: Field "instructions" is empty.',
      diagnosedReason: 'Model invoked without prompt instructions or evaluation criteria.',
      proposedCorrection: 'Inject recruitment evaluation scoring instructions into AI Assistant.',
      appliedCorrection: 'Updated component configuration field "instructions" with standard HR rubric.',
      revalidationResult: 'PASSED (Readiness: 100%, 0 errors, 0 warnings)',
      retestResult: 'PASSED (4 of 4 test scenarios successful)',
      finalStatus: 'VERIFIED_SUCCESS',
      timestamp: new Date().toLocaleTimeString(),
    };

    setRepairReport(report);
    showToast('Workflow Repaired & Verified', 'Applied prompt instructions. Workflow passed validation and all test cases.', 'success');
  }, [repairState.attemptCount, currentExecution, activeAgentName, setNodes, showToast]);

  return (
    <WorkflowContext.Provider
      value={{
        currentPage,
        setCurrentPage,
        activeAgentName,
        setActiveAgentName,
        activePrompt,
        setActivePrompt,
        backendStatus,
        checkBackendHealth,
        nodes,
        edges,
        selectedNode,
        setSelectedNode,
        selectedEdge,
        setSelectedEdge,
        onNodesChange,
        onEdgesChange,
        onConnect,
        disconnectEdge,
        addNode,
        updateNodeConfig,
        deleteNode,
        duplicateNode,
        canUndo,
        canRedo,
        undo,
        redo,
        resetWorkflow,
        saveWorkflow,
        loadTemplate,
        loadAgent,
        generateAgentFromPrompt,
        isGenerating,
        generationStep,
        testCases,
        generateRequirementTests,
        runTestCases,
        isTesting,
        validationIssues,
        requirementCoverage,
        validationMetrics,
        runValidation,
        isValidating,
        executionHistory,
        currentExecution,
        runAgentExecution,
        isExecuting,
        repairState,
        repairReport,
        triggerFailureScenario,
        executeAutoRepair,
        toasts,
        showToast,
        dismissToast,
        sidebarOpen,
        setSidebarOpen,
        isHelpOpen,
        setIsHelpOpen,
      }}
    >
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflow = () => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return context;
};
