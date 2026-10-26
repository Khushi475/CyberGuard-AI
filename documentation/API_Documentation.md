# CyberGuard AI - REST API Documentation

**Base URL:** `http://127.0.0.1:5000/api`
**Version:** 1.0.0
**Live index:** `GET /api` returns a machine-readable list of every registered endpoint.

---

## Conventions

### Response envelope

Every successful response:

```json
{
  "success": true,
  "message": "OK",
  "data": { }
}
```

List endpoints add pagination, and often filter metadata:

```json
{
  "success": true,
  "message": "OK",
  "data": [ ],
  "pagination": {
    "page": 1, "per_page": 20, "total": 143, "pages": 8,
    "has_next": true, "has_prev": false
  },
  "filters": { }
}
```

Every failure:

```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "source_ip must be a valid IPv4/IPv6 address (received '999.999.1.1').",
  "details": { "field": "source_ip" }
}
```

### Error codes

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `BAD_REQUEST` | Malformed request |
| 401 | `NO_TOKEN` | No Authorization header supplied |
| 401 | `TOKEN_INVALID` | Signature verification failed |
| 401 | `TOKEN_EXPIRED` | Token past its expiry |
| 401 | `INVALID_CREDENTIALS` | Wrong email or password |
| 401 | `ACCOUNT_DISABLED` | Account is deactivated |
| 403 | `FORBIDDEN` | Authenticated but not permitted |
| 404 | `NOT_FOUND` | Resource or route does not exist |
| 405 | `METHOD_NOT_ALLOWED` | Wrong HTTP verb for this path |
| 409 | `CONFLICT` | Illegal state transition |
| 413 | `FILE_TOO_LARGE` | Upload exceeds 8 MB |
| 422 | `VALIDATION_ERROR` | Input failed validation - `details.field` names the culprit |
| 500 | `INTERNAL_SERVER_ERROR` | Unhandled failure (session rolled back) |
| 501 | - | Optional dependency missing (for example ReportLab for PDF) |

### Authentication

All endpoints except `GET /api/health` and `GET /api` require:

```
Authorization: Bearer <token>
```

Obtain a token from `POST /api/auth/login`. Tokens are signed with `SECRET_KEY`
and expire after `TOKEN_MAX_AGE_SECONDS` (default 86400 = 24 hours).

### Common query parameters

| Parameter | Applies to | Default | Notes |
|-----------|-----------|---------|-------|
| `page` | all list endpoints | 1 | 1-based |
| `per_page` | all list endpoints | 20 (50 for assets/intel) | capped at 200 |
| `search` | alerts, incidents, events, threats, assets, intel | - | case-insensitive partial match |
| `sort` | alerts, incidents | `newest` | `newest`, `oldest`, `risk` |

---

# Authentication

## POST /api/auth/login

Exchange credentials for a session token. **No authentication required.**

**Request**

```json
{
  "email": "admin@cyberguard.ai",
  "password": "admin123"
}
```

**Response `200`**

```json
{
  "success": true,
  "message": "Signed in successfully.",
  "data": {
    "token": "eyJ1aWQiOjEsImVtYWlsIjoi...",
    "user": {
      "id": 1,
      "full_name": "Priya Administrator",
      "email": "admin@cyberguard.ai",
      "role": "ADMIN",
      "department": "Security Operations Centre",
      "is_active": true,
      "last_login": "2026-09-22T03:14:05",
      "created_at": "2026-09-21T21:46:05",
      "preferences": {
        "notify_email": true,
        "notify_critical_only": false,
        "detection_sensitivity": 1.0,
        "theme": "dark"
      }
    }
  }
}
```

**Errors**

| Status | Code | Cause |
|--------|------|-------|
| 401 | `INVALID_CREDENTIALS` | Wrong password **or** unknown email (identical message, by design) |
| 401 | `ACCOUNT_DISABLED` | Account deactivated |
| 422 | `VALIDATION_ERROR` | Malformed email, or password missing |

## POST /api/auth/logout

Records the sign-out in the audit trail. Returns `200`.

## GET /api/auth/me

Returns the profile behind the supplied token, including preferences.

## PUT /api/auth/profile

**Request:** `{ "full_name": "...", "email": "...", "department": "..." }` (all optional)
**Response `200`:** the updated user.
**Errors:** `422` if the email is malformed or already used by another account.

