from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from ..models import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    username: str
    password: str
