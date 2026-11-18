import React, { useState } from 'react';
import {
  History,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  Play,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { ExecutionRecord } from '../../types';

export const ExecutionHistoryPage: React.FC = () => {
  const { executionHistory, setCurrentPage } = useWorkflow();

  const [filter, setFilter] = useState<'all' | 'completed' | 'repaired' | 'failed'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<ExecutionRecord | null>(null);

  const filteredHistory = executionHistory.filter((rec) => {
    const matchesFilter =
      filter === 'all' ||
      (filter === 'completed' && rec.status === 'completed') ||
      (filter === 'repaired' && rec.status === 'repaired') ||
      (filter === 'failed' && rec.status === 'failed');

    const matchesSearch =
      rec.agentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rec.id.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Heading */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF5F1] border border-[#CF8047]/30 text-[#B15F2C] text-xs font-semibold">
          <History className="w-3.5 h-3.5" />
          <span>Audit Log & Trace History</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#111111] tracking-tight">
          Execution History
        </h1>
        <p className="text-sm text-[#8D8D8D]">
          Review past runs, execution times, component telemetry, and automatic repair logs.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-subtle flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Filters */}
        <div className="flex items-center gap-1.5 bg-[#F1F0EE] p-1 rounded-2xl w-full sm:w-auto">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filter === 'all'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            All Runs ({executionHistory.length})
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filter === 'completed'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            Successful
          </button>
          <button
            onClick={() => setFilter('repaired')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filter === 'repaired'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            Auto-Repaired
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filter === 'failed'
                ? 'bg-[#FFFFFF] text-[#111111] shadow-subtle'
                : 'text-[#8D8D8D] hover:text-[#111111]'
            }`}
          >
            Failed
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-[#8D8D8D] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search executions..."
            className="w-full text-xs text-[#111111] placeholder:text-[#8D8D8D] bg-[#F1F0EE]/60 border border-[#E6E5E2] rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-[#B15F2C] focus:bg-[#FFFFFF]"
          />
        </div>
      </div>

      {/* Executions Table Card */}
      <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#E6E5E2] shadow-card space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E6E5E2] text-[#8D8D8D] text-[11px] pb-2">
                <th className="py-2.5 font-semibold">Agent Name</th>
                <th className="py-2.5 font-semibold">Execution ID</th>
                <th className="py-2.5 font-semibold">Date & Time</th>
                <th className="py-2.5 font-semibold">Duration</th>
                <th className="py-2.5 font-semibold">Status</th>
                <th className="py-2.5 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6E5E2]">
              {filteredHistory.map((rec) => (
                <tr key={rec.id} className="hover:bg-[#F1F0EE]/40 transition-colors">
                  <td className="py-3.5 font-bold text-[#111111]">{rec.agentName}</td>
                  <td className="py-3.5 text-[#8D8D8D] font-mono text-[11px]">{rec.id}</td>
                  <td className="py-3.5 text-[#8D8D8D]">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#8D8D8D]" />
                      {rec.startedAt}
                    </span>
                  </td>
                  <td className="py-3.5 text-[#111111] font-medium">{rec.duration}</td>
                  <td className="py-3.5">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        rec.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : rec.status === 'repaired'
                          ? 'bg-blue-50 text-blue-800 border border-blue-200'
                          : 'bg-rose-50 text-rose-800 border border-rose-200'
                      }`}
                    >
                      {rec.status === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                      {rec.status === 'repaired' && <CheckCircle2 className="w-3 h-3 text-blue-600" />}
                      {rec.status === 'failed' && <AlertCircle className="w-3 h-3 text-rose-600" />}
                      <span>{rec.status.toUpperCase()}</span>
                    </span>
                  </td>
                  <td className="py-3.5 text-right">
                    <button
                      onClick={() => setSelectedRecord(rec)}
                      className="px-3 py-1 rounded-full bg-[#F1F0EE] hover:bg-[#0A0A0A] hover:text-white text-[#111111] text-[11px] font-semibold transition-colors"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredHistory.length === 0 && (
          <div className="py-12 text-center text-xs text-[#8D8D8D] space-y-2">
            <p>No execution records match your filter criteria.</p>
            <button
              onClick={() => {
                setFilter('all');
                setSearchQuery('');
              }}
              className="text-[#B15F2C] font-semibold hover:underline"
            >
              Reset filters
            </button>
          </div>
        )}
      </div>

      {/* Selected Run Details Modal / Drawer */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#FFFFFF] rounded-3xl max-w-xl w-full border border-[#E6E5E2] shadow-elevated p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#E6E5E2]">
              <div>
                <h3 className="font-bold text-base text-[#111111]">{selectedRecord.agentName}</h3>
                <p className="text-xs text-[#8D8D8D] font-mono">{selectedRecord.id} • {selectedRecord.startedAt}</p>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  selectedRecord.status === 'completed'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : selectedRecord.status === 'repaired'
                    ? 'bg-blue-50 text-blue-800 border border-blue-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                {selectedRecord.status.toUpperCase()}
              </span>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-xs text-[#111111]">Steps Executed:</h4>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {selectedRecord.steps.map((st, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[#F1F0EE]/60 border border-[#E6E5E2] flex items-center justify-between text-xs"
                  >
                    <div>
                      <p className="font-bold text-[#111111]">{st.componentName}</p>
                      <p className="text-[11px] text-[#8D8D8D]">{st.activity}</p>
                    </div>
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-white text-emerald-800">
                      {st.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-[#E6E5E2]">
              <button
                onClick={() => {
                  setSelectedRecord(null);
                  setCurrentPage('activity');
                }}
                className="text-xs text-[#B15F2C] font-semibold hover:underline"
              >
                Open in Full Live Monitor →
              </button>

              <button
                onClick={() => setSelectedRecord(null)}
                className="px-5 py-2 rounded-full bg-[#0A0A0A] hover:bg-[#1F1F1F] text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

