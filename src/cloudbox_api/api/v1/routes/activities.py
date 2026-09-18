from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.dependencies.auth import get_current_user
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.models.user import User
from cloudbox_api.schemas.activity import ActivityResponse
from cloudbox_api.services import activity as activity_service

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/", response_model=list[ActivityResponse])
async def list_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityResponse]:
    return await activity_service.list_activities(db, current_user.id)
