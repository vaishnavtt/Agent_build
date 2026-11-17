import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Position,
  Handle,
  BackgroundVariant,
} from '@xyflow/react';
import {
  FileInput,
  Bot,
  Wrench,
  FileOutput,
  Play,
  Cpu,
} from 'lucide-react';

// Custom node rendering component to demonstrate React Flow custom nodes
const CustomWorkflowNode = ({ data }: { data: { label: string; typeName: string; icon: string; subtitle: string; color: string } }) => {
  const getIcon = () => {
    switch (data.icon) {
      case 'FileInput':
        return <FileInput className="w-4 h-4 text-emerald-400" />;
      case 'Bot':
        return <Bot className="w-4 h-4 text-indigo-400" />;
      case 'Wrench':
        return <Wrench className="w-4 h-4 text-amber-400" />;
      case 'FileOutput':
        return <FileOutput className="w-4 h-4 text-purple-400" />;
      default:
        return <Cpu className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className={`px-4 py-3 rounded-xl border ${data.color} bg-slate-900/90 shadow-lg backdrop-blur-md min-w-[180px]`}>
      <Handle type="target" position={Position.Left} className="!bg-indigo-500 !w-2.5 !h-2.5" />
      <div className="flex items-center gap-2 mb-1">
        <div className="p-1 rounded-md bg-slate-800/80">{getIcon()}</div>
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{data.typeName}</span>
      </div>
      <div className="text-sm font-medium text-slate-100">{data.label}</div>
      <div className="text-[11px] text-slate-400 mt-0.5">{data.subtitle}</div>
      <Handle type="source" position={Position.Right} className="!bg-indigo-500 !w-2.5 !h-2.5" />
    </div>
  );
};

export const WorkflowCanvasPreview = () => {
  const nodeTypes = useMemo(() => ({ workflowNode: CustomWorkflowNode }), []);

  const initialNodes: Node[] = [
    {
      id: '1',
      type: 'workflowNode',
      position: { x: 40, y: 120 },
      data: {
        typeName: 'Input',
        label: 'User Query',
        subtitle: 'Natural language input',
        icon: 'FileInput',
        color: 'border-emerald-500/40 hover:border-emerald-400',
      },
    },
    {
      id: '2',
      type: 'workflowNode',
      position: { x: 280, y: 80 },
      data: {
        typeName: 'LLM',
        label: 'Gemini 1.5 Pro',
        subtitle: 'Intent parser & planner',
        icon: 'Bot',
        color: 'border-indigo-500/40 hover:border-indigo-400',
      },
    },
    {
      id: '3',
      type: 'workflowNode',
      position: { x: 520, y: 80 },
      data: {
        typeName: 'Tool',
        label: 'Web Search Tool',
        subtitle: 'Live API retrieval',
        icon: 'Wrench',
        color: 'border-amber-500/40 hover:border-amber-400',
      },
    },
    {
      id: '4',
      type: 'workflowNode',
      position: { x: 760, y: 120 },
      data: {
        typeName: 'Output',
        label: 'Final Response',
        subtitle: 'Synthesized report',
        icon: 'FileOutput',
        color: 'border-purple-500/40 hover:border-purple-400',
      },
    },
  ];

  const initialEdges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#6366f1', strokeWidth: 2 } },
    { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#6366f1', strokeWidth: 2 } },
    { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#a855f7', strokeWidth: 2 } },
  ];

  return (
    <div className="relative w-full h-[380px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
      <div className="absolute top-3 left-4 z-10 flex items-center gap-3">
        <span className="flex h-2.5 w-2.5 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <span className="text-xs font-medium text-slate-300">Live Visual Canvas Preview (React Flow)</span>
      </div>

      <div className="absolute top-3 right-4 z-10">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
          <Play className="w-3 h-3 fill-indigo-400" />
          Interactive Canvas Demo
        </span>
      </div>

      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        nodeTypes={nodeTypes}
        fitView
        className="bg-slate-950"
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300 fill-slate-300" />
        <MiniMap
          nodeColor="#4f46e5"
          maskColor="rgba(15, 23, 42, 0.7)"
          className="!bg-slate-900 !border-slate-800 rounded-lg overflow-hidden"
        />
      </ReactFlow>
    </div>
  );
};

