#!/usr/bin/env bash
set -euo pipefail

echo "[⚙️] Beginning G.O.D. Stack asset orchestration configuration..."

# 1. Guarantee structural layout setup
mkdir -p config parser utils logs vaults

# 2. Compile dynamic target profile matrix
echo "[⚙️] Writing config/targets.json..."
cat << 'TARGETS_JSON' > config/targets.json
{
  "targets": [
    {
      "url": "https://news.ycombinator.com"
    }
  ]
}
TARGETS_JSON

# 3. Compile the structural runner logic matrix
echo "[⚙️] Compiling run_orchestrator.sh..."
cat << 'RUNNER_SCRIPT' > run_orchestrator.sh
#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------
# 0️⃣  Environment preparation
# -------------------------------------------------
if [ -d ".venv" ]; then               # bind the virtual‑env *once* for the whole script
    export PATH="${PWD}/.venv/bin:${PATH}"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

export VAULT_DIR="${SCRIPT_DIR}/vaults"
export CONFIG_FILE="${SCRIPT_DIR}/config/targets.json"
mkdir -p "${VAULT_DIR}" logs

# -------------------------------------------------
# 1️⃣  Ensure the SQLite table exists
# -------------------------------------------------
if ! sqlite3 storage.sqlite \
   "SELECT name FROM sqlite_master WHERE type='table' AND name='ingestion_records';" \
   | grep -q ingestion_records; then
    if [ -f "./scripts/init_db.py" ]; then
        python3 ./scripts/init_db.py
    else
        sqlite3 storage.sqlite "
        CREATE TABLE IF NOT EXISTS ingestion_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT
        );"
    fi
fi

# -------------------------------------------------
# 2️⃣  Run identifier & logfile
# -------------------------------------------------
RUN_ID="$(date +%s)_$(tr -dc a-zA-Z0-9 </dev/urandom | head -c4 2>/dev/null || echo unq)"
export GOD_RUN_ID="${RUN_ID}"
LOG_FILE="${SCRIPT_DIR}/logs/orchestrator_$(date -u +%Y%m%dT%H%M%SZ).log"
mkdir -p "$(dirname "${LOG_FILE}")"

# -------------------------------------------------
# 3️⃣  Load targets (dynamic JSON → fallback static)
# -------------------------------------------------
if [ -f "${CONFIG_FILE}" ] && command -v jq &>/dev/null; then
    mapfile -t TARGETS < <(jq -r '.targets[].url' "${CONFIG_FILE}")
else
    TARGETS=("https://news.ycombinator.com"\)
fi

# -------------------------------------------------
# 4️⃣  Helper – run the parser chain for a single URL
# -------------------------------------------------
run_engine_for_target() {
    local target_url=$1
    echo "[INFO] Processing Target Asset Profile: ${target_url}"

    # Primary parser
    if python3 parser/god_dom_parser.py /tmp/target_snapshot.html "${VAULT_DIR}/vault_${RUN_ID}.json" 2>/dev/null; then
        return 0
    fi

    # Fallback renderer (if primary fails)
    if [ -f "parser/fallback_renderer.py" ]; then
        echo "[INFO] Primary parser dropped out. Invoking fallback matrix..."
        if python3 parser/fallback_renderer.py "${target_url}" /tmp/target_snapshot.html; then
            python3 parser/god_dom_parser.py /tmp/target_snapshot.html "${VAULT_DIR}/vault_${RUN_ID}.json"
            return $?
        fi
    fi

    return 1   # both primary & fallback failed
}

# -------------------------------------------------
# 5️⃣  Main orchestration loop (wrapped in a function)
# -------------------------------------------------
main() {
    {
        echo "[INFO] Starting G.O.D. Stack Cluster Orchestration Sequence Engine"
        echo "[INFO] Active Frame Cycle: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "----------------------------------------------------------"

        local global_failed=0                # `local` is *allowed* inside this function

        for TARGET_URL in "${TARGETS[@]}"; do
            echo "[INFO] Processing Target: ${TARGET_URL}"

            # ---- runtime delta tracking (ms) ----
            START_TIME=$(date +%s%3N)

            set +e
            run_engine_for_target "${TARGET_URL}"
            engine_status=$?                # <-- no `local` here
            set -e

            END_TIME=$(date +%s%3N)
            DURATION=$((END_TIME - START_TIME))

            if [ "${engine_status}" -eq 0 ]; then
                python3 -c "
import sys; sys.path.append('utils');
from telemetry import log_ingestion;
log_ingestion('${TARGET_URL}', '${RUN_ID}', 'SUCCESS', ${DURATION})
"
                echo "[SUCCESS] Metrics captured cleanly in ${DURATION}ms"
            else
                python3 -c "
import sys; sys.path.append('utils');
from telemetry import log_ingestion;
log_ingestion('${TARGET_URL}', '${RUN_ID}', 'ERROR', ${DURATION}, 'Pipeline exhausted parsing vectors.')
"
                echo "[ERROR] Failure sequence recorded in ${DURATION}ms"
                global_failed=1
            fi
            echo "----------------------------------------------------------"
        done

        echo "=========================================================="
        echo " ORCHESTRATION SUMMARY "
        echo "=========================================================="
        echo " Frame Event: $(date '+%Y-%m-%d %H:%M:%S')"
        echo " Log Target: ${LOG_FILE}"
        echo " Run Identifier: ${RUN_ID}"
        if [ "${global_failed}" -eq 0 ]; then
            echo " System State: SUCCESS OPERATIONAL"
            exit 0
        else
            echo " System State: PARTIAL FAILURE / DEGRADED"
            exit 1
        fi
        echo "=========================================================="
    } 2>&1 | tee -a "${LOG_FILE}"
}

main
RUNNER_SCRIPT

# 4. Correct file access execution modes
chmod +x run_orchestrator.sh
echo "[🚀] Operational matrix successfully loaded and locked into production."