## PUT /api/auth/preferences

**Request**

```json
{
  "notify_email": true,
  "notify_critical_only": false,
  "detection_sensitivity": 1.2,
  "theme": "dark"
}
```

`detection_sensitivity` must be between 0.5 and 1.5; `theme` must be `dark` or `light`.
**Errors:** `422` for out-of-range values.

## PUT /api/auth/password

**Request:** `{ "current_password": "...", "new_password": "..." }`
**Errors:** `401` if the current password is wrong; `422` if the new password is shorter than 6 characters or identical to the current one.

---

# Dashboard and Analytics

## GET /api/dashboard/stats

Every figure and chart series the dashboard needs.

**Query:** `days` (default 14, max 90)

**Response `200`** (abridged)

```json
{
  "data": {
    "totals": {
      "total_events": 320, "threats_detected": 143, "critical_alerts": 64,
      "open_alerts": 79, "active_incidents": 60, "resolved_incidents": 4,
      "monitored_assets": 12, "assets_at_risk": 5, "active_indicators": 15,
      "events_last_24h": 12, "threats_last_24h": 9
    },
    "threat_level": {
      "level": "CRITICAL", "score": 92, "window_hours": 24,
      "open_by_severity": {"LOW": 0, "MEDIUM": 6, "HIGH": 0, "CRITICAL": 12},
      "basis": "Unresolved alerts raised in the last 24 hours."
    },
    "detection_quality": {
      "triaged_alerts": 6, "confirmed_true_positive": 4,
      "confirmed_false_positive": 2, "accuracy": 66.7,
      "source": "analyst_triage", "label": "Analyst-confirmed precision",
      "note": "Measured from 6 alerts closed by analysts."
    },
    "system_health": {
      "overall": "OPERATIONAL", "score": 100,
      "checks": [
        {"component": "Database", "status": "OPERATIONAL", "detail": "SQLite connection responding."},
        {"component": "Detection Engine", "status": "OPERATIONAL", "detail": "Running in hybrid-ml mode with 18 features."},
        {"component": "ML Models", "status": "OPERATIONAL", "detail": "Trained models loaded."},
        {"component": "Event Pipeline", "status": "OPERATIONAL", "detail": "0 event(s) awaiting analysis."}
      ]
    },
    "charts": {
      "threats_over_time":   [{"date": "2026-09-08", "LOW": 0, "MEDIUM": 1, "HIGH": 3, "CRITICAL": 5, "total": 9}],
      "severity_distribution":[{"severity": "LOW", "count": 177}],
      "category_distribution":[{"category": "Brute Force Attempt", "count": 34}],
      "events_by_source":    [{"source_ip": "203.0.113.66", "count": 18}],
      "detection_trend":     [{"date": "2026-09-08", "events": 24, "threats": 9, "detection_rate": 37.5}],
      "protocol_distribution":[{"protocol": "HTTPS", "count": 96}]
    },
    "recent_alerts": [ ],
    "activity_feed": [
      {"type": "alert", "severity": "CRITICAL", "title": "...",
       "message": "...", "timestamp": "2026-09-22T03:14:05",
       "reference": "ALT-000144", "entity_id": 144}
    ],
    "window_days": 14,
    "generated_at": "2026-09-22T09:12:33"
  }
}
```

> **Note on `detection_quality`.** The response always carries `source`, `label`
> and `note`. The figure is analyst-confirmed precision once five or more alerts
> have been triaged; before that it falls back to the model's synthetic hold-out
> accuracy, or to mean engine confidence, and says so.

## GET /api/dashboard/activity

**Query:** `limit` (default 15, max 50). Merged, newest-first feed of alerts, incident transitions and audit entries.

## GET /api/dashboard/threat-level

Returns only the threat-level object above.

## GET /api/analytics

**Query:** `days` (default 30, max 365)

Deeper aggregates: averages (risk, confidence, analysis time), mean time to
resolve, severity and category distributions, detection trend, events by source,
protocol and event-type distributions, a 24-bucket hourly distribution,
ingestion channels, and alert/incident status breakdowns.

---

# Security Events

## GET /api/events

