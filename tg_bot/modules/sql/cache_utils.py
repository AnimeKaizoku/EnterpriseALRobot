import redis
import json
from functools import wraps

from tg_bot import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True,
)


def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"

            cached_result = redis_client.get(key)
            if cached_result:
                return json.loads(cached_result)

            result = func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            return result

        return wrapper

    return decorator


def clear_cache():
    redis_client.flushdb()


def invalidate_cache_pattern(pattern):
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)
