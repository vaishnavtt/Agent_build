import React from 'react';
import {
  LayoutDashboard,
  Layers,
  Sparkles,
  Activity,
  History,
  Boxes,
  Settings,
  HelpCircle,
  X,
  Bot,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { PageView } from '../../types';

export const Sidebar: React.FC = () => {
  const { currentPage, setCurrentPage, sidebarOpen, setSidebarOpen, setIsHelpOpen } = useWorkflow();

  const navItems: { id: PageView; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'my-agents', label: 'My Agents', icon: Layers, badge: '4' },
    { id: 'create-agent', label: 'Create Agent', icon: Sparkles },
    { id: 'templates', label: 'Templates', icon: Boxes, badge: 'New' },
    { id: 'activity', label: 'Agent Activity', icon: Activity },
    { id: 'history', label: 'Execution History', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleNavClick = (id: PageView) => {
    setCurrentPage(id);
    if (sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/15 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Apple Liquid Glass Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 liquid-glass flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0 shadow-elevated' : '-translate-x-full'
        }`}
      >
        {/* Top: Logo & Branding */}
        <div>
          <div className="h-16 px-5 flex items-center justify-between border-b border-[#EAE8E5]/80">
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => handleNavClick('dashboard')}
            >
              <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-[#0A0A0A] to-[#1F1F1F] flex items-center justify-center text-white shadow-subtle group-hover:scale-105 transition-transform">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-base tracking-tight text-[#111111]">AgentForge</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-[#FAF5F1] text-[#B15F2C] px-1.5 py-0.5 rounded-full border border-[#CF8047]/30">
                    AI
                  </span>
                </div>
                <p className="text-[11px] text-[#777777]">Autonomous Agent Studio</p>
              </div>
            </div>

            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 rounded-xl text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4] lg:hidden transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Create CTA in sidebar */}
          <div className="p-3">
            <button
              onClick={() => handleNavClick('create-agent')}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl bg-gradient-to-b from-[#B15F2C] to-[#984D20] hover:from-[#CF8047] hover:to-[#B15F2C] text-white text-xs font-semibold shadow-[0_4px_14px_-2px_rgba(177,95,44,0.35)] transition-all group active:scale-[0.98]"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-white/90" />
                Build My Agent
              </span>
              <ChevronRight className="w-4 h-4 text-white/70 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          {/* Navigation Items List */}
          <nav className="px-3 py-1 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-[#FAF5F1] text-[#B15F2C] font-semibold border border-[#CF8047]/30 shadow-subtle'
                      : 'text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4]/90'
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#B15F2C]' : 'text-[#777777]'}`} />
                    <span>{item.label}</span>
                  </span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                        isActive
                          ? 'bg-[#B15F2C] text-white'
                          : 'bg-[#F7F6F4] text-[#777777] border border-[#EAE8E5]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Help & User Profile */}
        <div className="p-3 border-t border-[#EAE8E5]/80 space-y-2 bg-transparent">
          <button
            onClick={() => setIsHelpOpen(true)}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs text-[#777777] hover:text-[#111111] hover:bg-[#F7F6F4]/90 transition-colors"
          >
            <span className="flex items-center gap-2.5">
              <HelpCircle className="w-4 h-4 text-[#777777]" />
              <span>Help & User Guide</span>
            </span>
            <ExternalLink className="w-3.5 h-3.5 text-[#777777]" />
          </button>

          {/* User Profile Card */}
          <div className="flex items-center gap-3 p-2.5 rounded-2xl bg-white/70 border border-[#EAE8E5] shadow-subtle">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#0A0A0A] to-[#2B2B2B] text-white font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-subtle">
              AU
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-[#111111] truncate">AgentForge User</p>
                <span className="text-[9px] bg-[#FAF5F1] text-[#B15F2C] border border-[#CF8047]/30 font-semibold px-1.5 py-0.2 rounded-full">
                  DEMO
                </span>
              </div>
              <p className="text-[10px] text-[#777777] truncate">user@agentforge.ai</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
