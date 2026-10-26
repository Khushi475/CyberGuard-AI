# 07 - Data Flow Diagram - Level 1

**Project:** CyberGuard AI
**Lab experiment:** 4 - Requirement modelling using DFD

---

## 1. Purpose

Level 1 decomposes each Level 0 process from document 06 into its constituent
sub-processes. The two processes that carry the most logic - **2.0 Process
Security Events** and **4.0 Manage Incidents** - are shown in full detail.

---

## 2. Process 1.0 - Manage Authentication

```
   EE1/EE2
      |
      | credentials
      v
 +--------------------+   email/password   +-----------+
 |        1.1         |------------------->|    D1     |
 |  Validate          |<-------------------|  USER DB  |
 |  Credentials       |   stored hash      +-----------+
 +--------------------+
      |            |
      | valid      | invalid
      v            v
 +--------------------+   +--------------------+       +-----------+
 |        1.2         |   |        1.4         |------>|    D5     |
 |  Issue Session     |   |  Record Failed     |       | AUDIT DB  |
 |  Token             |   |  Attempt           |       +-----------+
 +--------------------+   +--------------------+
      |                          |
      | token + profile          | HTTP 401
      v                          v
   EE1/EE2                    EE1/EE2

 +--------------------+   token   +--------------------+
 |        1.3         |<----------| every protected    |
 |  Verify Token      |           | request            |
 |  (per request)     |---------->| validated identity |
 +--------------------+           +--------------------+
      |
      | expired / forged
      v
   HTTP 401

 +--------------------+  preferences, profile, password  +-----------+
 |        1.5         |<---------------------------------|   EE1     |
 |  Manage Profile    |--------------------------------->|    D1     |
 |  and Preferences   |                                  +-----------+
 +--------------------+
```

| Sub-process | Responsibility | Code |
|-------------|----------------|------|
| 1.1 Validate Credentials | Email format check, account lookup, PBKDF2 verification, active check | `auth_service.login` |
| 1.2 Issue Session Token | Sign `{uid, email, role}` with `SECRET_KEY`, set expiry | `utils/security.generate_token` |
| 1.3 Verify Token | Decode, check expiry and signature, load the user onto the request | `utils/security.token_required` |
| 1.4 Record Failed Attempt | Write a FAILURE audit entry, return a non-disclosing 401 | `auth_service.login` |
| 1.5 Manage Profile and Preferences | Update name/email/department, notification settings, sensitivity, theme, password | `auth_service.update_profile`, `update_preferences`, `change_password` |

---

## 3. Process 2.0 - Process Security Events (primary decomposition)

```
    EE1 (manual entry)                        EE3 (CSV file)
         |                                          |
         | event payload                            | multipart file
         v                                          v
 +----------------------+                 +----------------------------+
 |         2.1          |                 |            2.2             |
 |  Validate Event      |                 |  Parse and Validate        |
 |  Payload             |                 |  CSV File                  |
 |                      |                 |                            |
 | - IP format          |                 | - decode (UTF-8/latin-1)   |
 | - port range 0-65535 |                 | - sniff delimiter          |
 | - protocol allow-list|                 | - normalise header aliases |
 | - event type list    |                 | - check required column    |
 | - numeric bounds     |                 | - validate each row via 2.1|
 | - timestamp parse    |                 +----------------------------+
 +----------------------+                      |                |
         |                                     | valid rows     | rejected rows
         | validated event                     |                | + reasons
         |                                     |                v
         |          +--------------------------+              EE1/EE3
         |          |                                      (validation feedback)
         v          v
 +--------------------------------+
 |             2.3                |     IP lookup        +-----------+
 |  Analyse Event                 |--------------------->|    D6     |
 |  (Detection Engine)            |<---------------------| ASSET DB  |
 |                                |     matched asset    +-----------+
 |  See document 08 for the       |
 |  Level 2 decomposition         |
 +--------------------------------+
         |
         | verdict: classification, risk_score,
         | confidence, severity, reasons
         v
 +--------------------------------+   SecurityEvent +   +-----------+
 |             2.4                |   DetectionResult   |    D2     |
 |  Persist Event and             |------------------>  | EVENT DB  |
 |  Detection Result              |                     +-----------+
 +--------------------------------+
         |
         | is_threat?
         v
   +-----+------+
   | no         | yes
   |            v
   |   +--------------------------------+   Threat row   +-----------+
   |   |             2.5                |--------------->|    D3     |
   |   |  Create Threat Record          |                | THREAT DB |
   |   +--------------------------------+                +-----------+
   |            |
   |            | risk >= 26 (ALERT_RISK_THRESHOLD)
   |            v
   |   +--------------------------------+   Alert row    +-----------+
   |   |             2.6                |--------------->|    D3     |
   |   |  Raise Alert                   |                | THREAT DB |
   |   +--------------------------------+                +-----------+
   |            |
   |            | risk >= 76 (INCIDENT_RISK_THRESHOLD)
   |            v
   |   +--------------------------------+   Incident row +-----------+
   |   |             2.7                |--------------->|    D4     |
   |   |  Open Critical Incident        |                |INCIDENT DB|
   |   |  (status = NEW, alert linked)  |                +-----------+
   |   +--------------------------------+
   |            |
   v            v
 +--------------------------------+   risk_level,   +-----------+
 |             2.8                |   last_seen     |    D6     |
 |  Update Asset Risk Posture     |---------------->| ASSET DB  |
 +--------------------------------+                 +-----------+
         |
         v
 +--------------------------------+   audit entry   +-----------+
 |             2.9                |---------------->|    D5     |
 |  Write Audit Entry and         |                 | AUDIT DB  |
 |  Commit Transaction            |                 +-----------+
 +--------------------------------+
         |
         | verdict + created artefacts
         v
       EE1
```

