import json
import uuid

from cloudbox_api.core.config import settings
from cloudbox_api.core.redis import get_redis


def _user_cache_key(user_id: uuid.UUID) -> str:
    return f"user:{user_id}"


async def get_cached_user(user_id: uuid.UUID) -> dict | None:
    redis = get_redis()
    if redis is None:
        return None

    try:
        data = await redis.get(_user_cache_key(user_id))
        if data is not None:
            return json.loads(data)
    except Exception:
        pass

    return None


async def cache_user(user_id: uuid.UUID, user_data: dict) -> None:
    redis = get_redis()
    if redis is None:
        return

    try:
        await redis.set(
            _user_cache_key(user_id),
            json.dumps(user_data, default=str),
            ex=settings.CACHE_USER_TTL_SECONDS,
        )
    except Exception:
        pass


async def invalidate_user_cache(user_id: uuid.UUID) -> None:
    redis = get_redis()
    if redis is None:
        return

    try:
        await redis.delete(_user_cache_key(user_id))
    except Exception:
        pass
