# 04 - Entity Relationship Diagram (Structural Modelling)

**Project:** CyberGuard AI
**Lab experiment:** 3 - Requirement modelling using Entity Relationship Diagram

> Every entity, attribute and relationship below is implemented in
> `backend/app/models/`. The ERD is a description of the running schema, not an
> idealised model drawn separately from it.

---

## 1. Entity summary

| # | Entity | Table | Purpose |
|---|--------|-------|---------|
| E1 | User | `users` | Analysts and administrators of the platform |
| E2 | Asset | `assets` | Monitored hosts, servers and network devices |
| E3 | SecurityEvent | `security_events` | One observed telemetry record (central fact table) |
| E4 | DetectionResult | `detection_results` | The engine's explainable verdict on one event |
| E5 | Threat | `threats` | A confirmed, classified malicious-looking finding |
| E6 | Alert | `alerts` | The analyst-facing notification raised from a threat |
| E7 | Incident | `incidents` | A tracked investigation case with a lifecycle |
| E8 | ThreatIndicator | `threat_indicators` | Simulated threat-intelligence records |
| E9 | Report | `reports` | A generated security report |
| E10 | AuditLog | `audit_logs` | Append-only trail of state-changing actions |

---

## 2. ER diagram (Crow's-foot notation)

```
                          +---------------------------+
                          |          USER             |
                          +---------------------------+
                          | PK id                     |
                          |    full_name              |
                          |    email          (UNIQUE)|
                          |    password_hash          |
                          |    role                   |
                          |    department             |
                          |    is_active              |
                          |    last_login             |
                          |    created_at             |
                          |    notify_email           |
                          |    notify_critical_only   |
                          |    detection_sensitivity  |
                          |    theme                  |
                          +---------------------------+
                            |            |           |
              assigned_to   |            | generates | performs
                    (1:N)   |            |   (1:N)   |  (1:N)
                            |            |           |
          +-----------------+            |           +--------------------+
          |                              |                                |
          v                              v                                v
+--------------------+       +----------------------+        +----------------------+
|     INCIDENT       |       |       REPORT         |        |      AUDIT_LOG       |
+--------------------+       +----------------------+        +----------------------+
| PK id              |       | PK id                |        | PK id                |
|    incident_code(U)|       |    report_code   (U) |        |    action            |
|    title           |       |    title             |        |    entity_type       |
|    description     |       |    report_type       |        |    entity_id         |
|    threat_type     |       |    period_days       |        |    description       |
|    severity        |       |    period_start      |        |    ip_address        |
|    priority        |       |    period_end        |        |    status            |
|    status          |       |    total_events      |        |    created_at        |
|    risk_score      |       |    total_threats     |        | FK user_id -> USER   |
|    source_ip       |       |    total_alerts      |        +----------------------+
|    detected_at     |       |    total_incidents   |
|    contained_at    |       |    content_json      |
|    resolved_at     |       |    generated_at      |
|    resolution_sum. |       | FK generated_by ->   |
|    history_json    |       |       USER           |
| FK assigned_to ->  |       +----------------------+
|       USER         |
+--------------------+
          ^
          | groups (1:N)
          |
+--------------------+
|       ALERT        |
+--------------------+
| PK id              |
|    alert_code   (U)|
|    title           |
|    threat_type     |
|    source_ip       |
|    destination_ip  |
|    severity        |
|    risk_score      |
|    confidence      |
|    status          |
|    description     |
|    reasons_json    |
|    recommended_act.|
|    notes           |
|    created_at      |
|    updated_at      |
|    resolved_at     |
| FK event_id    ----+------------------+
| FK threat_id   ----+---------+        |
| FK incident_id ----+--> INCIDENT      |
+--------------------+         |        |
          ^                    |        |
          | raises (1:N)       |        |
          |                    v        |
+--------------------+   +-----------------------+
|      THREAT        |   |                       |
+--------------------+   |                       |
| PK id              |   |                       |
|    category        |   |                       |
|    description     |   |                       |
|    severity        |   |                       |
|    risk_score      |   |                       |
|    confidence      |   |                       |
|    source_ip       |   |                       |
|    destination_ip  |   |                       |
|    mitre_tactic    |   |                       |
|    indicators_json |   |                       |
|    detected_at     |   |                       |
| FK event_id -------+---+                       |
+--------------------+   |                       |
          ^              |                       |
          | classified as|                       |
          |      (1:N)   |                       |
          |              v                       v
     +--------------------------------------------------+
     |                 SECURITY_EVENT                   |
     +--------------------------------------------------+
     | PK id                                            |
     |    timestamp                            (INDEX)  |
     |    source_ip                            (INDEX)  |
     |    destination_ip                                |
     |    source_port                                   |
     |    destination_port                     (INDEX)  |
     |    protocol                                      |
     |    event_type                           (INDEX)  |
     |    request_count                                 |
     |    failed_login_attempts                         |
     |    packet_count                                  |
     |    bytes_transferred                             |
     |    connection_duration                           |
     |    user_agent                                    |
     |    raw_log                                       |
     |    source_channel        (manual|csv|seed)       |
     |    processed                                     |
     |    created_at                                    |
     | FK asset_id -> ASSET                    (INDEX)  |
     +--------------------------------------------------+
             |                              ^
             | produces (1:1)               | observed on (1:N)
             v                              |
     +--------------------------+   +----------------------+
     |    DETECTION_RESULT      |   |        ASSET         |
     +--------------------------+   +----------------------+
     | PK id                    |   | PK id                |
     |    classification        |   |    name              |
     |    risk_score            |   |    ip_address (INDEX)|
     |    confidence            |   |    asset_type        |
     |    severity      (INDEX) |   |    operating_system  |
     |    is_threat     (INDEX) |   |    location          |
     |    rule_score            |   |    owner             |
     |    anomaly_score         |   |    criticality       |
     |    ml_score              |   |    status            |
     |    engine_version        |   |    risk_level        |
     |    model_used            |   |    risk_score        |
     |    reasons_json          |   |    last_seen         |
     |    features_json         |   |    created_at        |
     |    recommended_action    |   +----------------------+
     |    analysis_time_ms      |
     |    created_at            |
     | FK event_id (UNIQUE) ----+--> SECURITY_EVENT
     +--------------------------+


     +--------------------------------------+
     |          THREAT_INDICATOR            |   (independent reference entity -
     +--------------------------------------+    correlated by value, not by FK)
     | PK id                                |
     |    indicator                 (INDEX) |
     |    indicator_type            (INDEX) |
     |    category                          |
     |    risk_level                (INDEX) |
     |    confidence                        |
     |    status                    (INDEX) |
     |    description                       |
     |    source_feed                       |
     |    hit_count                         |
     |    is_simulated                      |
     |    first_seen                        |
     |    last_seen                 (INDEX) |
     |    created_at                        |
     +--------------------------------------+
```

