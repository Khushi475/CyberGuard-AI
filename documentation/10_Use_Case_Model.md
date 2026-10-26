# 10 - Use Case Model (Object-Oriented Design)

**Project:** CyberGuard AI
**Lab experiment:** 6 - OO design: Use case model

---

## 1. Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Security Analyst** | Primary, human | Operates the console day to day: analyses events, uploads logs, triages alerts, investigates incidents, generates reports. |
| **System Administrator** | Primary, human | Specialises the Analyst. Adds asset management, configuration and audit review. |
| **Detection Engine (System)** | Secondary, internal | Autonomous actor invoked by event submission. Classifies events, raises alerts, opens critical incidents and maintains asset risk. |

**Generalisation:** `System Administrator --|> Security Analyst`. An
administrator can perform every analyst use case plus the administrative ones.

---

## 2. Use Case Diagram

```
                             CYBERGUARD AI SYSTEM BOUNDARY
   +---------------------------------------------------------------------------+
   |                                                                           |
   |     +-------------------+                                                 |
   |     |  UC-01 Login      |<-------------------------+                      |
   |     +-------------------+                          |                      |
   |                                                    |                      |
   |     +-------------------+       <<include>>        |                      |
   |     | UC-02 View        |- - - - - - - - - - - ->  |                      |
   |     |      Dashboard    |         UC-01            |                      |
   |     +-------------------+                          |                      |
   |              |                                     |                      |
   |              | <<extend>>                          |                      |
   |              v                                     |                      |
   |     +-------------------+                          |                      |
   |     | UC-14 View        |                          |                      |
   |     |   System Health   |                          |                      |
   |     +-------------------+                          |                      |
   |                                                    |                      |
   |     +-------------------+                          |          +-----------+
   |     | UC-03 Monitor /   |                          |          |           |
   |     |   Submit Events   |                          +----------|  SECURITY |
   |     +-------------------+                          |          |  ANALYST  |
   |              |                                     |          |           |
   |              | <<include>>                         |          +-----------+
   |              v                                     |               ^
   |     +-------------------+                          |               |
   |     | UC-04 Analyze     |                          |               | generalises
   |     |      Event        |                          |               |
   |     +-------------------+                          |          +-----------+
   |              |                                     |          |  SYSTEM   |
   |              | <<include>>                         +----------| ADMINIS-  |
   |              v                                     |          |  TRATOR   |
   |     +-------------------+                          |          +-----------+
   |     | UC-06 Detect      |<---------------------+   |               |
   |     |      Threat       |                      |   |               |
   |     +-------------------+                      |   |               |
   |        |             |                         |   |               |
   |        | <<extend>>  | <<extend>>              |   |               |
   |        v             v                         |   |               |
   | +-------------+  +--------------+              |   |               |
   | | UC-06a      |  | UC-06b       |              |   |               |
   | | Raise Alert |  | Open Critical|              |   |               |
   | | (risk>=26)  |  | Incident     |              |   |               |
   | +-------------+  | (risk>=76)   |              |   |               |
   |                  +--------------+              |   |               |
   |                                                |   |               |
   |     +-------------------+   <<include>>        |   |               |
   |     | UC-05 Upload      |- - - - - - - - - - ->+   |               |
   |     |      Logs         |      UC-04               |               |
   |     +-------------------+                          |               |
   |                                                    |               |
   |     +-------------------+                          |               |
   |     | UC-07 View /      |                          |               |
   |     |   Triage Alerts   |<-------------------------+               |
   |     +-------------------+                          |               |
   |              |                                     |               |
   |              | <<extend>>                          |               |
   |              v                                     |               |
   |     +-------------------+                          |               |
   |     | UC-08 Investigate |<-------------------------+               |
   |     |      Incident     |                          |               |
   |     +-------------------+                          |               |
   |              |                                     |               |
   |              | <<include>>                         |               |
   |              v                                     |               |
   |     +-------------------+                          |               |
   |     | UC-09 Manage      |<-------------------------+               |
   |     |      Incidents    |                          |               |
   |     +-------------------+                          |               |
   |                                                    |               |
   |     +-------------------+                          |               |
   |     | UC-11 View Threat |<-------------------------+               |
   |     |   Intelligence    |                          |               |
   |     +-------------------+                          |               |
   |                                                    |               |
   |     +-------------------+                          |               |
   |     | UC-12 Generate    |<-------------------------+               |
   |     |      Reports      |                                          |
   |     +-------------------+                                          |
   |                                                                    |
   |     +-------------------+                                          |
   |     | UC-10 Manage      |<-----------------------------------------+
   |     |      Assets       |                                          |
   |     +-------------------+                                          |
   |                                                                    |
   |     +-------------------+                                          |
   |     | UC-13 Review      |<-----------------------------------------+
   |     |    Audit Logs     |                                          |
   |     +-------------------+                                          |
   |                                                                    |
   |     +-------------------+                                          |
   |     | UC-15 Configure   |<-----------------------------------------+
   |     | Detection Settings|                                          |
   |     +-------------------+                                          |
   |                                                                    |
   |                    +--------------------+                          |
   |                    |  UC-06 Detect      |                          |
   |                    |       Threat       |<------------+            |
   |                    +--------------------+             |            |
   |                    +--------------------+             |            |
   |                    | UC-16 Maintain     |<------------+            |
   |                    |    Asset Risk      |             |            |
   |                    +--------------------+             |            |
   |                    +--------------------+             |            |
   |                    | UC-17 Write Audit  |<------------+            |
   |                    |        Entry       |             |            |
   |                    +--------------------+             |            |
   +-------------------------------------------------------|------------+
                                                           |
                                                  +--------------------+
                                                  |  DETECTION ENGINE  |
                                                  |     (System)       |
                                                  +--------------------+
```

