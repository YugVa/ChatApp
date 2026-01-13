from fastapi import FastAPI

from news_monitoring.core.logging import configure_logging


configure_logging()

app = FastAPI(title="News Monitoring API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
