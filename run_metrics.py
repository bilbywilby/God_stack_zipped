#!/usr/bin/env python3
import time
import sys
from prometheus_client import start_http_server, REGISTRY

# Enforce local workspace prioritization
sys.path.insert(0, '.')
import prometheus_exporter

def main():
    port = 8000
    print("[METRICS] Initializing execution context...")
    
    # Explicitly touch variables to prevent import-sweeping optimizations
    metrics_ref = [
        prometheus_exporter.WORKER_EXECS,
        prometheus_exporter.PIPELINE_LATENCY,
        prometheus_exporter.SCRAPE_SUCCESS_TOTAL
    ]
    
    print(f"[METRICS] Successfully bound {len(metrics_ref)} core collectors to registry.")
    print(f"[METRICS] Booting server instance on port {port}...")
    
    start_http_server(port)
    
    # Print out currently registered metric names to terminal log
    registered_names = [metric.name for metric in REGISTRY._collector_to_names.values()]
    print(f"[METRICS] Active collectors found in registry: {[name for name in registered_names if 'god_stack' in str(name)]}")
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
