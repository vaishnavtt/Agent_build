import React from 'react';
import { Sparkles, Terminal, Activity, GitBranch } from 'lucide-react';

interface NavbarProps {
  backendOnline: boolean | null;
  onRefreshHealth: () => void;
  checkingHealth: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  backendOnline,
  onRefreshHealth,
  checkingHealth,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">AgentForge</span>
              <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                AI
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Visual Agent Builder</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={onRefreshHealth}
            disabled={checkingHealth}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-xs font-medium text-slate-300 transition-colors"
            title="Check backend health status"
          >
            <Activity
              className={`w-3.5 h-3.5 ${
                checkingHealth
                  ? 'animate-spin text-amber-400'
                  : backendOnline === true
                  ? 'text-emerald-400'
                  : backendOnline === false
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }`}
            />
            <span>
              Backend:{' '}
              {checkingHealth
                ? 'Pinging...'
                : backendOnline === true
                ? 'Online (v1)'
                : backendOnline === false
                ? 'Offline'
                : 'Unknown'}
            </span>
          </button>

          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-slate-900/40 px-3 py-1.5 rounded-lg border border-slate-800">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>Monorepo Foundation</span>
          </div>

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="p-2 text-slate-400 hover:text-white transition-colors"
            aria-label="Repository"
          >
            <GitBranch className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  );
};
