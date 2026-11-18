import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRight,
  RotateCcw,
  Bot,
  BrainCircuit,
  Boxes,
  Workflow,
  CheckCircle2,
  Lightbulb,
  FileCheck,
  ShieldCheck,
  Cpu,
  Layers,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { LiquidButton } from '../common/LiquidButton';

export const CreateAgentPage: React.FC = () => {
  const {
    activePrompt,
    activeAgentName,
    nodes,
    edges,
    generateAgentFromPrompt,
    isGenerating,
    generationStep,
    setCurrentPage,
  } = useWorkflow();

  const [prompt, setPrompt] = useState(activePrompt || '');

  useEffect(() => {
    if (activePrompt) {
      setPrompt(activePrompt);
    }
  }, [activePrompt]);

  const examplePrompts = [
    {
      title: 'Resume & Candidate Screener (Recommended)',
      category: 'HR & Recruiting',
      text: 'Create an agent that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report.',
    },
    {
      title: 'Invoice Approver & Tax Checker',
      category: 'Finance',
      text: 'Build an invoice processing agent that parses vendor PDF invoices, verifies tax IDs, checks if total is over $1,000, and requests finance manager approval.',
    },
    {
      title: 'Technical Documentation Q&A',
      category: 'Knowledge Base',
      text: 'Create a research agent where I can upload long technical PDFs and ask natural questions to get instant, referenced answers.',
    },
    {
      title: 'Executive Briefing Summarizer',
      category: 'Productivity',
      text: 'Create an agent that summarizes quarterly executive reports into 5 bullet points and emails it to the team.',
    },
  ];

  const handleGenerate = () => {
    const textToUse = prompt.trim() || examplePrompts[0].text;
    generateAgentFromPrompt(textToUse);
  };

  const handleClear = () => {
    setPrompt('');
  };

  // Generation Steps definition strictly matching project architecture
  const steps = [
    {
      number: 1,
      title: 'Understanding requirements',
      description: 'Analyzing natural language intent, goal parameters, and data sources',
      icon: BrainCircuit,
      detail: 'Goal: Automated candidate qualification against technical criteria',
    },
    {
      number: 2,
      title: 'Planning tasks',
      description: 'Decomposing requirement into discrete sequential and conditional tasks',
      icon: Workflow,
      detail: 'Decomposed: PDF Ingestion → LLM Skill Fit → Condition Check → Approval → Output',
    },
    {
      number: 3,
      title: 'Selecting components',
      description: 'Selecting appropriate predefined components from canonical library',
      icon: Boxes,
      detail: 'Selected: Input, Document Reader, AI Assistant, Condition, Human Approval, Output',
    },
    {
      number: 4,
      title: 'Generating workflow',
      description: 'Synthesizing visual nodes, configuring data ports, and wiring edges',
      icon: Bot,
      detail: `Graph assembled with ${nodes.length || 6} nodes and ${edges.length || 5} data flow edges`,
    },
  ];

  const isComplete = !isGenerating && generationStep === 4;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Heading & Subtitle */}
      <div className="text-center space-y-2 max-w-2xl mx-auto pt-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Natural Language Agent Builder</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-[#111111] tracking-tight">
          What would you like your AI agent to do?
        </h1>
        <p className="text-sm text-[#8D8D8D] leading-relaxed">
          Describe your task in simple language. AgentForge AI turns your instructions into an executable visual workflow.
        </p>
      </div>

      {/* Main Input Card */}
      <div className="p-6 sm:p-8 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-6">
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-[#111111]">
            Your Instructions
          </label>
          <div className="relative">
            <textarea
              rows={4}
              disabled={isGenerating}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Create an agent that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report."
              className="w-full text-sm sm:text-base text-[#111111] placeholder:text-[#8D8D8D]/60 bg-[#F1F0EE]/50 border border-[#E6E5E2] rounded-2xl p-4 sm:p-5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] transition-all resize-none disabled:opacity-50"
            />
            <div className="absolute bottom-3 right-4 text-[11px] text-[#8D8D8D]">
              {prompt.length} characters
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-3">
            <LiquidButton
              variant="primary"
              size="md"
              onClick={handleGenerate}
              loading={isGenerating}
              loadingText="Synthesizing Agent..."
              icon={<Sparkles className="w-4 h-4" />}
              glow
            >
              Generate Workflow
            </LiquidButton>

            <LiquidButton
              variant="secondary"
              size="md"
              onClick={handleClear}
              disabled={isGenerating || !prompt}
              icon={<RotateCcw className="w-3.5 h-3.5 text-[#8D8D8D]" />}
            >
              Clear
            </LiquidButton>
          </div>

          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>Or choose a pre-made template →</span>
          </button>
        </div>

        {/* 4-Stage Workflow Generation Pipeline Visualizer */}
        {(isGenerating || isComplete) && (
          <div className="mt-6 p-6 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 space-y-5 animate-in fade-in duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`w-8 h-8 rounded-xl ${isComplete ? 'bg-emerald-600' : 'bg-[#B15F2C]'} text-white flex items-center justify-center ${isGenerating ? 'animate-spin' : ''}`}>
                  {isComplete ? <CheckCircle2 className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#111111]">
                    {isComplete ? 'Workflow Generated Successfully!' : 'AgentForge AI is building your workflow...'}
                  </h3>
                  <p className="text-[11px] text-[#8D8D8D]">
                    {isComplete
                      ? `Synthesized "${activeAgentName}" with 6 components and verified schema.`
                      : 'Converting your requirements into an executable visual workflow'}
                  </p>
                </div>
              </div>
              <span className="text-xs font-bold text-[#B15F2C]">
                {isComplete ? 'Step 4 of 4 Completed' : `Step ${generationStep} of 4`}
              </span>
            </div>

            {/* Step Progress Line */}
            <div className="w-full bg-[#E6E5E2] h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 rounded-full ${isComplete ? 'bg-emerald-600' : 'bg-[#B15F2C]'}`}
                style={{ width: `${(generationStep / 4) * 100}%` }}
              />
            </div>

            {/* 4 Steps Checklist */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {steps.map((st) => {
                const Icon = st.icon;
                const isCurrent = isGenerating && generationStep === st.number;
                const isDone = isComplete || generationStep > st.number;
                return (
                  <div
                    key={st.number}
                    className={`p-3.5 rounded-xl border transition-all flex items-start gap-2.5 ${
                      isDone
                        ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
                        : isCurrent
                        ? 'bg-[#FFFFFF] border-[#B15F2C] shadow-subtle text-[#111111] ring-1 ring-[#B15F2C]'
                        : 'bg-[#F1F0EE]/60 border-[#E6E5E2] text-[#8D8D8D]'
                    }`}
                  >
                    <div className="pt-0.5">
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Icon className={`w-4 h-4 ${isCurrent ? 'text-[#B15F2C] animate-pulse' : 'text-[#8D8D8D]'}`} />
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-bold">{st.title}</p>
                      <p className="text-[10px] text-[#8D8D8D] mt-0.5">{st.description}</p>
                      {isDone && (
                        <p className="text-[10px] text-emerald-700 font-medium mt-1">
                          ✓ {st.detail}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Actions once workflow is generated */}
            {isComplete && (
              <div className="p-4 rounded-xl bg-[#FFFFFF] border border-[#E6E5E2] flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111111]">{activeAgentName}:</span>
                  <span className="text-xs text-[#8D8D8D]">{nodes.length} Components, {edges.length} Connections</span>
                </div>
                <div className="flex items-center gap-2">
                  <LiquidButton
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentPage('validation')}
                    icon={<ShieldCheck className="w-3.5 h-3.5 text-[#B15F2C]" />}
                  >
                    Check Agent
                  </LiquidButton>
                  <LiquidButton
                    variant="primary"
                    size="sm"
                    onClick={() => setCurrentPage('editor')}
                    icon={<ArrowRight className="w-3.5 h-3.5" />}
                    iconPosition="right"
                  >
                    Inspect & Configure Workflow
                  </LiquidButton>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Example Prompts Selection */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-[#8D8D8D] uppercase tracking-wider">
          <Lightbulb className="w-4 h-4 text-[#B15F2C]" />
          <span>Need inspiration? Try these prompt examples</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {examplePrompts.map((example, i) => (
            <div
              key={i}
              onClick={() => {
                setPrompt(example.text);
                generateAgentFromPrompt(example.text);
              }}
              className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle hover:shadow-card hover:border-[#CF8047]/40 cursor-pointer transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
                  {example.category}
                </span>
                <span className="text-[11px] text-[#B15F2C] font-semibold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  <span>Generate now</span>
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
              <h3 className="font-bold text-sm text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                {example.title}
              </h3>
              <p className="text-xs text-[#8D8D8D] leading-relaxed line-clamp-2">
                "{example.text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
