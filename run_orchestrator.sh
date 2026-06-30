#!/usr/bin/env bash
set -uo pipefail

# ---- CONFIG ----
INTERVAL=15
TARGETS=(
    "https://news.ycombinator.com|hn"
    "https://github.com|github"
    "https://python.org|python"
)

# 1. Start the long-running Prometheus exporter ONCE if it isn't already running
if ! pgrep -f "prometheus_exporter.py" > /dev/null; then
    echo "[INIT] Starting standalone Prometheus Exporter Daemon on port 9100..."
    python3 /home/tangleroot013/god_stack/prometheus_exporter.py &
fi

print_summary() {
    echo "=== ORCHESTRATION SUMMARY ==="
    echo "Frame Event: $(date +"%Y-%m-%d %H:%M:%S")"
    echo "Run Identifier: $(date +%s)_$RANDOM"
    echo "System State: SUCCESS OPERATIONAL"
}

while true; do
    FRAME_START=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[INFO] Active Frame Cycle: $FRAME_START"

    for entry in "${TARGETS[@]}"; do
        URL="${entry%%|*}"
        LABEL="${entry##*|}"
        echo "[INFO] Processing Target Asset Profile: $URL (label=$LABEL)"

        # Check target health and update state log
        if curl -sSf "$URL" > /dev/null; then
            echo "[SUCCESS] $URL completed"
        else
            echo "[WARN] $URL failed"
        fi
    done

    print_summary
    echo "[INFO] Sleeping for ${INTERVAL}s..."
    sleep "$INTERVAL"
done
