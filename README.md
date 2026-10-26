# CyberGuard AI - Intelligent Cyber Threat Detection System

A working, full-stack Security Operations Centre platform built for the
**BCSE301P Software Engineering Lab**. It ingests security telemetry, classifies
it with an explainable hybrid detection engine, raises alerts, drives a guarded
incident lifecycle, and reports on the outcome.

> **Academic prototype - defensive only.** This system analyses *simulated*
> security telemetry that a user supplies to it. It performs no scanning,
> probing, exploitation or attack automation of any kind, it makes no outbound
> network connections, and it contains no reference to real threat
> infrastructure. It is not production-ready and makes no production security
> claims. See [Known limitations](#known-limitations).

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [System requirements](#system-requirements)
- [Installation (Windows 11)](#installation-windows-11)
- [Running the application](#running-the-application)
- [Demo credentials](#demo-credentials)
- [Testing](#testing)
- [Project structure](#project-structure)
- [API documentation](#api-documentation)
- [The detection engine](#the-detection-engine)
- [Software Engineering documentation](#software-engineering-documentation)
- [Demonstrating the project in a viva](#demonstrating-the-project-in-a-viva)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Future enhancements](#future-enhancements)
- [Screenshots](#screenshots)

---

## Features

### Detection
- **Hybrid engine**: 7 explainable behavioural rules + statistical baseline + optional RandomForest and IsolationForest models
- **8 threat categories**: Normal Activity, Brute Force Attempt, Port Scanning Pattern, Suspicious Login Activity, Network Anomaly, Data Transfer Anomaly, Denial-of-Service Pattern, Credential Abuse Pattern
- **Explainable by design**: every verdict carries plain-English reasons, per-detector sub-scores, a recommended defensive action and a MITRE ATT&CK tactic reference
- **Works without ML**: if scikit-learn or the trained models are absent, the engine reports `hybrid-rules` mode and keeps working
- **Tunable sensitivity** per analyst (0.5 relaxed to 1.5 aggressive)

### Operations
- **Live dashboard** - 8 KPIs, 6 charts, threat level, system health, activity feed, all computed from the database
- **Alert triage** - server-side filtering, search, sorting, pagination; investigate / resolve / false positive / escalate
- **Incident lifecycle** - a guarded state machine; illegal transitions return HTTP 409, and the UI only offers legal ones
- **Log analyzer** - CSV upload with per-row validation; one malformed row never aborts the file
- **Asset inventory** - risk posture rises automatically with the highest-risk event observed
- **Threat intelligence** - a simulated indicator feed, clearly labelled as simulated
- **Reports** - generated from live data, exportable as PDF, CSV or JSON, with recommendations derived from the measured figures
- **Audit trail** - every state-changing action recorded, atomically with the change

### Engineering
- 117 automated tests, all passing
- ~40 REST endpoints across 11 blueprints with a uniform JSON envelope
- 23 Software Engineering documentation artefacts
- Strict layering: `routes -> services -> models`, with the detection engine depending on nothing inside the application

---

## Architecture

```
  Browser (React 18 + Vite + Tailwind + Recharts)
      |
      |  REST / JSON, Bearer token
      v
  Flask application factory
      |
      +-- routes/     11 blueprints, ~40 endpoints
      +-- services/   detection, alert, incident, analytics, report, auth, audit
      +-- ml/         detection engine (no Flask, no database dependency)
      |                 features.py   18 engineered features
      |                 rules.py      7 explainable behavioural rules
      |                 anomaly.py    statistical baseline
      |                 detector.py   fusion, severity, confidence, explanation
      +-- models/     10 SQLAlchemy entities
      +-- utils/      validation, security, errors, CSV parsing, logging
      |
      v
  SQLite (database/cyberguard.db)
```

Dependencies point strictly inward. `app/ml/` imports nothing from Flask or the
database, which is why its unit tests run with no application context at all.

---

## Technology stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3, Recharts, Lucide React, React Router 6, Axios |
| Backend | Python 3.10+, Flask 3, Flask-CORS, Flask-SQLAlchemy, SQLAlchemy 2 |
| Database | SQLite (via SQLAlchemy - portable to PostgreSQL by changing one URL) |
| ML | scikit-learn, NumPy, pandas, joblib (**all optional at runtime**) |
| Reports | ReportLab (optional - CSV and JSON always work) |
| Testing | pytest |

---

## System requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Windows 11 (also runs on Linux and macOS) |
| Python | 3.10 or newer |
| Node.js | 18 or newer (npm 9+) |
| RAM | 4 GB |
| Disk | ~500 MB including dependencies |
| Browser | Chrome, Edge or Firefox (current version) |

Check what you have:

```powershell
python --version
node --version
npm --version
```

If Python is missing, install it from python.org and **tick "Add Python to PATH"**.
If Node.js is missing, install the LTS build from nodejs.org.

---

## Installation (Windows 11)

Open PowerShell (or the VS Code terminal) in the project folder.

### Step 1 - Backend setup

```powershell
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

You should now see `(venv)` at the start of your prompt.

> If PowerShell blocks the activation script, run this once and retry:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### Step 2 - Environment file (optional)

```powershell
copy .env.example .env
```

The application runs with sensible defaults if you skip this. Create `.env` if
you want to change the port, the database path or the secret key.

### Step 3 - Train the ML models (optional)

```powershell
python -m app.ml.train_model
```

This generates 6000 synthetic events, trains a RandomForest and an
IsolationForest, fits the statistical baseline, and writes five artefacts into
`backend/ml_model/`.

**You can skip this.** Without the artefacts the engine runs in `hybrid-rules`
mode using the rule bank plus the default baseline, and everything still works.

### Step 4 - Seed the database

```powershell
python seed_database.py
```

This creates `database/cyberguard.db`, seeds 3 users, 12 assets and 15
indicators, pushes 320 synthetic events through the **real detection pipeline**,
advances some incidents through the lifecycle, triages some alerts, and
regenerates the sample CSV files.

Useful variants:

```powershell
python seed_database.py --events 500     # more history
python seed_database.py --keep           # add to existing data instead of resetting
python seed_database.py --no-csv         # don't regenerate sample_data/
```

### Step 5 - Frontend setup

Open a **second** terminal:

```powershell
cd frontend

npm install
```

---

## Running the application

You need **two terminals running at the same time**.

**Terminal 1 - backend:**

```powershell
cd backend
venv\Scripts\activate
python run.py
```

```
==================================================================
  CyberGuard AI - Intelligent Cyber Threat Detection System v1.0.0
  Academic prototype - defensive, simulated telemetry only
==================================================================
  API root        : http://127.0.0.1:5000/api
  Health check    : http://127.0.0.1:5000/api/health
  Detection engine: hybrid-ml (ml_available=True)
==================================================================
```

**Terminal 2 - frontend:**

```powershell
cd frontend
npm run dev
```

```
  VITE v5.4.21  ready in 412 ms
  ➜  Local:   http://localhost:5173/
```

**Open <http://localhost:5173> in your browser.**

The Vite dev server proxies `/api` to the Flask backend, so the browser only ever
talks to one origin.

---

## Demo credentials

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@cyberguard.ai` | `admin123` |
| Security Analyst | `analyst@cyberguard.ai` | `analyst123` |
| Viewer | `viewer@cyberguard.ai` | `viewer123` |

Click a demo card on the login page to fill the form automatically.

> These are seeded demonstration credentials for a local academic prototype.
> Passwords are stored as salted PBKDF2 hashes, never in plaintext.

---

## Testing

```powershell
cd backend
venv\Scripts\activate

python -m pytest                 # full suite, verbose
python -m pytest -q              # quiet summary
python -m pytest tests/test_detection_engine.py -v
python -m pytest -k "incident"   # filter by keyword
```

Latest run:

```
tests\test_alerts_incidents.py .........................                 [ 21%]
tests\test_assets_dashboard.py ................................         [ 48%]
tests\test_auth.py ...............                                       [ 61%]
tests\test_detection_engine.py ..................                        [ 76%]
tests\test_events.py ...........................                         [100%]

============================ 117 passed in 51.16s =============================
```

Every test module builds a fresh in-memory database, so the suite never touches
`database/cyberguard.db` and tests can run in any order.

You can also run the detection engine straight from the command line:

```powershell
python -m app.ml.predict --failed-logins 62 --dest-port 22 --event-type authentication
python -m app.ml.predict --csv ../sample_data/sample_logs_mixed.csv
```

---

## Project structure

```
CyberGuard-AI/
|
+-- frontend/
|   +-- src/
|   |   +-- components/
|   |   |   +-- ui.jsx                 ~20 reusable primitives
|   |   |   +-- charts/Charts.jsx      7 chart components
|   |   +-- pages/                     12 screens
|   |   +-- layouts/DashboardLayout.jsx
|   |   +-- context/                   AuthContext, ToastContext
|   |   +-- services/api.js            the ONLY module that talks to the backend
|   |   +-- hooks/useApi.js
|   |   +-- utils/format.js            severity colours, formatting
|   |   +-- App.jsx                    routes and guards
|   |   +-- main.jsx
|   +-- index.html
|   +-- package.json
|   +-- vite.config.js
|   +-- tailwind.config.js
|
+-- backend/
|   +-- app/
|   |   +-- routes/      11 blueprints
|   |   +-- models/      10 entities
|   |   +-- services/    7 services
|   |   +-- ml/          detection engine + training + CLI inference
|   |   +-- utils/       validators, security, errors, csv_parser, logger
|   |   +-- __init__.py  application factory
|   |   +-- config.py
|   |   +-- extensions.py
|   +-- tests/           5 test modules, 117 cases
|   +-- ml_model/        trained artefacts (generated)
|   +-- logs/            rotating application log (generated)
|   +-- seed_database.py
|   +-- requirements.txt
|   +-- run.py
|   +-- pytest.ini
|   +-- .env.example
|
+-- database/            cyberguard.db (generated)
+-- documentation/       23 SE artefacts
+-- sample_data/         4 CSV files (generated by the seeder)
+-- README.md
+-- .gitignore
```

---

## API documentation

Full reference with request/response examples for every endpoint:
**[documentation/API_Documentation.md](documentation/API_Documentation.md)**

The running application also serves a live index at `GET /api`.

**Most important endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login` | Sign in |
| GET | `/api/dashboard/stats` | All dashboard figures and charts |
| POST | `/api/events/analyze` | **Analyse one event** |
| POST | `/api/events/upload` | **CSV log ingestion** |
| GET | `/api/alerts` | Filterable alert queue |
| PUT | `/api/alerts/{id}` | Triage an alert |
| GET | `/api/incidents/{id}` | Incident with its legal transitions |
| PUT | `/api/incidents/{id}` | Drive the lifecycle |
| POST | `/api/reports/generate` | Generate a report |
| GET | `/api/health` | Liveness probe (no auth) |

Quick check from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

---

## The detection engine

Three detectors vote on every event:

```
  event (11 fields)
      |
      v
  18 engineered features
      |
      +-------------+-------------+
      |             |             |
      v             v             v
   Rule bank   Statistical   Machine learning
   7 rules     z-scores      RF + IsolationForest
   (explainable)(saturating)  (OPTIONAL)
      |             |             |
      +-------------+-------------+
                    |
                    v
      with ML:     0.58*rule + 0.18*anomaly + 0.24*ml
      without ML:  0.74*rule + 0.26*anomaly

      risk = clamp( max(weighted, 0.85 * rule_score) * sensitivity )
                    |
                    v
      LOW 0-25 | MEDIUM 26-50 | HIGH 51-75 | CRITICAL 76-100
                    |
                    v
      alert at >= 26, incident at >= 76
```

The **rule score acts as a floor**. The statistical and ML detectors contribute
only through the weighted term, so on their own they can raise an event to MEDIUM
for review but never to CRITICAL - which keeps unexplained outliers from flooding
the queue with unactionable "critical" noise.

Rule magnitude terms are **logarithmic** (`38 + 30*log10(failed/4)` for brute
force, for example) so that ordering is preserved across three orders of
magnitude instead of everything saturating at 100.

Measured on Windows 11 / Python 3.10: **7.1 ms** mean per event in `hybrid-ml`
mode, **0.033 ms** in `hybrid-rules` mode.

---

## Software Engineering documentation

All 23 artefacts are in [`documentation/`](documentation/).

| Document | Syllabus experiment |
|----------|---------------------|
| [01_Process_Model.md](documentation/01_Process_Model.md) | 1 - Process model analysis and selection |
| [02_WBS_and_Estimation.md](documentation/02_WBS_and_Estimation.md) | 2 - WBS (all four views) and estimation |
| [03_Requirements.md](documentation/03_Requirements.md) | Requirements specification (FR-01..12, NFR-01..07) |
| [04_ER_Diagram.md](documentation/04_ER_Diagram.md) | 3 - Structural modelling |
| [05_Context_DFD.md](documentation/05_Context_DFD.md) | 4 - Context flow diagram |
| [06_DFD_Level_0.md](documentation/06_DFD_Level_0.md) | 4 - DFD Level 0 |
| [07_DFD_Level_1.md](documentation/07_DFD_Level_1.md) | 4 - DFD Level 1 |
| [08_DFD_Level_2.md](documentation/08_DFD_Level_2.md) | 4 - DFD Level 2 |
| [09_State_Transition_Diagram.md](documentation/09_State_Transition_Diagram.md) | 5 - Behavioural modelling |
| [10_Use_Case_Model.md](documentation/10_Use_Case_Model.md) | 6 - Use case model |
| [11_Class_Model.md](documentation/11_Class_Model.md) | 6 - Class model |
| [12_Sequence_Diagrams.md](documentation/12_Sequence_Diagrams.md) | 7 - Interaction models |
| [13_Communication_Diagram.md](documentation/13_Communication_Diagram.md) | 7 - Collaboration models |
| [14_Package_Diagram.md](documentation/14_Package_Diagram.md) | 8 - Package model |
| [15_Component_Diagram.md](documentation/15_Component_Diagram.md) | 8 - Component model |
| [16_Deployment_Diagram.md](documentation/16_Deployment_Diagram.md) | 8 - Deployment model |
| [17_Test_Cases.md](documentation/17_Test_Cases.md) | 9 - Test case design |
| [18_Functional_Testing.md](documentation/18_Functional_Testing.md) | 9 - Functional testing |
| [19_Non_Functional_Testing.md](documentation/19_Non_Functional_Testing.md) | 9 - Non-functional testing |
| [20_Storyboard.md](documentation/20_Storyboard.md) | 10 - Storyboarding |
| [21_UI_Design.md](documentation/21_UI_Design.md) | 10 - UI design modelling |
| [22_Project_Report.md](documentation/22_Project_Report.md) | Full project report |
| [API_Documentation.md](documentation/API_Documentation.md) | Complete API reference |

**The syllabus mapping table is in
[22_Project_Report.md section 5](documentation/22_Project_Report.md).**

---

## Demonstrating the project in a viva

A 10-minute walkthrough that shows every syllabus concept against running code.

### 1. Show that it is real (1 min)

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

Point out `detection_engine.mode` and `database.connected`.

### 2. Login and dashboard (1 min)

Sign in with the Administrator demo card. On the dashboard:

- Note the Detection Accuracy tile **states its own source** ("Analyst-confirmed
  precision"). Explain that the system never shows a bare number.
- Note the Threat Level card states the basis for its assessment.

### 3. Analyse an event - the core demonstration (3 min)

Threat Detection -> load the sample **"Repeated failed SSH logins"** -> Analyze.

Talk through:
- The **risk score, severity and confidence**.
- The **reasons** - this is the explainability requirement in action.
- The **three sub-score bars** - rule bank, statistical, ML. Explain that the
  rule score is the floor, so a verdict is always anchored to something
  deterministic.
- The **alert and incident** that were created automatically at risk >= 26 and
  >= 76.

Then submit an **invalid IP** to show validation naming the exact field.

### 4. The state machine - the strongest SE demonstration (2 min)

Open the incident that was just created. Point out:

- The lifecycle tracker shows it in **NEW**.
- **Only three buttons are offered**: Investigate, Reopen as open, False positive.
  Contain and Resolve are **absent**.

Then, from a terminal, attempt the illegal transition directly:

```powershell
# replace 65 with the incident id
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/incidents/65 -Method Put `
  -Headers @{ Authorization = "Bearer $TOKEN" } -ContentType "application/json" `
  -Body '{"status":"RESOLVED"}'
```

It returns **HTTP 409** naming the current state and the allowed set. Explain that
`INCIDENT_STATE_TRANSITIONS` in `models/incident.py` is the single source of
truth, and the state transition diagram in document 09 describes exactly it.

Then drive the incident properly: Investigate -> Contain -> Resolve. Show the
four attributed history entries and that the linked alert closed with it.

### 5. CSV upload and error isolation (1.5 min)

Log Analyzer -> upload `sample_data/sample_logs_mixed.csv` -> show the severity
breakdown and per-record results.

Then upload `sample_data/sample_logs_invalid.csv`: **1 row analysed, 4 rejected**,
each with its line number and reason, and HTTP 201. Explain that one malformed
row must never abort a real log export.

### 6. Reports (1 min)

Generate a 30-day summary. Point out that the **recommendations are derived from
the actual figures**, not a fixed list. Download the PDF.

### 7. Tests and honesty (1.5 min)

```powershell
python -m pytest -q
```

117 passed. Then open
[18_Functional_Testing.md](documentation/18_Functional_Testing.md) section 4 and
walk through the five defects that testing actually caught - especially:

- **D1**, the severity saturation defect (every attack was CRITICAL, HIGH was
  empty) and the three-part fix.
- **D3**, the `n_jobs=-1` performance defect found by measurement (45 ms -> 7 ms).
- **D4**, the failing test that was itself wrong.

This is the strongest material in the project: it shows an engineering process,
not just a finished artefact.

### Likely viva questions

| Question | Where to answer from |
|----------|----------------------|
| Why Agile and not Waterfall? | Document 01 section 3, then the D1 defect as evidence |
| How does the engine decide? | Document 08, the Level 2 DFD |
| What if scikit-learn isn't installed? | Rename `ml_model/`, restart, show `hybrid-rules` mode still working |
| Is the ER diagram real? | `GET /api/system/status` shows live per-table row counts |
| Is 99.93% model accuracy believable? | No - say so. It is measured on synthetic data whose classes are separable by construction. The metadata file and document 22 both state this. |
| How is this safe? | Document 05: there is no outbound arrow anywhere in the context diagram |

---

## Troubleshooting

### `python` is not recognised

Python is not on PATH. Reinstall from python.org with **"Add Python to PATH"**
ticked, or use `py` instead of `python`.

### `venv\Scripts\activate` is blocked

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then retry. Alternatively use `venv\Scripts\activate.bat` from cmd.exe.

### `ModuleNotFoundError: No module named 'flask'`

The virtual environment is not active. You should see `(venv)` in your prompt:

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Port 5000 is already in use

```powershell
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

Or change the port in `backend/.env` (`PORT=5001`) and update the proxy target in
`frontend/vite.config.js`.

### Port 5173 is already in use

Vite will offer the next free port automatically. Use whichever URL it prints.

### The frontend shows "Backend unavailable"

The Flask server is not running. Start it in a separate terminal:

```powershell
cd backend
venv\Scripts\activate
python run.py
```

Then click **Try again** in the browser. You will **not** be signed out - the
session is preserved, and only a genuine 401 clears it.

### The dashboard is empty

The database has not been seeded:

```powershell
cd backend
venv\Scripts\activate
python seed_database.py
```

### Login fails with the demo credentials

Either the database was never seeded, or the demo password was changed from the
Settings page. Re-seed to reset:

```powershell
python seed_database.py
```

### `npm install` fails

```powershell
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm cache clean --force
npm install
```

### The engine shows `hybrid-rules` instead of `hybrid-ml`

This is **not an error** - the system is designed to run this way. To enable the
ML models:

```powershell
cd backend
venv\Scripts\activate
python -m app.ml.train_model
```

Then restart the backend, or click **Reload detection models** on
Settings -> Detection.

### PDF download returns an error

ReportLab is not installed:

```powershell
pip install reportlab
```

CSV and JSON exports work regardless.

### Tests fail with import errors

Run pytest from the `backend` directory, not the project root:

```powershell
cd backend
venv\Scripts\activate
python -m pytest
```

---

## Known limitations

Stated plainly rather than buried.

**Security**
- Tokens cannot be revoked before they expire; there is no server-side session store
- No rate limiting on the login endpoint
- No HTTPS in the shipped setup
- Role checks are coarse - any authenticated user reaches most endpoints
- No penetration testing or dependency vulnerability scanning was performed

**Data and detection**
- **All telemetry is synthetic.** The system has never analysed a real network capture
- The reported model accuracy is measured on synthetic hold-out data whose classes are well separated by construction - it is not evidence of real-world performance
- No cross-event correlation: each event is scored in isolation, so a slow distributed scan spread over many events would not be detected
- Indicators are simulated and are not automatically matched against events

**Scale and operations**
- SQLite allows one writer at a time - the first real ceiling
- CSV uploads are capped at 5000 rows because parsed rows are held in memory
- Single-process development server, no clustering or failover
- No concurrent-load testing was performed

**Testing**
- No automated frontend tests (React is verified manually and by the build)
- No cross-browser matrix, no real-device testing
- No automated accessibility audit or screen-reader testing

---

## Future enhancements

| Priority | Enhancement |
|----------|-------------|
| High | Cross-event correlation by source over a time window - the most significant detection gap |
| High | Automatic indicator matching against incoming events |
| High | Frontend test suite (Vitest + React Testing Library) |
| Medium | Server-side session store for immediate token revocation |
| Medium | Rate limiting on authentication and upload |
| Medium | Route-based code splitting (the bundle is currently one 824 kB chunk) |
| Medium | PostgreSQL deployment guide |
| Medium | Real PCAP or syslog ingestion for genuine calibration |
| Low | Light theme (the preference is stored but only dark ships) |
| Low | Scheduled report delivery |
| Low | WebSocket live feed instead of 45-second polling |

---

## Screenshots

Capture these from the running application and place them in
`documentation/screenshots/`:

| File | Screen | What to show |
|------|--------|--------------|
| `01-login.png` | Login | Split hero with the demo account cards |
| `02-dashboard.png` | Dashboard | KPIs, threat level, all six charts |
| `03-threat-detection.png` | Threat Detection | A CRITICAL verdict with its reasons and sub-scores |
| `04-alerts.png` | Alerts | The filtered queue |
| `05-alert-detail.png` | Alert detail | Reasons and recommended response |
| `06-incident-details.png` | Incident Details | The lifecycle tracker and status history |
| `07-log-analyzer.png` | Log Analyzer | The analysis summary after an upload |
| `08-log-analyzer-errors.png` | Log Analyzer | Rejected rows from `sample_logs_invalid.csv` |
| `09-assets.png` | Assets | The inventory with risk levels |
| `10-threat-intelligence.png` | Threat Intelligence | The simulation notice and indicator table |
| `11-reports.png` | Reports | A generated report with recommendations |
| `12-settings.png` | Settings | System status with live table counts |

---

## Licence and academic note

Built as coursework for **BCSE301P Software Engineering Lab**. All telemetry,
indicators and detections are simulated. IP addresses use the RFC 5737
documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and domains
use the reserved `.invalid` and `.example` namespaces, so nothing in this project
refers to real infrastructure.
