import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.exceptions import ConflictError
from cloudbox_api.models.folder import Folder
from cloudbox_api.models.share import ResourceType
from cloudbox_api.models.user import User
from cloudbox_api.schemas.folder import FolderCreate, FolderMove, FolderUpdate
from cloudbox_api.services.activity import publish_activity_event
from cloudbox_api.services.share import delete_shares_for_resource


async def create(db: AsyncSession, owner: User, data: FolderCreate) -> Folder:
    if data.parent_id is not None:
        await _get_owned_folder(db, owner.id, data.parent_id)

    await _check_name_conflict(db, owner.id, data.parent_id, data.name)

    folder = Folder(
        name=data.name,
        owner_id=owner.id,
        parent_id=data.parent_id,
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    await publish_activity_event("folder.created", owner.id, "folder", folder.id, folder.name)
    return folder


async def list_folders(
    db: AsyncSession, owner: User, parent_id: uuid.UUID | None = None
) -> list[Folder]:
    query = select(Folder).where(
        Folder.owner_id == owner.id,
        Folder.parent_id == parent_id,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get(db: AsyncSession, owner_id: uuid.UUID, folder_id: uuid.UUID) -> Folder:
    return await _get_owned_folder(db, owner_id, folder_id)


async def update(
    db: AsyncSession, owner: User, folder_id: uuid.UUID, data: FolderUpdate
) -> Folder:
    folder = await _get_owned_folder(db, owner.id, folder_id)

    if data.name != folder.name:
        await _check_name_conflict(db, owner.id, folder.parent_id, data.name)
        folder.name = data.name
        await db.commit()
        await db.refresh(folder)
        await publish_activity_event("folder.renamed", owner.id, "folder", folder.id, folder.name)
    else:
        await db.commit()
        await db.refresh(folder)
    return folder


async def get_path(db: AsyncSession, owner_id: uuid.UUID, folder_id: uuid.UUID) -> list[Folder]:
    folder = await _get_owned_folder(db, owner_id, folder_id)
    path = [folder]

    current = folder
    while current.parent_id is not None:
        current = await _get_owned_folder(db, owner_id, current.parent_id)
        path.append(current)

    path.reverse()
    return path


async def move(
    db: AsyncSession, owner: User, folder_id: uuid.UUID, data: FolderMove
) -> Folder:
    folder = await _get_owned_folder(db, owner.id, folder_id)

    if data.parent_id is not None:
        if data.parent_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move a folder into itself",
            )

        target_parent = await _get_owned_folder(db, owner.id, data.parent_id)

        # Walk up from target to root to detect circular reference
        current = target_parent
        while current.parent_id is not None:
            if current.parent_id == folder_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a folder into one of its own descendants",
                )
            current = await _get_owned_folder(db, owner.id, current.parent_id)

    if data.parent_id != folder.parent_id:
        await _check_name_conflict(db, owner.id, data.parent_id, folder.name)
        folder.parent_id = data.parent_id
        await db.commit()
        await db.refresh(folder)
        await publish_activity_event("folder.moved", owner.id, "folder", folder.id, folder.name)

    return folder


async def delete(db: AsyncSession, owner_id: uuid.UUID, folder_id: uuid.UUID) -> None:
    folder = await _get_owned_folder(db, owner_id, folder_id)
    folder_name = folder.name
    folder_id_copy = folder.id

    await delete_shares_for_resource(db, ResourceType.FOLDER, folder.id)
    await db.delete(folder)
    await db.commit()
    await publish_activity_event("folder.deleted", owner_id, "folder", folder_id_copy, folder_name)


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


async def _check_name_conflict(
    db: AsyncSession,
    owner_id: uuid.UUID,
    parent_id: uuid.UUID | None,
    name: str,
) -> None:
    query = select(Folder).where(
        Folder.owner_id == owner_id,
        Folder.name == name,
    )
    if parent_id is None:
        query = query.where(Folder.parent_id.is_(None))
    else:
        query = query.where(Folder.parent_id == parent_id)

    result = await db.execute(query)
    if result.scalar_one_or_none() is not None:
        raise ConflictError("A folder with this name already exists here")
