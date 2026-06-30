#!/usr/bin/env python3
# ==============================================================================
# data_storage_sync.py – FOSS transactional deduplication and WAL schema manager
# FIX: _init_db used bare sqlite3.connect() without a context manager; if any
#      cursor.execute() raised, conn.close() was never called, leaking the fd.
#      Both DB-touching methods now use `with sqlite3.connect(...)` throughout.
# ==============================================================================
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from utils.logger import setup_production_logging

logger = logging.getLogger("StorageSync")


class StorageSyncEngine:
    def __init__(self, db_path: str = "storage.sqlite") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Forces WAL compilation target schemas on startup."""
        with sqlite3.connect(self.db_path) as conn:   # was: bare connect, no context mgr
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_matrix (
                    payload_hash   TEXT PRIMARY KEY,
                    title          TEXT,
                    source_url     TEXT,
                    extracted_at   TEXT,
                    content_length INTEGER,
                    payload_data   TEXT,
                    status         TEXT
                )
            """)

    def calculate_fingerprint(self, source_url: str, title: str) -> str:
        """Generates a SHA-256 key for structural idempotency."""
        return hashlib.sha256(f"{source_url}::{title}".encode()).hexdigest()

    def sync_record(self, record: dict) -> bool:
        """Commits record or drops it if a duplicate fingerprint exists."""
        payload_hash = self.calculate_fingerprint(
            record["source_url"], record["title"]
        )
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO ingestion_matrix
                        (payload_hash, title, source_url, extracted_at,
                         content_length, payload_data, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    payload_hash,
                    record["title"],
                    record["source_url"],
                    record["extracted_at"],
                    record["content_length"],
                    record["payload_data"],
                    record["status"],
                ))
            logger.info(
                "💾 [STORAGE] Committed %s... -> %s",
                payload_hash[:12], record["title"],
            )
            return True
        except sqlite3.IntegrityError:
            logger.warning(
                "🛡️ [DEDUP] Dropped duplicate %s... (skipped)", payload_hash[:12]
            )
            return False


if __name__ == "__main__":
    setup_production_logging()
    engine = StorageSyncEngine()
    test_node = {
        "title": "Diagnostic Feed Spec",
        "source_url": "https://example.com/spec",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "content_length": 42,
        "payload_data": "Raw matrix stream validation elements.",
        "status": "PROCESSED",
    }
    print(engine.sync_record(test_node))   # True
    print(engine.sync_record(test_node))   # False — dedup fires
