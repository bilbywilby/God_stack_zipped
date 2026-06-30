import asyncio
import logging
import time
from urllib.parse import urlparse
import httpx

logger = logging.getLogger("ConnectionPool")

class ConnectionPoolManager:
    def __init__(self):
        self._client = None
        self._domain_cooldowns = {}
        self.default_delay = 1.0  # Politeness cooldown threshold in seconds

    def init_pool(self, max_connections: int = 100, max_keepalive: int = 20):
        """Initializes the underlying HTTPX asynchronous client with strict limit parameters."""
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive
        )
        self._client = httpx.AsyncClient(limits=limits, timeout=30.0)
        logger.info(f"Asynchronous HTTP Pool deployed. Max Open Sockets: {max_connections} | Keep-Alive: {max_keepalive}")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self.init_pool()
        return self._client

    async def acquire_domain_slot(self, url: str):
        """Enforces a rigid politeness cadence on a per-host basis before allowing egress I/O."""
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return

        if not domain:
            return

        while True:
            now = time.time()
            next_allowed_time = self._domain_cooldowns.get(domain, 0)
            
            if now >= next_allowed_time:
                # Reserve slot immediately by sliding the cooldown window forward
                self._domain_cooldowns[domain] = now + self.default_delay
                break
            
            # Sleep out the remaining delay window to clear host threshold
            await asyncio.sleep(next_allowed_time - now)

    async def shutdown(self):
        if self._client:
            await self._client.aclose()
            logger.info("Connection pool closed cleanly.")

# Instantiate global singleton manager node
HttpPool = ConnectionPoolManager()
