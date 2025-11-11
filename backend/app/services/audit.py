from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from ..models import AuditLog, User


def log_event(
    db: Session,
    *,
    action: str,
    resource: str,
    user: Optional[User] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    ip_address = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None
    record = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
