from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import auth, employees, pages
from .core.config import settings
from .services.audit import log_event

app = FastAPI(title=settings.app_name)
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Fallback error handler with audit logging
    from .core.database import SessionLocal

    with SessionLocal() as db:
        log_event(db, action="error", resource="application", details=str(exc), request=request)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
