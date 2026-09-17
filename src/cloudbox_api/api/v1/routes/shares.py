import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.dependencies.auth import get_current_user
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.models.share import ResourceType
from cloudbox_api.models.user import User
from cloudbox_api.schemas.share import ShareCreate, ShareResponse, ShareUpdate
from cloudbox_api.services import share as share_service

router = APIRouter(tags=["shares"])


# ── File shares ──────────────────────────────────────────────


@router.post(
    "/files/{file_id}/shares",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_file_share(
    file_id: uuid.UUID,
    data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    share = await share_service.create_share(
        db, current_user, ResourceType.FILE, file_id, data
    )
    return share


@router.get("/files/{file_id}/shares", response_model=list[ShareResponse])
async def list_file_shares(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ShareResponse]:
    return await share_service.list_shares(
        db, current_user.id, ResourceType.FILE, file_id
    )


@router.patch("/files/{file_id}/shares/{share_id}", response_model=ShareResponse)
async def update_file_share(
    file_id: uuid.UUID,
    share_id: uuid.UUID,
    data: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    return await share_service.update_share(
        db, current_user.id, ResourceType.FILE, file_id, share_id, data
    )


@router.delete(
    "/files/{file_id}/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_file_share(
    file_id: uuid.UUID,
    share_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await share_service.delete_share(
        db, current_user.id, ResourceType.FILE, file_id, share_id
    )


# ── Folder shares ───────────────────────────────────────────


@router.post(
    "/folders/{folder_id}/shares",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_folder_share(
    folder_id: uuid.UUID,
    data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    share = await share_service.create_share(
        db, current_user, ResourceType.FOLDER, folder_id, data
    )
    return share


@router.get("/folders/{folder_id}/shares", response_model=list[ShareResponse])
async def list_folder_shares(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ShareResponse]:
    return await share_service.list_shares(
        db, current_user.id, ResourceType.FOLDER, folder_id
    )


@router.patch(
    "/folders/{folder_id}/shares/{share_id}", response_model=ShareResponse
)
async def update_folder_share(
    folder_id: uuid.UUID,
    share_id: uuid.UUID,
    data: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    return await share_service.update_share(
        db, current_user.id, ResourceType.FOLDER, folder_id, share_id, data
    )


@router.delete(
    "/folders/{folder_id}/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_folder_share(
    folder_id: uuid.UUID,
    share_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await share_service.delete_share(
        db, current_user.id, ResourceType.FOLDER, folder_id, share_id
    )
