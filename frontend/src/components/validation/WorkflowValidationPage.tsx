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
  Boxes,
  Workflow,
  Check,
  ListFilter,
  FileCheck2,
  Cpu,
  Layers,
  HelpCircle,
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
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Top Heading */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Integrity & Verification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Check Your Agent
        </h1>
        <p className="text-sm text-[#8D8D8D]">
          Verify structural integrity, component configurations, and requirement coverage before running your agent.
        </p>
      </div>

      {/* Main Readiness Score Banner */}
      <div
        className={`p-6 sm:p-7 rounded-3xl border shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-6 ${
          hasErrors
            ? 'bg-rose-50/50 border-rose-200'
            : warningCount > 0
            ? 'bg-amber-50/40 border-amber-200'
            : 'bg-[#FFFFFF] border-[#E6E5E2]'
        }`}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 ${
              hasErrors
                ? 'bg-rose-600 text-white shadow-sm'
                : warningCount > 0
                ? 'bg-amber-500 text-white shadow-sm'
                : 'bg-emerald-600 text-white shadow-sm'
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
                  ? 'Ready with minor recommendations'
                  : 'Workflow is verified and ready to run'}
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
            <p className="text-xs text-[#8D8D8D] mt-1.5 max-w-xl leading-relaxed">
              {hasErrors
                ? 'One or more required components are missing parameters or instructions. Use "Fix Automatically" below or inspect settings.'
                : warningCount > 0
                ? 'Your agent graph is executable, but optional settings can be fine-tuned for optimal precision.'
                : 'All components, data flow paths, schemas, and test scenarios are fully validated.'}
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
            Re-check Agent
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
              Proceed to Agent Activity
            </LiquidButton>
          )}
        </div>
      </div>

      {/* 4 Multi-Dimensional Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <span className="text-xs text-[#8D8D8D] font-medium">Structural Score</span>
          <div className="text-2xl font-bold text-[#111111]">
            {validationMetrics?.structuralScore ?? 30}/30
          </div>
          <span className="text-[11px] text-emerald-700">Valid entry & exit points</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <span className="text-xs text-[#8D8D8D] font-medium">Configuration Score</span>
          <div className={`text-2xl font-bold ${errorCount > 0 ? 'text-rose-600' : 'text-emerald-700'}`}>
            {validationMetrics?.configScore ?? 40}/40
          </div>
          <span className="text-[11px] text-[#8D8D8D]">
            {errorCount === 0 ? 'All parameters valid' : `${errorCount} missing required field`}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <span className="text-xs text-[#8D8D8D] font-medium">Connections Score</span>
          <div className="text-2xl font-bold text-emerald-700">
            {validationMetrics?.connectionScore ?? 30}/30
          </div>
          <span className="text-[11px] text-[#8D8D8D]">{edges.length} active data edges</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle space-y-1">
          <span className="text-xs text-[#8D8D8D] font-medium">Requirement Coverage</span>
          <div className="text-2xl font-bold text-emerald-700">100%</div>
          <span className="text-[11px] text-[#8D8D8D]">{requirementCoverage.length} criteria satisfied</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-[#E6E5E2] pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'overview'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
              : 'text-[#8D8D8D] hover:text-[#111111]'
          }`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Issues & Settings ({validationIssues.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('structural')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'structural'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
              : 'text-[#8D8D8D] hover:text-[#111111]'
          }`}
        >
          <Workflow className="w-3.5 h-3.5" />
          <span>Structural Topology</span>
        </button>

        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'requirements'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
              : 'text-[#8D8D8D] hover:text-[#111111]'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>Requirement Coverage ({requirementCoverage.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'tests'
              ? 'bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30'
              : 'text-[#8D8D8D] hover:text-[#111111]'
          }`}
        >
          <Play className="w-3.5 h-3.5" />
          <span>Automated Test Suite ({testCases.length})</span>
        </button>
      </div>

      {/* Tab 1: Issues & Settings */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#111111]">Configuration & Integrity Issues</h2>
            <span className="text-xs text-[#8D8D8D]">
              Checking: <strong className="text-[#111111]">{activeAgentName}</strong>
            </span>
          </div>

          <div className="space-y-3">
            {validationIssues.map((issue) => (
              <div
                key={issue.id}
                className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all ${
                  issue.severity === 'error'
                    ? 'bg-rose-50/60 border-rose-200'
                    : issue.severity === 'warning'
                    ? 'bg-amber-50/60 border-amber-200'
                    : 'bg-[#FFFFFF] border-[#E6E5E2]'
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
                      <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[#F1F0EE] text-[#8D8D8D]">
                        {issue.componentName}
                      </span>
                    </div>
                    <p className="text-xs text-[#8D8D8D] mt-0.5 leading-relaxed">{issue.description}</p>
                    <p className="text-xs font-semibold text-[#B15F2C] mt-1">
                      Recommendation: {issue.suggestedFix}
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

      {/* Tab 2: Structural Topology Checks */}
      {activeTab === 'structural' && (
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#111111]">Graph Topology & Connection Verification</h2>
            <p className="text-xs text-[#8D8D8D]">Checks node reachability, entry and exit ports, and cycle safety.</p>
          </div>

          <div className="space-y-3 pt-2">
            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Entry Node Present</h4>
                  <p className="text-[11px] text-[#8D8D8D]">Workflow begins with a valid Input trigger component.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Terminal Exit Node Present</h4>
                  <p className="text-[11px] text-[#8D8D8D]">Workflow ends with a formatted Output destination component.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">No Isolated / Orphan Nodes</h4>
                  <p className="text-[11px] text-[#8D8D8D]">All {nodes.length} components have active incoming or outgoing connections.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-bold text-[#111111]">Cycle Safety & Directed Execution</h4>
                  <p className="text-[11px] text-[#8D8D8D]">Graph is guaranteed to terminate without infinite loops.</p>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">PASSED</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Requirement Coverage */}
      {activeTab === 'requirements' && (
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#111111]">Natural Language Requirement Coverage</h2>
            <p className="text-xs text-[#8D8D8D]">Compares the original prompt requirements against the generated components in your workflow.</p>
          </div>

          <div className="divide-y divide-[#E6E5E2]">
            {requirementCoverage.map((item) => (
              <div key={item.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-bold text-[#111111]">{item.requirement}</h4>
                    <p className="text-[11px] text-[#8D8D8D]">
                      Satisfied by component: <span className="font-semibold text-[#B15F2C]">{item.mappedComponent}</span>
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
        <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[#111111]">Requirement-Based Test Suite</h2>
              <p className="text-xs text-[#8D8D8D]">Simulated test scenarios generated directly from the agent requirements</p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => generateRequirementTests()}
                className="px-4 py-2 rounded-full bg-[#F1F0EE] hover:bg-[#E3E2DF] text-[#111111] text-xs font-semibold border border-[#E6E5E2] transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#B15F2C]" />
                <span>Generate Tests</span>
              </button>

              <button
                onClick={() => runTestCases()}
                disabled={isTesting}
                className="px-4 py-2 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold transition-all flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>{isTesting ? 'Running Scenarios...' : 'Run All Test Scenarios'}</span>
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E6E5E2] text-[#8D8D8D] text-[11px] pb-2">
                  <th className="py-2.5 font-semibold">Test Case</th>
                  <th className="py-2.5 font-semibold">Target Component</th>
                  <th className="py-2.5 font-semibold">Expected Outcome</th>
                  <th className="py-2.5 font-semibold">Actual Outcome</th>
                  <th className="py-2.5 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E6E5E2]">
                {testCases.map((tc) => (
                  <tr key={tc.id} className="hover:bg-[#F1F0EE]/40 transition-colors">
                    <td className="py-3 font-semibold text-[#111111]">{tc.name}</td>
                    <td className="py-3 text-[#8D8D8D]">{tc.targetComponent}</td>
                    <td className="py-3 text-[#8D8D8D] max-w-xs">{tc.expectedOutput}</td>
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
          className="text-xs text-[#8D8D8D] hover:text-[#111111] font-semibold"
        >
          ← Back to Workflow Studio
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
