import React, { useEffect, useState } from 'react';
import {
  Activity,
  Database,
  Cpu,
  FileText,
  AlertTriangle,
  History,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  Layers,
  ShieldAlert,
} from 'lucide-react';
import { getHealth, getRagStatus, getDocuments, getAuditLogs } from '../services/api';
import { DocumentSummary, RagStatus, AuditLogItem } from '../types';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardProps> = ({ onNavigate }) => {
  const [dbStatus, setDbStatus] = useState<string>('checking...');
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [health, rag, docs, logs] = await Promise.all([
          getHealth().catch(() => ({ status: 'error', database: 'disconnected' })),
          getRagStatus().catch(() => null),
          getDocuments().catch(() => []),
          getAuditLogs().catch(() => []),
        ]);
        setDbStatus(health.database === 'connected' ? 'Connected' : 'Disconnected');
        setRagStatus(rag);
        setDocuments(docs);
        setAuditLogs(logs);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalChunks = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);
  const conflictedCount = auditLogs.filter((l) => l.evidence_status === 'CONFLICTED').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-sky-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/20 text-sky-200 border border-sky-400/30 text-xs font-semibold mb-3">
            <Activity className="w-3.5 h-3.5 text-sky-300 animate-pulse" />
            <span>Healthcare Greenfield Enterprise RAG v1.0</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
            Retrieval a Clinical Team Can Rely On
          </h1>
          <p className="text-sm sm:text-base text-sky-100/90 leading-relaxed mb-6">
            ClinQuery eliminates medical hallucinations and prevents silent protocol selection.
            Every clinical claim is verified, cited with document & page coordinates, and guarded
            by automated conflict detection.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('ask')}
              className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-white font-semibold text-sm rounded-xl shadow-lg shadow-sky-900/30 transition flex items-center space-x-2"
            >
              <HelpCircle className="w-4 h-4" />
              <span>Ask ClinQuery</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('documents')}
              className="px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white font-semibold text-sm rounded-xl border border-white/20 transition flex items-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span>Manage Documents</span>
            </button>
          </div>
        </div>
      </div>

      {/* Live Health Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PostgreSQL Indicator */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-400 uppercase">PostgreSQL Database</div>
              <div className="text-sm font-bold text-slate-800">Port 5433 (Local Cluster)</div>
            </div>
          </div>
          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded-full flex items-center space-x-1 ${
              dbStatus === 'Connected'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{dbStatus}</span>
          </span>
        </div>

        {/* Qdrant Indicator */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-400 uppercase">Qdrant Vector Engine</div>
              <div className="text-sm font-bold text-slate-800">
                {ragStatus?.collection || 'healthcare_chunks'}
              </div>
            </div>
          </div>
          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded-full flex items-center space-x-1 ${
              ragStatus?.qdrant?.status === 'connected'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{ragStatus?.qdrant?.status === 'connected' ? 'Active & Ready' : 'Connecting...'}</span>
          </span>
        </div>

        {/* Embedding Engine Indicator */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-400 uppercase">Embedding Model</div>
              <div className="text-sm font-bold text-slate-800">
                {ragStatus?.embedding?.model ? 'BGE-Small ONNX (384d)' : 'FastEmbed ONNX'}
              </div>
            </div>
          </div>
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-sky-50 text-sky-700 border border-sky-200">
            Local CPU
          </span>
        </div>
      </div>

      {/* Numerical Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500">Documents Ingested</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">{documents.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">PDF, DOCX, CSV, XLSX, TXT</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500">Searchable Chunks</div>
          <div className="text-3xl font-extrabold text-sky-600 mt-1">{totalChunks}</div>
          <div className="text-[11px] text-slate-400 mt-1">Preserving table row/col/val</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500">Total Audited Queries</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">{auditLogs.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">Persisted to PostgreSQL</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-amber-600">Conflicted Protocols Flagged</div>
          <div className="text-3xl font-extrabold text-amber-600 mt-1">{conflictedCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Version safety alerts</div>
        </div>
      </div>

      {/* Recent Queries Preview */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
            <History className="w-5 h-5 text-sky-600" />
            <span>Recent Clinical Inquiries</span>
          </h3>
          <button
            onClick={() => onNavigate('audit')}
            className="text-xs font-semibold text-sky-600 hover:text-sky-800 transition flex items-center space-x-1"
          >
            <span>View Complete Audit Trail</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {auditLogs.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">
            No queries logged yet. Try asking your first healthcare question!
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {auditLogs.slice(0, 4).map((log) => (
              <div key={log.id} className="py-3 flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="text-sm font-semibold text-slate-800">{log.question}</div>
                  <div className="text-xs text-slate-500 line-clamp-1 mt-0.5">{log.answer}</div>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      log.evidence_status === 'SUFFICIENT'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : log.evidence_status === 'CONFLICTED'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {log.evidence_status}
                  </span>
                  <span className="text-[10px] text-slate-400 mt-1">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
