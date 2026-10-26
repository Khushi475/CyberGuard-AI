# 19 - Non-Functional Testing

**Project:** CyberGuard AI
**Lab experiment:** 9 - Non-functional testing

---

## How to read this document

Every section is split into **Test procedure** (how to reproduce it) and
**Result**. Results are one of:

| Label | Meaning |
|-------|---------|
| **Measured** | A real number produced by running the stated procedure on the machine described below. The procedure can be re-run to reproduce it. |
| **Observed** | A qualitative outcome confirmed by executing the procedure (for example, "the engine continued to classify events"). |
| **Procedure only** | The method is defined but no number is claimed, because the measurement needs equipment, users or scale this project does not have. |

**No figure in this document is estimated, extrapolated or invented.** Where a
number is absent, the section says so explicitly.

### Measurement environment

| Item | Value |
|------|-------|
| Machine | Windows 11 Home Single Language, 10.0.26200 |
| Python | 3.10.0 |
| Node.js | 24.14.1, npm 11.11.0 |
| Database | SQLite, `database/cyberguard.db`, ~440 events after seeding |
| Engine mode | `hybrid-ml` unless stated otherwise |
| Method | Single user, no concurrent load, warm process (first call discarded) |

---

## NFR-01 - Performance

### Test P1 - Detection engine latency per event

**Test procedure**

```python
# backend/  (with the venv active)
from app.ml.detector import ThreatDetector
from app.ml.generate_dataset import generate_events
import time, statistics

events = generate_events(2000, seed=99, days_back=14)
d = ThreatDetector(model_dir="ml_model")   # or model_dir=None for rules mode
d.detect(events[0])                        # warm-up, discarded
times = []
for e in events:
    t0 = time.perf_counter(); d.detect(e); times.append((time.perf_counter()-t0)*1000)
```

**Result: Measured** (n = 2000 events per mode)

| Mode | Mean | Median | p95 | p99 | Max | Throughput |
|------|------|--------|-----|-----|-----|-----------|
| `hybrid-ml` | **7.083 ms** | 6.596 ms | 9.890 ms | 13.672 ms | 38.948 ms | 141 events/s |
| `hybrid-rules` | **0.033 ms** | 0.027 ms | 0.069 ms | 0.121 ms | 0.616 ms | 29 930 events/s |

**Target:** under 50 ms per event. **Met**, with the p99 at 13.7 ms in ML mode.

**Defect found and fixed during this measurement.** The first run recorded a mean
of **45.353 ms** in `hybrid-ml` mode - close to the target ceiling and 1800x
slower than rules mode. Isolating the sub-calls showed:

| Call | With `n_jobs=-1` | With `n_jobs=1` |
|------|------------------|-----------------|
| `RandomForest.predict_proba` on 1 sample | 43.007 ms | 4.578 ms |
| `IsolationForest.decision_function` | 1.921 ms | 1.814 ms |
| `StandardScaler.transform` | 0.041 ms | 0.041 ms |

The models are trained with `n_jobs=-1`, which is correct for fitting. At
inference the engine scores **one event at a time**, and joblib spent far longer
dispatching to a thread pool than doing the work. The detector now forces
`n_jobs = 1` on the loaded models, which produced the 6.4x improvement above.
This is recorded as defect D3 in document 18.

### Test P2 - API endpoint latency

**Test procedure:** call each endpoint 25 times through the Flask test client
against the seeded database, discarding the first call.

**Result: Measured** (n = 25 per endpoint)

| Endpoint | Mean | p95 |
|----------|------|-----|
| `GET /api/health` | 0.7 ms | 0.8 ms |
| `GET /api/assets` | 2.5 ms | 2.8 ms |
| `GET /api/alerts?per_page=15` | 4.4 ms | 3.9 ms |
| `GET /api/incidents?per_page=15` | 8.3 ms | 9.4 ms |
| `POST /api/events/analyze?persist=false` | 8.5 ms | 10.7 ms |
| `GET /api/events?per_page=20` | 10.5 ms | 13.2 ms |
| `GET /api/dashboard/stats` | 13.4 ms | 16.4 ms |
| `GET /api/analytics?days=30` | 14.0 ms | 17.0 ms |

**Target:** dashboard aggregation under 1 s. **Met** - the heaviest endpoint
(`/api/analytics`, which runs roughly a dozen aggregate queries) completes in
14 ms, about 70x inside the target.

These figures exclude network transport and browser rendering, because they were
taken through the test client. They measure the server's own work.

### Test P3 - Bulk CSV analysis

