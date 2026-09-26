"""
Database Connection & Operations Test Script
Verifies:
1. PostgreSQL connection
2. Table creation (User, Document, DocumentChunk, AuditLog)
3. Document insertion & retrieval
4. DocumentChunk cascade relationship
5. User creation & query
"""

import sys
import os

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from sqlalchemy import text
from app.config import get_settings
from app.database import engine, SessionLocal, init_db, check_db_connection
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.models.audit_log import AuditLog


def run_tests():
    print("=" * 60)
    print("HEALTHCARE RAG - DATABASE CONNECTION & VERIFICATION SUITE")
    print("=" * 60)

    settings = get_settings()
    masked_url = settings.database_url
    if "@" in masked_url:
        proto_user, host_db = masked_url.split("@")
        masked_url = f"{proto_user.split(':')[0]}://****:****@{host_db}"
    print(f"Target Database URL: {masked_url}")

    # Step 1: Raw connection test
    print("\n[Step 1/5] Testing basic connectivity...")
    if not check_db_connection():
        print("[-] FAILED: Could not establish connection to PostgreSQL.")
        sys.exit(1)
    print("[+] SUCCESS: PostgreSQL connection verified.")

    # Step 2: Initialize tables
    print("\n[Step 2/5] Creating and verifying database tables...")
    try:
        init_db()
        print("[+] SUCCESS: Tables created / verified successfully.")
    except Exception as e:
        print(f"[-] FAILED: Table creation failed: {e}")
        sys.exit(1)

    # Step 3: Inspect tables in database
    print("\n[Step 3/5] Inspecting schema tables...")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        ))
        tables = [row[0] for row in result.fetchall()]
        print(f"[+] Tables found in PostgreSQL: {tables}")
        expected = ["audit_logs", "document_chunks", "documents", "users"]
        for exp in expected:
            assert exp in tables, f"Expected table '{exp}' not found in database!"
        print("[+] All 4 required models exist in PostgreSQL schema.")

    # Step 4: Insert and retrieve User
    print("\n[Step 4/5] Testing User insertion and retrieval...")
    db = SessionLocal()
    try:
        test_email = "dr.smith.test@hospital.internal"
        # Cleanup if leftover from previous run
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()

        new_user = User(
            name="Dr. Sarah Smith, MD",
            email=test_email,
            role="cardiologist",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_retrieved = db.query(User).filter(User.id == new_user.id).first()
        assert user_retrieved is not None
        assert user_retrieved.name == "Dr. Sarah Smith, MD"
        print(f"[+] User created and retrieved: ID={user_retrieved.id}, Name={user_retrieved.name}, Role={user_retrieved.role}")

        # Step 5: Insert and retrieve Document with Chunk
        print("\n[Step 5/5] Testing Document & DocumentChunk insertion and relationship...")
        test_doc = Document(
            title="AHA/ACC 2024 Guideline for the Management of Heart Failure",
            document_type="clinical_guideline",
            version="1.0",
            status="active",
            department="Cardiology",
            effective_date=date(2024, 1, 15),
        )
        db.add(test_doc)
        db.flush()

        test_chunk = DocumentChunk(
            document_id=test_doc.id,
            chunk_text="In patients with symptomatic heart failure with reduced ejection fraction (HFrEF), guideline-directed medical therapy (GDMT) includes SGLT2 inhibitors and ARNI/ACEi.",
            page_number=14,
            section="Section 4.2 - GDMT Pharmacotherapy",
            chunk_type="text",
            qdrant_point_id="hf-guideline-p14-c1",
        )
        db.add(test_chunk)
        db.commit()
        db.refresh(test_doc)

        doc_retrieved = db.query(Document).filter(Document.id == test_doc.id).first()
        assert doc_retrieved is not None
        assert len(doc_retrieved.chunks) == 1
        assert doc_retrieved.chunks[0].section == "Section 4.2 - GDMT Pharmacotherapy"
        print(f"[+] Document created and retrieved: ID={doc_retrieved.id}, Title='{doc_retrieved.title}'")
        print(f"[+] Chunks associated: {len(doc_retrieved.chunks)} chunk(s). Content sample: '{doc_retrieved.chunks[0].chunk_text[:60]}...'")

        print("\n" + "=" * 60)
        print("ALL DATABASE TESTS PASSED WITH 100% SUCCESS!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[-] FAILED during database CRUD test: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
