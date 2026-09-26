import { AskResponse, DocumentSummary, AuditLogItem, RagStatus, User, EvaluationResponse } from '../types';

const BASE_URL = '';

export async function getHealth(): Promise<{ status: string; database: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Failed to fetch health status');
  return res.json();
}

export async function getRagStatus(): Promise<RagStatus> {
  const res = await fetch(`${BASE_URL}/api/rag/status`);
  if (!res.ok) throw new Error('Failed to fetch RAG status');
  return res.json();
}

export async function askClinQuery(
  question: string,
  top_k: number = 4,
  user_id?: number | null,
  user_role?: string
): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/api/rag/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k, user_id, user_role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to execute ClinQuery RAG search');
  }
  return res.json();
}

export async function getDocuments(): Promise<DocumentSummary[]> {
  const res = await fetch(`${BASE_URL}/api/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function getDocumentDetail(id: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/documents/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch document ${id}`);
  return res.json();
}

export async function uploadDocument(formData: FormData): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Document upload failed');
  }
  return res.json();
}

export async function indexDocument(documentId: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/rag/index/${documentId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to index document ${documentId}`);
  }
  return res.json();
}

export async function getAuditLogs(statusFilter?: string): Promise<AuditLogItem[]> {
  const url = statusFilter
    ? `${BASE_URL}/api/audit-logs?evidence_status=${encodeURIComponent(statusFilter)}`
    : `${BASE_URL}/api/audit-logs`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

export async function getUsers(): Promise<User[]> {
  const res = await fetch(`${BASE_URL}/api/users`);
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function getEvaluation(): Promise<EvaluationResponse> {
  const res = await fetch(`${BASE_URL}/api/evaluation`);
  if (!res.ok) throw new Error('Failed to fetch evaluation benchmark');
  return res.json();
}

export async function runEvaluation(): Promise<EvaluationResponse> {
  const res = await fetch(`${BASE_URL}/api/evaluation/run`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to run evaluation benchmark');
  }
  return res.json();
}