---

## 3. Relationships with cardinality

| # | Parent | Child | Cardinality | Participation | Foreign key | Meaning |
|---|--------|-------|-------------|---------------|-------------|---------|
| R1 | User | Incident | 1 : N | Optional both ways | `incidents.assigned_to` | An analyst may own many incidents; an incident may be unassigned. |
| R2 | User | AuditLog | 1 : N | Optional | `audit_logs.user_id` | A user performs many audited actions; system actions have no user. |
| R3 | User | Report | 1 : N | Optional | `reports.generated_by` | A user generates many reports. |
| R4 | Asset | SecurityEvent | 1 : N | Optional | `security_events.asset_id` | An asset is observed in many events; an event may not match any asset. |
| R5 | SecurityEvent | DetectionResult | **1 : 1** | Mandatory on the child | `detection_results.event_id` **UNIQUE** | Every analysed event has exactly one verdict. |
| R6 | SecurityEvent | Threat | 1 : N | Optional | `threats.event_id` | A suspicious event yields a threat record; benign events yield none. |
| R7 | SecurityEvent | Alert | 1 : N | Optional | `alerts.event_id` | An event may raise an alert. |
| R8 | Threat | Alert | 1 : N | Optional | `alerts.threat_id` | An alert cites the threat that produced it. |
| R9 | Incident | Alert | 1 : N | Optional | `alerts.incident_id` | An incident groups the alerts being investigated together. |

### 3.1 Notes on specific relationships

**R5 is the only true 1:1.** It is enforced by a `UNIQUE` constraint on
`detection_results.event_id`, and expressed in the ORM as
`uselist=False`. Conceptually one event cannot have two contradictory verdicts.

