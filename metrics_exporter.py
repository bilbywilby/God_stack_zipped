#!/usr/bin/env python3
# ==============================================================================
# metrics_exporter.py – FOSS Prometheus-compatible telemetry exposition endpoint
# FIX: SYSTEM_METRICS was a plain dict mutated from the main thread while the
#      HTTP handler thread (serve_forever) read it concurrently — a data race.
#      Added a threading.Lock and increment()/snapshot() helpers so all callers
#      use the safe path instead of direct dict assignment.
# ==============================================================================
import http.server
import logging
import threading
from collections import defaultdict
from utils.logger import setup_production_logging

logger = logging.getLogger("TelemetryExporter")

_metrics_lock = threading.Lock()

SYSTEM_METRICS: dict[str, int] = defaultdict(int, {
    "god_stack_ingestion_attempts_total": 0,
    "god_stack_ingestion_success_total": 0,
    "god_stack_deduplication_skips_total": 0,
    "god_stack_bytes_processed_total": 0,
})


def increment(key: str, amount: int = 1) -> None:
    """Thread-safe counter increment. Always use this instead of direct assignment."""
    with _metrics_lock:
        SYSTEM_METRICS[key] += amount


def snapshot() -> dict[str, int]:
    """Returns a consistent point-in-time copy of all counters."""
    with _metrics_lock:
        return dict(SYSTEM_METRICS)


class PrometheusMetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        data = snapshot()
        lines: list[str] = []
        for name, val in data.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val}")
        body = ("\n".join(lines) + "\n").encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def start_telemetry_server(port: int = 8000) -> None:
    """Spins up the Prometheus exposition server in a daemon thread."""
    server = http.server.HTTPServer(("0.0.0.0", port), PrometheusMetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("📊 Telemetry live on :%d/metrics", port)


if __name__ == "__main__":
    setup_production_logging()
    import time
    start_telemetry_server(8000)
    increment("god_stack_ingestion_attempts_total", 3)
    increment("god_stack_ingestion_success_total", 2)
    print("Self-test running — Control+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
