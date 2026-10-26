# 03 - Software Requirements Specification

**Project:** CyberGuard AI - Intelligent Cyber Threat Detection System
**Document type:** SRS (condensed, IEEE 830 inspired)

---

## 1. Introduction

### 1.1 Purpose

CyberGuard AI is a web-based platform that ingests security telemetry, classifies
it using an explainable hybrid detection engine, raises alerts, drives an
incident lifecycle, and reports on the result. This document specifies what the
system must do and the quality attributes it must exhibit.

### 1.2 Scope and safety boundary

**In scope (defensive only):**

- Accepting security event records that a user or a log file supplies.
- Scoring those records against behavioural rules, a statistical baseline and
  optional trained models.
- Alert triage, incident management, asset inventory, reporting, audit logging.

**Explicitly out of scope - and absent from the code base:**

| Excluded | Confirmation |
|----------|--------------|
| Real malware or malicious payloads | No binary payloads exist in the repository. |
| Exploit execution or vulnerability exploitation | The system performs no network operations against any host. |
| Credential theft or password cracking | No credential harvesting or brute-forcing code exists. |
| Attack automation or scanning | The engine only reads numbers already given to it; it never probes. |
| Real threat infrastructure | Indicators use RFC 5737 documentation IPs and reserved `.invalid` / `.example` domains. |

The system is an **academic prototype**. It is not production-ready and makes no
production security claims.

### 1.3 Definitions

| Term | Meaning |
|------|---------|
| Security Event | One observed record of network or authentication activity. |
| Detection Result | The engine's verdict on one event: classification, risk score, confidence, severity, reasons. |
| Risk Score | An integer 0-100 expressing how suspicious an event is. |
| Severity | The band a risk score falls into: LOW 0-25, MEDIUM 26-50, HIGH 51-75, CRITICAL 76-100. |
| Threat | A detection result that crossed the threat threshold and was classified as non-benign. |
| Alert | An analyst-facing notification raised from a threat (risk >= 26). |
| Incident | A tracked investigation case, following a defined lifecycle. |
| Indicator | A simulated threat-intelligence record giving context to detections. |

---

## 2. Overall description

### 2.1 Actors

| Actor | Description | Key goals |
|-------|-------------|-----------|
| **System Administrator** | Owns configuration, users, assets and the audit trail. | Keep the platform healthy and configured; review audit logs. |
| **Security Analyst** | Day-to-day operator of the console. | Triage alerts, investigate incidents, analyse events and logs, produce reports. |
| **System (Detection Engine)** | Autonomous internal actor. | Analyse every submitted event, classify it, raise alerts, open critical incidents, maintain asset risk. |

A **Viewer** role also exists in the data model for read-oriented access.

### 2.2 Operating environment

| Layer | Technology |
|-------|-----------|
| Client | Modern browser (Chrome, Edge, Firefox) |
| Frontend | React 18, Vite 5, Tailwind CSS 3, Recharts, Lucide |
| Backend | Python 3.10+, Flask 3, Flask-CORS, SQLAlchemy 2 |
| ML | scikit-learn, NumPy, pandas, joblib (all optional at runtime) |
| Database | SQLite |
| Host OS | Windows 11 (also runs on Linux/macOS) |

---

## 3. Functional Requirements

Each requirement lists its priority, the actor, the acceptance criteria, and
where it is implemented and tested.

---

### FR-01 - User Login

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Administrator, Analyst, Viewer |
| **Description** | The system shall authenticate a user by email and password and issue a signed, expiring session token. |
| **Input** | Email address, password, "remember me" flag. |
| **Processing** | Validate the email format; look up the account; verify the password against a salted PBKDF2 hash; reject inactive accounts; record the attempt in the audit trail; issue a token. |
| **Output** | On success: token plus the user profile. On failure: HTTP 401 with a message that does not reveal whether the account exists. |
| **Acceptance criteria** | (a) Valid credentials return a token. (b) Invalid credentials return 401. (c) Unknown email and wrong password return an identical message. (d) A disabled account cannot sign in. (e) Protected routes reject a missing or forged token with 401. (f) Both success and failure are audited. |
| **Implements** | `backend/app/services/auth_service.py`, `backend/app/routes/auth.py`, `backend/app/utils/security.py`, `frontend/src/pages/Login.jsx` |
| **Verified by** | `tests/test_auth.py` (15 cases) |

