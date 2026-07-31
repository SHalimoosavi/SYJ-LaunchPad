from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database(db: AsyncSession) -> str:
    try:
        await db.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        return "unavailable"
