#!/usr/bin/env python3
import asyncio
import curses
import os
import sys
import time
import json
import logging
from parsers.dom_parser import HardenedDOMParser
from data_alchemist import DataAlchemist
from utils.logger import setup_production_logging

LOG_FILE = "logs/daemon_orchestrator.log"
METRICS_FILE = "metrics/pipeline_stats.json"
os.makedirs("logs", exist_ok=True)
os.makedirs("metrics", exist_ok=True)

logger = logging.getLogger("MatrixDaemon")

# Mock elements acting as HTML trees
class MockElement:
    def __init__(self, text, href, score_text=None):
        self.text = text
        self.href = href
        self.score_text = score_text

    def find(self, *args, **kwargs):
        if "class_" in kwargs:
            if kwargs["class_"] == "titleline" and self.text:
                return self
            if kwargs["class_"] == "score" and self.score_text:
                return self
        elif args and args[0] == "a" and self.text:
            return self
        return None

    def get_text(self, strip=True):
        return self.score_text if self.score_text else self.text

    def get(self, attr, default=""):
        return self.href if attr == "href" else default

class RefinedOrchestrator:
    def __init__(self, interval_seconds=300):
        self.interval = interval_seconds
        self.cycle_count = 0
        self.failures_encountered = 0
        self.last_execution_status = "INITIALIZED"
        self.targets = [
            "https://news.ycombinator.com/news",
            "https://news.ycombinator.com/newest",
            "https://news.ycombinator.com/best"
        ]

    def load_metrics(self):
        try:
            if os.path.exists(METRICS_FILE):
                with open(METRICS_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "tasks_total": 0, "tasks_successful": 0, "tasks_failed": 0,
            "last_latency_ms": 0.0, "avg_latency_ms": 0.0
        }

    def load_latest_logs(self, max_lines=10):
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    return f.readlines()[-max_lines:]
        except Exception:
            pass
        return []

    async def invoke_pipeline_matrix(self):
        self.cycle_count += 1
        logger.info(f"Triggering Core Pipeline Automation Matrix (Cycle #{self.cycle_count})...")
        
        stats = self.load_metrics()
        
        # Valid Mock HTML Trees matching expected attributes
        raw_mocked_responses = [
            MockElement("Target Matrix Sync Complete", self.targets[0], "90 points"),
            MockElement("Resilient Extraction Optimization", self.targets[1], "142 points"),
            None,  # Fault Target (triggers DOM safe mode)
            MockElement("   ", "Malformed Target URL", "0 points")  # Discard target
        ]

        start_ts = time.perf_counter()
        
        extracted_nodes = []
        for element in raw_mocked_responses:
            try:
                node_data = HardenedDOMParser.extract_metrics_safely(element)
                extracted_nodes.append(node_data)
            except Exception as e:
                self.failures_encountered += 1
                logger.error(f"❌ [CORE VARIATION] Critical escape failure: {e}")

        purified_dataset = DataAlchemist.optimize_array_processing(extracted_nodes)
        duration_ms = (time.perf_counter() - start_ts) * 1000
        
        stats["tasks_total"] += len(raw_mocked_responses)
        stats["tasks_successful"] += len(purified_dataset)
        stats["tasks_failed"] += (len(raw_mocked_responses) - len(purified_dataset))
        stats["last_latency_ms"] = duration_ms
        stats["total_latency_ms"] = stats.get("total_latency_ms", 0.0) + duration_ms
        stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["tasks_total"]
        stats["last_updated"] = int(time.time())

        temp_name = f"{METRICS_FILE}.tmp"
        with open(temp_name, "w") as f:
            json.dump(stats, f, indent=2)
        os.replace(temp_name, METRICS_FILE)

        self.last_execution_status = "NOMINAL_EXIT"

    def purge_sensitive_footprint(self):
        targets = [LOG_FILE, METRICS_FILE, f"{METRICS_FILE}.tmp"]
        for target in targets:
            if os.path.exists(target):
                try:
                    size = os.path.getsize(target)
                    with open(target, "wb") as shredder:
                        shredder.write(os.urandom(max(size, 1)))
                        shredder.flush()
                    os.remove(target)
                except Exception:
                    pass

    async def draw_dashboard(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

        next_run_time = time.time()

        while True:
            h, w = stdscr.getmaxyx()
            stdscr.clear()

            metrics = self.load_metrics()
            logs = self.load_latest_logs(max_lines=h - 15)

            stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(1, 2, "=" * (w - 4))
            stdscr.addstr(2, 4, "G.O.D. STACK v2.2.0 | REAL TIME TELEMETRY ORCHESTRATOR")
            stdscr.addstr(3, 2, "=" * (w - 4))
            stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

            stdscr.addstr(5, 4, f"• Sweep Cycles    : {self.cycle_count}")
            stdscr.addstr(6, 4, f"• Engine Status   : {self.last_execution_status}")
            stdscr.addstr(7, 4, f"• Handled Faults  : {self.failures_encountered}")
            
            stdscr.addstr(5, 44, f"• Total Elements  : {metrics['tasks_total']}")
            stdscr.addstr(6, 44, f"• Purified / Drop : {metrics['tasks_successful']} / {metrics['tasks_failed']}")
            stdscr.addstr(7, 44, f"• Processing Speed: {metrics['last_latency_ms']:.3f} ms")

            stdscr.addstr(9, 2, "[- ACTIVE DEPLOYMENT LOGSTREAM]")
            for idx, line in enumerate(logs):
                if 10 + idx < h - 4:
                    clean_line = line.strip()[:w - 8]
                    stdscr.addstr(10 + idx, 4, f"› {clean_line}")

            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(h - 2, 2, "[ Press 'q' to break execution thread, initiate lockdown scrub sequence ]")
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            stdscr.refresh()

            if time.time() >= next_run_time:
                await self.invoke_pipeline_matrix()
                next_run_time = time.time() + self.interval

            try:
                key = stdscr.getch()
                if key == ord('q'):
                    break
            except Exception:
                pass

            await asyncio.sleep(0.1)

def launch_daemon(stdscr):
    orchestrator = RefinedOrchestrator(interval_seconds=300)
    try:
        asyncio.run(orchestrator.draw_dashboard(stdscr))
    finally:
        orchestrator.purge_sensitive_footprint()

if __name__ == "__main__":
    setup_production_logging()
    try:
        curses.wrapper(launch_daemon)
    except KeyboardInterrupt:
        pass
