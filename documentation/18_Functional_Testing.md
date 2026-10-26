# 18 - Functional Testing

**Project:** CyberGuard AI
**Lab experiment:** 9 - Functional testing

---

## 1. Scope

Functional testing verifies **what** the system does against the functional
requirements FR-01 to FR-12. It is black-box: each test drives the public API or
the user interface and checks the observable outcome, not the internal
implementation.

Two layers are covered:

1. **Automated API testing** - 117 pytest cases exercising the REST contract
   through the service layer, the ORM and a real database.
2. **Manual end-to-end scenarios** - workflows driven through the browser against
   the running stack, to confirm the frontend and backend agree.

---

## 2. Automated functional test execution

### 2.1 Execution record

```
Command      : python -m pytest -q
Environment  : Windows 11, Python 3.10.0, pytest 8.3.2
Engine mode  : hybrid-ml (trained artefacts present)
Database     : SQLite in-memory, freshly seeded per test module

tests\test_alerts_incidents.py .........................                 [ 21%]
tests\test_assets_dashboard.py ................................         [ 48%]
tests\test_auth.py ...............                                       [ 61%]
tests\test_detection_engine.py ..................                        [ 76%]
tests\test_events.py ...........................                         [100%]

============================ 117 passed in 51.16s =============================
```

**Result: 117 passed, 0 failed, 0 skipped, 0 errors.**

### 2.2 Results by functional requirement

| Requirement | Cases | Passed | Failed | Verdict |
|-------------|-------|--------|--------|---------|
| FR-01 User Login | 15 | 15 | 0 | PASS |
| FR-02 Dashboard | 8 | 8 | 0 | PASS |
| FR-03 Event Submission | 5 | 5 | 0 | PASS |
| FR-04 Event Analysis | 7 | 7 | 0 | PASS |
| FR-05 Threat Detection | 18 | 18 | 0 | PASS |
| FR-06 Alert Management | 13 | 13 | 0 | PASS |
| FR-07 Incident Management | 12 | 12 | 0 | PASS |
| FR-08 Asset Management | 9 | 9 | 0 | PASS |
| FR-09 Threat Intelligence | 2 | 2 | 0 | PASS |
| FR-10 Log Analysis | 9 | 9 | 0 | PASS |
| FR-11 Report Generation | 3 | 3 | 0 | PASS |
| FR-12 Audit Logging | 4 | 4 | 0 | PASS |
| NFR-02 Security (validation and access control) | 11 | 11 | 0 | PASS |
| Misc. system endpoints | 1 | 1 | 0 | PASS |
| **Total** | **117** | **117** | **0** | **PASS** |

---

## 3. Manual end-to-end scenarios

Each scenario was executed through the browser with both servers running.
"Observed" records what the system actually did.

---

### FT-01 - Sign in and reach the console

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open `http://localhost:5173` | Redirected to `/login` | Redirect occurred |
| 2 | Click the "Administrator" demo card | Email and password fields populate | Fields populated |
| 3 | Click "Sign in to console" | Token issued; navigation to `/dashboard`; success toast | Dashboard rendered; toast "Welcome back, Priya." |
| 4 | Refresh the browser (F5) | Session survives; no re-login prompt | Session restored via `GET /api/auth/me` |
| 5 | Enter a wrong password | Inline error; no navigation | "Invalid email address or password." shown; stayed on `/login` |

**Verdict: PASS** (FR-01)

---

### FT-02 - Dashboard reflects live database state

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open the Dashboard | All KPI tiles populated from the API | Totals rendered |
| 2 | Compare "Total Events" with the Events page total | Identical | Both matched |
| 3 | Inspect the six charts | All render with data | Threats-over-time, severity donut, category bars, protocol donut, detection trend, top sources all rendered |
| 4 | Read the Threat Level card | One of LOW/MEDIUM/HIGH/CRITICAL with a stated basis | "CRITICAL - Unresolved alerts raised in the last 24 hours." |
| 5 | Read the Detection Accuracy tile | A percentage **with its source labelled** | Percentage shown with "Analyst-confirmed precision" and an explanatory note |
| 6 | Analyse a new threat, return to the Dashboard | Totals increase | Total events and threats both incremented |

