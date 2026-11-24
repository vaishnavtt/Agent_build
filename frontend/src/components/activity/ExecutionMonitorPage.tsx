import React from 'react';
import {
  Activity,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Check,
  FileText,
  Bot,
  FileOutput,
  GitFork,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';
import { RepairPanel } from './RepairPanel';

export const ExecutionMonitorPage: React.FC = () => {
  const {
    activeAgentName,
    currentExecution,
    runAgentExecution,
    isExecuting,
  } = useWorkflow();

  const isFailed = currentExecution?.status === 'failed';

  // Friendly execution timeline example steps strictly matching Phase 9
  const friendlyTimeline = [
    { number: 1, title: 'Reading your document', desc: 'Extracted text & structured sections from uploaded resume.', icon: FileText },
    { number: 2, title: 'Understanding the information', desc: 'Gemini evaluated candidate skills, experience, and score.', icon: Bot },
    { number: 3, title: 'Comparing the results', desc: 'Evaluated score >= 7.0 rule and checked approval status.', icon: GitFork },
    { number: 4, title: 'Preparing the final report', desc: 'Formatted candidate brief & dispatched interview email.', icon: FileOutput },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 select-none page-fade-in">
      {/* Friendly Guide Ribbon: Where am I? What can I do here? What should I do next? */}
      <div className="p-3.5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shadow-subtle">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-[#B15F2C] text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
            ?
          </span>
          <p className="text-xs text-[#111111]">
            <strong className="text-[#B15F2C]">Step 3 of 3:</strong> Review sample execution activity and request repair for a recorded backend failure.
          </p>
        </div>
        <span className="text-[11px] font-bold text-[#B15F2C]">
          Execution Monitor
        </span>
      </div>

      {/* Page Title & Controls strictly matching Phase 9 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-bold shadow-subtle">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>Execution Telemetry & Auto-Repair</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111111] tracking-tight mt-1">
            Watch Your Agent Work
          </h1>
          <p className="text-sm text-[#777777]">
            Review execution activity and check repair readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Re-run button */}
          <ElevatedButton
            variant="primary"
            size="sm"
            onClick={() => runAgentExecution()}
            loading={isExecuting}
            loadingText="Executing..."
            icon={<Play className="w-3.5 h-3.5 fill-white" />}
            glow
          >
            Re-run Agent
          </ElevatedButton>
        </div>
      </div>

      {/* Execution Summary Metadata Card */}
      <div className="p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-semibold">Execution ID</span>
          <div className="text-base font-extrabold text-[#111111] font-mono">
            {currentExecution?.id || 'exec-9821'}
          </div>
          <span className="text-[11px] text-[#777777] truncate block">{activeAgentName}</span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-semibold">Status</span>
          <div>
            {isExecuting ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                Processing
              </span>
            ) : isFailed ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                Needs Attention
              </span>
            ) : currentExecution?.status === 'repaired' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Sample repair record
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Completed
              </span>
            )}
          </div>
          <span className="text-[11px] text-[#777777] font-medium">
            Demo execution record
          </span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-semibold">Start Time</span>
          <div className="text-base font-bold text-[#111111] flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[#777777]" />
            <span>{currentExecution?.startedAt || 'Today at 14:22'}</span>
          </div>
          <span className="text-[11px] text-[#777777]">Trigger: {currentExecution?.triggerType || 'Manual Run'}</span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-semibold">Duration</span>
          <div className="text-base font-extrabold text-[#111111]">
            {currentExecution?.duration || '2.1s'}
          </div>
          <span className="text-[11px] text-emerald-700 font-bold">Optimized speed</span>
        </div>
      </div>

      {/* Phase 9: Beautiful Animated Progress Timeline */}
      <section className="p-6 sm:p-7 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-[#111111]">
              Execution Progress Timeline
            </h2>
            <p className="text-xs text-[#777777]">
              Step-by-step progress as your agent processes information
            </p>
          </div>
          <span className="text-[11px] font-bold text-[#B15F2C] bg-[#FAF5F1] px-2.5 py-0.5 rounded-full border border-[#CF8047]/30">
            {isExecuting ? 'Running Steps...' : isFailed ? 'Paused for Review' : 'All 4 Steps Done'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {friendlyTimeline.map((step) => {
            const Icon = step.icon;
            const isCompletedStep = !isFailed && !isExecuting;
            return (
              <div
                key={step.number}
                className={`p-4 rounded-2xl border transition-all space-y-2 ${
                  isCompletedStep
                    ? 'bg-emerald-50/70 border-emerald-200'
                    : isExecuting
                    ? 'bg-amber-50/50 border-amber-200 ring-1 ring-amber-400'
                    : isFailed && step.number === 2
                    ? 'bg-rose-50/70 border-rose-200 ring-1 ring-rose-400'
                    : 'bg-[#F7F6F4] border-[#EAE8E5]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-xl bg-white border border-[#EAE8E5] flex items-center justify-center shadow-subtle">
                    <Icon className="w-4 h-4 text-[#B15F2C]" />
                  </div>
                  {isCompletedStep ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-800">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Done
                    </span>
                  ) : isFailed && step.number === 2 ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-rose-800">
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                      Failed
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold text-[#777777]">
                      Step {step.number}
                    </span>
                  )}
                </div>

                <h4 className="font-extrabold text-xs text-[#111111]">
                  {step.number}. {step.title}
                </h4>
                <p className="text-[11px] text-[#777777] leading-relaxed">
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      <RepairPanel />

      {/* Step-by-Step Component Execution Trace */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-extrabold text-[#111111]">
            Step Execution Details
          </h2>
          <span className="text-xs text-[#777777]">
            {currentExecution?.steps.length || 0} Steps in pipeline
          </span>
        </div>

        <div className="space-y-3">
          {currentExecution?.steps.map((st, i) => (
            <div
              key={st.id || i}
              className={`p-4 rounded-3xl border transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                st.status === 'failed'
                  ? 'bg-rose-50/70 border-rose-200'
                  : st.status === 'processing'
                  ? 'bg-amber-50/70 border-amber-200'
                  : 'bg-white border-[#EAE8E5] shadow-card'
              }`}
            >
              <div className="flex items-start sm:items-center gap-3">
                <span className="w-8 h-8 rounded-2xl bg-[#F7F6F4] text-[#111111] font-extrabold text-xs flex items-center justify-center flex-shrink-0 border border-[#EAE8E5] shadow-subtle">
                  {st.stepNumber}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-xs sm:text-sm text-[#111111]">
                      {st.componentName}
                    </h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
                      {st.componentType}
                    </span>
                  </div>
                  <p className="text-xs text-[#777777] mt-0.5 leading-relaxed">
                    {st.activity}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[11px] text-[#777777] font-mono">
                  {st.timestamp}
                </span>

                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold ${
                    st.status === 'completed'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : st.status === 'processing'
                      ? 'bg-amber-50 text-amber-800 border border-amber-200 animate-pulse'
                      : st.status === 'failed'
                      ? 'bg-rose-50 text-rose-800 border border-rose-200'
                      : 'bg-[#F7F6F4] text-[#777777]'
                  }`}
                >
                  {st.status === 'completed' && <Check className="w-3 h-3 text-emerald-600" />}
                  {st.status === 'failed' && <AlertCircle className="w-3 h-3 text-rose-600" />}
                  <span>{st.status.toUpperCase()}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