**Test procedure:** upload `sample_data/sample_logs_mixed.csv` (120 rows) through
`POST /api/events/upload` and time the complete request.

**Result: Measured**

| Metric | Value |
|--------|-------|
| Rows | 120 |
| Total request time | 1475.1 ms |
| Per row | 12.3 ms |
| Status | 201 |

The per-row cost (12.3 ms) exceeds the isolated engine cost (7.1 ms) because it
also includes CSV parsing, per-row validation, four ORM inserts and the shared
commit. A 5000-row file - the configured ceiling - would therefore take roughly
60 seconds, which is why the ceiling exists and why the client uses a 120-second
timeout for uploads.

### Test P4 - Frontend bundle size

**Test procedure:** `npm run build` and read the emitted asset sizes.

**Result: Measured**

| Asset | Raw | Gzipped |
|-------|-----|---------|
| `index.html` | 1.00 kB | 0.52 kB |
| CSS bundle | 38.27 kB | 6.99 kB |
| JS bundle | 824.48 kB | 231.24 kB |
| Build time | 4.93 s | |

The JS bundle is dominated by Recharts and React. It is a single chunk; route-based
code splitting is listed under future enhancements.

### Not measured

- **Latency under concurrent load.** No load-testing tool was used. Reproducing
  this would need Locust or JMeter driving many simultaneous sessions.
  **Procedure only.**
- **End-to-end browser latency.** Would require browser performance timings.
  **Procedure only.**

---

## NFR-02 - Security

### Test S1 - Password storage

**Test procedure:** open `database/cyberguard.db` and inspect `users.password_hash`.

```bash
python -c "import sqlite3;print(sqlite3.connect('database/cyberguard.db').execute('select email,password_hash from users limit 1').fetchone())"
```

**Result: Observed.** The column stores a Werkzeug PBKDF2 hash of the form
`pbkdf2:sha256:<iterations>$<salt>$<digest>`. No plaintext password appears
anywhere in the database, and no API response contains a password or hash field
(asserted by `test_login_with_valid_credentials_returns_token`).

### Test S2 - Authentication enforcement

**Test procedure:** call protected endpoints with no token, and with a forged one.

**Result: Measured** (automated, TC-11)

| Case | Expected | Actual |
|------|----------|--------|
| No token on `/api/alerts` | 401 `NO_TOKEN` | 401 `NO_TOKEN` |
| Forged token | 401 `TOKEN_INVALID` | 401 `TOKEN_INVALID` |
| Dashboard, events, incidents, assets, upload without a token | 401 | 401 in all cases |

All five negative cases pass.

### Test S3 - Account-existence disclosure

**Test procedure:** compare the response for an unknown email with the response
for a known email and a wrong password.

**Result: Measured.** Both return HTTP 401 with the byte-identical message
"Invalid email address or password." Asserted by
`test_login_with_unknown_email_gives_the_same_message`.

### Test S4 - Input validation coverage

**Test procedure:** submit each invalid-input class and check for a 4xx response
naming the offending field.

**Result: Measured** (automated, TC-10)

| Invalid input | Response |
|---------------|----------|
| Malformed IP `999.999.1.1` | 422, `details.field = source_ip` |
| Port 70000 | 422, `details.field = destination_port` |
| Unknown protocol | 422 listing valid protocols |
| Negative failed-login count | 422 |
| Non-numeric bytes | 422 |
| Report period 9999 days | 422 |
| Unknown report type | 422 |
| Duplicate asset IP | 422, `details.field = ip_address` |

8 of 8 classes rejected with a specific, actionable message.

### Test S5 - SQL injection resistance

**Test procedure:** search and filter parameters were supplied with SQL
metacharacters (`' OR 1=1 --`) through `/api/alerts?search=`, and the code base
was inspected for string-built SQL.

**Result: Observed.** The input is treated as a literal search string and returns
no rows. A repository-wide search finds no f-string or concatenated SQL: every
query is built through SQLAlchemy expression objects, which parameterise values.
The single raw statement in the code base is `db.text("SELECT 1")`, a constant
liveness probe with no interpolation.

### Test S6 - Secret management

**Test procedure:** search the repository for hard-coded secrets and check
`.gitignore`.

**Result: Observed.** `SECRET_KEY` and `DATABASE_URL` are read from the
environment with development defaults in `config.py`. `.env` is git-ignored and
only `.env.example` is committed. The seeded demo passwords are intentionally
documented - they are demonstration credentials for a local prototype, and the
README says so.

### Test S7 - Upload safety

**Test procedure:** attempt oversized, wrong-type and empty uploads.

**Result: Measured**

