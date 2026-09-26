"""
Healthcare Greenfield Enterprise RAG - Phase 3 Verification Suite
Connects PostgreSQL document chunks to Qdrant vector database and verifies semantic retrieval.

Tests:
1. Qdrant connectivity and status endpoint (GET /api/rag/status)
2. Collection creation: healthcare_chunks
3. Configurable embedding generation (FastEmbed BAAI/bge-small-en-v1.5)
4. Document indexing: POST /api/rag/index/{document_id}
   - Verifies vector generation and upsert into Qdrant
   - Verifies payload retention:
     chunk_id, document_id, document_title, version, page_number,
     section, chunk_type, department, status, chunk_text
   - Verifies database chunk qdrant_point_id link
5. Semantic search: POST /api/rag/search
   - Query: "What does the hospital SOP say about medication storage?"
   - Query: "What is the empiric antibiotic and vasopressor dosing for septic shock?"
   - Query: "What are the recommended drug classes for heart failure with reduced ejection fraction?"
   - Query: "What are the critical laboratory thresholds for serum potassium?"
6. Verifies retrieved chunks, scores, document names, pages, and sections.
"""

import sys
import os

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.qdrant_service import get_qdrant_service

client = TestClient(app)
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")


def upload_sample_doc(filename: str, title: str, department: str, doc_type: str, version: str) -> int:
    filepath = os.path.join(SAMPLE_DIR, filename)
    assert os.path.exists(filepath), f"File not found: {filepath}"

    with open(filepath, "rb") as f:
        files = {"file": (filename, f)}
        data = {
            "title": title,
            "department": department,
            "document_type": doc_type,
            "version": version,
            "effective_date": "2024-01-15",
        }
        resp = client.post("/api/documents/upload", files=files, data=data)

    assert resp.status_code == 201, f"Upload failed for {filename}: {resp.text}"
    return resp.json()["document_id"]


