#!/usr/bin/env python3
import logging
import time

logger = logging.getLogger("MatrixDaemon")

class DataAlchemist:
    @staticmethod
    def optimize_array_processing(raw_payloads: list) -> list:
        """
        Executes an unrolled, single-pass list comprehension over raw dictionary matrices.
        Hoists global calculations and utilizes inner assignment expressions for speed.
        """
        if not raw_payloads:
            return []

        start_time = time.perf_counter()
        batch_processed_at = int(time.time())
        
        processed_records = [
            {
                "title": title,
                "url": url,
                "score": int(score) if isinstance(score, (int, float)) else 0,
                "processed_at": batch_processed_at
            }
            for record in raw_payloads
            if isinstance(record, dict)
            for title in (record.get("title", "").strip(),)
            for url in (record.get("url", "").strip(),)
            for score in (record.get("score", 0),)
            if title and url
        ]
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"✨ [ALCHEMIST] Transformed {len(processed_records)}/{len(raw_payloads)} "
            f"records in {duration_ms:.3f}ms"
        )
        return processed_records
