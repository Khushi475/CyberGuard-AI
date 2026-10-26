# 13 - Communication / Collaboration Diagrams (Interaction Modelling)

**Project:** CyberGuard AI
**Lab experiment:** 7 - OO design: Interaction models

---

## 1. Sequence vs. communication diagrams

Both describe the same interactions. A sequence diagram emphasises **time**
(what happens in what order); a communication diagram emphasises **structure**
(which objects are linked to which, and what messages travel over those links).

The diagrams below show the same collaborations as document 12, drawn
structurally. Message numbering uses the Decimal (Dewey) scheme: `1`, `1.1`,
`1.1.1` denote nesting depth.

---

## 2. Collaboration 1 - User Login

```
                          1: login(email, password)
        +--------+  ------------------------------------>  +-------------+
        | :Analyst|                                        | :Login.jsx  |
        +--------+  <------------------------------------  +-------------+
                          9: render dashboard                     |
                                                                  | 2: login()
                                                                  v
                                                          +----------------+
                                                          | :AuthContext   |
                                                          +----------------+
                                                                  |
                                                                  | 3: post(/auth/login)
                                                                  v
                                                          +----------------+
                                                          |    :api.js     |
                                                          +----------------+
                                                                  |
                                                                  | 4: POST
                                                                  v
                                                          +----------------+
                                                          |   :auth.py     |
                                                          |   (blueprint)  |
                                                          +----------------+
                                                                  |
                                                                  | 5: login(email, pw)
                                                                  v
                                                          +----------------+
       +----------------+   5.1: query(email)             | :auth_service  |
       |    :User       | <------------------------------ +----------------+
       |   (model)      |                                   |     |      |
       +----------------+   5.2: check_password(pw)         |     |      |
              ^         <----------------------------------+     |      |
              |                                                  |      |
              | 5.3: last_login = now                            |      |
              +--------------------------------------------------+      |
                                                                 |      |
       +----------------+   5.4: record(LOGIN_SUCCESS)           |      |
       |  :audit_service| <--------------------------------------+      |
       +----------------+                                               |
              |                                                         |
              | 5.4.1: INSERT AuditLog                                  |
              v                                                         |
       +----------------+                                               |
       |   :AuditLog    |                                               |
       +----------------+                                               |
                                                                        |
       +----------------+   5.5: generate_token(user)                   |
       | :security.py   | <---------------------------------------------+
       +----------------+                                               |
              |                                                         |
              | 5.5.1: URLSafeTimedSerializer.dumps()                   |
              |         signed with SECRET_KEY + expiry                 |
              |                                                         |
              +---------- 6: {token, user} ---------------------------->+
                                                                        |
                                        7: 200 {token, user}            |
                          +---------------------------------------------+
                          |
                          | 8: tokenStore.set() / userStore.set()
                          v
                  +----------------+
                  |  localStorage  |
                  +----------------+
```

**Links exercised:** Analyst -> Login.jsx -> AuthContext -> api.js -> auth.py ->
auth_service -> {User, audit_service, security}.

---

## 3. Collaboration 2 - Security Event Analysis (central collaboration)

