#!/usr/bin/env bash
# ==============================================================================
#  G.O.D. Stack (Global Orchestration Daemon) — Automated Orchestrator Driver
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# 1. CORE PIPELINE CONFIGURATION
# ------------------------------------------------------------------------------
CONFIG_FILE="config/target_urls.json"
BACKUP_DIR="./config/backups"
LOG_DIR="./logs"
METRICS_DIR="./metrics"
VAULT_DIR="./vaults"

MAX_RETRIES=3
RETRY_DELAY=30

SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_ADDR="${NOTIFY_EMAIL:-}"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TIMESTAMP_HUMAN="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
LOG_FILE="${LOG_DIR}/orchestrator_${TIMESTAMP}.log"
METRICS_FILE="${METRICS_DIR}/metrics_${TIMESTAMP}.json"
BACKUP_CONFIG="${BACKUP_DIR}/target_urls_${TIMESTAMP}.json.bak"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# 2. TELEMETRY & LOGGING LOGISTICS
# ------------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC}    $1" | tee -a "${LOG_FILE}"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $1" | tee -a "${LOG_FILE}"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $1" | tee -a "${LOG_FILE}"; }

die() {
    log_error "$1"
    exit 1
}

# ------------------------------------------------------------------------------
# 3. PRE-FLIGHT COMPLIANCE VALIDATIONS
# ------------------------------------------------------------------------------
check_dependencies() {
    log_info "Initiating environmental pre-flight audits..."
    
    local deps=("python3" "jq" "curl")
    for dep in "${deps[@]}"; do
        if ! command -v "${dep}" &> /dev/null; then
            die "Missing system dependency: ${dep}. Ensure path access before execution."
        fi
    done
    
    if [[ -n "${EMAIL_ADDR}" ]] && ! command -v mail &> /dev/null; then
        log_warn "NOTIFY_EMAIL is configured, but system 'mail' utility is missing. Email alerts skipped."
    fi
    
    python3 -c "import pandas, pyarrow, boto3, numpy" 2>/dev/null || \
        die "Python packaging matrix mismatch. Verify global modules or environment mapping."
        
    log_success "Environmental system compliance verified."
}

check_config_validity() {
    log_info "Parsing structural integrity of targets template: ${CONFIG_FILE}"
    
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        die "Target configuration structure unlocatable at designated target path."
    fi
    
    if ! jq empty "${CONFIG_FILE}" 2>/dev/null; then
        die "Invalid JSON syntax discovered in configuration map."
    fi
    
    local required_keys=("_metadata" "carriers" "scrape_parameters")
    for key in "${required_keys[@]}"; do
        if ! jq -e ".${key}" "${CONFIG_FILE}" > /dev/null 2>&1; then
            die "Malformed target file mapping. Missing critical system root entity: ${key}"
        fi
    done
    
    log_success "Configuration mapping verified successfully."
}

# ------------------------------------------------------------------------------
# 4. CONFIGURATION CONCURRENCY MUTATION
# ------------------------------------------------------------------------------
backup_config() {
    log_info "Executing atomic baseline backup of live configuration mapping..."
    mkdir -p "${BACKUP_DIR}"
    cp "${CONFIG_FILE}" "${BACKUP_CONFIG}"
    log_success "State saved safely to: ${BACKUP_CONFIG}"
}

inject_solver_settings() {
    log_info "Injecting real-time Cloudflare solver modules and execution limits..."
    
    local tmp_config
    tmp_config=$(mktemp)
    trap 'rm -f "${tmp_config}"' EXIT
    
    jq '
      .scrape_parameters |= (
        . + {
          "cloudflare_solver": {
            "enabled": true,
            "max_solve_time_ms": 12000,
            "solvers": ["hcaptcha", "turnstile", "js_challenge"]
          },
          "fallback_renderer": {
            "engine": "playwright",
            "browser": "chromium",
            "headless": true,
            "timeout_ms": 30000
          },
          "proxy_cooldown_ms": 1500,
          "retry_policy": {
            "max_retries": 6,
            "backoff_factor": 2,
            "status_codes_to_retry": [429, 502, 503, 504],
            "respect_retry_after": true
          },
          "audit": {
            "store_challenge_solution": true,
            "solution_key": "challenge_solution"
          }
        }
      )
    ' "${CONFIG_FILE}" > "${tmp_config}"
    
    mv "${tmp_config}" "${CONFIG_FILE}"
    log_success "Dynamic configuration payload rewritten with solver profiles."
}

