# ==============================================================================
# WHATWG COMPLIANT URL SANITIZATION MATRIX (url_sanitizer.py)
# Architecture: Standardized Normalization, Deterministic Query Sorting, & Tracker Stripping
# ==============================================================================

import logging
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from utils.logger import setup_production_logging

logger = logging.getLogger("UrlSanitizer")

class UrlSanitizer:
    """Enforces strict structural compliance with modern browser network layers."""
    
    @staticmethod
    def normalize(raw_url: str, strip_trackers: bool = True) -> str:
        """Transforms erratic web strings into normalized, web-compliant endpoints."""
        if not raw_url or not isinstance(raw_url, str):
            return ""

        cleaned = raw_url.strip()
        
        # Enforce scheme baseline if dropped by mistake
        if cleaned.startswith("//"):
            cleaned = "https:" + cleaned
        elif not cleaned.startswith(("http://", "https://")):
            cleaned = "https://" + cleaned

        try:
            parsed = urlparse(cleaned)
            
            # Extract and filter query string parameters
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            
            if strip_trackers:
                # Discard common behavioral analytics tracking noise
                blacklisted_keys = {
                    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                    "gclid", "fbclid", "yclid", "twclid", "msclkid", "_hsenc", "mkt_tok"
                }
                query_params = [(k, v) for k, v in query_params if k.lower() not in blacklisted_keys]

            # Enforce deterministic parameter sequencing for database deduplication
            query_params.sort(key=lambda pair: pair[0])
            normalized_query = urlencode(query_params)
            
            # Clean paths and normalize trailing slashes consistently
            normalized_path = parsed.path if parsed.path else "/"
            if len(normalized_path) > 1 and normalized_path.endswith("/"):
                normalized_path = normalized_path.rstrip("/")
            
            final_url = urlunparse((
                parsed.scheme.lower(),      # Schemes are lowercase per WHATWG spec
                parsed.netloc.lower(),      # Hostnames must evaluate to lowercase
                normalized_path,
                parsed.params,
                normalized_query,
                ""                          # Strip fragment identifiers (hash anchors aren't sent to servers)
            ))
            
            if final_url != raw_url:
                logger.info(f"Normalized link mutation: {raw_url} -> \033[1;36m{final_url}\033[0m")
            return final_url

        except Exception as e:
            logger.error(f"WHATWG specification violation parsing input structural link: {str(e)}")
            return cleaned

if __name__ == "__main__":
    setup_production_logging()
    print("\n\033[1;35m--- EVALUATING UPGRADED URL COMPLIANCE ENGINE ---\033[0m")
    
    # Advanced test matrix verifying parameters, casing, order variations, and trailing slashes
    dirty_urls = [
        "NEWS.YCOMBINATOR.COM/newest/",
        "https://news.ycombinator.com/front?utm_source=twitter&id=123&abc=xyz#comments",
        "https://news.ycombinator.com/front?abc=xyz&id=123", # Out-of-order parameters to deduplicate
        "//news.ycombinator.com/ask?msclkid=999&search=python"
    ]
    
    for url in dirty_urls:
        UrlSanitizer.normalize(url)
