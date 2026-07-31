from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.health.schemas import HealthResponse
from app.features.health.service import check_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Liveness + readiness probe. Used by Railway/Kubernetes health checks."""
    db_status = await check_database(db)
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        database=db_status,
    )
