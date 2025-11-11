from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import unquote_plus

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import require_user
from ..models import Employee, EmployeeRank, User, UserRole
from ..services.audit import log_event
from .deps import get_db_session

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="backend/app/templates")


class ForbiddenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Недостаточно прав")


def ensure_editor(user: User) -> None:
    if user.role not in {UserRole.ROOT, UserRole.MANAGER}:
        raise ForbiddenException()

@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
    rank: Optional[EmployeeRank] = None,
    hired_from: Optional[date] = None,
    hired_to: Optional[date] = None,
):
    query = db.query(Employee)
    if rank:
        query = query.filter(Employee.rank == rank)
    if hired_from:
        query = query.filter(Employee.hire_date >= hired_from)
    if hired_to:
        query = query.filter(Employee.hire_date <= hired_to)
    employees = query.order_by(Employee.last_name).all()
    params = request.query_params
    import_created = params.get("import_created")
    import_updated = params.get("import_updated")
    raw_error = params.get("import_error")
    import_error = unquote_plus(raw_error) if raw_error else None
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "employees": employees,
            "rank_filter": rank.value if rank else "",
            "hired_from": hired_from.isoformat() if hired_from else "",
            "hired_to": hired_to.isoformat() if hired_to else "",
            "ranks": list(EmployeeRank),
            "settings": settings,
            "import_created": import_created,
            "import_updated": import_updated,
            "import_error": import_error,
        },
    )


@router.get("/employees/{employee_id}", response_class=HTMLResponse)
def employee_card(
    employee_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return templates.TemplateResponse(
        "employee_card.html",
        {"request": request, "employee": employee, "user": user},
    )


@router.post("/employees/{employee_id}/photo")
def upload_photo(
    employee_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    ensure_editor(user)
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    settings.media_root.mkdir(parents=True, exist_ok=True)
    filename = f"employee_{employee.id}{Path(file.filename).suffix}"
    destination = settings.media_root / filename
    with destination.open("wb") as buffer:
        buffer.write(file.file.read())
    employee.photo_path = f"/static/photos/{filename}"
    db.add(employee)
    db.commit()
    db.refresh(employee)
    log_event(db, action="upload_photo", resource="employee", user=user, details=f"employee_id={employee.id}", request=request)
    return RedirectResponse(url=f"/employees/{employee.id}", status_code=303)


@router.post("/employees/new")
def create_employee_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    rank: EmployeeRank = Form(...),
    hire_date: date = Form(...),
    attestation_date: Optional[date] = Form(None),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    ensure_editor(user)
    employee = Employee(
        first_name=first_name,
        last_name=last_name,
        rank=rank,
        hire_date=hire_date,
    )
    employee.attestation_date = attestation_date
    db.add(employee)
    db.commit()
    log_event(db, action="create_form", resource="employee", user=user, details=f"employee_id={employee.id}", request=request)
    return RedirectResponse(url="/", status_code=303)


@router.post("/employees/{employee_id}/update")
def update_employee_form(
    employee_id: int,
    request: Request,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    rank: Optional[EmployeeRank] = Form(None),
    hire_date: Optional[date] = Form(None),
    attestation_date: Optional[date] = Form(None),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    ensure_editor(user)
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if first_name:
        employee.first_name = first_name
    if last_name:
        employee.last_name = last_name
    if rank:
        employee.rank = rank
    if hire_date:
        employee.hire_date = hire_date
    if attestation_date:
        employee.attestation_date = attestation_date
    db.add(employee)
    db.commit()
    log_event(db, action="update_form", resource="employee", user=user, details=f"employee_id={employee.id}", request=request)
    return RedirectResponse(url=f"/employees/{employee.id}", status_code=303)