**Query:** `page`, `per_page`, `severity`, `event_type`, `protocol`, `channel`, `search`

**Response `200`:** paginated events, each with its embedded `detection` object.

## GET /api/events/{id}

One event with its detection result. `404` if not found.

## POST /api/events

Submit an event; it is validated, stored and analysed immediately.

**Request** (only `source_ip` is required)

```json
{
  "source_ip": "203.0.113.66",
  "destination_ip": "10.0.1.20",
  "source_port": 44122,
  "destination_port": 22,
  "protocol": "SSH",
  "event_type": "authentication",
  "request_count": 68,
  "failed_login_attempts": 62,
  "packet_count": 340,
  "bytes_transferred": 41000,
  "connection_duration": 95,
  "timestamp": "2026-09-22T03:14:00"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `source_ip` | string | **Yes** | Valid IPv4 or IPv6 |
| `destination_ip` | string | No | Valid IPv4 or IPv6 |
| `source_port`, `destination_port` | int | No | 0-65535 |
| `protocol` | string | No | TCP, UDP, ICMP, HTTP, HTTPS, SSH, FTP, DNS, SMTP, RDP (default TCP) |
| `event_type` | string | No | authentication, network_traffic, file_access, process_execution, dns_query, web_request, firewall, vpn_session, database_query, email_gateway (default network_traffic) |
| `request_count` | int | No | 0 - 10 000 000 |
| `failed_login_attempts` | int | No | 0 - 100 000 |
| `packet_count` | int | No | 0 - 100 000 000 |
| `bytes_transferred` | float | No | 0 - 1e12 |
| `connection_duration` | float | No | 0 - 1e6 seconds |
| `timestamp` | string | No | ISO-8601; defaults to now |
| `asset_id` | int | No | Explicit asset link |

**Response `201`:** the same shape as `POST /api/events/analyze` below.

## POST /api/events/analyze

**The primary detection endpoint.**

**Query:** `persist` (default `true`). `persist=false` runs a dry run - the engine
returns a verdict and nothing is written to the database.

**Request:** same body as `POST /api/events`, plus an optional `sensitivity`
(0.5-1.5) that overrides the analyst's saved preference for this call.

**Response `200`**

```json
{
  "success": true,
  "message": "Analysis complete.",
  "data": {
    "event_id": 441,
    "persisted": true,
    "classification": "Brute Force Attempt",
    "risk_score": 92,
    "confidence": 0.97,
    "severity": "CRITICAL",
    "is_threat": true,
    "reasons": [
      "62 failed authentication attempts recorded for this source.",
      "The event originates from an authentication service.",
      "The targeted port 22 hosts a remote-access or database service.",
      "'failed login attempts' is 112.4 standard deviations above the learned normal baseline.",
      "The trained classifier assigns a 99% probability that this event is malicious."
    ],
    "recommended_action": "Temporarily rate-limit or lock the targeted account, enforce MFA, and review authentication logs for the source address.",
    "mitre_tactic": "Credential Access (TA0006)",
    "scores": { "rule": 86.7, "anomaly": 100.0, "ml": 99.0 },
    "triggered_rules": [ {"category": "Brute Force Attempt", "score": 86.7} ],
    "feature_summary": {
      "Failed logins": 62, "Requests": 68, "Packets": 340,
      "Bytes transferred": 41000, "Duration (s)": 95.0,
      "Requests/sec": 0.72, "Bytes/packet": 120.59,
      "Hour of day": 3, "Off hours": true
    },
    "model_used": "hybrid-ml",
    "engine_version": "1.2",
    "analysis_time_ms": 7.42,
    "event": { },
    "alert": { "id": 144, "alert_code": "ALT-000144", "status": "NEW" },
    "incident": { "id": 65, "incident_code": "INC-000065", "status": "NEW" },
    "threat_id": 144
  }
}
```

**Side effects when `persist=true`**

| Condition | Effect |
|-----------|--------|
| always | `SecurityEvent` + `DetectionResult` stored; asset risk updated; audit entry written |
| `is_threat` | `Threat` record created |
| `risk_score >= 26` | `Alert` created with status NEW |
| `risk_score >= 76` | `Incident` created with status NEW, and the alert linked to it |

All of the above commit in **one transaction**.

**Errors:** `422` with `details.field` naming the offending input; `401` without a token.

## POST /api/events/upload

CSV log ingestion. `multipart/form-data` with a `file` part.

**Accepted:** `.csv`, `.txt`, `.log`; max 8 MB; max 5000 rows.

**Columns** - only `source_ip` is mandatory. These aliases are accepted:

| CSV column | Maps to |
|------------|---------|
| `bytes`, `byte_count` | `bytes_transferred` |
| `packets` | `packet_count` |
| `failed_logins`, `failed_login` | `failed_login_attempts` |
| `duration` | `connection_duration` |
| `src_ip`, `dst_ip` | `source_ip`, `destination_ip` |
| `src_port`, `dst_port` | `source_port`, `destination_port` |
| `requests` | `request_count` |
| `time`, `date` | `timestamp` |

**Response `201`**

```json
{
  "data": {
    "filename": "sample_logs_mixed.csv",
    "total_records": 120,
    "normal_events": 61,
    "suspicious_events": 59,
    "low": 61, "medium": 6, "high": 26, "critical": 27,
    "high_risk_events": 53,
    "alerts_created": 59,
    "incidents_created": 12,
    "rejected_rows": 0,
    "row_errors": [],
    "categories": [ {"category": "Brute Force Attempt", "count": 14} ],
    "top_sources": [ {"source_ip": "203.0.113.66", "count": 9} ],
    "records": [
      {
        "event_id": 442, "timestamp": "2026-09-22T03:14:00",
        "source_ip": "203.0.113.66", "destination_ip": "10.0.1.20",
        "destination_port": 22, "protocol": "SSH",
        "event_type": "authentication",
        "classification": "Brute Force Attempt", "risk_score": 92,
        "severity": "CRITICAL", "confidence": 0.97,
        "reason": "62 failed authentication attempts recorded for this source."
      }
    ]
  }
}
```

**Partial failures do not abort the upload.** Invalid rows appear in
`row_errors` as `{"row": 3, "error": "source_ip must be a valid IPv4/IPv6 address..."}`
while valid rows are still analysed and stored.

**Errors**

| Status | Cause |
|--------|-------|
| 422 | Empty file, header-only file, missing `source_ip` column, wrong extension, no file part, or every row invalid |
| 413 | File exceeds 8 MB |

## GET /api/events/sample

Five ready-made payloads (one per detection category) for demonstrations.

## DELETE /api/events/{id}

Deletes the event and cascades to its detection result, threat and alerts.

---

# Threats and Threat Intelligence

## GET /api/threats

**Query:** `page`, `per_page`, `severity`, `category`, `search`
**Filters returned:** the eight categories and four severities.

## GET /api/threats/{id}

One threat with its originating event and detection result.

## GET /api/threat-intelligence

**Query:** `page`, `per_page`, `indicator_type`, `risk_level`, `status`, `search`

**Response `200`**

```json
{
  "data": [
    {
      "id": 1, "indicator": "203.0.113.66", "indicator_type": "Suspicious IP",
      "category": "Brute Force Attempt", "risk_level": "HIGH",
      "confidence": 0.91, "status": "ACTIVE",
      "description": "Repeated failed SSH authentication bursts against the domain controller.",
      "source_feed": "CyberGuard Simulated Feed", "hit_count": 23,
      "is_simulated": true,
      "first_seen": "2026-07-14T09:22:11", "last_seen": "2026-09-21T23:40:02"
    }
  ],
  "notice": "All indicators in this feed are simulated for academic demonstration. They use RFC 5737 documentation addresses and reserved domain names."
}
```

## PUT /api/threat-intelligence/{id}

**Request:** `{ "status": "ACTIVE" | "MONITORING" | "RETIRED" }`

---

# Alerts

## GET /api/alerts

**Query:** `page`, `per_page`, `severity`, `status`, `threat_type`, `search`, `date_from`, `date_to`, `min_risk`, `sort`

**Response `200`:** paginated alerts plus a `filters` object containing the
available severities, statuses and threat types.

## GET /api/alerts/{id}

Full detail including the originating event, the reasons and any linked incident.

## PUT /api/alerts/{id}

Change the alert's status.

**Request:** either an explicit status or a friendly action.

```json
{ "action": "resolve", "note": "Source blocked at the perimeter gateway." }
```

| `action` | Resulting status |
|----------|------------------|
| `acknowledge` | ACKNOWLEDGED |
| `investigate` | INVESTIGATING |
| `resolve` | RESOLVED |
| `false_positive` | FALSE_POSITIVE |
| `reopen` | INVESTIGATING |

Or `{ "status": "RESOLVED" }` directly.

**Errors:** `422` for an unknown status; `409` for an illegal transition.

## POST /api/alerts/{id}/escalate

Create (or return) the incident that tracks this alert. **Idempotent** - if the
alert already has an incident, that incident is returned rather than a duplicate
being created.

**Request:** `{ "title": "optional custom title" }`
**Response `201`:** `{ "incident": { }, "alert": { } }`

## GET /api/alerts/filters

Dropdown values for the Alerts page.

---

# Incidents

## GET /api/incidents

**Query:** `page`, `per_page`, `status`, `severity`, `assigned_to` (id or `unassigned`), `search`, `sort`
**Filters returned:** statuses and the list of active analysts.

## GET /api/incidents/{id}

**Response `200`** includes the status history, linked alerts, related events and
the state machine:

```json
{
  "data": {
    "id": 65, "incident_code": "INC-000065",
    "title": "Brute Force Attempt targeting 10.0.1.20",
    "threat_type": "Brute Force Attempt",
    "severity": "CRITICAL", "priority": "P1", "status": "NEW",
    "risk_score": 92, "source_ip": "203.0.113.66",
    "assigned_to": 2, "assigned_analyst": "Arjun Analyst",
    "detected_at": "2026-09-22T03:14:00",
    "contained_at": null, "resolved_at": null,
    "resolution_summary": null,
    "allowed_transitions": ["FALSE_POSITIVE", "INVESTIGATING", "OPEN"],
    "history": [
      {"from": null, "to": "NEW", "actor": "Detection Engine",
       "note": "Incident opened automatically because the risk score reached the critical band.",
       "at": "2026-09-22T03:14:00"}
    ],
    "alerts": [ ],
    "related_events": [ ],
    "state_machine": {
      "current": "NEW",
      "allowed": ["FALSE_POSITIVE", "INVESTIGATING", "OPEN"],
      "all_states": ["NEW","OPEN","INVESTIGATING","CONTAINED","RESOLVED","FALSE_POSITIVE"]
    }
  }
}
```

## POST /api/incidents

**Request**

```json
{
  "title": "Suspicious VPN sessions from a new region",
  "description": "Several sign-ins outside the expected geography.",
  "threat_type": "Suspicious Login Activity",
  "severity": "HIGH",
  "source_ip": "203.0.113.201",
  "assigned_to": 2,
  "alert_ids": [12, 13]
}
```

Only `title` is required. Severity defaults to MEDIUM; the assignee defaults to
the caller. Priority is derived from severity (CRITICAL->P1, HIGH->P2, MEDIUM->P3, LOW->P4).

## PUT /api/incidents/{id}

Drive the lifecycle state machine, or reassign.

**Request**

```json
{ "action": "resolve", "note": "Verified.", "resolution_summary": "MFA enforced." }
```

| `action` | Resulting status |
|----------|------------------|
| `open` | OPEN |
| `investigate` | INVESTIGATING |
| `contain` | CONTAINED |
| `resolve` | RESOLVED |
| `false_positive` | FALSE_POSITIVE |
| `reopen` | INVESTIGATING |

Reassign with `{ "assigned_to": 3 }` alone (no status change).

**Legal transitions**

| From | To |
|------|----|
| NEW | OPEN, INVESTIGATING, FALSE_POSITIVE |
| OPEN | INVESTIGATING, CONTAINED, FALSE_POSITIVE |
| INVESTIGATING | CONTAINED, RESOLVED, FALSE_POSITIVE |
| CONTAINED | RESOLVED, INVESTIGATING |
| RESOLVED | INVESTIGATING |
| FALSE_POSITIVE | INVESTIGATING |

**Error `409`**

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Invalid lifecycle transition: NEW -> RESOLVED. Allowed from NEW: FALSE_POSITIVE, INVESTIGATING, OPEN.",
  "details": { "current": "NEW", "requested": "RESOLVED",
               "allowed": ["FALSE_POSITIVE","INVESTIGATING","OPEN"] }
}
```