**Verdict: PASS** (FR-02) - confirms the requirement that no dashboard statistic
is hard-coded in React.

---

### FT-03 - Analyse a security event end to end

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Threat Detection | Empty form with an explanatory empty state | Rendered |
| 2 | Click sample "Repeated failed SSH logins" | Form populates | All fields populated; toast confirmed |
| 3 | Click "Analyze Threat" | Verdict panel appears | Classification "Brute Force Attempt", risk 92/100, CRITICAL |
| 4 | Read the reasons | Plain-English explanations | "62 failed authentication attempts recorded for this source.", "The event originates from an authentication service.", "The targeted port 22 hosts a remote-access or database service." |
| 5 | Read the sub-scores | Rule, statistical and ML bars shown separately | All three rendered with values |
| 6 | Check the created artefacts | Alert and incident links offered | "Alert ALT-000144 raised" and "Incident INC-000065 opened" |
| 7 | Follow the alert link | Alerts page opens with that alert focused | Alert detail modal opened |
| 8 | Submit an invalid IP (`999.999.1.1`) | Field-level error, nothing stored | Field highlighted; "source_ip must be a valid IPv4/IPv6 address"; event count unchanged |
| 9 | Untick "Store this event", analyse again | Verdict returned but nothing persisted | "dry run, nothing was stored" shown; no new alert |

**Verdict: PASS** (FR-03, FR-04, FR-05)

---

### FT-04 - Upload and analyse a CSV log file

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Log Analyzer | Drop zone and column guidance shown | Rendered |
| 2 | Upload `sample_data/sample_logs_mixed.csv` (120 rows) | Progress, then a summary | Completed; summary rendered |
| 3 | Check the KPI tiles | Total 120; normal + suspicious = 120 | Total 120, normal 61, suspicious 59, high-risk 53, critical 27 |
| 4 | Check the severity breakdown | Four bands populated | LOW 61, MEDIUM 6, HIGH 26, CRITICAL 27 |
| 5 | Check alert creation | Alerts raised for suspicious rows | 59 alerts created; link offered |
| 6 | Filter the results table by CRITICAL | Only critical rows shown | Filter worked |
| 7 | Export the results | CSV downloads | File downloaded with all analysed rows |
| 8 | Upload `sample_logs_invalid.csv` | Valid rows processed, invalid rows reported individually | 1 row analysed, 4 rejected, each with its line number and reason |
| 9 | Upload an empty file | Clear error, nothing stored | "The uploaded file is empty." |
| 10 | Attempt a `.exe` file | Rejected before upload | "Only .csv, .txt or .log files are accepted." |

**Verdict: PASS** (FR-10) - step 8 is the key case: a partially malformed file is
processed, not rejected wholesale.

---

### FT-05 - Triage an alert

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Alerts | Paginated queue with filters | Rendered with pagination |
| 2 | Filter severity = CRITICAL | Only critical alerts | Filter applied server-side |
| 3 | Filter status = NEW | Only new alerts | Applied |
| 4 | Search a source IP | Matching alerts only | Applied |
| 5 | Sort by highest risk | Descending risk order | Applied |
| 6 | Open an alert | Detail modal with reasons, telemetry, recommended action | All rendered |
| 7 | Add a note and click Investigate | Status becomes Investigating; note attributed | Status changed; note stored as "[timestamp] Priya Administrator: ..." |
| 8 | Click Resolve with confirmation | Confirmation dialog, then RESOLVED | Dialog shown; status changed |
| 9 | Click Escalate on another alert | Incident created and opened | Navigated to the incident details page |
| 10 | Check Settings > Audit log | Both changes recorded | `ALERT_STATUS_CHANGED` and `ALERT_ESCALATED` present |

**Verdict: PASS** (FR-06, FR-12)

---

