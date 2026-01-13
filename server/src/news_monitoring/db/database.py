from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from news_monitoring.core.config import settings


def build_engine() -> AsyncEngine:
    return create_async_engine(settings.postgres_dsn, pool_pre_ping=True)
