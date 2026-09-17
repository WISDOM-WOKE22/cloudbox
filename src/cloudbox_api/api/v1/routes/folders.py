import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.dependencies.auth import get_current_user
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.models.user import User
from cloudbox_api.schemas.folder import (
    FolderCreate,
    FolderMove,
    FolderPathEntry,
    FolderResponse,
    FolderUpdate,
)
from cloudbox_api.services import folder as folder_service

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FolderResponse:
    folder = await folder_service.create(db, current_user, data)
    return folder


@router.get("/", response_model=list[FolderResponse])
async def list_folders(
    parent_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FolderResponse]:
    folders = await folder_service.list_folders(db, current_user, parent_id)
    return folders


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FolderResponse:
    folder = await folder_service.get(db, current_user.id, folder_id)
    return folder


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: uuid.UUID,
    data: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FolderResponse:
    folder = await folder_service.update(db, current_user, folder_id, data)
    return folder


@router.get("/{folder_id}/path", response_model=list[FolderPathEntry])
async def get_folder_path(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FolderPathEntry]:
    path = await folder_service.get_path(db, current_user.id, folder_id)
    return path


@router.post("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: uuid.UUID,
    data: FolderMove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FolderResponse:
    folder = await folder_service.move(db, current_user, folder_id, data)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await folder_service.delete(db, current_user.id, folder_id)