```
                         1: submit event form
        +---------+  ----------------------------->  +---------------------+
        | :Analyst|                                  | :ThreatDetection.jsx|
        +---------+  <-----------------------------  +---------------------+
                       14: render verdict                     |
                                                              | 2: analyzeEvent(payload)
                                                              v
                                                      +---------------+
                                                      |    :api.js    |
                                                      +---------------+
                                                              |
                                                              | 3: POST /events/analyze
                                                              v
                                                      +---------------+
                     4: validate_event_payload()      |  :events.py   |
     +-----------------+ <-------------------------   |  (blueprint)  |
     |  :validators    |                              +---------------+
     +-----------------+  --- 4.1: cleaned event --->        |
                                                              | 5: persist_analysis(cleaned, user)
                                                              v
                                                   +------------------------+
                                                   |  :detection_service    |
                                                   +------------------------+
                                                     |   |   |   |   |    |
            6: resolve_asset(src, dst)               |   |   |   |   |    |
     +-----------+  <--------------------------------+   |   |   |   |    |
     |  :Asset   |                                       |   |   |   |    |
     +-----------+  --- 6.1: matched asset or None --->  |   |   |   |    |
          ^                                              |   |   |   |    |
          | 12: risk_level = max(current, new)           |   |   |   |    |
          +----------------------------------------------+   |   |   |    |
                                                             |   |   |    |
            7: INSERT + flush()                              |   |   |    |
     +-----------------+  <-------------------------------- +   |   |    |
     | :SecurityEvent  |                                         |   |    |
     +-----------------+                                         |   |    |
                                                                 |   |    |
            8: detect(feature_payload)                           |   |    |
     +-----------------+  <----------------------------------- +-+   |    |
     | :ThreatDetector |                                             |    |
     +-----------------+                                             |    |
        |    |     |    \                                            |    |
        |    |     |     \  8.4: _ml_score(features)                 |    |
        |    |     |      +---------------------+                    |    |
        |    |     |                            v                    |    |
        |    |     |                   +------------------+          |    |
        |    |     |                   | :RandomForest    |          |    |
        |    |     |                   | :IsolationForest |          |    |
        |    |     |                   |  (optional)      |          |    |
        |    |     |                   +------------------+          |    |
        |    |     |                                                 |    |
        |    |     | 8.3: score(features)                            |    |
        |    |     +----------------------+                          |    |
        |    |                            v                          |    |
        |    |                  +----------------------+             |    |
        |    |                  | :StatisticalBaseline |             |    |
        |    |                  +----------------------+             |    |
        |    |                                                       |    |
        |    | 8.2: evaluate_rules(features, event)                  |    |
        |    +-------------------+                                   |    |
        |                        v                                   |    |
        |               +------------------+                         |    |
        |               |  :rules (module) |                         |    |
        |               +------------------+                         |    |
        |                  | R1..R7 each returning (score, reasons)  |    |
        |                                                            |    |
        | 8.1: extract_features(event)                               |    |
        +-------------------+                                        |    |
                            v                                        |    |
                  +---------------------+                            |    |
                  | :features (module)  |                            |    |
                  +---------------------+                            |    |
                                                                     |    |
            8.5: verdict {classification, risk, severity, reasons}   |    |
            ------------------------------------------------------> +-+   |
                                                                     |    |
            9: INSERT DetectionResult                                |    |
     +---------------------+  <-------------------------------------+    |
     | :DetectionResult    |                                             |
     +---------------------+                                             |
                                                                         |
            10: [is_threat] INSERT Threat                                |
     +-----------+  <----------------------------------------------------+
     |  :Threat  |                                                       |
     +-----------+                                                       |
                                                                         |
            11: [risk >= 26] INSERT Alert                                |
     +-----------+  <----------------------------------------------------+
     |  :Alert   |                                                       |
     +-----------+                                                       |
          ^                                                              |
          | 11.2: alert.incident_id = incident.id                        |
          |                                                              |
     +-----------+  11.1: [risk >= 76] INSERT Incident                   |
     | :Incident |  <---------------------------------------------------+
     +-----------+                                                       |
                                                                         |
            13: record(EVENT_ANALYSED) + COMMIT                          |
     +-----------------+  <--------------------------------------------- +
     | :audit_service  |
     +-----------------+
```

### 3.1 Message table

