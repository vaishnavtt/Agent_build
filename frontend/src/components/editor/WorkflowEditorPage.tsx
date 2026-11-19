import React, { useState, useRef, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  ReactFlowProvider,
  Node,
  Edge,
} from '@xyflow/react';
import {
  Save,
  Undo2,
  Redo2,
  Play,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  Edit2,
  Check,
  Info,
  ArrowLeft,
  MousePointerClick,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ComponentLibrary } from './ComponentLibrary';
import { ComponentSettings } from './ComponentSettings';
import { EditorBottomPanel } from './EditorBottomPanel';
import { CustomWorkflowNode } from './CustomWorkflowNode';
import { ComponentType } from '../../types';
import { ElevatedButton } from '../common/ElevatedButton';

const WorkflowEditorContent: React.FC = () => {
  const {
    activeAgentName,
    setActiveAgentName,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setSelectedNode,
    addNode,
    saveWorkflow,
    resetWorkflow,
    runValidation,
    isValidating,
    runAgentExecution,
    isExecuting,
    canUndo,
    canRedo,
    undo,
    redo,
    disconnectEdge,
    backendStatus,
    setCurrentPage,
  } = useWorkflow();

  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  // In-line title editing
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState(activeAgentName);

  const nodeTypes = useMemo(() => ({ customWorkflow: CustomWorkflowNode }), []);

  const handleTitleSubmit = () => {
    if (titleInput.trim()) {
      setActiveAgentName(titleInput.trim());
    }
    setIsEditingTitle(false);
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow') as ComponentType;
      if (!type) return;

      if (reactFlowWrapper.current && reactFlowInstance) {
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });
        addNode(type, position);
      } else {
        addNode(type);
      }
    },
    [reactFlowInstance, addNode]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
    },
    [setSelectedNode]
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      disconnectEdge(edge.id);
    },
    [disconnectEdge]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-white select-none">
      {/* 1. Top Friendly Studio Toolbar */}
      <div className="h-14 px-4 liquid-glass border-b border-[#EAE8E5] flex items-center justify-between z-10 shadow-subtle">
        {/* Left: Back button & Workflow Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentPage('dashboard')}
            className="p-1.5 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] transition-colors flex items-center gap-1.5 text-xs font-semibold"
            title="Return to Home"
          >
            <ArrowLeft className="w-4 h-4 text-[#777777]" />
            <span className="hidden sm:inline">Home</span>
          </button>

          <div className="h-4 w-px bg-[#EAE8E5] hidden sm:block" />

          {isEditingTitle ? (
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleTitleSubmit()}
                autoFocus
                className="text-sm font-bold text-[#111111] bg-[#F7F6F4] border border-[#B15F2C] rounded-lg px-2.5 py-1 focus:outline-none"
              />
              <button
                onClick={handleTitleSubmit}
                className="p-1 rounded bg-[#B15F2C] text-white"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div
              className="flex items-center gap-2 cursor-pointer group"
              onClick={() => {
                setTitleInput(activeAgentName);
                setIsEditingTitle(true);
              }}
            >
              <h2 className="text-sm font-extrabold text-[#111111] tracking-tight group-hover:text-[#B15F2C] transition-colors">
                {activeAgentName || 'Build Your Agent'}
              </h2>
              <Edit2 className="w-3 h-3 text-[#777777] opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="text-[10px] bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 px-2 py-0.5 rounded-full font-bold">
                {nodes.length} Steps
              </span>
            </div>
          )}
        </div>

        {/* Center/Right 3D Elevated Buttons */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Undo / Redo */}
          <div className="flex items-center border border-[#EAE8E5] rounded-xl bg-white p-0.5 shadow-subtle">
            <button
              onClick={undo}
              disabled={!canUndo}
              title="Undo last change"
              className="p-1.5 rounded-lg text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Undo2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={redo}
              disabled={!canRedo}
              title="Redo change"
              className="p-1.5 rounded-lg text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Redo2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Reset Template */}
          <button
            onClick={resetWorkflow}
            title="Reset to default building blocks"
            className="p-2 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] border border-[#EAE8E5] transition-colors shadow-subtle"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Save Workflow */}
          <ElevatedButton
            variant="secondary"
            size="sm"
            onClick={saveWorkflow}
            icon={<Save className="w-3.5 h-3.5 text-[#777777]" />}
          >
            <span className="hidden sm:inline">Save</span>
          </ElevatedButton>

          {/* Check My Agent */}
          <ElevatedButton
            variant="secondary"
            size="sm"
            onClick={() => runValidation()}
            loading={isValidating}
            loadingText="Checking..."
            icon={<ShieldCheck className="w-3.5 h-3.5 text-[#B15F2C]" />}
          >
            Check My Agent
          </ElevatedButton>

          {/* Prominent Run My Agent Button */}
          <ElevatedButton
            variant="primary"
            size="sm"
            onClick={() => runAgentExecution()}
            loading={isExecuting}
            loadingText="Running..."
            icon={<Play className="w-3.5 h-3.5 fill-white" />}
            glow
          >
            Run My Agent
          </ElevatedButton>
        </div>
      </div>

      {/* 2. Instruction Banner (Strictly Phase 7 Requirement) */}
      <div className="h-8 px-4 bg-[#FAF5F1] border-b border-[#CF8047]/20 flex items-center justify-between text-xs text-[#B15F2C] font-semibold">
        <div className="flex items-center gap-2">
          <MousePointerClick className="w-3.5 h-3.5 text-[#B15F2C]" />
          <span>Drag a building block into the middle to add a step. Connect the steps to show what happens next.</span>
        </div>
        <span className="text-[10px] text-[#777777] hidden md:inline">
          Click any connection line to remove it
        </span>
      </div>

      {/* 3. Main 3-Column Studio Layout:
          - Left: Building Blocks
          - Centre: Your Agent's Steps
          - Right: Customize This Step */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left: Building Blocks */}
        <ComponentLibrary />

        {/* Centre: Your Agent's Steps (React Flow Canvas) */}
        <div
          ref={reactFlowWrapper}
          className="flex-1 h-full relative bg-white"
          onDragOver={onDragOver}
          onDrop={onDrop}
        >
          {/* Subtle canvas tip badge */}
          <div className="absolute top-3 left-4 z-10 pointer-events-none">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full liquid-glass border border-[#EAE8E5] text-[11px] text-[#777777] shadow-glass font-medium">
              <Info className="w-3.5 h-3.5 text-[#B15F2C]" />
              <span>Center: Your Agent's Steps • Drag blocks from left panel</span>
            </span>
          </div>

          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[16, 16]}
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: '#B15F2C', strokeWidth: 2.5 },
            }}
            className="bg-white"
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1.3}
              color="#EAE8E5"
            />
            <Controls
              position="bottom-left"
              className="!bg-white !border-[#EAE8E5] !rounded-2xl !shadow-card"
            />
            <MiniMap
              nodeColor="#B15F2C"
              maskColor="rgba(247, 246, 244, 0.7)"
              position="bottom-right"
              className="!bg-white !border-[#EAE8E5] !rounded-2xl !shadow-card !bottom-12"
            />
          </ReactFlow>
        </div>

        {/* Right: Customize This Step */}
        <ComponentSettings />
      </div>

      {/* Bottom: Results, Tests, Activity & Problems Drawer */}
      <EditorBottomPanel />
    </div>
  );
};

export const WorkflowEditorPage: React.FC = () => {
  return (
    <ReactFlowProvider>
      <WorkflowEditorContent />
    </ReactFlowProvider>
  );
};
