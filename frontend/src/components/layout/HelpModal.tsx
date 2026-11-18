import React from 'react';
import { X, Sparkles, Workflow, ShieldCheck, Wrench, CheckCircle2 } from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

export const HelpModal: React.FC = () => {
  const { isHelpOpen, setIsHelpOpen } = useWorkflow();

  if (!isHelpOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-in fade-in">
      <div className="bg-[#FFFFFF] rounded-3xl max-w-2xl w-full border border-[#E6E5E2] shadow-elevated overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-[#E6E5E2] flex items-center justify-between bg-[#FAF5F1]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#111111]">AgentForge AI User Guide</h2>
              <p className="text-xs text-[#8D8D8D]">Building autonomous agents without programming knowledge</p>
            </div>
          </div>
          <button
            onClick={() => setIsHelpOpen(false)}
            className="p-2 rounded-xl text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-[#111111]">
          {/* 4 Simple Steps */}
          <div>
            <h3 className="text-sm font-bold text-[#111111] mb-3">How to Build Your Agent in 4 Steps:</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-2xl bg-[#F1F0EE] border border-[#E6E5E2] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-[10px]">1</span>
                  <span>Describe in Words</span>
                </div>
                <p className="text-[#8D8D8D] leading-relaxed">
                  Tell AgentForge what you want to achieve, like "read resumes and score candidate skills."
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F1F0EE] border border-[#E6E5E2] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-[10px]">2</span>
                  <span>Review the Workflow</span>
                </div>
                <p className="text-[#8D8D8D] leading-relaxed">
                  AgentForge generates connected components on an interactive canvas that you can drag and inspect.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F1F0EE] border border-[#E6E5E2] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-[10px]">3</span>
                  <span>Check Your Agent</span>
                </div>
                <p className="text-[#8D8D8D] leading-relaxed">
                  Run automated test scenarios to verify inputs, connections, and outputs before live execution.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F1F0EE] border border-[#E6E5E2] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-[10px]">4</span>
                  <span>Automatic Self-Repair</span>
                </div>
                <p className="text-[#8D8D8D] leading-relaxed">
                  If any step fails, AgentForge AI diagnoses the problem and fixes the configuration with 1 click.
                </p>
              </div>
            </div>
          </div>

          {/* Component Cheat Sheet */}
          <div>
            <h3 className="text-sm font-bold text-[#111111] mb-2.5">Available Components:</h3>
            <div className="space-y-2 border border-[#E6E5E2] rounded-2xl divide-y divide-[#E6E5E2] overflow-hidden">
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-semibold text-[10px]">INPUT</div>
                <div>
                  <p className="font-semibold text-[#111111]">Input</p>
                  <p className="text-[#8D8D8D]">Accepts user prompts, files, or webhook triggers.</p>
                </div>
              </div>
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-amber-50 text-amber-800 font-semibold text-[10px]">PDF</div>
                <div>
                  <p className="font-semibold text-[#111111]">PDF Reader</p>
                  <p className="text-[#8D8D8D]">Extracts text and key sections from uploaded PDF documents.</p>
                </div>
              </div>
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-[#FAF5F1] text-[#B15F2C] font-semibold text-[10px]">AI</div>
                <div>
                  <p className="font-semibold text-[#111111]">AI Assistant (Gemini)</p>
                  <p className="text-[#8D8D8D]">Processes language, reasons through tasks, and evaluates data.</p>
                </div>
              </div>
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-blue-50 text-blue-800 font-semibold text-[10px]">LOGIC</div>
                <div>
                  <p className="font-semibold text-[#111111]">Condition</p>
                  <p className="text-[#8D8D8D]">Splits execution into branches based on rules and scores.</p>
                </div>
              </div>
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-purple-50 text-purple-800 font-semibold text-[10px]">GATE</div>
                <div>
                  <p className="font-semibold text-[#111111]">Human Approval</p>
                  <p className="text-[#8D8D8D]">Pauses for human sign-off before critical steps are executed.</p>
                </div>
              </div>
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-[#F1F0EE] text-[#111111] font-semibold text-[10px]">OUTPUT</div>
                <div>
                  <p className="font-semibold text-[#111111]">Output</p>
                  <p className="text-[#8D8D8D]">Presents final reports, summaries, or dispatches emails.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E6E5E2] bg-[#F1F0EE] flex justify-end">
          <button
            onClick={() => setIsHelpOpen(false)}
            className="px-5 py-2 rounded-xl bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white font-medium text-xs transition-colors"
          >
            Got it, let's build
          </button>
        </div>
      </div>
    </div>
  );
};

