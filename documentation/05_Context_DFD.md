# 05 - Context Flow Diagram (Functional Modelling)

**Project:** CyberGuard AI
**Lab experiment:** 4 - Requirement modelling using Context flow diagram

---

## 1. Purpose

The context diagram is the highest level of functional decomposition. It shows
CyberGuard AI as a **single process (Process 0)** and defines its boundary: who
interacts with it, and what data crosses that boundary in each direction.

Nothing inside the system is shown at this level - that decomposition begins in
document 06.

---

## 2. External entities

| ID | External entity | Type | Role |
|----|-----------------|------|------|
| EE1 | Security Analyst | Human | Submits events, uploads logs, triages alerts, investigates incidents, generates reports. |
| EE2 | System Administrator | Human | Manages assets and configuration, reviews the audit trail and system status. |
| EE3 | Log File Source | External data source | The CSV export a user supplies to the Log Analyzer. |

> **Note on the system boundary.** The Log File Source is drawn as an external
> entity rather than as an automated collector because CyberGuard AI never
> reaches out to collect telemetry. A human chooses a file and hands it in. This
> is a direct consequence of the defensive-only scope rule in document 03: the
> system has no outbound data-collection capability of any kind.

---

## 3. Context diagram (Level 0 / Process 0)

```
                              credentials, event data,
                              filter criteria, triage
                              decisions, report requests
        +------------------+  ------------------------------->  +------------------------+
        |                  |                                    |                        |
        |    EE1           |                                    |                        |
        | SECURITY ANALYST |  <-------------------------------  |                        |
        |                  |   session token, dashboard         |                        |
        +------------------+   statistics, detection verdicts,   |                        |
                               alert queue, incident details,    |                        |
                               reports, notifications            |                        |
                                                                 |                        |
                                                                 |                        |
                               asset definitions, configuration,  |          0.0          |
                               settings, audit queries            |                        |
        +----------------------+  ---------------------------->  |     CYBERGUARD AI      |
        |        EE2           |                                  |                        |
        | SYSTEM ADMINISTRATOR |                                  |   Intelligent Cyber    |
        |                      |  <----------------------------  |   Threat Detection     |
        +----------------------+   asset inventory, system        |       System           |
                                   health, audit trail,           |                        |
                                   model status                   |                        |
                                                                 |                        |
                                                                 |                        |
                               CSV log records                    |                        |
        +------------------+  ---------------------------------> |                        |
        |      EE3         |                                      |                        |
        | LOG FILE SOURCE  |  <---------------------------------  |                        |
        |                  |   validation feedback                |                        |
        +------------------+   (rejected rows + reasons)          +------------------------+
```

---

## 4. Data flows crossing the boundary

### 4.1 Inbound (into the system)

| ID | From | Data flow | Content | Entry point |
|----|------|-----------|---------|-------------|
| DF-I1 | EE1, EE2 | Login credentials | email, password, remember flag | `POST /api/auth/login` |
| DF-I2 | EE1 | Security event data | source/destination IP and port, protocol, event type, request count, failed logins, packets, bytes, duration, timestamp | `POST /api/events`, `POST /api/events/analyze` |
| DF-I3 | EE3 | CSV log file | multipart file of up to 5000 telemetry rows | `POST /api/events/upload` |
| DF-I4 | EE1 | Query and filter criteria | severity, status, threat type, date range, search text, page, sort | `GET /api/alerts`, `/api/incidents`, `/api/events`, ... |
| DF-I5 | EE1 | Alert triage decision | target status (investigate / resolve / false positive), analyst note | `PUT /api/alerts/<id>` |
| DF-I6 | EE1 | Incident action | target lifecycle state, note, resolution summary, assignee | `PUT /api/incidents/<id>` |
| DF-I7 | EE1 | Report request | period in days, report type, optional title, export format | `POST /api/reports/generate`, `GET /api/reports/<id>/download` |
| DF-I8 | EE2 | Asset definition | name, IP, type, OS, location, owner, criticality, status | `POST /api/assets`, `PUT /api/assets/<id>` |
| DF-I9 | EE1, EE2 | Configuration change | detection sensitivity, notification preferences, theme, profile, password | `PUT /api/auth/preferences`, `/api/auth/profile`, `/api/auth/password` |
| DF-I10 | EE2 | Audit query | action filter, row limit | `GET /api/audit-logs` |
| DF-I11 | EE1 | Indicator status change | ACTIVE / MONITORING / RETIRED | `PUT /api/threat-intelligence/<id>` |

