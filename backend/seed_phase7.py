import os
import sys
from datetime import date
from sqlalchemy import text

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, engine
from app.models.document import Document, DocumentChunk, IngestionStatus
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.config import get_settings


def seed_rbac_data():
    print("\n--- 1. Seeding Demo Users with Roles (ADMIN, CLINICAL, OPERATIONS) ---")
    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO users (id, name, email, role)
            VALUES 
                (1, 'Dr. Sarah Smith, MD', 's.smith@hospital.internal', 'CLINICAL'),
                (2, 'Alex Rivera', 'a.rivera.ops@hospital.internal', 'OPERATIONS'),
                (3, 'Chief Admin', 'admin@hospital.internal', 'ADMIN')
            ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, name = EXCLUDED.name;
        """)
        )
        conn.commit()
    print("Users seeded successfully.")

    db = next(get_db())
    settings = get_settings()
    embedder = get_embedding_service()
    qdrant = get_qdrant_service()
    qdrant.ensure_collection(settings.qdrant_collection, vector_size=embedder.get_dimension())

    print("\n--- 2. Ensuring Existing Clinical Documents have allowed_roles='ADMIN,CLINICAL' ---")
    clinical_docs = (
        db.query(Document)
        .filter(Document.title.ilike("%medication%") | Document.title.ilike("%sepsis%"))
        .all()
    )
    for doc in clinical_docs:
        doc.allowed_roles = "ADMIN,CLINICAL"
    db.commit()

    print("\n--- 3. Creating and Indexing Operations Document (allowed_roles='ADMIN,OPERATIONS') ---")
    ops_doc = (
        db.query(Document)
        .filter(Document.title == "Hospital Facility Safety & Hazardous Waste Operations Manual")
        .first()
    )
    if not ops_doc:
        ops_doc = Document(
            title="Hospital Facility Safety & Hazardous Waste Operations Manual",
            document_type="Operations SOP",
            version="1.0",
            status="ACTIVE",
            department="Facilities & Engineering",
            effective_date=date(2024, 3, 1),
            allowed_roles="ADMIN,OPERATIONS",
        )
        db.add(ops_doc)
        db.commit()
        db.refresh(ops_doc)

        ops_chunks_text = [
            (
                "Section 2.1: Biohazard Waste Handling\nBiohazard and infectious waste containers must be sealed immediately when 75% full. All biohazard waste bags must be transported using dedicated leak-proof red carts directly to the basement sterilization autoclave area. Personnel must wear puncture-resistant utility gloves and face shields.",
                "Biohazard Waste Handling",
                1,
            ),
            (
                "Section 4.3: Airborne Infection Isolation Rooms (AIIR) HVAC Operations\nAll negative-pressure isolation rooms must maintain a minimum air exchange rate of 12 air changes per hour (ACH) for new facilities and 6 ACH for existing facilities. Pressure differentials of at least -2.5 Pascals (-0.01 inch water gauge) relative to the corridor must be monitored daily by facility operations staff.",
                "HVAC Operations & Pressure Differential",
                2,
            ),
        ]

        for idx, (txt, sec, pg) in enumerate(ops_chunks_text):
            chunk = DocumentChunk(
                document_id=ops_doc.id,
                document_version="1.0",
                chunk_text=txt,
                section=sec,
                page_number=pg,
                chunk_type="protocol",
                qdrant_point_id=f"doc-{ops_doc.id}-c{idx+1}",
            )
            db.add(chunk)
        db.commit()
        db.refresh(ops_doc)

    # Index operations doc chunks into Qdrant
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == ops_doc.id).all()
    texts = [c.chunk_text for c in chunks]
    vectors = embedder.embed_texts(texts)

    chunks_data = []
    for chunk, vec in zip(chunks, vectors):
        chunks_data.append(
            {
                "point_id": int(chunk.id),
                "vector": vec,
                "payload": {
                    "chunk_id": int(chunk.id),
                    "document_id": int(ops_doc.id),
                    "document_title": ops_doc.title,
                    "version": "1.0",
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "chunk_type": chunk.chunk_type,
                    "department": ops_doc.department,
                    "status": ops_doc.status,
                    "effective_date": str(ops_doc.effective_date),
                    "chunk_text": chunk.chunk_text,
                    "allowed_roles": ops_doc.allowed_roles,
                },
            }
        )

    qdrant.upsert_chunks(chunks_data, settings.qdrant_collection)
    print(f"Indexed {len(chunks_data)} chunks for Operations Document (ID {ops_doc.id}).")


if __name__ == "__main__":
    seed_rbac_data()