| Case | Response |
|------|----------|
| `.exe` file | 422 listing accepted extensions |
| Empty file | 422 "The uploaded file is empty." |
| Over 8 MB | 413 naming the limit |
| Over 5000 rows | Excess skipped and reported |

### Security limitations (stated, not tested away)

The following are **absent by design** in an academic prototype and are not
claimed to be secure:

- Tokens cannot be revoked before expiry - there is no server-side session store.
- No rate limiting on the login endpoint, so repeated attempts are not throttled.
- No CSRF token (the API is token-authenticated rather than cookie-authenticated,
  which mitigates but does not eliminate the concern).
- No HTTPS in the shipped topology - everything is plaintext over loopback.
- Role checks are coarse: any authenticated user can reach most endpoints.
- No penetration testing or dependency vulnerability scanning was performed.

---

## NFR-03 - Usability

### Test U1 - Task completion walkthrough

**Test procedure:** perform each core task without consulting documentation, and
record the number of interactions needed from the dashboard.

**Result: Observed**

| Task | Clicks from the dashboard | Completed without documentation |
|------|---------------------------|----------------------------------|
| Analyse a sample event | 3 (Threat Detection -> sample -> Analyze) | Yes |
| Find all critical alerts | 2 (Alerts -> severity filter) | Yes |
| Resolve an alert | 3 (open -> Resolve -> confirm) | Yes |
| Investigate and resolve an incident | 5 | Yes |
| Upload and analyse a log file | 3 | Yes |
| Generate and download a PDF report | 3 | Yes |
| Add a monitored asset | 3 | Yes |

### Test U2 - Interface state coverage

**Test procedure:** for every page that loads data, force each of the four states
(loading, populated, empty, error) and confirm a purposeful rendering.

**Result: Observed** - all four states implemented on all ten data-driven pages.

| Page | Loading | Empty | Error | Confirmation on destructive action |
|------|---------|-------|-------|-------------------------------------|
| Dashboard | Skeleton cards | N/A (always aggregates) | Error panel with retry | N/A |
| Threat Detection | Spinner in the button | Explanatory empty state | Error panel | N/A |
| Alerts | Skeleton table | Empty state with "clear filters" | Error panel with retry | Yes |
| Incidents | Skeleton table | Empty state with "new incident" | Error panel | N/A |
| Incident Details | Loading state | N/A | Error panel | Yes (transition modal) |
| Threat Intelligence | Skeleton table | Empty state | Error panel | N/A |
| Log Analyzer | Progress bar with percentage | Explanatory empty state | Error panel listing rejected rows | N/A |
| Assets | Skeleton table | Empty state with "add asset" | Error panel | Yes |
| Reports | Skeleton table | Empty state | Error panel | Yes |
| Settings | Skeleton table | N/A | Error panel with retry | N/A |

### Test U3 - Accessibility checks

**Test procedure:** keyboard-only navigation; contrast inspection of the severity
palette against the `#0a1120` surface; inspection of ARIA attributes.

**Result: Observed**

| Check | Outcome |
|-------|---------|
| Keyboard navigation reaches every interactive control | Yes - a visible focus ring is defined globally via `:focus-visible` |
| Modals close on Escape and on overlay click | Yes |
| Body scroll is locked while a modal is open | Yes |
| Icon-only buttons have accessible names | Yes - `aria-label` on each |
| Toggles expose their state | Yes - `role="switch"` with `aria-checked` |
| Toast region is announced | Yes - `role="status"`, `aria-live="polite"` |
| Severity is never signalled by colour alone | Yes - every badge carries its text label |
| Body text contrast (`#e2e8f0` on `#0a1120`) | Approximately 14:1, comfortably above WCAG AA |

**Not measured:** no automated audit (axe, Lighthouse) and no screen-reader
testing was performed. **Procedure only.**

### Test U4 - Responsive layout

**Test procedure:** resize the browser through mobile, tablet and desktop widths
and check for horizontal overflow and control accessibility.

**Result: Observed**

| Width | Behaviour |
|-------|-----------|
| 375 px | Sidebar collapses to a drawer; KPI cards stack to one column; tables scroll horizontally within their container, with no page-level overflow |
| 768 px | Two-column KPI grid; sidebar still a drawer |
| 1024 px | Sidebar becomes permanent; multi-column panels |
| 1440 px+ | Full layout, capped at 1600 px so content does not stretch indefinitely |

**Not measured:** no real-device testing; results are from browser emulation.

---

## NFR-04 - Reliability

### Test R1 - Operation without trained ML models

**Test procedure:** rename `backend/ml_model/`, restart the backend, and analyse
events.