---

### FR-02 - Dashboard

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst, Administrator |
| **Description** | The system shall present a live security overview computed entirely from the database. |
| **Input** | Optional window in days (default 14). |
| **Processing** | Aggregate counts of events, threats, alerts, incidents, assets and indicators; derive the current threat level from unresolved 24-hour alerts; compute six chart series; assemble a merged activity feed; run a subsystem self-check. |
| **Output** | Totals, threat level, detection quality, system health, six chart series, recent alerts, activity feed. |
| **Acceptance criteria** | (a) No statistic on the dashboard is hard-coded in the frontend. (b) Totals match the corresponding list endpoints. (c) The threat level is one of LOW/MEDIUM/HIGH/CRITICAL. (d) Every severity band appears in the severity chart, even at zero. (e) The activity feed is ordered newest first. |
| **Implements** | `backend/app/services/analytics_service.py`, `backend/app/routes/dashboard.py`, `frontend/src/pages/Dashboard.jsx` |
| **Verified by** | `tests/test_assets_dashboard.py::test_dashboard_*` |

---

### FR-03 - Event Submission

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst |
| **Description** | The system shall accept a manually described security event, validate it, store it and analyse it. |
| **Input** | Source IP (required); destination IP, ports, protocol, event type, request count, failed logins, packet count, bytes transferred, connection duration, timestamp (all optional). |
| **Processing** | Validate every field; resolve the owning asset by IP; persist the event; invoke the detection engine; persist the detection result and any downstream artefacts. |
| **Output** | HTTP 201 with the stored event and its verdict. |
| **Acceptance criteria** | (a) A valid event is stored with `processed = true`. (b) An event whose IP matches a monitored asset is linked to it. (c) Every invalid field returns HTTP 422 naming the offending field. |
| **Implements** | `backend/app/routes/events.py`, `backend/app/utils/validators.py`, `backend/app/services/detection_service.py` |
| **Verified by** | `tests/test_events.py` |

---

### FR-04 - Event Analysis

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst |
| **Description** | The system shall analyse a submitted event and return an explainable verdict, optionally without storing anything. |
| **Input** | An event payload; optional `persist=false` for a dry run; optional per-analyst sensitivity. |
| **Processing** | Feature extraction -> rule bank -> statistical baseline -> optional ML -> score fusion -> severity mapping -> reason assembly. |
| **Output** | Classification, risk score (0-100), confidence (0-1), severity, threat flag, reason list, recommended defensive action, per-detector sub-scores, feature summary, analysis time. |
| **Acceptance criteria** | (a) Every verdict carries at least one reason. (b) Every verdict carries a recommended action. (c) The risk score is always within 0-100. (d) A dry run stores nothing. (e) The verdict includes the individual rule, statistical and ML sub-scores. |
| **Implements** | `backend/app/ml/detector.py`, `frontend/src/pages/ThreatDetection.jsx` |
| **Verified by** | `tests/test_detection_engine.py`, `tests/test_events.py` |

---

