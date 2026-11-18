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
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

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
  } = useWorkflow();

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [demoInfoOpen, setDemoInfoOpen] = useState(false);

  const getPageInfo = () => {
    switch (currentPage) {
      case 'dashboard':
        return { title: 'Dashboard', breadcrumb: 'Overview' };
      case 'my-agents':
        return { title: 'My Agents', breadcrumb: 'Workspace' };
      case 'create-agent':
        return { title: 'Create Agent', breadcrumb: 'Natural Language Builder' };
      case 'editor':
        return { title: activeAgentName, breadcrumb: 'Workflow Studio' };
      case 'validation':
        return { title: 'Check Your Agent', breadcrumb: 'Verification & Tests' };
      case 'activity':
        return { title: 'Agent Activity', breadcrumb: 'Live Monitor & Self-Repair' };
      case 'history':
        return { title: 'Execution History', breadcrumb: 'Activity Log' };
      case 'templates':
        return { title: 'Agent Templates', breadcrumb: 'Quick Start' };
      case 'settings':
        return { title: 'Settings', breadcrumb: 'System Preferences' };
      default:
        return { title: 'AgentForge AI', breadcrumb: 'Platform' };
    }
  };

  const { title, breadcrumb } = getPageInfo();

  return (
    <header className="h-16 px-4 sm:px-6 liquid-glass sticky top-0 z-30 flex items-center justify-between border-b border-[#EAE8E5]/80 transition-all">
      {/* Left: Mobile Toggle & Clean Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] lg:hidden transition-colors"
          aria-label="Open Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2 text-[11px] text-[#777777] font-medium">
            <span>AgentForge AI</span>
            <span className="text-[#D8D5D0]">/</span>
            <span className="text-[#B15F2C] font-semibold">{breadcrumb}</span>
          </div>
          <h1 className="text-sm sm:text-base font-bold text-[#111111] tracking-tight truncate max-w-[200px] sm:max-w-md">
            {title}
          </h1>
        </div>
      </div>

      {/* Right: Runtime Status, Quick Actions & Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Runtime Status Pill (Apple Glass Lozenge) */}
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
                backendStatus === 'connected' ? 'bg-emerald-600' : 'bg-[#B15F2C]'
              } animate-pulse`}
            />
            <span>
              {backendStatus === 'connected'
                ? 'Live Backend Online'
                : 'Demo Mode (Simulated)'}
            </span>
            <Info className="w-3 h-3 opacity-60" />
          </button>

          {demoInfoOpen && (
            <div className="absolute right-0 mt-2 w-72 liquid-glass-elevated rounded-3xl p-4 z-50 text-xs animate-in fade-in space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE8E5]">
                <span className="font-bold text-[#111111] flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-[#B15F2C]" />
                  <span>Runtime Environment</span>
                </span>
                <button
                  onClick={() => setDemoInfoOpen(false)}
                  className="text-[#777777] hover:text-[#111111]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <p className="text-[#777777] leading-relaxed">
                {backendStatus === 'connected'
                  ? 'Connected to local FastAPI backend on port 8000 with active SQLite database.'
                  : 'Operating in Interactive Demo Mode with complete local state, visual workflow simulation, and autonomous self-repair.'}
              </p>

              <div className="pt-2 border-t border-[#EAE8E5] flex items-center justify-between">
                <button
                  onClick={() => checkBackendHealth()}
                  className="text-[11px] font-semibold text-[#B15F2C] hover:underline"
                >
                  Ping Backend Again ↺
                </button>
                <span className="text-[10px] text-[#777777] font-mono">v1.0.0</span>
              </div>
            </div>
          )}
        </div>

        {/* Quick Studio Action if not in Studio */}
        {currentPage !== 'editor' && (
          <button
            onClick={() => setCurrentPage('editor')}
            className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold shadow-subtle transition-all active:scale-[0.98]"
          >
            <Play className="w-3 h-3 fill-white" />
            <span>Workflow Studio</span>
          </button>
        )}

        {/* Notifications Icon & Liquid Dropdown */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2.5 rounded-2xl text-[#777777] hover:text-[#111111] hover:bg-white/80 border border-transparent hover:border-[#EAE8E5] transition-all"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#B15F2C]" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 liquid-glass-elevated rounded-3xl p-4 z-50 text-xs animate-in fade-in space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE8E5]">
                <span className="font-bold text-sm text-[#111111]">Notifications</span>
                <button
                  onClick={() => setNotificationsOpen(false)}
                  className="text-[#777777] hover:text-[#111111]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="divide-y divide-[#EAE8E5]/70 max-h-72 overflow-y-auto space-y-1">
                <div className="py-2.5">
                  <div className="flex items-center gap-1.5 text-emerald-800 font-semibold mb-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Requirement Coverage Verified</span>
                  </div>
                  <p className="text-[11px] text-[#777777] leading-relaxed">
                    All candidate screening requirements are mapped to workflow components.
                  </p>
                  <span className="text-[10px] text-[#777777] mt-1 block">5 minutes ago</span>
                </div>

                <div className="py-2.5">
                  <div className="flex items-center gap-1.5 text-[#B15F2C] font-semibold mb-0.5">
                    <Wrench className="w-3.5 h-3.5 text-[#B15F2C]" />
                    <span>Auto-Repair Available</span>
                  </div>
                  <p className="text-[11px] text-[#777777] leading-relaxed">
                    AgentForge AI detected missing instructions and prepared a 1-click fix.
                  </p>
                  <span className="text-[10px] text-[#777777] mt-1 block">15 minutes ago</span>
                </div>
              </div>

              <div className="pt-2 text-center border-t border-[#EAE8E5]">
                <button
                  onClick={() => {
                    setCurrentPage('activity');
                    setNotificationsOpen(false);
                  }}
                  className="text-[11px] text-[#B15F2C] font-semibold hover:underline"
                >
                  View Activity & Self-Repair →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar & Mini Menu */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-1.5 p-1 rounded-2xl hover:bg-white/80 border border-transparent hover:border-[#EAE8E5] transition-all"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#0A0A0A] to-[#2B2B2B] text-white font-bold text-xs flex items-center justify-center shadow-subtle">
              AU
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#777777] hidden sm:block" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 liquid-glass-elevated rounded-3xl p-2.5 z-50 text-xs shadow-glass-hover">
              <div className="px-3 py-2 border-b border-[#EAE8E5] mb-1">
                <p className="font-bold text-[#111111]">AgentForge User</p>
                <p className="text-[10px] text-[#777777]">user@agentforge.ai</p>
              </div>
              <button
                onClick={() => {
                  setCurrentPage('settings');
                  setProfileOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-xl text-[#111111] hover:bg-[#F7F6F4] transition-colors"
              >
                Settings & Preferences
              </button>
              <button
                onClick={() => {
                  setCurrentPage('my-agents');
                  setProfileOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-xl text-[#111111] hover:bg-[#F7F6F4] transition-colors"
              >
                My Saved Agents
              </button>
              <div className="border-t border-[#EAE8E5] mt-1 pt-1">
                <button
                  onClick={() => setProfileOpen(false)}
                  className="w-full text-left px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 transition-colors font-medium"
                >
                  Log out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
