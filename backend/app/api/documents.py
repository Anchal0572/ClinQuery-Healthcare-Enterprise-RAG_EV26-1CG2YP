import os
import logging
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.document import Document, DocumentChunk, IngestionStatus
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUploadResponse,
    DocumentChunkCreate,
    DocumentChunkResponse,
)
from app.services.document_parser import DocumentParserService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads")
os.makedirs(UPLOAD_STORAGE_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload and chunk clinical document")
async def upload_document(
    file: UploadFile = File(..., description="Healthcare file (PDF, DOCX, TXT, CSV, XLSX)"),
    title: Optional[str] = Form(None, description="Optional clinical document title"),
    document_type: Optional[str] = Form("clinical_guideline", description="Document type (e.g. guideline, protocol, monograph, lab)"),
    version: Optional[str] = Form("1.0", description="Document version"),
    department: Optional[str] = Form(None, description="Clinical department (e.g. Oncology, Cardiology)"),
    effective_date: Optional[str] = Form(None, description="Effective date (YYYY-MM-DD)"),
    status: Optional[str] = Form(None, description="Document lifecycle status: ACTIVE, SUPERSEDED, or RETIRED"),
    allowed_roles: Optional[str] = Form("ADMIN,CLINICAL", description="Comma-separated allowed roles: ADMIN, CLINICAL, OPERATIONS"),
    db: Session = Depends(get_db),
):
    """
    Uploads a synthetic/de-identified healthcare document, parses text, sections,
    pages, and tables (preserving table name, row, column, value), and persists chunks in PostgreSQL.
    Status transitions: UPLOADING -> PROCESSING -> COMPLETED (or FAILED).
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty")

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in DocumentParserService.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Supported: {', '.join(DocumentParserService.SUPPORTED_EXTENSIONS)}"
        )

    # 1. Parse effective date if provided
    parsed_date = None
    if effective_date:
        try:
            parsed_date = date.fromisoformat(effective_date)
        except ValueError:
            pass

    doc_title = title.strip() if title and title.strip() else os.path.splitext(file.filename)[0]

    # 2. Read file content
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 3. Save physical file copy for records
    safe_filename = f"{int(date.today().strftime('%Y%m%d'))}_{file.filename}"
    saved_path = os.path.join(UPLOAD_STORAGE_DIR, safe_filename)
    try:
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        logger.warning(f"Could not persist upload to disk: {e}")
        saved_path = None

    # 4. Create Document in PostgreSQL with status=UPLOADING
    new_doc = Document(
        title=doc_title,
        document_type=document_type,
        version=version or "1.0",
        status=IngestionStatus.UPLOADING,
        department=department,
        effective_date=parsed_date,
        file_path=saved_path,
        file_size_bytes=file_size,
        allowed_roles=allowed_roles.strip().upper() if allowed_roles else "ADMIN,CLINICAL",
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 5. Parse and chunk document (status -> PROCESSING)
    try:
        new_doc.status = IngestionStatus.PROCESSING
        db.commit()

        parser = DocumentParserService(target_chunk_size=700, overlap=100)
        parsed_chunks = parser.parse_file(file_bytes, file.filename)

        if not parsed_chunks:
            raise ValueError("No parseable text or table content found in the uploaded file.")

        distinct_sections = set()

        # 6. Save DocumentChunk records in PostgreSQL
        # Each chunk retains: document_id, document_version, page_number, section, chunk_type, chunk_text
        for idx, chunk in enumerate(parsed_chunks):
            distinct_sections.add(chunk.section or "General")
            db_chunk = DocumentChunk(
                document_id=new_doc.id,
                document_version=new_doc.version,
                page_number=chunk.page_number,
                section=chunk.section,
                chunk_type=chunk.chunk_type,
                chunk_text=chunk.chunk_text,
                qdrant_point_id=f"doc-{new_doc.id}-p{chunk.page_number or 1}-c{idx+1}",
            )
            db.add(db_chunk)

        # 7. Update status -> ACTIVE/SUPERSEDED/RETIRED if specified, else COMPLETED
        if status and status.upper() in ["ACTIVE", "SUPERSEDED", "RETIRED"]:
            new_doc.status = status.upper()
        else:
            new_doc.status = IngestionStatus.COMPLETED
        db.commit()
        db.refresh(new_doc)

        logger.info(
            f"Successfully ingested document '{new_doc.title}' (ID: {new_doc.id}): "
            f"{len(parsed_chunks)} chunks created across {len(distinct_sections)} sections."
        )

        return DocumentUploadResponse(
            document_id=new_doc.id,
            title=new_doc.title,
            status=new_doc.status,
            document_type=new_doc.document_type,
            version=new_doc.version,
            department=new_doc.department,
            chunks_created=len(parsed_chunks),
            extracted_sections=sorted(list(distinct_sections)),
            message=f"Document successfully parsed and converted into {len(parsed_chunks)} searchable chunks.",
        )

    except Exception as e:
        db.rollback()
        new_doc.status = IngestionStatus.FAILED
        new_doc.error_message = str(e)
        db.commit()
        logger.error(f"Failed parsing document ID {new_doc.id} ({file.filename}): {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse and chunk document: {str(e)}"
        )


@router.post("", response_model=DocumentDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a new document")
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    """
    Ingest a new healthcare document (e.g. Clinical Guideline, Drug Monograph, Protocol).
    Optionally include initial chunks.
    """
    try:
        new_doc = Document(
            title=payload.title,
            document_type=payload.document_type,
            version=payload.version,
            status=payload.status,
            department=payload.department,
            effective_date=payload.effective_date,
        )
        db.add(new_doc)
        db.flush()  # populate new_doc.id

        if payload.chunks:
            for chunk in payload.chunks:
                db_chunk = DocumentChunk(
                    document_id=new_doc.id,
                    chunk_text=chunk.chunk_text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    chunk_type=chunk.chunk_type,
                    qdrant_point_id=chunk.qdrant_point_id,
                )
                db.add(db_chunk)

        db.commit()
        db.refresh(new_doc)
        logger.info(f"Created document '{new_doc.title}' (ID: {new_doc.id}) with {len(new_doc.chunks)} chunks")
        return new_doc
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse], summary="List documents")
def list_documents(
    department: Optional[str] = Query(None, description="Filter by clinical department"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    doc_status: Optional[str] = Query(None, alias="status", description="Filter by status (active, draft, archived)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List healthcare documents with optional filtering and chunk counts.
    """
    query = db.query(
        Document,
        func.count(DocumentChunk.id).label("chunk_count")
    ).outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)

    if department:
        query = query.filter(Document.department.ilike(f"%{department}%"))
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if doc_status:
        query = query.filter(Document.status == doc_status)

    query = query.group_by(Document.id).order_by(Document.created_at.desc()).offset(skip).limit(limit)

    results = []
    for doc, count in query.all():
        doc_data = DocumentResponse(
            id=doc.id,
            title=doc.title,
            document_type=doc.document_type,
            version=doc.version,
            status=doc.status,
            department=doc.department,
            effective_date=doc.effective_date,
            created_at=doc.created_at,
            chunk_count=count,
        )
        results.append(doc_data)

    return results


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document by ID")
def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full document metadata along with all associated chunks.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return doc


@router.post("/{document_id}/chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED, summary="Add chunk to document")
def add_chunk(document_id: int, payload: DocumentChunkCreate, db: Session = Depends(get_db)):
    """
    Add a text chunk directly to an existing document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_text=payload.chunk_text,
        page_number=payload.page_number,
        section=payload.section,
        chunk_type=payload.chunk_type,
        qdrant_point_id=payload.qdrant_point_id,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a document")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and all cascading chunks.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    db.delete(doc)
    db.commit()
    return None