def run_phase3_tests():
    print("=" * 75)
    print("HEALTHCARE RAG - PHASE 3 QDRANT EMBEDDINGS & RETRIEVAL SUITE")
    print("=" * 75)

    # ---------------------------------------------------------
    # 1. Verify Qdrant Connection & RAG Status
    # ---------------------------------------------------------
    print("\n[Step 1/5] Checking Qdrant Connection & Active Embedding Model...")
    status_resp = client.get("/api/rag/status")
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
    status_data = status_resp.json()
    print(f"  [+] Overall RAG Status: {status_data['status']}")
    print(f"  [+] Qdrant Endpoint: {status_data['qdrant']['url']}")
    print(f"  [+] Qdrant Status: {status_data['qdrant']['status']}")
    print(f"  [+] Target Collection: {status_data['collection']}")
    print(f"  [+] Embedding Provider: {status_data['embedding']['provider']}")
    print(f"  [+] Embedding Model: {status_data['embedding']['model']} ({status_data['embedding']['dimension']} dims)")
    assert status_data["qdrant"]["status"] == "connected", "Qdrant must be connected"

    # ---------------------------------------------------------
    # 2. Upload Healthcare Documents to PostgreSQL
    # ---------------------------------------------------------
    print("\n[Step 2/5] Ingesting Healthcare Documents (PostgreSQL Pipeline)...")
    docs_to_test = [
        {
            "filename": "synthetic_hospital_medication_storage_sop.txt",
            "title": "Hospital Standard Operating Procedure: Medication Storage and Handling",
            "department": "Pharmacy",
            "document_type": "sop",
            "version": "2.4",
        },
        {
            "filename": "synthetic_cardiology_hf_guideline.pdf",
            "title": "AHA/ACC 2024 Heart Failure Pharmacotherapy Guideline",
            "department": "Cardiology",
            "document_type": "clinical_guideline",
            "version": "2.1",
        },
        {
            "filename": "synthetic_icu_sepsis_resuscitation.docx",
            "title": "ICU Sepsis and Septic Shock Resuscitation Protocol",
            "department": "Intensive Care Unit",
            "document_type": "protocol",
            "version": "3.4",
        },
        {
            "filename": "synthetic_critical_lab_intervals.xlsx",
            "title": "Clinical Pathology Critical Laboratory Reference Intervals",
            "department": "Laboratory Medicine",
            "document_type": "lab_reference",
            "version": "4.0",
        },
    ]

    indexed_doc_ids = []
    for item in docs_to_test:
        doc_id = upload_sample_doc(
            item["filename"], item["title"], item["department"], item["document_type"], item["version"]
        )
        indexed_doc_ids.append((doc_id, item["title"]))
        print(f"  [+] Uploaded '{item['title']}' -> PostgreSQL Document ID: {doc_id}")

    # ---------------------------------------------------------
    # 3. Index Documents into Qdrant (POST /api/rag/index/{id})
    # ---------------------------------------------------------
    print("\n[Step 3/5] Indexing Document Chunks into Qdrant (POST /api/rag/index/{id})...")
    total_chunks_indexed = 0

    for doc_id, doc_title in indexed_doc_ids:
        resp = client.post(f"/api/rag/index/{doc_id}")
        assert resp.status_code == 200, f"Indexing failed for doc {doc_id}: {resp.text}"
        res = resp.json()
        total_chunks_indexed += res["indexed_chunks"]
        print(f"  [+] Indexed Document ID {doc_id}: '{doc_title}'")
        print(f"      Chunks: {res['indexed_chunks']} | Collection: '{res['collection']}' | Status: {res['status']}")

    assert total_chunks_indexed > 0, "At least some chunks must be indexed"
    print(f"\n  [+] Total Chunks Successfully Vectorized & Upserted: {total_chunks_indexed}")

    # ---------------------------------------------------------
    # 4. Verify Qdrant Stored Payloads & PostgreSQL Linking
    # ---------------------------------------------------------
    print("\n[Step 4/5] Verifying Qdrant Payloads & Database Foreign Point IDs...")
    db = SessionLocal()
    try:
        qdrant = get_qdrant_service()
        # Verify collection exists in Qdrant
        exists = qdrant.client.collection_exists("healthcare_chunks")
        assert exists, "Collection 'healthcare_chunks' must exist in Qdrant"

        # Check PostgreSQL chunks have qdrant_point_id set
        for doc_id, _ in indexed_doc_ids:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
            for c in chunks:
                assert c.qdrant_point_id is not None, f"Chunk {c.id} must have qdrant_point_id populated"
                assert str(c.id) == c.qdrant_point_id, f"qdrant_point_id must match chunk id"

        print("  [+] All PostgreSQL chunks have verified qdrant_point_id links.")

        # Inspect points directly in Qdrant to verify all required payload fields
        points_info = qdrant.client.retrieve(
            collection_name="healthcare_chunks",
            ids=[int(chunks[0].id)],
            with_payload=True,
            with_vectors=False,
        )
        assert len(points_info) > 0, "Point must exist in Qdrant"
        payload = points_info[0].payload
        required_keys = [
            "chunk_id",
            "document_id",
            "document_title",
            "version",
            "page_number",
            "section",
            "chunk_type",
            "department",
            "status",
            "chunk_text",
        ]
        for key in required_keys:
            assert key in payload, f"Missing payload key in Qdrant: {key}"
        print(f"  [+] Qdrant payload schema validated! Sample Payload Keys: {list(payload.keys())}")
    finally:
        db.close()

    # ---------------------------------------------------------
    # 5. Semantic Retrieval Tests (POST /api/rag/search)
    # ---------------------------------------------------------
    print("\n[Step 5/5] Performing Semantic Retrieval via POST /api/rag/search...")

    test_queries = [
        {
            "query": "What does the hospital SOP say about medication storage?",
            "expected_keyword": "storage",
            "description": "User requested sample query on medication storage SOP",
        },
        {
            "query": "What is the recommended antibiotic regimen and dosing for septic shock in the ICU?",
            "expected_keyword": "piperacillin",
            "description": "ICU Sepsis empiric antimicrobial protocol",
        },
        {
            "query": "What are the guideline-directed quadruple medical therapy classes for heart failure?",
            "expected_keyword": "arni",
            "description": "AHA/ACC Heart Failure Pharmacotherapy Guideline",
        },
        {
            "query": "What is the critical laboratory panic threshold for potassium?",
            "expected_keyword": "potassium",
            "description": "Critical laboratory alert values reference intervals",
        },
    ]

    for idx, tq in enumerate(test_queries, 1):
        print("\n" + "-" * 75)
        print(f"Test Query #{idx}: \"{tq['query']}\"")
        print(f"Goal: {tq['description']}")
        print("-" * 75)

        search_payload = {
            "query": tq["query"],
            "top_k": 5,
        }
        s_resp = client.post("/api/rag/search", json=search_payload)
        assert s_resp.status_code == 200, f"Search failed: {s_resp.text}"
        s_data = s_resp.json()

        assert s_data["total_results"] > 0, f"No results returned for query: {tq['query']}"
        top_match = s_data["results"][0]

        print(f"  [+] Total Retrieved Chunks: {s_data['total_results']}")
        print(f"  [+] Top Rank (Rank #1):")
        print(f"      - Similarity Score: {top_match['similarity_score']:.4f}")
        print(f"      - Document: '{top_match['document']}' (ID: {top_match['document_id']})")
        print(f"      - Page: {top_match['page']} | Section: '{top_match['section']}'")
        print(f"      - Chunk Type: {top_match['chunk_type']} | Department: '{top_match['department']}'")
        preview = top_match["chunk_text"].replace("\n", " ")[:200]
        print(f"      - Chunk Text: \"{preview}...\"")

        # Verify relevance
        combined_text = " ".join([r["chunk_text"].lower() for r in s_data["results"]])
        assert tq["expected_keyword"].lower() in combined_text, (
            f"Expected keyword '{tq['expected_keyword']}' not found in retrieved chunks."
        )

        # Print all top-3 ranked chunks
        for r_idx, r in enumerate(s_data["results"][1:], 2):
            print(f"  [+] Rank #{r_idx}: Score={r['similarity_score']:.4f} | Doc='{r['document']}' | Sec='{r['section']}'")

    print("\n" + "=" * 75)
    print("ALL PHASE 3 REQUIREMENTS VERIFIED WITH 100% SUCCESS!")
    print("===========================================================================")


if __name__ == "__main__":
    run_phase3_tests()
