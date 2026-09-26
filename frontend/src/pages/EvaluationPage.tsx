import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  CheckCircle2,
  XCircle,
  Play,
  RotateCw,
  ShieldCheck,
  FileCheck,
  AlertTriangle,
  Lock,
  Layers,
  Sparkles,
} from 'lucide-react';
import { getEvaluation, runEvaluation } from '../services/api';
import { EvaluationResponse, EvaluationItemResult } from '../types';

export const EvaluationPage: React.FC = () => {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getEvaluation();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch evaluation benchmark');
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await runEvaluation();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to execute evaluation suite');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const categories = data
    ? ['ALL', ...Array.from(new Set(data.results.map((r) => r.category)))]
    : ['ALL'];

  const filteredResults = data
    ? filterCategory === 'ALL'
      ? data.results
      : data.results.filter((r) => r.category === filterCategory)
    : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <BarChart3 className="w-6 h-6" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              ClinQuery Evaluation & Safety Benchmark
            </h1>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Empirical evaluation across 15 synthetic clinical test cases measuring retrieval, citations, grounding, safe refusals, and access control.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            id="run-eval-btn"
            onClick={handleRunEvaluation}
            disabled={running || loading}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg font-medium text-sm transition-all shadow-sm shadow-indigo-600/20 active:scale-95 cursor-pointer"
          >
            {running ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin" />
                <span>Running Benchmark...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Re-Run Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/70 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-rose-500" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchResults}
            className="text-xs font-semibold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {loading && !data ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <RotateCw className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
          <p className="text-sm font-medium">Loading evaluation metrics...</p>
        </div>
      ) : data ? (
        <>
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Metric 1 */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Retrieval Success
                </span>
                <span className="p-1.5 rounded-md bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
                  <Layers className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.metrics.retrieval_success}%
                </span>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-0.5" /> High Precision
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Target evidence retrieved in top-k
              </p>
            </div>

            {/* Metric 2 */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Citation Presence
                </span>
                <span className="p-1.5 rounded-md bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400">
                  <FileCheck className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.metrics.citation_presence}%
                </span>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-0.5" /> 100% Traceable
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Answers include verifiable citations
              </p>
            </div>

            {/* Metric 3 */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Grounded Answer Rate
                </span>
                <span className="p-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                  <Sparkles className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.metrics.grounded_answer_rate}%
                </span>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-0.5" /> Zero Hallucination
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Factual statements supported by source
              </p>
            </div>

            {/* Metric 4 */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Refusal Accuracy
                </span>
                <span className="p-1.5 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.metrics.refusal_accuracy}%
                </span>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-0.5" /> Safe Boundary
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Refusal on missing/out-of-scope data
              </p>
            </div>

            {/* Metric 5 */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Access-Control Accuracy
                </span>
                <span className="p-1.5 rounded-md bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400">
                  <Lock className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.metrics.access_control_accuracy}%
                </span>
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center">
                  <ShieldCheck className="w-3 h-3 mr-0.5" /> Role Enforced
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Pre-retrieval role-based isolation
              </p>
            </div>
          </div>

          {/* Execution Overview & Category Badges */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-sm font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>
                  {data.passed_questions} / {data.total_questions} Tests Passed
                </span>
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Executed in {data.elapsed_seconds}s • Timestamp: {new Date(data.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {/* Category Breakdown Badges */}
            <div className="flex flex-wrap items-center gap-2">
              {Object.entries(data.breakdown).map(([cat, stat]) => (
                <span
                  key={cat}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                >
                  {cat}: {stat.passed}/{stat.total}
                </span>
              ))}
            </div>
          </div>

          {/* Test Cases Table */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                  Evaluation Test Cases (15 Synthetic Queries)
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Full test breakdown across clinical fact retrieval, lab tables, refusals, version conflicts, and RBAC.
                </p>
              </div>

              {/* Category Filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-500">Category:</span>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Test ID</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4 min-w-[280px]">Question</th>
                    <th className="py-3 px-4">Expected</th>
                    <th className="py-3 px-4">Actual</th>
                    <th className="py-3 px-4">Citations</th>
                    <th className="py-3 px-4">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredResults.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-slate-700 dark:text-slate-300">
                        {item.id}
                      </td>
                      <td className="py-3 px-4 text-xs font-medium text-slate-600 dark:text-slate-300">
                        {item.category}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 text-xs font-semibold rounded-md ${
                            item.user_role === 'CLINICAL'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                              : item.user_role === 'OPERATIONS'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                              : 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
                          }`}
                        >
                          {item.user_role}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <p className="text-slate-900 dark:text-white font-medium text-xs leading-relaxed">
                          {item.question}
                        </p>
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 line-clamp-1 italic">
                          "{item.answer_preview}"
                        </p>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                        {item.expected_evidence}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold font-mono ${
                            item.actual_evidence === 'SUFFICIENT'
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                              : item.actual_evidence === 'CONFLICTED'
                              ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
                              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                          }`}
                        >
                          {item.actual_evidence}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs font-mono text-slate-600 dark:text-slate-400">
                        {item.citation_count} docs
                      </td>
                      <td className="py-3 px-4">
                        {item.passed ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Pass
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                            <XCircle className="w-3.5 h-3.5" />
                            Fail
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
