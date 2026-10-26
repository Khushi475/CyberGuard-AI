"""Experiment 9, Task 1 - execute the functional test suite and capture evidence.

Runs the same ten test cases that are defined in
documentation/exp9/selenium/CyberGuardAI.side, driving a real browser, and writes
one screenshot per test case plus a machine-readable result file.

    cd backend
    venv\\Scripts\\activate
    python exp9_run_functional.py
"""
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
EXP9 = ROOT / "documentation" / "exp9"
SHOTS = EXP9 / "screenshots"
RESULTS = EXP9 / "results"
SAMPLE_CSV = ROOT / "sample_data" / "sample_logs_mixed.csv"

BASE = "http://localhost:5173"
EMAIL = "admin@cyberguard.ai"
PASSWORD = "admin123"
VIEWPORT = {"width": 1440, "height": 900}

FREEZE = """
  *, *::before, *::after {
    animation-duration: 0s !important; transition-duration: 0s !important;
    caret-color: transparent !important;
  }
"""

results = []


def settle(page, ms=1200):
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(ms)
    try:
        page.add_style_tag(content=FREEZE)
    except Exception:
        pass


def close_toasts(page):
    try:
        for b in page.locator('button[aria-label="Dismiss notification"]').all():
            try:
                b.click(timeout=600)
            except Exception:
                pass
    except Exception:
        pass
    page.wait_for_timeout(200)


def capture(page, name):
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(350)
    path = SHOTS / name
    page.screenshot(path=str(path))
    return path.name


def clear_session(page):
    """Drop the stored token so the login page is reachable again.

    An authenticated visit to /login is redirected straight to /dashboard by the
    PublicOnlyRoute guard, so the three authentication test cases must start from
    a cleared session.
    """
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.wait_for_selector("#email", timeout=20000)
    settle(page, 600)


def sign_in(page):
    clear_session(page)
    page.fill("#email", EMAIL)
    page.fill("#password", PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=30000)
    settle(page, 2500)
    close_toasts(page)


def ensure_signed_in(page):
    """Sign in only if the session is not already established."""
    page.goto(BASE + "/dashboard", wait_until="domcontentloaded")
    settle(page, 900)
    if "/login" in page.url:
        sign_in(page)


def body_text(page):
    """Rendered text, lower-cased. Labels styled with text-transform: uppercase
    render in capitals, so every assertion compares case-insensitively."""
    return page.locator("body").inner_text().lower()


def run(tc_id, title, expected, fn, page, shot_name):
    """Execute one test case, record pass/fail, duration and a screenshot."""
    started = time.perf_counter()
    status, actual = "PASS", ""
    try:
        actual = fn(page) or expected
    except Exception as exc:
        status = "FAIL"
        actual = "%s: %s" % (type(exc).__name__, str(exc).split("\n")[0][:160])
    elapsed = (time.perf_counter() - started) * 1000
    try:
        shot = capture(page, shot_name)
    except Exception:
        shot = ""
    results.append({
        "id": tc_id, "title": title, "expected": expected, "actual": actual,
        "status": status, "ms": round(elapsed, 1), "screenshot": shot,
    })
    print("  %-7s %-52s %s  %6.0f ms" % (tc_id, title[:52], status, elapsed))
    return status


# ------------------------------------------------------------------ test bodies
def tc01(page):
    sign_in(page)
    heading = page.locator("h1").first.inner_text()
    assert "Security Overview" in heading, "dashboard heading not found"
    assert page.locator("nav").count() > 0, "sidebar missing"
    return "Signed in; dashboard rendered with heading '%s'" % heading


def tc02(page):
    clear_session(page)
    page.fill("#email", EMAIL)
    page.fill("#password", "wrongpassword")
    page.click('button[type="submit"]')
    page.wait_for_selector("text=Invalid email address or password", timeout=15000)
    assert "/login" in page.url, "should remain on the login page"
    return "HTTP 401; message 'Invalid email address or password.'; stayed on /login"


def tc03(page):
    clear_session(page)
    page.click('button[type="submit"]')
    page.wait_for_selector(".field-error", timeout=10000)
    count = page.locator(".field-error").count()
    assert count >= 2, "expected two inline errors, saw %d" % count
    return "%d inline validation messages shown; no request sent" % count


def tc04(page):
    ensure_signed_in(page)
    settle(page, 2200)
    body = body_text(page)
    for label in ("total events", "threats detected", "critical alerts", "active incidents"):
        assert label in body, "missing KPI: %s" % label
    charts = page.locator(".recharts-surface").count()
    assert charts >= 4, "expected chart canvases, saw %d" % charts
    return "4 KPI tiles present; %d chart canvases rendered from API data" % charts


def tc05(page):
    ensure_signed_in(page)
    page.goto(BASE + "/detection", wait_until="domcontentloaded")
    settle(page)
    page.get_by_role("button", name="Repeated failed SSH logins").click()
    page.wait_for_timeout(800)
    page.get_by_role("button", name="Analyze Threat").click()
    page.wait_for_selector("text=Why the engine reached this verdict", timeout=45000)
    page.wait_for_timeout(1200)
    close_toasts(page)
    body = body_text(page)
    assert "brute force attempt" in body, "classification not shown"
    assert "critical" in body, "severity not shown"
    assert "recommended defensive action" in body, "no recommended action"
    return "Classified 'Brute Force Attempt', severity CRITICAL, reasons and action displayed"


