from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Clinical or protocol query")
    top_k: int = Field(5, ge=1, le=50, description="Number of top chunks to retrieve")
    department: Optional[str] = Field(None, description="Optional department filter")


class SearchResultItem(BaseModel):
    chunk_id: Optional[int] = Field(None, description="Database chunk primary key")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    chunk_text: str = Field(..., description="Content of the retrieved chunk")
    document: str = Field(..., description="Document title")
    document_id: Optional[int] = Field(None, description="Parent document database ID")
    version: Optional[str] = Field(None, description="Document version")
    page: Optional[int] = Field(None, description="Physical or logical page number")
    section: Optional[str] = Field(None, description="Section or header hierarchy")
    chunk_type: Optional[str] = Field(None, description="text, table, protocol")
    department: Optional[str] = Field(None, description="Clinical department")
    status: Optional[str] = Field(None, description="Ingestion lifecycle status")
    effective_date: Optional[str] = Field(None, description="Document effective date (YYYY-MM-DD)")


class SearchResponse(BaseModel):
    query: str
    top_k: int
    total_results: int
    results: List[SearchResultItem]


class IndexResponse(BaseModel):
    document_id: int
    document_title: str
    indexed_chunks: int
    collection: str
    status: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Clinical query to be answered from knowledge base")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Override top_k chunks retrieved")
    user_id: Optional[int] = Field(None, description="Optional user ID for audit log tracking")
    user_role: Optional[str] = Field("CLINICAL", description="Role of user: ADMIN, CLINICAL, or OPERATIONS")


class Citation(BaseModel):
    document_id: str = Field(..., description="Document identifier")
    document_title: str = Field(..., description="Document title")
    page: Optional[int] = Field(None, description="Physical page or logical sheet index")
    section: Optional[str] = Field(None, description="Section or header hierarchy")


class ConflictItem(BaseModel):
    source: str = Field(..., description="Source document title")
    version: str = Field(..., description="Document version")
    date: Optional[str] = Field(None, description="Document effective date")
    status: Optional[str] = Field(None, description="Lifecycle status (ACTIVE, SUPERSEDED, RETIRED)")
    claim: str = Field(..., description="Summarized clinical claim or recommendation")
    relevant_passage: str = Field(..., description="Exact relevant textual passage")
    citation: str = Field(..., description="Standard citation format")
    is_active_fresh: bool = Field(False, description="True if marked as the active fresh version")


class AskResponse(BaseModel):
    answer: str = Field(..., description="Clinically grounded answer, conflict disclosure, or refusal")
    evidence_status: str = Field(..., description="'SUFFICIENT', 'INSUFFICIENT', or 'CONFLICTED'")
    user_role: str = Field("CLINICAL", description="Role of the authenticated user")
    access_status: str = Field("GRANTED", description="Access status: GRANTED, FILTERED, or DENIED")
    citations: List[Citation] = Field(default_factory=list, description="Citations supporting factual claims")
    sources: List[SearchResultItem] = Field(default_factory=list, description="Raw retrieved evidence chunks")
    conflicts: List[ConflictItem] = Field(default_factory=list, description="Explicit conflicting evidence items across versions")
    audit_log_id: Optional[int] = Field(None, description="Database audit log primary key")
