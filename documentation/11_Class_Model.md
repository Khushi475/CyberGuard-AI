# 11 - Class Model (Object-Oriented Design)

**Project:** CyberGuard AI
**Lab experiment:** 6 - OO design: Class model

---

## 1. Class diagram - domain (entity) classes

```
                    +--------------------------------------+
                    |              <<entity>>              |
                    |                 User                 |
                    +--------------------------------------+
                    | - id : int  {PK}                     |
                    | - full_name : str                    |
                    | - email : str  {unique}              |
                    | - password_hash : str                |
                    | - role : str                         |
                    | - department : str                   |
                    | - is_active : bool                   |
                    | - last_login : datetime              |
                    | - created_at : datetime              |
                    | - notify_email : bool                |
                    | - notify_critical_only : bool        |
                    | - detection_sensitivity : float      |
                    | - theme : str                        |
                    +--------------------------------------+
                    | + set_password(raw : str) : void     |
                    | + check_password(raw : str) : bool   |
                    | + to_dict(include_prefs) : dict      |
                    +--------------------------------------+
                        |1            |1             |1
                        |             |              |
             assigned_to|   generates |    performs  |
                        |0..*         |0..*          |0..*
                        v             v              v
           +------------------+ +-----------+ +--------------+
           |    Incident      | |  Report   | |   AuditLog   |
           +------------------+ +-----------+ +--------------+


 +--------------------------------------+        +----------------------------------+
 |             <<entity>>               |        |           <<entity>>             |
 |               Asset                  |        |         SecurityEvent            |
 +--------------------------------------+        +----------------------------------+
 | - id : int  {PK}                     |1       | - id : int  {PK}                 |
 | - name : str                         |--------| - timestamp : datetime           |
 | - ip_address : str  {indexed}        |  0..*  | - source_ip : str                |
 | - asset_type : str                   |        | - destination_ip : str           |
 | - operating_system : str             | observed - source_port : int             |
 | - location : str                     |   on   | - destination_port : int         |
 | - owner : str                        |        | - protocol : str                 |
 | - criticality : str                  |        | - event_type : str               |
 | - status : str                       |        | - request_count : int            |
 | - risk_level : str                   |        | - failed_login_attempts : int    |
 | - risk_score : int                   |        | - packet_count : int             |
 | - last_seen : datetime               |        | - bytes_transferred : float      |
 +--------------------------------------+        | - connection_duration : float    |
 | + to_dict(include_counts) : dict     |        | - user_agent : str               |
 +--------------------------------------+        | - raw_log : str                  |
                                                 | - source_channel : str           |
                                                 | - processed : bool               |
                                                 | - asset_id : int  {FK}           |
                                                 +----------------------------------+
                                                 | + feature_payload() : dict       |
                                                 | + to_dict(include_detection):dict|
                                                 +----------------------------------+
                                                    |1          |1            |1
                                                    |           |             |
                                              produces|   classified|     raises|
                                                    |1          |0..*         |0..*
                                                    v           v             v
 +-----------------------------------+  +---------------------+  +-------------------------+
 |           <<entity>>              |  |     <<entity>>      |  |      <<entity>>         |
 |        DetectionResult            |  |       Threat        |  |         Alert           |
 +-----------------------------------+  +---------------------+  +-------------------------+
 | - id : int  {PK}                  |  | - id : int  {PK}    |  | - id : int  {PK}        |
 | - event_id : int  {FK, unique}    |  | - event_id : int{FK}|  | - alert_code : str{uniq}|
 | - classification : str            |  | - category : str    |  | - event_id : int  {FK}  |
 | - risk_score : int                |  | - description : str |  | - threat_id : int {FK}  |
 | - confidence : float              |  | - severity : str    |  | - incident_id : int{FK} |
 | - severity : str                  |  | - risk_score : int  |  | - title : str           |
 | - is_threat : bool                |  | - confidence: float |  | - threat_type : str     |
 | - rule_score : float              |  | - source_ip : str   |  | - source_ip : str       |
 | - anomaly_score : float           |  | - destination_ip:str|  | - destination_ip : str  |
 | - ml_score : float                |  | - mitre_tactic : str|  | - severity : str        |
 | - engine_version : str            |  | - indicators_json   |  | - risk_score : int      |
 | - model_used : str                |  | - detected_at       |  | - confidence : float    |
 | - reasons_json : str              |  +---------------------+  | - status : str          |
 | - features_json : str             |  | + indicators : list |  | - description : str     |
 | - recommended_action : str        |  |   {property}        |  | - reasons_json : str    |
 | - analysis_time_ms : float        |  | + to_dict() : dict  |  | - recommended_action:str|
 +-----------------------------------+  +---------------------+  | - notes : str           |
 | + reasons : list  {property}      |         |1                | - created_at, updated_at|
 | + features : dict {property}      |         |                 | - resolved_at           |
 | + to_dict(include_features) : dict|  raises |0..*             +-------------------------+
 +-----------------------------------+         +---------------->| + reasons:list{property}|
                                                                 | + can_transition(a,b)   |
                                                                 |   : bool  {static}      |
                                                                 | + to_dict(incl_event)   |
                                                                 +-------------------------+
                                                                             |0..*
                                                                             |
                                                                     grouped |
                                                                      into   |1
                                                                             v
 +-----------------------------------+                    +----------------------------------+
 |           <<entity>>              |                    |            <<entity>>            |
 |        ThreatIndicator            |                    |            Incident              |
 +-----------------------------------+                    +----------------------------------+
 | - id : int  {PK}                  |                    | - id : int  {PK}                 |
 | - indicator : str                 |                    | - incident_code : str  {unique}  |
 | - indicator_type : str            |                    | - title : str                    |
 | - category : str                  |                    | - description : str              |
 | - risk_level : str                |                    | - threat_type : str              |
 | - confidence : float              |                    | - severity : str                 |
 | - status : str                    |                    | - priority : str                 |
 | - description : str               |                    | - status : str                   |
 | - source_feed : str               |                    | - risk_score : int               |
 | - hit_count : int                 |                    | - source_ip : str                |
 | - is_simulated : bool  {always 1} |                    | - detected_at : datetime         |
 | - first_seen, last_seen           |                    | - contained_at : datetime        |
 +-----------------------------------+                    | - resolved_at : datetime         |
 | + to_dict() : dict                |                    | - resolution_summary : str       |
 +-----------------------------------+                    | - history_json : str             |
                                                          | - assigned_to : int  {FK}        |
 +-----------------------------------+                    +----------------------------------+
 |           <<entity>>              |                    | + history : list  {property}     |
 |             Report                |                    | + append_history(from,to,actor,   |
 +-----------------------------------+                    |     note) : void                 |
 | - id : int  {PK}                  |                    | + can_transition(a, b) : bool    |
 | - report_code : str  {unique}     |                    |     {static}                     |
 | - title : str                     |                    | + allowed_transitions(s) : list  |
 | - report_type : str               |                    |     {static}                     |
 | - period_days : int               |                    | + to_dict(include_alerts) : dict |
 | - period_start, period_end        |                    +----------------------------------+
 | - total_events : int              |
 | - total_threats : int             |                    +----------------------------------+
 | - total_alerts : int              |                    |           <<entity>>             |
 | - total_incidents : int           |                    |            AuditLog              |
 | - content_json : str              |                    +----------------------------------+
 | - generated_by : int  {FK}        |                    | - id : int  {PK}                 |
 +-----------------------------------+                    | - action : str                   |
 | + content : dict  {property}      |                    | - entity_type : str              |
 | + to_dict(include_content) : dict |                    | - entity_id : int                |
 +-----------------------------------+                    | - description : str              |
                                                          | - ip_address : str               |
                                                          | - status : str                   |
                                                          | - user_id : int  {FK}            |
                                                          +----------------------------------+
                                                          | + to_dict() : dict               |
                                                          +----------------------------------+
```

