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
        return { title: 'Build Your Agent', breadcrumb: 'Natural Language Creator' };
      case 'editor':
        return { title: activeAgentName, breadcrumb: 'Workflow Studio' };
      case 'validation':
        return { title: 'Check Your Agent', breadcrumb: 'Integrity & Tests' };
      case 'activity':
        return { title: 'Agent Activity', breadcrumb: 'Live Monitor & Auto-Repair' };
      case 'history':
        return { title: 'Execution History', breadcrumb: 'Audit & Records' };
      case 'templates':
        return { title: 'Agent Templates', breadcrumb: 'Pre-built Recipes' };
      case 'settings':
        return { title: 'Settings', breadcrumb: 'Preferences' };
      default:
        return { title: 'AgentForge AI', breadcrumb: 'Platform' };
    }
  };

  const { title, breadcrumb } = getPageInfo();

  return (
    <header className="h-16 px-4 sm:px-6 bg-[#FFFFFF] border-b border-[#E6E5E2] sticky top-0 z-30 flex items-center justify-between">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-xl text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE] lg:hidden"
          aria-label="Open Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2 text-[11px] text-[#8D8D8D] font-medium">
            <span>AgentForge AI</span>
            <span>/</span>
            <span className="text-[#B15F2C] font-semibold">{breadcrumb}</span>
          </div>
          <h1 className="text-sm sm:text-base font-bold text-[#111111] tracking-tight truncate max-w-[200px] sm:max-w-md">
            {title}
          </h1>
        </div>
      </div>

      {/* Right: Engine Status, Action Buttons & Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Transparent Demo Mode / Backend Status Badge */}
        <div className="relative">
          <button
            onClick={() => setDemoInfoOpen(!demoInfoOpen)}
            className={`hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold border transition-all ${
              backendStatus === 'connected'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-[#FAF5F1] text-[#B15F2C] border-[#CF8047]/30'
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
                : 'Demo Simulation Mode'}
            </span>
            <Info className="w-3 h-3 opacity-70" />
          </button>

          {demoInfoOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-[#FFFFFF] rounded-2xl shadow-elevated border border-[#E6E5E2] p-4 z-50 text-xs animate-in fade-in space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-[#E6E5E2]">
                <span className="font-bold text-[#111111] flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-[#B15F2C]" />
                  <span>Execution Runtime Mode</span>
                </span>
                <button
                  onClick={() => setDemoInfoOpen(false)}
                  className="text-[#8D8D8D] hover:text-[#111111]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <p className="text-[#8D8D8D] leading-relaxed">
                {backendStatus === 'connected'
                  ? 'Connected to local FastAPI backend on port 8000 with active SQLite database.'
                  : 'Currently operating in Interactive Demo Mode with complete local state, graph manipulation, validation, and auto-repair simulation.'}
              </p>

              <div className="pt-2 border-t border-[#E6E5E2] flex items-center justify-between">
                <button
                  onClick={() => checkBackendHealth()}
                  className="text-[11px] font-semibold text-[#B15F2C] hover:underline"
                >
                  Ping Backend Again ↺
                </button>
                <span className="text-[10px] text-[#8D8D8D] font-mono">v1.0.0</span>
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Studio Actions */}
        {currentPage === 'editor' && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => runValidation()}
              disabled={isValidating}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F1F0EE] hover:bg-[#E3E2DF] text-[#111111] text-xs font-medium border border-[#E6E5E2] transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-[#B15F2C]" />
              <span>{isValidating ? 'Checking...' : 'Check Agent'}</span>
            </button>

            <button
              onClick={() => runAgentExecution()}
              disabled={isExecuting}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs font-semibold shadow-sm transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>{isExecuting ? 'Running...' : 'Run Agent'}</span>
            </button>
          </div>
        )}

        {currentPage !== 'editor' && (
          <button
            onClick={() => setCurrentPage('editor')}
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold transition-all"
          >
            <Play className="w-3 h-3 fill-white" />
            <span>Open Studio</span>
          </button>
        )}

        {/* Notifications Icon & Dropdown */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 rounded-xl text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE] transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#B15F2C]" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-[#FFFFFF] rounded-2xl shadow-elevated border border-[#E6E5E2] p-4 z-50 text-xs animate-in fade-in">
              <div className="flex items-center justify-between pb-3 border-b border-[#E6E5E2]">
                <span className="font-semibold text-sm text-[#111111]">Notifications</span>
                <button
                  onClick={() => setNotificationsOpen(false)}
                  className="text-[#8D8D8D] hover:text-[#111111]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="divide-y divide-[#E6E5E2] mt-1 max-h-72 overflow-y-auto">
                <div className="py-2.5">
                  <div className="flex items-center gap-1.5 text-emerald-700 font-semibold mb-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Requirement Coverage Verified</span>
                  </div>
                  <p className="text-[11px] text-[#8D8D8D]">
                    All candidate screening requirements are mapped to workflow nodes.
                  </p>
                  <span className="text-[10px] text-[#8D8D8D] mt-1 block">5 minutes ago</span>
                </div>

                <div className="py-2.5">
                  <div className="flex items-center gap-1.5 text-[#B15F2C] font-semibold mb-0.5">
                    <Wrench className="w-3.5 h-3.5 text-[#B15F2C]" />
                    <span>Auto-Repair Recipe Ready</span>
                  </div>
                  <p className="text-[11px] text-[#8D8D8D]">
                    AgentForge AI detected missing instructions and synthesized a 1-click fix.
                  </p>
                  <span className="text-[10px] text-[#8D8D8D] mt-1 block">15 minutes ago</span>
                </div>
              </div>

              <div className="pt-2 text-center border-t border-[#E6E5E2]">
                <button
                  onClick={() => {
                    setCurrentPage('activity');
                    setNotificationsOpen(false);
                  }}
                  className="text-[11px] text-[#B15F2C] font-semibold hover:underline"
                >
                  View Activity & Repair Console →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Profile Avatar & Mini Menu */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-1.5 p-1 rounded-xl hover:bg-[#F1F0EE] transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-[#0A0A0A] text-white font-bold text-xs flex items-center justify-center">
              AU
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#8D8D8D] hidden sm:block" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-[#FFFFFF] rounded-2xl shadow-elevated border border-[#E6E5E2] p-2 z-50 text-xs">
              <div className="px-3 py-2 border-b border-[#E6E5E2] mb-1">
                <p className="font-semibold text-[#111111]">AgentForge User</p>
                <p className="text-[10px] text-[#8D8D8D]">user@agentforge.ai</p>
              </div>
              <button
                onClick={() => {
                  setCurrentPage('settings');
                  setProfileOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-xl text-[#111111] hover:bg-[#F1F0EE] transition-colors"
              >
                Settings & Preferences
              </button>
              <button
                onClick={() => {
                  setCurrentPage('my-agents');
                  setProfileOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-xl text-[#111111] hover:bg-[#F1F0EE] transition-colors"
              >
                My Saved Agents
              </button>
              <div className="border-t border-[#E6E5E2] mt-1 pt-1">
                <button
                  onClick={() => setProfileOpen(false)}
                  className="w-full text-left px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 transition-colors"
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