### FR-05 - Threat Detection

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | System |
| **Description** | The system shall classify event behaviour into one of eight defensive categories and assign a severity. |
| **Categories** | Normal Activity, Brute Force Attempt, Port Scanning Pattern, Suspicious Login Activity, Network Anomaly, Data Transfer Anomaly, Denial-of-Service Pattern, Credential Abuse Pattern. |
| **Processing** | Seven behavioural rules score the event; the highest-scoring rule wins the classification; the statistical and ML detectors adjust the fused score; the score maps to a severity band. |
| **Output** | A `DetectionResult` row, and for a threat a `Threat` row. |
| **Acceptance criteria** | (a) Each documented attack shape is classified into its intended category. (b) Normal traffic scores LOW and is not a threat. (c) The risk score increases monotonically with attack intensity. (d) The engine remains functional with no trained model present. (e) Severity bands match the specification exactly. |
| **Implements** | `backend/app/ml/` (features, rules, anomaly, detector) |
| **Verified by** | `tests/test_detection_engine.py` (18 cases) |

---

### FR-06 - Alert Management

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst |
| **Description** | The system shall raise an alert for any detection at MEDIUM severity or above, and let an analyst triage it. |
| **Input** | Filter criteria (severity, status, threat type, date range, minimum risk, free-text search, sort); status transitions with an optional note. |
| **Processing** | Server-side filtering and pagination; status transitions validated against the alert state machine; every change audited. |
| **Output** | A paginated alert queue with filter metadata; the updated alert. |
| **Alert states** | NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE. |
| **Acceptance criteria** | (a) A MEDIUM-or-above detection creates exactly one alert. (b) A LOW detection creates none. (c) Every filter narrows the result set correctly. (d) An invalid status returns 422 and an illegal transition returns 409. (e) An alert can be escalated to an incident, and escalating an already-linked alert returns the existing incident rather than a duplicate. |
| **Implements** | `backend/app/services/alert_service.py`, `frontend/src/pages/Alerts.jsx` |
| **Verified by** | `tests/test_alerts_incidents.py` |

---

### FR-07 - Incident Management

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst, Administrator |
| **Description** | The system shall manage investigation cases through a defined lifecycle, automatically opening one for any CRITICAL detection. |
| **Input** | Incident details for manual creation; a target status plus optional note and resolution summary for transitions; an assignee. |
| **Processing** | Validate the requested transition against the state machine; stamp `contained_at` / `resolved_at`; append to the status history; close the incident's alerts when the incident closes; audit every change. |
| **Output** | The incident with its history, linked alerts, related events and the list of currently legal transitions. |
| **Incident states** | NEW, OPEN, INVESTIGATING, CONTAINED, RESOLVED, FALSE_POSITIVE. |
| **Acceptance criteria** | (a) A CRITICAL detection opens an incident in NEW. (b) An illegal transition returns HTTP 409 naming the current state and the allowed set. (c) The full path NEW -> INVESTIGATING -> CONTAINED -> RESOLVED succeeds and records four history entries. (d) Resolving an incident resolves its alerts. (e) The API reports the legal transitions so the UI can never offer an illegal one. |
| **Implements** | `backend/app/models/incident.py`, `backend/app/services/incident_service.py`, `frontend/src/pages/IncidentDetails.jsx` |
| **Verified by** | `tests/test_alerts_incidents.py` |

---

### FR-08 - Asset Management

| Field | Detail |
|-------|--------|
| **Priority** | Should have |
| **Actor** | Administrator |
| **Description** | The system shall maintain the inventory of monitored assets and track each asset's risk posture. |
| **Input** | Asset name and IP (required); type, OS, location, owner, criticality, status. |
| **Processing** | Validate and enforce IP uniqueness; link incoming events to assets by IP; raise an asset's risk level to the highest risk observed on it; on deletion, detach events rather than destroying them. |
| **Output** | Paginated inventory with per-asset event counts. |
| **Acceptance criteria** | (a) A duplicate IP is rejected with 422. (b) A missing name or an invalid IP is rejected. (c) A CRITICAL detection against an asset raises that asset's risk level. (d) Deleting an asset preserves its historical events. |
| **Implements** | `backend/app/routes/assets.py`, `frontend/src/pages/Assets.jsx` |
| **Verified by** | `tests/test_assets_dashboard.py` |

---

