# G.O.D. STACK
### Global Orchestration Daemon — Async Web Intelligence Pipeline

Python 3.11+ · Crostini/Debian · selectolax · courlan · Prometheus · Grafana

---

## What it is

An async, domain-bucketed web scraper with a live curses TUI dashboard, SQLite task queue, proxy rotation, anti-bot detection, and a Prometheus/Grafana observability stack. Targets are fetched and extracted by a concurrency-bounded engine, discovered links are re-enqueued into a frontier with crawl-trap detection, and all telemetry is written to a JSON metrics store consumed by the dashboard in real time.

The primary target for current configurations is Hacker News, but the pipeline is target-agnostic — any URL list works.

---

## Architecture

```
main.py
 ├── daemon       GodOrchestrator (TUI loop) → GodEngine → parsers/html_parser
 ├── worker       WorkerNode → DistributedWorkQueue (SQLite) → GodEngine
 ├── batch        BatchRunner → UrlSanitizer → CaptchaHandler
 └── scrape <url> GodOrchestrator.execute_mission → stdout JSON

GodScraper (concurrent)
 └── asyncio.Semaphore(N) → GodEngine.fetch_and_extract → FrontierManager.enqueue_batch

FrontierManager
 └── domain-bucketed deque (round-robin) → CourlanRouter (trap detection)

Observability
 └── Prometheus PushGateway → Grafana dashboard (docker-compose)
```

**Key design decisions:**

- `GodEngine` is instantiated once per process and injected into orchestrator, scraper, and worker. No module-level singletons.
- `asyncio.run()` owns the process lifecycle. Curses is initialized inside the async coroutine, not the other way around.
- `DistributedWorkQueue` uses `BEGIN IMMEDIATE` on SQLite to serialize concurrent workers on a single machine. For multi-host distribution, swap for PostgreSQL.
- `FrontierManager` maintains a `seen_urls` set for deduplication and rotates domain buckets to avoid hammering a single host.

---

## Directory structure

```
god_stack/
├── main.py                     # Single canonical entrypoint
├── god_engine.py               # Core async extraction engine
├── god_scraper.py              # Concurrent URL processor (semaphore-bounded)
├── orchestrator.py             # Pipeline coordinator: sanitize → proxy → extract
├── daemon_core.py              # Curses TUI dashboard + pipeline loop
├── worker_node.py              # Standalone SQLite queue consumer
├── batch_runner.py             # One-shot sequential sweep
├── frontier_manager.py         # Domain-bucketed URL frontier
├── courlan_router.py           # URL validation + crawl-trap detection
├── url_sanitizer.py            # WHATWG normalization, tracker stripping
├── scavenger.py                # Public proxy harvest + verification
├── captcha_handler.py          # CF/reCAPTCHA/hCaptcha signature detection
├── data_alchemist.py           # Record filter + normalization pass
├── parsers/
│   ├── html_parser.py          # selectolax C-backed HTML extraction
│   └── dom_parser.py           # HardenedDOMParser (MockElement interface)
├── utils/
│   └── work_queue.py           # SQLite task queue (PENDING → PROCESSING → DONE)
├── tests/
│   └── test_core.py            # Full regression suite (pytest-asyncio)
├── config/
│   ├── target_urls.json        # URL list for batch mode
│   └── proxies.json            # Static proxy pool override
├── vaults/                     # Obsidian knowledge graph + queue DB (gitignored)
├── grafana/                    # Grafana provisioning config
├── docker-compose.yml          # Prometheus + Grafana + PushGateway + node-exporter
├── god-orchestrator.service    # systemd unit for daemon mode
├── requirements.txt
└── pytest.ini
```

---

## Requirements

- Python 3.11+
- Debian Bookworm / Crostini (primary test environment)
- Docker + Docker Compose (optional — observability stack only)

---

## Installation

```bash
git clone https://github.com/tangleroot013/god_stack.git
cd god_stack
git checkout main

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Copy and configure the environment file:

```bash
cp .env.example .env
# Edit .env — set proxy pool, jitter values, telemetry paths
```

---

## Usage

All modes go through the single entrypoint:

```bash
# Live curses TUI dashboard (default — runs pipeline on 300s interval)
python main.py daemon

# Standalone task queue worker (polls vaults/queue.db)
python main.py worker

# One-shot batch sweep from config/target_urls.json
python main.py batch

