from redis.asyncio import Redis

from cloudbox_api.core.config import settings

redis_client: Redis | None = None


async def init_redis() -> None:
    global redis_client
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
    except Exception:
        redis_client = None


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> Redis | None:
    return redis_client
