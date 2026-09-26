import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, check_db_connection
from app.api.router import api_router

settings = get_settings()

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("healthcare_rag")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager:
    Initializes database tables and verifies services on startup.
    """
    logger.info("Initializing Healthcare RAG Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider} (Model: {settings.llm_model})")
    
    # Try initializing DB schema on startup
    try:
        init_db()
        logger.info("PostgreSQL database tables initialized successfully.")
    except Exception as e:
        logger.warning(
            f"Database initialization deferred (database might not be ready yet): {e}"
        )

    yield

    logger.info("Healthcare RAG Backend shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Healthcare Greenfield Enterprise RAG Backend — "
        "Retrieval a Clinical Team Can Rely On. "
        "High-reliability clinical document ingestion, vector retrieval, and grounded Q&A."
    ),
    lifespan=lifespan,
)

# Configure CORS Middleware for React + Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please contact the clinical engineering team.",
            "path": request.url.path,
        },
    )


# Include API Router
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "health_check": "/health",
        "docs": "/docs",
    }
