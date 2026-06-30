# ==============================================================================
# god_engine.py – Core async extraction engine
# FIX: parse_html() now accepts a base_url parameter for resolving relative links.
#      Passed the target url through so the Frontier receives absolute hrefs.
# ==============================================================================
import asyncio
import logging
from typing import Any, Dict, Optional

from parsers.html_parser import parse_html, MAX_PAYLOAD_BYTES

logger = logging.getLogger("GodEngine")


class GodEngine:
    def __init__(self) -> None:
        self.initialized = False

    async def initialize(self, headless: bool = True) -> None:
        logger.info("Initializing extraction engine (Headless: %s)...", headless)
        self.initialized = True
        logger.info("Engine context stabilized.")

    async def fetch_and_extract(
        self,
        url: str,
        raw_html_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.initialized:
            raise RuntimeError("Call initialize() before fetch_and_extract().")

        logger.info("Processing extraction sequence for: %s", url)

        html_payload = raw_html_content or (
            f"<html><head><title>Stream for {url}</title></head>"
            f"<body><main><p>Matrix operating nominally.</p></main>"
            f"<a href='https://news.ycombinator.com/item?id=99'>Thread</a></body></html>"
        )

        payload_size = len(html_payload)
        if payload_size > MAX_PAYLOAD_BYTES:
            logger.warning("Payload %d bytes exceeds ceiling. Aborting.", payload_size)
            return {
                "url": url,
                "status": "ABORTED_CEILING_EXCEEDED",
                "extracted_data": {"title": None, "body": "", "links": []},
            }

        loop = asyncio.get_running_loop()
        # Pass url as base_url so relative hrefs are resolved to absolute
        extracted_frame = await loop.run_in_executor(
            None, lambda: parse_html(html_payload, base_url=url)
        )

        logger.info(
            "Extraction complete. Title: '%s' | Links: %d",
            extracted_frame["title"], len(extracted_frame["links"]),
        )

        return {
            "url": url,
            "status": "SUCCESS",
            "metrics": {
                "payload_bytes": payload_size,
                "discovered_anchors_count": len(extracted_frame["links"]),
            },
            "extracted_data": extracted_frame,
        }

    async def shutdown(self) -> None:
        logger.info("Tearing down extraction engine...")
        self.initialized = False
        logger.info("Engine deactivated.")


# Singleton — instantiated here (no Semaphore, safe at import time)
GodEngineNode = GodEngine()