### FT-06 - Drive an incident through its lifecycle

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open an incident in NEW | Lifecycle tracker at stage 1 | Rendered |
| 2 | Inspect the available buttons | **Only** Investigate, Reopen-as-open and False positive | Contain and Resolve were **not** offered |
| 3 | Click Investigate, add a note | Status INVESTIGATING; tracker advances | Confirmed |
| 4 | Click Contain, add a note | Status CONTAINED; `contained_at` set | Confirmed |
| 5 | Click Resolve with a resolution summary | Status RESOLVED; summary stored | Confirmed |
| 6 | Check the status history | Four entries, each attributed and timestamped | Four entries shown newest first |
| 7 | Check the linked alerts | Closed with the incident | Alert status became RESOLVED |
| 8 | Reassign the incident | Assignee changes; recorded in history | Confirmed |
| 9 | Attempt an illegal transition via the API directly (`NEW -> RESOLVED`) | HTTP 409 with the allowed set | `{"error":"CONFLICT", "details":{"current":"NEW","allowed":["FALSE_POSITIVE","INVESTIGATING","OPEN"]}}` |

**Verdict: PASS** (FR-07) - step 2 and step 9 together confirm the state machine
is enforced in both the UI and the API.

---

### FT-07 - Manage the asset inventory

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Assets | Inventory with risk levels and event counts | 12 seeded assets rendered |
| 2 | Add a new asset | Created; risk starts LOW | Created; toast confirmed |
| 3 | Add a duplicate IP | Rejected with a specific message | "An asset with IP address ... is already registered." |
| 4 | Edit an asset to QUARANTINED | Status updated | Confirmed |
| 5 | Analyse a CRITICAL event against that asset's IP | Asset risk rises | Risk level became CRITICAL |
| 6 | Delete an asset | Confirmation dialog; events preserved | Dialog shown; event total unchanged afterwards |
| 7 | Filter by risk level and search by name | Filters applied | Both worked |

**Verdict: PASS** (FR-08)

---

### FT-08 - Review threat intelligence

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Threat Intelligence | Feed with a prominent simulation notice | Warning banner displayed |
| 2 | Inspect the indicators | RFC 5737 / reserved namespaces only | All addresses in 192.0.2.x, 198.51.100.x, 203.0.113.x; domains `.invalid` / `.example` |
| 3 | Filter by each of the four indicator types | Type filter applied | All four worked |
| 4 | Change an indicator to MONITORING | Status updated and audited | Confirmed |

**Verdict: PASS** (FR-09)

---

### FT-09 - Generate and export a report

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Reports | Generation form and a live preview | Preview figures rendered |
| 2 | Choose 30 days, Summary, click Generate | Report created and displayed | `RPT-000001` created; modal opened |
| 3 | Read the recommendations | Derived from the actual data | Recommendations referenced the observed critical count, brute-force and scanning categories, and the open incident count |
| 4 | Download PDF | A real PDF file | Downloaded; opened correctly; 7 sections |
| 5 | Download CSV | Flattened CSV | Downloaded and opened in a spreadsheet |
| 6 | Download JSON | Structured JSON | Downloaded |
| 7 | Delete a report with confirmation | Removed | Confirmed |

**Verdict: PASS** (FR-11)

---

### FT-10 - Settings, audit trail and system status

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open Settings > Profile | Current profile shown | Rendered |
| 2 | Change the full name and save | Persisted; reflected in the top bar | Confirmed |
| 3 | Change the password and re-login | New password works | Confirmed |
| 4 | Settings > Detection, move the sensitivity slider to 1.5 | Saved | Confirmed |
| 5 | Analyse the same borderline event before and after | Higher risk at 1.5 | Risk increased |
| 6 | Settings > System status | Live table counts, engine mode, thresholds | All rendered; counts matched the database |
| 7 | Settings > Audit log | Every action from this session listed | All present, newest first |
| 8 | Click "Reload detection models" | Engine reloads without a restart | Toast "Detection engine reloaded in hybrid-ml mode." |

**Verdict: PASS** (FR-12, NFR-07)

---

