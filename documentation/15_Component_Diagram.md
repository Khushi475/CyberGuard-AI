# 15 - Component Diagram

**Project:** CyberGuard AI
**Lab experiment:** 8 - OO design: Package, component and deployment models

---

## 1. Component diagram

Notation: `O-` is a provided interface (lollipop), `-(` is a required interface
(socket).

```
+==============================================================================+
|                          CLIENT TIER (browser)                               |
|                                                                              |
|   +----------------------------------------------------------------------+   |
|   |  <<component>>  React Frontend Application                           |   |
|   |                                                                      |   |
|   |   +------------------+   +------------------+   +-----------------+  |   |
|   |   | <<component>>    |   | <<component>>    |   | <<component>>   |  |   |
|   |   |  Auth UI         |   |  SOC Console UI  |   |  Design System  |  |   |
|   |   |------------------|   |------------------|   |-----------------|  |   |
|   |   | Login page       |   | Dashboard        |   | ui.jsx          |  |   |
|   |   | Route guards     |   | ThreatDetection  |   | Charts.jsx      |  |   |
|   |   | AuthContext      |   | Alerts/Incidents |   | Tailwind theme  |  |   |
|   |   |                  |   | LogAnalyzer      |   | ToastContext    |  |   |
|   |   |                  |   | Assets/Reports   |   |                 |  |   |
|   |   |                  |   | Settings         |   |                 |  |   |
|   |   +------------------+   +------------------+   +-----------------+  |   |
|   |            |                      |                      ^           |   |
|   |            |                      |                      |           |   |
|   |            +----------+-----------+----------------------+           |   |
|   |                       |                                              |   |
|   |                       v                                              |   |
|   |            +------------------------------+                          |   |
|   |            |      <<component>>           |                          |   |
|   |            |      API Client              |  O- IDataAccess          |   |
|   |            |      (services/api.js)       |                          |   |
|   |            |------------------------------|                          |   |
|   |            | - base URL resolution        |                          |   |
|   |            | - Bearer token injection     |                          |   |
|   |            | - error translation          |                          |   |
|   |            | - 401 -> session clear       |                          |   |
|   |            +------------------------------+                          |   |
|   |                       |                                              |   |
|   +-----------------------|----------------------------------------------+   |
+===========================|==================================================+
                            |  -( IRestApi      HTTP / JSON
                            |                   Bearer token
                            v
+==============================================================================+
|                       APPLICATION TIER (Flask process)                       |
|                                                                              |
|   +----------------------------------------------------------------------+   |
|   |  <<component>>  Flask REST API                     O- IRestApi       |   |
|   |----------------------------------------------------------------------|   |
|   |  CORS filter -> Blueprint router -> error handler -> JSON envelope    |   |
|   |                                                                      |   |
|   |  auth | dashboard | analytics | events | threats | intel |           |   |
|   |  alerts | incidents | assets | reports | system                       |   |
|   +----------------------------------------------------------------------+   |
|        |            |            |            |            |                 |
|        | -(IAuth    | -(IDetect  | -(ICase    | -(IAnalyt  | -(IReport       |
|        v            v            v            v            v                 |
|   +----------+ +-------------+ +------------+ +-----------+ +-------------+   |
|   |<<compo-  | |<<component>>| |<<compo-    | |<<compo-   | |<<component>>|   |
|   | nent>>   | | Threat      | | nent>>     | | nent>>    | | Report      |   |
|   | Authenti-| | Detection   | | Incident   | | Analytics | | Generation  |   |
|   | cation   | | Service     | | & Alert    | | Engine    | | Module      |   |
|   | Module   | |             | | Management | |           | |             |   |
|   |----------| |-------------| |------------| |-----------| |-------------|   |
|   | login    | | persist_    | | alert      | | dashboard | | build       |   |
|   | logout   | |  analysis   | |  triage    | |  stats    | |  content    |   |
|   | token    | | analyze_    | | escalation | | charts    | | recommend-  |   |
|   |  issue/  | |  batch      | | lifecycle  | | threat    | |  ations     |   |
|   |  verify  | | asset risk  | |  guard     | |  level    | | CSV export  |   |
|   | profile  | | alert/      | | cascade    | | detection | | JSON export |   |
|   | prefs    | |  incident   | |  closure   | |  quality  | | PDF export  |   |
|   |          | |  creation   | |            | | health    | |             |   |
|   |          | |             | |            | |           | |  -( IPdf    |   |
|   | O- IAuth | | O- IDetect  | | O- ICase   | | O-IAnalyt | | O- IReport  |   |
|   +----------+ +-------------+ +------------+ +-----------+ +-------------+   |
|        |             |               |             |              |          |
|        |             | -(IEngine     |             |              | -(IPdf   |
|        |             v               |             |              v          |
|        |   +--------------------------------+      |      +----------------+ |
|        |   |  <<component>>                 |      |      | <<library>>    | |
|        |   |  AI Detection Engine           |      |      | ReportLab      | |
|        |   |--------------------------------|      |      | (OPTIONAL)     | |
|        |   |  +--------------------------+  |      |      +----------------+ |
|        |   |  | Feature Extractor        |  |      |                         |
|        |   |  | 11 raw -> 18 features    |  |      |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  | Rule Bank (7 rules)      |  |      |                         |
|        |   |  | explainable, logarithmic |  |      |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  | Statistical Baseline     |  |      |                         |
|        |   |  | robust z-score, saturating|  |     |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  | ML Classifier (OPTIONAL) |  |      |                         |
|        |   |  | RandomForest +           |  |      |                         |
|        |   |  | IsolationForest          |--+------+---> -( ISklearn         |
|        |   |  +--------------------------+  |      |                         |
|        |   |  +--------------------------+  |      |    +-----------------+  |
|        |   |  | Score Fusion + Severity  |  |      |    | <<library>>     |  |
|        |   |  | + Explanation Assembly   |  |      |    | scikit-learn    |  |
|        |   |  +--------------------------+  |      |    | joblib, NumPy   |  |
|        |   |                                |      |    | (OPTIONAL)      |  |
|        |   |   O- IEngine                   |      |    +-----------------+  |
|        |   +--------------------------------+      |             ^           |
|        |             |                             |             |           |
|        |             | -(IModelStore               |             |           |
|        |             v                             |             |           |
|        |   +--------------------------------+      |             |           |
|        |   | <<artifact store>>             |      |             |           |
|        |   |   ml_model/                    |------+-------------+           |
|        |   |   threat_classifier.joblib     |                                |
|        |   |   isolation_forest.joblib      |    ABSENT -> engine reports    |
|        |   |   feature_scaler.joblib        |    "hybrid-rules" and keeps    |
|        |   |   baseline.json                |    working                     |
|        |   |   metadata.json                |                                |
|        |   +--------------------------------+                                |
|        |                                                                     |
|        +----------------+----------------+----------------+                  |
|                         |                                                    |
|                         v                                                    |
|   +----------------------------------------------------------------------+   |
|   |  <<component>>  Audit Module                        O- IAudit        |   |
|   |  records every state-changing action, committed with the change      |   |
|   +----------------------------------------------------------------------+   |
|                         |                                                    |
|                         | -( IPersistence                                    |
|                         v                                                    |
|   +----------------------------------------------------------------------+   |
|   |  <<component>>  SQLAlchemy ORM Layer             O- IPersistence     |   |
|   |----------------------------------------------------------------------|   |
|   |  10 entity mappings | session and transaction management |            |   |
|   |  parameterised query construction | relationship loading             |   |
|   +----------------------------------------------------------------------+   |
|                         |                                                    |
+=========================|====================================================+
                          |  -( ISql        DB-API / SQL
                          v
+==============================================================================+
|                             DATA TIER                                        |
|   +----------------------------------------------------------------------+   |
|   |  <<database>>  SQLite   (database/cyberguard.db)     O- ISql         |   |
|   |----------------------------------------------------------------------|   |
|   |  users | assets | security_events | detection_results | threats      |   |
|   |  alerts | incidents | threat_indicators | reports | audit_logs       |   |
|   +----------------------------------------------------------------------+   |
+==============================================================================+
```

