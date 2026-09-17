import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.models.file import File
from cloudbox_api.models.folder import Folder
from cloudbox_api.models.share import ResourceType
from cloudbox_api.models.user import User
from cloudbox_api.schemas.file import FileCreate, FileMove, FileUpdate
from cloudbox_api.services.share import delete_shares_for_resource


async def create(db: AsyncSession, owner: User, data: FileCreate) -> File:
    if data.folder_id is not None:
        await _get_owned_folder(db, owner.id, data.folder_id)

    file = File(
        name=data.name,
        owner_id=owner.id,
        folder_id=data.folder_id,
        mime_type=data.mime_type,
        size=data.size,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def list_files(
    db: AsyncSession, owner: User, folder_id: uuid.UUID | None = None
) -> list[File]:
    query = select(File).where(
        File.owner_id == owner.id,
        File.folder_id == folder_id,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get(db: AsyncSession, owner_id: uuid.UUID, file_id: uuid.UUID) -> File:
    return await _get_owned_file(db, owner_id, file_id)


async def update(
    db: AsyncSession, owner_id: uuid.UUID, file_id: uuid.UUID, data: FileUpdate
) -> File:
    file = await _get_owned_file(db, owner_id, file_id)

    if data.name != file.name:
        file.name = data.name

    await db.commit()
    await db.refresh(file)
    return file


async def move(
    db: AsyncSession, owner: User, file_id: uuid.UUID, data: FileMove
) -> File:
    file = await _get_owned_file(db, owner.id, file_id)

    if data.folder_id is not None:
        await _get_owned_folder(db, owner.id, data.folder_id)

    if data.folder_id != file.folder_id:
        file.folder_id = data.folder_id
        await db.commit()
        await db.refresh(file)

    return file


async def delete(db: AsyncSession, owner_id: uuid.UUID, file_id: uuid.UUID) -> None:
    file = await _get_owned_file(db, owner_id, file_id)
    await delete_shares_for_resource(db, ResourceType.FILE, file.id)
    await db.delete(file)
    await db.commit()


async def _get_owned_file(
    db: AsyncSession, owner_id: uuid.UUID, file_id: uuid.UUID
) -> File:
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == owner_id)
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return file


async def _get_owned_folder(
    db: AsyncSession, owner_id: uuid.UUID, folder_id: uuid.UUID
) -> Folder:
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.owner_id == owner_id)
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    return folder
