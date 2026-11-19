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

interface BlockPresentation {
  tag: string;
  friendlyTitle: string;
  icon: React.ElementType;
  badgeBg: string;
  badgeBorder: string;
  badgeColor: string;
}

const getBlockPresentation = (type: ComponentType): BlockPresentation => {
  switch (type) {
    case 'Input':
      return {
        tag: 'START',
        friendlyTitle: 'Start Input',
        icon: FileInput,
        badgeBg: 'bg-emerald-50',
        badgeBorder: 'border-emerald-200',
        badgeColor: 'text-emerald-700',
      };
    case 'Document Reader':
      return {
        tag: 'READ',
        friendlyTitle: 'Read Document',
        icon: FileText,
        badgeBg: 'bg-amber-50',
        badgeBorder: 'border-amber-200',
        badgeColor: 'text-amber-800',
      };
    case 'LLM':
      return {
        tag: 'THINK',
        friendlyTitle: 'Understand & Score',
        icon: Bot,
        badgeBg: 'bg-[#FAF5F1]',
        badgeBorder: 'border-[#CF8047]/30',
        badgeColor: 'text-[#B15F2C]',
      };
    case 'Condition':
      return {
        tag: 'DECIDE',
        friendlyTitle: 'Decide Next Step',
        icon: GitFork,
        badgeBg: 'bg-blue-50',
        badgeBorder: 'border-blue-200',
        badgeColor: 'text-blue-700',
      };
    case 'Tool':
      return {
        tag: 'DO',
        friendlyTitle: 'Perform Action',
        icon: Wrench,
        badgeBg: 'bg-teal-50',
        badgeBorder: 'border-teal-200',
        badgeColor: 'text-teal-700',
      };
    case 'Human Approval':
      return {
        tag: 'APPROVE',
        friendlyTitle: 'Ask For Approval',
        icon: UserCheck,
        badgeBg: 'bg-purple-50',
        badgeBorder: 'border-purple-200',
        badgeColor: 'text-purple-700',
      };
    case 'Output':
      return {
        tag: 'FINISH',
        friendlyTitle: 'Deliver Result',
        icon: FileOutput,
        badgeBg: 'bg-[#F7F6F4]',
        badgeBorder: 'border-[#EAE8E5]',
        badgeColor: 'text-[#111111]',
      };
    default:
      return {
        tag: 'STEP',
        friendlyTitle: type,
        icon: Cpu,
        badgeBg: 'bg-[#F7F6F4]',
        badgeBorder: 'border-[#EAE8E5]',
        badgeColor: 'text-[#777777]',
      };
  }
};

