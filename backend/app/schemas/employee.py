from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from ..models.employee import EmployeeRank


class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    rank: EmployeeRank = EmployeeRank.JUNIOR
    hire_date: date
    attestation_date: Optional[date] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    rank: Optional[EmployeeRank] = None
    hire_date: Optional[date] = None
    attestation_date: Optional[date] = None


class EmployeeRead(EmployeeBase):
    id: int
    photo_path: Optional[str] = None

    class Config:
        orm_mode = True