| # | Message | Sender | Receiver | Argument / return |
|---|---------|--------|----------|-------------------|
| 1 | submit form | Analyst | ThreatDetection.jsx | event fields |
| 2 | analyzeEvent(payload) | ThreatDetection.jsx | api.js | payload, persist flag |
| 3 | POST /events/analyze | api.js | events.py | JSON + Bearer token |
| 4 | validate_event_payload() | events.py | validators | raw payload -> cleaned |
| 5 | persist_analysis() | events.py | detection_service | cleaned, user, channel, sensitivity |
| 6 | resolve_asset() | detection_service | Asset | source/destination IP -> Asset |
| 7 | INSERT + flush | detection_service | SecurityEvent | new row, id assigned |
| 8 | detect() | detection_service | ThreatDetector | feature payload -> verdict |
| 8.1 | extract_features() | ThreatDetector | features | event -> 18 features |
| 8.2 | evaluate_rules() | ThreatDetector | rules | features -> category, score, reasons |
| 8.3 | score() | ThreatDetector | StatisticalBaseline | features -> anomaly score |
| 8.4 | _ml_score() | ThreatDetector | sklearn models | vector -> ML score (skipped if absent) |
| 8.5 | return verdict | ThreatDetector | detection_service | full verdict dict |
| 9 | INSERT | detection_service | DetectionResult | verdict persisted |
| 10 | INSERT | detection_service | Threat | only when `is_threat` |
| 11 | INSERT | detection_service | Alert | only when risk >= 26 |
| 11.1 | INSERT | detection_service | Incident | only when risk >= 76 |
| 11.2 | link | detection_service | Alert | `incident_id` set |
| 12 | update risk | detection_service | Asset | risk level raised to the maximum seen |
| 13 | record + commit | detection_service | audit_service | one transaction |
| 14 | render | ThreatDetection.jsx | Analyst | score ring, reasons, actions |

---

## 4. Collaboration 3 - CSV Log Upload

```
                    1: drop / select file
     +---------+  ------------------------>  +------------------+
     | :Analyst|                             | :LogAnalyzer.jsx |
     +---------+  <------------------------  +------------------+
                    11: render summary              |
                                                    | 2: uploadLogs(file, onProgress)
                                                    v
                                            +---------------+
                                            |    :api.js    |
                                            +---------------+
                                                    | 3: POST multipart
                                                    v
                                            +---------------+
        4: validate_upload(file)            |  :events.py   |
    +----------------+ <------------------- +---------------+
    |  :csv_parser   |                              |
    +----------------+                              |
        |   |   |                                   |
        |   |   | 4.1: decode_file()                |
        |   |   |      utf-8-sig -> utf-8 -> latin-1|
        |   |   |                                   |
        |   |   | 4.2: sniff dialect + normalise    |
        |   |   |      header aliases               |
        |   |   |                                   |
        |   |   | 4.3: require source_ip column     |
        |   |   |                                   |
        |   | 4.4: per row -> validate_event_payload()
        |   +---------------------+                 |
        |                         v                 |
        |                +-----------------+        |
        |                |  :validators    |        |
        |                +-----------------+        |
        |                                           |
        +--- 5: (valid_rows, row_errors) ---------->+
                                                    |
                                                    | 6: analyze_batch(valid_rows, user, "csv")
                                                    v
                                         +------------------------+
                                         |  :detection_service    |
                                         +------------------------+
                                            |        |         |
                     6.1: loop persist_analysis(row, commit=False)
                                            |        |         |
                                            v        v         v
                                  +---------------+  +-------+ +--------+
                                  |:ThreatDetector|  |:Alert | |:Threat |
                                  +---------------+  +-------+ +--------+
                                            |
                     6.2: tally severity counters, categories, top sources
                                            |
                     7: record(LOG_UPLOAD_ANALYSED)
                                            v
                                  +-----------------+
                                  | :audit_service  |
                                  +-----------------+
                                            |
                     8: COMMIT  <-- ONE transaction for the whole file
                                            v
                                     +-------------+
                                     |  :Database  |
                                     +-------------+
                                            |
                     9: summary {counts, categories, records, row_errors}
                                            |
                    10: 201 -------------->  back through api.js
```

**Key structural point:** `csv_parser` and `validators` collaborate per row, but
`detection_service` holds the transaction. This is why one malformed row can be
reported without losing the rest of the file.

---

## 5. Collaboration 4 - Alert Triage and Escalation