### FR-09 - Threat Intelligence

| Field | Detail |
|-------|--------|
| **Priority** | Should have |
| **Actor** | Analyst |
| **Description** | The system shall present a simulated indicator feed, clearly labelled as simulated, across four indicator types. |
| **Types** | Suspicious IP, Suspicious Domain, Suspicious User Activity, Anomalous Network Activity. |
| **Input** | Filters by type, risk level, status and free-text search; a status change. |
| **Output** | Indicator, type, related category, risk, confidence, first seen, last seen, status - plus a notice stating that the feed is simulated. |
| **Acceptance criteria** | (a) Every indicator is flagged `is_simulated = true`. (b) The response carries an explicit simulation notice. (c) No indicator refers to real infrastructure. (d) An indicator's watch status can be changed. |
| **Implements** | `backend/app/routes/threats.py`, `frontend/src/pages/ThreatIntelligence.jsx` |
| **Verified by** | `tests/test_assets_dashboard.py::test_threat_intelligence_is_marked_simulated` |

---

### FR-10 - Log Analysis

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst |
| **Description** | The system shall accept a CSV log file, validate each row independently, analyse every valid row and report the outcome. |
| **Input** | A `.csv`, `.txt` or `.log` file up to 8 MB and 5000 rows. |
| **Processing** | Decode (UTF-8 with BOM tolerance, latin-1 fallback); sniff the delimiter; normalise header aliases; validate each row; analyse each valid row through the same pipeline as a manual submission; commit in one transaction. |
| **Output** | Total records, normal, suspicious, high-risk and critical counts; per-severity breakdown; category and top-source distributions; per-record results; rejected rows with the reason for each. |
| **Acceptance criteria** | (a) Only `source_ip` is mandatory. (b) Column aliases (`bytes`, `packets`, `failed_logins`, `duration`) are accepted. (c) An invalid row is reported with its line number and reason, and does **not** abort the upload. (d) An empty file, a header-only file, a file missing `source_ip` and a wrong extension are each rejected with a specific message. (e) Alerts are raised for suspicious rows. |
| **Implements** | `backend/app/utils/csv_parser.py`, `backend/app/services/detection_service.py::analyze_batch`, `frontend/src/pages/LogAnalyzer.jsx` |
| **Verified by** | `tests/test_events.py` (9 upload cases) |

---

### FR-11 - Report Generation

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | Analyst, Administrator |
| **Description** | The system shall generate a security report from live data and export it as PDF, CSV or JSON. |
| **Input** | Period in days (1-365), report type (SUMMARY / THREAT / INCIDENT / COMPLIANCE), optional custom title. |
| **Processing** | Aggregate the period's figures; derive recommendations from the measured values; store the report as structured JSON; render on demand. |
| **Output** | Title, generation date, totals, severity breakdown, threat categories, detection statistics, incident statistics, at-risk assets and recommendations. |
| **Acceptance criteria** | (a) A report is stored and re-downloadable. (b) All three export formats work; PDF returns a real PDF or a clear 501 if ReportLab is absent. (c) Recommendations reflect the actual data, not a fixed list. (d) An invalid period or type is rejected with 422. (e) Preview computes figures without storing a report. |
| **Implements** | `backend/app/services/report_service.py`, `frontend/src/pages/Reports.jsx` |
| **Verified by** | `tests/test_assets_dashboard.py::test_report_*` |

---

### FR-12 - Audit Logging