### 3.1 Sub-process specification

| ID | Sub-process | Input | Processing | Output | Code |
|----|-------------|-------|------------|--------|------|
| 2.1 | Validate Event Payload | Raw JSON or a CSV row | Field-by-field validation; normalise to the canonical event dictionary; raise HTTP 422 naming the offending field | Validated event | `utils/validators.validate_event_payload` |
| 2.2 | Parse and Validate CSV | Uploaded file | Decode, sniff delimiter, map header aliases, enforce `source_ip`, delegate each row to 2.1, collect per-row errors | Valid rows + rejected rows | `utils/csv_parser.parse_csv` |
| 2.3 | Analyse Event | Validated event | Detection engine (decomposed in document 08) | Verdict | `ml/detector.ThreatDetector.detect` |
| 2.4 | Persist Event and Result | Event + verdict | Insert `SecurityEvent`, flush for its id, insert `DetectionResult`, mark processed | Stored rows | `detection_service.persist_analysis` |
| 2.5 | Create Threat Record | Verdict where `is_threat` | Build description, attach indicators and MITRE tactic | `Threat` row | `detection_service.persist_analysis` |
| 2.6 | Raise Alert | Threat with risk >= 26 | Generate `ALT-` code, copy severity/score/reasons, status NEW | `Alert` row | `detection_service.persist_analysis` |
| 2.7 | Open Critical Incident | Alert with risk >= 76 | Generate `INC-` code, set priority from severity, seed the history, link the alert | `Incident` row | `detection_service.persist_analysis` |
| 2.8 | Update Asset Risk | Verdict + matched asset | Raise `risk_score`/`risk_level` to the highest seen; refresh `last_seen` | Updated asset | `detection_service._update_asset_risk` |
| 2.9 | Write Audit and Commit | All of the above | Append the audit entry and commit everything in one transaction | Committed state | `audit_service.record` + `db.session.commit` |

### 3.2 Transaction boundary

Sub-processes 2.4 through 2.9 execute inside **one database transaction**. For a
CSV upload the loop over rows runs with `commit=False` and a single commit
happens at the end (`detection_service.analyze_batch`).

The consequence is important and intentional: an upload either lands completely
or not at all. There is no state in which some rows produced alerts and the rest
were lost. This is the mechanism behind the reliability claim in NFR-04.

---

## 4. Process 3.0 - Manage Alerts

```
      EE1
       |
       | filter criteria
       v
 +----------------------+   query    +-----------+
 |        3.1           |----------->|    D3     |
 |  Query Alert Queue   |<-----------| THREAT DB |
 |  (filter, search,    |   rows     +-----------+
 |   sort, paginate)    |
 +----------------------+
       |
       | paginated queue + filter metadata
       v
      EE1
       |
       | triage decision (action + note)
       v
 +----------------------+
 |        3.2           |
 |  Validate Alert      |--- illegal --> HTTP 409 CONFLICT
 |  State Transition    |
 +----------------------+
       | legal
       v
 +----------------------+   status, note,  +-----------+
 |        3.3           |   resolved_at    |    D3     |
 |  Apply Status Change |----------------->| THREAT DB |
 +----------------------+                  +-----------+
       |
       +---------------------------+
       |                           |
       v                           v
 +----------------------+   +-----------+
 |        3.4           |   |    D5     |
 |  Escalate to         |   | AUDIT DB  |
 |  Incident            |   +-----------+
 +----------------------+
       |
       | existing incident? return it : create new
       v
   Process 4.0
```