**Side effect:** moving to RESOLVED or FALSE_POSITIVE closes every alert linked to the incident.

---

# Assets

## GET /api/assets

**Query:** `page`, `per_page`, `status`, `risk_level`, `asset_type`, `search`
Each asset carries a live `event_count`.

## GET /api/assets/{id}

One asset plus its 20 most recent events.

## POST /api/assets

**Request**

```json
{
  "name": "Primary Web Server",
  "ip_address": "10.0.3.10",
  "asset_type": "Web Server",
  "operating_system": "Ubuntu Server 22.04 LTS",
  "location": "Data Centre A",
  "owner": "Platform Team",
  "criticality": "CRITICAL",
  "status": "ONLINE"
}
```

`name` and `ip_address` are required; the IP must be unique.

**Errors:** `422` for a duplicate IP, an invalid IP or a missing name.

## PUT /api/assets/{id}

Partial update of any of the fields above.

## DELETE /api/assets/{id}

Removes the asset. **Its security events are preserved** with `asset_id` set to null.

---

# Reports

## GET /api/reports

Paginated list of previously generated reports.

## GET /api/reports/preview

**Query:** `days`, `report_type`. Builds the content **without storing** a report.

## GET /api/reports/{id}

A stored report including its full content.

## POST /api/reports/generate