**Result: Observed and automated.** The engine reports `hybrid-rules`, the
Settings page shows the ML Models check as "FALLBACK", and classification
continues using the rule bank plus the default statistical baseline. Automated by
`test_engine_works_without_any_trained_model`.

### Test R2 - Partial-failure isolation in bulk upload

**Test procedure:** upload `sample_data/sample_logs_invalid.csv`, which contains
one valid row and four deliberately malformed ones.

**Result: Measured**

| Metric | Value |
|--------|-------|
| HTTP status | 201 (success) |
| Rows analysed | 1 |
| Rows rejected | 4 |
| Error detail | Row number and reason for each rejection |

One bad row does not abort the file. Automated by
`test_csv_upload_reports_invalid_rows_without_failing`.

### Test R3 - Transaction atomicity

**Test procedure:** inspect the commit boundary in `analyze_batch`, then upload a
file and confirm that either all rows are present or none are.

**Result: Observed.** `persist_analysis` is called with `commit=False` for every
row and a single `db.session.commit()` follows the loop. There is no intermediate
state in which some rows produced alerts and others were lost. The global error
handler calls `db.session.rollback()` on any unhandled exception.

### Test R4 - Backend unavailability

**Test procedure:** stop the Flask process and use the console.

**Result: Observed.** Each page shows a "Backend unavailable" error state
containing the exact commands to start the server. Critically, **the session is
not cleared** - only a genuine HTTP 401 signs the user out - so restarting the
backend and clicking "Try again" restores the page without re-authenticating.

### Test R5 - Repeatable initialisation

**Test procedure:** run `python seed_database.py` twice in succession.

**Result: Observed.** The script drops and recreates all ten tables, then
re-seeds. Both runs produced an identical, consistent dataset. A missing database
file is recreated by `db.create_all()` at start-up.

### Not measured

- **Mean time between failures / uptime.** Requires long-running observation.
  **Procedure only:** run the stack for a defined period under synthetic traffic
  and poll `/api/health` on an interval, recording failures.
- **Crash recovery under concurrent writers.** Not tested. **Procedure only.**

---

## NFR-05 - Maintainability

### Test M1 - Change-impact analysis

**Test procedure:** for each representative change, enumerate the files that must
be modified.

**Result: Observed**

| Change | Files to modify | Count |
|--------|-----------------|-------|
| Add a detection category | `ml/rules.py` (rule function + `RULE_BANK` + action + tactic) | 1 |
| Change a severity band | `ml/detector.py` (`SEVERITY_BANDS`) | 1 |
| Change an incident transition rule | `models/incident.py` (`INCIDENT_STATE_TRANSITIONS`) | 1 |
| Add a field to the event model | `models/security_event.py`, `utils/validators.py`, `ml/features.py` | 3 |
| Add an API endpoint | one blueprint in `routes/`, plus `services/` if it carries business logic | 1-2 |
| Change the API base URL | `frontend/src/services/api.js` | 1 |
| Restyle every severity badge | `frontend/src/utils/format.js` | 1 |
| Swap the database engine | `backend/.env` (`DATABASE_URL`) | 1 (configuration only) |

The single-file changes are the direct payoff of defining each concept exactly
once: the state machine, the severity bands and the severity colour map each
exist in one place and are consumed everywhere else.

### Test M2 - Structural metrics

**Test procedure:** count modules and inspect the import graph for cycles.

**Result: Measured**

| Metric | Value |
|--------|-------|
| Backend Python modules | 48 (plus 6 test modules) |
| Frontend JSX/JS modules | 22 |
| Backend packages | 5 (`routes`, `services`, `ml`, `models`, `utils`) |
| REST endpoints | ~40 across 11 blueprints |
| Reusable UI primitives | ~20 in `components/ui.jsx` |
| Chart components | 7 in `components/charts/Charts.jsx` |
| Import cycles | 0 |
| Modules in `ml/` importing Flask or the database | 0 |

The last row is the important one: the detection engine has no dependency on the
web framework or the database, which is why its 18 unit tests need no application
context.

### Test M3 - Documentation-to-code consistency

**Test procedure:** for each behavioural claim in the documentation, locate the
code that enforces it.

**Result: Observed**

