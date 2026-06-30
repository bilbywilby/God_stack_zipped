# ==============================================================================
# G.O.D. STACK ORCHESTRATOR (run_god_stack.py)
# Architecture: Unified Pipeline bridging Scavenger, Sanitizer, and Engine
# ==============================================================================

import asyncio
import logging
from scavenger import ProxyScavenger
from url_sanitizer import UrlSanitizer
from utils.logger import setup_production_logging
# Assuming god_engine is patched to accept proxies in its matrix
from god_engine import GodEngine 

 # Suppress lower level logs for clean UI
logger = logging.getLogger("MasterOrchestrator")

class GodStackPipeline:
    def __init__(self):
        self.scavenger = ProxyScavenger(max_concurrent_checks=12)
        self.engine = GodEngine()
        self.active_proxies = []

    async def execute_pipeline(self, raw_targets: list):
        """Runs the complete end-to-end data extraction lifecycle."""
        # 1. Sanitize Inputs
        clean_targets = [UrlSanitizer.normalize(url) for url in raw_targets]
        clean_targets = [url for url in clean_targets if url]
        
        # 2. Scavenge Egress Routes
        self.active_proxies = await self.scavenger.run()
        
        # 3. Execute Extraction Matrix
        if not self.active_proxies:
            logger.error("No proxies secured. Running on local IP...")
        
        # Pass targets to the engine (engine would be adapted to use self.active_proxies)
        self.engine.process_target_array(clean_targets)
        return True

if __name__ == "__main__":
    setup_production_logging()
    targets = [
        "https://news.ycombinator.com/front?utm_source=tracker",
        "//news.ycombinator.com/newest"
    ]
    pipeline = GodStackPipeline()
    asyncio.run(pipeline.execute_pipeline(targets))
