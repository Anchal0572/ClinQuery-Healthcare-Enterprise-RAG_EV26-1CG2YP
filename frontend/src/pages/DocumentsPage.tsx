import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Database,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Search,
  Plus,
  Layers,
  Clock,
  Building,
  Tag,
  X,
  FileCheck,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { getDocuments, uploadDocument, indexDocument, getDocumentDetail } from '../services/api';
import { DocumentSummary } from '../types';

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [version, setVersion] = useState('1.0');
  const [documentType, setDocumentType] = useState('SOP');
  const [department, setDepartment] = useState('Pharmacy');
  const [effectiveDate, setEffectiveDate] = useState(new Date().toISOString().split('T')[0]);
  const [status, setStatus] = useState('ACTIVE');
  const [allowedRoles, setAllowedRoles] = useState('ADMIN,CLINICAL');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Indexing state tracking
  const [indexingId, setIndexingId] = useState<number | null>(null);
  const [indexSuccess, setIndexSuccess] = useState<{ id: number; message: string } | null>(null);

  // Document details / chunk modal state
  const [selectedDocDetails, setSelectedDocDetails] = useState<any | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch document catalog');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('title', title || uploadFile.name);
      formData.append('version', version);
      formData.append('document_type', documentType);
      formData.append('department', department);
      formData.append('effective_date', effectiveDate);
      formData.append('status', status);
      formData.append('allowed_roles', allowedRoles);

      const res = await uploadDocument(formData);
      setUploadSuccess(`Document "${res.title}" parsed & uploaded (${res.chunks_created} chunks generated)`);
      setIsUploadOpen(false);
      // Reset form
      setUploadFile(null);
      setTitle('');
      fetchDocs();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleIndex = async (docId: number, docTitle: string) => {
    setIndexingId(docId);
    setError(null);
    setIndexSuccess(null);
    try {
      const res = await indexDocument(docId);
      setIndexSuccess({
        id: docId,
        message: `Indexed ${res.indexed_count} chunks into Qdrant for "${docTitle}"`,
      });
      fetchDocs();
    } catch (err: any) {
      setError(err.message || `Failed to index document ${docId}`);
    } finally {
      setIndexingId(null);
    }
  };

  const handleViewDetails = async (docId: number) => {
    setLoadingDetails(true);
    try {
      const details = await getDocumentDetail(docId);
      setSelectedDocDetails(details);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch document chunks');
    } finally {
      setLoadingDetails(false);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.department && doc.department.toLowerCase().includes(searchQuery.toLowerCase())) ||
      doc.document_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || doc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-sky-600" />
            Clinical Documents & Knowledge Ingestion
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage hospital guidelines, policies, and vector indexing for grounding ClinQuery.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDocs}
            disabled={loading}
            className="p-2.5 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition shadow-sm"
            title="Refresh documents"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-sky-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {uploadSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {indexSuccess && (
        <div className="bg-sky-50 border border-sky-200 text-sky-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <Database className="w-5 h-5 text-sky-600 shrink-0" />
          <span>{indexSuccess.message}</span>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by title, department, type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          {['ALL', 'ACTIVE', 'SUPERSEDED', 'RETIRED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                statusFilter === st
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Documents Table / Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-sky-600" />
            <p className="text-sm">Loading document catalog from PostgreSQL...</p>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <FileText className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No documents found matching criteria</p>
            <p className="text-xs text-slate-400">Upload a hospital guideline or adjust your search filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Document Title</th>
                  <th className="py-3.5 px-4">Type</th>
                  <th className="py-3.5 px-4">Version</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Allowed Roles</th>
                  <th className="py-3.5 px-4">Department</th>
                  <th className="py-3.5 px-4">Chunks</th>
                  <th className="py-3.5 px-4">Effective Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800 flex items-center space-x-2">
                        <FileCheck className="w-4 h-4 text-sky-600 shrink-0" />
                        <span className="truncate max-w-xs">{doc.title}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 pl-6">ID #{doc.id}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs font-medium">
                        {doc.document_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-700">
                      v{doc.version}
                    </td>
                    <td className="py-3.5 px-4">
                      {doc.status === 'ACTIVE' && (
                        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                          ACTIVE
                        </span>
                      )}
                      {doc.status === 'SUPERSEDED' && (
                        <span className="bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                          SUPERSEDED
                        </span>
                      )}
                      {doc.status === 'RETIRED' && (
                        <span className="bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                          RETIRED
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                        (doc.allowed_roles || 'ADMIN,CLINICAL').includes('OPERATIONS')
                          ? 'bg-amber-50 text-amber-800 border-amber-300'
                          : 'bg-sky-50 text-sky-800 border-sky-200'
                      }`}>
                        {doc.allowed_roles || 'ADMIN,CLINICAL'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      {doc.department || 'General'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center space-x-1 font-mono text-xs bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
                        <Layers className="w-3 h-3 text-slate-400" />
                        <span>{doc.chunk_count || 0}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500">
                      {doc.effective_date || '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleViewDetails(doc.id)}
                          className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-sky-700 bg-slate-100 hover:bg-sky-50 rounded-lg transition"
                          title="Inspect parsed chunks"
                        >
                          Chunks
                        </button>
                        <button
                          onClick={() => handleIndex(doc.id, doc.title)}
                          disabled={indexingId === doc.id}
                          className="px-3 py-1 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 rounded-lg shadow-sm transition flex items-center space-x-1"
                          title="Generate embeddings and store in Qdrant"
                        >
                          {indexingId === doc.id ? (
                            <>
                              <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                              <span>Indexing...</span>
                            </>
                          ) : (
                            <>
                              <Database className="w-3 h-3" />
                              <span>Index Qdrant</span>
                            </>
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* UPLOAD MODAL */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <Upload className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-slate-800 text-base">Upload Healthcare Document</h3>
              </div>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select File (PDF, DOCX, TXT, CSV, XLSX) *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.txt,.csv,.xlsx"
                  onChange={(e) => {
                    const f = e.target.files?.[0] || null;
                    setUploadFile(f);
                    if (f && !title) setTitle(f.name.replace(/\.[^/.]+$/, ''));
                  }}
                  className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 border border-slate-200 rounded-xl p-2 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Hospital Medication Storage SOP"
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Document Type
                  </label>
                  <select
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white"
                  >
                    <option value="SOP">SOP</option>
                    <option value="Clinical Guideline">Clinical Guideline</option>
                    <option value="Policy">Policy</option>
                    <option value="Protocol">Protocol</option>
                    <option value="Formulary">Formulary</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Version
                  </label>
                  <input
                    type="text"
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                    placeholder="e.g. 1.0 or 2.1"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. Pharmacy, ICU"
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Lifecycle Status
                  </label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white font-medium"
                  >
                    <option value="ACTIVE">ACTIVE (Current)</option>
                    <option value="SUPERSEDED">SUPERSEDED (Outdated)</option>
                    <option value="RETIRED">RETIRED</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Allowed Access Roles (RBAC)
                </label>
                <select
                  value={allowedRoles}
                  onChange={(e) => setAllowedRoles(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white font-medium"
                >
                  <option value="ADMIN,CLINICAL">ADMIN, CLINICAL (Standard Clinical Guideline/Protocol)</option>
                  <option value="ADMIN,OPERATIONS">ADMIN, OPERATIONS (Facility, Engineering & Supply Chain)</option>
                  <option value="ADMIN,CLINICAL,OPERATIONS">ADMIN, CLINICAL, OPERATIONS (Hospital-wide Access)</option>
                  <option value="ADMIN">ADMIN ONLY (Restricted Governance)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Effective Date
                </label>
                <input
                  type="date"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2 text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 rounded-xl shadow-md transition flex items-center space-x-2"
                >
                  {uploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Parsing & Chunking...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Upload & Ingest</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CHUNKS INSPECTOR MODAL */}
      {selectedDocDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="font-bold text-slate-800 text-base flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-sky-600" />
                  <span>Document Chunks ({selectedDocDetails.chunks?.length || 0})</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {selectedDocDetails.title} (v{selectedDocDetails.version}) - {selectedDocDetails.status}
                </p>
              </div>
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              {selectedDocDetails.chunks?.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">No chunks found for this document.</p>
              ) : (
                selectedDocDetails.chunks?.map((chunk: any, cIdx: number) => (
                  <div key={cIdx} className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                      <div className="flex items-center space-x-2">
                        <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
                          Chunk #{chunk.chunk_index}
                        </span>
                        {chunk.section && (
                          <span className="text-sky-700 font-medium">Sec: {chunk.section}</span>
                        )}
                        {chunk.page_number && <span>Page: {chunk.page_number}</span>}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">Tokens: ~{chunk.token_count || 0}</span>
                    </div>

                    <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs text-slate-800 whitespace-pre-wrap font-sans leading-relaxed">
                      {chunk.chunk_text}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-lg transition"
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