| Sub-process | Note |
|-------------|------|
| 3.1 Query Alert Queue | All filtering happens in SQL, never in the browser. `alert_service.build_query` |
| 3.2 Validate Transition | Checks `ALERT_STATUS_TRANSITIONS` before mutating anything |
| 3.3 Apply Status Change | Appends a timestamped, attributed note; stamps `resolved_at` for terminal states |
| 3.4 Escalate to Incident | **Idempotent**: if the alert already has an incident, that incident is returned rather than a duplicate created |

---

## 5. Process 4.0 - Manage Incidents

```
      EE1                                  Process 2.0 / 3.0
       |                                          |
       | manual creation                          | automatic creation
       v                                          v
 +--------------------------+            +--------------------------+
 |           4.1            |            |           4.2            |
 |  Create Incident         |            |  Auto-open Critical      |
 |  (validate title,        |            |  Incident                |
 |   severity, assignee)    |            |  (status = NEW)          |
 +--------------------------+            +--------------------------+
       |                                          |
       +--------------------+---------------------+
                            |
                            v  new incident row
                      +-----------+
                      |    D4     |
                      |INCIDENT DB|
                      +-----------+
                            ^
       EE1                  |
        |                   |
        | transition request|
        v                   |
 +--------------------------+
 |           4.3            |
 |  Validate Lifecycle      |--- illegal --> HTTP 409 with
 |  Transition              |                current state +
 |  (state machine guard)   |                allowed set
 +--------------------------+
        | legal
        v
 +--------------------------+   status, timestamps,   +-----------+
 |           4.4            |   history entry         |    D4     |
 |  Apply Transition        |------------------------>|INCIDENT DB|
 |                          |                         +-----------+
 | - CONTAINED -> stamp     |
 |   contained_at           |
 | - RESOLVED / FALSE_POS   |
 |   -> stamp resolved_at   |
 | - append history entry   |
 +--------------------------+
        |
        | terminal state?
        v
 +--------------------------+   close child alerts    +-----------+
 |           4.5            |------------------------>|    D3     |
 |  Cascade Alert Closure   |                         | THREAT DB |
 +--------------------------+                         +-----------+
        |
        v
 +--------------------------+   audit entry           +-----------+
 |           4.6            |------------------------>|    D5     |
 |  Assign Analyst /        |                         | AUDIT DB  |
 |  Write Audit             |                         +-----------+
 +--------------------------+
        |
        | incident + history + alerts + related events + legal transitions
        v
       EE1
```

| Sub-process | Note |
|-------------|------|
| 4.1 Create Incident | Validates title and severity; defaults the assignee to the acting user |
| 4.2 Auto-open Critical | Triggered by process 2.7 when risk >= 76 |
| 4.3 Validate Transition | Reads `INCIDENT_STATE_TRANSITIONS` - the single source of truth shared with document 09 |
| 4.4 Apply Transition | Appends `{from, to, actor, note, at}` to the history |
| 4.5 Cascade Alert Closure | Resolving an incident resolves its alerts; marking it a false positive marks them false positives |
| 4.6 Assign and Audit | Reassignment is also recorded in the history |

---

## 6. Process 5.0 - Generate Analytics

```
                            +-----------------------------+
   +-----------+            |            5.1              |
   |    D2     |----------->|  Aggregate Totals           |
   | EVENT DB  |            |  (events, threats, alerts,  |
   +-----------+            |   incidents, assets)        |
   +-----------+            +-----------------------------+
   |    D3     |----------->             |
   | THREAT DB |            +-----------------------------+
   +-----------+            |            5.2              |
   +-----------+            |  Build Chart Series         |
   |    D4     |----------->|  - threats over time        |
   |INCIDENT DB|            |  - severity distribution    |
   +-----------+            |  - category distribution    |
   +-----------+            |  - events by source         |
   |    D6     |----------->|  - detection trend          |
   | ASSET DB  |            |  - protocol distribution    |
   +-----------+            +-----------------------------+
   +-----------+                         |
   |    D7     |----------->+-----------------------------+
   | INTEL DB  |            |            5.3              |
   +-----------+            |  Derive Threat Level        |
                            |  (unresolved alerts, 24 h)  |
                            +-----------------------------+
                                         |
                            +-----------------------------+
                            |            5.4              |
                            |  Compute Detection Quality  |
                            |  (analyst triage -> model   |
                            |   hold-out -> mean          |
                            |   confidence, with the      |
                            |   source always stated)     |
                            +-----------------------------+
                                         |
                            +-----------------------------+
   +-----------+            |            5.5              |
   |    D5     |----------->|  Assemble Activity Feed     |
   | AUDIT DB  |            |  (merge alerts, incidents,  |
   +-----------+            |   audit; sort newest first) |
                            +-----------------------------+
                                         |
                            +-----------------------------+
                            |            5.6              |
                            |  Run System Health Check    |
                            +-----------------------------+
                                         |
                                         v
                                        EE1
                              dashboard statistics
```

