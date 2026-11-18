import React, { useState } from 'react';
import {
  Settings,
  Sparkles,
  ShieldCheck,
  Key,
  Sliders,
  Check,
  Bot,
  Info,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

export const SettingsPage: React.FC = () => {
  const { showToast } = useWorkflow();

  const [defaultModel, setDefaultModel] = useState('Gemini 1.5 Pro (Recommended)');
  const [autoRepairEnabled, setAutoRepairEnabled] = useState(true);
  const [maxRepairAttempts, setMaxRepairAttempts] = useState(2);
  const [executionTimeout, setExecutionTimeout] = useState(300);

  const handleSave = () => {
    showToast('Preferences Saved', 'Your system preferences have been updated.', 'success');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <Settings className="w-3.5 h-3.5" />
          <span>System & Preferences</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Settings
        </h1>
        <p className="text-sm text-[#8D8D8D]">
          Configure default AI models, automated repair policies, and runtime boundaries.
        </p>
      </div>

      {/* Model & AI Settings Card */}
      <div className="p-6 sm:p-7 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-5">
        <div className="flex items-center gap-3 pb-3 border-b border-[#E6E5E2]">
          <div className="w-9 h-9 rounded-xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/20 flex items-center justify-center">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-sm text-[#111111]">AI Reasoning Engine</h2>
            <p className="text-xs text-[#8D8D8D]">Google Gemini API runtime parameters</p>
          </div>
        </div>

        <div className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-[#111111]">Default AI Model</label>
            <select
              value={defaultModel}
              onChange={(e) => setDefaultModel(e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2.5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
            >
              <option value="Gemini 1.5 Pro (Recommended)">Gemini 1.5 Pro (Advanced reasoning & workflow planning)</option>
              <option value="Gemini 1.5 Flash (Fast)">Gemini 1.5 Flash (Ultra-low latency execution)</option>
            </select>
            <p className="text-[11px] text-[#8D8D8D]">
              Used when synthesizing workflows from natural language or executing AI Assistant nodes.
            </p>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-[#111111]">Maximum Execution Timeout (Seconds)</label>
            <input
              type="number"
              min={30}
              max={1800}
              value={executionTimeout}
              onChange={(e) => setExecutionTimeout(parseInt(e.target.value))}
              className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2.5"
            />
            <p className="text-[11px] text-[#8D8D8D]">
              Workflows taking longer than this will safely pause for review.
            </p>
          </div>
        </div>
      </div>

      {/* Autonomous Self-Repair Policy Card */}
      <div className="p-6 sm:p-7 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-5">
        <div className="flex items-center gap-3 pb-3 border-b border-[#E6E5E2]">
          <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-sm text-[#111111]">Autonomous Self-Repair Policy</h2>
            <p className="text-xs text-[#8D8D8D]">Rules governing automated fault detection and patching</p>
          </div>
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between p-3 rounded-2xl bg-[#F1F0EE]/50 border border-[#E6E5E2]">
            <div>
              <p className="font-semibold text-[#111111]">Enable Automatic Self-Repair</p>
              <p className="text-[11px] text-[#8D8D8D]">
                Allow AgentForge AI to analyze failed nodes and suggest 1-click automatic fixes.
              </p>
            </div>
            <input
              type="checkbox"
              checked={autoRepairEnabled}
              onChange={(e) => setAutoRepairEnabled(e.target.checked)}
              className="w-4 h-4 accent-[#B15F2C] rounded cursor-pointer"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-[#111111]">Maximum Automatic Repair Attempts</label>
            <input
              type="number"
              min={1}
              max={2}
              value={maxRepairAttempts}
              onChange={(e) => setMaxRepairAttempts(parseInt(e.target.value))}
              className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2.5"
            />
            <p className="text-[11px] text-[#8D8D8D]">
              Strictly limited to 2 attempts max to prevent circular modifications.
            </p>
          </div>
        </div>
      </div>

      {/* Security & API Key Notice */}
      <div className="p-5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30 text-xs text-[#111111] flex items-start gap-3">
        <Info className="w-5 h-5 text-[#B15F2C] flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-xs text-[#111111]">Secure Backend Environment Notice</p>
          <p className="text-[#8D8D8D] leading-relaxed">
            API keys and credentials are never stored in the browser frontend. Production keys for Google Gemini API and database connections are safely loaded from the server's <code className="bg-white px-1.5 py-0.5 rounded border border-[#CF8047]/20 font-mono text-[10px]">.env</code> configuration.
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="px-6 py-2.5 rounded-full bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs font-bold shadow-sm transition-all"
        >
          Save Preferences
        </button>
      </div>
    </div>
  );
};

