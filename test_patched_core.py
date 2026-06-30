import asyncio
import unittest
from god_engine import GodEngineNode

class TestPatchedCoreEngine(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Bootstrap the singleton node context."""
        await GodEngineNode.initialize(headless=True)

    async def asyncTearDown(self):
        """Clean up active frame environments."""
        await GodEngineNode.shutdown()

    async def test_engine_extraction_hotpath(self):
        """Validates successful engine processing extraction pipeline loop."""
        target_url = "https://news.ycombinator.com/best"
        payload = (
            "<html><head><title>Hacker News Test Core</title></head>"
            "<body><article><p>Refactored execution matrix validation output.</p></article>"
            "<a href='https://news.ycombinator.com/item?id=1337'>Target deep link match</a></body></html>"
        )
        
        response = await GodEngineNode.fetch_and_extract(target_url, raw_html_content=payload)
        
        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["extracted_data"]["title"], "Hacker News Test Core")
        self.assertIn("https://news.ycombinator.com/item?id=1337", response["extracted_data"]["links"])
        self.assertEqual(response["metrics"]["discovered_anchors_count"], 1)

    async def test_payload_ceiling_guard(self):
        """Ensures massive strings trigger the payload threshold defensive abort boundary."""
        target_url = "https://news.ycombinator.com/overload"
        # Generate an oversized payload exceeding the MAX_PAYLOAD_BYTES constraint limits
        massive_payload = "<html>" + ("<p>Flood text tracking data layer...</p>" * 150000) + "</html>"
        
        response = await GodEngineNode.fetch_and_extract(target_url, raw_html_content=massive_payload)
        self.assertEqual(response["status"], "ABORTED_CEILING_EXCEEDED")
        self.assertIsNone(response["extracted_data"]["title"])

if __name__ == "__main__":
    unittest.main()
