#!/usr/bin/env python3
import json
import random
import sys
import time
import urllib.request
import urllib.error

# --------------------------------------------------------------------------- #
#    Configuration Settings
# --------------------------------------------------------------------------- #
PUSHGATEWAY_URL = "http://localhost:9091/metrics/job/background_worker/instance/worker_node_01"
TICK_INTERVAL = 3.0  # Push every 3 seconds

print("\033[1;32m[SIMULATOR]\033[0m Initializing worker metric generation telemetry...")
print(f"\033[1;32m[SIMULATOR]\033[0m Target Pushgateway: {PUSHGATEWAY_URL}")
print("\033[1;32m[SIMULATOR]\033[0m Press Ctrl+C to stop transmitting.")
print("-" * 60)

# Track persistent state for counters
total_tasks_processed = 0

try:
    while True:
        # 1. Generate realistic data variations
        cpu_usage = random.uniform(20.0, 85.0)
        memory_bytes = random.randint(256000000, 512000000) # 256MB - 512MB
        processing_lag_seconds = random.uniform(0.02, 1.45)
        
        # Increment counter dynamically
        new_tasks = random.randint(1, 5)
        total_tasks_processed += new_tasks

        # 2. Construct standard Prometheus exposition text format payload
        # Each line: metric_name{label="val"} value
        payload_lines = [
            "# HELP worker_cpu_utilization Percentage of CPU currently consumed by the worker process.",
            "# TYPE worker_cpu_utilization gauge",
            f"worker_cpu_utilization {cpu_usage:.2f}",
            
            "# HELP worker_memory_bytes Memory footprints consumed in bytes.",
            "# TYPE worker_memory_bytes gauge",
            f"worker_memory_bytes {memory_bytes}",
            
            "# HELP worker_tasks_total Cumulative total of background jobs successfully executed.",
            "# TYPE worker_tasks_total counter",
            f"worker_tasks_total {total_tasks_processed}",
            
            "# HELP worker_processing_lag_seconds Time dilation lag processing incoming queue messages.",
            "# TYPE worker_processing_lag_seconds gauge",
            f"worker_processing_lag_seconds {processing_lag_seconds:.4f}"
        ]
        
        payload_data = "\n".join(payload_lines) + "\n"
        
        # 3. Transmit payload over HTTP POST/PUT to Pushgateway endpoints
        req = urllib.request.Request(
            url=PUSHGATEWAY_URL,
            data=payload_data.encode("utf-8"),
            headers={"Content-Type": "text/plain; version=0.0.4"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                if response.status in (200, 202):
                    print(f"\033[1;34m[TX]\033[0m Pushed packet: Tasks={total_tasks_processed} | CPU={cpu_usage:.1f}% | Lag={processing_lag_seconds:.2f}s")
                else:
                    print(f"\033[1;31m[WARN]\033[0m Gateway responded with unexpected status: {response.status}")
        except urllib.error.URLError as e:
            print(f"\033[1;31m[CONNECTION ERROR]\033[0m Could not connect to Pushgateway: {e.reason}")
            print("Is the docker stack running? Retrying next cycle...")
            
        time.sleep(TICK_INTERVAL)

except KeyboardInterrupt:
    print("\n\033[1;32m[SIMULATOR]\033[0m Telemetry collection suspended gracefully. Exiting.")
    sys.exit(0)