**Request**

```json
{ "days": 30, "report_type": "SUMMARY", "title": "Morning handover" }
```

`report_type` is one of `SUMMARY`, `THREAT`, `INCIDENT`, `COMPLIANCE`.
`days` must be 1-365.

**Response `201`:** the stored report with a `content` object containing the
title, period, summary counts, severity breakdown, threat categories, detection
statistics, incident statistics, top sources, at-risk assets, threat level and
**recommendations derived from the measured figures**.

## GET /api/reports/{id}/download

**Query:** `format` = `pdf` | `csv` | `json` (default `json`)

| Format | Content-Type | Notes |
|--------|--------------|-------|
| `pdf` | `application/pdf` | Seven-section A4 document. Returns `501` with an install hint if ReportLab is unavailable. |
| `csv` | `text/csv` | Flattened section/metric/value layout |
| `json` | `application/json` | Full structured content |

All three set `Content-Disposition: attachment`.

## DELETE /api/reports/{id}

Removes a stored report.

---

# System

## GET /api/health

**Public** liveness probe.

```json
{
  "data": {
    "status": "healthy",
    "service": "CyberGuard AI API",
    "version": "1.0.0",
    "environment": "development",
    "database": { "connected": true, "detail": "connected" },
    "detection_engine": {
      "mode": "hybrid-ml", "ml_available": true,
      "engine_version": "1.2",
      "baseline_source": ".../ml_model/baseline.json"
    }
  }
}
```

