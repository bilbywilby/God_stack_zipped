# ==============================================================================
# ADVANCED FRONTIER URL ROUTER (courlan_router.py)
# Architecture: High-Performance Normalization and Crawler Trap Avoidance
# ==============================================================================

import logging
import courlan
from urllib.parse import urlparse
from utils.logger import setup_production_logging

logger = logging.getLogger("CourlanRouter")

class CourlanRouter:
    """Handles URL normalization, cleanliness checks, and tracking parameter removal."""

    @staticmethod
    def validate_and_clean(url: str) -> str:
        """
        Validates, scrubs tracking parameters, and checks against crawl traps.
        Returns a pristine URL string, or an empty string if malicious/invalid.
        """
        if not url or not isinstance(url, str):
            return ""

        logger.info(f"Passing target through Courlan frontier filters: {url}")
        
        try:
            cleaned_url = courlan.clean_url(url)
            if not cleaned_url:
                return ""

            validation_check = courlan.validate_url(cleaned_url)
            if not validation_check:
                logger.warning(f"URL rejected by Courlan validation filters: {url}")
                return ""

            path_segments = [seg for seg in urlparse(cleaned_url).path.split('/') if seg]
            if len(path_segments) > 5 and len(set(path_segments)) < (len(path_segments) / 2):
                logger.warning(f"Dropping suspected recursive loop path pattern: {cleaned_url}")
                return ""

            return cleaned_url

        except Exception as parse_error:
            logger.error(f"Non-critical anomaly encountered filtering {url}: {str(parse_error)}")
            return ""

if __name__ == "__main__":
    setup_production_logging()
    test_target = "https://news.ycombinator.com/item?id=123&utm_source=feed#hash"
    result = CourlanRouter.validate_and_clean(test_target)
    print(f"\nScrubbed Output: {result}")
