from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.exceptions import ConflictError
from cloudbox_api.models.user import User
from cloudbox_api.schemas.user import UserUpdate


async def update(db: AsyncSession, user: User, update_data: UserUpdate) -> User:
    data = update_data.model_dump(exclude_unset=True)

    if not data:
        return user

    if "email" in data and data["email"] != user.email:
        result = await db.execute(select(User).where(User.email == data["email"]))
        if result.scalar_one_or_none() is not None:
            raise ConflictError("Email already registered")

    if "username" in data and data["username"] != user.username:
        result = await db.execute(select(User).where(User.username == data["username"]))
        if result.scalar_one_or_none() is not None:
            raise ConflictError("Username already taken")

    for field, value in data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user
