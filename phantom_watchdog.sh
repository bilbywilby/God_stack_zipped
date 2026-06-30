#!/usr/bin/env bash
# =============================================================================
# G.O.D. STACK PHANTOM WATCHDOG v2.1.2 (phantom_watchdog.sh)
# Architecture: Continuous Process Monitor & Inline Engine Execution
# =============================================================================

TARGET_SCRIPT="run_stack_pipeline.py"
PYTHON_BIN="/home/tangleroot013/god_stack/.venv/bin/python3"

echo "[WATCHDOG] Monitoring loop activated for target: $TARGET_SCRIPT"

while true; do
    if ! pgrep -f "$TARGET_SCRIPT" > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') | [CRITICAL] $TARGET_SCRIPT is offline."
        echo "$(date '+%Y-%m-%d %H:%M:%S') | [RECOVERY] Launching engine pipeline instance..."

        # Verify the target engine script exists before trying to execute it
        if [ -f "$TARGET_SCRIPT" ]; then
            $PYTHON_BIN $TARGET_SCRIPT > logs/pipeline_runtime.log 2>&1 &
            sleep 2
        else
            # Fallback if run_stack_pipeline.py doesn't exist yet (using god_engine.py as surrogate)
            echo "$(date '+%Y-%m-%d %H:%M:%S') | [WARN] $TARGET_SCRIPT not found. Falling back to god_engine.py"
            $PYTHON_BIN god_engine.py > logs/pipeline_runtime.log 2>&1 &
            sleep 2
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') | [HEARTBEAT] Pipeline operational grid stable."
    fi
    sleep 30
done
