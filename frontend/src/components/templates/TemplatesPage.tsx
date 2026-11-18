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
import { LiquidButton } from '../common/LiquidButton';

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
    <div className="max-w-6xl mx-auto space-y-8 pb-12 select-none">
      {/* Header */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Boxes className="w-3.5 h-3.5" />
          <span>Ready-Made Templates</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Agent Templates
        </h1>
        <p className="text-sm text-[#777777]">
          Pre-built visual workflows you can launch or customize in one click.
        </p>
      </div>

      {/* Filter Tabs & Search */}
      <div className="p-4 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 bg-[#F7F6F4] p-1 rounded-2xl border border-[#EAE8E5]">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#EAE8E5]'
                  : 'text-[#777777] hover:text-[#111111]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-[#777777] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full text-xs text-[#111111] placeholder:text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl pl-8 pr-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] transition-all"
          />
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredTemplates.map((tpl) => (
          <div
            key={tpl.id}
            className="p-7 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 transition-all flex flex-col justify-between space-y-5"
          >
            <div className="space-y-3.5">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-2xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#F7F6F4] text-[#777777] border border-[#EAE8E5]">
                  {tpl.category}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-lg text-[#111111]">{tpl.name}</h3>
                <p className="text-xs text-[#777777] mt-1 leading-relaxed">
                  {tpl.description}
                </p>
              </div>

              {/* Sample Prompt Preview */}
              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <span className="text-[10px] font-bold uppercase text-[#777777] tracking-wider">
                  Initial Natural Language Request
                </span>
                <p className="text-xs text-[#111111] italic leading-relaxed">
                  "{tpl.samplePrompt}"
                </p>
              </div>

              {/* Component Tags */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] text-[#777777] font-medium mr-1">Uses:</span>
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

            <div className="pt-3 border-t border-[#EAE8E5] flex items-center justify-between">
              <span className="text-xs text-[#777777]">
                {tpl.componentCount} connected components
              </span>

              <LiquidButton
                variant="primary"
                size="sm"
                onClick={() => loadTemplate(tpl)}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                glow
              >
                Use Template
              </LiquidButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
