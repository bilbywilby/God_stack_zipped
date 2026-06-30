# ==============================================================================
# G.O.D. STACK PROMETHEUS METRICS EXPORTER (prometheus_exporter.py)
# Architecture: Core Infrastructure Telemetry & Operational Counters
# ==============================================================================

try:
    from prometheus_client import Counter, Gauge, start_http_server
except ImportError:
    # Fallback mock classes if prometheus_client is missing in the local .venv
    class Counter:
        def __init__(self, name, documentation, labelnames=()): self.name = name
        def labels(self, *args, **kwargs):
            class MockLabel:
                def inc(self, amount=1): pass
            return MockLabel()
    class Gauge:
        def __init__(self, name, documentation, labelnames=()): self.name = name
        def labels(self, *args, **kwargs):
            class MockLabel:
                def set(self, val): pass
            return MockLabel()
    def start_http_server(port): pass

# Core telemetry registration targets expected by verify_stack.py
WORKER_EXECS = Counter('god_stack_worker_executions_total', 'Total executed worker iterations', ['worker_id', 'status'])
PIPELINE_LATENCY = Gauge('god_stack_pipeline_latency_seconds', 'Active pipeline round-trip latency tracking')
SCRAPE_SUCCESS_TOTAL = Counter('god_stack_scrape_success_total', 'Total successful database extractions')

def init_metrics_server(port=8000):
    try:
        start_http_server(port)
    except Exception as e:
        print(f"[METRICS] Failed to bind server on port {port}: {e}")
