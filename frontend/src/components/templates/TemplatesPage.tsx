import React, { useState } from 'react';
import {
  Boxes,
  Search,
  ArrowRight,
  FileText,
  Sparkles,
  Bot,
  Layers,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { SAMPLE_TEMPLATES } from '../../data/mockData';
import { AgentTemplate } from '../../types';

export const TemplatesPage: React.FC = () => {
  const { loadTemplate, setCurrentPage } = useWorkflow();

  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const categories = ['All', 'HR & Recruitment', 'Finance & Accounts', 'Knowledge & Research', 'Productivity'];

  const filteredTemplates = SAMPLE_TEMPLATES.filter((tpl) => {
    const matchesCategory = selectedCategory === 'All' || tpl.category === selectedCategory;
    const matchesSearch =
      tpl.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tpl.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Boxes className="w-3.5 h-3.5" />
          <span>Recipe Library</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Agent Templates
        </h1>
        <p className="text-sm text-[#8D8D8D]">
          Pre-built, battle-tested visual workflows ready to customize or deploy immediately.
        </p>
      </div>

      {/* Filter Tabs & Search */}
      <div className="p-4 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 bg-[#F1F0EE] p-1 rounded-2xl">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                  : 'text-[#8D8D8D] hover:text-[#111111]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-[#8D8D8D] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full text-xs text-[#111111] placeholder:text-[#8D8D8D] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
          />
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredTemplates.map((tpl) => (
          <div
            key={tpl.id}
            className="p-7 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle hover:shadow-card hover:border-[#CF8047]/40 transition-all flex flex-col justify-between space-y-5"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-2xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#F1F0EE] text-[#8D8D8D]">
                  {tpl.category}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-lg text-[#111111]">{tpl.name}</h3>
                <p className="text-xs text-[#8D8D8D] mt-1 leading-relaxed">
                  {tpl.description}
                </p>
              </div>

              {/* Sample Prompt Preview */}
              <div className="p-3.5 rounded-2xl bg-[#F1F0EE]/60 border border-[#E6E5E2] space-y-1">
                <span className="text-[10px] font-bold uppercase text-[#8D8D8D]">
                  Initial Prompt
                </span>
                <p className="text-xs text-[#111111] italic leading-relaxed">
                  "{tpl.samplePrompt}"
                </p>
              </div>

              {/* Component Tags */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] text-[#8D8D8D] font-medium mr-1">Includes:</span>
                {tpl.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-[#E6E5E2] flex items-center justify-between">
              <span className="text-xs text-[#8D8D8D]">
                {tpl.componentCount} connected components
              </span>

              <button
                onClick={() => loadTemplate(tpl)}
                className="px-5 py-2.5 rounded-full bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs font-bold shadow-sm transition-all flex items-center gap-2"
              >
                <span>Use Template</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

