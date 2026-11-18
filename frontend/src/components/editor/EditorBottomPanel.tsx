import React, { useState } from 'react';
import {
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  Terminal,
  FileCheck,
  Play,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

type TabType = 'results' | 'tests' | 'logs' | 'issues';

export const EditorBottomPanel: React.FC = () => {
  const {
    testCases,
    runTestCases,
    isTesting,
    validationIssues,
    currentExecution,
    runValidation,
    executeAutoRepair,
    triggerFailureScenario,
  } = useWorkflow();

  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('results');

  const errorCount = validationIssues.filter((i) => i.severity === 'error').length;
  const warningCount = validationIssues.filter((i) => i.severity === 'warning').length;

  return (
    <div className="border-t border-[#E6E5E2] bg-[#FFFFFF] flex flex-col z-20 shadow-subtle transition-all duration-200">
      {/* Tab Header Bar */}
      <div className="h-10 px-4 border-b border-[#E6E5E2] flex items-center justify-between bg-[#F1F0EE]/60 select-none">
        <div className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => {
              setActiveTab('results');
              setIsOpen(true);
            }}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'results'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#E6E5E2]'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            <FileCheck className="w-3.5 h-3.5 text-[#B15F2C]" />
            <span>Results</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('tests');
              setIsOpen(true);
            }}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'tests'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#E6E5E2]'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Test Cases ({testCases.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('logs');
              setIsOpen(true);
            }}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'logs'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#E6E5E2]'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            <Terminal className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span>Execution Logs</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('issues');
              setIsOpen(true);
            }}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'issues'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle border border-[#E6E5E2]'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>
              Issues
              {errorCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-rose-100 text-rose-800">
                  {errorCount}
                </span>
              )}
            </span>
          </button>
        </div>

        {/* Toggle open/collapse */}
        <div className="flex items-center gap-2">
          {activeTab === 'tests' && isOpen && (
            <button
              onClick={() => runTestCases()}
              disabled={isTesting}
              className="text-[11px] font-semibold text-[#B15F2C] hover:text-[#CF8047] flex items-center gap-1"
            >
              <Play className="w-3 h-3 fill-[#B15F2C]" />
              <span>{isTesting ? 'Running tests...' : 'Run All Tests'}</span>
            </button>
          )}

          {activeTab === 'issues' && isOpen && (
            <button
              onClick={() => triggerFailureScenario()}
              className="text-[11px] font-semibold text-rose-700 hover:text-rose-800 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-md"
            >
              Simulate Failure
            </button>
          )}

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded-lg text-[#8D8D8D] hover:text-[#111111] hover:bg-[#E3E2DF]"
            title={isOpen ? 'Collapse panel' : 'Expand panel'}
          >
            {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expandable Content Area */}
      {isOpen && (
        <div className="h-56 overflow-y-auto p-4 bg-[#FFFFFF] text-xs">
          {/* Results Tab */}
          {activeTab === 'results' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#E6E5E2]">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#111111]">Candidate Evaluation Scorecard</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                    Score: 8.5 / 10 (Recommended)
                  </span>
                </div>
                <span className="text-[11px] text-[#8D8D8D]">Output from: Evaluation Report Node</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-[#F1F0EE]/60 border border-[#E6E5E2] space-y-1">
                  <p className="font-semibold text-[#8D8D8D] text-[10px] uppercase">Candidate Profile</p>
                  <p className="font-bold text-sm text-[#111111]">Sarah Jenkins</p>
                  <p className="text-[11px] text-[#8D8D8D]">Senior Fullstack Engineer (7 yrs exp)</p>
                </div>
                <div className="p-3 rounded-xl bg-[#F1F0EE]/60 border border-[#E6E5E2] space-y-1">
                  <p className="font-semibold text-[#8D8D8D] text-[10px] uppercase">Key Matched Skills</p>
                  <p className="text-[11px] text-[#111111]">React 19, TypeScript, Python 3.11, FastAPI, System Architecture</p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-1">
                  <p className="font-semibold text-emerald-800 text-[10px] uppercase">Next Step</p>
                  <p className="font-bold text-emerald-900">Passed Threshold & Lead Approved</p>
                  <p className="text-[11px] text-emerald-700">Interview invitation dispatched via email.</p>
                </div>
              </div>
            </div>
          )}

          {/* Test Cases Tab */}
          {activeTab === 'tests' && (
            <div className="space-y-2">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E6E5E2] text-[#8D8D8D] text-[11px]">
                    <th className="pb-2 font-medium">Test Scenario</th>
                    <th className="pb-2 font-medium">Target Component</th>
                    <th className="pb-2 font-medium">Expected Result</th>
                    <th className="pb-2 font-medium">Actual Result</th>
                    <th className="pb-2 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E6E5E2]">
                  {testCases.map((tc) => (
                    <tr key={tc.id} className="py-2 hover:bg-[#F1F0EE]/40">
                      <td className="py-2 font-semibold text-[#111111]">{tc.name}</td>
                      <td className="py-2 text-[#8D8D8D]">{tc.targetComponent}</td>
                      <td className="py-2 text-[#8D8D8D] max-w-xs truncate">{tc.expectedOutput}</td>
                      <td className="py-2 text-[#111111] max-w-xs truncate">{tc.actualOutput}</td>
                      <td className="py-2 text-right">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            tc.status === 'passed'
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : tc.status === 'running'
                              ? 'bg-amber-50 text-amber-800 border border-amber-200'
                              : 'bg-rose-50 text-rose-800 border border-rose-200'
                          }`}
                        >
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>{tc.status.toUpperCase()}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Execution Logs Tab */}
          {activeTab === 'logs' && (
            <div className="space-y-2 font-mono text-[11px]">
              {currentExecution?.steps.map((st, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-[#F1F0EE]/60 border border-[#E6E5E2] flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[#8D8D8D]">{st.timestamp}</span>
                    <span className="font-semibold text-[#111111]">[{st.componentName}]</span>
                    <span className="text-[#8D8D8D]">{st.activity}</span>
                  </div>
                  <span
                    className={`font-semibold uppercase text-[10px] px-2 py-0.5 rounded ${
                      st.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : st.status === 'processing'
                        ? 'bg-amber-100 text-amber-800'
                        : st.status === 'failed'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-[#E3E2DF] text-[#8D8D8D]'
                    }`}
                  >
                    {st.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Issues Tab */}
          {activeTab === 'issues' && (
            <div className="space-y-2.5">
              {validationIssues.map((issue) => (
                <div
                  key={issue.id}
                  className={`p-3 rounded-xl border flex items-start justify-between gap-3 ${
                    issue.severity === 'error'
                      ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                      : issue.severity === 'warning'
                      ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                      : 'bg-blue-50/70 border-blue-200 text-blue-900'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs">{issue.title}</span>
                      <span className="text-[10px] uppercase font-semibold px-1.5 py-0.2 rounded bg-white/70">
                        {issue.componentName}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#111111]/80">{issue.description}</p>
                    <p className="text-[11px] font-medium text-[#B15F2C]">
                      Suggested Fix: {issue.suggestedFix}
                    </p>
                  </div>

                  {issue.canAutoFix && (
                    <button
                      onClick={() => executeAutoRepair()}
                      className="px-3 py-1.5 rounded-lg bg-[#B15F2C] hover:bg-[#CF8047] text-white text-[11px] font-semibold whitespace-nowrap shadow-sm flex items-center gap-1"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Fix Automatically</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

