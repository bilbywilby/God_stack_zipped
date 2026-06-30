# god_stack – v2 Changelog (consolidating `main` onto the fixed `matrix-core-refactor` base)

## Context

`main` was found to be a divergent branch — not a merge of the earlier
`feature/matrix-core-refactor` fixes. It grew from ~70 to ~330 files but the
core engine modules (`daemon_core.py`, `worker_pool.py`, `god_scraper.py`,
`data_storage_sync.py`, `metrics_exporter.py`, `proxy_shuffler.py`,
`job_queue.py`) were byte-identical to the **pre-fix** versions: all 9
previously-fixed bugs were present again because they were never actually
fixed on this line of history.

This version (v2) starts from the verified, fixed `matrix-core-refactor`
base and selectively ports the genuinely new logic from `main`, fixing
what was broken there rather than carrying the bugs forward.

---

## New critical bug found and fixed (not in any prior audit)

**`frontier_manager.py` — `Frontier = FrontierManager` (bare class, not an
instance).** Every downstream caller (`god_scraper.py`,
`run_unified_stack.py`, `unified_matrix_core.py`,
`unified_production_core.py`) called `Frontier.enqueue_batch(urls)`
expecting instance state (`self.seen_urls`, `self.domain_buckets`). Calling
an unbound method this way silently passes `urls` as `self` — guaranteed
`TypeError` or silent corruption depending on call shape. Two more call
sites referenced `Frontier.add_url()` and `Frontier.get_queue()`, neither
of which existed on the class at all — guaranteed `AttributeError` on
first use. Fixed: instantiated correctly (`Frontier = FrontierManager()`),
`add_url()` and `get_queue()` added, and the whole class made
thread-safe with an internal lock since it's now a shared mutable
structure touched by concurrent resilience-layer producers.

**`central_supervisor.py` (main) was integration theater.**
`bootstrap_pipeline_mesh()` logged `"RateLimiter [OK] | CircuitBreaker
[OK] | DualBuffer [OK]"` and set `subsystems_active = True`
unconditionally, without importing or calling any of those modules. Not
ported — replaced by actual wiring in `god_scraper.py` (see below).

**`scripts/deploy/*.sh` (105 files) were not deployment automation.**
Each script was a `cat << 'PYEOF' > module.py` heredoc that re-emitted a
byte-identical copy of a module already at repo root (confirmed via
diff). This is the likely origin mechanism for main's file-count
explosion without a corresponding increase in real functionality. Not
ported. If any of these scripts are run against a fixed checkout, they
will silently overwrite fixed files with the unfixed originals — treat
the whole directory as load-bearing only for the rare case where a
heredoc differs from its root counterpart, which was not observed in
this audit.

---

## Resilience primitives ported from `main` (`resilience/` package)

Six single-purpose modules existed on `main` as isolated demo scripts —
each correct or near-correct in isolation, but never imported by
`god_scraper.py`, `god_engine.py`, or any orchestration loop. Ported into
a proper package and **actually wired into the real fetch path** in
`god_scraper.py`:

| Module | Status on `main` | Fix applied during port |
|---|---|---|
| `sliding_rate_limiter.py` | Correct as-is | None — ported unchanged |
| `jittered_retry.py` | Correct as-is | None — ported unchanged |
| `adaptive_concurrency.py` | Correct as-is | Added type hints, return value |
| `load_shedder.py` | Correct logic | Removed `print()` from a hot-path decision function |
| `dead_letter_stream.py` | Correct logic | Added async-safe write path (`asyncio.to_thread`), human-readable timestamp |
| `dual_buffer.py` | **Race condition** | `asyncio.create_task()`'d flushes had no guard against a second flush starting before the first completed, risking the in-flight buffer being overwritten mid-write. Fixed with an `asyncio.Event` gate. |
| `network_backoff.py` | **Not ported** | Imported `tkinter` for a "backoff tracker" widget — a GUI dependency with no place in a headless scraper's resilience layer; would crash in any container without an X server. |

### Actual integration (new — main never did this)

`god_scraper.py` now calls, on the real fetch path:
- `SlidingRateLimiter.acquire(domain=...)` before every fetch, keyed per-domain
- `ResilientRetryCircuit.execute_with_jitter(...)` wrapping the fetch call
- `ConcurrencyThrottleMatrix.evaluate_performance_telemetry(...)` after every
  fetch, dynamically resizing the next batch size from observed latency
- `HighWatermarkLoadShedder.audit_ingest_safety(...)` gating each orchestration
  tick against frontier queue depth as a backpressure proxy
- `DeadLetterAuditStream.route_async(...)` quarantining any URL that exhausts
  all retries, instead of silently logging and dropping it
- `AsymmetricPayloadBuffer.ingest_payload(...)` for non-blocking persistence of
  discovered links, flushed on shutdown via `flush_remaining()`

---

## Architectural fix: centralized logging (43 files affected)

`main` had **43 separate modules** independently calling
`logging.basicConfig()`. Since `basicConfig()` is a documented no-op
after the first call in a process, whichever module happened to import
first silently won and applied its format to every logger in the
process — including completely unrelated loggers. Confirmed in a live
smoke test: every log line in the process, regardless of source module,
was tagged `[COURLAN-ROUTER]` because `courlan_router.py` happened to
import first.

Fixed:
- `utils/logger.py` rewritten to configure the **root** logger (not a
  named `"GodStack"` logger), so every module's `logging.getLogger(name)`
  call inherits correctly and `%(name)s` reports the real source.
- Default `log_dir` changed from `/var/log/god_stack` (requires root,
  fails by default in Crostini/Debian containers) to a repo-relative
  `logs/` directory, with `PermissionError` still caught so file logging
  degrades gracefully rather than crashing the process.
- All 43 `basicConfig()` call sites removed.
- `setup_production_logging()` inserted as the first statement in each of
  the 39 real `if __name__ == "__main__":` entry points.
- 4 files (`connection_pool.py`, `utils/monitor_relay.py`,
  `utils/redis_metrics.py`, `utils/scheduler.py`) had `basicConfig()` at
  *module level* — meaning merely importing them reconfigured the entire
  process's logging as a side effect. These are now silent on import, as
  a library module should be.

Verified post-fix via smoke test: log lines now correctly report
`[GodScraper]`, `[GodEngine]`, `[AdaptiveConcurrency]`, etc., and the
structured JSON file handler captures the real `logger` field per line.

---

## Files NOT ported from `main`

- `scripts/deploy/*.sh` (105 files) — heredoc duplicators, not deployment tooling
- `unified_matrix_core.py`, `unified_production_core.py`,
  `master_mesh_runtime.py`, `central_supervisor.py` — four parallel,
  non-integrating "unification" attempts, each calling the broken
  `Frontier` API independently; superseded by the real integration in
  `god_scraper.py`
- ~50 single-purpose GUI/diagnostic/watchdog stubs (`gui_*.py`,
  `*_watchdog.py`, `*_purger.py`, etc.) with no call sites anywhere in
  the codebase — dead code with no consumers
