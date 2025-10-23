import redis.asyncio as redis

from app.config import env

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


async def init_redis():
    """Initialize Redis connection pool."""
    global redis_client
    redis_client = await redis.from_url(
        env.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
