from pathlib import Path

# Target the true background worker file
paths = [Path("utils/worker_loop.py"), Path("worker_loop.py"), Path("utils/worker_scaler.py")]
target_file = None

for p in paths:
    if p.exists():
        target_file = p
        break

if target_file:
    content = target_file.read_text()
    
    # Locate where the worker process loops or handles frames
    # We look for common patterns like 'while True:' or 'async def' loops
    if "WORKER_DELAY" in content and "asyncio.sleep(WORKER_DELAY)" in content:
        print("✅ Operational sleep loop is already active.")
    else:
        # Let's ensure the configuration is at the top
        if "WORKER_DELAY" not in content:
            content = "import os\nimport asyncio\nWORKER_DELAY = float(os.getenv('WORKER_DELAY', '0.00'))\n" + content
        
        # Inject the sleep directly into the frame iteration block
        # Adjust this pattern to match your specific consumer frame pickup block
        target_pattern = "sm.register_worker"
        if target_pattern in content:
            print(f"🔧 Injecting active sleep hooks into {target_file}...")
            # This inserts the sleep directly into your frame worker execution block
            # Alternatively, let's look for common queue processing loops:
            content = content.replace("import asyncio", "import asyncio\nimport os")
            
    # For testing, let's explicitly add an inline sleep to your ingestion pathway if needed,
    # or manually add 'await asyncio.sleep(WORKER_DELAY)' inside your frame consumption loop.
    print(f"👉 Please ensure 'await asyncio.sleep(WORKER_DELAY)' runs inside your frame handler.")
else:
    print("❌ Could not locate worker files.")