---

## 2. Class diagram - detection engine (boundary and control classes)

```
       +------------------------------------------+
       |              <<control>>                 |
       |             ThreatDetector               |
       +------------------------------------------+
       | - model_dir : Path                       |
       | - sensitivity : float                    |
       | - baseline : StatisticalBaseline         |
       | - _classifier : RandomForestClassifier   |
       | - _iforest : IsolationForest             |
       | - _scaler : StandardScaler               |
       | - _models_loaded : bool                  |
       | - _lock : threading.Lock                 |
       +------------------------------------------+
       | + detect(event, sensitivity) : dict      |
       | + detect_batch(events) : list            |
       | + model_info() : dict                    |
       | + reload() : dict                        |
       | + ml_available : bool  {property}        |
       | - _load_models() : void                  |
       | - _ml_score(features) : tuple            |
       | - _confidence(...) : float  {static}     |
       +------------------------------------------+
            |                |                |
            | uses           | uses           | uses
            v                v                v
 +---------------------+ +------------------------+ +-------------------------+
 |     <<utility>>     | |      <<control>>       | |      <<utility>>        |
 |  features (module)  | |  StatisticalBaseline   | |    rules (module)       |
 +---------------------+ +------------------------+ +-------------------------+
 | + FEATURE_NAMES     | | - stats : dict         | | + RULE_BANK : tuple     |
 |   : list[18]        | | - source : str         | | + RECOMMENDED_ACTIONS   |
 +---------------------+ +------------------------+ | + MITRE_TACTICS         |
 | + extract_features  | | + load(dir) {classmethod}| +-------------------------+
 |   (event) : dict    | | + save(dir) : Path     | | + evaluate_rules(f, e)  |
 | + features_to_vector| | + z_scores(f) : dict   | |   : dict                |
 |   (features) : list | | + score(f) : tuple     | | + rule_brute_force      |
 | + describe_features | | + as_dict() : dict     | | + rule_dos_pattern      |
 |   (features) : dict | +------------------------+ | + rule_data_transfer_*  |
 +---------------------+                            | + rule_port_scanning    |
                                                    | + rule_credential_abuse |
                                                    | + rule_suspicious_login |
                                                    | + rule_network_anomaly  |
                                                    | + recommended_action(c) |
                                                    | + mitre_tactic(c)       |
                                                    +-------------------------+
```

