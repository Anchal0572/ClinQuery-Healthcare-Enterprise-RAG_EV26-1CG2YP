from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.users import router as users_router
from app.api.rag import router as rag_router
from app.api.audit_logs import router as audit_logs_router
from app.api.evaluation import router as evaluation_router

api_router = APIRouter()

# Include health router (root /health as required)
api_router.include_router(health_router)

# Include resource routers
api_router.include_router(documents_router)
api_router.include_router(users_router)
api_router.include_router(rag_router)
api_router.include_router(audit_logs_router)
api_router.include_router(evaluation_router)
