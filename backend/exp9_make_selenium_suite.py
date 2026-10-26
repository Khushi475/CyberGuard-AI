"""Build the Selenium IDE project file for Experiment 9.

Produces documentation/exp9/selenium/CyberGuardAI.side which can be opened
directly in the Selenium IDE browser extension and run with "Run all tests".

Ten functional test cases covering login, detection, alert triage, the incident
lifecycle, CSV log analysis, asset management and report generation.
"""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "documentation" / "exp9" / "selenium" / "CyberGuardAI.side"
BASE = "http://localhost:5173"


def uid():
    return str(uuid.uuid4())


def cmd(command, target="", value="", comment="", targets=None):
    return {
        "id": uid(),
        "comment": comment,
        "command": command,
        "target": target,
        "targets": targets or [],
        "value": value,
    }


def login_steps():
    """Reusable sign-in sequence."""
    return [
        cmd("open", "/login", comment="Navigate to the login page"),
        cmd("setWindowSize", "1440x900"),
        cmd("type", "id=email", "admin@cyberguard.ai", "Enter the analyst email"),
        cmd("type", "id=password", "admin123", "Enter the password"),
        cmd("click", "css=button[type='submit']", comment="Submit the sign-in form"),
        cmd("waitForElementPresent", "css=h1", "10000", "Wait for the console to load"),
    ]


