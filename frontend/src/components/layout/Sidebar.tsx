import React from 'react';
import {
  LayoutDashboard,
  Layers,
  Sparkles,
  Workflow,
  ShieldCheck,
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
    { id: 'editor', label: 'Workflow Studio', icon: Workflow },
    { id: 'validation', label: 'Check Your Agent', icon: ShieldCheck },
    { id: 'activity', label: 'Agent Activity', icon: Activity },
    { id: 'history', label: 'Execution History', icon: History },
    { id: 'templates', label: 'Templates', icon: Boxes, badge: 'New' },
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
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#FFFFFF] border-r border-[#E6E5E2] flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top: Logo & Branding */}
        <div>
          <div className="h-16 px-5 flex items-center justify-between border-b border-[#E6E5E2]">
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => handleNavClick('dashboard')}
            >
              <div className="w-9 h-9 rounded-xl bg-[#0A0A0A] flex items-center justify-center text-white shadow-sm group-hover:bg-[#B15F2C] transition-colors">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-base tracking-tight text-[#111111]">AgentForge</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-[#FAF5F1] text-[#B15F2C] px-1.5 py-0.5 rounded border border-[#CF8047]/20">
                    AI
                  </span>
                </div>
                <p className="text-[11px] text-[#8D8D8D]">Autonomous Agent Studio</p>
              </div>
            </div>

            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1 rounded-lg text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE] lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Create CTA in sidebar */}
          <div className="p-3">
            <button
              onClick={() => handleNavClick('create-agent')}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl bg-[#B15F2C] hover:bg-[#CF8047] text-white text-xs font-semibold shadow-sm transition-all group"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-white/90" />
                Build New Agent
              </span>
              <ChevronRight className="w-4 h-4 text-white/70 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          {/* Nav Items List */}
          <nav className="px-3 py-1 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-[#FAF5F1] text-[#B15F2C] font-semibold border border-[#CF8047]/20'
                      : 'text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE]'
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#B15F2C]' : 'text-[#8D8D8D]'}`} />
                    <span>{item.label}</span>
                  </span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                        isActive
                          ? 'bg-[#B15F2C] text-white'
                          : 'bg-[#F1F0EE] text-[#8D8D8D]'
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
        <div className="p-3 border-t border-[#E6E5E2] space-y-2 bg-[#FFFFFF]">
          <button
            onClick={() => setIsHelpOpen(true)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs text-[#8D8D8D] hover:text-[#111111] hover:bg-[#F1F0EE] transition-colors"
          >
            <span className="flex items-center gap-2.5">
              <HelpCircle className="w-4 h-4 text-[#8D8D8D]" />
              <span>Help & User Guide</span>
            </span>
            <ExternalLink className="w-3.5 h-3.5 text-[#8D8D8D]" />
          </button>

          {/* User Profile Card */}
          <div className="flex items-center gap-3 p-2.5 rounded-xl bg-[#F1F0EE]/80 border border-[#E6E5E2]">
            <div className="w-8 h-8 rounded-full bg-[#0A0A0A] text-white font-semibold text-xs flex items-center justify-center flex-shrink-0">
              V
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-[#111111] truncate">Vaishnav T</p>
                <span className="text-[9px] bg-emerald-100 text-emerald-800 font-medium px-1 rounded">PRO</span>
              </div>
              <p className="text-[10px] text-[#8D8D8D] truncate">vaishnaaa90@gmail.com</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