| Field | Detail |
|-------|--------|
| **Priority** | Must have |
| **Actor** | System, Administrator |
| **Description** | The system shall record every state-changing action in an append-only audit trail. |
| **Recorded actions** | LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, PROFILE_UPDATED, PREFERENCES_UPDATED, PASSWORD_CHANGED, EVENT_SUBMITTED, EVENT_ANALYSED, EVENT_DELETED, LOG_UPLOAD_ANALYSED, ALERT_STATUS_CHANGED, ALERT_ESCALATED, INCIDENT_CREATED, INCIDENT_STATUS_CHANGED, INCIDENT_ASSIGNED, ASSET_CREATED, ASSET_UPDATED, ASSET_DELETED, INDICATOR_UPDATED, REPORT_GENERATED, REPORT_DOWNLOADED, REPORT_DELETED, MODEL_RELOADED, DATABASE_SEEDED. |
| **Processing** | Each entry captures action, description, entity type and id, acting user, client IP and outcome, and is committed atomically with the change it describes. |
| **Output** | A queryable audit log, surfaced on the Settings page. |
| **Acceptance criteria** | (a) Every listed action produces an entry. (b) A failed login is recorded with status FAILURE. (c) The trail is viewable through the API and the UI. |
| **Implements** | `backend/app/services/audit_service.py`, `backend/app/models/audit_log.py`, Settings > Audit log tab |
| **Verified by** | `tests/test_auth.py`, `tests/test_assets_dashboard.py::test_audit_log_records_every_state_change` |

---

## 4. Non-Functional Requirements

### NFR-01 - Performance

| Field | Detail |
|-------|--------|
| **Requirement** | Single-event analysis shall complete well within interactive latency, and a 120-row CSV shall be analysed in a single request without timing out. |
| **Target** | Engine analysis under 50 ms per event; dashboard aggregation under 1 s on the seeded dataset. |
| **Design support** | Indexed foreign keys and timestamps; SQL-side aggregation rather than in-Python loops; batch CSV analysis committed once rather than per row; models loaded once per process and cached. |
| **Measurement** | `analysis_time_ms` is recorded on every `DetectionResult` and exposed through `GET /api/analytics`. See document 19 for the measurement procedure. |

### NFR-02 - Security

| Field | Detail |
|-------|--------|
| **Requirement** | The prototype shall apply defensive coding practices appropriate to an academic build, without claiming production security. |
| **Controls** | Salted PBKDF2 password hashing (Werkzeug); signed, expiring session tokens; validation of every input before it reaches the engine or the database; SQLAlchemy parameterised queries (no string-built SQL anywhere); explicit CORS allow-list; an 8 MB upload ceiling and a 5000-row cap; uniform authentication errors that do not disclose account existence; no secrets in source, configuration via `.env`. |
| **Stated limits** | Tokens are not revocable before expiry; there is no rate limiting, no CSRF token, no HTTPS termination, and role checks are coarse. These are listed as known limitations in the README. |

### NFR-03 - Usability

| Field | Detail |
|-------|--------|
| **Requirement** | An analyst shall be able to complete the core workflows without training, and the interface shall communicate state clearly at all times. |
| **Design support** | Consistent severity colour language across badges, charts and borders; every asynchronous view has loading, empty and error states; destructive actions require confirmation; every action produces a toast; keyboard-visible focus rings; form errors appear inline next to the field and name the problem. |
| **Measurement** | Task-completion walkthrough, document 19. |

### NFR-04 - Reliability

| Field | Detail |
|-------|--------|
| **Requirement** | The system shall degrade gracefully rather than fail, and shall not lose or corrupt data on a partial failure. |
| **Design support** | The detection engine falls back to `hybrid-rules` mode when ML artefacts are missing or unloadable; one malformed CSV row does not abort an upload; every unhandled exception rolls back the session and returns a JSON envelope; batch analysis is a single transaction, so an upload is all-or-nothing; the frontend distinguishes "backend unreachable" from other errors and shows the exact command to start it. |
| **Measurement** | Fault-injection procedure, document 19. |

### NFR-05 - Maintainability

| Field | Detail |
|-------|--------|
| **Requirement** | The code shall be organised so that a change has one obvious home. |
| **Design support** | Strict layering (routes -> services -> models); one blueprint per feature area; business rules live in services, never in routes; a single API client module on the frontend; shared UI primitives instead of duplicated markup; the incident state machine and the severity bands each defined exactly once and consumed everywhere. |
| **Measurement** | Change-impact walkthrough, document 19. |

