import React, { useState } from 'react';
import {
  Activity,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Wrench,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Check,
  Terminal,
  FileCheck2,
  Copy,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { LiquidButton } from '../common/LiquidButton';

export const ExecutionMonitorPage: React.FC = () => {
  const {
    activeAgentName,
    currentExecution,
    runAgentExecution,
    isExecuting,
    repairState,
    repairReport,
    triggerFailureScenario,
    executeAutoRepair,
    setCurrentPage,
    showToast,
  } = useWorkflow();

  const [showLogEvidence, setShowLogEvidence] = useState(true);

  const isFailed = currentExecution?.status === 'failed' || repairState.isActive || repairState.stage !== 'idle';
  const isRepaired = currentExecution?.status === 'repaired' || repairState.stage === 'completed' || repairReport !== null;

  const repairSteps = [
    { number: 1, key: 'identifying', label: 'Problem identified', desc: 'Analyzed configuration & execution trace' },
    { number: 2, key: 'preparing', label: 'Correction prepared', desc: 'Created optimal instructions & settings' },
    { number: 3, key: 'applying', label: 'Correction applied', desc: 'Updated component configuration in graph' },
    { number: 4, key: 'checking', label: 'Workflow checked again', desc: 'Verified topology & schema compliance' },
    { number: 5, key: 'retesting', label: 'Tests executed again', desc: 'Executed 4 test scenarios successfully' },
  ];

  const getStepProgressNumber = (stage: string) => {
    switch (stage) {
      case 'identifying':
        return 1;
      case 'preparing':
        return 2;
      case 'applying':
        return 3;
      case 'checking':
        return 4;
      case 'retesting':
        return 5;
      case 'completed':
        return 6;
      default:
        return 0;
    }
  };

  const currentStepNum = getStepProgressNumber(repairState.stage);

  const copyReportSummary = () => {
    if (!repairReport) return;
    const summary = `AgentForge AI Repair Report\nAgent: ${repairReport.agentName}\nInitial: ${repairReport.originalError}\nCorrection: ${repairReport.appliedCorrection}\nValidation: ${repairReport.revalidationResult}\nRetest: ${repairReport.retestResult}\nStatus: ${repairReport.finalStatus}`;
    navigator.clipboard.writeText(summary);
    showToast('Copied to Clipboard', 'Repair report summary copied to clipboard', 'info');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 select-none">
      {/* Page Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
            <Activity className="w-3.5 h-3.5" />
            <span>Telemetry & Live Activity</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight mt-1">
            What is your agent doing?
          </h1>
          <p className="text-sm text-[#777777]">
            Live execution trace, problem detection, and autonomous repair.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Failure Scenario Simulator */}
          <LiquidButton
            variant="destructive"
            size="sm"
            onClick={() => triggerFailureScenario()}
            icon={<AlertTriangle className="w-3.5 h-3.5 text-white" />}
            title="Simulate a broken component to test Auto-Repair"
          >
            Simulate Failure
          </LiquidButton>

          {/* Re-run button */}
          <LiquidButton
            variant="primary"
            size="sm"
            onClick={() => runAgentExecution()}
            loading={isExecuting}
            loadingText="Executing..."
            icon={<Play className="w-3.5 h-3.5 fill-white" />}
            glow
          >
            Re-run Agent
          </LiquidButton>
        </div>
      </div>

      {/* Execution Summary Metadata Card */}
      <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-medium">Execution ID</span>
          <div className="text-base font-bold text-[#111111] font-mono">
            {currentExecution?.id || 'exec-9821'}
          </div>
          <span className="text-[11px] text-[#777777] truncate block">{activeAgentName}</span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-medium">Status</span>
          <div>
            {isExecuting ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                Processing
              </span>
            ) : isFailed && repairState.stage !== 'completed' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                Needs Fix
              </span>
            ) : isRepaired ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Auto-Repaired
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Completed
              </span>
            )}
          </div>
          <span className="text-[11px] text-[#777777]">
            {isRepaired ? 'Repaired in 1 attempt' : '100% verified'}
          </span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-medium">Start Time</span>
          <div className="text-base font-bold text-[#111111] flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[#777777]" />
            <span>{currentExecution?.startedAt || 'Today at 14:22'}</span>
          </div>
          <span className="text-[11px] text-[#777777]">Trigger: {currentExecution?.triggerType || 'Manual Run'}</span>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-[#777777] font-medium">Duration</span>
          <div className="text-base font-bold text-[#111111]">
            {currentExecution?.duration || '2.1s'}
          </div>
          <span className="text-[11px] text-emerald-700 font-medium">Optimized</span>
        </div>
      </div>

      {/* AUTONOMOUS WORKFLOW SELF-REPAIR CARD */}
      {(isFailed || repairState.stage !== 'idle' || repairReport) && (
        <div className="p-6 sm:p-7 rounded-3xl bg-[#FAF5F1] border-2 border-[#CF8047] shadow-card space-y-6 animate-in slide-in-from-top-4 duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#CF8047]/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center flex-shrink-0 shadow-subtle">
                <Wrench className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base sm:text-lg font-bold text-[#111111]">
                    Autonomous Workflow Self-Repair
                  </h2>
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-[#FFFFFF] text-[#B15F2C] border border-[#CF8047]/30">
                    Attempt {repairState.attemptCount || 1} of 2
                  </span>
                </div>
                <p className="text-xs text-[#777777]">
                  AgentForge AI identified an issue, found why it happened, and prepared a fix.
                </p>
              </div>
            </div>

            {repairState.stage !== 'completed' && !repairReport && (
              <LiquidButton
                variant="primary"
                size="md"
                onClick={() => executeAutoRepair()}
                loading={repairState.stage !== 'idle'}
                loadingText="Repairing Workflow..."
                disabled={repairState.attemptCount >= 2}
                icon={<Sparkles className="w-4 h-4" />}
                glow
              >
                Fix Automatically
              </LiquidButton>
            )}
          </div>

          {/* Plain English Diagnosis Triad */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-rose-200 space-y-1.5 shadow-subtle">
              <p className="text-[10px] font-bold uppercase text-rose-700 tracking-wider">
                1. What went wrong?
              </p>
              <p className="font-bold text-xs text-[#111111]">
                {repairState.problemFound || 'The AI Assistant component is missing instructions.'}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] space-y-1.5 shadow-subtle">
              <p className="text-[10px] font-bold uppercase text-[#777777] tracking-wider">
                2. Why did this happen?
              </p>
              <p className="text-xs text-[#777777] leading-relaxed">
                {repairState.whyItHappened || 'The assistant requires instructions before it can evaluate candidate skills.'}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#CF8047]/40 space-y-1.5 shadow-subtle">
              <p className="text-[10px] font-bold uppercase text-[#B15F2C] tracking-wider">
                3. How can we fix it?
              </p>
              <p className="text-xs text-[#111111] font-medium leading-relaxed">
                {repairState.suggestedFix || 'Automatically inject candidate scoring instructions and re-run verification.'}
              </p>
            </div>
          </div>

          {/* Execution Log Evidence Panel */}
          {repairState.logEvidence && repairState.logEvidence.length > 0 && (
            <div className="p-4 rounded-2xl bg-[#111111] text-[#F7F6F4] space-y-2 border border-[#EAE8E5]/20 font-mono text-xs">
              <div
                className="flex items-center justify-between cursor-pointer select-none"
                onClick={() => setShowLogEvidence(!showLogEvidence)}
              >
                <div className="flex items-center gap-2 text-rose-400">
                  <Terminal className="w-4 h-4" />
                  <span className="font-bold text-xs font-sans">Execution Log Evidence (Failure Trace)</span>
                </div>
                <div className="text-[11px] text-[#777777] flex items-center gap-1">
                  <span>{showLogEvidence ? 'Collapse' : 'Expand'}</span>
                  {showLogEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </div>
              </div>

              {showLogEvidence && (
                <div className="pt-2 space-y-1.5 overflow-x-auto text-[11px] leading-relaxed text-[#777777]">
                  {repairState.logEvidence.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-[#777777]/60 whitespace-nowrap">[{log.timestamp}]</span>
                      <span
                        className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                          log.level === 'ERROR'
                            ? 'bg-rose-900/60 text-rose-300'
                            : log.level === 'WARN'
                            ? 'bg-amber-900/60 text-amber-300'
                            : 'bg-zinc-800 text-zinc-300'
                        }`}
                      >
                        {log.level}
                      </span>
                      <span className="text-[#CF8047] font-semibold whitespace-nowrap">[{log.component}]</span>
                      <span className="text-[#FFFFFF]">{log.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 5-Step Repair Execution Progress */}
          {repairState.stage !== 'idle' && (
            <div className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#111111]">
                  Self-Repair Progression Pipeline
                </span>
                <span className="text-xs text-[#B15F2C] font-semibold">
                  {repairState.stage === 'completed'
                    ? '100% Repaired & Verified'
                    : `In progress: Step ${Math.min(currentStepNum, 5)} of 5`}
                </span>
              </div>

              {/* Steps List */}
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
                {repairSteps.map((st) => {
                  const isDone = currentStepNum > st.number;
                  const isCurrent = currentStepNum === st.number;
                  return (
                    <div
                      key={st.number}
                      className={`p-3 rounded-xl border transition-all text-xs space-y-1 ${
                        isDone
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                          : isCurrent
                          ? 'bg-[#FAF5F1] border-[#B15F2C] text-[#111111] shadow-subtle ring-1 ring-[#B15F2C]'
                          : 'bg-[#F7F6F4] border-[#EAE8E5] text-[#777777]'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 font-bold">
                        {isDone ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <span
                            className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] ${
                              isCurrent ? 'bg-[#B15F2C] text-white animate-pulse' : 'bg-[#EAE8E5] text-[#777777]'
                            }`}
                          >
                            {st.number}
                          </span>
                        )}
                        <span className="text-[11px] truncate">{st.label}</span>
                      </div>
                      <p className="text-[10px] text-[#777777] leading-tight">{st.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* FINAL EXECUTION & REPAIR REPORT */}
          {repairReport && (
            <div className="p-6 rounded-2xl bg-[#FFFFFF] border-2 border-emerald-500 shadow-card space-y-4 animate-in fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#EAE8E5] pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-subtle">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#111111]">
                      Final Execution & Repair Report
                    </h3>
                    <p className="text-[11px] text-[#777777]">
                      Verification complete • Status: <span className="text-emerald-700 font-bold">{repairReport.finalStatus}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <LiquidButton
                    variant="secondary"
                    size="sm"
                    onClick={copyReportSummary}
                    icon={<Copy className="w-3.5 h-3.5 text-[#777777]" />}
                  >
                    Copy Summary
                  </LiquidButton>
                  <LiquidButton
                    variant="primary"
                    size="sm"
                    onClick={() => setCurrentPage('editor')}
                  >
                    Open in Visual Canvas
                  </LiquidButton>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 rounded-xl bg-[#FAF5F1] border border-[#CF8047]/20 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-[#B15F2C]">Original Failure Diagnosis</span>
                  <p className="font-bold text-[#111111]">{repairReport.originalError}</p>
                  <p className="text-[11px] text-[#777777]">{repairReport.diagnosedReason}</p>
                </div>

                <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-emerald-800">Applied Correction</span>
                  <p className="font-bold text-emerald-950">{repairReport.appliedCorrection}</p>
                  <p className="text-[11px] text-emerald-800">Graph nodes patched in 1 attempt (max 2 allowed).</p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#F7F6F4] border border-[#EAE8E5] flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
                <span className="text-[#777777]">
                  Topology Re-check: <strong className="text-emerald-700">{repairReport.revalidationResult}</strong>
                </span>
                <span className="text-[#777777]">
                  Test Suite: <strong className="text-emerald-700">{repairReport.retestResult}</strong>
                </span>
                <span className="text-[11px] font-mono text-[#777777]">{repairReport.timestamp}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Workflow Component Step Execution Flow */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-[#111111]">
            Step-by-Step Component Execution Trace
          </h2>
          <span className="text-xs text-[#777777]">
            {currentExecution?.steps.length || 0} Steps in pipeline
          </span>
        </div>

        <div className="space-y-3">
          {currentExecution?.steps.map((st, i) => (
            <div
              key={st.id || i}
              className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                st.status === 'failed'
                  ? 'bg-rose-50/60 border-rose-200'
                  : st.status === 'processing'
                  ? 'bg-amber-50/60 border-amber-200'
                  : 'bg-[#FFFFFF] border-[#EAE8E5] shadow-card'
              }`}
            >
              <div className="flex items-start sm:items-center gap-3">
                <span className="w-7 h-7 rounded-xl bg-[#F7F6F4] text-[#111111] font-bold text-xs flex items-center justify-center flex-shrink-0 border border-[#EAE8E5]">
                  {st.stepNumber}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-xs sm:text-sm text-[#111111]">
                      {st.componentName}
                    </h3>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20">
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

      {/* Execution Logs Table */}
      <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-4">
        <h2 className="text-base font-bold text-[#111111]">Execution Activity Log</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-[#EAE8E5] text-[#777777] text-[11px] pb-2">
                <th className="py-2 font-medium">Timestamp</th>
                <th className="py-2 font-medium">Component</th>
                <th className="py-2 font-medium">Activity Description</th>
                <th className="py-2 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE8E5]">
              {currentExecution?.steps.map((st, i) => (
                <tr key={i} className="hover:bg-[#F7F6F4]/50 transition-colors">
                  <td className="py-2.5 text-[#777777]">{st.timestamp}</td>
                  <td className="py-2.5 font-semibold text-[#111111]">[{st.componentName}]</td>
                  <td className="py-2.5 text-[#777777]">{st.activity}</td>
                  <td className="py-2.5 text-right font-sans">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                        st.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-800'
                          : st.status === 'processing'
                          ? 'bg-amber-50 text-amber-800'
                          : st.status === 'failed'
                          ? 'bg-rose-50 text-rose-800'
                          : 'bg-[#F7F6F4] text-[#777777]'
                      }`}
                    >
                      {st.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