# Single URL extraction to stdout as JSON
python main.py scrape https://news.ycombinator.com/newest
```

**Single URL output example:**

```json
{
  "url": "https://news.ycombinator.com/newest",
  "status": "SUCCESS",
  "metrics": {
    "payload_bytes": 48291,
    "discovered_anchors_count": 312
  },
  "extracted_data": {
    "title": "New Links | Hacker News",
    "body": "...",
    "links": ["https://...", "..."]
  }
}
```

---

## Configuration

### `config/target_urls.json`

URL array consumed by `python main.py batch`:

```json
[
  "https://news.ycombinator.com/news",
  "https://news.ycombinator.com/newest",
  "https://news.ycombinator.com/best"
]
```

### `config/proxies.json`

Static proxy pool override (bypasses live scavenging):

```json
["http://127.0.0.1:8080", "socks5://127.0.0.1:9050"]
```

### `.env`

| Variable | Default | Description |
|---|---|---|
| `OUTBOUND_PROXY_POOL` | — | Comma-separated proxy endpoints |
| `PROXY_ROTATION_STRATEGY` | `round_robin` | `round_robin` / `random` / `latency_optimized` |
| `SCRAPE_JITTER_MIN` | `0.1` | Min politeness delay (seconds) |
| `SCRAPE_JITTER_MAX` | `0.4` | Max politeness delay (seconds) |
| `SPOOF_USER_AGENTS` | `true` | Rotate via `fake-useragent` |
| `LATENCY_P95_MAX_THRESHOLD_MS` | `100` | Alert threshold for Prometheus |

---

## Observability stack

Start the full Prometheus + Grafana + PushGateway + node-exporter stack:

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Grafana dashboard | http://localhost:3000 (admin / admin) |
| Prometheus | http://localhost:9090 |
| PushGateway | http://localhost:9091 |
| Node Exporter | http://localhost:9100 |

The daemon writes pipeline metrics to `metrics/pipeline_stats.json` on every cycle. The Prometheus scrape config at `prometheus.yml` pulls from PushGateway.

---

## Daemon as a systemd service

```bash
# Edit god-orchestrator.service — replace User and WorkingDirectory with your paths
sudo cp god-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable god-orchestrator
sudo systemctl start god-orchestrator