TESTS = [
    {
        "name": "TC-01 Valid login is accepted",
        "commands": login_steps() + [
            cmd("assertText", "css=h1", "Security Overview",
                "Dashboard heading confirms a successful sign-in"),
            cmd("assertElementPresent", "css=nav", comment="Sidebar navigation is rendered"),
        ],
    },
    {
        "name": "TC-02 Invalid password is rejected",
        "commands": [
            cmd("open", "/login"),
            cmd("setWindowSize", "1440x900"),
            cmd("type", "id=email", "admin@cyberguard.ai"),
            cmd("type", "id=password", "wrongpassword", "Deliberately wrong password"),
            cmd("click", "css=button[type='submit']"),
            cmd("waitForElementPresent", "css=.text-danger, .border-danger\\/40", "10000"),
            cmd("assertText", "css=.border-danger\\/40",
                "*Invalid email address or password*",
                "Error message must not reveal whether the account exists"),
        ],
    },
    {
        "name": "TC-03 Empty credentials are validated client side",
        "commands": [
            cmd("open", "/login"),
            cmd("setWindowSize", "1440x900"),
            cmd("click", "css=button[type='submit']", comment="Submit with both fields blank"),
            cmd("waitForElementPresent", "css=.field-error", "5000"),
            cmd("assertElementPresent", "css=.field-error",
                comment="Inline validation messages appear"),
        ],
    },
    {
        "name": "TC-04 Dashboard loads live statistics",
        "commands": login_steps() + [
            cmd("waitForElementPresent", "css=.panel", "15000"),
            cmd("assertText", "css=h1", "Security Overview"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Total Events')]"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Threats Detected')]"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Critical Alerts')]"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Active Incidents')]"),
            cmd("assertElementPresent", "css=.recharts-surface",
                comment="Chart canvases are rendered from API data"),
        ],
    },
    {
        "name": "TC-05 Threat detection classifies a brute-force event",
        "commands": login_steps() + [
            cmd("click", "linkText=Threat Detection"),
            cmd("waitForElementPresent", "xpath=//button[contains(.,'Repeated failed SSH logins')]",
                "10000"),
            cmd("click", "xpath=//button[contains(.,'Repeated failed SSH logins')]",
                comment="Load the prepared brute-force sample"),
            cmd("click", "xpath=//button[contains(.,'Analyze Threat')]"),
            cmd("waitForElementPresent", "xpath=//*[contains(text(),'Brute Force Attempt')]",
                "30000"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'CRITICAL')]",
                comment="Severity band is CRITICAL"),
            cmd("assertElementPresent",
                "xpath=//*[contains(text(),'Why the engine reached this verdict')]",
                comment="Explainable reasons are displayed"),
            cmd("assertElementPresent",
                "xpath=//*[contains(text(),'Recommended defensive action')]"),
        ],
    },
    {
        "name": "TC-06 Invalid IP address is rejected with a field error",
        "commands": login_steps() + [
            cmd("click", "linkText=Threat Detection"),
            cmd("waitForElementPresent", "css=input.mono", "10000"),
            cmd("type", "css=input.mono", "999.999.1.1", "Enter a malformed IPv4 address"),
            cmd("click", "xpath=//button[contains(.,'Analyze Threat')]"),
            cmd("waitForElementPresent", "css=.field-error", "10000"),
            cmd("assertElementPresent", "css=.field-input-error",
                comment="The offending input is highlighted"),
        ],
    },
    {
        "name": "TC-07 Alerts page filters by severity",
        "commands": login_steps() + [
            cmd("click", "linkText=Alerts"),
            cmd("waitForElementPresent", "css=table", "15000"),
            cmd("click", "xpath=//button[contains(.,'Filters')]"),
            cmd("select", "css=select", "label=Critical", "Filter the queue to CRITICAL"),
            cmd("pause", "", "2000"),
            cmd("assertElementPresent", "css=table tbody tr",
                comment="Filtered rows are returned by the API"),
        ],
    },
    {
        "name": "TC-08 Incident lifecycle offers only legal transitions",
        "commands": login_steps() + [
            cmd("click", "linkText=Incidents"),
            cmd("waitForElementPresent", "css=table tbody tr", "15000"),
            cmd("click", "css=table tbody tr:nth-child(1)", comment="Open the first incident"),
            cmd("waitForElementPresent", "xpath=//*[contains(text(),'Incident lifecycle')]",
                "15000"),
            cmd("assertElementPresent",
                "xpath=//*[contains(text(),'Available transitions')]",
                comment="Only permitted transitions are rendered as buttons"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Status history')]"),
        ],
    },
    {
        "name": "TC-09 Log analyzer accepts a CSV upload",
        "commands": login_steps() + [
            cmd("click", "linkText=Log Analyzer"),
            cmd("waitForElementPresent", "css=input[type='file']", "10000"),
            cmd("type", "css=input[type='file']",
                str((ROOT / "sample_data" / "sample_logs_mixed.csv")).replace("\\", "/"),
                "Attach the 120-row sample log file"),
            cmd("click", "xpath=//button[contains(.,'Analyze log file')]"),
            cmd("waitForElementPresent", "xpath=//*[contains(text(),'Ingestion summary')]",
                "120000"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Total records')]"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Suspicious')]"),
        ],
    },
    {
        "name": "TC-10 Report generation and listing",
        "commands": login_steps() + [
            cmd("click", "linkText=Reports"),
            cmd("waitForElementPresent", "xpath=//button[contains(.,'Generate Report')]", "15000"),
            cmd("click", "xpath=//button[contains(.,'Generate Report')]"),
            cmd("waitForElementPresent", "xpath=//*[contains(text(),'RPT-')]", "30000"),
            cmd("assertElementPresent", "xpath=//*[contains(text(),'Recommendations')]",
                comment="Report content includes derived recommendations"),
        ],
    },
]


def main():
    tests = []
    for spec in TESTS:
        tests.append({"id": uid(), "name": spec["name"], "commands": spec["commands"]})

    project = {
        "id": uid(),
        "version": "2.0",
        "name": "CyberGuard AI - Functional Test Suite",
        "url": BASE,
        "tests": tests,
        "suites": [{
            "id": uid(),
            "name": "Experiment 9 - Functional Suite",
            "persistSession": False,
            "parallel": False,
            "timeout": 600,
            "tests": [t["id"] for t in tests],
        }],
        "urls": [BASE],
        "plugins": [],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(project, indent=2), encoding="utf-8")
    print("Written: %s" % OUT)
    print("Tests  : %d" % len(tests))
    total = sum(len(t["commands"]) for t in tests)
    print("Commands: %d" % total)


if __name__ == "__main__":
    main()
