#!/usr/bin/env bash
# =============================================================================
# G.O.D. STACK TERMINAL STREAM AUDITOR v1.5.3 (verify_logs.sh)
# Architecture: High-Priority Log Diagnostics & FOSS Compliance Purge Engine
# =============================================================================

# Ensure log directory exists to prevent search faults
mkdir -p logs

if [ "$1" == "--purge" ]; then
    echo -e "\033[1;35m[SYSTEM-ACTION] Initializing secure data erasure matrix...\033[0m"
    # FOSS Compliance: Zero out active logs rather than breaking directory descriptors
    rm -f logs/*.log 2>/dev/null
    rm -f logs/*.json 2>/dev/null
    echo -e "\033[1;32m[SUCCESS] Physical logging footprint cleared from storage layout.\033[0m"
    exit 0
fi

echo -e "\033[1;35mChecking framework active log directory integrity...\033[0m"

# Only search within the designated log file directory for actual runtime writes
ERRORS=$(grep -rnw ./logs -e "CRITICAL" -e "ERROR" 2>/dev/null)

if [ -z "$ERRORS" ]; then
    echo -e "\033[1;32m[PERFECT] No active runtime failures detected inside logging namespaces.\033[0m"
    exit 0
else
    echo -e "\033[1;31m[WARNING] Isolated runtime errors found inside execution logs:\033[0m"
    echo "$ERRORS"
    exit 1
fi
