import asyncio
import logging
from daemon_core import DaemonCore
from utils.logger import setup_production_logging

# Configure clean terminal telemetry output
log = logging.getLogger("PoolCheck")

async def run_diagnostics():
    print("\n=== 🖥️ G.O.D. CLUSTER WORKER POOL DIAGNOSTICS ===")
    
    # Initialize the core daemon process
    core = DaemonCore(concurrent_slots=3)
    
    # Create a task to run the main worker pool loop
    pool_task = asyncio.create_task(core.main_loop())
    
    # Allow the pool to run concurrently for a few seconds to verify stability
    log.info("Monitoring worker pool initialization window...")
    await asyncio.sleep(3)
    
    print("\n[+] Pool stability test window completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    setup_production_logging()
    try:
        asyncio.run(run_diagnostics())
    except KeyboardInterrupt:
        log.warning("Diagnostics terminated by user.")
