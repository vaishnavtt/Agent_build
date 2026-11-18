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
  Info,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { WorkflowNodeData, ComponentType } from '../../types';
import { LiquidButton } from '../common/LiquidButton';

const getDisplayTitle = (type: ComponentType): string => {
  switch (type) {
    case 'Input':
      return 'Input Settings';
    case 'Document Reader':
      return 'PDF Reader Settings';
    case 'LLM':
      return 'AI Assistant Settings';
    case 'Condition':
      return 'Decision Settings';
    case 'Human Approval':
      return 'Human Approval Settings';
    case 'Tool':
      return 'Tool Settings';
    case 'Output':
      return 'Output Settings';
    default:
      return `${type} Settings`;
  }
};

export const ComponentSettings: React.FC = () => {
  const { selectedNode, setSelectedNode, updateNodeConfig, deleteNode, duplicateNode, showToast } = useWorkflow();

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
      <div className="w-80 bg-[#FFFFFF] border-l border-[#EAE8E5] flex flex-col items-center justify-center p-6 text-center select-none">
        <div className="w-12 h-12 rounded-2xl bg-[#F7F6F4] text-[#777777] border border-[#EAE8E5] flex items-center justify-center mb-3 shadow-subtle">
          <Settings2 className="w-6 h-6" />
        </div>
        <h4 className="font-bold text-sm text-[#111111]">No Component Selected</h4>
        <p className="text-xs text-[#777777] mt-1.5 max-w-[210px] leading-relaxed">
          Click any component on the visual canvas to inspect or adjust what it does.
        </p>
      </div>
    );
  }

  const nodeData = selectedNode.data as unknown as WorkflowNodeData;
  const { componentType } = nodeData;

  const handleSave = () => {
    updateNodeConfig(selectedNode.id, label, config);
    showToast('Settings Saved', `${label || componentType} settings updated`, 'success');
  };

  const handleConfigChange = (field: string, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-80 bg-[#FFFFFF] border-l border-[#EAE8E5] flex flex-col h-full overflow-hidden select-none">
      {/* Panel Header */}
      <div className="p-4 border-b border-[#EAE8E5] flex items-center justify-between bg-[#FAF5F1]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-[#B15F2C] text-white flex items-center justify-center shadow-subtle">
            <Settings2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-xs text-[#111111]">{getDisplayTitle(componentType)}</h3>
            <span className="text-[10px] text-[#B15F2C] font-semibold">Active Component</span>
          </div>
        </div>

        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 rounded-lg text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Form Fields */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Component Display Label */}
        <div className="space-y-1.5">
          <label className="font-semibold text-[#111111]">Display Name</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] transition-all"
          />
          <p className="text-[10px] text-[#777777]">Name visible on the visual workspace.</p>
        </div>

        {/* AI Assistant Specific Settings */}
        {componentType === 'LLM' && (
          <>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">AI Intelligence Level</label>
              <select
                value={config.model || 'Gemini 1.5 Pro (Recommended)'}
                onChange={(e) => handleConfigChange('model', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
              >
                <option value="Gemini 1.5 Pro (Recommended)">Gemini 1.5 Pro (Smartest - deep reasoning)</option>
                <option value="Gemini 1.5 Flash (Fast)">Gemini 1.5 Flash (Fast & lightweight)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-[#111111]">What should this assistant do?</label>
                <span className="text-[10px] text-[#B15F2C] font-semibold">Important</span>
              </div>
              <textarea
                rows={4}
                value={config.instructions || ''}
                onChange={(e) => handleConfigChange('instructions', e.target.value)}
                placeholder="Give clear, plain English instructions... e.g. Analyze candidate skills in React, TypeScript, Python and score alignment from 1 to 10."
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl p-3 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF] resize-none leading-relaxed transition-all"
              />
              <p className="text-[10px] text-[#777777]">
                Explain in ordinary words what this assistant should look for and decide.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Creativity Level</label>
              <select
                value={config.creativity || 'Balanced (0.4)'}
                onChange={(e) => handleConfigChange('creativity', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2 focus:outline-none focus:border-[#B15F2C]"
              >
                <option value="Precise & Factual (0.0)">Precise & Factual (strict analysis)</option>
                <option value="Balanced (0.4)">Balanced (Recommended)</option>
                <option value="Creative (0.8)">Creative (for writing & drafting)</option>
              </select>
            </div>
          </>
        )}

        {/* PDF Reader Settings */}
        {componentType === 'Document Reader' && (
          <>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Where does the document come from?</label>
              <select
                value={config.sourceInput || 'From User Input'}
                onChange={(e) => handleConfigChange('sourceInput', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="From User Input">Uploaded by user in the first step</option>
                <option value="Fixed Sample File">Fixed sample resume (demo test)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">What information should we read?</label>
              <select
                value={config.extractionMode || 'Text & Structured Sections'}
                onChange={(e) => handleConfigChange('extractionMode', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="Text & Structured Sections">All text and section headings</option>
                <option value="Full Text Only">Raw text only</option>
                <option value="Tables & Metrics">Tables & Key Metrics</option>
              </select>
            </div>
          </>
        )}

        {/* Decision (Condition) Settings */}
        {componentType === 'Condition' && (
          <>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">What should we check?</label>
              <input
                type="text"
                value={config.fieldToCheck || 'fit_score'}
                onChange={(e) => handleConfigChange('fieldToCheck', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
              <p className="text-[10px] text-[#777777]">The information produced by the previous step (e.g. score).</p>
            </div>

            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Rule to follow</label>
              <select
                value={config.rule || 'Greater Than or Equal To'}
                onChange={(e) => handleConfigChange('rule', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              >
                <option value="Greater Than or Equal To">Greater Than or Equal To (≥)</option>
                <option value="Equals">Exactly Equals (=)</option>
                <option value="Contains Text">Contains specific text</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Target Value</label>
              <input
                type="text"
                value={config.targetValue || '7'}
                onChange={(e) => handleConfigChange('targetValue', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Human Approval Settings */}
        {componentType === 'Human Approval' && (
          <>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Question for the reviewer</label>
              <textarea
                rows={3}
                value={config.approvalPrompt || 'Please review candidate score before the invite is dispatched.'}
                onChange={(e) => handleConfigChange('approvalPrompt', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl p-3 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">Wait time before warning (Hours)</label>
              <input
                type="number"
                value={config.timeoutHours || 24}
                onChange={(e) => handleConfigChange('timeoutHours', parseInt(e.target.value))}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Output Settings */}
        {componentType === 'Output' && (
          <>
            <div className="space-y-1.5">
              <label className="font-semibold text-[#111111]">How should results look?</label>
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
              <label className="font-semibold text-[#111111]">Where should results go?</label>
              <input
                type="text"
                value={config.destination || 'Display in Dashboard & Email Candidate Brief'}
                onChange={(e) => handleConfigChange('destination', e.target.value)}
                className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
              />
            </div>
          </>
        )}

        {/* Input Settings */}
        {componentType === 'Input' && (
          <div className="space-y-1.5">
            <label className="font-semibold text-[#111111]">Input Type</label>
            <select
              value={config.inputType || 'File Upload (PDF / Doc)'}
              onChange={(e) => handleConfigChange('inputType', e.target.value)}
              className="w-full text-xs text-[#111111] bg-[#F7F6F4] border border-[#EAE8E5] rounded-xl px-3 py-2"
            >
              <option value="File Upload (PDF / Doc)">Document or Resume Upload</option>
              <option value="Text Prompt">Typed text or message</option>
              <option value="JSON Webhook Payload">Incoming web data</option>
            </select>
          </div>
        )}

        {/* Tool Settings */}
        {componentType === 'Tool' && (
          <div className="space-y-1.5">
            <label className="font-semibold text-[#111111]">What tool should run?</label>
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

        {/* Collapsible Advanced Settings Accordion for Non-Technical Users */}
        <div className="pt-2 border-t border-[#EAE8E5]">
          <button
            type="button"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="w-full flex items-center justify-between text-xs font-semibold text-[#777777] hover:text-[#111111] py-1"
          >
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#B15F2C]" />
              <span>Advanced Settings</span>
            </span>
            {isAdvancedOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {isAdvancedOpen && (
            <div className="mt-3 space-y-3 p-3 rounded-2xl bg-[#F7F6F4] border border-[#EAE8E5]">
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-[#777777]">Component ID</label>
                <div className="font-mono text-[10px] text-[#111111] p-1.5 rounded-lg bg-[#FFFFFF] border border-[#EAE8E5]">
                  {selectedNode.id}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-[#777777]">Execution Timeout (seconds)</label>
                <input
                  type="number"
                  value={config.timeoutSeconds || 30}
                  onChange={(e) => handleConfigChange('timeoutSeconds', parseInt(e.target.value))}
                  className="w-full text-xs text-[#111111] bg-[#FFFFFF] border border-[#EAE8E5] rounded-lg px-2.5 py-1.5"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-[#777777]">Retry on Error</label>
                <select
                  value={config.retryPolicy || 'Auto-retry up to 2 times'}
                  onChange={(e) => handleConfigChange('retryPolicy', e.target.value)}
                  className="w-full text-xs text-[#111111] bg-[#FFFFFF] border border-[#EAE8E5] rounded-lg px-2 py-1.5"
                >
                  <option value="Auto-retry up to 2 times">Auto-retry up to 2 times</option>
                  <option value="Do not retry">Do not retry</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons in Footer */}
      <div className="p-4 border-t border-[#EAE8E5] bg-[#FFFFFF] space-y-2">
        <LiquidButton
          variant="primary"
          size="md"
          onClick={handleSave}
          className="w-full"
          icon={<Save className="w-3.5 h-3.5" />}
        >
          Save Settings
        </LiquidButton>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => duplicateNode(selectedNode.id)}
            className="py-2 rounded-xl bg-[#F7F6F4] hover:bg-[#EAE8E5] text-[#111111] text-xs font-medium border border-[#EAE8E5] transition-colors flex items-center justify-center gap-1.5 shadow-subtle"
          >
            <Copy className="w-3.5 h-3.5 text-[#777777]" />
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
