import os
import json
import sqlite3
import logging
from glob import glob
from utils.logger import setup_production_logging

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
    setup_production_logging()
    vfs = VFSOperator()
    vfs.mount_vfs()
    vfs.ingest_payloads()
    vfs.close()
