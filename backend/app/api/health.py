import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.database import check_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service and Database Health Check")
def get_health():
    """
    Returns the operational health of the FastAPI service and PostgreSQL database.
    Required format:
    {
      "status": "ok",
      "database": "connected"
    }
    """
    is_db_connected = check_db_connection()

    if is_db_connected:
        return {
            "status": "ok",
            "database": "connected"
        }
    else:
        logger.error("Health check: PostgreSQL database connection failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "disconnected"
            }
        )