---

## 3. Class diagram - service layer

```
 +--------------------------------------------------------------+
 |                        <<service>>                           |
 |                    detection_service                         |
 +--------------------------------------------------------------+
 | + get_engine() : ThreatDetector                              |
 | + analyze_only(payload, sensitivity) : dict                  |
 | + persist_analysis(cleaned, user, channel, sensitivity,      |
 |       commit, auto_incident) : dict                          |
 | + analyze_batch(rows, user, channel, sensitivity) : dict     |
 | + analysis_to_response(bundle) : dict                        |
 | + resolve_asset(src_ip, dst_ip) : Asset                      |
 | + next_code(prefix, model, column) : str                     |
 +--------------------------------------------------------------+
        |                |                 |               |
        | creates        | creates         | creates       | updates
        v                v                 v               v
   SecurityEvent   DetectionResult    Threat/Alert     Asset
   + Incident

 +---------------------------+   +---------------------------+
 |       <<service>>         |   |       <<service>>         |
 |      alert_service        |   |     incident_service      |
 +---------------------------+   +---------------------------+
 | + build_query(args)       |   | + build_query(args)       |
 | + get_alert(id) : Alert   |   | + get_incident(id)        |
 | + update_status(a, s, n,u)|   | + create_incident(p, u)   |
 | + escalate_to_incident(   |   | + transition(i, s, n, u,  |
 |     a, u, title)          |   |     resolution_summary)   |
 | + alert_filter_options()  |   | + assign(i, uid, actor)   |
 +---------------------------+   | + related_events(i, lim)  |
                                 +---------------------------+

 +---------------------------+   +---------------------------+
 |       <<service>>         |   |       <<service>>         |
 |     analytics_service     |   |      report_service       |
 +---------------------------+   +---------------------------+
 | + dashboard_stats(days)   |   | + build_report_content(   |
 | + threat_level()          |   |     days, type) : dict    |
 | + detection_quality()     |   | + generate_report(days,   |
 | + system_health()         |   |     type, title, user)    |
 | + threats_over_time(d)    |   | + to_csv(report) : str    |
 | + detection_trend(d)      |   | + to_pdf(report) : bytes  |
 | + severity_distribution() |   | - _recommendations(c)     |
 | + category_distribution() |   +---------------------------+
 | + events_by_source()      |
 | + protocol_distribution() |   +---------------------------+
 | + hourly_distribution()   |   |       <<service>>         |
 | + activity_feed(limit)    |   |      audit_service        |
 | + analytics_overview(d)   |   +---------------------------+
 +---------------------------+   | + record(action, desc,    |
                                 |     entity_type, id, user,|
 +---------------------------+   |     status, commit)       |
 |       <<service>>         |   | + recent(limit, uid, act) |
 |       auth_service        |   +---------------------------+
 +---------------------------+
 | + login(email, password)  |
 | + logout(user)            |
 | + update_profile(u, p)    |
 | + update_preferences(u,p) |
 | + change_password(u,c,n)  |
 +---------------------------+
```

---

## 4. Multiplicity summary

| Association | Source | Multiplicity | Target | Multiplicity | Reading |
|-------------|--------|--------------|--------|--------------|---------|
| assigned to | User | 0..1 | Incident | 0..* | An analyst owns zero or more incidents; an incident has at most one owner. |
| performs | User | 0..1 | AuditLog | 0..* | A user performs many audited actions; system actions have no user. |
| generates | User | 0..1 | Report | 0..* | A user generates many reports. |
| observed on | Asset | 0..1 | SecurityEvent | 0..* | An asset appears in many events; an event may match no asset. |
| produces | SecurityEvent | 1 | DetectionResult | **1** | Exactly one verdict per analysed event (unique FK). |
| classified as | SecurityEvent | 1 | Threat | 0..* | A suspicious event yields a threat; a benign one yields none. |
| raises | SecurityEvent | 1 | Alert | 0..* | An event may raise an alert. |
| cites | Threat | 0..1 | Alert | 0..* | An alert cites the threat that produced it. |
| grouped into | Incident | 0..1 | Alert | 0..* | An incident groups the alerts under investigation. |

