import asyncio
import logging
from scavenger import ProxyScavenger
from god_scraper import GodScraper
from utils.logger import setup_production_logging

logger = logging.getLogger("TestRunner")

async def run_stealth_validation():
    print("\n\033[1;36m[STEP 1]\033[0m Harvesting fresh egress node from Scavenger matrix...")
    scavenger = ProxyScavenger()
    proxies = await scavenger.run()
    
    if not proxies:
        logger.error("No active proxy nodes returned. Aborting stealth run.")
        return
        
    target_proxy = proxies[0]
    logger.info(f"Locking targeting vector to Egress Node: {target_proxy}")

    print("\n\033[1;36m[STEP 2]\033[0m Spinning up GodScraper with high_privacy_profile & Proxy...")
    scraper = GodScraper(profile_name="high_privacy_profile")
    
    # Clean execution using the native initialize framework
    await scraper.initialize(headless=True, proxy_url=target_proxy)
    page = await scraper.context.new_page()
    
    print("\n\033[1;36m[STEP 3]\033[0m Validating fingerprint leakage at httpbin.org...")
    try:
        await page.goto("https://httpbin.org/ip", timeout=15000)
        content = await page.inner_text("body")
        logger.info(f"\033[1;32m[NODE TRACE CONFIRMED]\033[0m Exposed IP data reads: {content.strip()}")
    except Exception as e:
        logger.warning(f"Connection through proxy timed out or failed: {e}")
    finally:
        await scraper.shutdown()

if __name__ == "__main__":
    setup_production_logging()
    asyncio.run(run_stealth_validation())
