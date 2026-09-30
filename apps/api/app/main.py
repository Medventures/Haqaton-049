from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import Base, engine
from app.errors import http_exception_handler, validation_exception_handler
from app.modules.engine.catalog import get_catalog
from app.routers import auth, catalog, families, interview, plans


def create_app() -> FastAPI:
    # Раздел 14: "API загружает [справочники] в память при старте" — сбой
    # валидации по JSON Schema должен остановить запуск, а не всплыть
    # позже при первом запросе.
    get_catalog()

    app = FastAPI(title="AqylRoute API")

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(auth.router, prefix="/api")
    app.include_router(interview.router, prefix="/api")
    app.include_router(plans.router, prefix="/api")
    app.include_router(catalog.router, prefix="/api")
    app.include_router(families.router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
