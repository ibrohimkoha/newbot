import redis.asyncio as redis
from datetime import datetime


async def get_today_key(user_id: int):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f"user:{user_id}:{today}"