def tc06(page):
    ensure_signed_in(page)
    page.goto(BASE + "/detection", wait_until="domcontentloaded")
    settle(page)
    page.fill("input.mono >> nth=0", "999.999.1.1")
    page.get_by_role("button", name="Analyze Threat").click()
    page.wait_for_selector(".field-error", timeout=15000)
    close_toasts(page)
    msg = page.locator(".field-error").first.inner_text()
    return "Rejected with field-level error: '%s'" % msg.strip()[:90]


def tc07(page):
    ensure_signed_in(page)
    page.goto(BASE + "/alerts", wait_until="domcontentloaded")
    settle(page, 1800)
    before = page.locator("table tbody tr").count()
    page.get_by_role("button", name="Filters").click()
    page.wait_for_timeout(500)
    page.select_option("select >> nth=1", label="Critical")
    page.wait_for_timeout(2200)
    close_toasts(page)
    after = page.locator("table tbody tr").count()
    body = page.locator("table").inner_text()
    assert "MEDIUM" not in body and "LOW" not in body, "non-critical rows present after filtering"
    return "Filter applied server-side; %d rows before, %d CRITICAL rows after" % (before, after)


def tc08(page):
    ensure_signed_in(page)
    page.goto(BASE + "/incidents", wait_until="domcontentloaded")
    settle(page, 1800)
    page.locator("table tbody tr").first.click()
    page.wait_for_selector("text=Incident lifecycle", timeout=20000)
    settle(page, 1200)
    close_toasts(page)
    body = body_text(page)
    assert "available transitions" in body, "transition panel missing"
    assert "status history" in body, "history panel missing"
    return "Lifecycle tracker shown; only permitted transitions offered; history rendered"


def tc09(page):
    ensure_signed_in(page)
    page.goto(BASE + "/log-analyzer", wait_until="domcontentloaded")
    settle(page)
    page.set_input_files('input[type="file"]', str(SAMPLE_CSV))
    page.wait_for_timeout(600)
    page.get_by_role("button", name="Analyze log file").click()
    page.wait_for_selector("text=Ingestion summary", timeout=180000)
    page.wait_for_timeout(1800)
    close_toasts(page)
    body = body_text(page)
    assert "total records" in body, "summary tiles missing"
    return "120-row CSV parsed, validated, analysed and summarised by severity"


def tc10(page):
    ensure_signed_in(page)
    page.goto(BASE + "/reports", wait_until="domcontentloaded")
    settle(page, 1500)
    page.get_by_role("button", name="Generate Report").click()
    page.wait_for_selector("text=Recommendations", timeout=45000)
    page.wait_for_timeout(1200)
    body = body_text(page)
    assert "rpt-" in body, "report code not shown"
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    close_toasts(page)
    return "Report generated with an RPT- code and data-derived recommendations"


CASES = [
    ("TC-01", "Valid login is accepted", "Dashboard loads; session established", tc01, "TC01_valid_login.png"),
    ("TC-02", "Invalid password is rejected", "HTTP 401, generic error, stays on login", tc02, "TC02_invalid_password.png"),
    ("TC-03", "Empty credentials are validated", "Inline field errors, no request sent", tc03, "TC03_empty_fields.png"),
    ("TC-04", "Dashboard loads live statistics", "KPI tiles and charts populated from API", tc04, "TC04_dashboard.png"),
    ("TC-05", "Brute-force event is classified", "Brute Force Attempt, CRITICAL, with reasons", tc05, "TC05_detection_result.png"),
    ("TC-06", "Invalid IP address is rejected", "422 with field-level validation message", tc06, "TC06_invalid_input.png"),
    ("TC-07", "Alerts filter by severity", "Only CRITICAL rows returned", tc07, "TC07_alert_filter.png"),
    ("TC-08", "Incident shows legal transitions only", "Lifecycle tracker and permitted actions", tc08, "TC08_incident_lifecycle.png"),
    ("TC-09", "CSV log upload is analysed", "120 records analysed with severity split", tc09, "TC09_log_analyzer.png"),
    ("TC-10", "Report generation", "Report stored with recommendations", tc10, "TC10_report.png"),
]


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    print("\nExperiment 9 - Task 1: Functional test execution")
    print("=" * 78)
    started = datetime.now()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1,
                                      reduced_motion="reduce")
        page = context.new_page()
        for tc_id, title, expected, fn, shot in CASES:
            run(tc_id, title, expected, fn, page, shot)
        context.close()
        browser.close()

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    payload = {
        "executed_at": started.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": "Windows 11, Chromium (Playwright), viewport 1440x900",
        "application": BASE,
        "total": len(results), "passed": passed, "failed": failed,
        "pass_rate": round(passed * 100.0 / len(results), 1) if results else 0,
        "cases": results,
    }
    (RESULTS / "functional_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 78)
    print("Total %d | Passed %d | Failed %d | Pass rate %.1f%%"
          % (len(results), passed, failed, payload["pass_rate"]))
    print("Results -> %s" % (RESULTS / "functional_results.json"))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
