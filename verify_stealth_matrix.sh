#!/usr/bin/env bash
# ==============================================================================
# verify_stealth_matrix.sh – Automated Stealth Script Verification Engine
# Architecture: Defensive Runtime Audit, Environment Validation & Sync Checks
# ==============================================================================
set -euo pipefail

# 1. Color Palette Definitions (Aligned with Workspace Log Aesthetics)
BLUE="\033[1;34m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
CYAN="\033[1;36m"
RESET="\033[0m"

# 2. Central Logging Framework Functions
log_info() {
    echo -e "${BLUE}$(date +"%H:%M:%S")${RESET} | ${CYAN}[STEALTH-AUDIT]${RESET} $1"
}

log_success() {
    echo -e "${BLUE}$(date +"%H:%M:%S")${RESET} | ${GREEN}[VERIFIED]${RESET} $1"
}

log_warn() {
    echo -e "${BLUE}$(date +"%H:%M:%S")${RESET} | ${YELLOW}[WARN-ALERT]${RESET} $1"
}

log_error() {
    echo -e "${BLUE}$(date +"%H:%M:%S")${RESET} | ${RED}[CRITICAL-FAIL]${RESET} $1" >&2
}

# 3. Environment Context & Virtualenv Auto-Discovery
check_runtime_environment() {
    log_info "Initiating runtime perimeter scan..."
    
    # Verify execution from inside the target root workspace directory
    if [[ ! -d "core" && ! -f "god_engine.py" ]]; then
        log_error "Execution constraint violated: Must run from the 'god_stack' project root workspace folder."
        exit 1
    fi

    # Inspect active python layer environment boundaries
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log_success "Active Virtual Environment isolated via: ${VIRTUAL_ENV}"
    elif [[ -d ".venv" ]]; then
        log_warn "Local sandbox directory '.venv' detected but inactive. Intercepting context to auto-activate..."
        # Source context safely inside a controlled function sequence
        set +u
        source .venv/bin/activate
        set -u
        log_success "Bound runtime shell to local environment wrapper: ${VIRTUAL_ENV}"
    elif [[ -d "venv" ]]; then
        log_warn "Local sandbox directory 'venv' detected but inactive. Intercepting context to auto-activate..."
        set +u
        source venv/bin/activate
        set -u
        log_success "Bound runtime shell to local environment wrapper: ${VIRTUAL_ENV}"
    else
        log_warn "No isolated python environment found. Assessing system-level interpreter paths..."
    fi
}

# 4. Comprehensive Third-Party Library Auditing Matrix
audit_dependencies() {
    log_info "Scanning package registries for missing ecosystem requirements..."
    local missing_packages=0
    
    # Complete list of discrete external components declared across core assets
    local core_modules=(
        "courlan" "tldextract" "cloudscraper" "fake_useragent" 
        "httpx" "bs4" "playwright" "markdownify" "yaml"
    )

    for pkg in "${core_modules[@]}"; do
        if python3 -c "import ${pkg}" &>/dev/null; then
            log_success "Dependency signature verified: '${pkg}'"
        else
            log_error "Missing underlying dependency node library: '${pkg}'"
            missing_packages=$((missing_packages + 1))
        fi
    done

    if [[ ${missing_packages} -gt 0 ]]; then
        log_warn "${missing_packages} core packages are absent. Please run: pip install courlan tldextract cloudscraper fake-useragent httpx beautifulsoup4 playwright markdownify pyyaml"
        return 1
    fi
    log_success "Ecosystem core requirements validation loop returned clean."
}

# 5. Static Compilation and Integrity Evaluation
verify_script_syntax() {
    local target_script="$1"
    log_info "Evaluating structural integrity & compilation matrix: ${target_script}"

    if [[ ! -f "${target_script}" ]]; then
        log_error "Target workspace asset target not found: ${target_script}"
        return 1
    fi

    # Compiles code directly into bytecode safely in a subshell without executing the script payload blocks
    if python3 -m py_compile "${target_script}" &>/dev/null; then
        log_success "Bytecode parsing validated successfully for ${target_script}"
    else
        log_error "Python compiler dropped token sequence. Syntax anomalies found inside: ${target_script}"
        return 1
    fi
}

# 6. Configuration Layer Parser Checks
verify_profiles_config() {
    local config_file="stealth_profiles.yaml"
    log_info "Inspecting local structural parameters configuration profile: ${config_file}"

    if [[ ! -f "${config_file}" ]]; then
        log_error "Config component missing: ${config_file} must exist inside current runtime tree path context."
        return 1
    fi

    # Validate structure using standard Python yaml framework
    if python3 -c "import yaml; yaml.safe_load(open('${config_file}'))" &>/dev/null; then
        log_success "Configuration schema bounds validated for ${config_file}"
    else
        log_error "Formatting exception caught: ${config_file} possesses invalid YAML indentation structural keys."
        return 1
    fi
}

# Main Execution Orchestrator
main() {
    echo -e "${BLUE}==============================================================================${RESET}"
    echo -e "${CYAN}             INITIALIZING STEALTH MATRIX CORE VERIFICATION RUNNER             ${RESET}"
    echo -e "${BLUE}==============================================================================${RESET}"

    local failure_count=0

    check_runtime_environment

    echo -e "${BLUE}------------------------------------------------------------------------------${RESET}"
    audit_dependencies || failure_count=$((failure_count + 1))

    echo -e "${BLUE}------------------------------------------------------------------------------${RESET}"
    verify_profiles_config || failure_count=$((failure_count + 1))

    echo -e "${BLUE}------------------------------------------------------------------------------${RESET}"
    # Array mapping to the provided suite assets uploaded into your framework layout
    local core_scripts=(
        "url_sanitizer.py"
        "courlan_router.py"
        "captcha_handler.py"
        "scavenger.py"
        "god_engine.py"
        "god_scraper.py"
    )

    for script in "${core_scripts[@]}"; do
        verify_script_syntax "${script}" || failure_count=$((failure_count + 1))
    done

    echo -e "${BLUE}==============================================================================${RESET}"
    if [[ ${failure_count} -eq 0 ]]; then
        echo -e "${GREEN}🛡️  SUCCESS: All core stealth matrix operations passed compilation boundaries flawlessly.${RESET}"
        echo -e "${BLUE}==============================================================================${RESET}"
        exit 0
    else
        echo -e "${RED}⚠️  ALERT: Integrity checks failed with [${failure_count}] configuration or structural faults.${RESET}"
        echo -e "${BLUE}==============================================================================${RESET}"
        exit 1
    fi
}

main
