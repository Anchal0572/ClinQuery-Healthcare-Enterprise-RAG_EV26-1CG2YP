from app.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS allowed_roles VARCHAR(255) DEFAULT 'ADMIN,CLINICAL';"))
        conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_role VARCHAR(50) DEFAULT 'CLINICAL';"))
        conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS access_status VARCHAR(50) DEFAULT 'GRANTED';"))
        conn.execute(text("UPDATE documents SET allowed_roles = 'ADMIN,CLINICAL' WHERE allowed_roles IS NULL;"))
        conn.commit()
    print("Migration successfully applied!")

if __name__ == "__main__":
    run_migration()
