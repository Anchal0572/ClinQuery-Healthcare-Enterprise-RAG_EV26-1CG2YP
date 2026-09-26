import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse], status_code=status.HTTP_200_OK, summary="List clinical query audit logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    evidence_status: Optional[str] = Query(None, description="Filter by status (SUFFICIENT, INSUFFICIENT, CONFLICTED)"),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if evidence_status:
        query = query.filter(AuditLog.evidence_status == evidence_status)
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
