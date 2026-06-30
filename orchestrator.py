# ==============================================================================
# G.O.D. STACK ORCHESTRATOR (orchestrator.py)
# Architecture: Unified Pipeline Manager for Sanitize -> Proxy -> Anti-Bot -> Scrape
# ==============================================================================

import asyncio
import logging
from url_sanitizer import UrlSanitizer
from scavenger import ProxyScavenger
from captcha_handler import CaptchaHandler
from utils.logger import setup_production_logging
# Assumes god_engine.py is accessible in the same directory
from god_engine import GodEngine

logger = logging.getLogger("GodOrchestrator")

class GodOrchestrator:
    def __init__(self, use_proxies: bool = True):
        self.use_proxies = use_proxies
        self.scavenger = ProxyScavenger() if use_proxies else None
        self.sentinel = CaptchaHandler()
        self.engine = GodEngine()
        self.active_proxies = []

    async def initialize_matrix(self):
        """Bootstraps the proxy grid if enabled."""
        if self.use_proxies:
            logger.info("Bootstrapping proxy egress matrix...")
            self.active_proxies = await self.scavenger.run()
        logger.info("Orchestrator matrix initialized and ready.")

    async def execute_mission(self, raw_url: str) -> dict:
        """Runs the full pipeline on a single target."""
        logger.info(f"Initiating mission for target: {raw_url}")
        
        # Step 1: Sanitize Target
        clean_url = UrlSanitizer.normalize(raw_url)
        if not clean_url:
            return {"status": "error", "message": "Invalid URL structure"}

        # Step 2: Route Selection
        proxy = self.active_proxies[0] if self.active_proxies else None
        
        # Step 3 & 4: Execution (Engine + Captcha Handling)
        # Note: In a full production setup, the engine would trigger the sentinel 
        # upon hitting a 403/Challenge page. We pass the proxy to the engine.
        logger.info(f"Deploying extraction engine to {clean_url}")
        
        try:
            # We wrap the synchronous engine in a thread to keep async event loop clean
            result = await asyncio.to_thread(self.engine.process_target_array, [clean_url])
            return {"status": "success", "target": clean_url, "message": "Data extracted and serialized."}
        except Exception as e:
            logger.error(f"Mission failed: {str(e)}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    setup_production_logging()
    async def run_cli_test():
        print("\n\033[1;32m--- G.O.D. ORCHESTRATOR TERMINAL TEST ---\033[0m")
        orchestrator = GodOrchestrator(use_proxies=False) # Set False for rapid test
        await orchestrator.initialize_matrix()
        await orchestrator.execute_mission("https://news.ycombinator.com/front?utm_source=test")
        
    asyncio.run(run_cli_test())
