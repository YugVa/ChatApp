from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: str
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
