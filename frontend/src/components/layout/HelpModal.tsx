import React from 'react';
import { X, Sparkles, Workflow, ShieldCheck, Wrench, CheckCircle2, Bot, FileText, FileOutput, GitFork, UserCheck, FileInput } from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';

export const HelpModal: React.FC = () => {
  const { isHelpOpen, setIsHelpOpen } = useWorkflow();

  if (!isHelpOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-in fade-in select-none">
      <div className="bg-white rounded-3xl max-w-2xl w-full border border-[#EAE8E5] shadow-glass overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-[#EAE8E5] flex items-center justify-between bg-[#FAF5F1]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center shadow-subtle">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-[#111111]">AgentForge AI User Guide</h2>
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
            <h3 className="text-sm font-extrabold text-[#111111] mb-3">How to Build Your Agent in 4 Steps:</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-bold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">1</span>
                  <span>Describe in Plain Words</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  Tell AgentForge what you want to achieve, like "read resumes and evaluate candidate skills."
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-bold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">2</span>
                  <span>Review the Building Blocks</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  AgentForge connects building blocks on a visual canvas that you can inspect, move, or customize.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-bold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">3</span>
                  <span>Check Your Agent</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  Verify connections, instructions, and run automated test scenarios before live execution.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] space-y-1">
                <div className="flex items-center gap-2 font-bold text-[#111111]">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px]">4</span>
                  <span>Automatic Self-Repair</span>
                </div>
                <p className="text-[#777777] leading-relaxed">
                  If any step runs into a problem, AgentForge AI diagnoses the issue and repairs it in 1 click.
                </p>
              </div>
            </div>
          </div>

          {/* 7 Building Blocks Cheat Sheet */}
          <div>
            <h3 className="text-sm font-extrabold text-[#111111] mb-2.5">The 7 Building Blocks:</h3>
            <div className="space-y-2 border border-[#EAE8E5] rounded-3xl divide-y divide-[#EAE8E5] overflow-hidden bg-white shadow-subtle">
              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-extrabold text-[10px]">START</div>
                <div>
                  <p className="font-bold text-[#111111]">Start Input</p>
                  <p className="text-[#777777]">Where the information begins (uploaded file, message, or webhook).</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-amber-50 text-amber-800 font-extrabold text-[10px]">READ</div>
                <div>
                  <p className="font-bold text-[#111111]">Read Document</p>
                  <p className="text-[#777777]">Reads information from PDF documents and resumes.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-[#FAF5F1] text-[#B15F2C] font-extrabold text-[10px]">THINK</div>
                <div>
                  <p className="font-bold text-[#111111]">Understand (AI Assistant)</p>
                  <p className="text-[#777777]">Understands information, reasons through steps, and scores results.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-blue-50 text-blue-800 font-extrabold text-[10px]">DECIDE</div>
                <div>
                  <p className="font-bold text-[#111111]">Decide</p>
                  <p className="text-[#777777]">Chooses what happens next based on a rule or score.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-teal-50 text-teal-800 font-extrabold text-[10px]">DO</div>
                <div>
                  <p className="font-bold text-[#111111]">Do Action (Tool)</p>
                  <p className="text-[#777777]">Performs an external action like syncing data, web search, or email.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-purple-50 text-purple-800 font-extrabold text-[10px]">APPROVE</div>
                <div>
                  <p className="font-bold text-[#111111]">Ask Me (Human Approval)</p>
                  <p className="text-[#777777]">Waits for your sign-off before carrying out critical actions.</p>
                </div>
              </div>

              <div className="p-3 flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-[#F7F6F4] text-[#111111] font-extrabold text-[10px]">FINISH</div>
                <div>
                  <p className="font-bold text-[#111111]">Show Result (Output)</p>
                  <p className="text-[#777777]">Delivers the final report, scorecard, or email dispatch.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer with 3D Elevated Button */}
        <div className="p-4 border-t border-[#EAE8E5] bg-[#F7F6F4] flex justify-end">
          <ElevatedButton
            variant="primary"
            size="md"
            onClick={() => setIsHelpOpen(false)}
            glow
          >
            Got it, let's build!
          </ElevatedButton>
        </div>
      </div>
    </div>
  );
};
