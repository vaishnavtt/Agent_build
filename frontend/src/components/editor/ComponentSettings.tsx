import React, { useState, useEffect } from 'react';
import {
  X,
  Settings2,
  Copy,
  Trash2,
  Save,
  CheckCircle2,
  Sparkles,
  HelpCircle,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { WorkflowNodeData } from '../../types';

export const ComponentSettings: React.FC = () => {
  const { selectedNode, setSelectedNode, updateNodeConfig, deleteNode, duplicateNode } = useWorkflow();

  const [label, setLabel] = useState('');
  const [config, setConfig] = useState<Record<string, any>>({});

  useEffect(() => {
    if (selectedNode) {
      const data = selectedNode.data as unknown as WorkflowNodeData;
      setLabel(data.label || '');
      setConfig(data.config || {});
    }
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <div className="w-80 bg-[#FFFFFF] border-l border-[#E6E5E2] flex flex-col items-center justify-center p-6 text-center select-none">
        <div className="w-12 h-12 rounded-2xl bg-[#F1F0EE] text-[#8D8D8D] flex items-center justify-center mb-3">
          <Settings2 className="w-6 h-6" />
        </div>
        <h4 className="font-bold text-sm text-[#111111]">No Component Selected</h4>
        <p className="text-xs text-[#8D8D8D] mt-1 max-w-[200px] leading-relaxed">
          Click any component on the visual canvas to inspect or adjust its settings.
        </p>
      </div>
    );
  }

  const nodeData = selectedNode.data as unknown as WorkflowNodeData;
  const { componentType } = nodeData;

  const handleSave = () => {
    updateNodeConfig(selectedNode.id, label, config);
  };

  const handleConfigChange = (field: string, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-80 bg-[#FFFFFF] border-l border-[#E6E5E2] flex flex-col h-full overflow-hidden select-none">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#E6E5E2] flex items-center justify-between bg-[#FAF5F1]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-[#B15F2C] text-white flex items-center justify-center shadow-sm">
            <Settings2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-xs text-[#111111]">Component Settings</h3>
            <span className="text-[10px] text-[#B15F2C] font-semibold">{componentType}</span>
          </div>
        </div>

        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 rounded-lg text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE]"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Form Fields */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Component Display Label */}
        <div className="space-y-1">
          <label className="font-semibold text-[#111111]">Display Name</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
          />
          <p className="text-[10px] text-[#8D8D8D]">Friendly name shown on the visual canvas.</p>
        </div>

        {/* AI Assistant Specific Settings */}
        {componentType === 'LLM' && (
          <>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">AI Model</label>
              <select
                value={config.model || 'Gemini 1.5 Pro (Recommended)'}
                onChange={(e) => handleConfigChange('model', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
              >
                <option value="Gemini 1.5 Pro (Recommended)">Gemini 1.5 Pro (Recommended for reasoning)</option>
                <option value="Gemini 1.5 Flash (Fast)">Gemini 1.5 Flash (Fast & lightweight)</option>
              </select>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-[#111111]">What should the AI do?</label>
                <span className="text-[10px] text-[#B15F2C] font-semibold">Important</span>
              </div>
              <textarea
                rows={4}
                value={config.instructions || ''}
                onChange={(e) => handleConfigChange('instructions', e.target.value)}
                placeholder="Give clear, plain English instructions... e.g. Analyze candidate skills in React, TypeScript, Python and score alignment from 1 to 10."
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl p-3 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] resize-none leading-relaxed"
              />
              <p className="text-[10px] text-[#8D8D8D]">
                These instructions guide how the AI processes incoming information.
              </p>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Creativity Level</label>
              <select
                value={config.creativity || 'Balanced (0.4)'}
                onChange={(e) => handleConfigChange('creativity', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
              >
                <option value="Precise & Factual (0.0)">Precise & Factual (for structured scoring)</option>
                <option value="Balanced (0.4)">Balanced (Recommended)</option>
                <option value="Creative (0.8)">Creative (for copywriting)</option>
              </select>
            </div>
          </>
        )}

        {/* PDF Reader Settings */}
        {componentType === 'Document Reader' && (
          <>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Input Source</label>
              <select
                value={config.sourceInput || 'From User Input'}
                onChange={(e) => handleConfigChange('sourceInput', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              >
                <option value="From User Input">Connected User Input Document</option>
                <option value="Fixed Sample File">Fixed Sample Resume (Demo mode)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Extraction Options</label>
              <select
                value={config.extractionMode || 'Text & Structured Sections'}
                onChange={(e) => handleConfigChange('extractionMode', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              >
                <option value="Text & Structured Sections">Text & Structured Sections</option>
                <option value="Full Text Only">Full Raw Text Only</option>
                <option value="Tables & Metrics">Tables & Key Metrics</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Max Pages to Scan</label>
              <input
                type="number"
                min={1}
                max={20}
                value={config.maxPages || 5}
                onChange={(e) => handleConfigChange('maxPages', parseInt(e.target.value))}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Condition Settings */}
        {componentType === 'Condition' && (
          <>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Field to Check</label>
              <input
                type="text"
                value={config.fieldToCheck || 'fit_score'}
                onChange={(e) => handleConfigChange('fieldToCheck', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              />
              <p className="text-[10px] text-[#8D8D8D]">Field produced by previous component.</p>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Rule</label>
              <select
                value={config.rule || 'Greater Than or Equal To'}
                onChange={(e) => handleConfigChange('rule', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              >
                <option value="Greater Than or Equal To">Greater Than or Equal To (&gt;=)</option>
                <option value="Equals">Equals (==)</option>
                <option value="Contains Text">Contains Text</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Expected Value</label>
              <input
                type="text"
                value={config.targetValue || '7'}
                onChange={(e) => handleConfigChange('targetValue', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Human Approval Settings */}
        {componentType === 'Human Approval' && (
          <>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Reviewer Question</label>
              <textarea
                rows={3}
                value={config.approvalPrompt || 'Please review candidate score before invite is dispatched.'}
                onChange={(e) => handleConfigChange('approvalPrompt', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl p-3 resize-none"
              />
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Review Timeout (Hours)</label>
              <input
                type="number"
                value={config.timeoutHours || 24}
                onChange={(e) => handleConfigChange('timeoutHours', parseInt(e.target.value))}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Output Settings */}
        {componentType === 'Output' && (
          <>
            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Result Presentation Format</label>
              <select
                value={config.format || 'Formatted Summary & Scorecard'}
                onChange={(e) => handleConfigChange('format', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              >
                <option value="Formatted Summary & Scorecard">Formatted Summary & Scorecard</option>
                <option value="Markdown Report">Markdown Report</option>
                <option value="Clean JSON Object">Clean JSON Object</option>
                <option value="PDF Document File">PDF Document File</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-[#111111]">Result Destination</label>
              <input
                type="text"
                value={config.destination || 'Display in Dashboard & Email Candidate Brief'}
                onChange={(e) => handleConfigChange('destination', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Input Settings */}
        {componentType === 'Input' && (
          <div className="space-y-1">
            <label className="font-semibold text-[#111111]">Input Type</label>
            <select
              value={config.inputType || 'File Upload (PDF / Doc)'}
              onChange={(e) => handleConfigChange('inputType', e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
            >
              <option value="File Upload (PDF / Doc)">File Upload (PDF / Doc)</option>
              <option value="Text Prompt">Text Prompt</option>
              <option value="JSON Webhook Payload">JSON Webhook Payload</option>
            </select>
          </div>
        )}

        {/* Tool Settings */}
        {componentType === 'Tool' && (
          <div className="space-y-1">
            <label className="font-semibold text-[#111111]">Operation Type</label>
            <select
              value={config.operation || 'Candidate Database Sync'}
              onChange={(e) => handleConfigChange('operation', e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl px-3 py-2"
            >
              <option value="Candidate Database Sync">Candidate Database Sync</option>
              <option value="Web Search">Web Search</option>
              <option value="Send Email Dispatch">Send Email Dispatch</option>
              <option value="Python Script Runner">Python Script Runner</option>
            </select>
          </div>
        )}
      </div>

      {/* Action Buttons in Footer */}
      <div className="p-4 border-t border-[#E6E5E2] bg-[#FFFFFF] space-y-2">
        <button
          onClick={handleSave}
          className="w-full py-2.5 rounded-full bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs font-semibold shadow-sm transition-all flex items-center justify-center gap-2"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Settings</span>
        </button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => duplicateNode(selectedNode.id)}
            className="py-2 rounded-xl bg-[#F1F0EE] hover:bg-[#E3E2DF] text-[#111111] text-xs font-medium border border-[#E6E5E2] transition-colors flex items-center justify-center gap-1.5"
          >
            <Copy className="w-3.5 h-3.5 text-[#8D8D8D]" />
            <span>Duplicate</span>
          </button>

          <button
            onClick={() => deleteNode(selectedNode.id)}
            className="py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-medium border border-rose-200 transition-colors flex items-center justify-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-600" />
            <span>Delete</span>
          </button>
        </div>
      </div>
    </div>
  );
};
