# ==============================================================================
# god_scraper.py – Async scraping orchestrator with semaphore-bounded concurrency
#
# v2: wires in the resilience primitives ported from main (resilience/*.py).
# On main these modules existed as 100+ isolated demo scripts that were never
# imported by god_scraper.py, god_engine.py, or any orchestration loop — none
# of them actually protected anything. This version calls them on the real
# fetch path:
#   - SlidingRateLimiter: per-domain request pacing before every fetch
#   - ResilientRetryCircuit: full-jitter retry wrapping the fetch call
#   - ConcurrencyThrottleMatrix: shrinks/grows batch size from observed latency
#   - HighWatermarkLoadShedder: refuses new batches under simulated backpressure
#   - DeadLetterAuditStream: quarantines records that fail all retries
#   - AsymmetricPayloadBuffer: non-blocking disk flush of discovered link batches
# ==============================================================================
import asyncio
import logging
import time
from typing import List, Optional
from urllib.parse import urlparse

from frontier_manager import Frontier
from god_engine import GodEngineNode
from resilience import (
    AsymmetricPayloadBuffer,
    ConcurrencyThrottleMatrix,
    DeadLetterAuditStream,
    HighWatermarkLoadShedder,
    ResilientRetryCircuit,
    SlidingRateLimiter,
)

logger = logging.getLogger("GodScraper")


class GodScraper:
    def __init__(self, concurrency_limit: int = 10) -> None:
        self.concurrency_limit = concurrency_limit
        self._semaphore: Optional[asyncio.Semaphore] = None   # created in initialize()
        self.active = False

        # Resilience layer — instantiated here, not at import time, so any
        # event-loop-bound state stays inside a running loop.
        self._rate_limiter = SlidingRateLimiter(max_requests=5, window_seconds=1.0)
        self._retry_circuit = ResilientRetryCircuit(max_retries=3, base_delay=0.5, max_delay=4.0)
        self._concurrency_matrix = ConcurrencyThrottleMatrix(
            baseline_ceiling=concurrency_limit, absolute_floor=2
        )
        self._load_shedder = HighWatermarkLoadShedder(critical_threshold_pct=85.0)
        self._dead_letter = DeadLetterAuditStream()
        self._link_buffer = AsymmetricPayloadBuffer(
            flush_limit=50, dest_file="outputs/discovered_links.jsonl"
        )

    async def initialize(self) -> None:
        """Prepares worker matrices and underlying extraction dependencies."""
        self._semaphore = asyncio.Semaphore(self.concurrency_limit)
        logger.info("Initializing unified scraping engine runner sequence...")
        await GodEngineNode.initialize(headless=True)
        self.active = True
        logger.info("Scraper active. Concurrency ceiling: %d", self.concurrency_limit)

    async def _fetch_once(self, url: str) -> dict:
        """Single fetch attempt — what the retry circuit wraps."""
        result = await GodEngineNode.fetch_and_extract(url)
        if result["status"] != "SUCCESS":
            raise RuntimeError(f"Engine returned status={result['status']} for {url}")
        return result

    async def process_target(self, url: str) -> None:
        """Handles an isolated route extraction cycle with rate limiting, retry, and DLQ."""
        assert self._semaphore is not None, "Call initialize() before process_target()"
        async with self._semaphore:
            if not self.active:
                return

            domain = urlparse(url).netloc.lower()
            await self._rate_limiter.acquire(domain=domain)

            start = time.monotonic()
            try:
                result = await self._retry_circuit.execute_with_jitter(self._fetch_once, url)
            except Exception as exc:
                logger.error("All retries exhausted for %s: %s", url, exc)
                await self._dead_letter.route_async(
                    {"url": url}, violation_cause=f"FETCH_EXHAUSTED: {exc}"
                )
                return
            finally:
                elapsed_ms = (time.monotonic() - start) * 1000
                new_ceiling = self._concurrency_matrix.evaluate_performance_telemetry(elapsed_ms)
                # Live-adjust the semaphore's effective ceiling for the next batch.
                # (asyncio.Semaphore can't shrink safely mid-flight, so this value
                # is read by start_orchestration_loop to size the next batch.)
                self.concurrency_limit = new_ceiling

            discovered_links = result["extracted_data"]["links"]
            if discovered_links:
                logger.info(
                    "Discovered %d outbound routes from %s. Enqueuing...",
                    len(discovered_links), url,
                )
                Frontier.enqueue_batch(discovered_links)
                for link in discovered_links:
                    await self._link_buffer.ingest_payload({"source": url, "link": link})

    def _get_next_targets(self, batch_size: int = 5) -> List[str]:
        """Drains up to batch_size URLs from the Frontier."""
        return Frontier.get_queue(batch_size=batch_size)

    async def start_orchestration_loop(self, runtime_limit_ticks: Optional[int] = None) -> None:
        """Continually drains the Frontier until teardown, batch size driven by
        the adaptive concurrency matrix and gated by the load shedder."""
        logger.info("Entering operational extraction matrix runloop...")
        ticks = 0
        while self.active:
            if runtime_limit_ticks and ticks >= runtime_limit_ticks:
                logger.info("Tick threshold surpassed. Stopping runloop.")
                break

            # Simulated memory pressure proxy: queue depth as % of an assumed
            # 10,000-url soft ceiling. Replace with a real psutil reading if
            # available in the deployment environment.
            queue_depth = Frontier.stats()["queue_depth"]
            usage_pct = min(100.0, (queue_depth / 10_000) * 100.0)
            if not self._load_shedder.audit_ingest_safety(usage_pct):
                await asyncio.sleep(1.0)
                ticks += 1
                continue

            batch_size = max(2, self.concurrency_limit)
            next_targets = self._get_next_targets(batch_size=batch_size)
            if not next_targets:
                await asyncio.sleep(0.1)
                ticks += 1
                continue

            await asyncio.gather(*[
                asyncio.create_task(self.process_target(url)) for url in next_targets
            ])
            ticks += 1

    async def shutdown(self) -> None:
        """Terminates engine tasks, flushes buffers, and cleans workspace pipeline states."""
        logger.info("Executing graceful scraper teardown sequence...")
        self.active = False
        await self._link_buffer.flush_remaining()
        await GodEngineNode.shutdown()
        logger.info("Scraper core subsystem deactivated successfully.")


# NOTE: No module-level singleton instantiation here.  Callers that need a
# shared instance should create one inside their own async entry point after
# the event loop is running, then await .initialize().