**Process 5.4 deserves note.** It does not simply emit an accuracy number. It
selects a source in priority order and labels it:

1. If five or more alerts have been triaged -> **analyst-confirmed precision**
   (`resolved / (resolved + false_positive)`).
2. Otherwise, if a trained model exists -> **model hold-out accuracy**, marked as
   measured on synthetic data.
3. Otherwise -> **mean engine confidence**, marked as a fallback.

Every response carries `source`, `label` and `note`, so a number is never
presented without saying where it came from. This is a direct implementation of
the project rule against reporting unsupported figures.

---

## 7. Process 6.0 - Manage Assets and Intelligence

```
      EE2                                         EE1
       |                                           |
       | asset definition                          | indicator filter/status
       v                                           v
 +--------------------------+           +--------------------------+
 |           6.1            |           |           6.4            |
 |  Validate Asset Data     |           |  Query Indicator Feed    |
 |  (name, IP, uniqueness)  |           +--------------------------+
 +--------------------------+                      |
       |                                           v
       v                                    +-----------+
 +--------------------------+               |    D7     |
 |           6.2            |               | INTEL DB  |
 |  Persist Asset           |-------+       +-----------+
 +--------------------------+       |             |
       |                            v             v
       v                      +-----------+   +--------------------------+
 +--------------------------+ |    D6     |   |           6.5            |
 |           6.3            | | ASSET DB  |   |  Update Indicator Status |
 |  Detach Events on        | +-----------+   +--------------------------+
 |  Deletion (preserve      |
 |  security history)       |
 +--------------------------+
```

---

## 8. Process 7.0 - Generate Reports and Audit

```
      EE1
       |
       | period, type, title
       v
 +--------------------------+   aggregate queries   +-----------------+
 |           7.1            |---------------------->| D2, D3, D4, D6  |
 |  Aggregate Report        |<----------------------|                 |
 |  Figures                 |                       +-----------------+
 +--------------------------+
       |
       v
 +--------------------------+
 |           7.2            |
 |  Derive Recommendations  |   (conditional on the measured figures,
 |  from Measured Data      |    not a fixed list)
 +--------------------------+
       |
       v
 +--------------------------+   report row   +-----------+
 |           7.3            |--------------->|    D8     |
 |  Store Report Content    |                | REPORT DB |
 +--------------------------+                +-----------+
       |
       | format = pdf | csv | json
       v
 +--------------------------+
 |           7.4            |
 |  Render Export           |---- PDF (ReportLab) / CSV / JSON ----> EE1
 |                          |     (501 with a clear message if
 |                          |      ReportLab is unavailable)
 +--------------------------+
       |
       v
 +--------------------------+   audit entry  +-----------+
 |           7.5            |--------------->|    D5     |
 |  Record Audit Entry      |                | AUDIT DB  |
 +--------------------------+                +-----------+
       ^
       | audit entries from processes 1.0, 2.0, 3.0, 4.0, 6.0
       |
 +--------------------------+
 |           7.6            |
 |  Serve Audit Trail       |-----------------------------------> EE2
 +--------------------------+
```

---

## 9. Balancing check against Level 0

| Level 0 process | Level 1 sub-processes | Boundary flows preserved |
|-----------------|------------------------|--------------------------|
| 1.0 | 1.1 - 1.5 | F1, F2, F3, F4 |
| 2.0 | 2.1 - 2.9 | F5, F6, F7, F8, F9, F10 |
| 3.0 | 3.1 - 3.4 | F11, F12, F13, F14 |
| 4.0 | 4.1 - 4.6 | F15, F16, F17, F18 |
| 5.0 | 5.1 - 5.6 | F19, F20 |
| 6.0 | 6.1 - 6.5 | F21, F22, F23 |
| 7.0 | 7.1 - 7.6 | F24, F25, F26, F27 |

**Result: balanced.** Every Level 0 flow enters or leaves the corresponding
Level 1 diagram, and no sub-process introduces an unbalanced external flow.

Process 2.3 (Analyse Event) is decomposed one level further in document 08.
