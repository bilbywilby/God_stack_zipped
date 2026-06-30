# ==============================================================================
# scavenger.py – Proxy harvest and live validation engine
# FIX: `if idx := ip.replace('.', '').isdigit()` — walrus operator assigns the
#      bool to `idx` (which is never used) and the condition is always True for
#      any non-empty string because bool is truthy.  The intent is to only
#      accept rows where the IP column is numeric (i.e. a real IP, not a header).
#      Replaced with a direct `if ip.replace('.', '').isdigit():` check.
# ==============================================================================
import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("Scavenger")


class ProxyScavenger:
    """Dynamically harvests and verifies public egress nodes."""

    def __init__(self) -> None:
        self.source_url = "https://free-proxy-list.net/"
        self.verified_proxies: list[str] = []

    async def harvest_raw_list(self) -> list[str]:
        """Parses raw proxy table blocks from public source grids."""
        logger.info("Infiltrating public proxy distribution matrix...")
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.source_url)
                if response.status_code != 200:
                    logger.error("Failed to harvest proxy list (HTTP %d).", response.status_code)
                    return []

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table")
            if not table:
                return []

            proxies: list[str] = []
            for row in table.find_all("tr")[1:]:
                tds = row.find_all("td")
                if len(tds) >= 2:
                    ip = tds[0].text.strip()
                    port = tds[1].text.strip()
                    if ip.replace(".", "").isdigit():   # was: walrus `if idx := ...`
                        proxies.append(f"http://{ip}:{port}")

            logger.info("Harvest complete. %d raw nodes extracted.", len(proxies))
            return proxies[:40]
        except Exception as exc:
            logger.error("Scavenger fault: %s", exc)
            return []

    async def verify_node(self, proxy_url: str) -> None:
        """Tests node latency against a secure reference endpoint."""
        try:
            async with httpx.AsyncClient(
                proxies={"all://": proxy_url}, timeout=2.5
            ) as client:
                res = await client.get("http://www.google.com")
                if res.status_code == 200:
                    logger.info("✅ Verified: %s", proxy_url)
                    self.verified_proxies.append(proxy_url)
        except Exception:
            pass

    async def run(self) -> list[str]:
        raw_list = await self.harvest_raw_list()
        if not raw_list:
            return ["http://192.168.1.50:3128"]  # fallback
        await asyncio.gather(*[self.verify_node(p) for p in raw_list])
        logger.info("Pool updated. %d responsive routes.", len(self.verified_proxies))
        return self.verified_proxies or ["http://192.168.1.50:3128"]


if __name__ == "__main__":
    asyncio.run(ProxyScavenger().run())
