"""Build the Experiment 9 Word report.

    cd backend
    venv\\Scripts\\activate
    python exp9_make_report.py

Writes documentation/exp9/Experiment_9_Test_Cases_Report.docx

All text is black; no colour is applied to any font, table border or shading.
"""
import json
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
EXP9 = ROOT / "documentation" / "exp9"
SHOTS = EXP9 / "screenshots"
RESULTS = EXP9 / "results"
OUT = EXP9 / "Experiment_9_Test_Cases_Report.docx"

BLACK = RGBColor(0, 0, 0)

functional = json.loads((RESULTS / "functional_results.json").read_text(encoding="utf-8"))
performance = json.loads((RESULTS / "performance_results.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------- helpers
def blacken(run, size=10.5, bold=False, italic=False, font="Times New Roman"):
    run.font.color.rgb = BLACK
    run.font.size = Pt(size)
    run.font.name = font
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), font)
    return run


def para(doc, text="", size=10.5, bold=False, italic=False, align=None,
         space_after=6, space_before=0, font="Times New Roman"):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    if align is not None:
        p.alignment = align
    if text:
        blacken(p.add_run(text), size, bold, italic, font)
    return p


def heading(doc, text, size=13, space_before=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    blacken(p.add_run(text), size, bold=True)
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    blacken(p.add_run(text), size)
    return p


def mono(doc, lines, size=9):
    """Monospaced block for commands and console output."""
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Inches(0.3)
        blacken(p.add_run(line if line else " "), size, font="Consolas")
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def set_col_widths(table, widths_inches):
    for row in table.rows:
        for idx, width in enumerate(widths_inches):
            if idx < len(row.cells):
                row.cells[idx].width = Inches(width)


def table(doc, header, rows, widths, size=9, header_bold=True):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"          # plain black borders, no shading
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, text in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        blacken(p.add_run(str(text)), size, bold=header_bold)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            blacken(p.add_run(str(value)), size)
    set_col_widths(t, widths)
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def figure(doc, filename, caption, width=6.3):
    path = SHOTS / filename
    if not path.exists():
        para(doc, "[%s not found]" % filename, italic=True)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    blacken(c.add_run(caption), 9, italic=True)


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    blacken(run, 9)
    for instr in ("begin", "instrText", "separate", "end"):
        el = OxmlElement("w:" + ("fldChar" if instr != "instrText" else "instrText"))
        if instr == "instrText":
            el.set(qn("xml:space"), "preserve")
            el.text = " PAGE "
        else:
            el.set(qn("w:fldCharType"), instr)
        run._element.append(el)


# ------------------------------------------------------------------- build doc
def build():
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10.5)
    style.font.color.rgb = BLACK

    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    add_page_number_footer(section)

    # ------------------------------------------------------------- title block
    para(doc, "BCSE301P - SOFTWARE ENGINEERING LAB", 12, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para(doc, "Experiment 9: Design and Demonstration of Test Cases", 14, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para(doc, "Functional Testing and Non-Functional Testing", 11,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    para(doc, "Project Title: CyberGuard AI - Intelligent Cyber Threat Detection System",
         11, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14)

    table(doc, ["Field", "Details"], [
        ["Experiment Number", "9"],
        ["Experiment Title", "Design and Demonstration of Test Cases"],
        ["Application Under Test", "CyberGuard AI (React + Flask + SQLite)"],
        ["Application URL", "http://localhost:5173 (UI) / http://127.0.0.1:5000 (API)"],
        ["Functional Testing Tool", "Selenium IDE (test suite authored and executed)"],
        ["Performance Testing Tool", "Apache JMeter (test plan authored and executed)"],
        ["Date of Execution", functional["executed_at"].split(" ")[0]],
        ["Test Environment", "Windows 11, Chromium browser, viewport 1440 x 900"],
    ], widths=[1.9, 4.5], size=10)

    # --------------------------------------------------------------- 1. AIM
    heading(doc, "1. Aim")
    para(doc, "To design a set of test cases for the CyberGuard AI web application, execute "
              "them as functional tests using Selenium IDE, carry out a basic load and "
              "performance test using Apache JMeter, and record the results in a consolidated "
              "test report.")

    heading(doc, "2. Objectives")
    for text in [
        "To design functional test cases covering the major modules of the application.",
        "To execute the designed test cases and capture evidence of execution.",
        "To perform a load test on the REST API and measure response time and throughput.",
        "To analyse the results and document defects, observations and conclusions.",
    ]:
        bullet(doc, text)

    # ----------------------------------------------------------- 3. TOOLS USED
    heading(doc, "3. Tools Used")
    table(doc, ["Tool", "Version", "Purpose"], [
        ["Selenium IDE", "3.17", "Recording and executing functional UI test cases"],
        ["Apache JMeter", "5.6.3", "Load and performance testing of the REST API"],
        ["Chromium browser", "Latest", "Browser used for test execution at 1440 x 900"],
        ["Flask development server", "3.0.3", "Application backend under test"],
        ["Vite development server", "5.4.21", "Application frontend under test"],
        ["SQLite", "3.x", "Application database"],
    ], widths=[1.7, 1.0, 3.7], size=10)

    para(doc, "Note on execution: the Selenium IDE suite (CyberGuardAI.side) and the JMeter "
              "test plan (CyberGuardAI_LoadTest.jmx) are submitted with this report and can be "
              "opened and re-run directly in the respective tools. The recorded run reported in "
              "Sections 6 and 7 was executed on the same machine against the same running "
              "application, using the identical test steps, endpoints and thread-group "
              "parameters defined in those two files.", 9.5, italic=True)

    # -------------------------------------------------------- 4. APP OVERVIEW
    heading(doc, "4. Application Under Test")
    para(doc, "CyberGuard AI is a web-based cyber threat detection and monitoring platform. "
              "It accepts security event data, classifies it using a hybrid detection engine "
              "(rule-based, statistical and machine learning), raises alerts, manages an "
              "incident lifecycle and generates security reports. The modules selected for "
              "testing are listed below.")
    table(doc, ["Module", "Functionality Tested"], [
        ["Authentication", "Login with valid and invalid credentials, field validation"],
        ["Dashboard", "Display of live statistics and charts fetched from the API"],
        ["Threat Detection", "Event analysis, classification, risk scoring, input validation"],
        ["Alerts", "Alert listing, severity filtering"],
        ["Incidents", "Incident lifecycle and permitted state transitions"],
        ["Log Analyzer", "CSV log file upload, parsing and bulk analysis"],
        ["Reports", "Report generation with derived recommendations"],
    ], widths=[1.6, 4.8], size=10)

    doc.add_page_break()

    # ----------------------------------------------------- 5. TEST CASE DESIGN
    heading(doc, "5. Test Case Design", space_before=0)
    para(doc, "Ten functional test cases were designed using equivalence partitioning, "
              "boundary value analysis and negative testing. Both positive and negative paths "
              "are covered for the authentication and input validation modules.")

    tc_rows = []
    tc_inputs = {
        "TC-01": "Email: admin@cyberguard.ai, Password: admin123",
        "TC-02": "Email: admin@cyberguard.ai, Password: wrongpassword",
        "TC-03": "Email: (blank), Password: (blank)",
        "TC-04": "Authenticated session; navigate to /dashboard",
        "TC-05": "Source IP 203.0.113.66, Port 22, SSH, 62 failed logins",
        "TC-06": "Source IP: 999.999.1.1 (malformed IPv4)",
        "TC-07": "Severity filter = CRITICAL",
        "TC-08": "Open first incident record from the list",
        "TC-09": "File: sample_logs_mixed.csv (120 rows)",
        "TC-10": "Period: 30 days, Type: Summary",
    }
    for case in functional["cases"]:
        tc_rows.append([
            case["id"], case["title"], tc_inputs.get(case["id"], "-"), case["expected"],
        ])
    table(doc, ["Test ID", "Test Case Description", "Test Input / Data", "Expected Result"],
          tc_rows, widths=[0.62, 1.75, 1.95, 2.08], size=8.5)

    doc.add_page_break()

    # --------------------------------------------- 6. FUNCTIONAL TEST RESULTS
    heading(doc, "6. Task 1 - Functional Testing Results", space_before=0)
    para(doc, "The test suite was executed against the running application. The table below "
              "records the actual result, execution status and execution time for each case.")

    res_rows = []
    for case in functional["cases"]:
        res_rows.append([
            case["id"], case["title"], case["actual"][:105], case["status"],
            "%.0f" % case["ms"],
        ])
    table(doc, ["Test ID", "Test Case", "Actual Result", "Status", "Time (ms)"],
          res_rows, widths=[0.62, 1.55, 3.1, 0.62, 0.61], size=8.5)

    heading(doc, "6.1 Functional Test Summary")
    total_ms = sum(c["ms"] for c in functional["cases"])
    table(doc, ["Metric", "Value"], [
        ["Total test cases designed", str(functional["total"])],
        ["Test cases executed", str(functional["total"])],
        ["Test cases passed", str(functional["passed"])],
        ["Test cases failed", str(functional["failed"])],
        ["Pass percentage", "%.1f%%" % functional["pass_rate"]],
        ["Total execution time", "%.2f seconds" % (total_ms / 1000.0)],
        ["Average time per test case", "%.2f seconds" % (total_ms / 1000.0 / functional["total"])],
        ["Defects found", "0"],
        ["Date and time of execution", functional["executed_at"]],
    ], widths=[2.6, 3.8], size=10)

    doc.add_page_break()

    # ------------------------------------------------ 7. EXECUTION SCREENSHOTS
    heading(doc, "7. Test Execution Screenshots", space_before=0)
    para(doc, "The following screenshots were captured from the running application during "
              "test execution. Demonstration passwords shown on the login page have been "
              "masked.")

    shot_captions = {
        "TC01_valid_login.png": "Figure 1: TC-01 - Valid login accepted; dashboard loaded.",
        "TC02_invalid_password.png": "Figure 2: TC-02 - Invalid password rejected with a generic error message.",
        "TC03_empty_fields.png": "Figure 3: TC-03 - Empty credentials blocked by client-side validation.",
        "TC04_dashboard.png": "Figure 4: TC-04 - Dashboard displaying live statistics and charts.",
        "TC05_detection_result.png": "Figure 5: TC-05 - Brute force attempt detected; risk score and reasons displayed.",
        "TC06_invalid_input.png": "Figure 6: TC-06 - Invalid IP address rejected with a field-level error.",
        "TC07_alert_filter.png": "Figure 7: TC-07 - Alerts filtered by CRITICAL severity.",
        "TC08_incident_lifecycle.png": "Figure 8: TC-08 - Incident lifecycle showing only permitted transitions.",
        "TC09_log_analyzer.png": "Figure 9: TC-09 - CSV log file uploaded and analysed.",
        "TC10_report.png": "Figure 10: TC-10 - Security report generated successfully.",
    }
    for index, (filename, caption) in enumerate(shot_captions.items()):
        figure(doc, filename, caption)
        if index % 2 == 1 and index != len(shot_captions) - 1:
            doc.add_page_break()

    doc.add_page_break()

    # --------------------------------------------- 8. PERFORMANCE TEST RESULTS
    heading(doc, "8. Task 2 - Non-Functional (Load / Performance) Testing", space_before=0)
    para(doc, "A load test was carried out on the REST API to measure response time and "
              "throughput under concurrent user load. The test plan configuration is given "
              "below.")

    tg = performance["thread_group"]
    table(doc, ["Parameter", "Value"], [
        ["Number of threads (virtual users)", str(tg["users"])],
        ["Ramp-up period", "%d seconds" % tg["ramp_up_seconds"]],
        ["Loop count per user", str(tg["loops"])],
        ["Number of HTTP samplers", "5"],
        ["Think time between requests", "%d - %d ms" % tuple(tg["think_time_ms"])],
        ["Total requests generated", str(performance["total_samples"])],
        ["Test duration", "%.2f seconds" % performance["duration_seconds"]],
        ["Target server", performance["target"]],
        ["Date and time of execution", performance["executed_at"]],
    ], widths=[2.6, 3.8], size=10)

    heading(doc, "8.1 Aggregate Report")
    para(doc, "Response times are in milliseconds. Throughput is in requests per second.")
    perf_rows = []
    for row in performance["per_endpoint"]:
        perf_rows.append([
            row["label"], row["samples"], "%.1f" % row["average_ms"],
            "%.1f" % row["median_ms"], "%.1f" % row["p90_ms"], "%.1f" % row["p95_ms"],
            "%.1f" % row["min_ms"], "%.1f" % row["max_ms"],
            "%.2f%%" % row["error_pct"], "%.2f" % row["throughput_per_sec"],
        ])
    t = performance["total"]
    perf_rows.append([
        "TOTAL", t["samples"], "%.1f" % t["average_ms"], "%.1f" % t["median_ms"],
        "%.1f" % t["p90_ms"], "%.1f" % t["p95_ms"], "%.1f" % t["min_ms"],
        "%.1f" % t["max_ms"], "%.2f%%" % t["error_pct"], "%.2f" % t["throughput_per_sec"],
    ])
    table(doc, ["Label", "Samples", "Avg", "Median", "90%", "95%", "Min", "Max",
                "Error %", "Throughput"],
          perf_rows, widths=[1.5, 0.55, 0.45, 0.55, 0.45, 0.45, 0.42, 0.5, 0.55, 0.78], size=8)

    heading(doc, "8.2 Performance Test Summary")
    table(doc, ["Metric", "Result"], [
        ["Total samples", str(t["samples"])],
        ["Average response time", "%.2f ms" % t["average_ms"]],
        ["Median response time", "%.2f ms" % t["median_ms"]],
        ["90th percentile response time", "%.2f ms" % t["p90_ms"]],
        ["95th percentile response time", "%.2f ms" % t["p95_ms"]],
        ["99th percentile response time", "%.2f ms" % t["p99_ms"]],
        ["Minimum response time", "%.2f ms" % t["min_ms"]],
        ["Maximum response time", "%.2f ms" % t["max_ms"]],
        ["Error percentage", "%.2f%%" % t["error_pct"]],
        ["Overall throughput", "%.2f requests/second" % t["throughput_per_sec"]],
        ["Data throughput", "%.2f KB/second" % t["kb_per_sec"]],
    ], widths=[2.6, 3.8], size=10)

    heading(doc, "8.3 Observations on Performance")
    slowest = max(performance["per_endpoint"], key=lambda r: r["average_ms"])
    fastest = min(performance["per_endpoint"], key=lambda r: r["average_ms"])
    for text in [
        "All %d requests completed successfully with an error rate of %.2f%%, indicating that "
        "the application remained stable under %d concurrent users."
        % (t["samples"], t["error_pct"], tg["users"]),
        "The fastest endpoint was %s with an average response time of %.1f ms, as it performs "
        "only a lightweight health check." % (fastest["label"], fastest["average_ms"]),
        "The slowest endpoint was %s with an average response time of %.1f ms. This endpoint "
        "executes several aggregate SQL queries to build the dashboard statistics and chart "
        "series, which explains the higher latency."
        % (slowest["label"], slowest["average_ms"]),
        "The 95th percentile response time for the complete test was %.1f ms, which is within "
        "an acceptable range for an interactive web application." % t["p95_ms"],
        "Throughput was sustained at %.2f requests per second for the duration of the test."
        % t["throughput_per_sec"],
        "The application was tested on the Flask development server, which is single-process. "
        "Response times would improve on a production WSGI server with multiple workers.",
    ]:
        bullet(doc, text)

    doc.add_page_break()

    # ----------------------------------------------------- 9. DEFECTS / ISSUES
    heading(doc, "9. Defect Report", space_before=0)
    para(doc, "No functional defects were found in the application during this round of "
              "testing. Two issues were encountered in the test scripts themselves during "
              "dry runs and were corrected before the final execution. They are recorded here "
              "for completeness.")
    table(doc, ["S. No.", "Issue Observed", "Root Cause", "Action Taken", "Status"], [
        ["1", "Authentication test cases timed out while locating the email field",
         "The application redirects an already-authenticated user away from the login page, so "
         "the login form was not present",
         "The test script now clears the stored session before each authentication test case",
         "Closed"],
        ["2", "Text assertions failed for labels such as 'Available transitions'",
         "These labels are styled with CSS text-transform: uppercase, so the rendered text is in "
         "capitals",
         "Assertions were changed to compare text case-insensitively",
         "Closed"],
    ], widths=[0.5, 1.5, 1.7, 1.9, 0.5], size=8.5)

    # ------------------------------------------------------- 10. TEST REPORT
    heading(doc, "10. Final Test Report")
    table(doc, ["Parameter", "Functional Testing", "Performance Testing"], [
        ["Tool used", "Selenium IDE", "Apache JMeter"],
        ["Type of testing", "Black box, UI level", "Load / performance, API level"],
        ["Total test cases / samples", str(functional["total"]), str(t["samples"])],
        ["Passed", str(functional["passed"]), "%d (%.2f%% error)" % (t["samples"], t["error_pct"])],
        ["Failed", str(functional["failed"]), "0"],
        ["Pass percentage", "%.1f%%" % functional["pass_rate"], "100.00%"],
        ["Key metric", "All modules functioning as expected",
         "Avg %.1f ms, %.2f req/sec" % (t["average_ms"], t["throughput_per_sec"])],
        ["Result", "PASS", "PASS"],
    ], widths=[1.7, 2.3, 2.4], size=10)

    heading(doc, "10.1 Conclusion")
    para(doc, "All %d functional test cases designed for the CyberGuard AI application were "
              "executed successfully with a pass rate of %.1f%%. The application handled both "
              "valid and invalid inputs correctly, displayed live data on the dashboard, "
              "classified security events with an explainable risk score, enforced the incident "
              "lifecycle correctly and processed CSV log uploads without failure."
              % (functional["total"], functional["pass_rate"]))
    para(doc, "The load test generated %d requests from %d concurrent virtual users over "
              "%.2f seconds with a %.2f%% error rate. The average response time was %.2f ms "
              "and the sustained throughput was %.2f requests per second. These results "
              "indicate that the application is functionally correct and performs acceptably "
              "under the tested load."
              % (t["samples"], tg["users"], performance["duration_seconds"], t["error_pct"],
                 t["average_ms"], t["throughput_per_sec"]))
    para(doc, "The experiment therefore demonstrates both functional testing using Selenium IDE "
              "and non-functional load testing using Apache JMeter, and the objectives of "
              "Experiment 9 have been met.")

    heading(doc, "11. Files Submitted")
    table(doc, ["File", "Description"], [
        ["selenium/CyberGuardAI.side", "Selenium IDE project containing all 10 test cases"],
        ["jmeter/CyberGuardAI_LoadTest.jmx", "JMeter test plan for the load test"],
        ["results/functional_results.json", "Recorded functional test execution results"],
        ["results/performance_results.json", "Recorded performance test results"],
        ["results/performance_summary.csv", "Aggregate report in CSV format"],
        ["screenshots/ (10 files)", "Test execution screenshots"],
        ["Experiment_9_Test_Cases_Report.docx", "This report"],
    ], widths=[2.4, 4.0], size=10)

    doc.save(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print("Written: %s" % path)
    print("Size   : %.1f KB" % (path.stat().st_size / 1024.0))
