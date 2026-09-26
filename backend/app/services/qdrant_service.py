import logging
import re
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

_qdrant_client_instance: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Lazy singleton connection manager for Qdrant client.
    """
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        settings = get_settings()
        logger.info(f"Connecting to Qdrant at {settings.qdrant_url}...")
        _qdrant_client_instance = QdrantClient(url=settings.qdrant_url, timeout=10.0)
    return _qdrant_client_instance


class QdrantService:
    """
    Qdrant vector operations service for healthcare chunk indexing and retrieval.
    """

    def __init__(self, client: Optional[QdrantClient] = None):
        self.client = client or get_qdrant_client()
        self.settings = get_settings()

    def check_connection(self) -> Dict[str, Any]:
        """
        Verify that Qdrant is accessible and healthy.
        """
        try:
            collections_res = self.client.get_collections()
            collection_names = [c.name for c in collections_res.collections]
            return {
                "status": "connected",
                "url": self.settings.qdrant_url,
                "collections": collection_names,
            }
        except Exception as e:
            logger.error(f"Qdrant connection health check failed: {e}")
            return {
                "status": "disconnected",
                "url": self.settings.qdrant_url,
                "error": str(e),
            }

    def ensure_collection(
        self,
        collection_name: Optional[str] = None,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """
        Ensure that the specified collection exists in Qdrant; if not, create it.
        """
        name = collection_name or self.settings.qdrant_collection
        try:
            exists = self.client.collection_exists(collection_name=name)
            if not exists:
                logger.info(f"Creating Qdrant collection '{name}' with vector size {vector_size}...")
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                )
                logger.info(f"Collection '{name}' created successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection '{name}': {e}")
            raise

    def upsert_chunks(
        self,
        chunks_data: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Batch upsert chunks into Qdrant.
        Each item in chunks_data must have:
        - 'point_id': int or str (UUID)
        - 'vector': List[float]
        - 'payload': Dict with chunk_id, document_id, document_title, version,
                     page_number, section, chunk_type, department, status, chunk_text
        """
        if not chunks_data:
            return 0

        name = collection_name or self.settings.qdrant_collection
        points = [
            PointStruct(
                id=item["point_id"],
                vector=item["vector"],
                payload=item["payload"],
            )
            for item in chunks_data
        ]

        self.client.upsert(
            collection_name=name,
            points=points,
            wait=True,
        )
        logger.info(f"Successfully upserted {len(points)} points into Qdrant collection '{name}'.")
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        collection_name: Optional[str] = None,
        department: Optional[str] = None,
        allowed_document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for most similar chunks using cosine similarity vector search.
        If allowed_document_ids is provided, restricts search strictly to authorized documents.
        """
        if allowed_document_ids is not None and len(allowed_document_ids) == 0:
            # User has no accessible documents; immediately return empty to prevent data leakage
            logger.info("Access control: 0 allowed document IDs; returning empty retrieval.")
            return []

        name = collection_name or self.settings.qdrant_collection
        must_conditions = []

        if department:
            must_conditions.append(
                FieldCondition(
                    key="department",
                    match=MatchValue(value=department),
                )
            )

        if allowed_document_ids is not None:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=allowed_document_ids),
                )
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        # Use query_points (qdrant-client >= 1.10) with fallback to search
        # Fetch wider candidate pool so identical chunks across duplicate document uploads don't crowd out diverse evidence
        fetch_limit = max(top_k * 3, 12)
        try:
            response = self.client.query_points(
                collection_name=name,
                query=query_vector,
                limit=fetch_limit,
                query_filter=query_filter,
                with_payload=True,
            )
            hits = response.points
        except (AttributeError, Exception):
            hits = self.client.search(
                collection_name=name,
                query_vector=query_vector,
                limit=fetch_limit,
                query_filter=query_filter,
                with_payload=True,
            )

        results = []
        seen_texts = set()
        for hit in hits:
            payload = hit.payload or {}
            doc_id = payload.get("document_id")

            # Defense-in-depth safety check: Ensure chunk's document_id is authorized
            if allowed_document_ids is not None and doc_id not in allowed_document_ids:
                logger.warning(f"Unauthorized chunk {payload.get('chunk_id')} for doc {doc_id} blocked.")
                continue

            chunk_text = payload.get("chunk_text", "")
            # Deduplicate identical chunks from redundant document re-uploads while preserving version conflicts
            doc_key = f"{payload.get('document_title')}_{payload.get('version')}_{payload.get('page_number')}_{payload.get('section')}"
            if doc_key in seen_texts:
                continue
            seen_texts.add(doc_key)

            results.append({
                "chunk_id": payload.get("chunk_id"),
                "similarity_score": round(float(hit.score), 4),
                "chunk_text": chunk_text,
                "document": payload.get("document_title", ""),
                "document_id": doc_id,
                "version": payload.get("version"),
                "page": payload.get("page_number"),
                "section": payload.get("section"),
                "chunk_type": payload.get("chunk_type"),
                "department": payload.get("department"),
                "status": payload.get("status"),
                "effective_date": payload.get("effective_date"),
                "allowed_roles": payload.get("allowed_roles"),
            })

            if len(results) >= top_k:
                break

        return results


_qdrant_service_instance: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    global _qdrant_service_instance
    if _qdrant_service_instance is None:
        _qdrant_service_instance = QdrantService()
    return _qdrant_service_instance