## GET /api/system/status

Detailed status: API info and endpoint count, database engine and per-table row
counts, full detection-engine info, trained-model metadata, the health
self-check, and the configured thresholds (alert 26, incident 76, severity bands,
upload limits).

## POST /api/system/reload-model

Re-reads the ML artefacts from disk without restarting Flask. Useful after
running `train_model.py`.

## GET /api/audit-logs

**Query:** `limit` (default 100, max 500), `action`
Returns the audit trail newest-first.

## GET /api

**Public.** Machine-readable index of every registered `/api` route with its
methods and a one-line summary.

---

# Quick reference

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/auth/login` | No | Sign in |
| POST | `/api/auth/logout` | Yes | Sign out |
| GET | `/api/auth/me` | Yes | Current profile |
| PUT | `/api/auth/profile` | Yes | Update profile |
| PUT | `/api/auth/preferences` | Yes | Update preferences |
| PUT | `/api/auth/password` | Yes | Change password |
| GET | `/api/dashboard/stats` | Yes | Dashboard data |
| GET | `/api/dashboard/activity` | Yes | Activity feed |
| GET | `/api/dashboard/threat-level` | Yes | Threat posture |
| GET | `/api/analytics` | Yes | Deep analytics |
| GET | `/api/events` | Yes | List events |
| POST | `/api/events` | Yes | Submit an event |
| GET | `/api/events/{id}` | Yes | One event |
| POST | `/api/events/analyze` | Yes | **Analyse an event** |
| POST | `/api/events/upload` | Yes | **CSV log upload** |
| GET | `/api/events/sample` | Yes | Sample payloads |
| DELETE | `/api/events/{id}` | Yes | Delete an event |
| GET | `/api/threats` | Yes | List threats |
| GET | `/api/threats/{id}` | Yes | One threat |
| GET | `/api/threat-intelligence` | Yes | Indicator feed |
| PUT | `/api/threat-intelligence/{id}` | Yes | Update an indicator |
| GET | `/api/alerts` | Yes | Alert queue |
| GET | `/api/alerts/{id}` | Yes | One alert |
| PUT | `/api/alerts/{id}` | Yes | Triage an alert |
| POST | `/api/alerts/{id}/escalate` | Yes | Escalate to an incident |
| GET | `/api/alerts/filters` | Yes | Filter options |
| GET | `/api/incidents` | Yes | List incidents |
| POST | `/api/incidents` | Yes | Create an incident |
| GET | `/api/incidents/{id}` | Yes | Incident detail |
| PUT | `/api/incidents/{id}` | Yes | Transition / reassign |
| GET | `/api/assets` | Yes | Inventory |
| POST | `/api/assets` | Yes | Register an asset |
| GET | `/api/assets/{id}` | Yes | One asset |
| PUT | `/api/assets/{id}` | Yes | Update an asset |
| DELETE | `/api/assets/{id}` | Yes | Remove an asset |
| GET | `/api/reports` | Yes | List reports |
| GET | `/api/reports/preview` | Yes | Preview without storing |
| POST | `/api/reports/generate` | Yes | Generate a report |
| GET | `/api/reports/{id}` | Yes | One report |
| GET | `/api/reports/{id}/download` | Yes | Export PDF/CSV/JSON |
| DELETE | `/api/reports/{id}` | Yes | Delete a report |
| GET | `/api/health` | **No** | Liveness probe |
| GET | `/api/system/status` | Yes | Detailed status |
| POST | `/api/system/reload-model` | Yes | Reload ML artefacts |
| GET | `/api/audit-logs` | Yes | Audit trail |
| GET | `/api` | **No** | Endpoint index |

---

# curl examples

```bash
# 1. Health check (no auth)
curl http://127.0.0.1:5000/api/health

