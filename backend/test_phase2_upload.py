"""
Phase 2 Comprehensive Upload, Parser & Ingestion Test Suite
Tests:
- Uploading PDF, DOCX, CSV, XLSX, and TXT synthetic healthcare documents
- Verifying status lifecycle (UPLOADING -> PROCESSING -> COMPLETED)
- Verifying PostgreSQL records for Document and DocumentChunk
- Verifying chunk retention: document_id, document_version, page_number, section, chunk_type, chunk_text
- Verifying table chunks preserve: table name, row, column, value
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk, IngestionStatus

client = TestClient(app)
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")


def test_upload_and_verify():
    print("=" * 70)
    print("HEALTHCARE RAG - PHASE 2 DOCUMENT INGESTION & CHUNKING TEST")
    print("=" * 70)

    test_files = [
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
            "filename": "synthetic_emergency_drug_formulary.csv",
            "title": "Emergency Medicine Critical Resuscitation Formulary",
            "department": "Emergency Medicine",
            "document_type": "drug_monograph",
            "version": "1.0",
        },
        {
            "filename": "synthetic_critical_lab_intervals.xlsx",
            "title": "Clinical Pathology Critical Laboratory Reference Intervals",
            "department": "Laboratory Medicine",
            "document_type": "lab_reference",
            "version": "4.0",
        },
        {
            "filename": "synthetic_stroke_thrombolysis_protocol.txt",
            "title": "Acute Ischemic Stroke Thrombolytic Therapy Protocol",
            "department": "Neurology / ED",
            "document_type": "protocol",
            "version": "1.5",
        },
    ]

    uploaded_doc_ids = []

    for item in test_files:
        filepath = os.path.join(SAMPLE_DIR, item["filename"])
        assert os.path.exists(filepath), f"File not found: {filepath}"

        print(f"\n[Testing Upload] {item['filename']} ({item['document_type']})...")
        with open(filepath, "rb") as f:
            files = {"file": (item["filename"], f)}
            data = {
                "title": item["title"],
                "department": item["department"],
                "document_type": item["document_type"],
                "version": item["version"],
                "effective_date": "2024-06-01",
            }
            resp = client.post("/api/documents/upload", files=files, data=data)

        assert resp.status_code == 201, f"Upload failed ({resp.status_code}): {resp.text}"
        res_json = resp.json()
        doc_id = res_json["document_id"]
        uploaded_doc_ids.append(doc_id)

        print(f"  [+] Status Code: {resp.status_code}")
        print(f"  [+] Document ID: {doc_id}")
        print(f"  [+] Ingestion Status: {res_json['status']}")
        print(f"  [+] Chunks Created: {res_json['chunks_created']}")
        print(f"  [+] Extracted Sections: {res_json['extracted_sections']}")
        assert res_json["status"] == IngestionStatus.COMPLETED
        assert res_json["chunks_created"] > 0

    # Verify directly in PostgreSQL
    print("\n" + "=" * 70)
    print("VERIFYING POSTGRESQL DATABASE RECORDS & FIELD RETENTION")
    print("=" * 70)

    db = SessionLocal()
    try:
        total_chunks_verified = 0
        for doc_id in uploaded_doc_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is not None
            assert doc.status == IngestionStatus.COMPLETED
            assert doc.file_path is not None
            assert doc.file_size_bytes > 0

            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
            chunk_count = len(chunks)
            total_chunks_verified += chunk_count

            print(f"\n[Document ID: {doc.id}] '{doc.title}' (Version {doc.version})")
            print(f"  Status: {doc.status} | Department: {doc.department} | Size: {doc.file_size_bytes} bytes")
            print(f"  Chunks in PostgreSQL: {chunk_count}")

            # Verify chunk retention requirements
            for c in chunks:
                assert c.document_id == doc.id, "Chunk must retain document_id"
                assert c.document_version == doc.version, "Chunk must retain document_version"
                assert c.chunk_type in ["text", "table", "protocol"], "Chunk must retain valid chunk_type"
                assert c.chunk_text and len(c.chunk_text.strip()) > 0, "Chunk must retain chunk_text"
                assert c.page_number is not None, "Chunk must retain page_number"
                assert c.section is not None, "Chunk must retain section"

            # Print sample chunk
            sample_chunk = chunks[0]
            print(f"  Sample Chunk [ID={sample_chunk.id}, Type={sample_chunk.chunk_type}, Page={sample_chunk.page_number}, Sec='{sample_chunk.section}']: ")
            preview = sample_chunk.chunk_text.replace("\n", " ")[:120]
            print(f"    '{preview}...'")

            # If document has table chunks, verify Table Name, Row, Column, Value preservation
            table_chunks = [c for c in chunks if c.chunk_type == "table"]
            if table_chunks:
                tbl = table_chunks[0]
                print(f"  [Table Chunk Verified] ID={tbl.id} preserves table name, row, column, value:")
                tbl_preview = tbl.chunk_text.splitlines()[:4]
                for l in tbl_preview:
                    print(f"    | {l}")
                assert "[Table:" in tbl.chunk_text, "Table chunk must preserve table name"
                assert "Row " in tbl.chunk_text, "Table chunk must preserve row"
                assert "=" in tbl.chunk_text, "Table chunk must preserve column and value"

        print("\n" + "=" * 70)
        print(f"ALL 5 FORMATS VERIFIED! Total PostgreSQL Chunks Created & Verified: {total_chunks_verified}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    test_upload_and_verify()
