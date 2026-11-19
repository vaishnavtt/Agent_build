import React, { useState } from 'react';
import {
  Search,
  Plus,
  FileInput,
  Bot,
  FileText,
  Wrench,
  GitFork,
  UserCheck,
  FileOutput,
  Sparkles,
  GripVertical,
} from 'lucide-react';
import { ComponentType } from '../../types';
import { useWorkflow } from '../../context/WorkflowContext';

interface FriendlyBuildingBlock {
  type: ComponentType;
  actionTag: string; // START, READ, THINK, DECIDE, DO, APPROVE, FINISH
  title: string;
  explanation: string;
  icon: React.ElementType;
  badgeBg: string;
  badgeBorder: string;
  badgeColor: string;
}

export const ComponentLibrary: React.FC = () => {
  const { addNode } = useWorkflow();
  const [searchQuery, setSearchQuery] = useState('');

  // 7 Canonical Building Blocks mapped to friendly beginner concepts (Phase 7)
  const blocks: FriendlyBuildingBlock[] = [
    {
      type: 'Input',
      actionTag: 'START',
      title: 'Start',
      explanation: 'Where does the information come from?',
      icon: FileInput,
      badgeBg: 'bg-emerald-50',
      badgeBorder: 'border-emerald-200',
      badgeColor: 'text-emerald-700',
    },
    {
      type: 'Document Reader',
      actionTag: 'READ',
      title: 'Read Document',
      explanation: 'Read a document or resume.',
      icon: FileText,
      badgeBg: 'bg-amber-50',
      badgeBorder: 'border-amber-200',
      badgeColor: 'text-amber-800',
    },
    {
      type: 'LLM',
      actionTag: 'THINK',
      title: 'Understand',
      explanation: 'Understand the information.',
      icon: Bot,
      badgeBg: 'bg-[#FAF5F1]',
      badgeBorder: 'border-[#CF8047]/30',
      badgeColor: 'text-[#B15F2C]',
    },
    {
      type: 'Condition',
      actionTag: 'DECIDE',
      title: 'Decide',
      explanation: 'Choose what happens next.',
      icon: GitFork,
      badgeBg: 'bg-blue-50',
      badgeBorder: 'border-blue-200',
      badgeColor: 'text-blue-700',
    },
    {
      type: 'Tool',
      actionTag: 'DO',
      title: 'Do Action',
      explanation: 'Perform an action (sync data, email).',
      icon: Wrench,
      badgeBg: 'bg-teal-50',
      badgeBorder: 'border-teal-200',
      badgeColor: 'text-teal-700',
    },
    {
      type: 'Human Approval',
      actionTag: 'APPROVE',
      title: 'Ask Me',
      explanation: 'Ask me before continuing.',
      icon: UserCheck,
      badgeBg: 'bg-purple-50',
      badgeBorder: 'border-purple-200',
      badgeColor: 'text-purple-700',
    },
    {
      type: 'Output',
      actionTag: 'FINISH',
      title: 'Show Result',
      explanation: 'Show me the result.',
      icon: FileOutput,
      badgeBg: 'bg-[#F7F6F4]',
      badgeBorder: 'border-[#EAE8E5]',
      badgeColor: 'text-[#111111]',
    },
  ];

  const filteredBlocks = blocks.filter(
    (b) =>
      b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.actionTag.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.explanation.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const onDragStart = (event: React.DragEvent, type: ComponentType) => {
    event.dataTransfer.setData('application/reactflow', type);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-72 bg-[#FFFFFF] border-r border-[#EAE8E5] flex flex-col h-full overflow-hidden select-none z-10 shadow-subtle">
      {/* Header */}
      <div className="p-4 border-b border-[#EAE8E5] bg-[#FFFFFF] space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="font-extrabold text-sm text-[#111111] tracking-tight">
            Building Blocks
          </h3>
          <span className="text-[10px] font-bold uppercase tracking-wider bg-[#FAF5F1] text-[#B15F2C] px-2 py-0.5 rounded-full border border-[#CF8047]/30">
            7 Blocks
          </span>
        </div>
        <p className="text-[11px] text-[#777777] leading-relaxed">
          Drag blocks onto the canvas or tap <strong>+</strong> to add.
        </p>

        {/* Quick Filter */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#777777] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search blocks..."
            className="w-full text-xs text-[#111111] placeholder:text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Building Blocks List with Soft 3D Tactile Cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredBlocks.map((block) => {
          const Icon = block.icon;
          return (
            <div
              key={block.type}
              draggable
              onDragStart={(e) => onDragStart(e, block.type)}
              className="p-3 rounded-2xl bg-white border border-[#EAE8E5] shadow-[0_2px_0_#EAE8E5,0_4px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_4px_0_#E5E2DC,0_8px_18px_rgba(0,0,0,0.05)] hover:-translate-y-0.5 active:translate-y-0.5 transition-all duration-150 cursor-grab active:cursor-grabbing group relative"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-xl ${block.badgeBg} border ${block.badgeBorder} flex items-center justify-center flex-shrink-0 mt-0.5 shadow-subtle`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${block.badgeColor}`} />
                  </div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded ${block.badgeBg} ${block.badgeColor} border ${block.badgeBorder}`}>
                        {block.actionTag}
                      </span>
                      <h4 className="font-bold text-xs text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                        {block.title}
                      </h4>
                    </div>
                    <p className="text-[10px] text-[#777777] leading-tight">
                      {block.explanation}
                    </p>
                  </div>
                </div>

                {/* Instant Add Button */}
                <button
                  type="button"
                  onClick={() => addNode(block.type)}
                  title={`Add ${block.title} to workflow`}
                  className="p-1 rounded-lg text-[#777777] hover:text-[#B15F2C] hover:bg-[#FAF5F1] transition-colors flex-shrink-0 border border-transparent hover:border-[#CF8047]/30"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Drag indicator hint on hover */}
              <div className="absolute right-2 bottom-1.5 opacity-0 group-hover:opacity-60 transition-opacity">
                <GripVertical className="w-3 h-3 text-[#777777]" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Beginner Help Footer in Library */}
      <div className="p-3 border-t border-[#EAE8E5] bg-[#F7F6F4]/60 text-[10px] text-[#777777] flex items-center gap-1.5">
        <Sparkles className="w-3.5 h-3.5 text-[#B15F2C] flex-shrink-0" />
        <span>Connect steps in order from START to FINISH.</span>
      </div>
    </div>
  );
};