---

## 2. Component catalogue

| Component | Provided interface | Required interfaces | Source |
|-----------|-------------------|---------------------|--------|
| React Frontend Application | (user interface) | IRestApi | `frontend/src/` |
| API Client | IDataAccess | IRestApi | `frontend/src/services/api.js` |
| Flask REST API | IRestApi | IAuth, IDetect, ICase, IAnalytics, IReport, IAudit | `backend/app/routes/` |
| Authentication Module | IAuth | IPersistence, IAudit | `backend/app/services/auth_service.py`, `utils/security.py` |
| Threat Detection Service | IDetect | IEngine, IPersistence, IAudit | `backend/app/services/detection_service.py` |
| AI Detection Engine | IEngine | IModelStore, ISklearn (optional) | `backend/app/ml/` |
| Incident & Alert Management | ICase | IPersistence, IAudit | `backend/app/services/alert_service.py`, `incident_service.py` |
| Analytics Engine | IAnalytics | IPersistence, IEngine | `backend/app/services/analytics_service.py` |
| Report Generation Module | IReport | IAnalytics, IPersistence, IPdf (optional) | `backend/app/services/report_service.py` |
| Audit Module | IAudit | IPersistence | `backend/app/services/audit_service.py` |
| SQLAlchemy ORM Layer | IPersistence | ISql | `backend/app/models/`, `extensions.py` |
| SQLite Database | ISql | - | `database/cyberguard.db` |
| Model Artifact Store | IModelStore | - | `backend/ml_model/` |

