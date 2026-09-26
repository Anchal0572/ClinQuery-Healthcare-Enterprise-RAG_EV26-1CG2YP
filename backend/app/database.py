import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Configure SQLAlchemy engine with connection pool settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=(settings.log_level.upper() == "DEBUG"),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session
    and ensures it is closed after request handling.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Verify PostgreSQL connectivity by executing a lightweight query.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def init_db() -> None:
    """
    Creates all database tables registered in the Base metadata.
    """
    # Import models here to register them with metadata before creating tables
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
