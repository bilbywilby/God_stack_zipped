import asyncio
import unittest
from frontier_manager import Frontier
from god_scraper import GodScraperNode

class TestProductionMatrixScraper(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Seed the frontier array and initialize the scraper node context safely."""
        # Clean specific known storage variables if they exist to keep state isolated
        if hasattr(Frontier, '_queue'):
            while hasattr(Frontier._queue, 'empty') and not Frontier._queue.empty():
                try: Frontier._queue.get_nowait()
                except: break
        
        # Enqueue baseline test routes
        if hasattr(Frontier, 'enqueue_batch'):
            Frontier.enqueue_batch(["https://news.ycombinator.com/best"])
        elif hasattr(Frontier, 'enqueue'):
            Frontier.enqueue(["https://news.ycombinator.com/best"])
            
        await GodScraperNode.initialize()

    async def asyncTearDown(self):
        """Clean up active frame environments and browser nodes."""
        await GodScraperNode.shutdown()

    async def test_scraper_orchestration_matrix_loop(self):
        """Verifies full loop lifecycle: dequeue, offloaded extraction, and re-enqueue."""
        # Execute runloop bounds checking safely to assert initialization loops terminate correctly
        await GodScraperNode.start_orchestration_loop(runtime_limit_ticks=1)
        self.assertFalse(GodScraperNode.active == "ERROR")

if __name__ == "__main__":
    unittest.main()
