from fastapi import HTTPException, Request, status

from app.db.redis_cilent import get_redis


async def rate_limit(
    request: Request,
    max_requests: int = 100,
    timeframe_seconds: int = 60,
    key_prefix: str = "rate_limit",
):
    client_id = (
        request.client.host
        if request.client
        else request.headers.get("X-Forwarded-For", "unknown")
    )

    key = f"{key_prefix}:{client_id}"

    redis_client = await get_redis()

    current = await redis_client.get(key)

    if current is None:
        await redis_client.setex(key, timeframe_seconds, 1)
        return

    if int(current) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )

    await redis_client.incr(key)