---

## 3. Use case catalogue

| ID | Use case | Primary actor | Requirement | API entry point |
|----|----------|---------------|-------------|-----------------|
| UC-01 | Login | Analyst, Administrator | FR-01 | `POST /api/auth/login` |
| UC-02 | View Dashboard | Analyst | FR-02 | `GET /api/dashboard/stats` |
| UC-03 | Monitor / Submit Events | Analyst | FR-03 | `GET /api/events`, `POST /api/events` |
| UC-04 | Analyze Event | Analyst | FR-04 | `POST /api/events/analyze` |
| UC-05 | Upload Logs | Analyst | FR-10 | `POST /api/events/upload` |
| UC-06 | Detect Threat | Detection Engine | FR-05 | internal (`ThreatDetector.detect`) |
| UC-06a | Raise Alert | Detection Engine | FR-05, FR-06 | internal |
| UC-06b | Open Critical Incident | Detection Engine | FR-05, FR-07 | internal |
| UC-07 | View / Triage Alerts | Analyst | FR-06 | `GET /api/alerts`, `PUT /api/alerts/<id>` |
| UC-08 | Investigate Incident | Analyst | FR-07 | `GET /api/incidents/<id>` |
| UC-09 | Manage Incidents | Analyst | FR-07 | `POST`/`PUT /api/incidents` |
| UC-10 | Manage Assets | Administrator | FR-08 | `POST`/`PUT`/`DELETE /api/assets` |
| UC-11 | View Threat Intelligence | Analyst | FR-09 | `GET /api/threat-intelligence` |
| UC-12 | Generate Reports | Analyst | FR-11 | `POST /api/reports/generate` |
| UC-13 | Review Audit Logs | Administrator | FR-12 | `GET /api/audit-logs` |
| UC-14 | View System Health | Administrator | NFR-07 | `GET /api/system/status` |
| UC-15 | Configure Detection Settings | Administrator | FR-05 | `PUT /api/auth/preferences` |
| UC-16 | Maintain Asset Risk | Detection Engine | FR-08 | internal |
| UC-17 | Write Audit Entry | Detection Engine | FR-12 | internal |

### 3.1 Relationships

| Relationship | Meaning |
|--------------|---------|
| UC-02..UC-15 `<<include>>` UC-01 | Every protected use case requires authentication. |
| UC-03 `<<include>>` UC-04 | Submitting an event always analyses it. |
| UC-04 `<<include>>` UC-06 | Analysis always invokes the detection engine. |
| UC-05 `<<include>>` UC-04 | Every valid CSV row goes through the same analysis path. |
| UC-06 `<<extend>>` UC-06a | An alert is raised **only when** risk >= 26. |
| UC-06 `<<extend>>` UC-06b | An incident opens **only when** risk >= 76. |
| UC-07 `<<extend>>` UC-08 | An analyst may escalate an alert into an investigation. |
| UC-08 `<<include>>` UC-09 | Investigating uses the lifecycle management operations. |
| UC-02 `<<extend>>` UC-14 | Health details are an optional expansion of the dashboard. |

---

## 4. Detailed use case specifications

### UC-01 - Login

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst, System Administrator |
| **Goal** | Obtain an authenticated session. |
| **Preconditions** | The user has an active account; the backend is reachable. |
| **Postconditions** | A signed token is issued and the attempt is audited. |
| **Trigger** | The user submits the sign-in form. |

**Main success scenario**