| Documented claim | Enforced by |
|------------------|-------------|
| Severity bands 0-25 / 26-50 / 51-75 / 76-100 | `SEVERITY_BANDS` in `ml/detector.py`; asserted by `test_severity_bands_match_the_specification` |
| Incident transition table | `INCIDENT_STATE_TRANSITIONS` in `models/incident.py`; asserted by `test_illegal_transition_is_refused` |
| Alert at risk >= 26, incident at risk >= 76 | `ALERT_RISK_THRESHOLD` / `INCIDENT_RISK_THRESHOLD` in `config.py`; asserted by `test_system_status_reports_table_counts` |
| ER relationships | SQLAlchemy foreign keys in `models/` |
| Every endpoint in the API documentation exists | `GET /api` returns a live index; asserted by `test_api_index_lists_endpoints` |

---

## NFR-06 - Scalability

### Test SC1 - Pagination enforcement

**Test procedure:** request an unbounded page size and inspect the SQL generated
for list endpoints.

**Result: Observed.** Every list endpoint paginates server-side with a hard
maximum of 200 rows per page (`parse_pagination`). Filtering, sorting and
aggregation are performed in SQL with `LIMIT`/`OFFSET`; no endpoint loads a full
table into Python and filters it there.

### Test SC2 - Database portability

**Test procedure:** inspect the persistence layer for dialect-specific code.

**Result: Observed.** All persistence goes through SQLAlchemy models. The only
dialect-specific expression is `func.strftime` in the hourly-distribution query,
which would need a one-line change for PostgreSQL (`date_part`). Everything else
is portable, so switching engines is a `DATABASE_URL` change.

### Test SC3 - Engine statelessness

**Test procedure:** inspect `ThreatDetector.detect` for mutable per-call state.

**Result: Observed.** `detect()` holds no state between calls; the only shared
state is the loaded models, which are read-only after initialisation and guarded
by a lock during loading. The engine is therefore safe to run behind multiple
workers.

### Known ceilings (stated, not tested)

- **SQLite allows one writer at a time.** This is the first real limit and would
  be hit before any application-level bottleneck.
- **CSV uploads hold parsed rows in memory,** which is why the 5000-row cap
  exists. At 12.3 ms per row, a full 5000-row file would take roughly 60 seconds.
- **No horizontal scaling was tested.** **Procedure only.**

---

## NFR-07 - Availability

### Test A1 - Health endpoint

**Test procedure:** `curl http://127.0.0.1:5000/api/health` with no token.

**Result: Measured.** Returns 200 in 0.7 ms (mean of 25 calls) with database
connectivity, engine mode and ML availability. It requires no authentication, so
it is usable as an external liveness probe.

### Test A2 - Subsystem self-check

**Test procedure:** `GET /api/system/status` and inspect the four checks.

**Result: Observed.** Reports Database, Detection Engine, ML Models and Event
Pipeline individually, with a per-check status and detail line, plus an overall
score. Surfaced on the dashboard and on Settings > System status.

### Test A3 - Graceful degradation matrix

**Result: Observed**

| Component unavailable | Behaviour | Console still usable? |
|----------------------|-----------|----------------------|
| scikit-learn / joblib / `ml_model/` | Engine reports `hybrid-rules`; detection continues | Yes, fully |
| ReportLab | PDF returns 501 with the install command | Yes; CSV and JSON exports work |
| Flask backend | Frontend shows "Backend unavailable" with the start command; session retained | Read-only; recovers without re-login |
| SQLite file deleted | Schema recreated at start-up; re-seed restores data | Yes after seeding |

### Not measured

- **Uptime percentage / SLA.** Requires sustained monitoring. **Procedure only:**
  poll `/api/health` at a fixed interval over a defined window and compute
  successful polls divided by total polls.

---

## Summary

| Requirement | Verdict | Evidence type |
|-------------|---------|---------------|
| NFR-01 Performance | **Met** - 7.1 ms mean detection, 14 ms heaviest endpoint, both far inside target | Measured (n = 2000 and n = 25) |
| NFR-02 Security | **Met for the stated scope**; limitations listed explicitly | Measured (automated) + Observed |
| NFR-03 Usability | **Met** - all four interface states on all ten data pages; keyboard accessible | Observed |
| NFR-04 Reliability | **Met** - degrades rather than fails; atomic transactions; partial-failure isolation | Observed + automated |
| NFR-05 Maintainability | **Met** - single-file changes for core concepts; zero import cycles | Measured + Observed |
| NFR-06 Scalability | **Design supports it**; SQLite's single writer is the stated ceiling | Observed |
| NFR-07 Availability | **Met for a single-process prototype**; every optional component degrades gracefully | Measured + Observed |

### Measurements deliberately not claimed

Concurrent load, real uptime, automated accessibility audits, screen-reader
compatibility, real-device responsive testing, cross-browser matrices and
penetration testing. Each has a stated procedure above; none has a number
attached, because none was performed.
