import uuid
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.cache import cache_user, get_cached_user
from cloudbox_api.core.security import decode_access_token
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _user_from_cache(cached: dict) -> User:
    return User(
        id=uuid.UUID(cached["id"]),
        email=cached["email"],
        username=cached["username"],
        is_active=cached["is_active"],
        hashed_password="",
        created_at=datetime.fromisoformat(cached["created_at"]),
        updated_at=datetime.fromisoformat(cached["updated_at"]),
    )


def _user_to_cache(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Try cache first
    cached = await get_cached_user(uuid.UUID(user_id))
    if cached is not None:
        user = _user_from_cache(cached)
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
            )
        return user

    # Cache miss — query database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    await cache_user(user.id, _user_to_cache(user))

    return user
