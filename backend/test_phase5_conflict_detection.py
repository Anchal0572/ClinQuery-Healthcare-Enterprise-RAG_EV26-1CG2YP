"""
Healthcare Greenfield Enterprise RAG - Phase 5 Verification Suite
Conflict Detection & Multi-Version Clinical Safety

Tests:
1. Ingesting two synthetic clinical protocols with contradictory guidance:
   - Version 1.0 (SUPERSEDED, 2021-03-10): Recommends Dopamine as primary first-line vasopressor, Ceftriaxone within 3 hours.
   - Version 2.0 (ACTIVE, 2024-05-20): Dopamine strictly CONTRAINDICATED; Norepinephrine is mandatory first-line; Piperacillin-Tazobactam within 1 hour.
2. Indexing both versions into Qdrant vector database.
3. Querying the conflicting topic via POST /api/rag/ask.
4. Verifying:
   - evidence_status == "CONFLICTED"
   - Does NOT silently choose between conflicting sources
   - Does NOT hide conflicting evidence
   - Shows source, version, date, and relevant passage for each conflicting version
   - Demonstrates freshness preference (identifies ACTIVE current version 2.0)
   - Saves record in PostgreSQL AuditLog with status "CONFLICTED"
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.audit_log import AuditLog

client = TestClient(app)
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")


def upload_and_index_doc(filename: str, title: str, version: str, status_val: str, date_val: str) -> int:
    filepath = os.path.join(SAMPLE_DIR, filename)
    assert os.path.exists(filepath), f"File not found: {filepath}"

    with open(filepath, "rb") as f:
        files = {"file": (filename, f)}
        data = {
            "title": title,
            "department": "Critical Care / ICU",
            "document_type": "protocol",
            "version": version,
            "effective_date": date_val,
            "status": status_val,
        }
        resp = client.post("/api/documents/upload", files=files, data=data)

    assert resp.status_code == 201, f"Upload failed for {filename}: {resp.text}"
    doc_id = resp.json()["document_id"]

    # Index into Qdrant
    idx_resp = client.post(f"/api/rag/index/{doc_id}")
    assert idx_resp.status_code == 200, f"Indexing failed for doc {doc_id}: {idx_resp.text}"
    return doc_id


def run_phase5_tests():
    print("=" * 80)
    print("HEALTHCARE RAG - PHASE 5 CONFLICT DETECTION & VERSION SAFETY SUITE")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. Ingest Conflicting Protocol Versions
    # -------------------------------------------------------------
    print("\n[Step 1/4] Ingesting & Indexing Conflicting Clinical Protocol Versions...")

    # Version 1.0 (SUPERSEDED)
    v1_id = upload_and_index_doc(
        filename="synthetic_conflicting_sepsis_protocol_v1_superseded.txt",
        title="Hospital Clinical Practice Protocol: Sepsis Resuscitation & Antimicrobial Therapy",
        version="1.0",
        status_val="SUPERSEDED",
        date_val="2021-03-10",
    )
    print(f"  [+] Ingested & Indexed Version 1.0 (SUPERSEDED): Doc ID={v1_id}")

    # Version 2.0 (ACTIVE)
    v2_id = upload_and_index_doc(
        filename="synthetic_conflicting_sepsis_protocol_v2_active.txt",
        title="Hospital Clinical Practice Protocol: Sepsis Resuscitation & Antimicrobial Therapy",
        version="2.0",
        status_val="ACTIVE",
        date_val="2024-05-20",
    )
    print(f"  [+] Ingested & Indexed Version 2.0 (ACTIVE): Doc ID={v2_id}")

    # -------------------------------------------------------------
    # 2. Query Conflicting Clinical Topic via POST /api/rag/ask
    # -------------------------------------------------------------
    print("\n[Step 2/4] Querying Conflicted Topic via POST /api/rag/ask...")
    conflict_query = "What is the recommended first-line vasopressor and empiric antibiotic for septic shock resuscitation?"
    payload = {
        "question": conflict_query,
        "top_k": 4,
    }

    ask_resp = client.post("/api/rag/ask", json=payload)
    assert ask_resp.status_code == 200, f"/ask failed ({ask_resp.status_code}): {ask_resp.text}"
    res = ask_resp.json()

    # -------------------------------------------------------------
    # 3. Assertions on Conflict Detection
    # -------------------------------------------------------------
    print("\n[Step 3/4] Verifying Conflict Detection Results & Schema...")
    print(f"  [+] Query: '{conflict_query}'")
    print(f"  [+] Evidence Status: {res['evidence_status']}")
    print(f"  [+] Number of Conflicting Items Detected: {len(res.get('conflicts', []))}")
    print(f"  [+] Audit Log ID: {res.get('audit_log_id')}")

    # Assert status is CONFLICTED
    assert res["evidence_status"] == "CONFLICTED", (
        f"Expected evidence_status == 'CONFLICTED', got '{res['evidence_status']}'"
    )

    conflicts = res.get("conflicts", [])
    assert len(conflicts) >= 2, "Must return at least 2 conflicting version items"

    # Verify both versions and dates are represented
    versions_found = {c["version"] for c in conflicts}
    assert "1.0" in versions_found, "Version 1.0 must be reported in conflicts"
    assert "2.0" in versions_found, "Version 2.0 must be reported in conflicts"

    # Verify freshness preference (ACTIVE version is identified)
    active_conflicts = [c for c in conflicts if c.get("is_active_fresh")]
    assert len(active_conflicts) > 0, "ACTIVE current version must be clearly flagged under freshness preference"
    assert active_conflicts[0]["version"] == "2.0", "Version 2.0 must be marked as active fresh"
    assert active_conflicts[0]["status"] == "ACTIVE", "Active conflict must have status ACTIVE"

    # Verify all required conflict fields are present
    required_conflict_fields = ["source", "version", "date", "status", "claim", "relevant_passage", "citation"]
    for c in conflicts:
        for f in required_conflict_fields:
            assert f in c and c[f], f"Field '{f}' missing or empty in conflict item: {c}"

    # Verify conflicting evidence is NOT hidden in the answer
    answer_text = res["answer"]
    assert "dopamine" in answer_text.lower(), "Answer must disclose Dopamine recommendation"
    assert "norepinephrine" in answer_text.lower(), "Answer must disclose Norepinephrine recommendation"
    assert "conflict" in answer_text.lower() or "alert" in answer_text.lower()
    assert "active" in answer_text.lower()
    assert "superseded" in answer_text.lower()

    # -------------------------------------------------------------
    # 4. Verify PostgreSQL AuditLog Record
    # -------------------------------------------------------------
    print("\n[Step 4/4] Verifying AuditLog in PostgreSQL Database...")
    db = SessionLocal()
    try:
        audit = db.query(AuditLog).filter(AuditLog.id == res["audit_log_id"]).first()
        assert audit is not None, "AuditLog record must exist in PostgreSQL"
        assert audit.evidence_status == "CONFLICTED", (
            f"AuditLog evidence_status must be 'CONFLICTED', got '{audit.evidence_status}'"
        )
        print(f"  [+] AuditLog ID: {audit.id}")
        print(f"  [+] AuditLog Question: '{audit.question}'")
        print(f"  [+] AuditLog Evidence Status: {audit.evidence_status}")
        print(f"  [+] AuditLog Created At: {audit.created_at}")
    finally:
        db.close()

    # -------------------------------------------------------------
    # Actual Conflict Detection Output Display
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("ACTUAL CONFLICT DETECTION OUTPUT (RAW JSON STRUCTURE):")
    print("=" * 80)
    display_res = {
        "evidence_status": res["evidence_status"],
        "conflicts": res["conflicts"],
        "answer": res["answer"],
    }
    print(json.dumps(display_res, indent=2))

    print("\n" + "=" * 80)
    print("ALL PHASE 5 CONFLICT DETECTION REQUIREMENTS VERIFIED WITH 100% SUCCESS!")
    print("================================================================================")


if __name__ == "__main__":
    run_phase5_tests()
