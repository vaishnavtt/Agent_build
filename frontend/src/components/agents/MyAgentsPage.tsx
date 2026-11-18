import React, { useState } from 'react';
import {
  Layers,
  Search,
  Plus,
  Play,
  Clock,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { RECENT_AGENTS } from '../../data/mockData';
import { LiquidButton } from '../common/LiquidButton';

export const MyAgentsPage: React.FC = () => {
  const { loadAgent, setCurrentPage } = useWorkflow();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'All' | 'Ready' | 'Active' | 'Needs Review'>('All');

  const filteredAgents = RECENT_AGENTS.filter((agent) => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || agent.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12 select-none">
      {/* Heading & New Agent Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
            <Layers className="w-3.5 h-3.5" />
            <span>Workspace Agents</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight mt-1">
            My Agents
          </h1>
          <p className="text-sm text-[#777777]">
            Inspect, run, and configure all the AI assistants you've created.
          </p>
        </div>

        <LiquidButton
          variant="primary"
          size="md"
          onClick={() => setCurrentPage('create-agent')}
          icon={<Plus className="w-4 h-4" />}
          glow
        >
          Create New Agent
        </LiquidButton>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 bg-[#F7F6F4] p-1 rounded-2xl w-full sm:w-auto border border-[#EAE8E5]">
          {(['All', 'Ready', 'Active', 'Needs Review'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                statusFilter === st
                  ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#EAE8E5]'
                  : 'text-[#777777] hover:text-[#111111]'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-[#777777] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents..."
            className="w-full text-xs text-[#111111] placeholder:text-[#777777] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl pl-8 pr-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] transition-all"
          />
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 transition-all flex flex-col justify-between group space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span
                  className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                    agent.status === 'Ready'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : agent.status === 'Active'
                      ? 'bg-blue-50 text-blue-800 border border-blue-200'
                      : 'bg-amber-50 text-amber-800 border border-amber-200'
                  }`}
                >
                  {agent.status}
                </span>

                <span className="text-[11px] text-[#777777] flex items-center gap-1 font-medium">
                  <Clock className="w-3 h-3 text-[#777777]" />
                  {agent.lastUpdated}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-base text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                  {agent.name}
                </h3>
                <p className="text-xs text-[#777777] mt-1 leading-relaxed line-clamp-2">
                  {agent.description}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#EAE8E5] text-center">
                <div className="p-2 rounded-xl bg-[#F7F6F4] border border-[#EAE8E5]/60">
                  <span className="text-[10px] text-[#777777] block font-medium">Steps</span>
                  <span className="font-bold text-xs text-[#111111]">{agent.nodesCount}</span>
                </div>
                <div className="p-2 rounded-xl bg-[#F7F6F4] border border-[#EAE8E5]/60">
                  <span className="text-[10px] text-[#777777] block font-medium">Runs</span>
                  <span className="font-bold text-xs text-[#111111]">{agent.runsCount}</span>
                </div>
                <div className="p-2 rounded-xl bg-[#F7F6F4] border border-[#EAE8E5]/60">
                  <span className="text-[10px] text-[#777777] block font-medium">Success</span>
                  <span className="font-bold text-xs text-emerald-700">{agent.successRate}</span>
                </div>
              </div>
            </div>

            <div className="pt-2">
              <LiquidButton
                variant="secondary"
                size="md"
                onClick={() => loadAgent(agent)}
                className="w-full"
                icon={<Play className="w-3.5 h-3.5 fill-[#111111]" />}
              >
                Open in Canvas
              </LiquidButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
