import re
from pathlib import Path

target = Path("utils/broadcast_server.py")
content = target.read_text()

# Locate the main block and inject both the resource limit logic AND ensure ThreadingHTTPServer is preserved
patch = """if __name__ == "__main__":
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target_limit = min(65535, hard)
        resource.setrlimit(resource.RLIMIT_NOFILE, (target_limit, hard))
        print(f"🔓 OS File Descriptor Limits bumped to: {target_limit}")
    except Exception as limit_err:
        print(f"⚠️ Could not bump file limits: {limit_err}")
    run_server()"""

# Replace the entry point safely
if 'if __name__ == "__main__":' in content and 'resource' not in content:
    content = content.replace('if __name__ == "__main__":', patch)
    target.write_text(content)
    print("✅ utils/broadcast_server.py successfully patched with limits and threading parameters!")
else:
    print("⚠️ Main block already modified or skipped.")
