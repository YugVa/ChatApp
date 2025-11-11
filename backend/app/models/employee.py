from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import Date, Enum as SqlEnum, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, VARCHAR

from ..core.config import settings
from .base import Base


fernet = Fernet(settings.fernet_key)


class EncryptedString(TypeDecorator[str]):
    impl = VARCHAR(255)

    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect):  # type: ignore[override]
        if value is None:
            return None
        return fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value: Optional[str], dialect):  # type: ignore[override]
        if value is None:
            return None
        try:
            return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except Exception:
            return value


class EmployeeRank(str, Enum):
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"
    LEAD = "LEAD"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    rank: Mapped[EmployeeRank] = mapped_column(SqlEnum(EmployeeRank), default=EmployeeRank.JUNIOR)
    hire_date: Mapped[date] = mapped_column(Date())
    attestation_date_encrypted: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @property
    def attestation_date(self) -> Optional[date]:
        value = self.attestation_date_encrypted
        if value:
            return date.fromisoformat(value)
        return None

    @attestation_date.setter
    def attestation_date(self, value: Optional[date]) -> None:
        self.attestation_date_encrypted = value.isoformat() if value else None