---

## 3. Interface specifications

### IRestApi (Flask REST API -> clients)

| Operation group | Endpoints |
|-----------------|-----------|
| Authentication | `POST /api/auth/login`, `/logout`; `GET /api/auth/me`; `PUT /api/auth/profile`, `/preferences`, `/password` |
| Dashboard | `GET /api/dashboard/stats`, `/activity`, `/threat-level`; `GET /api/analytics` |
| Events | `GET`/`POST /api/events`; `GET /api/events/<id>`; `POST /api/events/analyze`, `/upload`; `GET /api/events/sample`; `DELETE /api/events/<id>` |
| Threats | `GET /api/threats`, `/threats/<id>`; `GET /api/threat-intelligence`; `PUT /api/threat-intelligence/<id>` |
| Alerts | `GET /api/alerts`, `/alerts/<id>`, `/alerts/filters`; `PUT /api/alerts/<id>`; `POST /api/alerts/<id>/escalate` |
| Incidents | `GET`/`POST /api/incidents`; `GET`/`PUT /api/incidents/<id>` |
| Assets | `GET`/`POST /api/assets`; `GET`/`PUT`/`DELETE /api/assets/<id>` |
| Reports | `GET`/`POST /api/reports`, `/reports/generate`, `/reports/preview`; `GET /api/reports/<id>`, `/download`; `DELETE /api/reports/<id>` |
| System | `GET /api/health`, `/api/system/status`, `/api/audit-logs`, `/api` |

**Contract:** every response uses the envelope
`{ "success": bool, "message": str, "data": ..., ["pagination"], ["filters"] }`
and every error uses `{ "success": false, "error": CODE, "message": str, ["details"] }`.

### IEngine (AI Detection Engine)

```python
detect(event: dict, sensitivity: float | None) -> dict
detect_batch(events: list, sensitivity: float | None) -> list
model_info() -> dict
reload() -> dict
```

`detect()` always returns a complete verdict: `classification`, `risk_score`,
`confidence`, `severity`, `is_threat`, `reasons`, `recommended_action`,
`mitre_tactic`, `scores`, `triggered_rules`, `feature_summary`, `model_used`,
`engine_version`, `analysis_time_ms`. It never returns a partial result and never
raises for a well-formed event.

