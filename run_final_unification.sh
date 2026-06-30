#!/usr/bin/env bash
# ==============================================================================
# FINAL PRODUCTION UNIFICATION (run_final_unification.sh)
# Architecture: Syncing Core APIs, Proxy Handlers, and VFS Parsers
# ==============================================================================
set -euo pipefail

BLUE="\033[1;34m"
GREEN="\033[1;32m"
RESET="\033[0m"

echo -e "${BLUE}[1/3] Patching VFS Orchestrator for dynamic JSON parsing...${RESET}"
cat > vfs_orchestrator.py <<'PY_EOF'
import os
import json
import sqlite3
import logging
from glob import glob

logging.basicConfig(
    level=logging.INFO,
    format="\033[1;36m%(asctime)s\033[0m | \033[1;34m[VFS-CORE]\033[0m %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("VFS_Core")

class VFSOperator:
    def __init__(self, db_path="god_stack_vfs.db", json_dir="outputs"):
        self.db_path = db_path
        self.json_dir = json_dir
        self.conn = None

    def mount_vfs(self):
        logger.info(f"Mounting SQLite Core VFS at {self.db_path}...")
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intel_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT UNIQUE,
                domain TEXT,
                user_agent TEXT,
                content_length INTEGER,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def ingest_payloads(self):
        search_pattern = os.path.join(self.json_dir, "*.json")
        payloads = glob(search_pattern)
        
        if not payloads:
            return

        cursor = self.conn.cursor()
        ingested_count = 0

        for file_path in payloads:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # Normalize raw data to a list of dicts to handle array payloads safely
                data_blocks = raw_data if isinstance(raw_data, list) else [raw_data]
                
                for data in data_blocks:
                    if not isinstance(data, dict):
                        continue
                        
                    cursor.execute('''
                        INSERT OR IGNORE INTO intel_matrix (target_url, domain, user_agent, content_length)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        data.get("target_url", "unknown_target"),
                        data.get("domain_context", {}).get("domain", "unknown_domain"),
                        data.get("extracted_headers", {}).get("User-Agent", "unknown_ua"),
                        data.get("content_length", 0)
                    ))
                    ingested_count += 1
            except Exception as e:
                logger.error(f"Failed to parse payload {file_path}: {e}")

        self.conn.commit()
        logger.info(f"Swept and synchronized {ingested_count} payload objects into persistent matrix.")

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("VFS connection closed safely.")

if __name__ == "__main__":
    vfs = VFSOperator()
    vfs.mount_vfs()
    vfs.ingest_payloads()
    vfs.close()
PY_EOF

echo -e "${BLUE}[2/3] Upgrading GodScraper API for strict proxy injection...${RESET}"
cat > god_scraper.py <<'PY_EOF'
import asyncio
import json
import logging
import yaml
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="\033[1;36m%(asctime)s\033[0m | \033[1;35m[GOD-ENGINE]\033[0m %(message)s"
)
logger = logging.getLogger("GodScraper")

class GodScraper:
    def __init__(self, profile_name: str = "default_profile", profile_path: str = "stealth_profiles.yaml"):
        self.profile_name = profile_name
        self.profile = self._load_profile(profile_path, profile_name)
        self.playwright = None
        self.browser = None
        self.context = None

    def _load_profile(self, path: str, name: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
                return config.get(name, config.get("default_profile", {}))
        except Exception:
            return {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    async def initialize(self, headless: bool = True, proxy_url: Optional[str] = None):
        self.playwright = await async_playwright().start()
        
        # Structure the proxy payload cleanly for Playwright if provided
        proxy_config = {"server": proxy_url} if proxy_url else None
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            proxy=proxy_config,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--ignore-certificate-errors'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.profile.get("user_agent"),
            viewport=self.profile.get("viewport", {"width": 1920, "height": 1080}),
            locale=self.profile.get("languages", ["en-US"])[0],
            timezone_id="America/New_York"
        )
        
        await self.context.add_init_script(f"""
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {self.profile.get('hardware_concurrency', 8)} }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {self.profile.get('device_memory', 8)} }});
            Object.defineProperty(navigator, 'platform', {{ get: () => '{self.profile.get('platform', 'Win32')}' }});
        """)

    async def shutdown(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
PY_EOF

echo -e "${BLUE}[3/3] Rewiring Matrix Test Runner to consume updated API...${RESET}"
cat > matrix_test_runner.py <<'PY_EOF'
import asyncio
import logging
from scavenger import ProxyScavenger
from god_scraper import GodScraper

logging.basicConfig(
    level=logging.INFO,
    format="\033[1;35m%(asctime)s\033[0m | \033[1;32m[TEST-RUNNER]\033[0m %(message)s",
    datefmt="%H:%M:%S"
)
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
    asyncio.run(run_stealth_validation())
PY_EOF

echo -e "${GREEN}SUCCESS: API boundaries aligned and compiled. Firing final execution sequences...${RESET}\n"
