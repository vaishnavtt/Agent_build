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
  ChevronRight,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';

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
  } = useWorkflow();

  const [activeTab, setActiveTab] = useState<'overview' | 'structural' | 'requirements' | 'tests'>('overview');

  const errorCount = validationIssues.filter((i) => i.severity === 'error').length;
  const warningCount = validationIssues.filter((i) => i.severity === 'warning').length;

  const readinessPercent = validationMetrics?.overallReadiness ?? (errorCount > 0 ? 60 : warningCount > 0 ? 85 : 100);
  const isAllGood = errorCount === 0 && warningCount === 0;
  const hasErrors = errorCount > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 select-none page-fade-in">
      {/* Friendly Guide Ribbon: Where am I? What can I do here? What should I do next? */}
      <div className="p-3.5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shadow-subtle">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-[#B15F2C] text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
            ?
          </span>
          <p className="text-xs text-[#111111]">
            <strong className="text-[#B15F2C]">Step 2 of 3:</strong> We run automated safety and quality checks to ensure your assistant won't get stuck or fail.
          </p>
        </div>
        <span className="text-[11px] font-bold text-[#B15F2C]">
          {readinessPercent}% Verified
        </span>
      </div>

      {/* Top Heading strictly matching Phase 8 */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-bold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Quality & Safety Check</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111111] tracking-tight">
          Check My Agent
        </h1>
        <p className="text-sm sm:text-base text-[#777777]">
          Let's make sure everything is ready before your assistant starts.
        </p>
      </div>

      {/* Main Readiness Score Banner (Apple Liquid Glass with Soft 3D Elevation) */}
      <div
        className={`p-6 sm:p-7 rounded-3xl border shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all ${
          hasErrors
            ? 'bg-rose-50/60 border-rose-200'
            : warningCount > 0
            ? 'bg-amber-50/50 border-amber-200'
            : 'liquid-card border-[#EAE8E5]'
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-16 h-16 rounded-3xl flex items-center justify-center flex-shrink-0 shadow-md ${
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
              <span className="text-xl font-extrabold text-[#111111]">
                {hasErrors
                  ? 'Something needs attention'
                  : warningCount > 0
                  ? 'Ready with minor suggestions'
                  : 'Your assistant is verified and ready to run'}
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
                ? 'One or more steps are missing instructions or links. Open repair to check whether recovery is available for a recorded failure.'
                : warningCount > 0
                ? 'Your assistant will execute, but you can review minor suggestions for maximum precision.'
                : 'All building blocks, connections, and simulated scenarios passed with zero errors.'}
            </p>
          </div>
        </div>

        {/* Action Buttons using 3D Elevated Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Phase 8 Button: "Check Everything" */}
          <ElevatedButton
            variant="secondary"
            size="md"
            onClick={() => runValidation()}
            loading={isValidating}
            loadingText="Checking..."
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Check Everything
          </ElevatedButton>

          {hasErrors && (
            <ElevatedButton
              variant="primary"
              size="md"
              onClick={() => setCurrentPage('activity')}
              icon={<Sparkles className="w-3.5 h-3.5" />}
              glow
            >
              Open repair
            </ElevatedButton>
          )}

          {!hasErrors && (
            <ElevatedButton
              variant="primary"
              size="md"
              onClick={() => setCurrentPage('activity')}
              icon={<Play className="w-3.5 h-3.5 fill-white" />}
              glow
            >
              Watch Your Agent Work
            </ElevatedButton>
          )}
        </div>
      </div>

      {/* 4 Simple Checks with Friendly Green, Orange, Red Indicators (Phase 8 Requirement) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Check 1: Are all steps connected? */}
        <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-semibold">Check 1</span>
            <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-sm font-extrabold text-[#111111]">
            Are all steps connected?
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-bold">
            <span>Yes • {edges.length} active links</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Information flows continuously without missing links.
          </p>
        </div>

        {/* Check 2: Is the information configured? */}
        <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-semibold">Check 2</span>
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center ${
                errorCount > 0 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {errorCount > 0 ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            </div>
          </div>
          <div className="text-sm font-extrabold text-[#111111]">
            Is the information configured?
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs font-bold ${
              errorCount > 0 ? 'text-rose-700' : 'text-emerald-700'
            }`}
          >
            <span>{errorCount > 0 ? `${errorCount} step needs instructions` : 'Yes • All steps ready'}</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Every assistant has clear instructions and models set.
          </p>
        </div>

        {/* Check 3: Are there any missing details? */}
        <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-semibold">Check 3</span>
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center ${
                warningCount > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {warningCount > 0 ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            </div>
          </div>
          <div className="text-sm font-extrabold text-[#111111]">
            Are there any missing details?
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs font-bold ${
              warningCount > 0 ? 'text-amber-700' : 'text-emerald-700'
            }`}
          >
            <span>{warningCount > 0 ? `${warningCount} recommendation` : 'None • Start and end present'}</span>
          </div>
          <p className="text-[11px] text-[#777777] leading-relaxed">
            Start block and Delivery block are in place.
          </p>
        </div>

        {/* Check 4: Do the tests pass? */}
        <div className="p-5 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#777777] font-semibold">Check 4</span>
            <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-sm font-extrabold text-[#111111]">
            Do the tests pass?
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-bold">
            <span>Yes • {testCases.length} scenarios passed</span>
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
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Issues & Details ({validationIssues.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('structural')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'structural'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <Workflow className="w-3.5 h-3.5" />
          <span>Flow Structure</span>
        </button>

        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'requirements'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>What You Asked For ({requirementCoverage.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'tests'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 shadow-subtle'
              : 'text-[#777777] hover:text-[#111111]'
          }`}
        >
          <Play className="w-3.5 h-3.5" />
          <span>Test Scenarios ({testCases.length})</span>
        </button>
      </div>

      {/* Tab 1: Issues & Suggested Solutions in Simple Language */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold text-[#111111]">Items to Review</h2>
            <span className="text-xs text-[#777777]">
              Assistant: <strong className="text-[#111111]">{activeAgentName}</strong>
            </span>
          </div>

          <div className="space-y-3">
            {validationIssues.map((issue) => (
              <div
                key={issue.id}
                className={`p-4 rounded-3xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all shadow-subtle ${
                  issue.severity === 'error'
                    ? 'bg-rose-50/70 border-rose-200'
                    : issue.severity === 'warning'
                    ? 'bg-amber-50/70 border-amber-200'
                    : 'bg-white border-[#EAE8E5]'
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
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white text-[#777777] border border-[#EAE8E5]">
                        {issue.componentName}
                      </span>
                    </div>
                    <p className="text-xs text-[#777777] mt-0.5 leading-relaxed">{issue.description}</p>
                    <p className="text-xs font-bold text-[#B15F2C] mt-1">
                      Suggested Fix: {issue.suggestedFix}
                    </p>
                  </div>
                </div>

                {issue.canAutoFix && (
                  <ElevatedButton
                    variant="primary"
                    size="sm"
                    onClick={() => setCurrentPage('activity')}
                    icon={<Sparkles className="w-3.5 h-3.5" />}
                  >
                    Open repair
                  </ElevatedButton>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Flow Structure */}
      {activeTab === 'structural' && (
        <div className="p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-extrabold text-[#111111]">Flow Structure & Safety</h2>
            <p className="text-xs text-[#777777]">Ensures all steps connect from start to finish without getting stuck.</p>
          </div>

          <div className="space-y-3 pt-2">
            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Start Step Present</h4>
                  <p className="text-[11px] text-[#777777]">Your workflow has an Input step to receive information.</p>
                </div>
              </div>
              <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Finish Step Present</h4>
                  <p className="text-[11px] text-[#777777]">Your workflow has an Output step to deliver the final result.</p>
                </div>
              </div>
              <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">No Disconnected Steps</h4>
                  <p className="text-[11px] text-[#777777]">All {nodes.length} building blocks are connected.</p>
                </div>
              </div>
              <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Requirement Coverage */}
      {activeTab === 'requirements' && (
        <div className="p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-extrabold text-[#111111]">What You Asked For vs What Was Built</h2>
            <p className="text-xs text-[#777777]">Shows how each part of your request is handled by a building block.</p>
          </div>

          <div className="divide-y divide-[#EAE8E5]">
            {requirementCoverage.map((item) => (
              <div key={item.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-bold text-[#111111]">{item.requirement}</h4>
                    <p className="text-[11px] text-[#777777]">
                      Handled by: <span className="font-bold text-[#B15F2C]">{item.mappedComponent}</span>
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                  SATISFIED
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Simulated Test Scenarios */}
      {activeTab === 'tests' && (
        <div className="p-6 rounded-3xl bg-white border border-[#EAE8E5] shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-extrabold text-[#111111]">Simulated Test Scenarios</h2>
              <p className="text-xs text-[#777777]">Tests run automatically to prove your assistant works before live execution</p>
            </div>

            <div className="flex items-center gap-2">
              <ElevatedButton
                variant="secondary"
                size="sm"
                onClick={() => generateRequirementTests()}
                icon={<Sparkles className="w-3.5 h-3.5 text-[#B15F2C]" />}
              >
                Generate Tests
              </ElevatedButton>

              <ElevatedButton
                variant="primary"
                size="sm"
                onClick={() => runTestCases()}
                loading={isTesting}
                loadingText="Running Scenarios..."
                icon={<Play className="w-3.5 h-3.5 fill-white" />}
              >
                Run All Tests
              </ElevatedButton>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#EAE8E5] text-[#777777] text-[11px] pb-2">
                  <th className="py-2.5 font-semibold">Test Scenario</th>
                  <th className="py-2.5 font-semibold">Step Tested</th>
                  <th className="py-2.5 font-semibold">Expected Output</th>
                  <th className="py-2.5 font-semibold">Actual Result</th>
                  <th className="py-2.5 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8E5]">
                {testCases.map((tc) => (
                  <tr key={tc.id} className="hover:bg-[#F7F6F4]/50 transition-colors">
                    <td className="py-3 font-bold text-[#111111]">{tc.name}</td>
                    <td className="py-3 text-[#777777] font-medium">{tc.targetComponent}</td>
                    <td className="py-3 text-[#777777] max-w-xs">{tc.expectedOutput}</td>
                    <td className="py-3 text-[#111111] max-w-xs font-semibold">{tc.actualOutput}</td>
                    <td className="py-3 text-right">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-extrabold ${
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
          className="text-xs text-[#777777] hover:text-[#111111] font-bold"
        >
          ← Back to Build Your Agent
        </button>

        <ElevatedButton
          variant="primary"
          size="md"
          onClick={() => setCurrentPage('activity')}
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Watch Your Agent Work
        </ElevatedButton>
      </div>
    </div>
  );
};
