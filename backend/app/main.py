"""Application entrypoint: `uvicorn app.main:app`.

Uses the app-factory pattern so tests can construct isolated app instances
with overridden settings/dependencies.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api_router import api_router
from app.common.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", environment=settings.environment)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SYJ LaunchPad API",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    # slowapi's own type stubs for `_rate_limit_exceeded_handler` don't match
    # Starlette's `add_exception_handler` signature exactly (a known gap in
    # slowapi's typing, not a bug in this code) — the handler is correct at
    # runtime, so we scope the ignore to this one line.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
