# 06 - Data Flow Diagram - Level 0

**Project:** CyberGuard AI
**Lab experiment:** 4 - Requirement modelling using DFD

---

## 1. Purpose

Level 0 opens Process 0.0 from the context diagram (document 05) into its major
sub-processes and shows the data stores they read from and write to.

Numbering convention used throughout documents 06-08:

- **0.0** - the whole system (context, document 05)
- **1.0 ... 7.0** - Level 0 major processes (this document)
- **2.1, 2.2 ...** - Level 1 decomposition (document 07)
- **2.3.1, 2.3.2 ...** - Level 2 decomposition (document 08)

---

## 2. Processes at Level 0

| ID | Process | Responsibility | Implemented by |
|----|---------|----------------|----------------|
| 1.0 | Manage Authentication | Verify credentials, issue and validate tokens, manage profile and preferences | `services/auth_service.py`, `utils/security.py` |
| 2.0 | Process Security Events | Validate, store and analyse events from manual entry or CSV upload | `routes/events.py`, `services/detection_service.py`, `ml/` |
| 3.0 | Manage Alerts | Raise alerts from threats, filter the queue, apply triage decisions | `services/alert_service.py` |
| 4.0 | Manage Incidents | Open cases, drive the lifecycle state machine, assign analysts | `services/incident_service.py` |
| 5.0 | Generate Analytics | Aggregate the database into dashboard statistics and chart series | `services/analytics_service.py` |
| 6.0 | Manage Assets and Intelligence | Maintain the monitored inventory and the simulated indicator feed | `routes/assets.py`, `routes/threats.py` |
| 7.0 | Generate Reports and Audit | Build and export reports; record every state change | `services/report_service.py`, `services/audit_service.py` |

## 3. Data stores

| ID | Store | Physical tables |
|----|-------|-----------------|
| D1 | User Database | `users` |
| D2 | Security Event Database | `security_events`, `detection_results` |
| D3 | Threat Database | `threats`, `alerts` |
| D4 | Incident Database | `incidents` |
| D5 | Audit Database | `audit_logs` |
| D6 | Asset Database | `assets` |
| D7 | Intelligence Database | `threat_indicators` |
| D8 | Report Database | `reports` |

---

## 4. Level 0 DFD

```
  EE1 SECURITY ANALYST                                        EE2 SYSTEM ADMINISTRATOR
        |     ^                                                        |      ^
        |     |                                                        |      |
 credentials  | token                                    asset defs,   |      | inventory,
 event data   | verdict                                  config        |      | health, audit
 filters      | queue                                                  |      |
        |     |                                                        |      |
        v     |                                                        v      |
   +---------------------+                                    +---------------------------+
   |        1.0          |    user record    +---------+      |           6.0             |
   | MANAGE              |<----------------->|   D1    |      | MANAGE ASSETS AND         |
   | AUTHENTICATION      |                   |  USER   |      | INTELLIGENCE              |
   +---------------------+                   |   DB    |      +---------------------------+
        |     |                              +---------+            |          |
        |     | validated identity                                  |          |
        |     +------------------------------------+               v          v
        |                                          |        +---------+  +---------+
        | audit entry                              |        |   D6    |  |   D7    |
        v                                          |        | ASSET   |  | INTEL   |
   +---------+                                     |        |   DB    |  |   DB    |
   |   D5    |                                     |        +---------+  +---------+
   | AUDIT   |<------------------------+           |             ^
   |   DB    |                         |           |             | asset lookup
   +---------+                         |           |             | + risk update
        ^                              |           v             |
        |                        +-----------------------------------+
        |                        |              2.0                  |
        |   audit entry          |     PROCESS SECURITY EVENTS       |
        +------------------------|  (validate -> store -> analyse)   |
        |                        +-----------------------------------+
        |                              |          |            |
        |                  event +     |          | threat     | detection
        |                  verdict     |          | record     | statistics
        |                              v          v            |
        |                        +---------+  +---------+      |
        |                        |   D2    |  |   D3    |      |
        |                        | EVENT   |  | THREAT  |      |
        |                        |   DB    |  |   DB    |      |
        |                        +---------+  +---------+      |
        |                              ^          ^  ^         |
        |                              |          |  |         |
        |                              |          |  | alert   |
        |                              |          |  | record  |
        |                              |          |  |         |
        |                        +-----+----------+--+---+     |
        |                        |          3.0          |     |
        |   audit entry          |     MANAGE ALERTS     |     |
        +------------------------|  (filter, triage)     |     |
        |                        +-----------------------+     |
        |                              |          ^            |
        |                 escalation   |          | alert      |
        |                              v          | linkage    |
        |                        +-----------------------+     |
        |   audit entry          |          4.0          |     |
        +------------------------|    MANAGE INCIDENTS   |     |
        |                        |  (lifecycle machine)  |     |
        |                        +-----------------------+     |
        |                              |          ^            |
        |                              v          |            |
        |                        +---------+      |            |
        |                        |   D4    |------+            |
        |                        |INCIDENT |                   |
        |                        |   DB    |                   |
        |                        +---------+                   |
        |                              |                       |
        |                              | incident counts       |
        |                              v                       v
        |                        +-------------------------------------+
        |                        |                5.0                  |
        |                        |        GENERATE ANALYTICS           |-----> EE1
        |                        |  (aggregate D2,D3,D4,D6,D7 -> KPIs) | dashboard
        |                        +-------------------------------------+ statistics
        |                              |
        |                              | aggregated figures
        |                              v
        |                        +-------------------------------------+
        |   audit entry          |                7.0                  |
        +------------------------|   GENERATE REPORTS AND AUDIT        |-----> EE1/EE2
                                 +-------------------------------------+ report file,
                                       |              ^                  audit trail
                                       v              |
                                 +---------+     +---------+
                                 |   D8    |     |   D5    |
                                 | REPORT  |     | AUDIT   |
                                 |   DB    |     |   DB    |
                                 +---------+     +---------+
```

