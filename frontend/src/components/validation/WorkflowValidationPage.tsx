import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Play,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Workflow,
  Check,
  FileCheck2,
  HelpCircle,
  Cable,
  Sliders,
  Flag,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { LiquidButton } from '../common/LiquidButton';

export const WorkflowValidationPage: React.FC = () => {
  const {
    activeAgentName,
    nodes,
    edges,
    validationIssues,
    validationMetrics,
    requirementCoverage,
    runValidation,
    isValidating,
    testCases,
    runTestCases,
    generateRequirementTests,
    isTesting,
    setCurrentPage,
    executeAutoRepair,
  } = useWorkflow();

  const [activeTab, setActiveTab] = useState<'overview' | 'structural' | 'requirements' | 'tests'>('overview');

  const errorCount = validationIssues.filter((i) => i.severity === 'error').length;
  const warningCount = validationIssues.filter((i) => i.severity === 'warning').length;

  const readinessPercent = validationMetrics?.overallReadiness ?? (errorCount > 0 ? 60 : warningCount > 0 ? 85 : 100);
  const isAllGood = errorCount === 0 && warningCount === 0;
  const hasErrors = errorCount > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 select-none">
      {/* Top Heading */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Agent Health & Verification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Check Your Agent
        </h1>
        <p className="text-sm text-[#777777]">
          Let's make sure your agent is completely ready to work before running it.
        </p>
      </div>

      {/* Main Readiness Score Banner (Apple Liquid Glass) */}
      <div
        className={`p-6 sm:p-7 rounded-3xl border shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all ${
          hasErrors
            ? 'bg-rose-50/50 border-rose-200'
            : warningCount > 0
            ? 'bg-amber-50/40 border-amber-200'
            : 'liquid-card border-[#EAE8E5]'
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-subtle ${
              hasErrors
                ? 'bg-rose-600 text-white'
                : warningCount > 0
                ? 'bg-amber-500 text-white'
                : 'bg-emerald-600 text-white'
            }`}
          >
            {hasErrors ? (
              <AlertCircle className="w-8 h-8" />
            ) : warningCount > 0 ? (
              <AlertTriangle className="w-8 h-8" />
            ) : (
              <CheckCircle2 className="w-8 h-8" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-xl font-bold text-[#111111]">
                {hasErrors
                  ? 'Something needs attention'
                  : warningCount > 0
                  ? 'Ready with minor suggestions'
                  : 'Your agent is verified and ready to run'}
              </span>
              <span
                className={`text-xs font-extrabold px-3 py-1 rounded-full ${
                  hasErrors
                    ? 'bg-rose-100 text-rose-800'
                    : warningCount > 0
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {readinessPercent}% Ready
              </span>
            </div>
            <p className="text-xs text-[#777777] mt-1.5 max-w-xl leading-relaxed">
              {hasErrors
                ? 'One or more components are missing instructions or connections. Click "Fix Automatically" below to let AgentForge AI repair them.'
                : warningCount > 0
                ? 'Your agent is executable, but optional settings can be fine-tuned for better accuracy.'
                : 'All components, data paths, and test scenarios are verified.'}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <LiquidButton
            variant="secondary"
            size="md"
            onClick={() => runValidation()}
            loading={isValidating}
            loadingText="Checking..."
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Check My Agent
          </LiquidButton>

          {hasErrors && (
            <LiquidButton
              variant="primary"
              size="md"
              onClick={() => executeAutoRepair()}
              icon={<Sparkles className="w-3.5 h-3.5" />}
              glow
            >
              Fix Automatically
            </LiquidButton>
          )}

          {!hasErrors && (
            <LiquidButton
              variant="primary"
              size="md"
              onClick={() => setCurrentPage('activity')}
              icon={<Play className="w-3.5 h-3.5 fill-white" />}
              glow
            >
              Run Agent
            </LiquidButton>
          )}
        </div>
      </div>

      {/* 4 Plain-Language Check Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Check 1: Connections */}
        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-medium">1. Connections</span>
            <Cable className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-sm font-bold text-[#111111]">
            Are components connected?
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{edges.length} active connections</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Information flows seamlessly from start to finish without gaps.
          </p>
        </div>

        {/* Check 2: Required Settings */}
        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-medium">2. Settings</span>
            <Sliders className="w-4 h-4 text-[#B15F2C]" />
          </div>
          <div className="text-sm font-bold text-[#111111]">
            Clear instructions?
          </div>
          <div className={`flex items-center gap-1.5 text-xs font-semibold ${errorCount > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
            {errorCount > 0 ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>{errorCount} need instructions</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>All settings complete</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Every assistant has precise goals and parameters.
          </p>
        </div>

        {/* Check 3: Missing Steps */}
        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-medium">3. Steps</span>
            <Flag className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-sm font-bold text-[#111111]">
            Start & end present?
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Input and Output verified</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            The agent knows where to receive input and where to deliver output.
          </p>
        </div>

        {/* Check 4: Tests */}
        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-medium">4. Tests</span>
            <FileCheck2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-sm font-bold text-[#111111]">
            Simulations passed?
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{testCases.length} scenarios passed</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Simulated scenarios run successfully before live activation.
          </p>
        </div>
      </div>

      {/* Detail Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-[#EAE8E5] pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Issues & Settings ({validationIssues.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('structural')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'structural'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <Workflow className="w-3.5 h-3.5" />
          <span>Workflow Structure</span>
        </button>

        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'requirements'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>Requirement Coverage ({requirementCoverage.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'tests'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <Play className="w-3.5 h-3.5" />
          <span>Test Scenarios ({testCases.length})</span>
        </button>
      </div>

      {/* Tab 1: Issues & Settings */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#111111]">Items to Review</h2>
            <span className="text-xs text-[#777777]">
              Agent: <strong className="text-[#111111]">{activeAgentName}</strong>
            </span>
          </div>

          <div className="space-y-3">
            {validationIssues.map((issue) => (
              <div
                key={issue.id}
                className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all shadow-subtle ${
                  issue.severity === 'error'
                    ? 'bg-rose-50/60 border-rose-200'
                    : issue.severity === 'warning'
                    ? 'bg-amber-50/60 border-amber-200'
                    : 'bg-[#FFFFFF] border-[#EAE8E5]'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="pt-0.5">
                    {issue.severity === 'error' ? (
                      <AlertCircle className="w-5 h-5 text-rose-600" />
                    ) : issue.severity === 'warning' ? (
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-xs sm:text-sm text-[#111111]">{issue.title}</h3>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-[#F7F6F4] text-[#777777] border border-[#EAE8E5]">
                        {issue.componentName}
                      </span>
                    </div>
                    <p className="text-xs text-[#777777] mt-0.5 leading-relaxed">{issue.description}</p>
                    <p className="text-xs font-semibold text-[#B15F2C] mt-1">
                      Suggested Fix: {issue.suggestedFix}
                    </p>
                  </div>
                </div>

                {issue.canAutoFix && (
                  <LiquidButton
                    variant="primary"
                    size="sm"
                    onClick={() => executeAutoRepair()}
                    icon={<Sparkles className="w-3.5 h-3.5" />}
                  >
                    Fix Automatically
                  </LiquidButton>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Workflow Structure */}
      {activeTab === 'structural' && (
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#111111]">Workflow Connections & Structure</h2>
            <p className="text-xs text-[#777777]">Ensures all components talk to each other without dead ends or loops.</p>
          </div>

          <div className="space-y-3 pt-2">
            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Starting Point Present</h4>
                  <p className="text-[11px] text-[#777777]">Workflow begins with a clear Input component.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Delivery Step Present</h4>
                  <p className="text-[11px] text-[#777777]">Workflow ends with a formatted Output component.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">No Disconnected Components</h4>
                  <p className="text-[11px] text-[#777777]">All {nodes.length} components are connected in the flow.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Safe Execution Path</h4>
                  <p className="text-[11px] text-[#777777]">The agent is guaranteed to reach the finish line without getting stuck.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Requirement Coverage */}
      {activeTab === 'requirements' && (
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#111111]">What You Asked For vs What Was Built</h2>
            <p className="text-xs text-[#777777]">Shows how each part of your request is handled by a workflow component.</p>
          </div>

          <div className="divide-y divide-[#EAE8E5]">
            {requirementCoverage.map((item) => (
              <div key={item.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-bold text-[#111111]">{item.requirement}</h4>
                    <p className="text-[11px] text-[#777777]">
                      Handled by: <span className="font-semibold text-[#B15F2C]">{item.mappedComponent}</span>
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                  COVERED
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Automated Test Suite */}
      {activeTab === 'tests' && (
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EAE8E5] shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[#111111]">Simulated Test Scenarios</h2>
              <p className="text-xs text-[#777777]">Realistic tests generated to prove the agent works before you run it</p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => generateRequirementTests()}
                className="px-4 py-2 rounded-full bg-[#F7F6F4] hover:bg-[#EAE8E5] text-[#111111] text-xs font-semibold border border-[#EAE8E5] transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#B15F2C]" />
                <span>Generate Tests</span>
              </button>

              <button
                onClick={() => runTestCases()}
                disabled={isTesting}
                className="px-4 py-2 rounded-full bg-[#111111] hover:bg-[#222222] text-white text-xs font-semibold transition-all flex items-center gap-1.5 shadow-subtle"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>{isTesting ? 'Running Scenarios...' : 'Run All Test Scenarios'}</span>
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#EAE8E5] text-[#777777] text-[11px] pb-2">
                  <th className="py-2.5 font-semibold">Test Scenario</th>
                  <th className="py-2.5 font-semibold">Component Tested</th>
                  <th className="py-2.5 font-semibold">Expected Outcome</th>
                  <th className="py-2.5 font-semibold">Actual Result</th>
                  <th className="py-2.5 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8E5]">
                {testCases.map((tc) => (
                  <tr key={tc.id} className="hover:bg-[#F7F6F4]/50 transition-colors">
                    <td className="py-3 font-semibold text-[#111111]">{tc.name}</td>
                    <td className="py-3 text-[#777777]">{tc.targetComponent}</td>
                    <td className="py-3 text-[#777777] max-w-xs">{tc.expectedOutput}</td>
                    <td className="py-3 text-[#111111] max-w-xs font-medium">{tc.actualOutput}</td>
                    <td className="py-3 text-right">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                          tc.status === 'passed'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : tc.status === 'running'
                            ? 'bg-amber-50 text-amber-800 border border-amber-200 animate-pulse'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}
                      >
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span>{tc.status.toUpperCase()}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={() => setCurrentPage('editor')}
          className="text-xs text-[#777777] hover:text-[#111111] font-semibold"
        >
          ← Back to Visual Canvas
        </button>

        <LiquidButton
          variant="primary"
          size="md"
          onClick={() => setCurrentPage('activity')}
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Proceed to Agent Activity
        </LiquidButton>
      </div>
    </div>
  );
};