# ------------------------------------------------------------------------------
# 5. CORE EXECUTION ENGINE LAYER
# ------------------------------------------------------------------------------
initialize_metrics() {
    mkdir -p "${METRICS_DIR}"
    cat > "${METRICS_FILE}" <<EOF
{
  "run_timestamp": "${TIMESTAMP}",
  "run_timestamp_human": "${TIMESTAMP_HUMAN}",
  "start_time_unix": $(date +%s),
  "config_file": "${CONFIG_FILE}",
  "log_file": "${LOG_FILE}",
  "status": "running",
  "exit_code": null,
  "duration_seconds": null,
  "errors": []
}
EOF
}

run_engine() {
    local attempt=1
    
    while [[ ${attempt} -le ${MAX_RETRIES} ]]; do
        log_info "Waking cluster coordinator daemon (Attempt ${attempt}/${MAX_RETRIES})..."
        
        local exit_code=0
        python3 -u god_engine.py --config "${CONFIG_FILE}" 2>&1 | tee -a "${LOG_FILE}" || exit_code=$?
        
        if [[ ${exit_code} -eq 0 ]]; then
            log_success "Global Master loop routine exited with status code zero."
            return 0
        else
            log_warn "Cluster process supervisor registered anomaly and dropped with error code: ${exit_code}"
            if [[ ${attempt} -lt ${MAX_RETRIES} ]]; then
                log_warn "Sleeping execution pipeline thread for ${RETRY_DELAY}s before recycling workers..."
                sleep "${RETRY_DELAY}"
            fi
        fi
        ((attempt++))
    done
    
    log_error "Operational pipeline failure encountered: Daemon loop exhausted all target attempts."
    return 1
}

# ------------------------------------------------------------------------------
# 6. PAYLOAD DECOMPRESSION & RECOVERY CHECKS
# ------------------------------------------------------------------------------
validate_extraction_results() {
    log_info "Verifying extraction sequence integrity from localized storage..."
    
    if [[ ! -d "${VAULT_DIR}" ]]; then
        log_warn "Target output directory missing. Processing sequence generated no output metrics."
        return 0
    fi
    
    local vault_count
    vault_count=$(find "${VAULT_DIR}" -name "*.bin" -type f 2>/dev/null | wc -l)
    
    if [[ ${vault_count} -eq 0 ]]; then
        log_error "Zero binary state files extracted. Data target extraction anomaly detected."
        return 1
    fi
    
    log_info "Located ${vault_count} serialized binary binary arrays. Unpacking targets..."
    
    local corrupt_count=0
    while IFS= read -r vault_file; do
        if ! python3 -c "import pickle; pickle.load(open('${vault_file}', 'rb'))" 2>/dev/null; then
            log_error "Corrupt storage structural array identified in vault payload: ${vault_file}"
            ((corrupt_count++))
        fi
    done < <(find "${VAULT_DIR}" -name "*.bin" -type f -mmin -60)
    
    if [[ ${corrupt_count} -gt 0 ]]; then
        log_error "Extraction integrity compromised. ${corrupt_count} data arrays failed check."
        return 1
    fi
    
    log_success "All freshly isolated binary database maps passed serialization validity routines."
    return 0
}

