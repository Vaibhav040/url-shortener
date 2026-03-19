import redis
import logging
from app.config import Settings


logger = logging.getLogger(__name__)

def get_redis_client():
    try:
        client = redis.Redis(
            host=Settings.redis_host,
            port=Settings.redis_port,
            decode_response=True,
            socket_connect_timeout=2,
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Reddis unavailable: {e}")
        return None
    
def get_cached_url(short_code: str) -> str | None:
    client = get_redis_client()
    if not client:
        return
    try:
        return client.get(f"url: {short_code}")
    except Exception:
        return None
    
def cache_url(short_code: str, original_url: str, ttl: int = 3600):
    client = get_redis_client()
    if not client:
        return
    try:
        client.setex(f"url: {short_code}", ttl, original_url)
    except Exception:
        pass

def invalidate_cache(short_code: str):
    client = get_redis_client()
    if not client:
        return
    try:
        client.delete(f"url: {short_code}")
    except Exception:
        pass