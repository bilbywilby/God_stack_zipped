# god_stack – Refactor Changelog (`feature/matrix-core-refactor`)

All bugs below were identified by static audit of the full repo tree.  
Every fix is annotated inline in the relevant file with a `# FIX:` comment.

---

## Bug Fixes

| # | File | Bug | Severity |
|---|------|-----|----------|
| 1 | `god_stack/daemon_core.py` | `self.last_run = None` shared across all jobs; first `run_forever` tick raises `TypeError: unsupported operand type(s) for -: 'datetime' and 'NoneType'`. Fixed: each job tracks its own `last_run`, seeded to `datetime.min`. | **Runtime crash** |
| 2 | `core/worker_pool.py` | `finally` block wrote `self.running = False` (no underscore), creating a new public attribute and leaving `self._running = True` permanently — `stop_pool()` could never halt the pool. | **Logic error** |
| 3 | `data_storage_sync.py` | `_init_db()` used bare `sqlite3.connect()` without a context manager; any exception from `cursor.execute()` leaked the file descriptor. | **Resource leak** |
| 4 | `metrics_exporter.py` | `SYSTEM_METRICS` dict mutated from the main thread while `serve_forever` read it from its own thread — classic data race. Added `threading.Lock` + `increment()`/`snapshot()` helpers. | **Thread safety** |
| 5 | `run_production_matrix.py` | (a) `import time` appeared on lines 5, 63, and 71 — two dead imports. (b) Two statements after the `while True:` loop were unreachable dead code. (c) `scraper.process_target()` is `async def`; calling it without `await` silently discarded the coroutine — no scraping occurred. | **Silent no-op / dead code** |
| 6 | `utils/proxy_shuffler.py` | Default `proxy_config_path` hardcoded to `/home/tangleroot013/god_stack/config/proxies.json` — breaks on CI, Docker, and any other dev machine. | **Portability** |
| 7 | `daemons/job_queue.py` | (a) Same hardcoded absolute path. (b) `pop_task()` issued `BEGIN IMMEDIATE` (exclusive write-lock) on the empty-queue `SELECT` path, unnecessarily serialising all workers on every idle poll. | **Portability / Lock contention** |
| 8 | `parsers/html_parser.py` | `list(set(links))` deduplicated raw href strings but relative paths (`/item?id=1`) were never resolved to absolute URLs, so the Frontier received unresolvable relative links. Added `urljoin(base_url, href)` resolution before deduplication. | **Data correctness** |
| 9 | `god_scraper.py` | `asyncio.Semaphore(n)` created at module import time via the module-level `GodScraperNode = GodScraper()`. In Python 3.10+ this is a `DeprecationWarning`; in 3.12+ it's a `RuntimeError` because no event loop exists at import time. Semaphore now created lazily inside `initialize()`. | **RuntimeError on Python 3.12+** |
| 10 | `utils/redis_worker.py` | `execute_transaction()` called `self.scraper.scrape(url, identity=...)` — method does not exist (correct name: `process_target`). `run_mission_loop()` slept 3600s per iteration, effectively dead. | **NameError / dead loop** |
| 11 | `utils/queue_manager.py` | `task_complete()` only logged a debug line — never actually removed the task from any store. Added `dequeue_task()` method required by the fixed `RedisWorker`. | **Silent no-op** |
| 12 | `utils/obsidian_bridge.py` | `stack_vault` hardcoded to `/home/tangleroot013/god_stack/outputs/vault`. | **Portability** |
| 13 | `god_engine.py` | Did not pass `base_url` to `parse_html()`, so relative links extracted from pages were never made absolute. | **Data correctness** |
| 14 | `scavenger.py` | `if idx := ip.replace('.', '').isdigit():` — walrus assigns the bool to `idx` (unused) and the condition evaluates as always-True for any non-empty string, admitting header rows as proxies. | **Logic error** |
| 15 | `utils/exporter.py` | `self.conn` held as an instance variable with no context manager; exceptions between `__init__` and explicit `.close()` leaked the SQLite connection. | **Resource leak** |
| 16 | `parsers/content_extractor.py` | Used a brittle `"Standard Source Tree" in raw_html` heuristic instead of calling the actual `parse_html()` pipeline, silently discarding real content. | **Silent data loss** |
| 17 | `god_stack/` inner package | `god_stack/parsers/parser_matrix.py` and `god_stack/engines/phantom_engine.py` were byte-for-byte duplicates of the root-level equivalents with no `__init__.py` making them importable — accidental shadow package. Removed. | **Structural** |

---

## Architectural Notes (not bugs, but worth tracking)

- `logging.basicConfig()` was called in 50+ modules. `basicConfig` is a no-op after the first call, so most per-module colour formats were silently discarded. Long-term fix: centralise logging config in `utils/logger.py:setup_production_logging()` and call it once at process entry.
- The `god_stack/` inner package directory shadows the root-level modules without being a proper package (missing `__init__.py` at the `god_stack/` level). After removing the duplicate files, the directory still exists but is inert.
