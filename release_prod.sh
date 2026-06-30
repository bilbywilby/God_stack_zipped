#!/usr/bin/env bash
# =============================================================================
# G.O.D. STACK 2.0 PRODUCTION ORCHESTRATOR (release_prod.sh)
# Architecture: Final Release Deployment & Pipeline Initialization
# =============================================================================

echo -e "\033[1;35m[PROD-RELEASE] Initiating G.O.D. Stack 2.0 deployment sequence...\033[0m"

# Step 1: Enforce correct file systems permissions across scripts
echo -e "\033[1;36m[PROD-RELEASE] Securing script execution privileges...\033[0m"
chmod +x *.sh

# Step 2: Run verification checks before startup
if [ -f "verify_stack.py" ]; then
    echo -e "\033[1;34m[PROD-RELEASE] Running root integrity verification metrics...\033[0m"
    .venv/bin/python3 verify_stack.py
fi

# Step 3: Pre-seed stealth profiles so initial requests are safe
echo -e "\033[1;34m[PROD-RELEASE] Pre-seeding initial stealth profile matrix...\033[0m"
.venv/bin/python3 stealth_mutator.py

# Step 4: Spawning the self-healing phantom watchdog in detached daemon mode
echo -e "\033[1;34m[PROD-RELEASE] Detaching Phantom Watchdog daemon loop to background...\033[0m"
nohup ./phantom_watchdog.sh > logs/watchdog_daemon.log 2>&1 &

echo -e "\033[1;32m[SUCCESS] G.O.D. Stack 2.0 deployment secured. System is running hot.\033[0m"
exit 0
