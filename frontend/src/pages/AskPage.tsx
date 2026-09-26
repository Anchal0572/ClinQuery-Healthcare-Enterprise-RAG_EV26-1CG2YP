import React, { useState } from 'react';
import {
  HelpCircle,
  Search,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Lock,
  AlertTriangle,
  AlertCircle,
  BookOpen,
  FileText,
  Clock,
  ExternalLink,
  ChevronRight,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { askClinQuery } from '../services/api';
import { AskResponse, SourceChunk, User } from '../types';
import { PassageModal } from '../components/PassageModal';

interface AskPageProps {
  currentUser: User | null;
  initialQuestion?: string;
}

const DEMO_SCENARIOS = [
  {
    num: 1,
    title: '1. Normal Grounded Question',
    query: 'What are the required temperature storage conditions for refrigerated pharmaceuticals?',
    tag: 'Grounded Retrieval',
    desc: 'Retrieves Medication Storage SOP (2-8°C); synthesizes verified answer with inline citations.',
    role: 'CLINICAL',
  },
  {
    num: 2,
    title: '2. Interactive Citation Click',
    query: 'What are the guideline-directed quadruple medical therapy classes for heart failure with reduced ejection fraction (HFrEF)?',
    tag: 'Evidence Audit',
    desc: 'Retrieves AHA Heart Failure Guideline; clicking the citation tag opens the exact retrieved passage drawer.',
    role: 'CLINICAL',
  },
  {
    num: 3,
    title: '3. Conflicting Documents',
    query: 'What is the recommended first-line vasopressor and empiric antibiotic for septic shock resuscitation?',
    tag: 'Conflict Safety',
    desc: 'Detects v1.0 (SUPERSEDED, Dopamine) vs v2.0 (ACTIVE, Norepinephrine); displays clinical safety warning.',
    role: 'CLINICAL',
  },
  {
    num: 4,
    title: '4. Insufficient Evidence / Refusal',
    query: "What is the average surface atmospheric temperature of Jupiter's moon Europa and orbital velocity?",
    tag: 'Safe Refusal',
    desc: 'Out-of-scope query triggers similarity threshold guardrail; system refuses rather than hallucinating.',
    role: 'CLINICAL',
  },
  {
    num: 5,
    title: '5. Unauthorized Document (RBAC)',
    query: 'What does the hospital SOP say about medication storage?',
    tag: 'Access Control',
    desc: 'Executed with OPERATIONS role; clinical document is filtered pre-retrieval (zero clinical leakage).',
    role: 'OPERATIONS',
  },
  {
    num: 6,
    title: '6. Document Version Freshness',
    query: 'What is the recommended empiric antimicrobial therapy for sepsis resuscitation across document versions?',
    tag: 'Freshness Preference',
    desc: 'Identifies active v2.0 protocol over superseded v1.0 and highlights version lifecycle tracking.',
    role: 'CLINICAL',
  },
];

export const AskPage: React.FC<AskPageProps> = ({ currentUser, initialQuestion }) => {
  const [question, setQuestion] = useState(initialQuestion || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<SourceChunk | null>(null);
  const [activeRoleOverride, setActiveRoleOverride] = useState<string | null>(null);

  React.useEffect(() => {
    if (initialQuestion) {
      setQuestion(initialQuestion);
    }
  }, [initialQuestion]);

  const handleAsk = async (queryToAsk?: string, roleOverride?: string) => {
    const q = queryToAsk || question;
    if (!q.trim()) return;

    const roleToUse = roleOverride || activeRoleOverride || currentUser?.role || 'CLINICAL';
    setActiveRoleOverride(roleOverride || null);

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await askClinQuery(q, 4, currentUser?.id, roleToUse);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Error communicating with ClinQuery RAG engine');
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citation: any) => {
    // Find matching source chunk if available
    const match = response?.sources.find(
      (s) =>
        s.document === citation.document_title ||
        String(s.document_id) === String(citation.document_id) ||
        s.section === citation.section
    );

    if (match) {
      setSelectedChunk(match);
    } else {
      // Create temporary chunk view from citation
      setSelectedChunk({
        chunk_id: 0,
        similarity_score: 1.0,
        chunk_text: `Citation reference: ${citation.document_title}\nSection: ${citation.section || 'General'}\nPage: ${citation.page || 1}`,
        document: citation.document_title,
        version: citation.version || '1.0',
        page: citation.page,
        section: citation.section,
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Search Input Box */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200">
        <div className="flex items-center space-x-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center">
            <HelpCircle className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Ask ClinQuery</h2>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="space-y-4"
        >
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask your healthcare question... (e.g., medication storage rules, sepsis protocol, lab intervals)"
              className="w-full p-4 text-base border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 focus:outline-none transition shadow-inner placeholder-slate-400"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-slate-400" />
              <span>Role: <strong className="text-slate-600 font-semibold">{currentUser?.role || 'CLINICAL'}</strong></span>
              <span>•</span>
              <span>Pre-retrieval document access control active.</span>
            </div>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-6 py-2.5 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white font-semibold text-sm rounded-xl shadow-md shadow-sky-600/20 transition flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Retrieving Evidence...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Ask</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Final Demo Scenarios Panel */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Live Demonstration Scenarios (Hackathon Showcase):
            </span>
            <span className="text-[11px] text-slate-400">Click any card to execute live</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {DEMO_SCENARIOS.map((s) => (
              <button
                key={s.num}
                type="button"
                onClick={() => {
                  setQuestion(s.query);
                  handleAsk(s.query, s.role);
                }}
                className="text-left p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-sky-50/80 hover:border-sky-300 transition-all flex flex-col justify-between group active:scale-[0.99] cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-bold text-slate-800 group-hover:text-sky-700">
                      {s.title}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                        s.role === 'OPERATIONS'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-sky-100 text-sky-800 border border-sky-200'
                      }`}
                    >
                      {s.role}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug line-clamp-2">
                    {s.desc}
                  </p>
                </div>
                <div className="mt-2.5 flex items-center justify-between pt-1.5 border-t border-slate-200/60 text-[10px] text-slate-400">
                  <span className="font-semibold text-sky-600">[{s.tag}]</span>
                  <span className="flex items-center text-sky-600 font-medium group-hover:translate-x-0.5 transition-transform">
                    Run <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* Answer Section */}
      {response && (
        <div className="space-y-6">
          {/* Main Answer Box */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
            {/* Header / Status Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-slate-900 text-lg">Answer</h3>
              </div>

              {/* Evidence & Access Status Badges */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Access Status Badge */}
                {response.access_status === 'FILTERED' ? (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-300 text-xs font-bold uppercase tracking-wider">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                    <span>Access: FILTERED</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold uppercase tracking-wider">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Access: GRANTED</span>
                  </span>
                )}

                {/* Evidence Status Badge */}
                {response.evidence_status === 'SUFFICIENT' && (
                  <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold uppercase tracking-wider">
                    <span>Evidence: SUFFICIENT</span>
                  </span>
                )}
                {response.evidence_status === 'CONFLICTED' && (
                  <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-300 text-xs font-bold uppercase tracking-wider animate-pulse">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Evidence: CONFLICTED</span>
                  </span>
                )}
                {response.evidence_status === 'INSUFFICIENT' && (
                  <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-300 text-xs font-bold uppercase tracking-wider">
                    <AlertCircle className="w-4 h-4 text-slate-500" />
                    <span>Evidence: INSUFFICIENT</span>
                  </span>
                )}
              </div>
            </div>

            {/* ROLE RESTRICTION WARNING CARD */}
            {response.access_status === 'FILTERED' && (
              <div className="bg-rose-50/90 border-2 border-rose-300 rounded-xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-rose-900 font-bold text-sm">
                  <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>PRE-RETRIEVAL ACCESS CONTROL: ROLE RESTRICTION ENFORCED</span>
                </div>
                <p className="text-xs text-rose-800 leading-relaxed">
                  Your active role (<strong>{currentUser?.role || response.user_role || 'OPERATIONS'}</strong>) does not have authorization to view protected clinical documents matching this query.
                  Pre-retrieval role filtering prevented unauthorized documents from being searched in Qdrant. <strong>Unauthorized documents NEVER entered LLM context.</strong>
                </p>
              </div>
            )}

            {/* CONFLICT WARNING CARD */}
            {response.evidence_status === 'CONFLICTED' && response.conflicts && response.conflicts.length > 0 && (
              <div className="bg-amber-50/80 border-2 border-amber-300 rounded-xl p-5 space-y-4">
                <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm sm:text-base">
                  <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                  <span>CLINICAL SAFETY ALERT — CONFLICTING PROTOCOLS DETECTED</span>
                </div>
                <p className="text-xs text-amber-800 leading-relaxed">
                  The knowledge base contains contradictory clinical recommendations across different document versions.
                  The system refuses to silently choose between them. Current active guidance is prioritized below.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  {response.conflicts.map((conf, cIdx) => (
                    <div
                      key={cIdx}
                      className={`p-4 rounded-xl border text-xs space-y-2.5 transition ${
                        conf.is_active_fresh
                          ? 'bg-white border-emerald-400 shadow-sm ring-1 ring-emerald-200'
                          : 'bg-slate-50 border-slate-300 text-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 truncate">{conf.source}</span>
                        {conf.is_active_fresh ? (
                          <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">
                            ACTIVE CURRENT (FRESH)
                          </span>
                        ) : (
                          <span className="bg-slate-200 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-slate-300">
                            SUPERSEDED / RETIRED
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-slate-500 flex items-center space-x-3">
                        <span>Version: <strong>v{conf.version}</strong></span>
                        {conf.date && <span>Date: <strong>{conf.date}</strong></span>}
                      </div>

                      <div className="p-2.5 bg-slate-50 rounded border border-slate-200 text-slate-800 font-medium">
                        "{conf.claim}"
                      </div>

                      <div className="text-[11px] text-slate-500 italic">
                        Passage: "{conf.relevant_passage}"
                      </div>

                      <div className="text-[10px] font-mono text-sky-700 pt-1 border-t border-slate-100 truncate">
                        Citation: {conf.citation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* INSUFFICIENT EVIDENCE CARD */}
            {response.evidence_status === 'INSUFFICIENT' && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-slate-800 font-bold text-sm">
                  <AlertCircle className="w-5 h-5 text-slate-500" />
                  <span>Clinical Knowledge Base Refusal</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  The retrieval similarity score was below the clinical grounding threshold (0.65). To protect patient safety, ClinQuery does not hallucinate or guess without authorized hospital evidence.
                </p>
              </div>
            )}

            {/* Answer Content */}
            <div className="prose prose-slate max-w-none text-sm sm:text-base leading-relaxed text-slate-800 whitespace-pre-wrap font-sans">
              {response.answer}
            </div>

            {/* CITATIONS CARDS */}
            {response.citations && response.citations.length > 0 && (
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <BookOpen className="w-4 h-4 text-sky-600" />
                  <span>Clinical Citations (Click to view exact verbatim text)</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {response.citations.map((cit, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleCitationClick(cit)}
                      className="text-left p-3.5 rounded-xl border border-slate-200 hover:border-sky-400 hover:bg-sky-50/40 transition group flex items-start justify-between"
                    >
                      <div className="space-y-1">
                        <div className="text-xs font-bold text-slate-800 group-hover:text-sky-900 leading-tight">
                          {cit.document_title}
                        </div>
                        <div className="text-[11px] text-slate-500 flex flex-wrap gap-2">
                          {cit.section && (
                            <span className="text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-100">
                              Sec: {cit.section}
                            </span>
                          )}
                          {cit.page && <span>Page {cit.page}</span>}
                        </div>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600 shrink-0 ml-2 mt-0.5" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* SOURCES SECTION */}
          {response.sources && response.sources.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-slate-500" />
                  <h4 className="font-bold text-slate-800 text-sm">
                    Retrieved Evidence Chunks ({response.sources.length})
                  </h4>
                </div>
                <span className="text-xs text-slate-400">Dense vector similarity search via Qdrant</span>
              </div>

              <div className="space-y-3">
                {response.sources.map((source, sIdx) => (
                  <div
                    key={sIdx}
                    onClick={() => setSelectedChunk(source)}
                    className="p-4 rounded-xl border border-slate-200 hover:border-sky-400 hover:bg-slate-50/80 cursor-pointer transition space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-800">{source.document}</span>
                        {source.version && (
                          <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[10px]">
                            v{source.version}
                          </span>
                        )}
                        {source.section && (
                          <span className="text-sky-700 font-medium">| {source.section}</span>
                        )}
                      </div>
                      <span className="font-mono text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                        Score: {source.similarity_score.toFixed(4)}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                      "{source.chunk_text}"
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                      <span>Type: {source.chunk_type || 'text'}</span>
                      <span className="text-sky-600 hover:underline flex items-center space-x-0.5">
                        <span>Inspect passage</span>
                        <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Verbatim Passage Modal */}
      <PassageModal chunk={selectedChunk} onClose={() => setSelectedChunk(null)} />
    </div>
  );
};
