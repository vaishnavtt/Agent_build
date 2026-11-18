import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Boxes,
  Play,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Clock,
  Layers,
  ChevronRight,
  ShieldCheck,
  Bot,
  Zap,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { RECENT_AGENTS, SAMPLE_TEMPLATES } from '../../data/mockData';
import { LiquidButton } from '../common/LiquidButton';

export const DashboardPage: React.FC = () => {
  const { setCurrentPage, generateAgentFromPrompt, loadTemplate, loadAgent, executionHistory } = useWorkflow();

  const [promptText, setPromptText] = useState('');

  const promptSuggestions = [
    'Create a resume evaluation assistant.',
    'Create an invoice processing assistant.',
    'Create a PDF question-answering assistant.',
    'Create a document summarization assistant.',
  ];

  const handleCreateAgent = () => {
    const finalPrompt = promptText.trim() || promptSuggestions[0];
    generateAgentFromPrompt(finalPrompt);
  };

  return (
    <div className="space-y-10 pb-16 max-w-6xl mx-auto">
      {/* 1. Header & Hero Intro */}
      <section className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Autonomous AI Agent Builder</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-[#111111] tracking-tight">
          Welcome to AgentForge AI
        </h1>
        <p className="text-sm sm:text-base text-[#777777]">
          Create intelligent AI assistants without writing code.
        </p>
      </section>

      {/* 2. Prominent Natural Language Input Card (Apple Liquid Glass) */}
      <section className="p-6 sm:p-7 rounded-3xl liquid-glass border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#B15F2C]">
            <Bot className="w-4 h-4" />
            <span>Describe Your AI Assistant</span>
          </div>
          <span className="text-[11px] font-semibold text-[#777777] bg-white/80 px-2.5 py-0.5 rounded-full border border-[#EAE8E5]">
            Plain English Instructions
          </span>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="What would you like your AI agent to do?"
            className="w-full text-base sm:text-lg text-[#111111] placeholder:text-[#777777]/60 bg-white/90 border border-[#EAE8E5] rounded-2xl p-4 sm:p-5 focus:outline-none focus:border-[#B15F2C] focus:bg-white shadow-subtle transition-all resize-none leading-relaxed"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-3">
            <LiquidButton
              variant="primary"
              size="md"
              onClick={handleCreateAgent}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
              glow
            >
              Create My Agent
            </LiquidButton>

            <LiquidButton
              variant="secondary"
              size="md"
              onClick={() => setCurrentPage('templates')}
              icon={<Boxes className="w-4 h-4 text-[#777777]" />}
            >
              Explore Templates
            </LiquidButton>
          </div>

          <span className="text-[11px] text-[#777777] hidden sm:inline">
            Tip: Click an example chip below to start instantly
          </span>
        </div>

        {/* Example Prompt Chips */}
        <div className="pt-3 border-t border-[#EAE8E5]/80">
          <p className="text-[11px] font-semibold text-[#777777] uppercase tracking-wider mb-2.5">
            Quick Examples:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {promptSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => setPromptText(suggestion)}
                className="text-left p-3 rounded-2xl bg-white/80 hover:bg-[#FAF5F1] border border-[#EAE8E5] hover:border-[#CF8047]/40 text-xs text-[#111111] transition-all flex items-center justify-between group shadow-subtle active:scale-[0.99]"
              >
                <span className="font-medium truncate mr-2">{suggestion}</span>
                <span className="text-[10px] text-[#B15F2C] opacity-0 group-hover:opacity-100 transition-opacity font-semibold flex items-center gap-0.5 whitespace-nowrap">
                  Use prompt →
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 3. B. Activity Overview (4 Clean Metric Cards) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-bold text-[#111111]">Activity Overview</h2>
          <span className="text-[11px] text-[#777777] bg-[#F7F6F4] px-2.5 py-0.5 rounded-full border border-[#EAE8E5]">
            Demo Simulation Metrics
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <div className="p-5 rounded-2xl bg-white border border-[#EAE8E5] shadow-card space-y-1 hover:shadow-card-hover transition-shadow">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-medium">Total Agents</span>
              <Layers className="w-4 h-4 text-[#B15F2C]" />
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-[#111111]">12</div>
            <p className="text-[11px] text-emerald-800 font-medium">Active in workspace</p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#EAE8E5] shadow-card space-y-1 hover:shadow-card-hover transition-shadow">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-medium">Successful Runs</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-[#111111]">128</div>
            <p className="text-[11px] text-[#777777]">97.7% verification rate</p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#EAE8E5] shadow-card space-y-1 hover:shadow-card-hover transition-shadow">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-medium">Failed Runs</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-[#111111]">3</div>
            <p className="text-[11px] text-[#B15F2C] font-semibold">All auto-repaired</p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#EAE8E5] shadow-card space-y-1 hover:shadow-card-hover transition-shadow">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-medium">Workflows Created</span>
              <Boxes className="w-4 h-4 text-[#0A0A0A]" />
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-[#111111]">18</div>
            <p className="text-[11px] text-[#777777]">Visual agent graphs</p>
          </div>
        </div>
      </section>

      {/* 4. A. My Agents (Recently Created Agents as Clean Cards) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">My Agents</h2>
            <p className="text-xs text-[#777777]">Your active AI assistants and workflows</p>
          </div>
          <button
            onClick={() => setCurrentPage('my-agents')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>View All ({RECENT_AGENTS.length})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {RECENT_AGENTS.map((agent) => (
            <div
              key={agent.id}
              className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 transition-all flex flex-col justify-between group"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      agent.status === 'Ready'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : agent.status === 'Active'
                        ? 'bg-blue-50 text-blue-800 border border-blue-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {agent.status}
                  </span>
                  <span className="text-[10px] text-[#777777] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {agent.lastUpdated}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                  {agent.name}
                </h3>
                <p className="text-xs text-[#777777] line-clamp-2 leading-relaxed">
                  {agent.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#EAE8E5] flex items-center justify-between">
                <span className="text-[11px] text-[#777777] font-medium">
                  {agent.nodesCount} components
                </span>
                <button
                  onClick={() => loadAgent(agent)}
                  className="px-3 py-1.5 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-subtle active:scale-[0.98]"
                >
                  <Play className="w-3 h-3 fill-white" />
                  <span>Open</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. C. Recent Activity (Recent Executions & Statuses) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Recent Activity</h2>
            <p className="text-xs text-[#777777]">Latest execution runs, telemetry and self-repair events</p>
          </div>
          <button
            onClick={() => setCurrentPage('activity')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>Activity Console →</span>
          </button>
        </div>

        <div className="p-4 sm:p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-3">
          <div className="divide-y divide-[#EAE8E5]">
            {executionHistory.slice(0, 3).map((rec) => (
              <div key={rec.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                      rec.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : rec.status === 'repaired'
                        ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}
                  >
                    {rec.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : rec.status === 'repaired' ? (
                      <ShieldCheck className="w-4 h-4" />
                    ) : (
                      <AlertTriangle className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-bold text-[#111111]">{rec.agentName}</h4>
                    <p className="text-[11px] text-[#777777]">
                      {rec.triggerType} • Ran in {rec.duration} • {rec.steps.length} components executed
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center">
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                      rec.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : rec.status === 'repaired'
                        ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
                        : 'bg-rose-50 text-rose-800 border border-rose-200'
                    }`}
                  >
                    {rec.status === 'repaired' ? 'AUTO-REPAIRED' : rec.status.toUpperCase()}
                  </span>
                  <button
                    onClick={() => setCurrentPage('activity')}
                    className="text-xs font-semibold text-[#777777] hover:text-[#111111] transition-colors"
                  >
                    Details →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. D. Quick Start Templates */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Quick Start Templates</h2>
            <p className="text-xs text-[#777777]">Proven, pre-configured agent workflows ready to customize</p>
          </div>
          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>All Templates ({SAMPLE_TEMPLATES.length})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {SAMPLE_TEMPLATES.map((tpl) => (
            <div
              key={tpl.id}
              className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-2xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20 shadow-subtle">
                    <FileText className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] text-[#777777] font-semibold bg-[#F7F6F4] px-2 py-0.5 rounded-full border border-[#EAE8E5]">
                    {tpl.category}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-[#111111]">{tpl.name}</h3>
                <p className="text-xs text-[#777777] line-clamp-2 leading-relaxed">
                  {tpl.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#EAE8E5] flex items-center justify-between">
                <span className="text-[11px] text-[#777777]">
                  {tpl.componentCount} components
                </span>
                <LiquidButton
                  variant="secondary"
                  size="sm"
                  onClick={() => loadTemplate(tpl)}
                  icon={<ArrowRight className="w-3 h-3" />}
                  iconPosition="right"
                >
                  Use Template
                </LiquidButton>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
