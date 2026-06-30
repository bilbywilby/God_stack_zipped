import logging
import threading
from collections import deque
from urllib.parse import urlparse
from courlan_router import CourlanRouter

logger = logging.getLogger("FrontierManager")


class FrontierManager:
    """
    NOTE: on a later main-branch snapshot, `Frontier = FrontierManager` aliased
    the bare class (not an instance), so `Frontier.enqueue_batch(urls)` silently
    passed `urls` as `self`. `Frontier.add_url()` and `Frontier.get_queue()`
    were also called from several callers but never defined on this class.
    Fixed: instantiated correctly at the bottom of this file, add_url() added
    as a convenience wrapper, and a threading.Lock added since the resilience
    layer now drives concurrent producers into this structure.
    """

    def __init__(self) -> None:
        self.seen_urls: set[str] = set()
        self.domain_buckets: dict[str, deque] = {}
        self.domain_order: deque = deque()
        self._lock = threading.Lock()
        self._metrics = {
            "frontier.enqueue": 0,
            "frontier.dequeue": 0,
            "frontier.trap_dropped": 0,
        }

    def add_url(self, url: str) -> None:
        """Single-URL convenience wrapper — referenced by callers but never defined."""
        self.enqueue_batch([url])

    def enqueue_batch(self, urls: list) -> None:
        with self._lock:
            for raw_url in urls:
                if not raw_url:
                    continue

                cleaned_url = CourlanRouter.validate_and_clean(raw_url)
                if not cleaned_url:
                    self._metrics["frontier.trap_dropped"] += 1
                    continue

                if cleaned_url in self.seen_urls:
                    continue

                try:
                    parsed = urlparse(cleaned_url)
                    domain = parsed.netloc.lower()
                    if not domain:
                        continue
                except Exception:
                    continue

                self.seen_urls.add(cleaned_url)
                if domain not in self.domain_buckets:
                    self.domain_buckets[domain] = deque()
                    self.domain_order.append(domain)

                self.domain_buckets[domain].append(cleaned_url)
                self._metrics["frontier.enqueue"] += 1

            logger.info(
                "Frontier sync complete. Active Domain Queues: %d | Seen Register: %d",
                len(self.domain_buckets), len(self.seen_urls),
            )

    def dequeue(self) -> str:
        with self._lock:
            if not self.domain_order:
                return ""

            target_domain = self.domain_order[0]
            bucket = self.domain_buckets[target_domain]

            url = bucket.popleft()
            self._metrics["frontier.dequeue"] += 1

            if not bucket:
                del self.domain_buckets[target_domain]
                self.domain_order.popleft()
            else:
                self.domain_order.rotate(-1)

            return url

    def get_queue(self, batch_size: int = 10) -> list[str]:
        """Drains up to batch_size URLs. Referenced by callers but never defined on main."""
        drained: list[str] = []
        for _ in range(batch_size):
            url = self.dequeue()
            if not url:
                break
            drained.append(url)
        return drained

    def stats(self) -> dict:
        with self._lock:
            return {
                **self._metrics,
                "queue_depth": sum(len(b) for b in self.domain_buckets.values()),
                "unique_domains_cached": len(self.domain_buckets),
            }

    def flush(self) -> None:
        with self._lock:
            self.domain_buckets.clear()
            self.domain_order.clear()


# Instantiated here — was `Frontier = FrontierManager` (bare class) on main,
# which made every Frontier.method(...) call pass its first arg as `self`.
Frontier = FrontierManager()
