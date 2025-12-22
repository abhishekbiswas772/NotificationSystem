import redis
import os
from dotenv import load_dotenv

load_dotenv()

_redis_pool = None 

def get_redis_pool():
    global _redis_pool
    if _redis_pool is None:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("Redis url not found.")
        _redis_pool = redis.ConnectionPool.from_url(redis_url, max_connections = 10, decode_responses = True)
    return redis.Redis(connection_pool=_redis_pool)

            