```
                   1: choose action + note
     +---------+  -------------------------->  +---------------+
     | :Analyst|                               | :Alerts.jsx   |
     +---------+  <--------------------------  +---------------+
                   9: refreshed queue + toast         |
                                                      | 2: updateAlert(id, {action, note})
                                                      v
                                              +---------------+
                                              |    :api.js    |
                                              +---------------+
                                                      | 3: PUT /alerts/:id
                                                      v
                                              +---------------+
                                              |  :alerts.py   |
                                              +---------------+
                                                      | 4: map action -> status
                                                      | 5: update_status(alert, status, note, user)
                                                      v
                                            +--------------------+
              6: can_transition(cur, new)   |  :alert_service    |
    +-----------+ <---------------------------------------------+
    |  :Alert   |                           +--------------------+
    | (model)   |  --- 6.1: true / false --->     |         |
    +-----------+                                 |         |
         ^                                        |         |
         | 7: status, notes, resolved_at          |         |
         +----------------------------------------+         |
                                                            |
              8: record(ALERT_STATUS_CHANGED)               |
    +-----------------+ <-----------------------------------+
    | :audit_service  |
    +-----------------+

   ESCALATION BRANCH
                                              +---------------+
                                              |  :alerts.py   |
                                              +---------------+
                                                      | E1: escalate_to_incident(alert, user)
                                                      v
                                            +--------------------+
                                            |  :alert_service    |
                                            +--------------------+
                                               |            |
              E2: [alert.incident_id set?]      |            |
                  yes -> return existing        |            |
    +-------------+ <----------------------------+            |
    |  :Incident  |                                           |
    +-------------+  E3: no -> INSERT Incident                |
         ^              (status = INVESTIGATING)              |
         |                                                    |
         | E4: alert.incident_id = incident.id                |
    +-----------+ <-------------------------------------------+
    |  :Alert   |
    +-----------+
```

**Note on E2.** The idempotence check is a structural property visible here: the
`alert_service` object is linked to both `Alert` and `Incident`, and consults the
existing link before creating anything. This is what
`test_escalating_an_already_linked_alert_returns_the_same_incident` verifies.

---

## 6. Collaboration 5 - Incident Lifecycle Transition

```
                  1: click an allowed transition
     +---------+  ------------------------------>  +---------------------+
     | :Analyst|                                   | :IncidentDetails.jsx|
     +---------+  <------------------------------  +---------------------+
                  10: tracker advances + toast             |
                                                           | 2: updateIncident(id, {status, note})
                                                           v
                                                   +----------------+
                                                   |    :api.js     |
                                                   +----------------+
                                                           | 3: PUT /incidents/:id
                                                           v
                                                   +----------------+
                                                   | :incidents.py  |
                                                   +----------------+
                                                           | 4: transition(i, status, note, user)
                                                           v
                                                +------------------------+
         5: can_transition(current, requested)  |  :incident_service     |
    +-------------+ <--------------------------  +------------------------+
    |  :Incident  |                                 |    |     |      |
    |  (model)    |  --- 5.1: consult                |    |     |      |
    |             |      INCIDENT_STATE_TRANSITIONS  |    |     |      |
    +-------------+  --- 5.2: true / false --------->|    |     |      |
         ^                                           |    |     |      |
         | 6: status, contained_at / resolved_at     |    |     |      |
         |    resolution_summary                     |    |     |      |
         +-------------------------------------------+    |     |      |
         ^                                                |     |      |
         | 7: append_history({from,to,actor,note,at})     |     |      |
         +------------------------------------------------+     |      |
                                                                |      |
         8: [terminal state] close every linked alert           |      |
    +-----------+ <-------------------------------------------- +      |
    |  :Alert   |   status = RESOLVED or FALSE_POSITIVE                |
    +-----------+   resolved_at = now                                  |
                                                                       |
         9: record(INCIDENT_STATUS_CHANGED) + COMMIT                   |
    +-----------------+ <------------------------------------------- +-+
    | :audit_service  |
    +-----------------+

   [illegal transition]
    +------------------------+
    |  :incident_service     |  --- raises ConflictError(409) with
    +------------------------+      {current, requested, allowed}
```

---

## 7. Collaboration 6 - Dashboard Aggregation

