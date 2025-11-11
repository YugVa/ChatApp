from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Cookie, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from ..models import SessionToken, User, UserRole

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
fernet = Fernet(settings.fernet_key)

SESSION_COOKIE_NAME = "chatapp_session"


@dataclass(slots=True)
class SessionTicket:
    session: SessionToken
    encrypted_token: str


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token() -> str:
    return uuid4().hex


def create_session(db: Session, user: User) -> SessionTicket:
    token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.session_expire_minutes)
    session = SessionToken(
        user_id=user.id,
        token_hash=pwd_context.hash(token),
        created_at=datetime.utcnow(),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    encrypted_token = fernet.encrypt(token.encode("utf-8")).decode("utf-8")
    return SessionTicket(session=session, encrypted_token=encrypted_token)


def destroy_session(db: Session, encrypted_token: str) -> None:
    token = decrypt_token(encrypted_token)
    if token is None:
        return
    sessions = db.query(SessionToken).filter(SessionToken.expires_at > datetime.utcnow()).all()
    for record in sessions:
        if pwd_context.verify(token, record.token_hash):
            db.delete(record)
    db.commit()


def decrypt_token(encrypted_token: str) -> Optional[str]:
    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def get_current_session(
    db: Session = Depends(get_db),
    session_cookie: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Optional[SessionToken]:
    if not session_cookie:
        return None
    token = decrypt_token(session_cookie)
    if token is None:
        return None
    sessions = db.query(SessionToken).filter(SessionToken.expires_at > datetime.utcnow()).all()
    for record in sessions:
        if pwd_context.verify(token, record.token_hash):
            return record
    return None


def require_user(
    required_role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    session: Optional[SessionToken] = Depends(get_current_session),
) -> User:
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if required_role and not user.has_role(required_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def require_root(user: User = Depends(lambda: require_user(UserRole.ROOT))) -> User:
    return user