# ------------------------------------------------------------------------------
# 7. TELEMETRY BOUNDARY NOTIFICATIONS
# ------------------------------------------------------------------------------
notify() {
    local status="$1"
    local message="$2"
    local color="good"
    [[ "${status}" == "failure" ]] && color="danger"
    
    if [[ -n "${SLACK_WEBHOOK}" ]]; then
        local payload
        payload=$(jq -n \
            --arg col "${color}" \
            --arg title "G.O.D. Stack Cluster Alert — ${status}" \
            --arg txt "${message}" \
            --arg time "${TIMESTAMP_HUMAN}" \
            --arg log "${LOG_FILE}" \
            '{attachments: [{color: $col, title: $title, text: $txt, fields: [{title: "Timestamp", value: $time, short: true},{title: "Log Path", value: $log, short: false}]}]}')
            
        curl -s -X POST -H 'Content-type: application/json' --data "${payload}" "${SLACK_WEBHOOK}" > /dev/null || log_warn "Webhook dispatch dropped."
    fi
    
    if [[ -n "${EMAIL_ADDR}" ]] && command -v mail &> /dev/null; then
        mail -s "G.O.D. Cluster Alert [${status}] — ${TIMESTAMP_HUMAN}" "${EMAIL_ADDR}" <<EOF
Pipeline Execution Frame: ${status}
Audit Clock: ${TIMESTAMP_HUMAN}
Active Configuration Profile: ${CONFIG_FILE}
Active Console Log Capture: ${LOG_FILE}

Event Description:
${message}
EOF
    fi
}

# ------------------------------------------------------------------------------
# 8. POST-EXECUTION CONSOLIDATION
# ------------------------------------------------------------------------------
finalize_metrics() {
    local exit_code="$1"
    local end_time
    end_time=$(date +%s)
    local start_time
    start_time=$(jq -r '.start_time_unix' "${METRICS_FILE}")
    local duration=$((end_time - start_time))
    
    jq \
        --arg status "$([ ${exit_code} -eq 0 ] && echo 'success' || echo 'failed')" \
        --arg exit_code "${exit_code}" \
        --arg duration "${duration}" \
        '.status = $status | .exit_code = ($exit_code | tonumber) | .duration_seconds = ($duration | tonumber)' \
        "${METRICS_FILE}" > "${METRICS_FILE}.tmp" && mv "${METRICS_FILE}.tmp" "${METRICS_FILE}"
        
    log_info "Telemetry profile structural log generated: ${METRICS_FILE}"
}

print_summary() {
    local exit_code="$1"
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║                  ORCHESTRATION SUMMARY                 ║"
    echo "╠════════════════════════════════════════════════════════╣"
    echo "║ Frame Event: ${TIMESTAMP_HUMAN}"
    echo "║ Log Target:  ${LOG_FILE}"
    echo "║ Metrics Map: ${METRICS_FILE}"
    echo "║ State Save:  ${BACKUP_CONFIG}"
    if [[ ${exit_code} -eq 0 ]]; then
        echo -e "║ System State: ${GREEN}✓ SUCCESS OPERATIONAL${NC}                    ║"
    else
        echo -e "║ System State: ${RED}✗ PIPELINE CRITICAL ERROR${NC}                ║"
    fi
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
}

# ------------------------------------------------------------------------------
# 9. PRIMARY SYSTEM LIFE CYCLE ENTRYPOINT
# ------------------------------------------------------------------------------
main() {
    mkdir -p "${LOG_DIR}"
    
    {
        log_info "==========================================================="
        log_info "Starting G.O.D. Stack Cluster Orchestration Sequence Engine"
        log_info "Active Frame Cycle: ${TIMESTAMP_HUMAN}"
        log_info "==========================================================="
        
        check_dependencies
        check_config_validity
        backup_config
        
        inject_solver_settings
        initialize_metrics
        
        if run_engine && validate_extraction_results; then
            finalize_metrics 0
            print_summary 0
            notify "success" "Scrape cluster driver finished cleanly without anomalies."
            return 0
        else
            finalize_metrics 1
            print_summary 1
            notify "failure" "Pipeline execution terminated due to severe runtime engine failures."
            return 1
        fi
    } 2>&1 | tee -a "${LOG_FILE}"
}

main
