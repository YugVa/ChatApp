from __future__ import annotations

from datetime import date, datetime
from typing import List
from urllib.parse import quote_plus

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import require_root, require_user
from ..models import Employee, EmployeeRank, User, UserRole
from ..schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from ..services.audit import log_event
from ..services.excel import ExcelImportError, read_employees_from_excel, workbook_with_password
from .deps import get_db_session

router = APIRouter(prefix="/employees", tags=["employees"])


def _ensure_editor(user: User) -> None:
    if user.role not in {UserRole.ROOT, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


@router.get("/", response_model=List[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
    rank: EmployeeRank | None = None,
    hired_from: date | None = None,
    hired_to: date | None = None,
):
    query = db.query(Employee)
    if rank:
        query = query.filter(Employee.rank == rank)
    if hired_from:
        query = query.filter(Employee.hire_date >= hired_from)
    if hired_to:
        query = query.filter(Employee.hire_date <= hired_to)
    employees = query.order_by(Employee.last_name).all()
    return employees


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    _ensure_editor(user)
    employee = Employee(
        first_name=payload.first_name,
        last_name=payload.last_name,
        rank=payload.rank,
        hire_date=payload.hire_date,
    )
    employee.attestation_date = payload.attestation_date
    db.add(employee)
    db.commit()
    db.refresh(employee)
    log_event(db, action="create", resource="employee", user=user, details=f"employee_id={employee.id}")
    return employee


@router.get("/{employee_id}", response_model=EmployeeRead)
def read_employee(
    employee_id: int,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    _ensure_editor(user)
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        if key == "attestation_date":
            employee.attestation_date = value
        elif value is not None:
            setattr(employee, key, value)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    log_event(db, action="update", resource="employee", user=user, details=f"employee_id={employee.id}")
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_root),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    log_event(db, action="delete", resource="employee", user=user, details=f"employee_id={employee.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/import/xlsx")
def import_employees(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_root),
):
    try:
        df = read_employees_from_excel(file)
    except ExcelImportError as exc:
        log_event(db, action="import_failed", resource="employee", user=user, details=str(exc), request=request)
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse(
                url=f"/?import_error={quote_plus(str(exc))}",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        raise HTTPException(status_code=400, detail=str(exc))
    created, updated = 0, 0
    for _, row in df.iterrows():
        employee = (
            db.query(Employee)
            .filter(Employee.first_name == row["first_name"], Employee.last_name == row["last_name"])
            .first()
        )
        attestation_value = row.get("attestation_date")
        attestation_date = None
        if pd.notna(attestation_value):
            if hasattr(attestation_value, "date"):
                attestation_date = attestation_value.date()
            elif isinstance(attestation_value, date):
                attestation_date = attestation_value
            else:
                attestation_date = date.fromisoformat(str(attestation_value))
        hire_value = row.get("hire_date")
        if hasattr(hire_value, "date"):
            hire_date = hire_value.date()
        elif isinstance(hire_value, date):
            hire_date = hire_value
        else:
            hire_date = date.fromisoformat(str(hire_value))
        if employee:
            employee.rank = EmployeeRank(row["rank"])
            employee.hire_date = hire_date
            employee.attestation_date = attestation_date
            updated += 1
        else:
            employee = Employee(
                first_name=row["first_name"],
                last_name=row["last_name"],
                rank=EmployeeRank(row["rank"]),
                hire_date=hire_date,
            )
            employee.attestation_date = attestation_date
            db.add(employee)
            created += 1
    db.commit()
    log_event(
        db,
        action="import",
        resource="employee",
        user=user,
        request=request,
        details=f"created={created}, updated={updated}",
    )
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(
            url=f"/?import_created={created}&import_updated={updated}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return {"created": created, "updated": updated}


@router.get("/export")
def export_employees(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_user),
):
    employees = db.query(Employee).all()
    df = pd.DataFrame(
        [
            {
                "first_name": e.first_name,
                "last_name": e.last_name,
                "rank": e.rank.value,
                "hire_date": e.hire_date,
                "attestation_date": e.attestation_date,
            }
            for e in employees
        ]
    )
    output = workbook_with_password(df, settings.password_export_excel)
    log_event(db, action="export", resource="employee", user=user, details=f"count={len(df)}")
    filename = f"employees_{datetime.utcnow().date()}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
