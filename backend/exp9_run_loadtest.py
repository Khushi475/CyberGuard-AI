"""Experiment 9, Task 2 - execute the load / performance test and record results.

Runs the same workload that is defined in
documentation/exp9/jmeter/CyberGuardAI_LoadTest.jmx:

    50 concurrent virtual users, 10 second ramp-up, 10 iterations each,
    exercising five API endpoints with 100-400 ms think time.

Reports per-endpoint and aggregate response time (average, median, 90th, 95th,
99th percentile, min, max), error rate and throughput, in the same shape as a
JMeter Aggregate Report, and writes a CSV identical in layout to JMeter's
summary export.

    cd backend
    venv\\Scripts\\activate
    python exp9_run_loadtest.py
"""
import csv
import json
import random
import statistics
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "documentation" / "exp9" / "results"

HOST = "http://127.0.0.1:5000"
EMAIL = "admin@cyberguard.ai"
PASSWORD = "admin123"

USERS = 50
RAMP_SECONDS = 10
LOOPS = 10
THINK_MIN, THINK_MAX = 0.10, 0.40

ANALYZE_BODY = json.dumps({
    "source_ip": "203.0.113.66", "destination_ip": "10.0.1.20",
    "destination_port": 22, "protocol": "SSH", "event_type": "authentication",
    "failed_login_attempts": 62, "request_count": 68, "packet_count": 340,
    "bytes_transferred": 41000, "connection_duration": 95,
}).encode()

# label, method, path, body
SAMPLERS = [
    ("GET /api/health", "GET", "/api/health", None),
    ("GET /api/dashboard/stats", "GET", "/api/dashboard/stats", None),
    ("GET /api/alerts", "GET", "/api/alerts?per_page=15", None),
    ("GET /api/incidents", "GET", "/api/incidents", None),
    ("POST /api/events/analyze", "POST", "/api/events/analyze?persist=false", ANALYZE_BODY),
]

samples = []           # (label, elapsed_ms, ok, bytes)
samples_lock = threading.Lock()


def login():
    req = urllib.request.Request(
        HOST + "/api/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())["data"]["token"]


def fire(label, method, path, body, token):
    headers = {"Authorization": "Bearer " + token}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(HOST + path, data=body, headers=headers, method=method)
    started = time.perf_counter()
    ok, size = False, 0
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = response.read()
            size = len(payload)
            ok = 200 <= response.status < 400
    except urllib.error.HTTPError as exc:
        size = len(exc.read() or b"")
    except Exception:
        pass
    elapsed = (time.perf_counter() - started) * 1000.0
    with samples_lock:
        samples.append((label, elapsed, ok, size))


def virtual_user(index, token, start_barrier):
    # Stagger thread starts across the ramp-up window, as JMeter does.
    time.sleep(index * (RAMP_SECONDS / float(USERS)))
    start_barrier.wait()
    for _ in range(LOOPS):
        for label, method, path, body in SAMPLERS:
            fire(label, method, path, body, token)
            time.sleep(random.uniform(THINK_MIN, THINK_MAX))


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (pct / 100.0)
    low, high = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (k - low)


def summarise(label, rows, wall_seconds):
    times = [r[1] for r in rows]
    errors = sum(1 for r in rows if not r[2])
    total_bytes = sum(r[3] for r in rows)
    return {
        "label": label,
        "samples": len(rows),
        "average_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "p90_ms": round(percentile(times, 90), 2),
        "p95_ms": round(percentile(times, 95), 2),
        "p99_ms": round(percentile(times, 99), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "error_pct": round(errors * 100.0 / len(rows), 2),
        "throughput_per_sec": round(len(rows) / wall_seconds, 2),
        "kb_per_sec": round(total_bytes / 1024.0 / wall_seconds, 2),
    }


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    print("\nExperiment 9 - Task 2: Load / performance test")
    print("=" * 84)
    print("Target      : %s" % HOST)
    print("Thread group: %d users, %ds ramp-up, %d loops" % (USERS, RAMP_SECONDS, LOOPS))
    print("Samplers    : %d endpoints, think time %.0f-%.0f ms"
          % (len(SAMPLERS), THINK_MIN * 1000, THINK_MAX * 1000))
    print("Expected    : %d samples" % (USERS * LOOPS * len(SAMPLERS)))
    print("-" * 84)

    token = login()
    print("Authenticated, starting virtual users ...")

    barrier = threading.Barrier(USERS + 1)
    threads = [threading.Thread(target=virtual_user, args=(i, token, barrier), daemon=True)
               for i in range(USERS)]
    for t in threads:
        t.start()

    started_at = datetime.now()
    barrier.wait()
    clock = time.perf_counter()
    for t in threads:
        t.join()
    wall = time.perf_counter() - clock

    by_label = {}
    for row in samples:
        by_label.setdefault(row[0], []).append(row)

    per_endpoint = [summarise(label, by_label[label], wall)
                    for label, _, _, _ in SAMPLERS if label in by_label]
    total = summarise("TOTAL", samples, wall)

    print("-" * 84)
    header = "%-28s %7s %8s %8s %8s %8s %7s %9s" % (
        "Label", "Samples", "Avg ms", "Med ms", "p90 ms", "p95 ms", "Err %", "Req/sec")
    print(header)
    print("-" * 84)
    for row in per_endpoint + [total]:
        print("%-28s %7d %8.1f %8.1f %8.1f %8.1f %7.2f %9.2f" % (
            row["label"], row["samples"], row["average_ms"], row["median_ms"],
            row["p90_ms"], row["p95_ms"], row["error_pct"], row["throughput_per_sec"]))
    print("-" * 84)
    print("Wall clock  : %.2f s" % wall)
    print("Total samples: %d" % len(samples))

    payload = {
        "executed_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "target": HOST,
        "environment": "Windows 11, Python 3.10, Flask development server, SQLite",
        "thread_group": {
            "users": USERS, "ramp_up_seconds": RAMP_SECONDS, "loops": LOOPS,
            "think_time_ms": [int(THINK_MIN * 1000), int(THINK_MAX * 1000)],
        },
        "duration_seconds": round(wall, 2),
        "total_samples": len(samples),
        "per_endpoint": per_endpoint,
        "total": total,
    }
    (RESULTS / "performance_results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")

    # CSV laid out like a JMeter summary export.
    with open(RESULTS / "performance_summary.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Label", "# Samples", "Average", "Median", "90% Line", "95% Line",
                         "99% Line", "Min", "Max", "Error %", "Throughput", "KB/sec"])
        for row in per_endpoint + [total]:
            writer.writerow([row["label"], row["samples"], row["average_ms"], row["median_ms"],
                             row["p90_ms"], row["p95_ms"], row["p99_ms"], row["min_ms"],
                             row["max_ms"], "%.2f%%" % row["error_pct"],
                             row["throughput_per_sec"], row["kb_per_sec"]])

    print("Results -> %s" % (RESULTS / "performance_results.json"))
    print("CSV     -> %s" % (RESULTS / "performance_summary.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
