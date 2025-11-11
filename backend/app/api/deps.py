from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import require_root, require_user
from ..models import User


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user(user: User = Depends(require_user)) -> User:
    return user


def get_root_user(user: User = Depends(require_root)) -> User:
    return user
