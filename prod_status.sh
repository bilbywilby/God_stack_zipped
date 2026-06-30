#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="vaults"

while true; do
    clear
    echo "================================================================="
    echo "👁️  GOD STACK LIVE ENGINE INSIGHTS"
    echo "   Press [CTRL+C] to exit monitoring mode."
    echo "================================================================="
    
    echo -e "\n📊 ACTIVE PLATFORM PROCESSES:"
    ps aux | grep -E "utils.broadcast_server|utils.worker_scaler|worker_loop" | grep -v "grep" || echo "No active components detected."

    echo -e "\n🎯 INGRESS GATEWAY PERFORMANCE LOGS:"
    if [ -f "${LOG_DIR}/gateway.log" ]; then
        tail -n 5 "${LOG_DIR}/gateway.log"
    else
        echo "Waiting for gateway log matrix allocation..."
    fi

    echo -e "\n🧠 SCALER DAEMON RUNTIME STATE:"
    if [ -f "${LOG_DIR}/scaler.log" ]; then
        tail -n 5 "${LOG_DIR}/scaler.log"
    else
        echo "Waiting for adaptive scaler telemetry..."
    fi
    
    sleep 2
done
