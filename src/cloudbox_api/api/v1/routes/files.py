import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.dependencies.auth import get_current_user
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.models.user import User
from cloudbox_api.schemas.file import (
    DownloadUrlResponse,
    FileCreate,
    FileMove,
    FileResponse,
    FileUpdate,
    UploadUrlResponse,
)
from cloudbox_api.services import file as file_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    data: FileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    file = await file_service.create(db, current_user, data)
    return file


@router.get("/", response_model=list[FileResponse])
async def list_files(
    folder_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FileResponse]:
    files = await file_service.list_files(db, current_user, folder_id)
    return files


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    file = await file_service.get(db, current_user.id, file_id)
    return file


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: uuid.UUID,
    data: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    file = await file_service.update(db, current_user.id, file_id, data)
    return file


@router.post("/{file_id}/move", response_model=FileResponse)
async def move_file(
    file_id: uuid.UUID,
    data: FileMove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    file = await file_service.move(db, current_user, file_id, data)
    return file


@router.post("/{file_id}/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadUrlResponse:
    return await file_service.get_upload_url(db, current_user.id, file_id)


@router.post("/{file_id}/confirm-upload", response_model=FileResponse)
async def confirm_upload(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await file_service.confirm_upload(db, current_user.id, file_id)


@router.get("/{file_id}/download-url", response_model=DownloadUrlResponse)
async def get_download_url(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DownloadUrlResponse:
    return await file_service.get_download_url(db, current_user.id, file_id)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await file_service.delete(db, current_user.id, file_id)