# 2. Sign in and capture the token
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cyberguard.ai","password":"admin123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

# 3. Dashboard
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/api/dashboard/stats

# 4. Analyse a brute-force event
curl -X POST http://127.0.0.1:5000/api/events/analyze \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"source_ip":"203.0.113.66","destination_ip":"10.0.1.20",
       "destination_port":22,"protocol":"SSH","event_type":"authentication",
       "failed_login_attempts":62,"request_count":68,"packet_count":340,
       "bytes_transferred":41000,"connection_duration":95}'

# 5. Dry run (nothing stored)
curl -X POST "http://127.0.0.1:5000/api/events/analyze?persist=false" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"source_ip":"10.0.1.42","destination_port":443,"request_count":10}'

# 6. Upload a CSV log file
curl -X POST http://127.0.0.1:5000/api/events/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_data/sample_logs_mixed.csv"

# 7. Critical alerts, highest risk first
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:5000/api/alerts?severity=CRITICAL&status=NEW&sort=risk"

# 8. Resolve an alert
curl -X PUT http://127.0.0.1:5000/api/alerts/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"action":"resolve","note":"Source blocked at the gateway."}'

# 9. Attempt an illegal incident transition (returns 409)
curl -X PUT http://127.0.0.1:5000/api/incidents/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"RESOLVED"}'

# 10. Generate and download a PDF report
curl -X POST http://127.0.0.1:5000/api/reports/generate \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"days":30,"report_type":"SUMMARY"}'
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:5000/api/reports/1/download?format=pdf" -o report.pdf
```

On Windows PowerShell, replace the `$TOKEN` capture with:

```powershell
$r = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/login -Method Post `
  -ContentType "application/json" `
  -Body '{"email":"admin@cyberguard.ai","password":"admin123"}'
$TOKEN = $r.data.token
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/dashboard/stats `
  -Headers @{ Authorization = "Bearer $TOKEN" }
```
