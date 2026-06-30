#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="."

run_profile() {
    local profile_name=$1
    local clients=$2
    local std_max=$3
    local delay=$4

    echo "================================================================="
    echo "🚀 RUNNING AUTOMATED PROFILE: ${profile_name}"
    echo "⚙️  Configuration -> Std Max Queue: ${std_max} | Worker Latency: ${delay}s"
    echo "🔥 Target Load    -> Concurrent Simulation Clients: ${clients}"
    echo "================================================================="

    # EXPORT parameters so prod_orchestrator.sh and python workers read the environment matrix variables
    export STD_MAX_QUEUE="${std_max}"
    export WORKER_LATENCY="${delay}"

    # Reset metrics state cleanly via orchestrator
    ./prod_orchestrator.sh

    echo "⚡ Injecting traffic matrix via client simulator..."
    python3 simulate_clients.py "${clients}" "${delay}" || true

    echo "🛑 Tearing down context for ${profile_name}..."
    pkill -f "utils.broadcast_server" || true
    pkill -f "utils.worker_scaler" || true
    pkill -f "utils.worker_loop" || true
    sleep 1.0
}

main() {
    run_profile "SWEEP_A_NOMINAL" 200 300 0.00
    run_profile "SWEEP_B_DEGRADED" 400 100 0.02
    run_profile "SWEEP_C_SATURATED" 600 20 0.08
    echo "🧹 All sweeps finished. Generating final post-run metrics summary."
}

main "$@"
