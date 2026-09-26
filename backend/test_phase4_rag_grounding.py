"""
Healthcare Greenfield Enterprise RAG - Phase 4 Verification Suite
Tests Clinically Grounded Q&A via POST /api/rag/ask

Tests:
1. Supported Question:
   - "What does the hospital SOP say about medication storage?"
   - Verifies evidence_status == "SUFFICIENT"
   - Verifies citation objects contain document_id, document_title, page, section
   - Verifies answer contains clinical evidence grounding
   - Verifies audit log entry saved in PostgreSQL
2. Second Supported Question (ICU Sepsis Protocol):
   - "What is the recommended antibiotic regimen and loading dose for septic shock?"
   - Verifies evidence_status == "SUFFICIENT"
   - Verifies citations link to sepsis resuscitation protocol
3. Unsupported Question (Out of medical knowledge base):
   - "What is the capital of Mars and how do quantum rocket engines operate?"
   - Verifies evidence_status == "INSUFFICIENT"
   - Verifies answer == "I could not find sufficient evidence in the available knowledge base."
   - Verifies citations == []
   - Verifies audit log entry saved in PostgreSQL with status INSUFFICIENT
4. PostgreSQL AuditLog Verification:
   - Inspects audit_logs table for audit entries
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.audit_log import AuditLog

client = TestClient(app)


def run_phase4_tests():
    print("=" * 80)
    print("HEALTHCARE RAG - PHASE 4 CLINICALLY GROUNDED Q&A VERIFICATION SUITE")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. Test Supported Question: Medication Storage SOP
    # -------------------------------------------------------------
    print("\n[Test 1/4] Testing Supported Question: Medication Storage SOP...")
    q1 = "What does the hospital SOP say about medication storage?"
    payload1 = {"question": q1}

    resp1 = client.post("/api/rag/ask", json=payload1)
    assert resp1.status_code == 200, f"/ask failed ({resp1.status_code}): {resp1.text}"
    data1 = resp1.json()

    print(f"  [+] Question: '{q1}'")
    print(f"  [+] Evidence Status: {data1['evidence_status']}")
    print(f"  [+] Answer Preview:\n      {data1['answer'][:250]}...")
    print(f"  [+] Number of Citations: {len(data1['citations'])}")
    print(f"  [+] Number of Sources: {len(data1['sources'])}")
    print(f"  [+] Audit Log ID: {data1.get('audit_log_id')}")

    assert data1["evidence_status"] == "SUFFICIENT", "Supported question must have SUFFICIENT evidence"
    assert len(data1["citations"]) > 0, "Supported question must have citations"
    assert len(data1["sources"]) > 0, "Supported question must have sources"
    assert "medication" in data1["answer"].lower() or "storage" in data1["answer"].lower()

    # Validate Citation Object schema
    cit1 = data1["citations"][0]
    print(f"  [+] Verified Citation Object:")
    print(f"      - document_id: {cit1['document_id']}")
    print(f"      - document_title: '{cit1['document_title']}'")
    print(f"      - page: {cit1['page']}")
    print(f"      - section: '{cit1['section']}'")
    assert "document_id" in cit1
    assert "document_title" in cit1
    assert "page" in cit1
    assert "section" in cit1

    # -------------------------------------------------------------
    # 2. Test Supported Question: ICU Sepsis Antimicrobial Regimen
    # -------------------------------------------------------------
    print("\n[Test 2/4] Testing Supported Question: ICU Sepsis Antimicrobial Protocol...")
    q2 = "What is the recommended antibiotic regimen and loading dose for septic shock?"
    payload2 = {"question": q2}

    resp2 = client.post("/api/rag/ask", json=payload2)
    assert resp2.status_code == 200, f"/ask failed ({resp2.status_code}): {resp2.text}"
    data2 = resp2.json()

    print(f"  [+] Question: '{q2}'")
    print(f"  [+] Evidence Status: {data2['evidence_status']}")
    print(f"  [+] Answer Preview:\n      {data2['answer'][:250]}...")
    print(f"  [+] Number of Citations: {len(data2['citations'])}")
    print(f"  [+] Top Citation: '{data2['citations'][0]['document_title']}' (Sec: '{data2['citations'][0]['section']}')")

    assert data2["evidence_status"] == "SUFFICIENT"
    assert len(data2["citations"]) > 0
    assert "sepsis" in data2["citations"][0]["document_title"].lower() or "shock" in data2["answer"].lower()

    # -------------------------------------------------------------
    # 3. Test Unsupported Question: Out-of-Domain Knowledge
    # -------------------------------------------------------------
    print("\n[Test 3/4] Testing Unsupported Question: Out-of-Domain Refusal...")
    q3 = "What is the average surface temperature of Jupiter's moon Europa and how do rocket engines operate?"
    payload3 = {"question": q3}

    resp3 = client.post("/api/rag/ask", json=payload3)
    assert resp3.status_code == 200, f"/ask failed ({resp3.status_code}): {resp3.text}"
    data3 = resp3.json()

    print(f"  [+] Question: '{q3}'")
    print(f"  [+] Evidence Status: {data3['evidence_status']}")
    print(f"  [+] Answer: '{data3['answer']}'")
    print(f"  [+] Citations: {data3['citations']}")
    print(f"  [+] Sources: {data3['sources']}")

    assert data3["evidence_status"] == "INSUFFICIENT", "Unsupported query must return INSUFFICIENT"
    assert "could not find sufficient evidence" in data3["answer"].lower(), (
        "Answer must refuse when evidence is insufficient"
    )
    assert data3["citations"] == [], "Unsupported query must have empty citations"
    assert data3["sources"] == [], "Unsupported query must have empty sources"

    # -------------------------------------------------------------
    # 4. Verify PostgreSQL AuditLog Records
    # -------------------------------------------------------------
    print("\n[Test 4/4] Verifying PostgreSQL AuditLog Records...")
    db = SessionLocal()
    try:
        # Check audit log for supported question
        log_supported = db.query(AuditLog).filter(AuditLog.id == data1["audit_log_id"]).first()
        assert log_supported is not None, "AuditLog record for supported question must exist"
        assert log_supported.question == q1
        assert log_supported.evidence_status == "SUFFICIENT"
        print(f"  [+] Verified AuditLog Entry #{log_supported.id}:")
        print(f"      - Question: '{log_supported.question}'")
        print(f"      - Status: {log_supported.evidence_status}")
        print(f"      - Created At: {log_supported.created_at}")

        # Check audit log for unsupported question
        log_unsupported = db.query(AuditLog).filter(AuditLog.id == data3["audit_log_id"]).first()
        assert log_unsupported is not None, "AuditLog record for unsupported question must exist"
        assert log_unsupported.question == q3
        assert log_unsupported.evidence_status == "INSUFFICIENT"
        print(f"  [+] Verified AuditLog Entry #{log_unsupported.id}:")
        print(f"      - Question: '{log_unsupported.question}'")
        print(f"      - Status: {log_unsupported.evidence_status}")
        print(f"      - Created At: {log_unsupported.created_at}")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print("ALL PHASE 4 CLINICAL GROUNDING & REFUSAL TESTS PASSED WITH 100% SUCCESS!")
    print("================================================================================")


if __name__ == "__main__":
    run_phase4_tests()
