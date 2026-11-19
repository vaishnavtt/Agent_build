import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Boxes,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  ChevronRight,
  Bot,
  Zap,
  HelpCircle,
  FileText,
  Activity,
  ArrowUpRight,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { RECENT_AGENTS, SAMPLE_TEMPLATES } from '../../data/mockData';
import { ElevatedButton } from '../common/ElevatedButton';

export const DashboardPage: React.FC = () => {
  const {
    setCurrentPage,
    generateAgentFromPrompt,
    loadTemplate,
    loadAgent,
    executionHistory,
    savedAgents,
  } = useWorkflow();

  const [promptText, setPromptText] = useState('');

  const promptSuggestions = [
    'Read resumes and evaluate candidates.',
    'Read invoices and organize information.',
    'Answer questions from PDF documents.',
    'Summarize long documents.',
    'Organize customer requests.',
  ];

  const handleCreateAgent = () => {
    const finalPrompt = promptText.trim() || promptSuggestions[0];
    generateAgentFromPrompt(finalPrompt);
  };

  return (
    <div className="space-y-10 pb-16 max-w-6xl mx-auto page-fade-in select-none">
      {/* Beginner Guide Ribbon: Where am I? What can I do here? What should I do next? */}
      <div className="p-3.5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shadow-subtle">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-[#B15F2C] text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
            ?
          </span>
          <p className="text-xs text-[#111111]">
            <strong className="text-[#B15F2C]">First time here?</strong> Type what you want your AI assistant to do, or click any example chip below to watch your agent build itself!
          </p>
        </div>
        <button
          onClick={() => setCurrentPage('create-agent')}
          className="text-xs font-bold text-[#B15F2C] hover:text-[#984D20] flex items-center gap-1 transition-colors whitespace-nowrap pl-8 sm:pl-0"
        >
          <span>Quick creation wizard</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 1. Header & Hero Section with Animated Welcome Illustration */}
      <section className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pt-2">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-bold shadow-subtle">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            <span>Autonomous AI Assistant Builder</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#111111] tracking-tight leading-tight">
            Hello! What would you like to create today?
          </h1>
          <p className="text-base sm:text-lg text-[#777777] font-normal leading-relaxed">
            Build your own AI assistant in just a few simple steps. No coding needed.
          </p>
        </div>

        {/* Friendly Animated Welcome Illustration (Pure SVG + CSS Micro-Interactions) */}
        <div className="relative w-44 h-36 sm:w-52 sm:h-40 flex-shrink-0 hidden md:flex items-center justify-center animate-float-slow">
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-[#FAF5F1] to-[#FFF9F5] border border-[#CF8047]/20 shadow-card" />
          {/* Ambient Glow Aura */}
          <div className="absolute w-24 h-24 rounded-full bg-[#CF8047]/15 blur-xl -z-10" />

          {/* Floating Glass Tile 1: AI Brain */}
          <div className="absolute top-3 left-3 p-2 rounded-2xl bg-white/95 border border-[#EAE8E5] shadow-card flex items-center gap-1.5 animate-float-gentle">
            <span className="w-5 h-5 rounded-xl bg-[#FAF5F1] text-[#B15F2C] flex items-center justify-center text-xs font-bold">
              AI
            </span>
            <span className="text-[10px] font-bold text-[#111111]">Assistant</span>
          </div>

          {/* Central Friendly Mascot Icon */}
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-b from-[#B15F2C] to-[#8F471B] text-white flex items-center justify-center shadow-[0_6px_20px_rgba(177,95,44,0.4)] border-2 border-white/80">
              <Bot className="w-9 h-9 text-white" />
            </div>
            <div className="mt-1 flex items-center gap-1 px-2 py-0.5 rounded-full bg-white border border-[#EAE8E5] shadow-subtle">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-bold text-[#111111]">Ready to help</span>
            </div>
          </div>

          {/* Floating Glass Tile 2: Output */}
          <div className="absolute bottom-3 right-3 p-2 rounded-2xl bg-white/95 border border-[#EAE8E5] shadow-card flex items-center gap-1.5 animate-float-gentle [animation-delay:1.5s]">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span className="text-[10px] font-bold text-[#111111]">Verified</span>
          </div>
        </div>
      </section>

      {/* 2. Prominent Natural Language Prompt Card */}
      <section className="p-6 sm:p-8 rounded-3xl liquid-glass border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#B15F2C]">
            <Bot className="w-4 h-4" />
            <span>Tell Us What You Want Your Assistant To Do</span>
          </div>
          <span className="text-[11px] font-semibold text-[#777777] bg-white px-3 py-1 rounded-full border border-[#EAE8E5] shadow-subtle">
            No technical terms required
          </span>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="Tell us what you want your AI assistant to do... (e.g. Read resumes and evaluate candidates for our team)"
            className="w-full text-base sm:text-lg text-[#111111] placeholder:text-[#777777]/60 bg-white border border-[#EAE8E5] rounded-2xl p-4 sm:p-5 focus:outline-none focus:border-[#B15F2C] focus:bg-white shadow-subtle transition-all resize-none leading-relaxed"
          />
        </div>

        {/* Primary 3D Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex flex-wrap items-center gap-3">
            <ElevatedButton
              variant="primary"
              size="md"
              onClick={handleCreateAgent}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
              glow
            >
              Create My Agent
            </ElevatedButton>

            <ElevatedButton
              variant="secondary"
              size="md"
              onClick={() => setCurrentPage('templates')}
              icon={<Boxes className="w-4 h-4 text-[#777777]" />}
            >
              Explore Ready-Made Agents
            </ElevatedButton>
          </div>

          <span className="text-[11px] text-[#777777] font-medium hidden sm:inline">
            Click any example below to prefill
          </span>
        </div>

        {/* 5 Clickable Example Chips */}
        <div className="pt-4 border-t border-[#EAE8E5]">
          <p className="text-[11px] font-bold text-[#777777] uppercase tracking-wider mb-2.5">
            Click an idea to try:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {promptSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => setPromptText(suggestion)}
                className="text-left p-3 rounded-2xl bg-white hover:bg-[#FAF5F1] border border-[#EAE8E5] hover:border-[#CF8047]/40 text-xs text-[#111111] transition-all flex items-center justify-between group shadow-subtle active:scale-[0.98]"
              >
                <span className="font-semibold truncate mr-2">{suggestion}</span>
                <span className="text-[10px] text-[#B15F2C] opacity-0 group-hover:opacity-100 transition-opacity font-bold flex items-center gap-0.5 whitespace-nowrap">
                  Use this →
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 3. Four Clean Overview Cards (Phase 5 Requirement) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Overview</h2>
            <p className="text-xs text-[#777777]">Your workspace assistants and performance</p>
          </div>
          <span className="text-[11px] font-semibold text-[#777777] bg-[#F7F6F4] px-2.5 py-1 rounded-full border border-[#EAE8E5]">
            Live workspace stats
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {/* Card 1: My AI Agents */}
          <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-1">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-semibold">My AI Agents</span>
              <div className="p-1.5 rounded-xl bg-[#FAF5F1] text-[#B15F2C]">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-[#111111]">
              {savedAgents.length}
            </div>
            <p className="text-[11px] text-emerald-800 font-semibold">Ready to run</p>
          </div>

          {/* Card 2: Successful Tasks */}
          <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-1">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-semibold">Successful Tasks</span>
              <div className="p-1.5 rounded-xl bg-emerald-50 text-emerald-700">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-[#111111]">128</div>
            <p className="text-[11px] text-[#777777] font-medium">97.7% success rate</p>
          </div>

          {/* Card 3: Tasks Needing Attention */}
          <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-1">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-semibold">Tasks Needing Attention</span>
              <div className="p-1.5 rounded-xl bg-amber-50 text-amber-700">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-[#111111]">0</div>
            <p className="text-[11px] text-[#B15F2C] font-semibold">Auto-repaired automatically</p>
          </div>

          {/* Card 4: Total Runs */}
          <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all space-y-1">
            <div className="flex items-center justify-between text-[#777777]">
              <span className="text-xs font-semibold">Total Runs</span>
              <div className="p-1.5 rounded-xl bg-[#F7F6F4] text-[#111111]">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-[#111111]">
              {executionHistory.length + 130}
            </div>
            <p className="text-[11px] text-[#777777] font-medium">Recorded executions</p>
          </div>
        </div>
      </section>

      {/* 4. My AI Agents (Quick Access) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">My Assistants</h2>
            <p className="text-xs text-[#777777]">Open any assistant to view its building blocks</p>
          </div>
          <button
            onClick={() => setCurrentPage('my-agents')}
            className="text-xs text-[#B15F2C] font-bold hover:underline flex items-center gap-1"
          >
            <span>See all ({savedAgents.length})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {savedAgents.slice(0, 4).map((agent) => (
            <div
              key={agent.id}
              className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 transition-all flex flex-col justify-between group space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      agent.status === 'Ready'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
                    }`}
                  >
                    {agent.status}
                  </span>
                  <span className="text-[10px] text-[#777777] flex items-center gap-1 font-medium">
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

              <div className="pt-2 border-t border-[#EAE8E5] flex items-center justify-between">
                <span className="text-[11px] text-[#777777] font-semibold">
                  {agent.nodesCount} steps
                </span>
                <ElevatedButton
                  variant="secondary"
                  size="sm"
                  onClick={() => loadAgent(agent)}
                  icon={<Play className="w-3 h-3 fill-[#111111]" />}
                >
                  Open
                </ElevatedButton>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Recent Activity Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Recent Activity</h2>
            <p className="text-xs text-[#777777]">Latest actions taken by your assistants</p>
          </div>
          <button
            onClick={() => setCurrentPage('activity')}
            className="text-xs text-[#B15F2C] font-bold hover:underline flex items-center gap-1"
          >
            <span>Watch Live</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="p-5 sm:p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-3">
          {executionHistory.slice(0, 3).map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-2xl bg-[#F7F6F4]/70 border border-[#EAE8E5] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:bg-[#FAF5F1] transition-colors"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-subtle ${
                    item.status === 'completed'
                      ? 'bg-emerald-100 text-emerald-800'
                      : item.status === 'repaired'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-[#111111]">{item.agentName}</h4>
                  <p className="text-[11px] text-[#777777]">
                    Execution {item.id} • Finished in {item.duration}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {item.status === 'repaired' ? 'AUTO-REPAIRED' : 'COMPLETED'}
                </span>
                <button
                  onClick={() => setCurrentPage('activity')}
                  className="p-1 rounded-lg text-[#777777] hover:text-[#111111] hover:bg-white transition-colors"
                >
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 6. Ready-Made Agent Templates */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Ready-Made Recipes</h2>
            <p className="text-xs text-[#777777]">Click to launch a tested assistant with 1 click</p>
          </div>
          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-bold hover:underline flex items-center gap-1"
          >
            <span>All Templates</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SAMPLE_TEMPLATES.slice(0, 2).map((tpl) => (
            <div
              key={tpl.id}
              className="p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-2xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle">
                    <FileText className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#F7F6F4] text-[#777777] border border-[#EAE8E5]">
                    {tpl.category}
                  </span>
                </div>

                <h3 className="font-bold text-base text-[#111111]">{tpl.name}</h3>
                <p className="text-xs text-[#777777] leading-relaxed">{tpl.description}</p>
              </div>

              <div className="pt-2 border-t border-[#EAE8E5] flex items-center justify-between">
                <span className="text-xs text-[#777777] font-medium">
                  {tpl.componentCount} building blocks
                </span>
                <ElevatedButton
                  variant="primary"
                  size="sm"
                  onClick={() => loadTemplate(tpl)}
                  icon={<ArrowRight className="w-3.5 h-3.5" />}
                  iconPosition="right"
                >
                  Use Template
                </ElevatedButton>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
