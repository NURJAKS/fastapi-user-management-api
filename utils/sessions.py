import os
import secrets
from datetime import datetime
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

SESSION_TTL = 60 * 60 * 24 * 7  # 7 дней

async def create_session(user_id: str):
    session_id = secrets.token_hex(32)
    key = f"session:{session_id}"

    await redis.hset(key, mapping={
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    })

    await redis.expire(key, SESSION_TTL)
    return session_id


async def get_session(session_id: str):
    key = f"session:{session_id}"
    data = await redis.hgetall(key)
    return data


async def delete_session(session_id: str):
    key = f"session:{session_id}"
    await redis.delete(key)