---

## 5. Data flow catalogue

| Flow | From | To | Data content |
|------|------|----|--------------|
| F1 | EE1/EE2 | 1.0 | Email, password |
| F2 | 1.0 | D1 | Credential lookup; `last_login` update |
| F3 | 1.0 | EE1/EE2 | Signed token, user profile |
| F4 | 1.0 | 2.0-7.0 | Validated identity for every protected request |
| F5 | EE1/EE3 | 2.0 | Event payload or CSV rows |
| F6 | 2.0 | D6 | Asset lookup by IP; asset risk-level update |
| F7 | 2.0 | D2 | `SecurityEvent` and `DetectionResult` rows |
| F8 | 2.0 | D3 | `Threat` row and `Alert` row when risk >= 26 |
| F9 | 2.0 | D4 | New `Incident` when risk >= 76 |
| F10 | 2.0 | EE1 | Classification, risk score, confidence, severity, reasons, recommended action |
| F11 | EE1 | 3.0 | Filter criteria and triage decisions |
| F12 | 3.0 | D3 | Alert queries and status updates |
| F13 | 3.0 | 4.0 | Escalation request (alert -> incident) |
| F14 | 3.0 | EE1 | Paginated alert queue |
| F15 | EE1 | 4.0 | Lifecycle transition request |
| F16 | 4.0 | D4 | Incident read, transition validation, history append |
| F17 | 4.0 | D3 | Alert closure when the parent incident closes |
| F18 | 4.0 | EE1 | Incident details plus the currently legal transitions |
| F19 | 5.0 | D2, D3, D4, D6, D7 | Aggregate queries (counts, group-by, averages) |
| F20 | 5.0 | EE1 | Dashboard totals, chart series, threat level, health |
| F21 | EE2 | 6.0 | Asset definitions and indicator status changes |
| F22 | 6.0 | D6, D7 | Asset and indicator persistence |
| F23 | 6.0 | EE2 | Inventory and intelligence feed |
| F24 | EE1/EE2 | 7.0 | Report request; audit query |
| F25 | 7.0 | D8 | Stored report content |
| F26 | 7.0 | D5 | Audit entries from every process |
| F27 | 7.0 | EE1/EE2 | Report file (PDF/CSV/JSON); audit trail |
| F28 | 1.0, 2.0, 3.0, 4.0, 6.0 | D5 | Audit entry written with each state change |

---

## 6. Balancing check against the context diagram

A DFD is only valid if the flows crossing the Level 0 boundary reconcile exactly
with those on the context diagram. The table below verifies this.

| Context flow (doc 05) | Appears at Level 0 as | Handled by |
|------------------------|------------------------|-----------|
| DF-I1 credentials | F1 | 1.0 |
| DF-I2 event data | F5 | 2.0 |
| DF-I3 CSV log file | F5 | 2.0 |
| DF-I4 query/filter criteria | F11 | 3.0, and equivalents into 4.0, 5.0, 6.0 |
| DF-I5 alert triage decision | F11 | 3.0 |
| DF-I6 incident action | F15 | 4.0 |
| DF-I7 report request | F24 | 7.0 |
| DF-I8 asset definition | F21 | 6.0 |
| DF-I9 configuration change | F1 path | 1.0 |
| DF-I10 audit query | F24 | 7.0 |
| DF-I11 indicator status change | F21 | 6.0 |
| DF-O1 token and profile | F3 | 1.0 |
| DF-O2 dashboard statistics | F20 | 5.0 |
| DF-O3 detection verdict | F10 | 2.0 |
| DF-O4 alert queue | F14 | 3.0 |
| DF-O5 incident details | F18 | 4.0 |
| DF-O6 log analysis summary | F10 | 2.0 |
| DF-O7 security report | F27 | 7.0 |
| DF-O8 threat intelligence | F23 | 6.0 |
| DF-O9 asset inventory | F23 | 6.0 |
| DF-O10 system health | F20 | 5.0 |
| DF-O11 audit trail | F27 | 7.0 |
| DF-O12 notifications | F14 | 3.0 |
| DF-O13 validation feedback | F10 | 2.0 |
| DF-O14 error responses | every process | error handler in `app/__init__.py` |

**Result: balanced.** Every context-level flow is accounted for, and Level 0
introduces no flow that crosses the system boundary without a context-level
counterpart.

---

## 7. Observations

- **Process 2.0 is the hub.** It writes to four of the eight stores (D2, D3, D4,
  D6) in one transaction. This is why the decomposition in documents 07 and 08
  concentrates on it.
- **Process 5.0 is read-only.** Analytics never writes. This keeps the dashboard
  side-effect free, so refreshing it repeatedly cannot alter the data it reports.
- **D5 (Audit) is written by five of the seven processes.** That breadth is what
  makes FR-12 meaningful: the trail is not a feature of one screen, it is a
  cross-cutting concern threaded through the service layer.
