import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.exceptions import ConflictError
from cloudbox_api.models.file import File
from cloudbox_api.models.folder import Folder
from cloudbox_api.models.share import Permission, ResourceType, Share
from cloudbox_api.models.user import User
from cloudbox_api.schemas.share import ShareCreate, ShareUpdate


async def create_share(
    db: AsyncSession,
    owner: User,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    data: ShareCreate,
) -> Share:
    await _verify_resource_ownership(db, owner.id, resource_type, resource_id)

    if data.shared_with_id == owner.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share a resource with yourself",
        )

    # Verify target user exists
    result = await db.execute(select(User).where(User.id == data.shared_with_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check for existing share
    result = await db.execute(
        select(Share).where(
            Share.resource_type == resource_type.value,
            Share.resource_id == resource_id,
            Share.shared_with_id == data.shared_with_id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise ConflictError("Resource is already shared with this user")

    share = Share(
        resource_type=resource_type.value,
        resource_id=resource_id,
        owner_id=owner.id,
        shared_with_id=data.shared_with_id,
        permission=data.permission.value,
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


async def list_shares(
    db: AsyncSession,
    owner_id: uuid.UUID,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
) -> list[Share]:
    await _verify_resource_ownership(db, owner_id, resource_type, resource_id)

    result = await db.execute(
        select(Share).where(
            Share.resource_type == resource_type.value,
            Share.resource_id == resource_id,
        )
    )
    return list(result.scalars().all())


async def update_share(
    db: AsyncSession,
    owner_id: uuid.UUID,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    share_id: uuid.UUID,
    data: ShareUpdate,
) -> Share:
    share = await _get_owned_share(
        db, owner_id, resource_type, resource_id, share_id
    )
    share.permission = data.permission.value
    await db.commit()
    await db.refresh(share)
    return share


async def delete_share(
    db: AsyncSession,
    owner_id: uuid.UUID,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    share_id: uuid.UUID,
) -> None:
    share = await _get_owned_share(
        db, owner_id, resource_type, resource_id, share_id
    )
    await db.delete(share)
    await db.commit()


async def delete_shares_for_resource(
    db: AsyncSession, resource_type: ResourceType, resource_id: uuid.UUID
) -> None:
    await db.execute(
        delete(Share).where(
            Share.resource_type == resource_type.value,
            Share.resource_id == resource_id,
        )
    )


async def _verify_resource_ownership(
    db: AsyncSession,
    owner_id: uuid.UUID,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
) -> None:
    if resource_type == ResourceType.FILE:
        model = File
    else:
        model = Folder

    result = await db.execute(
        select(model).where(model.id == resource_id, model.owner_id == owner_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type.value.capitalize()} not found",
        )


async def _get_owned_share(
    db: AsyncSession,
    owner_id: uuid.UUID,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    share_id: uuid.UUID,
) -> Share:
    await _verify_resource_ownership(db, owner_id, resource_type, resource_id)

    result = await db.execute(
        select(Share).where(
            Share.id == share_id,
            Share.resource_type == resource_type.value,
            Share.resource_id == resource_id,
        )
    )
    share = result.scalar_one_or_none()
    if share is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )
    return share