### NFR-06 - Scalability

| Field | Detail |
|-------|--------|
| **Requirement** | The design shall not prevent scaling beyond the prototype's data volumes. |
| **Design support** | All list endpoints paginate server-side; filtering and aggregation happen in SQL; the ORM abstracts the database so SQLite can be swapped for PostgreSQL by changing `DATABASE_URL` alone; the detection engine is stateless per call and safe to run behind multiple workers. |
| **Stated limits** | SQLite's single-writer model is the first real ceiling; the CSV path holds parsed rows in memory, which bounds uploads at the configured 5000 rows. |

### NFR-07 - Availability

| Field | Detail |
|-------|--------|
| **Requirement** | The system shall expose its own health, and a subsystem failure shall not take the whole console down. |
| **Design support** | Public `GET /api/health` liveness probe; authenticated `GET /api/system/status` with per-subsystem checks; the dashboard renders a health panel; the frontend keeps a cached session when the backend is merely unreachable and only signs the user out on a genuine 401. |
| **Stated limits** | Single-process development server with no clustering, no failover and no persistence guarantees beyond the SQLite file. |

---

## 5. Requirements traceability matrix

| Req | Use case | Design document | Implementation | Test |
|-----|----------|-----------------|----------------|------|
| FR-01 | UC-01 Login | 12 (Sequence 1) | `services/auth_service.py` | `test_auth.py` |
| FR-02 | UC-02 View Dashboard | 07 (DFD 1, P5) | `services/analytics_service.py` | `test_assets_dashboard.py` |
| FR-03 | UC-03 Monitor/Submit Events | 07 (DFD 1, P2) | `routes/events.py` | `test_events.py` |
| FR-04 | UC-04 Analyze Event | 08 (DFD 2), 12 (Sequence 2) | `ml/detector.py` | `test_detection_engine.py` |
| FR-05 | UC-06 Detect Threat | 08 (DFD 2) | `ml/rules.py`, `ml/anomaly.py` | `test_detection_engine.py` |
| FR-06 | UC-07 View/Triage Alerts | 12 (Sequence 5) | `services/alert_service.py` | `test_alerts_incidents.py` |
| FR-07 | UC-08/09 Investigate/Manage Incidents | 09 (State diagram), 12 (Sequence 6) | `services/incident_service.py` | `test_alerts_incidents.py` |
| FR-08 | UC-10 Manage Assets | 04 (ERD) | `routes/assets.py` | `test_assets_dashboard.py` |
| FR-09 | UC-11 View Threat Intelligence | 04 (ERD) | `routes/threats.py` | `test_assets_dashboard.py` |
| FR-10 | UC-05 Upload Logs | 12 (Sequence 3) | `utils/csv_parser.py` | `test_events.py` |
| FR-11 | UC-12 Generate Reports | 12 (Sequence 7) | `services/report_service.py` | `test_assets_dashboard.py` |
| FR-12 | UC-13 Review Audit Logs | 04 (ERD) | `services/audit_service.py` | `test_auth.py` |
| NFR-01 | - | 16 (Deployment) | indexes, SQL aggregation | Document 19 |
| NFR-02 | - | 15 (Component) | `utils/security.py`, `utils/validators.py` | `test_auth.py`, `test_events.py` |
| NFR-03 | - | 20, 21 (Storyboard, UI) | `components/ui.jsx` | Document 19 |
| NFR-04 | - | 15 (Component) | fallback mode, error handlers | `test_detection_engine.py` |
| NFR-05 | - | 14 (Package) | layered packages | Document 19 |
| NFR-06 | - | 16 (Deployment) | pagination, ORM | Document 19 |
| NFR-07 | - | 16 (Deployment) | `/api/health`, `/api/system/status` | `test_assets_dashboard.py` |
