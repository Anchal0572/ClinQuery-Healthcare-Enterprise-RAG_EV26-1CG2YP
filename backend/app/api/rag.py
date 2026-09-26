import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.models.document import Document, DocumentChunk
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.rag import (
    SearchRequest,
    SearchResponse,
    IndexResponse,
    SearchResultItem,
    AskRequest,
    AskResponse,
    Citation,
    ConflictItem,
)
from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.services.llm_service import get_llm_service
from app.services.conflict_service import get_conflict_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/status", summary="Check RAG services status (Qdrant & Embeddings)")
def get_rag_status():
    """
    Check Qdrant vector database connectivity and active embedding configuration.
    """
    settings = get_settings()
    qdrant = get_qdrant_service()
    embedder = get_embedding_service()

    qdrant_conn = qdrant.check_connection()

    return {
        "status": "ok" if qdrant_conn["status"] == "connected" else "degraded",
        "qdrant": qdrant_conn,
        "collection": settings.qdrant_collection,
        "embedding": {
            "provider": embedder.provider,
            "model": embedder.model_name,
            "dimension": embedder.get_dimension(),
        },
    }


@router.post(
    "/index/{document_id}",
    response_model=IndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index document chunks into Qdrant",
)
def index_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves chunks for a document from PostgreSQL, generates dense vector embeddings,
    and inserts them into the Qdrant vector database with clinical metadata payload.
    """
    settings = get_settings()
    embedder = get_embedding_service()
    qdrant = get_qdrant_service()

    # 1. Fetch document from PostgreSQL
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.id.asc())
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document '{doc.title}' (ID {document_id}) has no chunks to index.",
        )

    # 2. Ensure Qdrant collection exists
    vector_dim = embedder.get_dimension()
    try:
        qdrant.ensure_collection(
            collection_name=settings.qdrant_collection,
            vector_size=vector_dim,
        )
    except Exception as e:
        logger.error(f"Failed to ensure Qdrant collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {e}",
        )

    # 3. Generate embeddings for all chunks
    chunk_texts = [c.chunk_text for c in chunks]
    try:
        vectors = embedder.embed_texts(chunk_texts)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {e}",
        )

    # 4. Prepare Qdrant points with complete metadata payload
    chunks_data = []
    for chunk, vector in zip(chunks, vectors):
        point_id = int(chunk.id)
        payload = {
            "chunk_id": int(chunk.id),
            "document_id": int(doc.id),
            "document_title": doc.title,
            "version": str(chunk.document_version or doc.version or "1.0"),
            "page_number": chunk.page_number,
            "section": chunk.section or "",
            "chunk_type": chunk.chunk_type,
            "department": doc.department or "",
            "status": doc.status,
            "effective_date": str(doc.effective_date) if doc.effective_date else "",
            "chunk_text": chunk.chunk_text,
            "allowed_roles": doc.allowed_roles or "ADMIN,CLINICAL",
        }
        chunks_data.append({
            "point_id": point_id,
            "vector": vector,
            "payload": payload,
        })

        # Record point id reference in database chunk
        chunk.qdrant_point_id = str(point_id)

    # 5. Upsert to Qdrant
    try:
        qdrant.upsert_chunks(
            chunks_data=chunks_data,
            collection_name=settings.qdrant_collection,
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upsert vectors into Qdrant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index chunks into Qdrant: {e}",
        )

    logger.info(
        f"Indexed {len(chunks_data)} chunks for document '{doc.title}' (ID {doc.id}) into Qdrant."
    )

    return IndexResponse(
        document_id=doc.id,
        document_title=doc.title,
        indexed_chunks=len(chunks_data),
        collection=settings.qdrant_collection,
        status="indexed",
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic vector search across indexed healthcare chunks",
)
def search_chunks(request: SearchRequest):
    """
    Embeds the user query, queries Qdrant for top-k similar chunks,
    and returns chunk text, similarity score, document title, page, and section.
    """
    settings = get_settings()
    embedder = get_embedding_service()
    qdrant = get_qdrant_service()

    # 1. Embed user query
    try:
        query_vector = embedder.embed_text(request.query)
    except Exception as e:
        logger.error(f"Failed to embed search query '{request.query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query embedding generation failed: {e}",
        )

    # 2. Search Qdrant
    try:
        raw_results = qdrant.search(
            query_vector=query_vector,
            top_k=request.top_k,
            collection_name=settings.qdrant_collection,
            department=request.department,
        )
    except Exception as e:
        logger.error(f"Qdrant vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector search service error: {e}",
        )

    formatted_results: List[SearchResultItem] = [
        SearchResultItem(
            chunk_id=item["chunk_id"],
            similarity_score=item["similarity_score"],
            chunk_text=item["chunk_text"],
            document=item["document"],
            document_id=item["document_id"],
            version=item["version"],
            page=item["page"],
            section=item["section"],
            chunk_type=item["chunk_type"],
            department=item["department"],
            status=item["status"],
        )
        for item in raw_results
    ]

    return SearchResponse(
        query=request.query,
        top_k=request.top_k,
        total_results=len(formatted_results),
        results=formatted_results,
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Clinically grounded RAG Q&A with citations and audit logging",
)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    """
    Executes grounded clinical question-answering:
    1. Embeds question and retrieves top matching chunks from Qdrant.
    2. Evaluates evidence against the configurable similarity threshold.
    3. If below threshold: returns refusal with 'INSUFFICIENT' status.
    4. If above threshold: instructs LLM to answer strictly from retrieved evidence with citations.
    5. Saves the audit log record in PostgreSQL.
    """
    settings = get_settings()
    embedder = get_embedding_service()
    qdrant = get_qdrant_service()
    llm = get_llm_service()
    conflict_service = get_conflict_service()

    top_k = request.top_k or settings.rag_top_k
    threshold = settings.rag_similarity_threshold

    # 1. Determine user role and query accessible document IDs from PostgreSQL
    user_role = (request.user_role or "CLINICAL").strip().upper()
    if user_role not in ["ADMIN", "CLINICAL", "OPERATIONS"]:
        user_role = "CLINICAL"

    # Pre-retrieval access control: Filter accessible documents by allowed_roles
    if user_role == "ADMIN":
        accessible_docs = db.query(Document.id).all()
    else:
        accessible_docs = (
            db.query(Document.id)
            .filter(Document.allowed_roles.ilike(f"%{user_role}%"))
            .all()
        )
    accessible_doc_ids = [d[0] for d in accessible_docs]

    # 2. Retrieve top chunks from Qdrant strictly restricted to accessible documents
    try:
        query_vector = embedder.embed_text(request.question)
        raw_results = qdrant.search(
            query_vector=query_vector,
            top_k=top_k,
            collection_name=settings.qdrant_collection,
            allowed_document_ids=accessible_doc_ids,
        )
    except Exception as e:
        logger.error(f"Vector search failed during /ask: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Retrieval engine error: {e}",
        )

    # 3. Check insufficient-evidence or role-filtered condition
    access_status = "GRANTED"
    if not raw_results or raw_results[0]["similarity_score"] < threshold:
        # Check if an unrestricted search would have found matching clinical documents
        try:
            unrestricted_results = qdrant.search(
                query_vector=query_vector,
                top_k=1,
                collection_name=settings.qdrant_collection,
                allowed_document_ids=None,
            )
        except Exception:
            unrestricted_results = []

        if unrestricted_results and unrestricted_results[0]["similarity_score"] >= threshold and user_role != "ADMIN":
            access_status = "FILTERED"
            answer = f"Access Restricted: Your current role ({user_role}) does not have permission to view protected clinical documents matching this query."
            evidence_status = "INSUFFICIENT"
        else:
            access_status = "GRANTED" if user_role in ["ADMIN", "CLINICAL"] else "FILTERED"
            answer = "I could not find sufficient evidence in the available knowledge base."
            evidence_status = "INSUFFICIENT"

        citations = []
        sources = []
        conflicts = []
    else:
        access_status = "GRANTED"
        # Filter chunks that meet the relevance threshold
        qualifying_chunks = [c for c in raw_results if c["similarity_score"] >= threshold]

        # 4. Check for clinical conflict across document versions
        conflict_res = conflict_service.detect_conflicts(request.question, qualifying_chunks)

        if conflict_res and conflict_res["is_conflicted"]:
            evidence_status = "CONFLICTED"
            answer = conflict_res["answer"]
            conflicts = [ConflictItem(**item) for item in conflict_res["conflicts"]]
            # Provide full citations for both conflicting sources
            seen_cits = set()
            citations = []
            for c in qualifying_chunks:
                doc_id = str(c.get("document_id", ""))
                doc_title = c.get("document") or c.get("document_title", "Clinical Document")
                page = c.get("page")
                section = c.get("section")
                k = (doc_id, doc_title, page, section)
                if k not in seen_cits:
                    seen_cits.add(k)
                    citations.append(
                        Citation(
                            document_id=doc_id,
                            document_title=doc_title,
                            page=page,
                            section=section,
                        )
                    )
        else:
            # 5. Standard Grounded LLM generation
            grounded_res = llm.generate_grounded_answer(request.question, qualifying_chunks)
            answer = grounded_res["answer"]
            evidence_status = grounded_res.get("evidence_status", "SUFFICIENT")
            conflicts = []

            citations = [
                Citation(
                    document_id=str(c.get("document_id", "")),
                    document_title=c.get("document_title", "Clinical Document"),
                    page=c.get("page"),
                    section=c.get("section"),
                )
                for c in grounded_res.get("citations", [])
            ]

        sources = [
            SearchResultItem(
                chunk_id=item["chunk_id"],
                similarity_score=item["similarity_score"],
                chunk_text=item["chunk_text"],
                document=item["document"],
                document_id=item["document_id"],
                version=item["version"],
                page=item["page"],
                section=item["section"],
                chunk_type=item["chunk_type"],
                department=item["department"],
                status=item["status"],
                effective_date=item.get("effective_date"),
            )
            for item in qualifying_chunks
        ]

    # 6. Save question, user role, access status, and result to AuditLog
    valid_user_id = None
    if request.user_id:
        existing_user = db.query(User).filter(User.id == request.user_id).first()
        if existing_user:
            valid_user_id = existing_user.id

    audit_entry = AuditLog(
        user_id=valid_user_id,
        user_role=user_role,
        access_status=access_status,
        question=request.question,
        answer=answer,
        evidence_status=evidence_status,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    logger.info(
        f"Processed query '{request.question[:60]}...' [Role: {user_role}, Access: {access_status}] -> Status: {evidence_status} (AuditLog ID: {audit_entry.id})"
    )

    return AskResponse(
        answer=answer,
        evidence_status=evidence_status,
        user_role=user_role,
        access_status=access_status,
        citations=citations,
        sources=sources,
        conflicts=conflicts,
        audit_log_id=audit_entry.id,
    )
