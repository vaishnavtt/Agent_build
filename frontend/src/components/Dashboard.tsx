import React from 'react';
import {
  FileInput,
  Bot,
  FileText,
  Wrench,
  GitFork,
  UserCheck,
  FileOutput,
  Users,
  CheckCircle2,
  Workflow,
  ShieldCheck,
  Zap,
  ArrowRight,
} from 'lucide-react';
import { WorkflowCanvasPreview } from './WorkflowCanvasPreview';

export const Dashboard: React.FC = () => {
  const nodeTypes = [
    {
      name: 'Input',
      category: 'IO',
      icon: FileInput,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
      description: 'Ingests prompts, user payloads, and webhook triggers.',
    },
    {
      name: 'LLM',
      category: 'AI',
      icon: Bot,
      color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
      description: 'Executes reasoning chains with Google Gemini 1.5 Pro / Flash.',
    },
    {
      name: 'Document Reader',
      category: 'Data',
      icon: FileText,
      color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
      description: 'Parses and chunks PDF, DOCX, Markdown, and text context.',
    },
    {
      name: 'Tool',
      category: 'Action',
      icon: Wrench,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
      description: 'Executes API calls, web searches, and custom Python actions.',
    },
    {
      name: 'Condition',
      category: 'Logic',
      icon: GitFork,
      color: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
      description: 'Evaluates expressions to branch execution based on dynamic data.',
    },
    {
      name: 'Human Approval',
      category: 'Control',
      icon: UserCheck,
      color: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
      description: 'Human-in-the-loop pause gate for sensitive action approvals.',
    },
    {
      name: 'Output',
      category: 'IO',
      icon: FileOutput,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
      description: 'Formats and synthesizes final reports, metrics, and exports.',
    },
  ];

  const teamMembers = [
    {
      role: 'Member 1: Frontend Development',
      badge: 'React / React Flow / Tailwind',
      color: 'border-indigo-500/30 bg-indigo-500/5',
      focus: 'Visual canvas drag-and-drop, node inspector panels, dynamic graph state management, live execution tracing, and dashboard UI.',
    },
    {
      role: 'Member 2: Backend and Database',
      badge: 'FastAPI / SQLAlchemy / SQLite',
      color: 'border-cyan-500/30 bg-cyan-500/5',
      focus: 'REST API routing, database schema migrations, workflow persistence, execution history logging, and health/metrics endpoints.',
    },
    {
      role: 'Member 3: AI Agent Architect',
      badge: 'Gemini API / Prompt Engineering',
      color: 'border-purple-500/30 bg-purple-500/5',
      focus: 'Instruction-to-workflow translation prompts, intent parsing, structured JSON schema generation, and Gemini API integration.',
    },
    {
      role: 'Member 4: Workflow Generation & Components',
      badge: 'Graph DSL / Component Registry',
      color: 'border-amber-500/30 bg-amber-500/5',
      focus: 'Node definition catalog, connection validation rules, cycle detection, input/output port compatibility, and schema versioning.',
    },
    {
      role: 'Member 5: Workflow Execution Engine',
      badge: 'LangGraph / Async Runtime',
      color: 'border-emerald-500/30 bg-emerald-500/5',
      focus: 'LangGraph state graph compilation, asynchronous step runner, tool invocation sandbox, human approval pause/resume hooks.',
    },
    {
      role: 'Member 6: Testing, Validation & Self-Repair',
      badge: 'Pytest / Auto-Fix Loop',
      color: 'border-rose-500/30 bg-rose-500/5',
      focus: 'Automated test suite, static DAG validation, failure diagnosis agent, and autonomous graph self-repair feedback loop.',
    },
  ];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="relative pt-6 pb-2 text-center max-w-4xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
          <Zap className="w-3.5 h-3.5" />
          <span>Autonomous Visual Agent Platform</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Turn Natural Language into <br />
          <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-400 bg-clip-text text-transparent">
            Executable Visual Workflows
          </span>
        </h1>
        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
          AgentForge AI generates workflows, validates topology, tests functionality, detects failures, and performs autonomous self-repairs.
        </p>
      </section>

      {/* Visual Canvas Demo Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Workflow className="w-5 h-5 text-indigo-400" />
              Visual Workflow Studio Canvas
            </h2>
            <p className="text-xs text-slate-400">
              Interactive React Flow engine wired with shared node architecture.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">@xyflow/react v13+</span>
        </div>
        <WorkflowCanvasPreview />
      </section>

      {/* Supported Node Types Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Supported Node Types (Specification 1.0)
            </h2>
            <p className="text-xs text-slate-400">
              Contract defined in <code className="text-indigo-300">shared/node_definitions.json</code>
            </p>
          </div>
          <span className="text-xs text-slate-400 bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">
            7 Registered Primitives
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {nodeTypes.map((node) => {
            const Icon = node.icon;
            return (
              <div
                key={node.name}
                className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all hover:translate-y-[-2px] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2 rounded-lg border ${node.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      {node.category}
                    </span>
                  </div>
                  <h3 className="font-semibold text-sm text-slate-100">{node.name}</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{node.description}</p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Schema verified</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 6-Member Team Architecture & Responsibilities */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-400" />
              Six-Member Engineering Team Architecture
            </h2>
            <p className="text-xs text-slate-400">
              Clear modular segregation ensures parallel development across frontend, backend, AI, and runtime engine.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teamMembers.map((member) => (
            <div
              key={member.role}
              className={`p-5 rounded-xl border ${member.color} bg-slate-900/40 space-y-2`}
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-bold text-sm text-slate-200">{member.role}</h3>
              </div>
              <div className="inline-block px-2 py-0.5 rounded text-[11px] font-mono font-medium text-slate-300 bg-slate-800/80 border border-slate-700/60">
                {member.badge}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed pt-1">{member.focus}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Monorepo Architecture Directory Guide */}
      <section className="p-6 rounded-2xl border border-slate-800 bg-slate-900/30 space-y-4">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <span>Project Monorepo Structure</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-indigo-400 font-bold mb-1">frontend/</div>
            <div className="text-slate-400 font-sans">React + Vite + Tailwind + @xyflow/react visual workflow editor.</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-cyan-400 font-bold mb-1">backend/</div>
            <div className="text-slate-400 font-sans">FastAPI + SQLAlchemy + SQLite, modular api/core/db/models/services.</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-emerald-400 font-bold mb-1">shared/</div>
            <div className="text-slate-400 font-sans">Single source of truth JSON schemas, node specifications & TS types.</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="text-purple-400 font-bold mb-1">docs/</div>
            <div className="text-slate-400 font-sans">Architecture, API specification, 6-member team guide & roadmap.</div>
          </div>
        </div>
      </section>
    </div>
  );
};

