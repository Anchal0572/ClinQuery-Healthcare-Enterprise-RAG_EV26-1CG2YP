from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "connected"
    version: Optional[str] = None
