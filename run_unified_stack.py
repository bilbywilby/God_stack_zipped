import asyncio
import logging
from frontier_manager import Frontier
from url_sanitizer import UrlSanitizer
from scavenger import ProxyScavenger
from god_scraper import GodScraper
from connection_pool import HttpPool
from parsers.html_parser import parse_html
from utils.logger import setup_production_logging

logger = logging.getLogger("MatrixCore")

class UnifiedExecutionMatrix:
    def __init__(self, target_urls: list):
        self.shutdown_event = asyncio.Event()
        self.sanitized_urls = []
        self.raw_urls = target_urls
        self.scavenger = ProxyScavenger()
        self.engine = GodScraper()

    async def run_url_sanitizer_layer(self):
        logger.info("[SANITIZER] Initializing structural target validation matrix...")
        valid_pool = []
        for url in self.raw_urls:
            normalized = UrlSanitizer.normalize(url)
            if normalized:
                valid_pool.append(normalized)
        self.sanitized_urls = valid_pool
        
        Frontier.enqueue_batch(self.sanitized_urls)
        logger.info(f"[SANITIZER] Target alignment complete. Secured {len(self.sanitized_urls)} production routes.")

    async def bootstrap(self):
        await self.run_url_sanitizer_layer()
        
        HttpPool.init_pool(max_connections=50, max_keepalive=10)
        await self.scavenger.run()
        await self.engine.initialize(headless=True)

        loop = asyncio.get_running_loop()

        while not self.shutdown_event.is_set():
            url = Frontier.dequeue()
            if not url:
                logger.info("Frontier target queues depleted. Pausing runtime loops.")
                break
                
            await HttpPool.acquire_domain_slot(url)
            logger.info(f"[ENGINE] Firing extraction matrix sequences across active hotpaths for: {url}")
            
            # Simulated target HTML document frame payload context returned from target URL
            simulated_payload = f"<html><head><title>Hacker News Refactor Data</title></head><body><article><p>Production pipeline analysis processing loop for {url}.</p></article><a href='https://news.ycombinator.com/item?id=42'>Deep Link discovery</a></body></html>"
            
            # Offload heavy parsing actions completely to an unblocking background thread-pool executor
            extracted_data = await loop.run_in_executor(None, parse_html, simulated_payload)
            
            logger.info(f"[PARSER-OUT] Successfully Extracted Title: '{extracted_data['title']}'")
            logger.info(f"[PARSER-OUT] Discovered Extracted Secondary Anchors: {extracted_data['links']}")
            
            # Feed newly discovered extraction pipeline links directly back into the dynamic frontier manager
            if extracted_data['links']:
                Frontier.enqueue_batch(extracted_data['links'])

            stats = Frontier.stats()
            logger.info(f"[METRICS] Live Stats Matrix Queue Depth: {stats['queue_depth']} | Dequeue Operations: {stats['frontier.dequeue']}")
            
            await asyncio.sleep(0.01)

        await self.teardown()

    async def teardown(self):
        logger.info("Closing active tasks and tearing down network context structures...")
        await self.engine.shutdown()
        await HttpPool.shutdown()
        logger.info("[SUCCESS] Refactor matrix lifecycle execution complete. Workspace clean.")

async def main():
    test_urls = ["NEWS.YCOMBINATOR.COM/newest", "https://news.ycombinator.com/best"]
    matrix = UnifiedExecutionMatrix(test_urls)
    await matrix.bootstrap()

if __name__ == "__main__":
    setup_production_logging()
    asyncio.run(main())