**R9 is what makes triage work.** Several alerts from the same source can be
attached to one incident, so the analyst investigates a campaign rather than
each packet-level finding in isolation. When the incident closes, every alert
attached to it closes too (`incident_service.transition`).

**ThreatIndicator has no foreign key by design.** Indicators are correlated to
events *by value* (matching an IP, domain or account name), not by referential
integrity. Adding an FK would mean an indicator could only exist once evidence
already existed, which inverts how an intelligence feed actually works - the
feed is meant to be populated *before* the matching traffic appears.

---

## 4. Cascade and deletion behaviour

| Relationship | On delete | Rationale |
|--------------|-----------|-----------|
| SecurityEvent -> DetectionResult | `cascade="all, delete-orphan"` | A verdict about a deleted event is meaningless. |
| SecurityEvent -> Threat | `cascade="all, delete-orphan"` | Same reasoning. |
| SecurityEvent -> Alert | `cascade="all, delete-orphan"` | Same reasoning. |
| User -> AuditLog | `cascade="all, delete-orphan"` | The trail belongs to the account. |
| Asset -> SecurityEvent | **No cascade**; `asset_id` is set to `NULL` | Retiring an asset must not destroy security history. Implemented in `routes/assets.py::delete_asset`. |
| Incident -> Alert | **No cascade** | Alerts survive their incident and can be re-linked. |

---

## 5. Keys, constraints and indexes

### 5.1 Primary keys

Every entity uses a surrogate integer primary key (`id`). Three entities also
carry a human-readable business key, generated sequentially and constrained
`UNIQUE`:

| Entity | Business key | Format | Generated by |
|--------|--------------|--------|--------------|
| Alert | `alert_code` | `ALT-000001` | `detection_service.next_code` |
| Incident | `incident_code` | `INC-000001` | `detection_service.next_code` |
| Report | `report_code` | `RPT-000001` | `detection_service.next_code` |

### 5.2 Unique constraints

| Table | Column | Reason |
|-------|--------|--------|
| `users` | `email` | One account per address; also the login key. |
| `detection_results` | `event_id` | Enforces the 1:1 of relationship R5. |
| `alerts` | `alert_code` | Business identifier. |
| `incidents` | `incident_code` | Business identifier. |
| `reports` | `report_code` | Business identifier. |

### 5.3 Indexes

Indexes were chosen from the actual query patterns of the API, not added
speculatively:

| Table | Indexed column | Query it serves |
|-------|----------------|-----------------|
| `security_events` | `timestamp` | Dashboard time-series, "newest first" listing |
| `security_events` | `source_ip` | Top-sources aggregation, search |
| `security_events` | `event_type`, `destination_port` | Event filters |
| `security_events` | `asset_id` | Per-asset event counts |
| `detection_results` | `severity`, `is_threat`, `created_at` | Severity distribution chart |
| `threats` | `category`, `severity`, `source_ip`, `detected_at` | Category chart, threats-over-time |
| `alerts` | `status`, `severity`, `threat_type`, `source_ip`, `created_at` | Alert queue filters |
| `incidents` | `status`, `severity`, `assigned_to`, `detected_at` | Incident filters |
| `audit_logs` | `action`, `user_id`, `created_at` | Audit trail listing |
| `threat_indicators` | `indicator`, `indicator_type`, `risk_level`, `status`, `last_seen` | Intelligence filters |
| `assets` | `ip_address` | Event-to-asset resolution on every analysis |

The index on `assets.ip_address` matters most: it is hit on **every single event
analysis**, because `detection_service.resolve_asset` looks the endpoint IPs up
to attach the event to an asset.

---

## 6. Normalisation

The schema is in **Third Normal Form**, with two deliberate, documented
exceptions.

| Form | Status | Evidence |
|------|--------|----------|
| 1NF | Met | Every column holds a single atomic value; no repeating groups. |
| 2NF | Met | Every non-key attribute depends on the whole primary key. (All PKs are single-column surrogates, so partial dependency cannot arise.) |
| 3NF | Met, with the exceptions below | No non-key attribute depends on another non-key attribute. |

### 6.1 Documented denormalisation