### IDetect (Threat Detection Service)

```python
persist_analysis(cleaned, user, channel, sensitivity, commit, auto_incident) -> bundle
analyze_batch(rows, user, channel, sensitivity) -> summary
analyze_only(payload, sensitivity) -> verdict
```

### ICase (Incident & Alert Management)

```python
alert_service.build_query(args)              alert_service.update_status(a, s, note, user)
alert_service.escalate_to_incident(a, user)  incident_service.create_incident(payload, user)
incident_service.transition(i, status, note, user, resolution_summary)
incident_service.assign(i, user_id, actor)   incident_service.related_events(i, limit)
```

### IAudit (Audit Module)

```python
record(action, description, entity_type, entity_id, user, status, commit) -> AuditLog
recent(limit, user_id, action) -> list[AuditLog]
```

---

## 4. Component interaction for a single analysis request

```
 API Client
    | 1. POST /api/events/analyze  (IRestApi)
    v
 Flask REST API
    | 2. token verification              (IAuth)
    +--------------------------> Authentication Module
    |                                    |
    |                                    v  (IPersistence)
    |                              SQLAlchemy ORM --> SQLite
    |
    | 3. persist_analysis()              (IDetect)
    v
 Threat Detection Service
    | 4. detect()                        (IEngine)
    +--------------------------> AI Detection Engine
    |                                    | 5. load models (IModelStore)
    |                                    +-----> ml_model/  [optional]
    |                                    | 6. score       (ISklearn)
    |                                    +-----> scikit-learn [optional]
    |                                    |
    |                          <---------+ 7. verdict
    |
    | 8. persist event, result, threat, alert, incident   (IPersistence)
    +--------------------------> SQLAlchemy ORM --> SQLite
    |
    | 9. record()                        (IAudit)
    +--------------------------> Audit Module --> SQLAlchemy ORM
    |
    | 10. COMMIT (single transaction covering steps 8 and 9)
    v
 Flask REST API --> API Client --> SOC Console UI
```

---

## 5. Component substitutability

Because each component is reached only through its interface, several can be
replaced without touching the rest of the system:

| Component | Replaceable with | What must change |
|-----------|------------------|-----------------|
| SQLite Database | PostgreSQL, MySQL | `DATABASE_URL` in `.env`. Nothing else - the ORM abstracts the dialect. |
| AI Detection Engine | A different detector | Only that `detect()` keeps its contract. Services, routes and UI are unaffected. |
| ML Classifier sub-component | A different sklearn model | Retrain with `train_model.py`; the feature order in `FEATURE_NAMES` is the only coupling. |
| Report Generation (PDF) | WeasyPrint, wkhtmltopdf | `report_service.to_pdf()` only. The 501 fallback already exists. |
| API Client | fetch instead of axios | `services/api.js` only - no page calls the network directly. |
| Design System | A different component library | `components/ui.jsx` - pages consume the primitives, not raw markup. |

### 5.1 Degradation matrix

| Component unavailable | System behaviour | Verified by |
|----------------------|------------------|-------------|
| scikit-learn / joblib | Engine reports `hybrid-rules`; rules and statistics still score every event | `test_engine_works_without_any_trained_model` |
| `ml_model/` artefacts | Same as above; the Settings page shows "No trained model found" | `test_engine_works_without_any_trained_model` |
| ReportLab | PDF returns 501 with the install command; CSV and JSON unaffected | `test_report_downloads_in_every_format` |
| Flask REST API (not running) | Frontend shows "Backend unavailable" with the start command; the cached session is **kept**, not cleared | `ErrorState` component, `AuthContext` |
| SQLite file missing | `db.create_all()` recreates the schema on start-up; the seed script repopulates it | `seed_database.py` |

This matrix is the concrete basis for the reliability requirement NFR-04: every
optional component has a defined, tested degradation path rather than a crash.
