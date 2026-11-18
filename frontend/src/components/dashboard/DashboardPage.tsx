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
  ShieldAlert,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { RECENT_AGENTS, SAMPLE_TEMPLATES } from '../../data/mockData';
import { LiquidButton } from '../common/LiquidButton';

export const DashboardPage: React.FC = () => {
  const { setCurrentPage, generateAgentFromPrompt, loadTemplate, loadAgent } = useWorkflow();

  const [promptText, setPromptText] = useState('');

  const promptSuggestions = [
    'Create an agent that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report.',
    'Build an invoice processing agent that parses vendor invoices, checks if amount exceeds $1,000, and requests manager approval.',
    'Create a research agent that answers natural language questions from technical PDF manuals with citations.',
    'Build a weekly summarizer that condenses project updates and emails a 5-bullet digest to team leads.',
  ];

  const handleCreateAgent = () => {
    const finalPrompt = promptText.trim() || promptSuggestions[0];
    generateAgentFromPrompt(finalPrompt);
  };

  return (
    <div className="space-y-8 pb-12 max-w-7xl mx-auto">
      {/* Top Hero & Natural Language Prompt Card */}
      <section className="space-y-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
            Welcome to AgentForge AI
          </h1>
          <p className="text-sm text-[#8D8D8D] mt-1">
            Build intelligent AI agents without writing complex code.
          </p>
        </div>

        {/* Large Natural Language Input Card */}
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card hover:shadow-card-hover transition-shadow space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#B15F2C]">
            <Sparkles className="w-4 h-4" />
            <span>Describe Your Agent</span>
          </div>

          <div className="relative">
            <textarea
              rows={3}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="Describe what you want your AI agent to do... e.g. Create an agent that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report."
              className="w-full text-sm sm:text-base text-[#111111] placeholder:text-[#8D8D8D]/70 bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-2xl p-4 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] transition-all resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex items-center gap-2 sm:gap-3">
              <LiquidButton
                variant="primary"
                size="md"
                onClick={handleCreateAgent}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                glow
              >
                Create Agent
              </LiquidButton>

              <LiquidButton
                variant="secondary"
                size="md"
                onClick={() => setCurrentPage('templates')}
                icon={<Boxes className="w-4 h-4 text-[#8D8D8D]" />}
              >
                Explore Templates
              </LiquidButton>
            </div>

            <span className="text-[11px] text-[#8D8D8D]">
              Tip: Click any suggestion below to try an example
            </span>
          </div>

          {/* Prompt Suggestions */}
          <div className="pt-2 border-t border-[#E6E5E2]">
            <p className="text-[11px] font-semibold text-[#8D8D8D] uppercase tracking-wider mb-2">
              Popular Examples
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {promptSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setPromptText(suggestion)}
                  className="text-left p-2.5 rounded-xl bg-[#FAF5F1] hover:bg-[#FAF5F1]/80 border border-[#CF8047]/20 text-[11px] text-[#111111] leading-relaxed transition-colors flex items-start gap-2 group"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#B15F2C] mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform" />
                  <span className="line-clamp-2">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Statistics Section (4 Cards) */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 sm:p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-[#8D8D8D]">
            <span className="text-xs font-medium">Total Agents</span>
            <Layers className="w-4 h-4 text-[#B15F2C]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-[#111111]">12</div>
          <p className="text-[11px] text-emerald-700 flex items-center gap-1 font-medium">
            <TrendingUp className="w-3 h-3" />
            <span>+3 created this week</span>
          </p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-[#8D8D8D]">
            <span className="text-xs font-medium">Successful Runs</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-[#111111]">148</div>
          <p className="text-[11px] text-[#8D8D8D]">97.4% reliability score</p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-[#8D8D8D]">
            <span className="text-xs font-medium">Failed Runs</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-[#111111]">4</div>
          <p className="text-[11px] text-[#B15F2C] font-medium">3 auto-repaired automatically</p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-[#8D8D8D]">
            <span className="text-xs font-medium">Workflows Created</span>
            <Boxes className="w-4 h-4 text-[#0A0A0A]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-[#111111]">18</div>
          <p className="text-[11px] text-[#8D8D8D]">Across 4 departments</p>
        </div>
      </section>

      {/* Recent Agents Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Recent Agents</h2>
            <p className="text-xs text-[#8D8D8D]">Agents you created or worked on recently</p>
          </div>
          <button
            onClick={() => setCurrentPage('my-agents')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>View All</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {RECENT_AGENTS.map((agent) => (
            <div
              key={agent.id}
              className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle hover:shadow-card hover:border-[#CF8047]/40 transition-all flex flex-col justify-between group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
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

                <h3 className="font-bold text-sm text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                  {agent.name}
                </h3>
                <p className="text-xs text-[#8D8D8D] line-clamp-2 leading-relaxed">
                  {agent.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#E6E5E2] flex items-center justify-between">
                <span className="text-[11px] text-[#8D8D8D] font-medium">
                  {agent.nodesCount} components
                </span>
                <button
                  onClick={() => loadAgent(agent)}
                  className="px-3 py-1.5 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Play className="w-3 h-3 fill-white" />
                  <span>Open Agent</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Templates Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#111111]">Ready-to-Use Templates</h2>
            <p className="text-xs text-[#8D8D8D]">Start instantly with proven, pre-configured agent workflows</p>
          </div>
          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>Explore All Templates</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {SAMPLE_TEMPLATES.map((tpl) => (
            <div
              key={tpl.id}
              className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle hover:shadow-card hover:border-[#CF8047]/40 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
                    <FileText className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] text-[#8D8D8D] font-medium bg-[#F1F0EE] px-2 py-0.5 rounded-full">
                    {tpl.category}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-[#111111]">{tpl.name}</h3>
                <p className="text-xs text-[#8D8D8D] line-clamp-2 leading-relaxed">
                  {tpl.description}
                </p>

                <div className="flex flex-wrap gap-1">
                  {tpl.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] text-[#8D8D8D] bg-[#F1F0EE] px-1.5 py-0.5 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-[#E6E5E2] flex items-center justify-between">
                <span className="text-[11px] text-[#8D8D8D]">
                  {tpl.componentCount} components
                </span>
                <button
                  onClick={() => loadTemplate(tpl)}
                  className="px-3 py-1.5 rounded-full bg-[#FAF5F1] hover:bg-[#B15F2C] text-[#B15F2C] hover:text-white border border-[#CF8047]/30 text-xs font-semibold transition-all flex items-center gap-1"
                >
                  <span>Use Template</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Automatic Self-Repair Banner Notice */}
      <section className="p-5 sm:p-6 rounded-3xl bg-[#FAF5F1] border border-[#CF8047]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center flex-shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#111111]">
              Built-in Autonomous Self-Repair
            </h3>
            <p className="text-xs text-[#8D8D8D] mt-0.5">
              AgentForge AI detects broken links, missing AI instructions, or runtime exceptions and repairs them automatically with 1 click.
            </p>
          </div>
        </div>
        <button
          onClick={() => setCurrentPage('activity')}
          className="px-4 py-2 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold whitespace-nowrap"
        >
          See Repair Demo
        </button>
      </section>
    </div>
  );
};

