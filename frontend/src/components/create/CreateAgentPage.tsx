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
  ShieldCheck,
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

  const examplePrompts = [
    {
      title: 'Resume Evaluation Assistant',
      category: 'Recruiting & HR',
      text: 'Create a resume evaluation assistant that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report.',
    },
    {
      title: 'Invoice Processing Assistant',
      category: 'Finance & Ops',
      text: 'Create an invoice processing assistant that parses vendor PDF invoices, verifies tax IDs, checks if total exceeds $1,000, and requests manager approval.',
    },
    {
      title: 'PDF Question-Answering Assistant',
      category: 'Knowledge Base',
      text: 'Create a PDF question-answering assistant where users can upload technical documents and ask questions to get instant, referenced answers.',
    },
    {
      title: 'Document Summarization Assistant',
      category: 'Productivity',
      text: 'Create a document summarization assistant that condenses long reports into a concise 5-bullet executive summary and emails team leads.',
    },
  ];

  const [prompt, setPrompt] = useState(activePrompt || examplePrompts[0].text);

  useEffect(() => {
    if (activePrompt) {
      setPrompt(activePrompt);
    }
  }, [activePrompt]);

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
      title: 'Understanding your request',
      description: 'Analyzing natural language intent, goal parameters, and inputs',
      icon: BrainCircuit,
      detail: 'Parsed requirements & goal parameters',
    },
    {
      number: 2,
      title: 'Planning the tasks',
      description: 'Decomposing requirement into discrete sequential and conditional tasks',
      icon: Workflow,
      detail: 'Decomposed 5 operational steps',
    },
    {
      number: 3,
      title: 'Selecting the required components',
      description: 'Choosing appropriate predefined components from the library',
      icon: Boxes,
      detail: 'Selected Input, PDF Reader, AI Assistant, Decision & Output',
    },
    {
      number: 4,
      title: 'Building your agent',
      description: 'Synthesizing visual workflow graph, setting schemas and wiring connections',
      icon: Bot,
      detail: `Assembled ${nodes.length || 6} components with verified connections`,
    },
  ];

  const isComplete = !isGenerating && generationStep === 4;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Heading & Subtitle */}
      <div className="text-center space-y-2 max-w-2xl mx-auto pt-2">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>No-Code Agent Builder</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-[#111111] tracking-tight">
          What would you like your AI assistant to do?
        </h1>
        <p className="text-sm sm:text-base text-[#777777] leading-relaxed">
          Describe your task in simple language. AgentForge AI turns your instructions into an executable visual workflow.
        </p>
      </div>

      {/* Main Input Card (Liquid Glass) */}
      <div className="p-6 sm:p-8 rounded-3xl liquid-glass border border-[#EAE8E5] shadow-card space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#111111]">
              Your Instructions
            </label>
            <span className="text-[11px] text-[#777777] font-medium">
              Demo Simulation Runtime
            </span>
          </div>
          <div className="relative">
            <textarea
              rows={4}
              disabled={isGenerating}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Create a resume evaluation assistant that reads PDF resumes, extracts candidate skills, compares them with a job description and generates an evaluation report."
              className="w-full text-base sm:text-lg text-[#111111] placeholder:text-[#777777]/60 bg-white/90 border border-[#EAE8E5] rounded-2xl p-4 sm:p-5 focus:outline-none focus:border-[#B15F2C] focus:bg-white shadow-subtle transition-all resize-none disabled:opacity-50 leading-relaxed"
            />
            <div className="absolute bottom-3 right-4 text-[11px] text-[#777777]">
              {prompt.length} characters
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-3">
            <LiquidButton
              variant="primary"
              size="lg"
              onClick={handleGenerate}
              loading={isGenerating}
              loadingText="Building your agent..."
              icon={<Sparkles className="w-4 h-4" />}
              glow
            >
              Create My Agent
            </LiquidButton>

            <LiquidButton
              variant="secondary"
              size="md"
              onClick={handleClear}
              disabled={isGenerating || !prompt}
              icon={<RotateCcw className="w-3.5 h-3.5 text-[#777777]" />}
            >
              Clear
            </LiquidButton>
          </div>

          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-semibold hover:underline flex items-center gap-1"
          >
            <span>Or browse pre-configured templates →</span>
          </button>
        </div>

        {/* 4-Stage Workflow Generation Pipeline Visualizer */}
        {(isGenerating || isComplete) && (
          <div className="mt-6 p-6 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 space-y-5 animate-in fade-in duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`w-9 h-9 rounded-2xl ${
                    isComplete ? 'bg-emerald-600' : 'bg-[#B15F2C]'
                  } text-white flex items-center justify-center shadow-subtle ${
                    isGenerating ? 'animate-spin' : ''
                  }`}
                >
                  {isComplete ? <CheckCircle2 className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#111111]">
                    {isComplete ? 'Agent Workflow Built Successfully!' : 'AgentForge AI is building your agent...'}
                  </h3>
                  <p className="text-[11px] text-[#777777]">
                    {isComplete
                      ? `Synthesized "${activeAgentName}" with 6 connected components.`
                      : 'Converting your instructions into an executable visual workflow'}
                  </p>
                </div>
              </div>
              <span className="text-xs font-bold text-[#B15F2C]">
                {isComplete ? '4 of 4 Steps Completed' : `Step ${generationStep} of 4`}
              </span>
            </div>

            {/* Step Progress Line */}
            <div className="w-full bg-[#EAE8E5] h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  isComplete ? 'bg-emerald-600' : 'bg-[#B15F2C]'
                }`}
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
                    className={`p-3.5 rounded-2xl border transition-all flex items-start gap-3 ${
                      isDone
                        ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
                        : isCurrent
                        ? 'bg-white border-[#B15F2C] shadow-subtle text-[#111111] ring-1 ring-[#B15F2C]'
                        : 'bg-white/60 border-[#EAE8E5] text-[#777777]'
                    }`}
                  >
                    <div className="pt-0.5">
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Icon className={`w-4 h-4 ${isCurrent ? 'text-[#B15F2C] animate-pulse' : 'text-[#777777]'}`} />
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-bold">{st.title}</p>
                      <p className="text-[10px] text-[#777777] mt-0.5">{st.description}</p>
                      {isDone && (
                        <p className="text-[10px] text-emerald-700 font-semibold mt-1">
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
              <div className="p-4 rounded-2xl bg-white border border-[#EAE8E5] flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in shadow-subtle">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111111]">{activeAgentName}:</span>
                  <span className="text-xs text-[#777777]">{nodes.length} Components, {edges.length} Connections</span>
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
                    glow
                  >
                    Open in Workflow Studio
                  </LiquidButton>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Example Prompts Selection */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-[#777777] uppercase tracking-wider">
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
              className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card hover:shadow-card-hover hover:border-[#CF8047]/40 cursor-pointer transition-all space-y-2 group active:scale-[0.99]"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
                  {example.category}
                </span>
                <span className="text-[11px] text-[#B15F2C] font-semibold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  <span>Create now</span>
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
              <h3 className="font-bold text-sm text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                {example.title}
              </h3>
              <p className="text-xs text-[#777777] leading-relaxed line-clamp-2">
                "{example.text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
