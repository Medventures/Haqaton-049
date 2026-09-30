from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.db import SessionLocal
from app.errors import http_exception_handler, validation_exception_handler
from app.modules.engine.catalog import get_catalog
from app.routers import auth, catalog, demo, documents, families, interview, notifications, overdue, plans, reports


def _run_scheduler_tick():
    from app.models import Family
    from app.modules.scheduler.escalation import recompute_family

    db = SessionLocal()
    try:
        catalog_ = get_catalog()
        for family in db.query(Family).all():
            recompute_family(db, family, catalog_)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if not get_settings().database_url.startswith("sqlite:///:memory:"):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler = BackgroundScheduler()
            scheduler.add_job(_run_scheduler_tick, "interval", hours=1, id="escalation_tick")
            scheduler.start()
        except Exception:
            scheduler = None
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    # Раздел 14: "API загружает [справочники] в память при старте" — сбой
    # валидации по JSON Schema должен остановить запуск, а не всплыть
    # позже при первом запросе.
    get_catalog()

    app = FastAPI(title="AqylRoute API", lifespan=lifespan)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    for router in (auth, interview, plans, catalog, families, documents, reports, notifications, demo, overdue):
        app.include_router(router.router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
