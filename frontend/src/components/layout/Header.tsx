import React, { useState } from 'react';
import {
  Menu,
  Bell,
  Play,
  ShieldCheck,
  CheckCircle2,
  Wrench,
  X,
  ChevronDown,
  Info,
  Server,
  Sparkles,
  HelpCircle,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ElevatedButton } from '../common/ElevatedButton';

export const Header: React.FC = () => {
  const {
    currentPage,
    setCurrentPage,
    activeAgentName,
    setSidebarOpen,
    runAgentExecution,
    isExecuting,
    runValidation,
    isValidating,
    backendStatus,
    checkBackendHealth,
    setIsHelpOpen,
  } = useWorkflow();

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [demoInfoOpen, setDemoInfoOpen] = useState(false);

  const getPageInfo = () => {
    switch (currentPage) {
      case 'dashboard':
        return {
          title: 'Home',
          subtitle: 'Create intelligent AI assistants without writing code.',
          breadcrumb: 'Overview',
        };
      case 'my-agents':
        return {
          title: 'My AI Agents',
          subtitle: 'Inspect, customize, and launch your assistants.',
          breadcrumb: 'My Agents',
        };
      case 'create-agent':
        return {
          title: 'Create Your Agent',
          subtitle: 'Describe what you want your assistant to do in plain words.',
          breadcrumb: 'Guided Creation',
        };
      case 'editor':
        return {
          title: activeAgentName || 'Build Your Agent',
          subtitle: 'Connect building blocks to show how your agent works.',
          breadcrumb: 'Build Your Agent',
        };
      case 'validation':
        return {
          title: 'Check My Agent',
          subtitle: "Let's make sure everything is ready before your assistant starts.",
          breadcrumb: 'Check My Agent',
        };
      case 'activity':
        return {
          title: 'Watch Your Agent Work',
          subtitle: 'Live execution timeline, problem detection, and auto-repair.',
          breadcrumb: 'Watch Your Agent Work',
        };
      case 'history':
        return {
          title: 'Execution History',
          subtitle: 'Audit past runs, durations, and auto-repair results.',
          breadcrumb: 'History',
        };
      case 'templates':
        return {
          title: 'Ready-Made Agents',
          subtitle: 'Pick a pre-built recipe to start in seconds.',
          breadcrumb: 'Templates',
        };
      case 'settings':
        return {
          title: 'Settings',
          subtitle: 'Configure AI intelligence engine, limits, and repair policies.',
          breadcrumb: 'Settings',
        };
      default:
        return {
          title: 'AgentForge AI',
          subtitle: 'Build your own AI agents without writing code.',
          breadcrumb: 'Platform',
        };
    }
  };

  const { title, subtitle, breadcrumb } = getPageInfo();

  return (
    <header className="h-16 px-4 sm:px-6 liquid-glass sticky top-0 z-30 flex items-center justify-between border-b border-[#EAE8E5]/80 transition-all select-none">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-2xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] lg:hidden transition-colors"
          aria-label="Open Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-1.5 text-[11px] text-[#777777] font-medium">
            <span>AgentForge AI</span>
            <span className="text-[#D8D5D0]">/</span>
            <span className="text-[#B15F2C] font-semibold">{breadcrumb}</span>
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm sm:text-base font-bold text-[#111111] tracking-tight truncate max-w-[200px] sm:max-w-md">
              {title}
            </h1>
            <span className="hidden xl:inline text-xs text-[#777777]">
              — {subtitle}
            </span>
          </div>
        </div>
      </div>

      {/* Right: Runtime Status, Quick Help & Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Runtime Status Pill */}
        <div className="relative">
          <button
            onClick={() => setDemoInfoOpen(!demoInfoOpen)}
            className={`hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[11px] font-semibold border transition-all ${
              backendStatus === 'connected'
                ? 'bg-emerald-50/80 text-emerald-800 border-emerald-200 shadow-subtle'
                : 'bg-[#FAF5F1] text-[#B15F2C] border-[#CF8047]/30 shadow-subtle'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendStatus === 'connected' ? 'bg-emerald-600 animate-pulse' : 'bg-[#B15F2C]'
              }`}
            />
            <span>{backendStatus === 'connected' ? 'Live Backend Connected' : 'Simulated Runtime Mode'}</span>
            <Info className="w-3 h-3 text-[#777777]" />
          </button>

          {/* Status Popover */}
          {demoInfoOpen && (
            <div className="absolute right-0 mt-2 w-80 p-4 rounded-3xl bg-white border border-[#EAE8E5] shadow-elevated z-50 text-xs text-[#111111] space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE8E5]">
                <span className="font-bold">System Runtime Status</span>
                <button
                  onClick={() => setDemoInfoOpen(false)}
                  className="p-1 rounded-lg text-[#777777] hover:bg-[#F7F6F4]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-[#777777] leading-relaxed">
                AgentForge AI provides an autonomous visual workflow builder and execution engine.
              </p>
              <div className="p-2.5 rounded-2xl bg-[#F7F6F4] space-y-1 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-[#777777]">Backend API:</span>
                  <span className={backendStatus === 'connected' ? 'text-emerald-700 font-bold' : 'text-[#B15F2C] font-bold'}>
                    {backendStatus === 'connected' ? 'ONLINE (Port 8000)' : 'STANDALONE (Port 5173)'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#777777]">AI Reasoning:</span>
                  <span className="text-emerald-700 font-bold">Google Gemini API</span>
                </div>
              </div>
              <button
                onClick={() => checkBackendHealth()}
                className="w-full py-2 rounded-xl bg-[#FAF5F1] hover:bg-[#CF8047]/20 text-[#B15F2C] text-xs font-semibold border border-[#CF8047]/30 transition-colors flex items-center justify-center gap-1.5"
              >
                <Server className="w-3.5 h-3.5" />
                <span>Re-check Backend Connection</span>
              </button>
            </div>
          )}
        </div>

        {/* User Guide Pill */}
        <button
          onClick={() => setIsHelpOpen(true)}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F7F6F4] hover:bg-[#EAE8E5] text-[#111111] text-xs font-semibold border border-[#EAE8E5] transition-colors"
          title="Open User Guide"
        >
          <HelpCircle className="w-3.5 h-3.5 text-[#B15F2C]" />
          <span>Guide</span>
        </button>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 rounded-2xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] relative transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#B15F2C]" />
          </button>

          {/* Notifications Dropdown */}
          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-72 p-3 rounded-3xl bg-white border border-[#EAE8E5] shadow-elevated z-50 text-xs text-[#111111] space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE8E5]">
                <span className="font-bold">Recent Updates</span>
                <button
                  onClick={() => setNotificationsOpen(false)}
                  className="p-1 rounded-lg text-[#777777] hover:bg-[#F7F6F4]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="space-y-2">
                <div className="p-2.5 rounded-2xl bg-emerald-50/70 border border-emerald-200">
                  <p className="font-semibold text-emerald-900">Agent Verified</p>
                  <p className="text-[11px] text-emerald-700">Resume Screener passed all 4 test cases.</p>
                </div>
                <div className="p-2.5 rounded-2xl bg-[#FAF5F1] border border-[#CF8047]/30">
                  <p className="font-semibold text-[#B15F2C]">Autonomous Repair Ready</p>
                  <p className="text-[11px] text-[#777777]">Self-repair engine standby (max 2 attempts).</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar & Menu */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 p-1 pl-1.5 pr-2 rounded-full hover:bg-[#F7F6F4] transition-colors border border-transparent hover:border-[#EAE8E5]"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#0A0A0A] to-[#2B2B2B] text-white font-bold text-xs flex items-center justify-center shadow-subtle">
              AU
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#777777]" />
          </button>

          {/* Profile Dropdown */}
          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 p-2 rounded-3xl bg-white border border-[#EAE8E5] shadow-elevated z-50 text-xs text-[#111111] space-y-1 animate-in fade-in">
              <div className="p-3 border-b border-[#EAE8E5]">
                <p className="font-bold text-xs text-[#111111]">AgentForge User</p>
                <p className="text-[11px] text-[#777777]">user@agentforge.ai</p>
              </div>
              <button
                onClick={() => {
                  setProfileOpen(false);
                  setCurrentPage('my-agents');
                }}
                className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#F7F6F4] text-xs transition-colors"
              >
                My AI Agents
              </button>
              <button
                onClick={() => {
                  setProfileOpen(false);
                  setCurrentPage('settings');
                }}
                className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#F7F6F4] text-xs transition-colors"
              >
                System Preferences
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
