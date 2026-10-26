"""Capture the 12 documentation screenshots from the running CyberGuard AI application.

Prerequisites - both servers must already be running:

    Terminal 1:  cd backend  && venv\\Scripts\\activate && python run.py
    Terminal 2:  cd frontend && npm run dev

Then:

    cd backend
    venv\\Scripts\\activate
    pip install playwright
    python -m playwright install chromium
    python capture_screenshots.py

Every image is captured from the real rendered application at a 1440x900 viewport
and written to ``documentation/screenshots/``.

Secret handling: the login page renders seeded demo passwords on its account
cards. Before that screenshot is taken this script replaces the password text
with bullet characters, so no credential appears in the published image. Password
inputs are ``type="password"`` and mask themselves. Session tokens live in
localStorage and never appear on screen.
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
EMAIL = "admin@cyberguard.ai"
PASSWORD = "admin123"

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
SHOTS_DIR = PROJECT_ROOT / "documentation" / "screenshots"
SAMPLE_CSV = PROJECT_ROOT / "sample_data" / "sample_logs_mixed.csv"

VIEWPORT = {"width": 1440, "height": 900}

# Hides the blinking caret and freezes chart/loader animation so repeated runs
# produce identical images.
STABILISE_CSS = """
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    caret-color: transparent !important;
  }
