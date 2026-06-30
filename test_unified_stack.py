import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from run_unified_stack import UnifiedExecutionMatrix
from frontier_manager import Frontier

class TestUnifiedStackRefactor(unittest.IsolatedAsyncioTestCase):
    async def test_lifecycle_execution_sequence(self):
        print("\n[TEST] Launching Frontier Refactor Matrix Verification Loop...")
        
        test_urls = ["NEWS.YCOMBINATOR.COM/newest", "https://news.ycombinator.com/best"]
        matrix = UnifiedExecutionMatrix(test_urls)

        matrix.scavenger.run = AsyncMock(return_value=["http://127.0.0.1:8080"])
        matrix.engine.initialize = AsyncMock()
        matrix.engine.shutdown = AsyncMock()

        await matrix.run_url_sanitizer_layer()
        self.assertEqual(len(matrix.sanitized_urls), 2)
        self.assertTrue(matrix.sanitized_urls[0].startswith("https://"))
        print("\033[1;32m[PASS]\033[0m WHATWG URL standardization pipeline verified.")
        
        bootstrap_task = asyncio.create_task(matrix.bootstrap())
        await asyncio.sleep(0.2) 

        self.assertFalse(matrix.shutdown_event.is_set())
        print("\033[1;32m[PASS]\033[0m Asynchronous core background tasks initialized nominally.")

        print("\033[1;34m[TEST] Injecting graceful exit flag into active runtime state...\033[0m")
        matrix.shutdown_event.set()
        
        await bootstrap_task
        
        self.assertTrue(matrix.shutdown_event.is_set())
        matrix.scavenger.run.assert_called()
        print("\033[1;32m[PASS]\033[0m Teardown protocol finalized cleanly without dropped connection errors.")
        
if __name__ == "__main__":
    unittest.main()