---

## 5. Design patterns applied

| Pattern | Where | Why |
|---------|-------|-----|
| **Application Factory** | `create_app()` in `app/__init__.py` | Lets the test-suite build an isolated in-memory instance per test module. |
| **Repository (via ORM)** | SQLAlchemy models | Persistence is abstracted; swapping SQLite for PostgreSQL is a URL change. |
| **Service Layer** | `app/services/` | Business rules live in one place; routes stay thin and testable. |
| **Strategy** | The seven rule functions in `rules.py` | Each rule is an interchangeable `(features, event) -> (score, reasons)` function; adding a rule means adding a function and one tuple entry. |
| **Facade** | `ThreatDetector.detect()` | Hides feature extraction, three detectors, fusion, severity mapping and explanation behind one call. |
| **Singleton (per application)** | `app.extensions["cyberguard_detector"]` | Models load once per process rather than per request. |
| **Lazy Initialisation** | `ThreatDetector._load_models()` | ML artefacts load on first use, under a lock, and a load failure degrades to rules mode. |
| **Template Method** | `SerializerMixin.to_dict()` | Every entity honours the same serialisation contract. |
| **State** | `INCIDENT_STATE_TRANSITIONS`, `ALERT_STATUS_TRANSITIONS` | Legal transitions are data, not scattered `if` statements. |
| **Decorator** | `@token_required`, `@role_required` | Access control is declared on the route, not re-implemented inside it. |
| **Data Transfer Object** | The `bundle` dict from `persist_analysis` | Carries the event, verdict and created artefacts to the caller in one object. |

---

## 6. Design principles observed

### 6.1 Single Responsibility

Each module has one reason to change:

| Module | Sole responsibility |
|--------|---------------------|
| `features.py` | Turning an event into numbers |
| `rules.py` | Expressing behavioural knowledge as scores and reasons |
| `anomaly.py` | Statistical deviation from a baseline |
| `detector.py` | Combining detector outputs into one verdict |
| `detection_service.py` | Persisting a verdict and its consequences |
| `validators.py` | Deciding whether input is acceptable |

A concrete benefit: the increment-I7 re-calibration changed only `rules.py`,
`anomaly.py` and `detector.py`. No route, model or page needed editing.

### 6.2 Open/Closed

Adding an eighth detection category requires:

1. A new rule function in `rules.py`.
2. One entry in `RULE_BANK`.
3. One entry in `RECOMMENDED_ACTIONS` and `MITRE_TACTICS`.

No change to the detector, the services, the API or the frontend - the category
flows through as data.

### 6.3 Dependency direction

```
routes  ->  services  ->  models  ->  extensions(db)
   |            |
   |            +------>  ml/  (detector -> rules, anomaly, features)
   |
   +-------->  utils/  (validators, security, responses, errors)
```

Dependencies point strictly inward. `ml/` has **no knowledge of Flask, of the
database or of HTTP** - which is exactly why `test_detection_engine.py` can test
it with no application context at all.

### 6.4 Interface Segregation

`to_dict()` takes optional flags (`include_detection`, `include_alerts`,
`include_features`, `include_content`) so a list endpoint returns a light payload
while a detail endpoint returns the full object, without needing separate DTO
classes.

---

## 7. Class-to-file map

| Class / module | File |
|----------------|------|
| User | `backend/app/models/user.py` |
| Asset | `backend/app/models/asset.py` |
| SecurityEvent | `backend/app/models/security_event.py` |
| DetectionResult | `backend/app/models/detection_result.py` |
| Threat | `backend/app/models/threat.py` |
| Alert | `backend/app/models/alert.py` |
| Incident | `backend/app/models/incident.py` |
| ThreatIndicator | `backend/app/models/threat_indicator.py` |
| Report | `backend/app/models/report.py` |
| AuditLog | `backend/app/models/audit_log.py` |
| SerializerMixin | `backend/app/models/base.py` |
| ThreatDetector | `backend/app/ml/detector.py` |
| StatisticalBaseline | `backend/app/ml/anomaly.py` |
| features (module) | `backend/app/ml/features.py` |
| rules (module) | `backend/app/ml/rules.py` |
| All services | `backend/app/services/*.py` |
| ApiError hierarchy | `backend/app/utils/errors.py` |
