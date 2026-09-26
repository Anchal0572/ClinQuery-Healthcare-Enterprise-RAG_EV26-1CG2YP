import React, { useState, useEffect } from 'react';
import {
  History,
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Search,
  ArrowRight,
  Clock,
  User,
  MessageSquare,
  Sparkles,
  ChevronDown,
  ChevronUp,
  FileText,
} from 'lucide-react';
import { getAuditLogs } from '../services/api';
import { AuditLogItem } from '../types';

interface AuditPageProps {
  onRerunQuery?: (question: string) => void;
}

export const AuditPage: React.FC<AuditPageProps> = ({ onRerunQuery }) => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchLogs = async (filter?: string) => {
    setLoading(true);
    setError(null);
    try {
      const activeFilter = filter !== undefined ? filter : statusFilter;
      const data = await getAuditLogs(activeFilter === 'ALL' ? undefined : activeFilter);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch clinical audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [statusFilter]);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <History className="w-6 h-6 text-sky-600" />
            Clinical Audit Log & Governance History
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Complete traceability of clinical questions, evidence statuses, and grounded answers for regulatory compliance.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchLogs()}
            disabled={loading}
            className="flex items-center space-x-2 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition shadow-sm text-xs font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search questions or answer text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
          />
        </div>

        {/* Status Filter Chips */}
        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          {[
            { id: 'ALL', label: 'All Queries' },
            { id: 'SUFFICIENT', label: 'Sufficient Evidence' },
            { id: 'CONFLICTED', label: 'Protocol Conflict' },
            { id: 'INSUFFICIENT', label: 'Insufficient / Refused' },
          ].map((st) => (
            <button
              key={st.id}
              onClick={() => setStatusFilter(st.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                statusFilter === st.id
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Logs Table / List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-sky-600" />
            <p className="text-sm">Fetching audit logs from database...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <History className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No audit log records found</p>
            <p className="text-xs text-slate-400">Run a clinical question in the "Ask ClinQuery" tab to record queries.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredLogs.map((log) => {
              const isExpanded = expandedId === log.id;
              const dateStr = new Date(log.created_at).toLocaleString();

              return (
                <div key={log.id} className="transition hover:bg-slate-50/60">
                  <div
                    onClick={() => toggleExpand(log.id)}
                    className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {log.evidence_status === 'SUFFICIENT' && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase">
                            <ShieldCheck className="w-3 h-3" />
                            <span>SUFFICIENT</span>
                          </span>
                        )}
                        {log.evidence_status === 'CONFLICTED' && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-300 text-[10px] font-bold uppercase">
                            <AlertTriangle className="w-3 h-3 text-amber-600" />
                            <span>CONFLICT DETECTED</span>
                          </span>
                        )}
                        {log.evidence_status === 'INSUFFICIENT' && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-bold uppercase">
                            <AlertCircle className="w-3 h-3" />
                            <span>INSUFFICIENT REFUSAL</span>
                          </span>
                        )}

                        {/* RBAC Badges */}
                        {log.user_role && (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
                            <span>Role: {log.user_role}</span>
                          </span>
                        )}

                        {log.access_status === 'FILTERED' ? (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-300">
                            <span>Access: FILTERED</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span>Access: GRANTED</span>
                          </span>
                        )}

                        <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{dateStr}</span>
                        </span>

                        <span className="text-[11px] font-mono text-slate-400">
                          Log #{log.id}
                        </span>
                      </div>

                      <div className="text-sm font-semibold text-slate-900 leading-snug">
                        {log.question}
                      </div>

                      {!isExpanded && (
                        <p className="text-xs text-slate-500 line-clamp-1">
                          {log.answer}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center space-x-3 self-end sm:self-center">
                      {onRerunQuery && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRerunQuery(log.question);
                          }}
                          className="px-2.5 py-1 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 rounded-lg transition flex items-center space-x-1"
                          title="Re-run this question in Ask ClinQuery"
                        >
                          <span>Ask Again</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      )}
                      <button
                        type="button"
                        className="text-slate-400 hover:text-slate-600 p-1"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Detail Panel */}
                  {isExpanded && (
                    <div className="px-5 pb-5 pt-1 space-y-4 bg-slate-50/70 border-t border-slate-100">
                      <div>
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                          Clinical Answer Generated:
                        </span>
                        <div className="p-4 bg-white rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                          {log.answer}
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                        <div>Logged under PostgreSQL `audit_logs` table with tamper-evident record ID {log.id}.</div>
                        {onRerunQuery && (
                          <button
                            onClick={() => onRerunQuery(log.question)}
                            className="font-medium text-sky-600 hover:underline flex items-center space-x-1"
                          >
                            <span>Open in Ask ClinQuery</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