### FT-11 - Error handling and degraded operation

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Stop the Flask backend, reload the Dashboard | Clear "Backend unavailable" state, **not** a forced sign-out | Error state shown with the exact start command; session retained |
| 2 | Restart the backend, click Try again | Data loads | Recovered without re-login |
| 3 | Rename `ml_model/` and restart the backend | Engine degrades to rules mode | Health reported `hybrid-rules`; ML Models check showed "FALLBACK"; detections continued |
| 4 | Restore `ml_model/`, reload models from Settings | Engine returns to `hybrid-ml` | Confirmed |
| 5 | Request a non-existent route | JSON 404, not an HTML error page | `{"success":false,"error":"NOT_FOUND",...}` |
| 6 | Navigate to an unknown frontend route | Styled 404 page with a route back | Rendered |
| 7 | Let a token expire, then act | Redirected to login once | Session cleared on 401 and redirected |

**Verdict: PASS** (NFR-04) - step 3 demonstrates the requirement that the system
works without a trained model.

---

## 4. Defects found and fixed during functional testing

Honest record of what testing actually caught.

| # | Defect | Severity | Detected by | Resolution | Verified by |
|---|--------|----------|-------------|------------|-------------|
| D1 | Severity distribution saturated: every simulated attack scored CRITICAL and the HIGH band was empty, making the dashboard charts meaningless | High | Manual review of the seeded dashboard (FT-02) | Three changes: logarithmic magnitude terms in the rule bank; a saturating exponential curve in the statistical scorer; low/medium/high intensity tiers in the data generator | `test_generated_dataset_covers_every_severity_band`, `test_risk_grows_with_attack_intensity` |
| D2 | A wrong password shorter than six characters returned HTTP 422 (a validation error) instead of 401, because the registration password-strength rule was being applied at sign-in | Medium | TC-01.2 during API smoke testing | Login now checks only that a password was supplied; the strength rule applies to password *changes* | `test_login_with_wrong_password_is_rejected` |
| D3 | Single-event ML inference took ~45 ms because the models were loaded with `n_jobs=-1`; joblib's thread-pool dispatch dominated the work for a one-row prediction | Medium | Performance measurement (document 19) | Force `n_jobs = 1` on the loaded models; training still uses all cores | Re-measured: 7.1 ms mean (6.4x faster) |
| D4 | Escalating an alert that already had an auto-created incident was expected to create a second incident | Low | `test_resolving_an_incident_closes_its_alerts` failing | The behaviour was correct (escalation is idempotent); the **test** was wrong and was corrected, and a dedicated test was added for the idempotence property | `test_escalating_an_already_linked_alert_returns_the_same_incident` |
| D5 | Tailwind build failed on `border-white/12` - opacity 12 is not on the default scale | Low | `npm run build` | Replaced with `/15` throughout | Build succeeds |

> D4 is worth noting for the viva: the first instinct on a failing test is to
> change the code. Here the code was right and the test encoded a wrong
> assumption. The fix was to correct the test **and** add an explicit test for the
> behaviour that had been misunderstood.

---

## 5. Functional testing summary

| Measure | Result |
|---------|--------|
| Automated test cases | 117 |
| Automated pass rate | 117 / 117 (100%) |
| Manual scenarios | 11 |
| Manual pass rate | 11 / 11 (100%) |
| Functional requirements covered | 12 / 12 |
| Requirements with a negative-path test | 12 / 12 |
| Defects found | 5 |
| Defects fixed and re-verified | 5 |
| Defects outstanding | 0 |

### 5.1 What is not covered

Stated plainly rather than implied:

- **No automated frontend tests.** React components are verified manually
  (Section 3) and by the production build succeeding. A Vitest + React Testing
  Library suite is listed under future enhancements.
- **No cross-browser matrix.** Testing was performed on Chromium-based browsers
  and Firefox on Windows 11 only.
- **No load or concurrency testing.** The measurements in document 19 are
  single-user. Concurrent-writer behaviour under SQLite is untested.
- **No penetration testing.** Security testing here is limited to input
  validation and access control at the API level.