**(a) JSON-serialised columns.** `reasons_json`, `features_json`,
`indicators_json`, `history_json` and `content_json` store structured lists and
objects as text rather than in child tables.

*Justification:* these values are variable-length, are always read as a whole
with their parent row, and are never queried, filtered or joined on. Creating
five child tables would add joins to every read for no query benefit. Each is
wrapped in a typed Python property so the application sees a list or a dict, and
a malformed value degrades to an empty list rather than raising.

**(b) Severity and score duplicated across DetectionResult, Threat and Alert.**

*Justification:* this is a deliberate temporal snapshot. An alert records the
severity **as assessed at the moment it was raised**. If an analyst later changes
their detection sensitivity, previously stored detections must keep their
original scores, otherwise historical charts would silently rewrite themselves.
The duplication preserves auditability, which for a security tool outweighs
strict normalisation.

---

## 7. Data dictionary - selected key attributes

### SECURITY_EVENT (central fact table)

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| `id` | INTEGER | No | auto | Surrogate primary key |
| `timestamp` | DATETIME | No | `utcnow` | When the activity was observed |
| `source_ip` | VARCHAR(45) | No | - | Originating address (IPv4 or IPv6) |
| `destination_ip` | VARCHAR(45) | Yes | NULL | Target address |
| `source_port` | INTEGER | Yes | NULL | 0-65535 |
| `destination_port` | INTEGER | Yes | NULL | 0-65535 |
| `protocol` | VARCHAR(10) | No | `TCP` | One of 10 accepted protocols |
| `event_type` | VARCHAR(40) | No | `network_traffic` | One of 10 accepted types |
| `request_count` | INTEGER | No | 0 | Requests/connections in the window |
| `failed_login_attempts` | INTEGER | No | 0 | Rejected authentications |
| `packet_count` | INTEGER | No | 0 | Packets observed |
| `bytes_transferred` | FLOAT | No | 0.0 | Payload volume in bytes |
| `connection_duration` | FLOAT | No | 0.0 | Session length in seconds |
| `source_channel` | VARCHAR(30) | No | `manual` | How it entered: `manual`, `csv` or `seed` |
| `processed` | BOOLEAN | No | false | Set true once analysed |
| `asset_id` | INTEGER FK | Yes | NULL | Resolved monitored asset |

### DETECTION_RESULT (the verdict)

| Attribute | Type | Null | Description |
|-----------|------|------|-------------|
| `event_id` | INTEGER FK UNIQUE | No | The analysed event (1:1) |
| `classification` | VARCHAR(60) | No | One of the eight threat categories |
| `risk_score` | INTEGER | No | 0-100 fused score |
| `confidence` | FLOAT | No | 0.0-1.0 |
| `severity` | VARCHAR(20) | No | LOW / MEDIUM / HIGH / CRITICAL |
| `is_threat` | BOOLEAN | No | True when risk >= 26 and not Normal Activity |
| `rule_score` | FLOAT | No | Rule-bank sub-score (kept for explainability) |
| `anomaly_score` | FLOAT | No | Statistical sub-score |
| `ml_score` | FLOAT | No | Machine-learning sub-score |
| `model_used` | VARCHAR(40) | No | `hybrid-ml` or `hybrid-rules` |
| `reasons_json` | TEXT | No | Ordered list of plain-English reasons |
| `analysis_time_ms` | FLOAT | No | Measured engine latency (feeds NFR-01) |

---

## 8. Mapping from ERD to code

| ERD element | Source file |
|-------------|-------------|
| E1 User | `backend/app/models/user.py` |
| E2 Asset | `backend/app/models/asset.py` |
| E3 SecurityEvent | `backend/app/models/security_event.py` |
| E4 DetectionResult | `backend/app/models/detection_result.py` |
| E5 Threat | `backend/app/models/threat.py` |
| E6 Alert | `backend/app/models/alert.py` |
| E7 Incident | `backend/app/models/incident.py` |
| E8 ThreatIndicator | `backend/app/models/threat_indicator.py` |
| E9 Report | `backend/app/models/report.py` |
| E10 AuditLog | `backend/app/models/audit_log.py` |
| Schema creation | `db.create_all()` in `backend/app/__init__.py` |
| Live table counts | `GET /api/system/status` -> `database.tables` |
