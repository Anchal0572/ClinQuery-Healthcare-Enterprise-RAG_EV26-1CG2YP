"""
End-to-End API Verification Script
Tests:
- GET /health
- POST /api/documents
- GET /api/documents
- GET /api/documents/{id}
- POST /api/users
- GET /api/users
- GET /api/users/{id}
- CORS Headers
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def verify_all():
    print("=" * 60)
    print("HEALTHCARE RAG - FULL API VERIFICATION")
    print("=" * 60)

    # 1. Health check
    print("\n[1] Verifying GET /health ...")
    resp = client.get("/health")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.json()}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    print("[+] /health verified: status=ok, database=connected")

    # 2. Create User
    print("\n[2] Verifying POST /api/users ...")
    user_payload = {
        "name": "Dr. Marcus Vance",
        "email": "m.vance.oncology@hospital.internal",
        "role": "oncologist"
    }
    resp = client.post("/api/users", json=user_payload)
    if resp.status_code == 400:
        # If user already exists from previous test run
        print("[*] User already exists, fetching list...")
    else:
        assert resp.status_code == 201
        print(f"[+] User created: {resp.json()}")

    # 3. List Users
    print("\n[3] Verifying GET /api/users ...")
    resp = client.get("/api/users")
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1
    user_id = users[0]["id"]
    print(f"[+] Users retrieved: {len(users)} user(s). Sample: ID={user_id}, Name={users[0]['name']}")

    # 4. Get User by ID
    print(f"\n[4] Verifying GET /api/users/{user_id} ...")
    resp = client.get(f"/api/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id
    print(f"[+] User {user_id} retrieved successfully: {resp.json()['email']}")

    # 5. Create Document with Chunks
    print("\n[5] Verifying POST /api/documents ...")
    doc_payload = {
        "title": "NCCN Clinical Practice Guidelines: Non-Small Cell Lung Cancer",
        "document_type": "clinical_guideline",
        "version": "2024.2",
        "status": "active",
        "department": "Medical Oncology",
        "effective_date": "2024-03-01",
        "chunks": [
            {
                "chunk_text": "Category 1 recommendation: Pembrolizumab plus pemetrexed and platinum-based chemotherapy for first-line treatment of metastatic non-squamous NSCLC with EGFR/ALK negative.",
                "page_number": 42,
                "section": "Principles of Systemic Therapy - First-line NSCLC",
                "chunk_type": "text",
                "qdrant_point_id": "nsclc-guideline-p42-c1"
            },
            {
                "chunk_text": "Dosing: Pembrolizumab 200 mg IV every 3 weeks or 400 mg IV every 6 weeks until disease progression or unacceptable toxicity.",
                "page_number": 43,
                "section": "Dosing & Administration",
                "chunk_type": "text",
                "qdrant_point_id": "nsclc-guideline-p43-c2"
            }
        ]
    }
    resp = client.post("/api/documents", json=doc_payload)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    created_doc = resp.json()
    created_id = created_doc["id"]
    print(f"[+] Document created with ID {created_id}: '{created_doc['title']}' with {len(created_doc['chunks'])} chunks")

    # 6. List Documents
    print("\n[6] Verifying GET /api/documents ...")
    resp = client.get("/api/documents?department=Oncology")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) >= 1
    print(f"[+] Documents retrieved (filtered by Oncology): {len(docs)} document(s)")
    for d in docs:
        print(f"    - ID: {d['id']}, Title: {d['title']}, Chunks: {d['chunk_count']}")

    # 7. Get Document by ID
    print(f"\n[7] Verifying GET /api/documents/{created_id} ...")
    resp = client.get(f"/api/documents/{created_id}")
    assert resp.status_code == 200
    doc_detail = resp.json()
    assert doc_detail["id"] == created_id
    assert len(doc_detail["chunks"]) == 2
    print(f"[+] Document {created_id} retrieved with {len(doc_detail['chunks'])} chunks.")
    print(f"    First chunk section: {doc_detail['chunks'][0]['section']}")
    print(f"    First chunk Qdrant ID: {doc_detail['chunks'][0]['qdrant_point_id']}")

    # 8. CORS Verification
    print("\n[8] Verifying CORS headers ...")
    resp = client.options(
        "/api/documents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    print(f"CORS Options Response: {resp.status_code}")
    print(f"Access-Control-Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    print("[+] CORS properly permits frontend at http://localhost:5173")

    # 9. RAG Status Verification
    print("\n[9] Verifying GET /api/rag/status ...")
    resp = client.get("/api/rag/status")
    assert resp.status_code == 200
    rag_status = resp.json()
    print(f"[+] RAG status: {rag_status['status']} | Qdrant: {rag_status['qdrant']['status']}")
    assert rag_status["qdrant"]["status"] == "connected"

    # 10. RAG Search Verification
    print("\n[10] Verifying POST /api/rag/search ...")
    resp = client.post("/api/rag/search", json={"query": "medication storage temperature SOP", "top_k": 3})
    assert resp.status_code == 200
    search_data = resp.json()
    print(f"[+] RAG search returned {search_data['total_results']} chunks for query: '{search_data['query']}'")

    # 11. RAG Clinically Grounded Ask Verification
    print("\n[11] Verifying POST /api/rag/ask (Supported Question) ...")
    resp = client.post("/api/rag/ask", json={"question": "What does the hospital SOP say about medication storage?"})
    assert resp.status_code == 200
    ask_data = resp.json()
    print(f"[+] RAG ask status: {ask_data['evidence_status']} | Citations: {len(ask_data['citations'])} | Audit ID: {ask_data['audit_log_id']}")
    assert ask_data["evidence_status"] == "SUFFICIENT"
    assert len(ask_data["citations"]) > 0

    # 12. RAG Refusal / Insufficient Evidence Verification
    print("\n[12] Verifying POST /api/rag/ask (Unsupported Question / Refusal) ...")
    resp = client.post("/api/rag/ask", json={"question": "What is the capital of Mars and the speed of light on Neptune?"})
    assert resp.status_code == 200
    unsupported_data = resp.json()
    print(f"[+] Refusal status: {unsupported_data['evidence_status']} | Answer: '{unsupported_data['answer']}'")
    assert unsupported_data["evidence_status"] == "INSUFFICIENT"
    assert "could not find sufficient evidence" in unsupported_data["answer"].lower()

    # 13. RAG Conflict Detection Verification (Phase 5)
    print("\n[13] Verifying POST /api/rag/ask (Conflicted Clinical Protocols) ...")
    resp = client.post("/api/rag/ask", json={"question": "What is the recommended first-line vasopressor and empiric antibiotic for septic shock resuscitation?"})
    assert resp.status_code == 200
    conflict_data = resp.json()
    print(f"[+] Conflict detection status: {conflict_data['evidence_status']} | Conflicts detected: {len(conflict_data.get('conflicts', []))}")
    assert conflict_data["evidence_status"] == "CONFLICTED"
    assert len(conflict_data.get("conflicts", [])) >= 2
    assert any(c.get("is_active_fresh") for c in conflict_data["conflicts"])

    print("\n" + "=" * 60)
    print("ALL API ENDPOINTS (PHASE 1 - 5) VERIFIED & WORKING PERFECTLY!")
    print("=" * 60)


if __name__ == "__main__":
    verify_all()
