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
  AlertCircle,
  ListOrdered,
  Layers,
  Send,
  Code,
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
    analyzeRequirements,
    analysisResult,
    isAnalyzing,
    setAnalysisResult,
  } = useWorkflow();

  const examplePrompts = [
    {
      title: 'Weather Prediction Agent',
      category: 'Climate & Forecasting',
      text: 'Create an AI agent that predicts weather conditions using temperature, humidity, and wind speed and provides a weather prediction report.',
    },
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
  const [clarificationAnswers, setClarificationAnswers] = useState<Record<string, string>>({});
  const [showJsonPlan, setShowJsonPlan] = useState<boolean>(false);

  useEffect(() => {
    if (activePrompt) {
      setPrompt(activePrompt);
    }
  }, [activePrompt]);

  const handleGenerate = () => {
    const textToUse = prompt.trim() || examplePrompts[0].text;
    generateAgentFromPrompt(textToUse);
  };

  const handleAnalyze = async () => {
    const textToUse = prompt.trim() || examplePrompts[0].text;
    await analyzeRequirements(textToUse, clarificationAnswers);
  };

  const handleClarificationAnswerChange = (questionId: string, answerText: string) => {
    setClarificationAnswers((prev) => ({
      ...prev,
      [questionId]: answerText,
    }));
  };

  const handleClear = () => {
    setPrompt('');
    setAnalysisResult(null);
    setClarificationAnswers({});
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
          <div className="flex flex-wrap items-center gap-3">
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
              size="lg"
              onClick={handleAnalyze}
              loading={isAnalyzing}
              loadingText="Analyzing Requirements..."
              icon={<BrainCircuit className="w-4 h-4 text-[#B15F2C]" />}
            >
              Analyze Requirements
            </ElevatedButton>

            <ElevatedButton
              variant="secondary"
              size="md"
              onClick={handleClear}
              disabled={isGenerating || isAnalyzing || !prompt}
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

        {/* Member 2: AI Requirement Analysis & Architecture Plan Panel */}
        {analysisResult && (
          <div className="mt-6 p-6 rounded-3xl bg-white border-2 border-[#CF8047]/30 shadow-card space-y-6 animate-in fade-in duration-300">
            {/* Header: Objective & Status */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#EAE8E5]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 flex items-center gap-1">
                    <BrainCircuit className="w-3 h-3" />
                    Member 2 AI Architect
                  </span>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                    {analysisResult.ai_provider === 'google-gemini' ? 'Google Gemini AI' : 'Deterministic Engine'}
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-extrabold text-[#111111]">
                  {analysisResult.project_objective}
                </h3>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    analysisResult.status === 'ready'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                      : 'bg-amber-50 text-amber-700 border-amber-300'
                  }`}
                >
                  {analysisResult.status === 'ready' ? '✓ Plan Ready' : '⚠ Clarification Needed'}
                </span>
                <button
                  onClick={() => setShowJsonPlan((prev) => !prev)}
                  className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-[#F7F6F4] hover:bg-[#EAE8E5] text-[#111111] border border-[#EAE8E5] transition-colors flex items-center gap-1"
                >
                  <Code className="w-3.5 h-3.5" />
                  <span>{showJsonPlan ? 'Hide JSON' : 'View Plan JSON'}</span>
                </button>
              </div>
            </div>

            {/* Clarification Questions (if needed) */}
            {analysisResult.status === 'needs_clarification' && analysisResult.clarification_questions.length > 0 && (
              <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200/80 space-y-4">
                <div className="flex items-center gap-2 text-amber-800 text-xs font-bold">
                  <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>Missing or Ambiguous Requirements Detected</span>
                </div>
                <p className="text-xs text-amber-900/80">
                  To avoid generating an unreliable execution plan, please clarify the following details:
                </p>

                <div className="space-y-3">
                  {analysisResult.clarification_questions.map((q) => (
                    <div key={q.id} className="p-3 bg-white rounded-xl border border-amber-200 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <label className="text-xs font-bold text-[#111111]">
                          <span className="text-[#B15F2C] mr-1">[{q.id}]</span>
                          {q.question}
                        </label>
                      </div>
                      <p className="text-[11px] text-[#777777] italic bg-[#F7F6F4] p-1.5 rounded-lg border border-[#EAE8E5]">
                        <strong>Why clarification is needed:</strong> {q.reason}
                      </p>
                      <input
                        type="text"
                        placeholder="Type your clarification answer here..."
                        value={clarificationAnswers[q.id] || ''}
                        onChange={(e) => handleClarificationAnswerChange(q.id, e.target.value)}
                        className="w-full text-xs text-[#111111] bg-white border border-[#EAE8E5] rounded-lg px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
                      />
                    </div>
                  ))}
                </div>

                <div className="pt-1 flex justify-end">
                  <ElevatedButton
                    variant="primary"
                    size="md"
                    onClick={handleAnalyze}
                    loading={isAnalyzing}
                    loadingText="Updating Plan..."
                    icon={<Send className="w-3.5 h-3.5" />}
                  >
                    Submit Answers & Re-Analyze Plan
                  </ElevatedButton>
                </div>
              </div>
            )}

            {/* Extracted Requirements Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3.5 rounded-2xl bg-[#F7F6F4]/90 border border-[#EAE8E5] space-y-2">
                <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                  Identified Inputs
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysisResult.requirements.inputs.map((inp, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 text-[11px] font-medium">
                      {inp}
                    </span>
                  ))}
                  {analysisResult.requirements.inputs.length === 0 && (
                    <span className="text-[#777777] italic text-[11px]">None specified</span>
                  )}
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4]/90 border border-[#EAE8E5] space-y-2">
                <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                  Processing Steps
                </span>
                <ol className="list-decimal list-inside space-y-1 text-[#111111] text-[11px]">
                  {analysisResult.requirements.processing.map((step, idx) => (
                    <li key={idx} className="leading-snug">{step}</li>
                  ))}
                </ol>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4]/90 border border-[#EAE8E5] space-y-2">
                <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                  Expected Outputs
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysisResult.requirements.outputs.map((out, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-medium">
                      {out}
                    </span>
                  ))}
                  {analysisResult.requirements.outputs.length === 0 && (
                    <span className="text-[#777777] italic text-[11px]">None specified</span>
                  )}
                </div>
              </div>
            </div>

            {/* Selected Canonical Workflow Components */}
            <div className="space-y-2">
              <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                Selected Canonical Components ({analysisResult.required_components.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {analysisResult.required_components.map((comp, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 text-xs font-bold"
                  >
                    <Boxes className="w-3.5 h-3.5" />
                    <span>{comp}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Ordered Task Decomposition */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                  Ordered Task Decomposition ({analysisResult.tasks.length} Executable Tasks)
                </span>
                <span className="text-[11px] text-[#777777]">Sequential execution order</span>
              </div>

              <div className="space-y-2">
                {analysisResult.tasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="p-3 rounded-2xl bg-white border border-[#EAE8E5] hover:border-[#CF8047]/40 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-subtle"
                  >
                    <div className="flex items-start sm:items-center gap-3">
                      <span className="w-7 h-7 rounded-xl bg-[#B15F2C] text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                        {task.task_id}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-[#111111]">{task.task_name}</p>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
                            {task.component}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#777777] mt-0.5">{task.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-[#777777] sm:text-right flex-shrink-0">
                      {task.dependencies && task.dependencies.length > 0 ? (
                        <span>Depends on: <strong className="text-[#111111]">{task.dependencies.join(', ')}</strong></span>
                      ) : (
                        <span className="text-emerald-700 font-medium">Initial trigger</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Member 5: Acceptance Criteria */}
            {analysisResult.acceptance_criteria && analysisResult.acceptance_criteria.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#B15F2C]" />
                    Acceptance Criteria ({analysisResult.acceptance_criteria.length} Verifiable Rules)
                  </span>
                  <span className="text-[11px] text-[#777777]">Used by Member 5 for verification & test harness</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {analysisResult.acceptance_criteria.map((ac) => (
                    <div key={ac.id} className="p-3 rounded-2xl bg-[#F7F6F4]/80 border border-[#EAE8E5] space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded-md bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 font-bold text-[10px]">
                          {ac.id}
                        </span>
                        <p className="font-bold text-[#111111] leading-tight">{ac.criteria}</p>
                      </div>
                      {ac.description && (
                        <p className="text-[11px] text-[#777777]">{ac.description}</p>
                      )}
                      {ac.pass_condition && (
                        <div className="text-[10px] text-emerald-800 bg-emerald-50/70 px-2 py-1 rounded-lg border border-emerald-200/50 mt-1">
                          <strong>Pass Condition:</strong> {ac.pass_condition}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Edge Cases & Failure Analysis */}
            {analysisResult.edge_cases && analysisResult.edge_cases.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                    Edge Cases & Failure Resilience ({analysisResult.edge_cases.length} Scenarios)
                  </span>
                  <span className="text-[11px] text-[#777777]">Boundary & invalid input resilience</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {analysisResult.edge_cases.map((ec) => (
                    <div key={ec.scenario_id} className="p-3 rounded-2xl bg-white border border-[#EAE8E5] space-y-1 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-bold text-[10px]">
                            {ec.scenario_id}
                          </span>
                          <p className="font-bold text-[#111111] text-xs leading-tight">{ec.description}</p>
                        </div>
                        <span
                          className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-md border ${
                            ec.severity === 'Critical'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : ec.severity === 'High'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-slate-50 text-slate-700 border-slate-200'
                          }`}
                        >
                          {ec.severity}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#777777]">
                        <strong>Trigger:</strong> {ec.input_condition}
                      </p>
                      <p className="text-[11px] text-slate-800 bg-slate-50 p-1.5 rounded-lg border border-slate-200/60">
                        <strong>Expected Behavior:</strong> {ec.expected_behavior}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Member 5: Automated Test Scenarios */}
            {analysisResult.test_scenarios && analysisResult.test_scenarios.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block flex items-center gap-1.5">
                    <ListOrdered className="w-3.5 h-3.5 text-blue-600" />
                    Automated Test Scenarios ({analysisResult.test_scenarios.length} Scenarios for Member 5)
                  </span>
                  <span className="text-[11px] text-[#777777]">Positive, negative & edge tests</span>
                </div>

                <div className="space-y-2">
                  {analysisResult.test_scenarios.map((ts) => (
                    <div key={ts.test_id} className="p-3 rounded-2xl bg-white border border-[#EAE8E5] space-y-1 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 flex items-center justify-center font-bold text-[10px]">
                            {ts.test_id}
                          </span>
                          <p className="font-bold text-[#111111] text-xs">{ts.test_description}</p>
                        </div>
                        <span
                          className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                            ts.scenario_type === 'positive'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : ts.scenario_type === 'negative'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-purple-50 text-purple-700 border-purple-200'
                          }`}
                        >
                          {ts.scenario_type}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                        <div className="bg-[#F7F6F4] p-1.5 rounded-lg border border-[#EAE8E5]">
                          <strong className="text-[#777777]">Expected Status:</strong> {ts.expected_status}
                        </div>
                        <div className="bg-[#F7F6F4] p-1.5 rounded-lg border border-[#EAE8E5]">
                          <strong className="text-[#777777]">Pass Condition:</strong> {ts.pass_fail_condition}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw JSON Plan for Member 3 Integration */}
            {showJsonPlan && (
              <div className="space-y-2 animate-in fade-in">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#111111] uppercase text-[10px] tracking-wider block">
                    Execution Plan Contract (Member 3 Compatible JSON)
                  </span>
                  <span className="text-[11px] text-[#777777]">Schema v{analysisResult.contract_version}</span>
                </div>
                <pre className="p-4 rounded-2xl bg-[#111111] text-emerald-400 font-mono text-xs overflow-x-auto max-h-72 border border-slate-800">
                  {JSON.stringify(analysisResult, null, 2)}
                </pre>
              </div>
            )}

            {/* Hand-off Action to Member 3 */}
            {analysisResult.status === 'ready' && (
              <div className="p-4 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/40 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs">
                  <strong className="text-[#B15F2C]">Ready for Workflow Generation:</strong>
                  <p className="text-[#777777] text-[11px] mt-0.5">
                    Plan is validated. Member 3 can transform this structured execution plan into visual canvas nodes.
                  </p>
                </div>
                <ElevatedButton
                  variant="primary"
                  size="md"
                  onClick={handleGenerate}
                  icon={<ArrowRight className="w-4 h-4" />}
                  iconPosition="right"
                  glow
                >
                  Generate Visual Workflow
                </ElevatedButton>
              </div>
            )}
          </div>
        )}

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