# Logs
journalctl -u god-orchestrator -f
# or
tail -f logs/daemon_orchestrator.log
```

The service unit `ExecStart` now points to `python main.py daemon` — update the path to your venv interpreter if not using the system Python.

---

## Running tests

```bash
python -m pytest tests/ -v
```

Test coverage (`tests/test_core.py`):

| Class | What it tests |
|---|---|
| `TestUrlSanitizer` | Scheme injection, tracker stripping, query sort, fragment drop, host lowercase |
| `TestHtmlParser` | Title extraction, link filtering, payload ceiling, deduplication |
| `TestGodEngine` | Lifecycle, correct API surface, oversized payload abort, no-singleton assertion |
| `TestGodOrchestrator` | Mission execution, invalid URL handling, `process_target_array` absence guard |
| `TestWorkerNode` | `CancelledError` handled cleanly, engine shutdown in `finally` block |
| `TestDaemonCore` | `avg_latency_ms` is per-cycle mean, not per-item diluted average |
| `TestFrontierManager` | Deduplication, round-robin domain rotation, flush, stats accuracy |
| `TestDataAlchemist` | Empty title/url filter, valid passthrough, non-dict rejection |
| `TestCaptchaHandler` | Cloudflare, reCAPTCHA, hCaptcha detection, clean page |
| `TestProxyScavenger` | Walrus operator fix — IP validation correctness |

---

## Bug history (v2.2.0 → current)

All bugs below were present in `feature/matrix-core-refactor` and are fixed in `main`.

**`orchestrator.py` — hard crash on every mission execution.**
`execute_mission` called `self.engine.process_target_array([clean_url])`. That method does not exist on `GodEngine` — the API diverged during the refactor. Fixed: replaced with `await self._engine.fetch_and_extract(clean_url)`.

**Dual engine instantiation — split state, no shared initialization.**
`GodOrchestrator` created its own `GodEngine()` internally; `god_scraper.py` imported the module-level `GodEngineNode` singleton. Two separate instances, neither guaranteed initialized. Fixed: engine is injected at construction time across all callers.

**Module-level singletons — hidden global state.**
`GodEngineNode = GodEngine()` in `god_engine.py` and `GodScraperNode = GodScraper()` in `god_scraper.py`. Tests and multi-module imports shared state silently. Both removed.

**`daemon_core.py` — `asyncio.run()` inside `curses.wrapper()`.**
Works as `__main__` but raises `RuntimeError: This event loop is already running` the moment any async caller imports the module. Fixed: `asyncio.run()` owns the process; curses is initialized inside the async coroutine and torn down in `finally`.

**`daemon_core.py` — `avg_latency_ms` semantic error.**
Divided `total_latency_ms` by `tasks_total` (item count), not cycle count. On cycle 10 processing 4 items/cycle, the denominator was 40 — a meaningless diluted figure. Fixed: `total_cycle_latency_ms / cycle_count`.

**`worker_node.py` — `KeyboardInterrupt` never fires in coroutine context.**
`asyncio.run()` converts SIGINT to `CancelledError` on the main task. The `except KeyboardInterrupt` branch was dead code; `finally: await scraper.shutdown()` was unreliable. Fixed: catch `asyncio.CancelledError` at the coroutine boundary with a guaranteed `finally` block.

**`scavenger.py` — walrus operator misuse.**
`if idx := ip.replace('.', '').isdigit():` assigned the boolean to `idx` (never used) and tested the boolean as the branch condition. Evaluates correctly by accident; the variable is semantically wrong. Fixed: `if ip.replace(".", "").isdigit():`.

**`utils/work_queue.py` — hardcoded absolute path.**
`db_path="/home/tangleroot013/god_stack/vaults/queue.db"` fails on every other machine. Fixed: default is `vaults/queue.db` relative to working directory.

**`batch_runner.py` — wrong import paths.**
Imported from `utils.url_sanitizer` and `utils.captcha_handler` but those were 73-byte stub files. Canonical implementations live at root. Fixed.

**`logging.basicConfig()` in every module — config-stomping race.**
Import order determined which module's format string won. Removed from all modules; root config is set once in `main.py`.

**`courlan_router.py` — `log.info` on every URL validation.**
At crawl scale this produces millions of lines per hour. Demoted to `log.debug`; rejections stay at `WARNING`.

---

## What was removed

| Removed | Reason |
|---|---|
| `patch_pipeline.py`, `patch_worker.py`, `patch_server.py`, `patch_mmap_gateway.py`, `patch_ingest_shedder.py`, `patch_raw_shedder.py`, `patch_execution_delay.py` | Hotfix scripts layered on top of broken source instead of fixing source. Logic folded into the files they were patching. |
| `run_stack.py`, `run_orchestrator.py`, `run_orchestrator_clean.py`, `run_unified_stack.py`, `run_all.py`, `run_stack_pipeline.py` | Six entry points for one pipeline. Replaced by `main.py` with four subcommands. |
| `finalize_deployment.sh`, `finalize_god_stack.sh`, `finalize_release.sh`, `deploy_missing_stealth_core.sh`, `deploy_orchestrator.sh` | Deployment scripts that were baking hotfixes into releases instead of committing them. |
| `sitecustomize.py.bak` | `sitecustomize.py` runs at Python interpreter startup and affects the entire environment. A `.bak` copy in the repo root is a contamination risk and has no place in VCS. |
| `streamlit`, `altair`, `pyarrow`, `pydeck`, `narwhals`, `pandas` | Pulled in by a Streamlit dashboard that exists nowhere in the codebase. ~450MB install footprint removed. |
| `config/backups/*.json.bak` | Five timestamped copies of `target_urls.json` in VCS. Now covered by `.gitignore`. |

---

## Known limitations

`purge_sensitive_footprint()` performs a single-pass `os.urandom` overwrite before unlinking. This is adequate for local cache hygiene but is **not** a forensic-grade wipe on journaled filesystems (ext4, APFS, NTFS). Use `shred -u` or full-disk encryption if the files contain sensitive material.

The proxy scavenger pulls from `free-proxy-list.net` and validates nodes against `www.google.com`. Public free proxies have high churn; verified count is typically low. For sustained workloads, supply a static pool in `config/proxies.json` or via `OUTBOUND_PROXY_POOL` in `.env`.

`DistributedWorkQueue` uses SQLite `BEGIN IMMEDIATE` for worker coordination. This serializes correctly on a single machine with multiple workers but is not suitable for distributed multi-host deployments. Swap the queue backend for PostgreSQL with `SELECT ... FOR UPDATE SKIP LOCKED` for that use case.

---

## License

MIT
