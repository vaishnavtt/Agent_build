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
} from 'lucide-react';
import { COMPONENT_DEFINITIONS } from '../../data/mockData';
import { ComponentType } from '../../types';
import { useWorkflow } from '../../context/WorkflowContext';

const getComponentIcon = (type: ComponentType) => {
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
      return <FileOutput className="w-4 h-4 text-[#0A0A0A]" />;
  }
};

export const ComponentLibrary: React.FC = () => {
  const { addNode } = useWorkflow();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredComponents = COMPONENT_DEFINITIONS.filter(
    (c) =>
      c.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const onDragStart = (event: React.DragEvent, nodeType: ComponentType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-72 bg-[#FFFFFF] border-r border-[#E6E5E2] flex flex-col h-full overflow-hidden select-none">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#E6E5E2] space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-sm text-[#111111]">Components</h3>
          <span className="text-[10px] font-semibold text-[#8D8D8D] bg-[#F1F0EE] px-2 py-0.5 rounded-full">
            {COMPONENT_DEFINITIONS.length} Primitives
          </span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#8D8D8D] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search components..."
            className="w-full text-xs text-[#111111] placeholder:text-[#8D8D8D] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
          />
        </div>
      </div>

      {/* Component Cards List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold text-[#8D8D8D] uppercase tracking-wider px-1">
          <Info className="w-3 h-3 text-[#B15F2C]" />
          <span>Drag onto canvas or click +</span>
        </div>

        {filteredComponents.map((comp) => (
          <div
            key={comp.type}
            draggable
            onDragStart={(e) => onDragStart(e, comp.type)}
            className="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] hover:border-[#CF8047]/50 shadow-subtle hover:shadow-card cursor-grab active:cursor-grabbing transition-all space-y-1.5 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-xl border flex items-center justify-center ${comp.color}`}>
                  {getComponentIcon(comp.type)}
                </div>
                <div>
                  <h4 className="font-bold text-xs text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                    {comp.displayName}
                  </h4>
                  <span className="text-[9px] font-semibold uppercase text-[#8D8D8D]">
                    {comp.category}
                  </span>
                </div>
              </div>

              {/* Add to canvas button */}
              <button
                onClick={() => addNode(comp.type)}
                title="Add to canvas"
                className="w-6 h-6 rounded-lg bg-[#F1F0EE] hover:bg-[#B15F2C] text-[#8D8D8D] hover:text-white flex items-center justify-center transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>

            <p className="text-[11px] text-[#8D8D8D] leading-relaxed">
              {comp.description}
            </p>
          </div>
        ))}

        {filteredComponents.length === 0 && (
          <div className="p-6 text-center text-xs text-[#8D8D8D] space-y-1">
            <p>No components match "{searchQuery}"</p>
            <button
              onClick={() => setSearchQuery('')}
              className="text-[#B15F2C] font-semibold hover:underline"
            >
              Clear search
            </button>
          </div>
        )}
      </div>

      {/* Mini Helper Footer */}
      <div className="p-3 border-t border-[#E6E5E2] bg-[#FAF5F1] text-[11px] text-[#8D8D8D] flex items-start gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[#B15F2C] mt-1.5 flex-shrink-0" />
        <p>Connect output handles to input handles to chain data.</p>
      </div>
    </div>
  );
};

