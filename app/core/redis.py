# app/core/redis.py
import asyncio
from typing import Optional
from redis.asyncio import Redis, from_url
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Fallback in-memory cache for development without active Redis
class InMemoryRedis:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._ttls: dict[str, float] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._store[key] = value
        return True

    async def setex(self, key: str, time: int, value: str) -> bool:
        self._store[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def ping(self) -> bool:
        return True

_redis_client: Optional[Redis | InMemoryRedis] = None

async def get_redis() -> Redis | InMemoryRedis:
    global _redis_client
    if _redis_client is None:
        try:
            client = from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            await asyncio.wait_for(client.ping(), timeout=1.0)
            _redis_client = client
            logger.info("Connexion Redis établie avec succès")
        except Exception as e:
            logger.warning("Redis non disponible, basculement en mode In-Memory pour le cache local", error=str(e))
            _redis_client = InMemoryRedis()
    return _redis_client

