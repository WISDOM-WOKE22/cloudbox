from fastapi import HTTPException, Request, status

from cloudbox_api.core.config import settings
from cloudbox_api.core.redis import get_redis


async def check_login_rate_limit(request: Request) -> None:
    redis = get_redis()
    if redis is None:
        return  # No rate limiting if Redis is unavailable

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate:login:{client_ip}"

    try:
        count = await redis.incr(key)

        if count == 1:
            await redis.expire(key, settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS)

        if count > settings.RATE_LIMIT_LOGIN_MAX:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {ttl} seconds.",
                headers={"Retry-After": str(ttl)},
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Fail open — allow request if Redis errors
