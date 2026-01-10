import redis
import json
from ..config import settings

# Initialize Connection Pool
pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
client = redis.Redis(connection_pool=pool)

CACHE_TTL = 300  # 5 Minutes

def get_cache_key(user_id: int):
    return f"recs:user:{user_id}"

def get_cached_recommendations(user_id: int):
    """Try to get data from Redis. Returns List[Dict] or None."""
    try:
        key = get_cache_key(user_id)
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except redis.RedisError as e:
        print(f"⚠️ Redis Read Error: {e}")
        return None

def set_cached_recommendations(user_id: int, data: list):
    """Save recommendations to Redis with TTL."""
    try:
        key = get_cache_key(user_id)
        client.setex(key, CACHE_TTL, json.dumps(data))
    except redis.RedisError as e:
        print(f"⚠️ Redis Write Error: {e}")

def invalidate_user_cache(user_id: int):
    """Delete a user's cache (Used on Like/Unlike/Pref change)."""
    try:
        key = get_cache_key(user_id)
        client.delete(key)
        print(f"🗑️ Invalidated cache for User {user_id}")
    except redis.RedisError as e:
        print(f"⚠️ Redis Delete Error: {e}")