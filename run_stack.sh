#!/usr/bin/env bash
# ==============================================================================
# UNIFIED G.O.D. STACK ORCHESTRATION HARNESS (run_stack.sh)
# Handles both Monolithic Standalone and Distributed Multi-Lane Cluster environments.
# ==============================================================================

set -euo pipefail
IFS=$'\n\t'

export TERM=xterm-256color
NC='\033[0m'
BOLD='\033[1m'
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${WORKSPACE_DIR}/logs"
OUTPUT_DIR="${WORKSPACE_DIR}/outputs"
VAULT_DIR="${WORKSPACE_DIR}/vaults"

BACKGROUND_PIDS=()

log_info()    { echo -e "${BLUE}$(date +"%H:%M:%S")${NC} | ${CYAN}[ORCHESTRATOR]${NC} $1"; }
log_success() { echo -e "${BLUE}$(date +"%H:%M:%S")${NC} | ${GREEN}[SUCCESS]${NC} ${BOLD}$1${NC}"; }
log_warn()    { echo -e "${BLUE}$(date +"%H:%M:%S")${NC} | ${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${BLUE}$(date +"%H:%M:%S")${NC} | ${RED}[ERROR]${NC} ${BOLD}$1${NC}" >&2; }

cleanup_stack() {
    local exit_code=$?
    if [ ${#BACKGROUND_PIDS[@]} -gt 0 ]; then
        echo -e "\n"
        log_warn "Termination signal caught. Reaping background daemon chains..."
        for pid in "${BACKGROUND_PIDS[@]}"; do
            if kill -0 "$pid" &>/dev/null; then
                log_info "Sending SIGTERM to Process ID: ${pid}"
                kill "$pid" 2>/dev/null || true
            fi
        done
    fi
    exit "$exit_code"
}
trap 'cleanup_stack' EXIT INT TERM ERR

verify_environment() {
    log_info "Evaluating structural environment setup..."
    for dir in "${LOG_DIR}" "${OUTPUT_DIR}" "${VAULT_DIR}" "utils" "vaults"; do
        [ ! -d "${dir}" ] && mkdir -p "${dir}"
    done

    if [ -f "venv/bin/activate" ]; then
        log_info "Attaching runtime virtual environment matrix..."
        # shellcheck disable=SC1091
        source venv/bin/activate
    fi
}

execute_component_test() {
    local target_script=$1
    if [ -f "${target_script}" ]; then
        log_info "Validating integrity profile: [${target_script}]"
        python3 -m py_compile "${target_script}" || { log_error "Compilation failure in ${target_script}"; exit 1; }
    fi
}

launch_standalone() {
    log_info "Starting Monolithic Standalone Mode..."
    execute_component_test "god_engine.py"
    python3 god_engine.py 2>&1 | tee "${LOG_DIR}/engine_core.log"
}

launch_cluster() {
    log_info "Starting Distributed Cluster Stack..."
    
    execute_component_test "utils/broadcast_server.py"
    execute_component_test "utils/worker_scaler.py"
    execute_component_test "utils/worker_loop.py"

    log_info "Spinning up Ingress Routing Mesh..."
    python3 utils/broadcast_server.py > "${LOG_DIR}/gateway.log" 2>&1 &
    BACKGROUND_PIDS+=($!)
    sleep 1

    log_info "Spinning up Adaptive Auto-Scaler Daemon..."
    python3 utils/worker_scaler.py > "${LOG_DIR}/scaler.log" 2>&1 &
    BACKGROUND_PIDS+=($!)

    log_info "Deploying primary worker lane worker processes..."
    for i in {1..2}; do
        python3 utils/worker_loop.py > "${LOG_DIR}/worker_lane_${i}.log" 2>&1 &
        BACKGROUND_PIDS+=($!)
    done

    log_success "Distributed Cluster active. Processing background telemetry loop."
    log_info "Press [CTRL+C] to cleanly bring down the entire stack cluster layout."
    
    tail -f "${LOG_DIR}/gateway.log" "${LOG_DIR}/scaler.log" 2>/dev/null || wait
}

print_usage() {
    echo "Usage: $0 [MODE]"
    echo "Modes:"
    echo "  --standalone    Runs the sequential, single-file god_engine pipeline."
    echo "  --cluster       Runs the high-throughput gateway, adaptive scaler, and worker loops."
}

main() {
    echo -e "\n${BOLD}${CYAN}=== INITIALIZING UNIFIED G.O.D. STACK WORKFLOW RUNNER ===${NC}\n"
    cd "${WORKSPACE_DIR}"
    verify_environment

    execute_component_test "utils/dom_parser.py"
    execute_component_test "utils/ua_generator.py"

    if [ -f "scavenger.py" ]; then
        log_info "Launching global Proxy Scavenger engine..."
        python3 scavenger.py > "${LOG_DIR}/scavenger_runtime.log" 2>&1 &
        BACKGROUND_PIDS+=($!)
    fi

    local run_mode="${1:-}"
    case "${run_mode}" in
        --standalone)
            launch_standalone
            ;;
        --cluster)
            launch_cluster
            ;;
        *)
            log_warn "No explicit mode configured. Falling back to default [--cluster]."
            print_usage
            echo ""
            launch_cluster
            ;;
    esac
}

main "$@"
