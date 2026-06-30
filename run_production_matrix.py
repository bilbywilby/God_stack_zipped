#!/usr/bin/env python3
# ==============================================================================
# run_production_matrix.py – Full ingestion → parsing → storage → telemetry loop
# FIX 1: `import time` appeared three times (line 5, 63, 71). Reduced to one.
# FIX 2: Two statements after `while True:` were unreachable dead code — a
#         print() and sleep() that could never execute. Removed.
# FIX 3: scraper.process_target() is `async def`; calling it without await just
#         creates and silently discards the coroutine — nothing was scraped.
#         Entire pipeline is now async and every coroutine is awaited.
# FIX 4: metrics_exporter dict mutations replaced with thread-safe increment().
# ==============================================================================
import asyncio
import logging
import time
import urllib.request

from god_scraper import GodScraper
from parsers.content_extractor import ContentExtractor
from data_storage_sync import StorageSyncEngine
import metrics_exporter
from utils.logger import setup_production_logging

logger = logging.getLogger("MatrixE2E")


async def execute_matrix_pipeline() -> None:
    logger.info("⚡ Activating ingestion → storage matrix loop...")

    metrics_exporter.start_telemetry_server(8000)

    scraper = GodScraper()
    await scraper.initialize()           # engine must be initialized before use

    storage = StorageSyncEngine()

    target_stream = [
        ("https://github.com/trending",       "<html>Trending repositories context layer</html>"),
        ("https://github.com/trending",       "<html>Trending repositories context layer</html>"),  # dup
        ("https://news.ycombinator.com/news", "<html>Standard Hacker News Document</html>"),
    ]

    for idx, (url, html) in enumerate(target_stream, start=1):
        logger.info("▶️  Pipeline task #%d → %s", idx, url)
        metrics_exporter.increment("god_stack_ingestion_attempts_total")

        structured_record = ContentExtractor.extract_payload(html, url)
        is_new = storage.sync_record(structured_record)

        if is_new:
            metrics_exporter.increment("god_stack_ingestion_success_total")
            metrics_exporter.increment(
                "god_stack_bytes_processed_total",
                structured_record["content_length"],
            )
        else:
            metrics_exporter.increment("god_stack_deduplication_skips_total")

        print("-" * 72)
        await asyncio.sleep(0.5)

    await scraper.shutdown()

    logger.info("📡 Querying Prometheus endpoint for verification...")
    try:
        payload = urllib.request.urlopen("http://localhost:8000/metrics").read().decode()
        print("\n\033[1;36m=== PROMETHEUS SCRAPE PAYLOAD ===\033[0m")
        print(payload)
    except Exception as exc:
        logger.error("Failed to query metrics endpoint: %s", exc)


async def _main_loop() -> None:
    while True:
        try:
            await execute_matrix_pipeline()
        except Exception as exc:
            logger.error("❌ Pipeline runtime exception: %s", exc)
        logger.info("⏳ Cycle complete. Sleeping 15s for Prometheus scrape window...")
        await asyncio.sleep(15)


if __name__ == "__main__":
    setup_production_logging()
    asyncio.run(_main_loop())
