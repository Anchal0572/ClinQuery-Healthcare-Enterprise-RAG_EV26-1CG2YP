export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  page?: number | null;
  section?: string | null;
}

export interface SourceChunk {
  chunk_id: number;
  similarity_score: number;
  chunk_text: string;
  document: string;
  document_id?: number | null;
  version?: string | null;
  page?: number | null;
  section?: string | null;
  chunk_type?: string | null;
  department?: string | null;
  status?: string | null;
  effective_date?: string | null;
}

export interface ConflictItem {
  source: string;
  version: string;
  date?: string | null;
  status?: string | null;
  claim: string;
  relevant_passage: string;
  citation: string;
  is_active_fresh: boolean;
}

export interface AskResponse {
  answer: string;
  evidence_status: 'SUFFICIENT' | 'INSUFFICIENT' | 'CONFLICTED' | string;
  user_role?: string;
  access_status?: 'GRANTED' | 'FILTERED' | 'DENIED' | string;
  citations: Citation[];
  sources: SourceChunk[];
  conflicts: ConflictItem[];
  audit_log_id?: number | null;
}

export interface DocumentSummary {
  id: number;
  title: string;
  document_type: string;
  version: string;
  status: string;
  department?: string | null;
  effective_date?: string | null;
  allowed_roles?: string;
  file_path?: string | null;
  file_size_bytes?: number | null;
  created_at: string;
  chunk_count: number;
}

export interface AuditLogItem {
  id: number;
  user_id?: number | null;
  user_role?: string;
  access_status?: string;
  question: string;
  answer: string;
  evidence_status: string;
  created_at: string;
}

export interface RagStatus {
  status: string;
  qdrant: {
    status: string;
    url: string;
    collections?: string[];
  };
  collection: string;
  embedding: {
    provider: string;
    model: string;
    dimension: number;
  };
}

export interface EvaluationItemResult {
  id: string;
  category: string;
  question: string;
  user_role: string;
  expected_evidence: string;
  actual_evidence: string;
  expected_access: string;
  actual_access: string;
  citation_count: number;
  source_count: number;
  passed: boolean;
  answer_preview: string;
}

export interface EvaluationMetrics {
  retrieval_success: number;
  citation_presence: number;
  grounded_answer_rate: number;
  refusal_accuracy: number;
  access_control_accuracy: number;
}

export interface EvaluationResponse {
  timestamp: string;
  total_questions: number;
  passed_questions: number;
  elapsed_seconds: number;
  metrics: EvaluationMetrics;
  breakdown: Record<string, { total: number; passed: number }>;
  results: EvaluationItemResult[];
}
