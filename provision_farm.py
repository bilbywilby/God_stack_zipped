#!/usr/bin/env python3
"""
G.O.D. Stack – Production Farm Provisioning (Reinforced API Engine)
Phase 2 (Automation) + Phase 3 (Prometheus Deployment)
"""

import os
import sys
import json
import time
import subprocess
import stat
import yaml
from pathlib import Path

def run_cmd(cmd, capture: bool = False, check: bool = False):
    kwargs = {"text": True}
    if capture:
        kwargs["capture_output"] = True

    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n{result.stderr or result.stdout}"
        )
    return result

def ensure_network(name: str):
    exists = run_cmd(["docker", "network", "inspect", name], capture=True).returncode == 0
    if not exists:
        print(f"[ℹ️] Creating Docker network '{name}' …")
        run_cmd(["docker", "network", "create", name], check=True)
    else:
        print(f"[✅] Docker network '{name}' already present.")

def write_yaml(path: Path, data: dict):
    with path.open("w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"[✓] {path.name} written.")

def container_exists(name: str) -> bool:
    return (
        run_cmd(
            ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
            capture=True,
        )
        .stdout.strip()
        == name
    )

def wait_for_prometheus(url: str, timeout: int = 30, interval: float = 1.0):
    """Poll the target endpoint until we obtain a valid, parsable JSON response."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = run_cmd(["curl", "-s", url], capture=True).stdout
            json.loads(resp)
            return resp
        except Exception:
            time.sleep(interval)
    raise RuntimeError(f"Prometheus API at {url} did not become ready within {timeout}s")

# 1️⃣ Write Prometheus Config
prom_cfg = {
    "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
    "scrape_configs": [
        {
            "job_name": "god_pushgateway",
            "static_configs": [{"targets": ["god_pushgateway:9091"]}],
        }
    ],
}
cwd = Path.cwd()
prom_file = cwd / "prometheus.yml"
write_yaml(prom_file, prom_cfg)

# 2️⃣ Docker Network & Prometheus Container Management
ensure_network("god_network")

if container_exists("god_prometheus"):
    print("[⚙️] Removing old 'god_prometheus' container …")
    run_cmd(["docker", "rm", "-f", "god_prometheus"], check=True)

docker_cmd = [
    "docker",
    "run",
    "-d",
    "--name",
    "god_prometheus",
    "--network",
    "god_network",
    "-p",
    "9090:9090",
    "-v",
    f"{prom_file}:/etc/prometheus/prometheus.yml:ro",
    "--restart",
    "unless-stopped",
    "prom/prometheus:v2.53.0",
]
print("[⚙️] Starting Prometheus container …")
res = run_cmd(docker_cmd, capture=True, check=True)
container_id = res.stdout.strip()[:12]
print(f"[✓] Prometheus container launched → {container_id}")

# 3️⃣ Systemd Unit Compilation
service_path = cwd / "god-orchestrator.service"
service_content = f"""[Unit]
Description=G.O.D. Stack Orchestrator Engine Loop
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={cwd}
ExecStart={cwd}/run_orchestrator.sh
Environment="PATH={cwd}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
service_path.write_text(service_content)
print(f"[✓] Systemd unit written → {service_path.name}")

# 4️⃣ Robust Sanity Check via Polling Core
print("\n🔎 Executing Synchronous Health Verification Loop...")
try:
    health_json = wait_for_prometheus("http://localhost:9090/api/v1/targets")
    targets = json.loads(health_json).get("data", {}).get("activeTargets", [])
    if not targets:
        print(" • No active sync targets found yet (initializing...)")
    for t in targets:
        print(f" • {t.get('scrapeUrl')} – Status: [{t.get('health').upper()}]")
except Exception as exc:
    print(f"[⚠️] Critical Validation Failure: {exc}")

# 5️⃣ User Execution Guide
print("\n🚀 Next Steps (Run as root or with sudo):")
print(f"  sudo cp {service_path.name} /etc/systemd/system/")
print("  sudo systemctl daemon-reload")
print("  sudo systemctl enable --now god-orchestrator.service")
print("\n📈 Open http://localhost:9090 in a browser to explore metrics.")
print("\n✅ Provisioning script completed successfully.")
