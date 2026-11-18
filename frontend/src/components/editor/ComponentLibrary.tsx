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
  Info,
  Sparkles,
} from 'lucide-react';
import { ComponentType } from '../../types';
import { useWorkflow } from '../../context/WorkflowContext';

interface UserFriendlyComponent {
  type: ComponentType;
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

  // Exactly the 7 canonical components with plain English labels and explanations
  const components: UserFriendlyComponent[] = [
    {
      type: 'Input',
      title: 'Input',
      explanation: 'Receives information from you.',
      icon: FileInput,
      badgeBg: 'bg-emerald-50',
      badgeBorder: 'border-emerald-200',
      badgeColor: 'text-emerald-700',
    },
    {
      type: 'Document Reader',
      title: 'PDF Reader',
      explanation: 'Reads information from PDF documents.',
      icon: FileText,
      badgeBg: 'bg-amber-50',
      badgeBorder: 'border-amber-200',
      badgeColor: 'text-amber-800',
    },
    {
      type: 'LLM',
      title: 'AI Assistant',
      explanation: 'Understands information and generates responses.',
      icon: Bot,
      badgeBg: 'bg-[#FAF5F1]',
      badgeBorder: 'border-[#CF8047]/30',
      badgeColor: 'text-[#B15F2C]',
    },
    {
      type: 'Tool',
      title: 'Tool',
      explanation: 'Performs a specific action.',
      icon: Wrench,
      badgeBg: 'bg-teal-50',
      badgeBorder: 'border-teal-200',
      badgeColor: 'text-teal-700',
    },
    {
      type: 'Condition',
      title: 'Decision',
      explanation: 'Chooses what happens next.',
      icon: GitFork,
      badgeBg: 'bg-blue-50',
      badgeBorder: 'border-blue-200',
      badgeColor: 'text-blue-700',
    },
    {
      type: 'Human Approval',
      title: 'Human Approval',
      explanation: 'Waits for your confirmation.',
      icon: UserCheck,
      badgeBg: 'bg-purple-50',
      badgeBorder: 'border-purple-200',
      badgeColor: 'text-purple-700',
    },
    {
      type: 'Output',
      title: 'Output',
      explanation: 'Shows the final result.',
      icon: FileOutput,
      badgeBg: 'bg-[#F7F6F4]',
      badgeBorder: 'border-[#EAE8E5]',
      badgeColor: 'text-[#111111]',
    },
  ];

  const filteredComponents = components.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.explanation.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const onDragStart = (event: React.DragEvent, nodeType: ComponentType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-72 bg-white/90 backdrop-blur-xl border-r border-[#EAE8E5] flex flex-col h-full overflow-hidden select-none">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#EAE8E5] space-y-2.5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-[#111111]">What can your agent use?</h3>
            <p className="text-[11px] text-[#777777]">Drag into workflow or click Add</p>
          </div>
          <span className="text-[10px] font-bold text-[#B15F2C] bg-[#FAF5F1] px-2 py-0.5 rounded-full border border-[#CF8047]/30">
            {components.length} Items
          </span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#777777] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search components..."
            className="w-full text-xs text-[#111111] placeholder:text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-white transition-all shadow-subtle"
          />
        </div>
      </div>

      {/* Component Cards List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredComponents.map((comp) => {
          const Icon = comp.icon;
          return (
            <div
              key={comp.type}
              draggable
              onDragStart={(e) => onDragStart(e, comp.type)}
              className="p-3 rounded-2xl bg-white border border-[#EAE8E5] hover:border-[#CF8047]/50 shadow-subtle hover:shadow-card cursor-grab active:cursor-grabbing transition-all space-y-1 group active:scale-[0.99]"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-xl border flex items-center justify-center flex-shrink-0 ${comp.badgeBg} ${comp.badgeBorder}`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${comp.badgeColor}`} />
                  </div>
                  <div>
                    <h4 className="font-bold text-xs text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                      {comp.title}
                    </h4>
                  </div>
                </div>

                <button
                  onClick={() => addNode(comp.type)}
                  className="w-6 h-6 rounded-lg bg-[#F7F6F4] hover:bg-[#B15F2C] hover:text-white text-[#777777] border border-[#EAE8E5] hover:border-[#B15F2C] flex items-center justify-center transition-all"
                  title={`Add ${comp.title} to workflow`}
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              <p className="text-[11px] text-[#777777] leading-relaxed pl-9">
                {comp.explanation}
              </p>
            </div>
          );
        })}
      </div>

      {/* Helper Footer */}
      <div className="p-3 border-t border-[#EAE8E5] bg-[#F7F6F4]/60 text-[11px] text-[#777777] flex items-center gap-2">
        <Info className="w-3.5 h-3.5 text-[#B15F2C] flex-shrink-0" />
        <span>Connect ports on cards to link data flow</span>
      </div>
    </div>
  );
};
