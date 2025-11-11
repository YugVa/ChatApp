from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..core.security import (
    SESSION_COOKIE_NAME,
    create_session,
    destroy_session,
    get_password_hash,
    require_root,
    require_user,
    verify_password,
)
from ..models import User
from ..schemas.user import UserCreate
from ..services.audit import log_event
from .deps import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="backend/app/templates")


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_session),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        log_event(db, action="login_failed", resource="auth", details=f"user={username}", request=request)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    ticket = create_session(db, user)
    response = templates.TemplateResponse(
        "login_success.html", {"request": request, "user": user}
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=ticket.encrypted_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    log_event(db, action="login", resource="auth", user=user, request=request)
    return response


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    payload: UserCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_root),
):
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(db, action="register_user", resource="auth", user=current_user, details=f"new_user={user.username}", request=request)
    return user


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
    session_cookie: str | None = None,
):
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie:
        destroy_session(db, cookie)
        response.delete_cookie(SESSION_COOKIE_NAME)
    log_event(db, action="logout", resource="auth", user=user, request=request)
    return {"detail": "Logged out"}
