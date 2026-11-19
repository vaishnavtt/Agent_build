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
  HelpCircle,
  FileText,
  Sliders,
  Check,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';

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
      text: 'Read resumes and evaluate candidate skills against job requirements.',
    },
    {
      title: 'Invoice Processing Assistant',
      category: 'Finance & Ops',
      text: 'Read invoices, extract key totals, verify approval rules, and organize information.',
    },
    {
      title: 'PDF Question-Answering Assistant',
      category: 'Knowledge Base',
      text: 'Answer questions from PDF documents and provide referenced answers with citations.',
    },
    {
      title: 'Document Summarization Assistant',
      category: 'Productivity',
      text: 'Summarize long documents into concise 5-bullet executive summaries.',
    },
  ];

  const [prompt, setPrompt] = useState(activePrompt || examplePrompts[0].text);
  const [inputPref, setInputPref] = useState('PDF Documents');
  const [stylePref, setStylePref] = useState('High Precision');

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

  // Friendly generation steps strictly matching Phase 6
  const steps = [
    {
      number: 1,
      title: 'Understanding your idea',
      description: 'Analyzing what you want your assistant to accomplish',
      icon: BrainCircuit,
      detail: 'Goal and requirements understood',
    },
    {
      number: 2,
      title: 'Planning the work',
      description: 'Breaking down tasks into simple sequential and decision steps',
      icon: Workflow,
      detail: 'Planned the step-by-step roadmap',
    },
    {
      number: 3,
      title: 'Choosing the right tools',
      description: 'Selecting building blocks (Reader, AI Assistant, Decision & Delivery)',
      icon: Boxes,
      detail: 'Selected optimal components',
    },
    {
      number: 4,
      title: 'Building your assistant',
      description: 'Assembling the visual canvas and wiring connections',
      icon: Bot,
      detail: `Connected ${nodes.length || 6} building blocks ready for testing`,
    },
  ];

  const isComplete = !isGenerating && generationStep === 4;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16 page-fade-in select-none">
      {/* Friendly Guide Ribbon: Where am I? What can I do here? What should I do next? */}
      <div className="p-3.5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shadow-subtle">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-[#B15F2C] text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
            ?
          </span>
          <p className="text-xs text-[#111111]">
            <strong className="text-[#B15F2C]">Step-by-step:</strong> Describe what you want your assistant to do below in plain words. We automatically connect the right tools for you!
          </p>
        </div>
        <span className="text-[11px] font-semibold text-[#777777]">
          Simulated Agent Synthesis
        </span>
      </div>

      {/* Heading & Subtitle strictly matching Phase 6 */}
      <div className="text-center space-y-2 max-w-2xl mx-auto pt-2">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-bold shadow-subtle">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Step 1 of 3</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#111111] tracking-tight">
          What should your assistant do?
        </h1>
        <p className="text-sm sm:text-base text-[#777777] leading-relaxed">
          Describe the task in your own words. We will break it down into easy building blocks.
        </p>
      </div>

      {/* Main Guided Conversation Card */}
      <div className="p-6 sm:p-8 rounded-3xl liquid-glass border border-[#EAE8E5] shadow-card space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#111111]">
              Describe the task in plain language
            </label>
            <span className="text-[11px] text-[#777777] font-medium">
              No programming knowledge needed
            </span>
          </div>
          <div className="relative">
            <textarea
              rows={3}
              disabled={isGenerating}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Read resumes and evaluate candidate skills against job requirements."
              className="w-full text-base sm:text-lg text-[#111111] placeholder:text-[#777777]/60 bg-white border border-[#EAE8E5] rounded-2xl p-4 sm:p-5 focus:outline-none focus:border-[#B15F2C] focus:bg-white shadow-subtle transition-all resize-none disabled:opacity-50 leading-relaxed"
            />
            <div className="absolute bottom-3 right-4 text-[11px] text-[#777777]">
              {prompt.length} characters
            </div>
          </div>
        </div>

        {/* Simple Follow-Up Questions (Phase 6 Requirement) */}
        <div className="p-4 rounded-2xl bg-[#F7F6F4]/80 border border-[#EAE8E5] space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-[#111111]">
            <Sliders className="w-3.5 h-3.5 text-[#B15F2C]" />
            <span>Optional Preferences (Keep defaults or customize)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="font-semibold text-[#777777] text-[11px]">Where will information come from?</label>
              <select
                value={inputPref}
                onChange={(e) => setInputPref(e.target.value)}
                className="w-full text-xs text-[#111111] bg-white border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
              >
                <option value="PDF Documents">PDF Documents or Resumes</option>
                <option value="User Message">User Typed Message</option>
                <option value="Spreadsheet / Data">Spreadsheet / Invoices</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-[#777777] text-[11px]">Assistant Decision Style</label>
              <select
                value={stylePref}
                onChange={(e) => setStylePref(e.target.value)}
                className="w-full text-xs text-[#111111] bg-white border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
              >
                <option value="High Precision">High Precision (Structured & rule-based)</option>
                <option value="Balanced">Balanced (Recommended)</option>
                <option value="Creative">Creative (Detailed feedback)</option>
              </select>
            </div>
          </div>
        </div>

        {/* 3D Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-3">
            <ElevatedButton
              variant="primary"
              size="lg"
              onClick={handleGenerate}
              loading={isGenerating}
              loadingText="Building your assistant..."
              icon={<Sparkles className="w-4 h-4" />}
              glow
            >
              Build My Agent
            </ElevatedButton>

            <ElevatedButton
              variant="secondary"
              size="md"
              onClick={handleClear}
              disabled={isGenerating || !prompt}
              icon={<RotateCcw className="w-3.5 h-3.5 text-[#777777]" />}
            >
              Clear
            </ElevatedButton>
          </div>

          <button
            onClick={() => setCurrentPage('templates')}
            className="text-xs text-[#B15F2C] font-bold hover:underline flex items-center gap-1"
          >
            <span>Or pick a ready-made template →</span>
          </button>
        </div>

        {/* 5. Friendly Generation Animation */}
        {(isGenerating || isComplete) && (
          <div className="mt-6 p-6 rounded-3xl bg-[#FAF5F1] border-2 border-[#CF8047]/30 space-y-5 animate-in fade-in duration-300 shadow-card">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-2xl ${
                    isComplete ? 'bg-emerald-600' : 'bg-[#B15F2C]'
                  } text-white flex items-center justify-center shadow-subtle ${
                    isGenerating ? 'animate-spin' : ''
                  }`}
                >
                  {isComplete ? <CheckCircle2 className="w-6 h-6" /> : <Sparkles className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-extrabold text-[#111111]">
                    {isComplete ? 'Your AI assistant is ready!' : 'Building your assistant...'}
                  </h3>
                  <p className="text-[11px] sm:text-xs text-[#777777]">
                    {isComplete
                      ? `Assembled "${activeAgentName}" with all connected building blocks.`
                      : 'Connecting the right building blocks for your request'}
                  </p>
                </div>
              </div>
              <span className="text-xs font-bold text-[#B15F2C] bg-white px-3 py-1 rounded-full border border-[#CF8047]/30">
                {isComplete ? 'Ready to inspect' : `Step ${generationStep} of 4`}
              </span>
            </div>

            {/* Step Progress Line */}
            <div className="w-full bg-[#EAE8E5] h-2 rounded-full overflow-hidden">
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
                        ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
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

            {/* Step 6: "Your AI assistant is ready!" with Prominent "See How It Works" button */}
            {isComplete && (
              <div className="p-5 rounded-2xl bg-white border border-[#EAE8E5] flex flex-col sm:flex-row items-center justify-between gap-4 animate-in fade-in shadow-card">
                <div>
                  <h4 className="text-sm font-bold text-[#111111]">
                    Your AI assistant is ready!
                  </h4>
                  <p className="text-xs text-[#777777]">
                    {nodes.length} connected building blocks assembled for {activeAgentName}.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <ElevatedButton
                    variant="secondary"
                    size="md"
                    onClick={() => setCurrentPage('validation')}
                    icon={<ShieldCheck className="w-4 h-4 text-[#B15F2C]" />}
                  >
                    Check Everything
                  </ElevatedButton>
                  <ElevatedButton
                    variant="primary"
                    size="md"
                    onClick={() => setCurrentPage('editor')}
                    icon={<ArrowRight className="w-4 h-4" />}
                    iconPosition="right"
                    glow
                  >
                    See How It Works
                  </ElevatedButton>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Example Prompts Selection (Phase 6 Step 3) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-[#777777] uppercase tracking-wider">
          <Lightbulb className="w-4 h-4 text-[#B15F2C]" />
          <span>Click any example to start immediately:</span>
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
                <span className="text-[11px] text-[#B15F2C] font-bold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  <span>Build this now</span>
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
              <h3 className="font-bold text-sm text-[#111111] group-hover:text-[#B15F2C] transition-colors">
                {example.title}
              </h3>
              <p className="text-xs text-[#777777] leading-relaxed">
                "{example.text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