export const CustomWorkflowNode: React.FC<NodeProps> = memo(({ id, data, selected }) => {
  const nodeData = data as unknown as WorkflowNodeData;
  const { deleteNode, duplicateNode } = useWorkflow();

  const isInput = nodeData.componentType === 'Input';
  const isOutput = nodeData.componentType === 'Output';
  const isCondition = nodeData.componentType === 'Condition';

  const block = getBlockPresentation(nodeData.componentType);
  const Icon = block.icon;

  return (
    <div
      className={`w-64 rounded-3xl bg-white border transition-all duration-200 select-none group relative ${
        selected
          ? 'border-[#B15F2C] shadow-[0_4px_0_#7F3B15,0_12px_28px_rgba(177,95,44,0.3)] ring-2 ring-[#B15F2C]/30 -translate-y-1'
          : nodeData.status === 'failed'
          ? 'border-rose-400 shadow-[0_3px_0_#991B1B,0_8px_20px_rgba(220,38,38,0.2)] bg-rose-50/20'
          : nodeData.status === 'executing'
          ? 'border-amber-400 shadow-[0_3px_0_#B45309,0_8px_20px_rgba(245,158,11,0.2)] bg-amber-50/20'
          : 'border-[#EAE8E5] shadow-[0_3px_0_#E5E2DC,0_8px_20px_rgba(0,0,0,0.04)] hover:shadow-[0_5px_0_#DDD9D2,0_14px_28px_rgba(0,0,0,0.07)] hover:-translate-y-0.5'
      }`}
    >
      {/* Target Connection Handle (Left) */}
      {!isInput && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-4 !h-4 !-left-2 !bg-white !border-2 !border-[#B15F2C] hover:!scale-125 transition-transform shadow-md"
          title="Connect input from previous step"
        />
      )}

      {/* Header with Friendly Tag & Status */}
      <div className="p-3.5 pb-2.5 flex items-center justify-between border-b border-[#EAE8E5]">
        <div className="flex items-center gap-2">
          <div
            className={`w-7 h-7 rounded-xl ${block.badgeBg} border ${block.badgeBorder} flex items-center justify-center flex-shrink-0 shadow-subtle`}
          >
            <Icon className={`w-3.5 h-3.5 ${block.badgeColor}`} />
          </div>
          <span
            className={`text-[9px] font-extrabold tracking-wider px-2 py-0.5 rounded-full ${block.badgeBg} ${block.badgeColor} border ${block.badgeBorder}`}
          >
            {block.tag}
          </span>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-1.5">
          {nodeData.status === 'executing' && (
            <span className="flex items-center gap-1 text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded-full font-bold border border-amber-200">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
              Running
            </span>
          )}
          {nodeData.status === 'success' && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full font-bold border border-emerald-200">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Passed
            </span>
          )}
          {nodeData.status === 'failed' && (
            <span className="flex items-center gap-1 text-[10px] text-rose-800 bg-rose-50 px-2 py-0.5 rounded-full font-bold border border-rose-200">
              <AlertCircle className="w-3 h-3 text-rose-600" />
              Needs Fix
            </span>
          )}
          {nodeData.status === 'ready' && (
            <span className="text-[10px] text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] px-2 py-0.5 rounded-full font-semibold">
              Ready
            </span>
          )}
        </div>
      </div>

      {/* Body: Title & Friendly Description */}
      <div className="p-3.5 space-y-1">
        <h4 className="font-extrabold text-xs text-[#111111] leading-tight group-hover:text-[#B15F2C] transition-colors truncate">
          {nodeData.label}
        </h4>
        <p className="text-[11px] text-[#777777] line-clamp-2 leading-relaxed">
          {nodeData.description}
        </p>

        {/* Error message callout if step failed */}
        {nodeData.errorMessage && (
          <div className="mt-2 p-2 rounded-xl bg-rose-50 border border-rose-200 text-[10px] text-rose-800 flex items-start gap-1.5 font-medium">
            <AlertCircle className="w-3 h-3 text-rose-600 mt-0.5 flex-shrink-0" />
            <span>{nodeData.errorMessage}</span>
          </div>
        )}
      </div>

      {/* Footer / Quick Actions Bar */}
      <div className="px-3.5 py-2 bg-[#F7F6F4] border-t border-[#EAE8E5] rounded-b-3xl flex items-center justify-between text-[10px] text-[#777777]">
        <span className="truncate max-w-[120px] font-semibold">
          {nodeData.config?.model || nodeData.config?.inputType || 'Configured'}
        </span>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              duplicateNode(id);
            }}
            title="Duplicate step"
            className="p-1 rounded-md hover:bg-white hover:text-[#111111] transition-colors shadow-none hover:shadow-subtle"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              deleteNode(id);
            }}
            title="Delete step"
            className="p-1 rounded-md hover:bg-rose-50 hover:text-rose-600 transition-colors"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Source Connection Handle (Right) */}
      {!isOutput && !isCondition && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-4 !h-4 !-right-2 !bg-white !border-2 !border-[#B15F2C] hover:!scale-125 transition-transform shadow-md"
          title="Connect to next step"
        />
      )}

      {/* Branch Handles for Decision Nodes */}
      {isCondition && (
        <>
          <Handle
            id="true"
            type="source"
            position={Position.Right}
            style={{ top: '38%' }}
            className="!w-4 !h-4 !-right-2 !bg-emerald-500 !border-2 !border-white hover:!scale-125 transition-transform shadow-md"
            title="If Yes / Meets Rule"
          />
          <Handle
            id="false"
            type="source"
            position={Position.Right}
            style={{ top: '68%' }}
            className="!w-4 !h-4 !-right-2 !bg-rose-500 !border-2 !border-white hover:!scale-125 transition-transform shadow-md"
            title="If No / Fails Rule"
          />
        </>
      )}
    </div>
  );
});
