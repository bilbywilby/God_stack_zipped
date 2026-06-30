#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="."
export LOG_DIR="vaults"
export GATEWAY_PORT=8090

echo "💾 Initializing persistent vault arrays..."
mkdir -p "${LOG_DIR}"

if [ "$(uname)" != "Darwin" ]; then
    echo "🔓 Optimizing file descriptor limits..."
    ulimit -n 65535 || true
fi

echo "🧹 Purging residual engine threads..."
pkill -f "utils.worker_scaler" || true
pkill -f "utils.broadcast_server" || true
pkill -f "utils.worker_loop" || true
sleep 0.5

echo "🧠 Bootstrapping Multi-Lane Scaling Daemon..."
python3 utils/worker_scaler.py >> "${LOG_DIR}/scaler.log" 2>&1 &
SCALER_PID=$!

echo "⚡ Deploying Production Ingress Routing Mesh on port ${GATEWAY_PORT}..."
python3 utils/broadcast_server.py >> "${LOG_DIR}/gateway.log" 2>&1 &
GATEWAY_PID=$!

echo "🧱 Injecting parallel active execution worker lanes..."
python3 utils/worker_loop.py >> "${LOG_DIR}/worker_lane_1.log" 2>&1 &
python3 utils/worker_loop.py >> "${LOG_DIR}/worker_lane_2.log" 2>&1 &

sleep 2.0

if kill -0 "$GATEWAY_PID" 2>/dev/null && kill -0 "$SCALER_PID" 2>/dev/null; then
    echo "================================================================="
    echo "🏁 PRODUCTION SYSTEM ACTIVE WITH STREAMING WORKERS"
    echo "   ↳ Gateway Engine PID: $GATEWAY_PID"
    echo "   ↳ Adaptive Scaler PID:  $SCALER_PID"
    echo "================================================================="
else
    echo "❌ CRITICAL: Sub-component collapse detected during initialization."
    exit 1
fi