"""

results = []


def record(name, path, note=""):
    size = path.stat().st_size if path.exists() else 0
    results.append((name, path.name, size, note))
    print("  saved  %-28s %7d bytes  %s" % (path.name, size, note))


def settle(page, ms=1400):
    """Let the page finish fetching and rendering before capturing."""
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def dismiss_toasts(page):
    """Close any toast so it does not cover page content."""
    try:
        for button in page.locator('button[aria-label="Dismiss notification"]').all():
            try:
                button.click(timeout=800)
            except Exception:
                pass
    except Exception:
        pass
    page.wait_for_timeout(250)


def shot(page, filename, note=""):
    # Clicking a control low on a long page leaves the window scrolled, which would
    # crop the headline of the very panel we want to show. Always capture from the
    # top of the page.
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(450)
    path = SHOTS_DIR / filename
    page.screenshot(path=str(path))
    record(filename, path, note)
    return path


def main():
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=1,
            reduced_motion="reduce",
        )
        page = context.new_page()
        page.add_style_tag = page.add_style_tag  # noqa - kept for clarity below

        # ---------------------------------------------------------- 01 login
        print("\n[1/12] Login")
        page.goto(BASE_URL + "/login", wait_until="domcontentloaded")
        settle(page)
        page.add_style_tag(content=STABILISE_CSS)

        # Redact the seeded demo passwords before capturing.
        page.evaluate(
            """
            () => {
              document.querySelectorAll('span.mono').forEach((el) => {
                if (el.textContent && el.textContent.includes('@cyberguard.ai /')) {
                  const email = el.textContent.split('/')[0].trim();
                  el.textContent = email + ' / ' + '\\u2022'.repeat(8);
                }
              });
            }
            """
        )
        page.wait_for_timeout(300)
        shot(page, "01_login.png", "demo passwords redacted")

        # ------------------------------------------------------------ sign in
        print("\n[--/--] Signing in")
        page.fill("#email", EMAIL)
        page.fill("#password", PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard", timeout=30000)
        settle(page, 3000)
        dismiss_toasts(page)

        # ------------------------------------------------------ 02 dashboard
        print("\n[2/12] Dashboard")
        page.add_style_tag(content=STABILISE_CSS)
        settle(page, 2500)          # let every chart series finish drawing
        dismiss_toasts(page)
        page.mouse.move(2, 2)       # move the pointer off any hover target
        shot(page, "02_dashboard.png", "live KPIs and charts")

        # ----------------------------------------------- 03 threat detection
        print("\n[3/12] Threat Detection (form populated)")
        page.goto(BASE_URL + "/detection", wait_until="domcontentloaded")
        settle(page)
        page.add_style_tag(content=STABILISE_CSS)

        # Load the brute-force sample so the form shows realistic values.
        sample = page.get_by_role("button", name="Repeated failed SSH logins")
        sample.click()
        page.wait_for_timeout(900)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "03_threat_detection.png", "sample scenario loaded")

        # ------------------------------------------------ 12 detection result
        print("\n[12/12] Detection result")
        page.get_by_role("button", name="Analyze Threat").click()
        page.wait_for_selector("text=Why the engine reached this verdict", timeout=30000)
        page.wait_for_timeout(1800)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "12_detection_result.png", "explainable CRITICAL verdict")

        # --------------------------------------------------------- 04 alerts
        print("\n[4/12] Alerts")
        page.goto(BASE_URL + "/alerts", wait_until="domcontentloaded")
        settle(page, 1800)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "04_alerts.png", "triage queue")

        # ------------------------------------------------------ 05 incidents
        print("\n[5/12] Incidents")
        page.goto(BASE_URL + "/incidents", wait_until="domcontentloaded")
        settle(page, 1800)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "05_incidents.png", "incident list")

        # ----------------------------------------------- 06 incident details
        print("\n[6/12] Incident details")
        first_row = page.locator("table tbody tr").first
        first_row.click()
        page.wait_for_selector("text=Incident lifecycle", timeout=30000)
        settle(page, 1600)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "06_incident_details.png", "lifecycle tracker and history")

        # -------------------------------------------- 07 threat intelligence
        print("\n[7/12] Threat Intelligence")
        page.goto(BASE_URL + "/threat-intelligence", wait_until="domcontentloaded")
        settle(page, 1800)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "07_threat_intelligence.png", "simulated indicator feed")

        # --------------------------------------------------- 08 log analyzer
        print("\n[8/12] Log Analyzer (after an upload)")
        page.goto(BASE_URL + "/log-analyzer", wait_until="domcontentloaded")
        settle(page)
        page.add_style_tag(content=STABILISE_CSS)

        page.set_input_files('input[type="file"]', str(SAMPLE_CSV))
        page.wait_for_timeout(700)
        page.get_by_role("button", name="Analyze log file").click()
        page.wait_for_selector("text=Ingestion summary", timeout=120000)
        page.wait_for_timeout(2200)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "08_log_analyzer.png", "120-row CSV analysed")

        # --------------------------------------------------------- 09 assets
        print("\n[9/12] Assets")
        page.goto(BASE_URL + "/assets", wait_until="domcontentloaded")
        settle(page, 1800)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "09_assets.png", "monitored inventory")

        # -------------------------------------------------------- 10 reports
        print("\n[10/12] Reports")
        page.goto(BASE_URL + "/reports", wait_until="domcontentloaded")
        settle(page, 1800)
        page.add_style_tag(content=STABILISE_CSS)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "10_reports.png", "generation form and stored reports")

        # ------------------------------------------------------- 11 settings
        print("\n[11/12] Settings")
        page.goto(BASE_URL + "/settings", wait_until="domcontentloaded")
        settle(page, 1600)
        page.add_style_tag(content=STABILISE_CSS)
        # The System status tab shows live table counts - the most informative view.
        page.get_by_role("button", name="System status").click()
        page.wait_for_timeout(1800)
        dismiss_toasts(page)
        page.mouse.move(2, 2)
        shot(page, "11_settings.png", "system status with live table counts")

        context.close()
        browser.close()

    print("\n" + "=" * 72)
    print("SCREENSHOT SUMMARY")
    print("=" * 72)
    expected = [
        "01_login.png", "02_dashboard.png", "03_threat_detection.png",
        "04_alerts.png", "05_incidents.png", "06_incident_details.png",
        "07_threat_intelligence.png", "08_log_analyzer.png", "09_assets.png",
        "10_reports.png", "11_settings.png", "12_detection_result.png",
    ]
    missing = [name for name in expected if not (SHOTS_DIR / name).exists()]
    for name in expected:
        path = SHOTS_DIR / name
        state = "OK  %7d bytes" % path.stat().st_size if path.exists() else "MISSING"
        print("  %-30s %s" % (name, state))
    print("=" * 72)
    if missing:
        print("INCOMPLETE - missing: %s" % ", ".join(missing))
        return 1
    print("All 12 screenshots captured at %dx%d." % (VIEWPORT["width"], VIEWPORT["height"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