### 4.2 Outbound (out of the system)

| ID | To | Data flow | Content | Source endpoint |
|----|----|-----------|---------|-----------------|
| DF-O1 | EE1, EE2 | Session token and profile | signed token, user profile with preferences | `POST /api/auth/login` |
| DF-O2 | EE1 | Dashboard statistics | totals, threat level, six chart series, detection quality, health, activity feed | `GET /api/dashboard/stats` |
| DF-O3 | EE1 | Detection verdict | classification, risk score, confidence, severity, reasons, recommended action, sub-scores | `POST /api/events/analyze` |
| DF-O4 | EE1 | Alert queue | paginated alerts with filter metadata | `GET /api/alerts` |
| DF-O5 | EE1 | Incident details | incident, status history, linked alerts, related events, legal transitions | `GET /api/incidents/<id>` |
| DF-O6 | EE1 | Log analysis summary | record counts by severity, category distribution, per-record results, rejected rows | `POST /api/events/upload` |
| DF-O7 | EE1 | Security report | report content, or a PDF / CSV / JSON file | `POST /api/reports/generate`, `GET /api/reports/<id>/download` |
| DF-O8 | EE1 | Threat intelligence | indicator feed plus an explicit "simulated" notice | `GET /api/threat-intelligence` |
| DF-O9 | EE2 | Asset inventory | assets with risk level and event counts | `GET /api/assets` |
| DF-O10 | EE2 | System health and status | subsystem checks, table counts, engine mode, thresholds | `GET /api/health`, `GET /api/system/status` |
| DF-O11 | EE2 | Audit trail | ordered audit entries | `GET /api/audit-logs` |
| DF-O12 | EE1 | Notifications | unacknowledged alert summaries in the top bar | `GET /api/alerts?status=NEW` |
| DF-O13 | EE3 | Validation feedback | rejected row numbers with the reason for each | `POST /api/events/upload` |
| DF-O14 | EE1, EE2 | Error responses | typed JSON error envelope with a human-readable message | all endpoints |

---

## 5. Data stores referenced by the system

The lab brief asks for the data stores to be named at context level. They are
listed here for completeness, but by convention they are drawn **inside** the
system from Level 0 onwards (document 06), because they are internal to the
boundary rather than external entities.

| Store | Logical name | Physical tables |
|-------|--------------|-----------------|
| D1 | User Database | `users` |
| D2 | Security Event Database | `security_events`, `detection_results`, `assets` |
| D3 | Threat Database | `threats`, `alerts`, `threat_indicators` |
| D4 | Incident Database | `incidents` |
| D5 | Audit Database | `audit_logs`, `reports` |

---

## 6. What the context diagram tells us about scope

Reading the boundary carefully gives three design conclusions that the rest of
the project depends on:

1. **There is no outbound arrow to any network, host or third-party service.**
   The system only ever replies to the people who call it. This is the diagram-
   level proof of the defensive-only scope: CyberGuard AI cannot scan, probe or
   attack anything, because it has no flow through which to do so.

2. **All telemetry is pushed in, never pulled.** DF-I2 and DF-I3 are the only
   ways an event enters the system, and both originate from a human action. The
   system therefore needs strong input validation (NFR-02) rather than collector
   authentication.

3. **The two human actors have overlapping but distinct flows.** The analyst's
   flows are operational (triage, investigate, report); the administrator's are
   configuration and oversight (assets, settings, audit, health). This split is
   what the use case model in document 10 formalises into actors and use cases.
