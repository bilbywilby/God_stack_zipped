#!/usr/bin/env python3
import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def run_sanity_check():
    print("==================================================")
    print("🛰️  G.O.D. STACK SYSTEM SANITY CHECK INITIALIZED")
    print("==================================================\n")

    print("[1/3] Testing package imports...")
    try:
        from utils.logger import setup_production_logging
        from prometheus_exporter import WORKER_EXECS
        from workers.example_worker import run_example_payload
        print("✅ All core modules, utilities, and exporters loaded smoothly.")
    except ImportError as e:
        print(f"❌ Critical Import Error: {e}")
        sys.exit(1)

    print("\n[2/3] Testing logging engine structures...")
    try:
        logger = setup_production_logging()
        logger.info("🧪 Test Harness: Structured log verification checkpoint passed.")
        print("✅ Production logging system ready.")
    except Exception as e:
        print(f"❌ Logging System Failure: {e}")
        sys.exit(1)

    print("\n[3/3] Running isolated worker execution check...")
    try:
        print("⚙️  Invoking sample worker dry-run payload...")
        await run_example_payload()
        print("✅ Isolated payload completed with zero exceptions.")
    except Exception as e:
        print(f"❌ Worker Execution Failed: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("🎉 SANITY CHECK COMPLETE: STACK IS IN GO-STATUS!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_sanity_check())
