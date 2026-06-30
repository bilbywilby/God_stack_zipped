import os
from pathlib import Path

target = Path("utils/broadcast_server.py")
content = target.read_text()

# Inject environment checks dynamically into the routing path
old_block = """            else:
                std_depth = 0
                if std_depth > 400:"""

new_block = """            else:
                std_depth = 0
                max_allowed = int(os.environ.get("STD_MAX_QUEUE", 400))
                if std_depth > max_allowed:"""

if old_block in content:
    content = content.replace(old_block, new_block)
    target.write_text(content)
    print("✅ Dynamic queue load-shedding applied to gateway mesh configuration.")
else:
    print("⚠️ Target block already patched or structure mismatched.")
