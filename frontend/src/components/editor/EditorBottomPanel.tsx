import React, { useState } from 'react';
import {
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Play,
  RotateCcw,
  Sparkles,
  Activity,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';

type TabType = 'results' | 'tests' | 'logs' | 'issues';

export const EditorBottomPanel: React.FC = () => {
  const {
    testCases,
    runTestCases,
    isTesting,
    validationIssues,
    currentExecution,
    executeAutoRepair,
    triggerFailureScenario,
  } = useWorkflow();

  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('results');

  const errorCount = validationIssues.filter((i) => i.severity === 'error').length;
  const warningCount = validationIssues.filter((i) => i.severity === 'warning').length;

  return (
    <div className="border-t border-[#EAE8E5] bg-white flex flex-col z-20 shadow-glass transition-all duration-200">
      {/* Tab Header Bar with Apple Liquid Glass feel */}
      <div className="h-11 px-4 border-b border-[#EAE8E5] flex items-center justify-between bg-[#F7F6F4]/90 backdrop-blur-md select-none">
        <div className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => {
              setActiveTab('results');
              setIsOpen(true);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'results'
                ? 'bg-white text-[#111111] shadow-[0_2px_0_#EAE8E5,0_3px_8px_rgba(0,0,0,0.03)] border border-[#EAE8E5]'
                : 'text-[#777777] hover:text-[#111111]'
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
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'tests'
                ? 'bg-white text-[#111111] shadow-[0_2px_0_#EAE8E5,0_3px_8px_rgba(0,0,0,0.03)] border border-[#EAE8E5]'
                : 'text-[#777777] hover:text-[#111111]'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Tests ({testCases.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('logs');
              setIsOpen(true);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'logs'
                ? 'bg-white text-[#111111] shadow-[0_2px_0_#EAE8E5,0_3px_8px_rgba(0,0,0,0.03)] border border-[#EAE8E5]'
                : 'text-[#777777] hover:text-[#111111]'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-[#111111]" />
            <span>Activity</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('issues');
              setIsOpen(true);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isOpen && activeTab === 'issues'
                ? 'bg-white text-[#111111] shadow-[0_2px_0_#EAE8E5,0_3px_8px_rgba(0,0,0,0.03)] border border-[#EAE8E5]'
                : 'text-[#777777] hover:text-[#111111]'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>
              Problems
              {errorCount > 0 && (
                <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] bg-rose-100 text-rose-800 font-extrabold">
                  {errorCount}
                </span>
              )}
            </span>
          </button>
        </div>

        {/* Action controls */}
        <div className="flex items-center gap-2">
          {activeTab === 'tests' && isOpen && (
            <ElevatedButton
              variant="secondary"
              size="sm"
              onClick={() => runTestCases()}
              loading={isTesting}
              loadingText="Testing..."
              icon={<Play className="w-3 h-3 fill-[#B15F2C] text-[#B15F2C]" />}
            >
              Run All Tests
            </ElevatedButton>
          )}

          {activeTab === 'issues' && isOpen && (
            <ElevatedButton
              variant="destructive"
              size="sm"
              onClick={() => triggerFailureScenario()}
            >
              Simulate Failure
            </ElevatedButton>
          )}

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#EAE8E5] transition-colors"
            title={isOpen ? 'Collapse panel' : 'Expand panel'}
          >
            {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expandable Content Area */}
      {isOpen && (
        <div className="h-56 overflow-y-auto p-4 bg-white text-xs">
          {/* Results Tab */}
          {activeTab === 'results' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE8E5]">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-[#111111]">Candidate Evaluation Summary</span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                    Score: 8.5 / 10 (Recommended)
                  </span>
                </div>
                <span className="text-[11px] text-[#777777]">Delivered by: Output Step</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1 shadow-subtle">
                  <p className="font-bold text-[#777777] text-[10px] uppercase tracking-wider">Candidate Profile</p>
                  <p className="font-extrabold text-sm text-[#111111]">Sarah Jenkins</p>
                  <p className="text-[11px] text-[#777777]">Senior Fullstack Engineer (7 yrs exp)</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1 shadow-subtle">
                  <p className="font-bold text-[#777777] text-[10px] uppercase tracking-wider">Matched Skills</p>
                  <p className="text-[11px] text-[#111111] leading-relaxed font-medium">React 19, TypeScript, Python 3.11, FastAPI, System Architecture</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-emerald-50/70 border border-emerald-200 space-y-1 shadow-subtle">
                  <p className="font-bold text-emerald-800 text-[10px] uppercase tracking-wider">Next Action</p>
                  <p className="font-extrabold text-emerald-900">Score &gt;= 7.0 & Lead Approved</p>
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
                  <tr className="border-b border-[#EAE8E5] text-[#777777] text-[11px]">
                    <th className="pb-2 font-semibold">Test Scenario</th>
                    <th className="pb-2 font-semibold">Step Checked</th>
                    <th className="pb-2 font-semibold">Expected Output</th>
                    <th className="pb-2 font-semibold">Actual Result</th>
                    <th className="pb-2 font-semibold text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EAE8E5]">
                  {testCases.map((tc) => (
                    <tr key={tc.id} className="py-2 hover:bg-[#F7F6F4]/50 transition-colors">
                      <td className="py-2.5 font-bold text-[#111111]">{tc.name}</td>
                      <td className="py-2.5 text-[#777777] font-medium">{tc.targetComponent}</td>
                      <td className="py-2.5 text-[#777777] max-w-xs truncate">{tc.expectedOutput}</td>
                      <td className="py-2.5 text-[#111111] max-w-xs truncate font-medium">{tc.actualOutput}</td>
                      <td className="py-2.5 text-right">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
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

          {/* Activity / Logs Tab */}
          {activeTab === 'logs' && (
            <div className="space-y-2 font-mono text-[11px]">
              {currentExecution?.steps.map((st, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-[#777777] text-[10px]">{st.timestamp}</span>
                    <span className="font-bold text-[#111111]">[{st.componentName}]</span>
                    <span className="text-[#777777]">{st.activity}</span>
                  </div>
                  <span
                    className={`font-bold uppercase text-[10px] px-2 py-0.5 rounded-md ${
                      st.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : st.status === 'processing'
                        ? 'bg-amber-100 text-amber-800'
                        : st.status === 'failed'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-[#EAE8E5] text-[#777777]'
                    }`}
                  >
                    {st.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Issues / Problems Tab */}
          {activeTab === 'issues' && (
            <div className="space-y-2.5">
              {validationIssues.map((issue) => (
                <div
                  key={issue.id}
                  className={`p-3.5 rounded-2xl border flex items-start justify-between gap-3 ${
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
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white border border-[#EAE8E5]">
                        {issue.componentName}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#111111]/80 leading-relaxed">{issue.description}</p>
                    <p className="text-[11px] font-bold text-[#B15F2C]">
                      Suggested Fix: {issue.suggestedFix}
                    </p>
                  </div>

                  {issue.canAutoFix && (
                    <ElevatedButton
                      variant="primary"
                      size="sm"
                      onClick={() => executeAutoRepair()}
                      icon={<Sparkles className="w-3.5 h-3.5" />}
                    >
                      Fix Automatically
                    </ElevatedButton>
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
