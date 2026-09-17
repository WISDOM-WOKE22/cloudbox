from fastapi import APIRouter
from sqlalchemy import text

from cloudbox_api.core.config import settings
from cloudbox_api.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "version": settings.VERSION,
        "db": db_status,
    }
