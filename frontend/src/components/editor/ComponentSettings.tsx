import React, { useState, useEffect } from 'react';
import {
  X,
  Settings2,
  Copy,
  Trash2,
  Save,
  CheckCircle2,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Sliders,
  HelpCircle,
  FileText,
  Bot,
  GitFork,
  UserCheck,
  Wrench,
  FileOutput,
  FileInput,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { WorkflowNodeData, ComponentType } from '../../types';
import { ElevatedButton } from '../common/ElevatedButton';

const getBlockHeader = (type: ComponentType) => {
  switch (type) {
    case 'Input':
      return { tag: 'START', title: 'Start Settings', icon: FileInput, desc: 'Where the information begins' };
    case 'Document Reader':
      return { tag: 'READ', title: 'Read Document Settings', icon: FileText, desc: 'How documents are read' };
    case 'LLM':
      return { tag: 'THINK', title: 'AI Assistant Settings', icon: Bot, desc: 'What the assistant understands' };
    case 'Condition':
      return { tag: 'DECIDE', title: 'Decision Rule Settings', icon: GitFork, desc: 'Choose what happens next' };
    case 'Tool':
      return { tag: 'DO', title: 'Action Settings', icon: Wrench, desc: 'Perform an external action' };
    case 'Human Approval':
      return { tag: 'APPROVE', title: 'Approval Settings', icon: UserCheck, desc: 'Ask me before continuing' };
    case 'Output':
      return { tag: 'FINISH', title: 'Result Settings', icon: FileOutput, desc: 'Where the output goes' };
    default:
      return { tag: 'STEP', title: 'Step Settings', icon: Settings2, desc: 'Configure step parameters' };
  }
};

export const ComponentSettings: React.FC = () => {
  const {
    selectedNode,
    setSelectedNode,
    updateNodeConfig,
    deleteNode,
    duplicateNode,
    showToast,
  } = useWorkflow();

  const [label, setLabel] = useState('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  useEffect(() => {
    if (selectedNode) {
      const data = selectedNode.data as unknown as WorkflowNodeData;
      setLabel(data.label || '');
      setConfig(data.config || {});
    }
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <div className="w-80 bg-white border-l border-[#EAE8E5] flex flex-col items-center justify-center p-6 text-center select-none shadow-subtle">
        <div className="w-14 h-14 rounded-3xl bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 flex items-center justify-center mb-3 shadow-[0_3px_0_#EAE8E5,0_8px_16px_rgba(0,0,0,0.03)]">
          <Settings2 className="w-6 h-6" />
        </div>
        <h4 className="font-extrabold text-sm text-[#111111]">No Step Selected</h4>
        <p className="text-xs text-[#777777] mt-1.5 max-w-[220px] leading-relaxed">
          Click any building block on the canvas to customize what it does.
        </p>
      </div>
    );
  }

  const nodeData = selectedNode.data as unknown as WorkflowNodeData;
  const { componentType } = nodeData;
  const header = getBlockHeader(componentType);
  const Icon = header.icon;

  const handleSave = () => {
    updateNodeConfig(selectedNode.id, label, config);
    showToast('Saved', `Updated settings for "${label || header.title}"`, 'success');
  };

  const handleConfigChange = (field: string, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-80 bg-white border-l border-[#EAE8E5] flex flex-col h-full overflow-hidden select-none shadow-subtle">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#EAE8E5] flex items-center justify-between bg-[#FAF5F1]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-2xl bg-[#B15F2C] text-white flex items-center justify-center shadow-subtle">
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] font-extrabold px-1.5 py-0.2 rounded bg-white text-[#B15F2C] border border-[#CF8047]/30">
                {header.tag}
              </span>
              <h3 className="font-extrabold text-xs text-[#111111]">Customize This Step</h3>
            </div>
            <p className="text-[10px] text-[#777777] mt-0.5">{header.desc}</p>
          </div>
        </div>

        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-white transition-colors"
          title="Close panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Form Fields */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Step Display Label */}
        <div className="space-y-1.5">
          <label className="font-bold text-[#111111]">Step Name</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2.5 focus:outline-none focus:border-[#B15F2C] focus:bg-white transition-all shadow-subtle"
          />
          <p className="text-[10px] text-[#777777]">Name shown on the building block card.</p>
        </div>

        {/* AI Assistant (THINK) Settings */}
        {componentType === 'LLM' && (
          <>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Assistant Intelligence</label>
              <select
                value={config.model || 'Gemini 1.5 Pro (Recommended)'}
                onChange={(e) => handleConfigChange('model', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2.5 focus:outline-none focus:border-[#B15F2C] focus:bg-white"
              >
                <option value="Gemini 1.5 Pro (Recommended)">Gemini 1.5 Pro (Best for reasoning)</option>
                <option value="Gemini 1.5 Flash (Fast)">Gemini 1.5 Flash (Fastest)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="font-bold text-[#111111]">What should this assistant do?</label>
                <span className="text-[9px] font-bold text-[#B15F2C] bg-[#FAF5F1] px-1.5 py-0.5 rounded border border-[#CF8047]/30">
                  Required
                </span>
              </div>
              <textarea
                rows={4}
                value={config.instructions || ''}
                onChange={(e) => handleConfigChange('instructions', e.target.value)}
                placeholder="Explain in plain words... e.g. Read the candidate skills in React, TypeScript, and Python, then score fitness from 1 to 10."
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl p-3 focus:outline-none focus:border-[#B15F2C] focus:bg-white resize-none leading-relaxed transition-all shadow-subtle"
              />
              <p className="text-[10px] text-[#777777]">
                Explain what you want the assistant to look for and decide.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Creativity Level</label>
              <select
                value={config.creativity || 'Balanced (0.4)'}
                onChange={(e) => handleConfigChange('creativity', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
              >
                <option value="Precise & Factual (0.0)">Precise & Factual (Strict matching)</option>
                <option value="Balanced (0.4)">Balanced (Recommended)</option>
                <option value="Creative (0.8)">Creative (For writing & ideas)</option>
              </select>
            </div>
          </>
        )}

        {/* Read Document (READ) Settings */}
        {componentType === 'Document Reader' && (
          <>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Where does the document come from?</label>
              <select
                value={config.sourceInput || 'From User Input'}
                onChange={(e) => handleConfigChange('sourceInput', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="From User Input">Connected document from Start step</option>
                <option value="Fixed Sample File">Fixed sample resume (Demo)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">What should we read?</label>
              <select
                value={config.extractionMode || 'Text & Structured Sections'}
                onChange={(e) => handleConfigChange('extractionMode', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="Text & Structured Sections">All text and headings</option>
                <option value="Full Text Only">Raw text only</option>
                <option value="Tables & Metrics">Tables & Key Metrics</option>
              </select>
            </div>
          </>
        )}

        {/* Decision (DECIDE) Settings */}
        {componentType === 'Condition' && (
          <>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">What should we check?</label>
              <input
                type="text"
                value={config.fieldToCheck || 'fit_score'}
                onChange={(e) => handleConfigChange('fieldToCheck', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
              <p className="text-[10px] text-[#777777]">The information to evaluate (e.g. fit_score).</p>
            </div>

            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Rule to follow</label>
              <select
                value={config.rule || 'Greater Than or Equal To'}
                onChange={(e) => handleConfigChange('rule', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="Greater Than or Equal To">Greater Than or Equal To (≥)</option>
                <option value="Equals">Exactly Equals (=)</option>
                <option value="Contains Text">Contains specific word</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Target Value</label>
              <input
                type="text"
                value={config.targetValue || '7'}
                onChange={(e) => handleConfigChange('targetValue', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Human Approval (APPROVE) Settings */}
        {componentType === 'Human Approval' && (
          <>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Question for the reviewer</label>
              <textarea
                rows={3}
                value={config.approvalPrompt || 'Please review candidate score before the invite is dispatched.'}
                onChange={(e) => handleConfigChange('approvalPrompt', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl p-3 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Wait limit (Hours)</label>
              <input
                type="number"
                value={config.timeoutHours || 24}
                onChange={(e) => handleConfigChange('timeoutHours', parseInt(e.target.value))}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Output (FINISH) Settings */}
        {componentType === 'Output' && (
          <>
            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">How should results look?</label>
              <select
                value={config.format || 'Formatted Summary & Scorecard'}
                onChange={(e) => handleConfigChange('format', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="Formatted Summary & Scorecard">Summary Card & Scores</option>
                <option value="Markdown Report">Detailed Document Report</option>
                <option value="Clean JSON Object">Raw Data Record</option>
                <option value="PDF Document File">Downloadable PDF</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="font-bold text-[#111111]">Where should results go?</label>
              <input
                type="text"
                value={config.destination || 'Display in Dashboard & Email Candidate Brief'}
                onChange={(e) => handleConfigChange('destination', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Start (START) Settings */}
        {componentType === 'Input' && (
          <div className="space-y-1.5">
            <label className="font-bold text-[#111111]">Input Type</label>
            <select
              value={config.inputType || 'File Upload (PDF / Doc)'}
              onChange={(e) => handleConfigChange('inputType', e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
            >
              <option value="File Upload (PDF / Doc)">Document or Resume Upload</option>
              <option value="Text Prompt">Typed text or question</option>
              <option value="JSON Webhook Payload">Incoming web data</option>
            </select>
          </div>
        )}

        {/* Tool (DO) Settings */}
        {componentType === 'Tool' && (
          <div className="space-y-1.5">
            <label className="font-bold text-[#111111]">What action should run?</label>
            <select
              value={config.operation || 'Candidate Database Sync'}
              onChange={(e) => handleConfigChange('operation', e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
            >
              <option value="Candidate Database Sync">Candidate Database Sync</option>
              <option value="Web Search">Google Web Search</option>
              <option value="Send Email Dispatch">Send Email Notification</option>
              <option value="Python Script Runner">Python Calculator</option>
            </select>
          </div>
        )}

        {/* Collapsible Advanced Settings (Keeps interface uncluttered) */}
        <div className="pt-2 border-t border-[#EAE8E5]">
          <button
            type="button"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="w-full flex items-center justify-between text-xs font-bold text-[#777777] hover:text-[#111111] py-1 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#B15F2C]" />
              <span>Advanced Settings</span>
            </span>
            {isAdvancedOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {isAdvancedOpen && (
            <div className="mt-3 space-y-3 p-3 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5] animate-in fade-in">
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-[#777777]">Component ID</label>
                <div className="font-mono text-[10px] text-[#111111] p-1.5 rounded-lg bg-white border border-[#EAE8E5]">
                  {selectedNode.id}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-[#777777]">Timeout (seconds)</label>
                <input
                  type="number"
                  value={config.timeoutSeconds || 30}
                  onChange={(e) => handleConfigChange('timeoutSeconds', parseInt(e.target.value))}
                  className="w-full text-xs text-[#111111] bg-white border border-[#EAE8E5] rounded-lg px-2.5 py-1.5"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-[#777777]">Retry Policy</label>
                <select
                  value={config.retryPolicy || 'Auto-retry up to 2 times'}
                  onChange={(e) => handleConfigChange('retryPolicy', e.target.value)}
                  className="w-full text-xs text-[#111111] bg-white border border-[#EAE8E5] rounded-lg px-2 py-1.5"
                >
                  <option value="Auto-retry up to 2 times">Auto-retry up to 2 times (Default)</option>
                  <option value="Do not retry">Do not retry</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons in Footer with 3D Elevated Buttons */}
      <div className="p-4 border-t border-[#EAE8E5] bg-white space-y-2">
        <ElevatedButton
          variant="primary"
          size="md"
          onClick={handleSave}
          className="w-full"
          icon={<Save className="w-3.5 h-3.5" />}
        >
          Save Settings
        </ElevatedButton>

        <div className="grid grid-cols-2 gap-2">
          <ElevatedButton
            variant="secondary"
            size="sm"
            onClick={() => duplicateNode(selectedNode.id)}
            icon={<Copy className="w-3.5 h-3.5 text-[#777777]" />}
          >
            Duplicate
          </ElevatedButton>

          <ElevatedButton
            variant="destructive"
            size="sm"
            onClick={() => deleteNode(selectedNode.id)}
            icon={<Trash2 className="w-3.5 h-3.5" />}
          >
            Delete
          </ElevatedButton>
        </div>
      </div>
    </div>
  );
};
