#!/usr/bin/env bash
# ==============================================================================
# G.O.D. Stack v2.0.0 Release Hardening & Execution Pipeline Runner
# ==============================================================================
set -e

echo -e "\033[1;34m>>> INITIALIZING G.O.D. STACK HARDENING & SYSTEM INTEGRATION TESTING <<<\033[0m"

# 1. Enforce local execution runtime environments isolation
if [ -d ".venv" ]; then
    echo "[+] Virtual environment found. Activating layer: .venv/bin/activate"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "[+] Alternative virtual environment layer found. Activating: venv/bin/activate"
    source venv/bin/activate
else
    echo -e "\033[1;31m[-] Operational Threat Alert:\033[0m No active local shell environment layer detected."
fi

# 2. Run the pure Python orchestration and automated patch testing suite
python3 run_integration_tests.py

# 3. Synchronize workspace repository tree staging policies
echo "[+] Rewriting tracking matrix rules (.gitignore)..."
cat << 'GITEOF' > .gitignore
__pycache__/
*.py[cod]
.venv/
venv/
*.sqlite
storage/
logs/
metrics/
outputs/
datasets/
vaults/*
!vaults/index.html
.env
GITEOF

# 4. Commit verified code updates cleanly to Git tracking trees
echo "[+] Compiling system changes into workspace git branch trees..."
git add patch_pipeline.py run_integration_tests.py run_stack_pipeline.py .gitignore requirements.txt 2>/dev/null || true

if ! git diff-index --quiet HEAD --; then
    git commit -m "fix(pipeline): patch constructor argument constraints, restore importing references, and map core testing matrices"
else
    echo "[*] Working directory status is clean. Skipping commit loop generation sequence."
fi

# 5. Fast-forward milestone tag tracking positions safely
echo "[+] Relocating cryptographic development version milestones (v2.0.0)..."
git tag -d v2.0.0 2>/dev/null || true
git tag -a v2.0.0 -m "Release G.O.D. Stack Version 2.0.0 (Matrix Verified Stable Build)"

echo -e "\033[1;32m[+ SUCCESS] G.O.D. Stack v2.0.0 Deployment Hardened and Verified.\033[0m\n"