```
                 1: open dashboard
     +---------+  ------------------->  +------------------+
     | :Analyst|                        | :Dashboard.jsx   |
     +---------+  <-------------------  +------------------+
                 12: render KPIs + 6 charts      |
                                                 | 2: dashboardStats(14)
                                                 v
                                         +---------------+
                                         |    :api.js    |
                                         +---------------+
                                                 | 3: GET /dashboard/stats
                                                 v
                                         +----------------+
                                         | :dashboard.py  |
                                         +----------------+
                                                 | 4: dashboard_stats(days)
                                                 v
                                     +---------------------------+
                                     |   :analytics_service      |
                                     +---------------------------+
                                       |   |   |   |   |   |   |
     4.1: count totals                  |   |   |   |   |   |   |
     +-------------------+ <------------+   |   |   |   |   |   |
     | :SecurityEvent    |                  |   |   |   |   |   |
     | :Threat :Alert    |                  |   |   |   |   |   |
     | :Incident :Asset  |                  |   |   |   |   |   |
     +-------------------+                  |   |   |   |   |   |
                                            |   |   |   |   |   |
     4.2: threats_over_time(days)           |   |   |   |   |   |
     +-------------------+ <----------------+   |   |   |   |   |
     |  GROUP BY date,   |                      |   |   |   |   |
     |  severity         |                      |   |   |   |   |
     +-------------------+                      |   |   |   |   |
                                                |   |   |   |   |
     4.3: severity_distribution()               |   |   |   |   |
     4.4: category_distribution()  <------------+   |   |   |   |
     4.5: events_by_source()                        |   |   |   |
     4.6: detection_trend()                         |   |   |   |
     4.7: protocol_distribution()                   |   |   |   |
                                                    |   |   |   |
     4.8: threat_level()                            |   |   |   |
     +-------------------------+ <------------------+   |   |   |
     | unresolved alerts,      |                        |   |   |
     | last 24 h, by severity  |                        |   |   |
     +-------------------------+                        |   |   |
                                                        |   |   |
     4.9: detection_quality()                           |   |   |
     +-------------------------------+ <----------------+   |   |
     | priority 1 analyst triage     |                      |   |
     | priority 2 model hold-out     |                      |   |
     | priority 3 mean confidence    |                      |   |
     | ALWAYS returns source + label |                      |   |
     +-------------------------------+                      |   |
                                                            |   |
     4.10: activity_feed()                                  |   |
     +-------------------------------+ <--------------------+   |
     | merge Alert + Incident +      |                          |
     | AuditLog, sort newest first   |                          |
     +-------------------------------+                          |
                                                                |
     4.11: system_health()                                      |
     +-------------------------------+ <------------------------+
     | DB ping, engine mode,         |
     | ML availability, backlog      |
     +-------------------------------+
```

**Structural observation:** every link from `analytics_service` is a **read**.
The object has no write link to any model, which is the structural guarantee
behind the claim that refreshing the dashboard cannot alter data.

---

## 8. Object collaboration summary

| Collaboration | Participating objects | Links |
|---------------|-----------------------|-------|
| Login | Analyst, Login.jsx, AuthContext, api.js, auth.py, auth_service, User, security, audit_service | 8 |
| Event analysis | Analyst, ThreatDetection.jsx, api.js, events.py, validators, detection_service, ThreatDetector, features, rules, StatisticalBaseline, ML models, SecurityEvent, DetectionResult, Threat, Alert, Incident, Asset, audit_service | 18 |
| CSV upload | Analyst, LogAnalyzer.jsx, api.js, events.py, csv_parser, validators, detection_service, ThreatDetector, models, audit_service | 11 |
| Alert triage | Analyst, Alerts.jsx, api.js, alerts.py, alert_service, Alert, Incident, audit_service | 8 |
| Incident lifecycle | Analyst, IncidentDetails.jsx, api.js, incidents.py, incident_service, Incident, Alert, audit_service | 8 |
| Dashboard | Analyst, Dashboard.jsx, api.js, dashboard.py, analytics_service, all entity models | 10 |

### 8.1 What the structure reveals

Three facts are visible in the communication diagrams that the sequence diagrams
do not make obvious:

1. **`detection_service` is the highest-coupling object in the system** - it has
   links to eight other objects. This is intentional (it is the orchestrator),
   but it is also why it is the module most heavily covered by tests.

2. **`ThreatDetector` has no link to any model or to Flask.** Its only outward
   links are to `features`, `rules`, `StatisticalBaseline` and the optional
   sklearn artefacts. This structural isolation is what allows
   `test_detection_engine.py` to exercise it with no database and no application
   context.

3. **`audit_service` is linked from five different collaborations.** That is the
   structural expression of FR-12: auditing is a cross-cutting concern, not a
   feature of one screen.
