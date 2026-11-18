import React, { useState } from 'react';
import {
  Layers,
  Search,
  Plus,
  Play,
  Clock,
  Sparkles,
  ArrowRight,
  MoreVertical,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { RECENT_AGENTS } from '../../data/mockData';
import { AgentSummary } from '../../types';

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
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
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
          <p className="text-sm text-[#8D8D8D]">
            Manage, inspect, run, and configure all autonomous workflows you've constructed.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('create-agent')}
          className="px-5 py-2.5 rounded-full bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs sm:text-sm font-semibold shadow-sm transition-all flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Build New Agent</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 bg-[#F1F0EE] p-1 rounded-2xl w-full sm:w-auto">
          {(['All', 'Ready', 'Active', 'Needs Review'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                statusFilter === st
                  ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                  : 'text-[#8D8D8D] hover:text-[#111111]'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-[#8D8D8D] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents..."
            className="w-full text-xs text-[#111111] placeholder:text-[#8D8D8D] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
          />
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle hover:shadow-card hover:border-[#CF8047]/40 transition-all flex flex-col justify-between group space-y-4"
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

                <span className="text-[11px] text-[#8D8D8D] flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {agent.lastUpdated}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-base text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                  {agent.name}
                </h3>
                <p className="text-xs text-[#8D8D8D] mt-1 leading-relaxed line-clamp-2">
                  {agent.description}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#E6E5E2] text-center">
                <div className="p-2 rounded-xl bg-[#F1F0EE]/60">
                  <span className="text-[10px] text-[#8D8D8D] block">Components</span>
                  <span className="font-bold text-xs text-[#111111]">{agent.nodesCount}</span>
                </div>
                <div className="p-2 rounded-xl bg-[#F1F0EE]/60">
                  <span className="text-[10px] text-[#8D8D8D] block">Total Runs</span>
                  <span className="font-bold text-xs text-[#111111]">{agent.runsCount}</span>
                </div>
                <div className="p-2 rounded-xl bg-[#F1F0EE]/60">
                  <span className="text-[10px] text-[#8D8D8D] block">Success Rate</span>
                  <span className="font-bold text-xs text-emerald-700">{agent.successRate}</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <button
                onClick={() => loadAgent(agent)}
                className="w-full py-2.5 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Open in Workflow Studio</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

