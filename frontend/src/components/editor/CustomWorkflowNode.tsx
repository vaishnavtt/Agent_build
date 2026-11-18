import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import {
  FileInput,
  Bot,
  FileText,
  Wrench,
  GitFork,
  UserCheck,
  FileOutput,
  Cpu,
  Trash2,
  Copy,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { WorkflowNodeData, ComponentType } from '../../types';
import { useWorkflow } from '../../context/WorkflowContext';

const getDisplayTitle = (type: ComponentType): string => {
  switch (type) {
    case 'Input':
      return 'Input';
    case 'Document Reader':
      return 'PDF Reader';
    case 'LLM':
      return 'AI Assistant';
    case 'Condition':
      return 'Decision';
    case 'Human Approval':
      return 'Human Approval';
    case 'Tool':
      return 'Tool';
    case 'Output':
      return 'Output';
    default:
      return type;
  }
};

const getNodeIcon = (type: ComponentType) => {
  switch (type) {
    case 'Input':
      return <FileInput className="w-4 h-4 text-emerald-700" />;
    case 'Document Reader':
      return <FileText className="w-4 h-4 text-amber-800" />;
    case 'LLM':
      return <Bot className="w-4 h-4 text-[#B15F2C]" />;
    case 'Condition':
      return <GitFork className="w-4 h-4 text-blue-700" />;
    case 'Human Approval':
      return <UserCheck className="w-4 h-4 text-purple-700" />;
    case 'Tool':
      return <Wrench className="w-4 h-4 text-teal-700" />;
    case 'Output':
      return <FileOutput className="w-4 h-4 text-[#111111]" />;
    default:
      return <Cpu className="w-4 h-4 text-[#777777]" />;
  }
};

const getNodeTypeBadge = (type: ComponentType) => {
  switch (type) {
    case 'Input':
      return { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200' };
    case 'Document Reader':
      return { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' };
    case 'LLM':
      return { bg: 'bg-[#FAF5F1]', text: 'text-[#B15F2C]', border: 'border-[#CF8047]/30' };
    case 'Condition':
      return { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200' };
    case 'Human Approval':
      return { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200' };
    case 'Tool':
      return { bg: 'bg-teal-50', text: 'text-teal-800', border: 'border-teal-200' };
    case 'Output':
      return { bg: 'bg-[#F7F6F4]', text: 'text-[#111111]', border: 'border-[#EAE8E5]' };
    default:
      return { bg: 'bg-[#F7F6F4]', text: 'text-[#777777]', border: 'border-[#EAE8E5]' };
  }
};

export const CustomWorkflowNode: React.FC<NodeProps> = memo(({ id, data, selected }) => {
  const nodeData = data as unknown as WorkflowNodeData;
  const { deleteNode, duplicateNode } = useWorkflow();

  const isInput = nodeData.componentType === 'Input';
  const isOutput = nodeData.componentType === 'Output';
  const isCondition = nodeData.componentType === 'Condition';

  const badge = getNodeTypeBadge(nodeData.componentType);
  const displayTitle = getDisplayTitle(nodeData.componentType);

  return (
    <div
      className={`w-64 rounded-2xl bg-[#FFFFFF] border transition-all duration-200 select-none group ${
        selected
          ? 'border-[#B15F2C] shadow-elevated ring-2 ring-[#B15F2C]/15'
          : nodeData.status === 'failed'
          ? 'border-rose-400 shadow-card bg-rose-50/20 ring-2 ring-rose-300/30'
          : nodeData.status === 'executing'
          ? 'border-amber-400 shadow-card bg-amber-50/20 ring-1 ring-amber-400/30'
          : 'border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40'
      }`}
    >
      {/* Target Connection Handle (Left) */}
      {!isInput && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3.5 !h-3.5 !-left-2 !bg-[#FFFFFF] !border-2 !border-[#B15F2C] hover:!scale-125 transition-all shadow-subtle"
        />
      )}

      {/* Header */}
      <div className="p-3.5 pb-2.5 flex items-center justify-between border-b border-[#EAE8E5]">
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-xl ${badge.bg} border ${badge.border} flex items-center justify-center flex-shrink-0 shadow-subtle`}>
            {getNodeIcon(nodeData.componentType)}
          </div>
          <span className={`text-[10px] font-bold tracking-tight px-1.5 py-0.5 rounded-md ${badge.bg} ${badge.text}`}>
            {displayTitle}
          </span>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-1.5">
          {nodeData.status === 'executing' && (
            <span className="flex items-center gap-1 text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full font-semibold border border-amber-200">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
              Running
            </span>
          )}
          {nodeData.status === 'success' && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-semibold border border-emerald-200">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Passed
            </span>
          )}
          {nodeData.status === 'failed' && (
            <span className="flex items-center gap-1 text-[10px] text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full font-semibold border border-rose-200">
              <AlertCircle className="w-3 h-3 text-rose-600" />
              Needs Fix
            </span>
          )}
          {nodeData.status === 'ready' && (
            <span className="text-[10px] text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] px-2 py-0.5 rounded-full font-medium">
              Ready
            </span>
          )}
        </div>
      </div>

      {/* Body: Label & Details */}
      <div className="p-3.5 space-y-1.5">
        <h4 className="font-bold text-xs text-[#111111] leading-tight group-hover:text-[#B15F2C] transition-colors truncate">
          {nodeData.label}
        </h4>
        <p className="text-[11px] text-[#777777] line-clamp-2 leading-relaxed">
          {nodeData.description}
        </p>

        {/* Error message callout if node failed */}
        {nodeData.errorMessage && (
          <div className="mt-2 p-2 rounded-xl bg-rose-50 border border-rose-200 text-[10px] text-rose-800 flex items-start gap-1.5">
            <AlertCircle className="w-3 h-3 text-rose-600 mt-0.5 flex-shrink-0" />
            <span>{nodeData.errorMessage}</span>
          </div>
        )}
      </div>

      {/* Node Mini Footer / Action Toolbar on Hover */}
      <div className="px-3.5 py-2 bg-[#F7F6F4] border-t border-[#EAE8E5] rounded-b-2xl flex items-center justify-between text-[10px] text-[#777777]">
        <span className="truncate max-w-[120px] font-medium">
          {nodeData.config?.model || nodeData.config?.inputType || 'Configured'}
        </span>

        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              duplicateNode(id);
            }}
            title="Duplicate component"
            className="p-1 rounded-md hover:bg-[#FFFFFF] hover:text-[#111111] transition-colors"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteNode(id);
            }}
            title="Delete component"
            className="p-1 rounded-md hover:bg-rose-50 hover:text-rose-600 transition-colors"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Source Connection Handles (Right) */}
      {!isOutput && !isCondition && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3.5 !h-3.5 !-right-2 !bg-[#FFFFFF] !border-2 !border-[#B15F2C] hover:!scale-125 transition-all shadow-subtle"
        />
      )}

      {/* Special Branch Handles for Decision (Condition) Node */}
      {isCondition && (
        <>
          <Handle
            id="true"
            type="source"
            position={Position.Right}
            style={{ top: '38%' }}
            className="!w-3.5 !h-3.5 !-right-2 !bg-emerald-500 !border-2 !border-white hover:!scale-125 transition-all shadow-subtle"
            title="True path"
          />
          <Handle
            id="false"
            type="source"
            position={Position.Right}
            style={{ top: '68%' }}
            className="!w-3.5 !h-3.5 !-right-2 !bg-rose-500 !border-2 !border-white hover:!scale-125 transition-all shadow-subtle"
            title="False path"
          />
        </>
      )}
    </div>
  );
});
