import React from 'react';
import { X, Sparkles, Workflow, ShieldCheck, Wrench, CheckCircle2 } from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { LiquidButton } from '../common/LiquidButton';

export const HelpModal: React.FC = () => {
  const { isHelpOpen, setIsHelpOpen } = useWorkflow();

  if (!isHelpOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-in fade-in select-none">
      <div className="bg-[#FFFFFF] rounded-3xl max-w-2xl w-full border border-[#EAE8E5] shadow-glass overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-[#EAE8E5] flex items-center justify-between bg-[#FAF5F1]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center shadow-subtle">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#111111]">AgentForge AI User Guide</h2>
              <p className="text-xs text-[#777777]">Build your own AI agents without writing code</p>
            </div>
          </div>
          <button
            onClick={() => setIsHelpOpen(false)}
            className="p-2 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] transition-colors"
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
              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">1</span>
                  <span>Describe in Plain Words</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  Tell AgentForge what you want to achieve, like "read resumes and score candidate skills."
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">2</span>
                  <span>Review the Workflow</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  AgentForge generates connected components on an interactive canvas that you can inspect and move.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">3</span>
                  <span>Check Your Agent</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  Verify connections, instructions, and run automated test scenarios before live execution.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-semibold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">4</span>
                  <span>Automatic Self-Repair</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  If any step runs into a problem, AgentForge AI diagnoses the issue and repairs it in 1 click.
                </p>
              </div>
            </div>
          </div>

          {/* 7 Canonical Components Cheat Sheet */}
          <div>
            <h3 className="text-sm font-bold text-[#111111] mb-2.5">What Can Your Agent Use?</h3>
            <div className="space-y-2 border border-[#EAE8E5] rounded-2xl divide-y divide-[#EAE8E5] overflow-hidden">
              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-bold text-[10px]">INPUT</div>
                <div>
                  <p className="font-semibold text-[#111111]">Input</p>
                  <p className="text-[#777777]">Receives information, files, or messages to start your agent.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-amber-50 text-amber-800 font-bold text-[10px]">PDF</div>
                <div>
                  <p className="font-semibold text-[#111111]">PDF Reader</p>
                  <p className="text-[#777777]">Reads information from PDF documents and resumes.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-[#FAF5F1] text-[#B15F2C] font-bold text-[10px]">AI</div>
                <div>
                  <p className="font-semibold text-[#111111]">AI Assistant (Gemini)</p>
                  <p className="text-[#777777]">Understands information, reasons through steps, and writes answers.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-teal-50 text-teal-800 font-bold text-[10px]">TOOL</div>
                <div>
                  <p className="font-semibold text-[#111111]">Tool</p>
                  <p className="text-[#777777]">Searches the web, calculates numbers, or fetches database info.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-blue-50 text-blue-800 font-bold text-[10px]">DECISION</div>
                <div>
                  <p className="font-semibold text-[#111111]">Decision</p>
                  <p className="text-[#777777]">Chooses what happens next based on a rule or score.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-purple-50 text-purple-800 font-bold text-[10px]">APPROVAL</div>
                <div>
                  <p className="font-semibold text-[#111111]">Human Approval</p>
                  <p className="text-[#777777]">Asks a person for permission before continuing important actions.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3 bg-[#FFFFFF]">
                <div className="p-1.5 rounded-lg bg-[#F7F6F4] text-[#111111] font-bold text-[10px]">OUTPUT</div>
                <div>
                  <p className="font-semibold text-[#111111]">Output</p>
                  <p className="text-[#777777]">Delivers the final result, report, email, or summary.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#EAE8E5] bg-[#F7F6F4] flex justify-end">
          <LiquidButton
            variant="primary"
            size="md"
            onClick={() => setIsHelpOpen(false)}
            glow
          >
            Got it, let's build
          </LiquidButton>
        </div>
      </div>
    </div>
  );
};
