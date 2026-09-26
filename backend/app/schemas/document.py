from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Document Chunk Schemas ---

class DocumentChunkBase(BaseModel):
    chunk_text: str
    document_version: Optional[str] = "1.0"
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_type: str = "text"  # text, table, protocol_standard, summary
    qdrant_point_id: Optional[str] = None


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Document Schemas ---

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(..., min_length=1, max_length=100)  # clinical_guideline, drug_monograph, protocol
    version: str = "1.0"
    status: str = "COMPLETED"  # UPLOADING, PROCESSING, COMPLETED, FAILED
    department: Optional[str] = None
    effective_date: Optional[date] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    allowed_roles: str = "ADMIN,CLINICAL"


class DocumentCreate(DocumentBase):
    chunks: Optional[List[DocumentChunkCreate]] = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    effective_date: Optional[date] = None
    error_message: Optional[str] = None
    allowed_roles: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentBase):
    id: int
    created_at: datetime
    chunks: List[DocumentChunkResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document_id: int
    title: str
    status: str
    document_type: str
    version: str
    department: Optional[str] = None
    chunks_created: int
    extracted_sections: List[str] = []
    message: str = "Document successfully uploaded, parsed, and chunked."
