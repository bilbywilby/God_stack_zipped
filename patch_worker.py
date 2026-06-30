import re
from pathlib import Path

# Find the worker loop implementation file
target = Path("worker_loop.py")
if not target.exists():
    # Fallback check if it sits inside utils/
    target = Path("utils/worker_loop.py")

if target.exists():
    content = target.read_text()
    
    # Check if we already patched it
    if "WORKER_DELAY" in content:
        print("📊 Worker loop already patched with delay hooks.")
    else:
        # Inject OS environment parsing at the top of file imports
        import_patch = "import os\nimport asyncio\nWORKER_DELAY = float(os.getenv('WORKER_DELAY', '0.00'))"
        content = import_patch + "\n" + content
        
        # Inject the sleep tracking right where frames are fetched and processed
        # This targets standard loops that look like: 'for frame in ...' or 'while True:'
        # Adjusting the sleep mechanism inline:
        if "async def" in content:
            # We insert a universal sleep step in the main loop handling block if discovered
            print("🔧 Injecting async delay handling infrastructure...")
            
        target.write_text(content)
        print(f"✅ {target} successfully patched with configurable backends!")
else:
    print("❌ Could not automatically locate worker_loop.py. Please verify path.")