1. The user opens the login page.
2. The user enters an email address and a password.
3. The system validates the email format on the client, then on the server.
4. The system looks up the account by email.
5. The system verifies the password against the stored PBKDF2 hash.
6. The system confirms the account is active.
7. The system records `LOGIN_SUCCESS` in the audit trail and updates `last_login`.
8. The system issues a signed, expiring token and returns the user profile.
9. The client stores the token and navigates to the dashboard.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 3a | Email is malformed | HTTP 422 naming the `email` field; the form highlights it inline. |
| 4a | No such account | HTTP 401 "Invalid email address or password." - identical to 5a, so account existence is not disclosed. `LOGIN_FAILED` is audited. |
| 5a | Password is wrong | HTTP 401 with the same message; `LOGIN_FAILED` audited. |
| 6a | Account is deactivated | HTTP 401 `ACCOUNT_DISABLED`. |
| 8a | Backend unreachable | The client shows "Cannot reach the CyberGuard AI backend" with the exact start command. |

---

### UC-04 - Analyze Event

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst (primary), Detection Engine (secondary) |
| **Goal** | Obtain an explainable verdict on a described security event. |
| **Preconditions** | The analyst is authenticated. |
| **Postconditions** | The event, its verdict and any alert or incident are persisted (unless a dry run was requested). |
| **Trigger** | The analyst presses "Analyze Threat". |

**Main success scenario**

1. The analyst fills in the event form, or loads a sample scenario.
2. The client validates the fields and submits them.
3. The system validates every field server-side.
4. The system resolves the owning asset by matching the endpoint IPs.
5. The system stores the `SecurityEvent`.
6. The system invokes the Detection Engine (UC-06).
7. The system stores the `DetectionResult`.
8. **If the verdict is a threat**, the system stores a `Threat` (UC-06a path).
9. **If risk >= 26**, the system raises an `Alert`.
10. **If risk >= 76**, the system opens an `Incident` and links the alert.
11. The system updates the asset's risk posture (UC-16).
12. The system writes an audit entry and commits the whole transaction.
13. The system returns the verdict with reasons, sub-scores and recommended action.
14. The client renders the score ring, the reasons and any created artefacts.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 3a | A field is invalid | HTTP 422 naming the field; the page highlights it and lists every problem. |
| 4a | No asset matches | The event is stored with `asset_id = NULL`; analysis proceeds normally. |
| 6a | ML artefacts are missing | The engine runs in `hybrid-rules` mode; the response reports `model_used` so the analyst knows. |
| 6b | An ML model fails to load | The exception is caught, the engine falls back to rules, and `load_error` is exposed on the status endpoint. |
| 9a | The analyst requested `persist=false` | Steps 5, 7-12 are skipped; the verdict is returned with `persisted: false`. |
| 12a | Any step raises | The whole transaction rolls back; nothing partial is stored. |

---

### UC-05 - Upload Logs

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst |
| **Goal** | Analyse many events at once from a CSV export. |
| **Preconditions** | Authenticated; a CSV file is available. |
| **Postconditions** | Every valid row is stored and analysed; rejected rows are reported. |

**Main success scenario**

1. The analyst drags a CSV file onto the drop zone, or browses for it.
2. The client checks the extension and the size, then uploads it.
3. The system guards the upload (file part, extension, 8 MB ceiling).
4. The system decodes the bytes (UTF-8 with BOM tolerance, latin-1 fallback).
5. The system sniffs the delimiter and normalises the header aliases.
6. The system confirms `source_ip` is present.
7. For each data row, the system validates it and either queues it or records the rejection reason - **one bad row never aborts the upload**.
8. The system analyses every valid row through UC-04's engine path.
9. The system commits all rows in a single transaction.
10. The system returns counts by severity, the category and top-source distributions, the per-record results and the rejected rows.
11. The client renders the summary, the charts and a filterable results table.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 3a | Wrong extension | HTTP 422 "Only .csv, .txt or .log files are accepted." |
| 3b | Over 8 MB | HTTP 413 naming the limit. |
| 4a | File is empty | HTTP 422 "The uploaded file is empty." |
| 4b | Undecodable bytes | HTTP 422 asking for a UTF-8 CSV. |
| 6a | `source_ip` column missing | HTTP 422 naming the required column and listing the columns actually found. |
| 7a | Every row invalid | HTTP 422 with the first 20 row errors. |
| 7b | Over 5000 rows | The excess is skipped and reported as a row error. |
| 9a | Commit fails | The whole upload rolls back; the analyst retries. |

---

### UC-07 - View / Triage Alerts

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst |
| **Goal** | Work through the alert queue and record a decision on each. |
| **Postconditions** | Alert statuses updated; every change audited. |

**Main success scenario**

