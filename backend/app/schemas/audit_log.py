from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    user_role: Optional[str] = "CLINICAL"
    access_status: Optional[str] = "GRANTED"
    question: str
    answer: str
    evidence_status: str  # grounded, refusal, insufficient_evidence, conflicted


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
