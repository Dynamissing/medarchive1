from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import sys

from alembic import command
from alembic.config import Config
from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.admin import login_router as admin_login_router
from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.public import router as public_router
from app.core.config import BACKEND_DIR
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        logger.info("Starting %s", settings.app_name)
        run_startup_migrations()
        yield
        logger.info("Stopping %s", settings.app_name)

    return lifespan


def run_startup_migrations() -> None:
    if "pytest" in sys.modules:
        return
    alembic_ini = BACKEND_DIR / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("Alembic config not found at %s; skipping startup migrations.", alembic_ini)
        return
    try:
        config = Config(str(alembic_ini))
        command.upgrade(config, "head")
    except Exception:
        logger.exception("Startup database migration failed.")


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        debug=app_settings.debug,
        lifespan=build_lifespan(app_settings),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error while handling %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database is unavailable or not migrated. Check DATABASE_URL and database service.",
                "error_type": type(exc).__name__,
            },
            headers=CORS_HEADERS,
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while handling %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_type": type(exc).__name__},
            headers=CORS_HEADERS,
        )

    app.include_router(admin_login_router)
    app.include_router(admin_router)
    app.include_router(health_router)
    app.include_router(public_router)
    return app


app = create_app()