1. The analyst opens the Alerts page.
2. The system returns a paginated queue with filter metadata.
3. The analyst narrows the queue by severity, status, threat type, date or search text.
4. The analyst opens an alert to read its reasons, telemetry and recommended action.
5. The analyst chooses Investigate, Resolve or False Positive, optionally adding a note.
6. The system validates the transition against the alert state machine.
7. The system applies the change, stamps `resolved_at` for terminal states, appends the attributed note and writes an audit entry.
8. The queue refreshes.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 5a | The analyst escalates instead | An incident is opened (or the existing linked one returned) and the analyst is taken to it. |
| 6a | The transition is illegal | HTTP 409 stating the current status. |
| 6b | The status value is unknown | HTTP 422 listing the valid statuses. |
| 7a | Resolve or False Positive chosen | The decision feeds the detection-precision figure on the dashboard. |

---

### UC-09 - Manage Incidents

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst |
| **Goal** | Drive an investigation through its lifecycle to a recorded outcome. |
| **Postconditions** | The incident reaches a terminal state; its alerts are closed with it; the history is complete. |

**Main success scenario**

1. The analyst opens an incident.
2. The system returns the incident, its status history, linked alerts, related events and **the transitions that are currently legal**.
3. The UI renders a button only for each legal transition.
4. The analyst selects a transition and adds a note.
5. The system re-validates the transition server-side.
6. The system applies it, stamps the relevant timestamp and appends `{from, to, actor, note, at}` to the history.
7. **If the state is terminal**, the system closes every alert linked to the incident.
8. The system writes an audit entry and commits.
9. The page refreshes, showing the new position on the lifecycle tracker.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 5a | The transition is illegal | HTTP 409 with `current`, `requested` and the `allowed` set. |
| 4a | The analyst reassigns instead | The assignee changes and the reassignment is recorded in both the history and the audit trail. |
| 6a | Reopening a closed incident | `resolved_at` is cleared and the incident returns to INVESTIGATING. |

---

### UC-12 - Generate Reports

| Field | Detail |
|-------|--------|
| **Actors** | Security Analyst, System Administrator |
| **Goal** | Produce a shareable security summary for a chosen period. |
| **Postconditions** | The report is stored and can be re-downloaded in three formats. |

**Main success scenario**

1. The analyst chooses a period, a report type and an optional title.
2. The system aggregates the period's figures from the live database.
3. The system derives recommendations **from those measured figures**.
4. The system stores the report content as structured JSON with an `RPT-` code.
5. The system writes an audit entry.
6. The analyst downloads the report as PDF, CSV or JSON.
7. The download is audited.

**Extensions**

| # | Condition | System response |
|---|-----------|-----------------|
| 1a | Period outside 1-365 | HTTP 422. |
| 1b | Unknown report type | HTTP 422 listing the valid types. |
| 6a | ReportLab is not installed | HTTP 501 with a clear message; CSV and JSON still work. |
| 2a | The period contains no data | The report is still generated, and the recommendations say that no elevated activity was recorded. |

---

## 5. Use case to implementation map

| Use case | Backend | Frontend |
|----------|---------|----------|
| UC-01 | `routes/auth.py`, `services/auth_service.py` | `pages/Login.jsx`, `context/AuthContext.jsx` |
| UC-02 | `routes/dashboard.py`, `services/analytics_service.py` | `pages/Dashboard.jsx` |
| UC-03, UC-04 | `routes/events.py`, `services/detection_service.py` | `pages/ThreatDetection.jsx` |
| UC-05 | `routes/events.py::upload_events`, `utils/csv_parser.py` | `pages/LogAnalyzer.jsx` |
| UC-06, 06a, 06b, 16 | `ml/detector.py`, `services/detection_service.py` | (no direct UI - internal actor) |
| UC-07 | `routes/alerts.py`, `services/alert_service.py` | `pages/Alerts.jsx` |
| UC-08, UC-09 | `routes/incidents.py`, `services/incident_service.py` | `pages/Incidents.jsx`, `pages/IncidentDetails.jsx` |
| UC-10 | `routes/assets.py` | `pages/Assets.jsx` |
| UC-11 | `routes/threats.py` | `pages/ThreatIntelligence.jsx` |
| UC-12 | `routes/reports.py`, `services/report_service.py` | `pages/Reports.jsx` |
| UC-13, UC-17 | `routes/system.py`, `services/audit_service.py` | `pages/Settings.jsx` (Audit tab) |
| UC-14 | `routes/system.py::system_status` | `pages/Settings.jsx` (System tab), Dashboard health panel |
| UC-15 | `routes/auth.py::update_preferences` | `pages/Settings.jsx` (Detection tab) |
