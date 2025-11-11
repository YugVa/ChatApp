from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseModel):
    app_name: str = "ChatApp Employee Service"
    secret_key: str = Field(..., min_length=32)
    session_expire_minutes: int = 60 * 24
    database_url: str = Field(..., description="SQLAlchemy database URL")
    alembic_database_url: Optional[str] = None
    fernet_key: str = Field(..., description="URL-safe base64 key for Fernet encryption")
    media_root: Path = BASE_DIR / "backend" / "app" / "static" / "photos"
    password_export_excel: str = "secure"

    class Config:
        extra = "ignore"

    @validator("alembic_database_url", always=True)
    def _default_alembic_url(cls, v: Optional[str], values: dict[str, object]) -> Optional[str]:
        return v or values.get("database_url")  # type: ignore[return-value]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    import os

    data = {
        "app_name": os.getenv("APP_NAME", "ChatApp Employee Service"),
        "secret_key": os.environ["SECRET_KEY"],
        "session_expire_minutes": int(os.getenv("SESSION_EXPIRE_MINUTES", "1440")),
        "database_url": os.environ["DATABASE_URL"],
        "alembic_database_url": os.getenv("ALEMBIC_DATABASE_URL"),
        "fernet_key": os.environ["FERNET_KEY"],
        "password_export_excel": os.getenv("PASSWORD_EXPORT_EXCEL", "secure"),
    }
    settings = Settings(**data)
    settings.media_root.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
