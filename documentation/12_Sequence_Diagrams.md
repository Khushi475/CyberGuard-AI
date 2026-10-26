# 12 - Sequence Diagrams (Interaction Modelling)

**Project:** CyberGuard AI
**Lab experiment:** 7 - OO design: Interaction models

---

## Sequence 1 - User Login (FR-01, UC-01)

```
 Analyst    Login.jsx   AuthContext   api.js    Flask    auth_service   User    AuditLog   DB
    |           |            |           |        |           |          |         |       |
    |--enter--->|            |           |        |           |          |         |       |
    | creds     |            |           |        |           |          |         |       |
    |           |--validate--|           |        |           |          |         |       |
    |           |  (format)  |           |        |           |          |         |       |
    |           |--login()-->|           |        |           |          |         |       |
    |           |            |--post---->|        |           |          |         |       |
    |           |            | /auth/    |--POST->|           |          |         |       |
    |           |            |  login    |        |--login()->|          |         |       |
    |           |            |           |        |           |--query-->|         |       |
    |           |            |           |        |           |          |--SELECT-------->|
    |           |            |           |        |           |          |<--row-----------|
    |           |            |           |        |           |<--user---|         |       |
    |           |            |           |        |           |          |         |       |
    |           |            |           |        |    check_password()  |         |       |
    |           |            |           |        |    (PBKDF2 verify)   |         |       |
    |           |            |           |        |           |          |         |       |
    |           |            |           |        |    [password OK]     |         |       |
    |           |            |           |        |           |--set last_login--->|       |
    |           |            |           |        |           |--record LOGIN_SUCCESS----->|
    |           |            |           |        |           |          |         |--INS->|
    |           |            |           |        |           |--generate_token()  |       |
    |           |            |           |        |           |  (itsdangerous,    |       |
    |           |            |           |        |           |   signed + expiry) |       |
    |           |            |           |        |           |--commit()----------------->|
    |           |            |           |        |<--{token, |          |         |       |
    |           |            |           |        |    user}--|          |         |       |
    |           |            |           |<--200--|           |          |         |       |
    |           |            |<--result--|        |           |          |         |       |
    |           |            |                    |           |          |         |       |
    |           |     tokenStore.set(token, remember)         |          |         |       |
    |           |     userStore.set(user, remember)           |          |         |       |
    |           |     setUser(user)                           |          |         |       |
    |           |<--user-----|                                |          |         |       |
    |           |                                             |          |         |       |
    |           |--toast.success("Welcome back")              |          |         |       |
    |           |--navigate("/dashboard")                     |          |         |       |
    |<--SOC-----|                                             |          |         |       |
    | dashboard |                                             |          |         |       |

  ALTERNATE FLOW  [password wrong OR account unknown]
    |           |            |           |        |--record LOGIN_FAILED (status=FAILURE)->|
    |           |            |           |        |--commit()-------------------------->   |
    |           |            |           |<--401--|  AuthError("Invalid email address or   |
    |           |            |           |        |             password.")                |
    |           |            |<--ApiError|        |  (identical message for both cases,    |
    |           |<--throw----|           |        |   so account existence is not leaked)  |
    |<--inline--|                                 |                                        |
    |  error    |                                 |                                        |

  ALTERNATE FLOW  [backend not running]
    |           |            |           |--no response--                                  |
    |           |            |           |  axios interceptor -> ApiError(BACKEND_UNAVAILABLE)
    |<--"Cannot reach the CyberGuard AI backend. Start it with python run.py"--------------|
```

---

## Sequence 2 - Security Event Analysis (FR-04, UC-04)

This is the system's central interaction.

```
Analyst  ThreatDetection  api.js  events.py  validators  detection_service  ThreatDetector  DB
   |          |             |        |           |              |                |          |
   |--fill--->|             |        |           |              |                |          |
   | form     |             |        |           |              |                |          |
   |--click-->|             |        |           |              |                |          |
   | Analyze  |             |        |           |              |                |          |
   |          |--validate-->|        |           |              |                |          |
   |          | (client)    |        |           |              |                |          |
   |          |--analyzeEvent()----->|           |              |                |          |
   |          |             |--POST->|           |              |                |          |
   |          |             | /events/analyze    |              |                |          |
   |          |             |        |--token_required()------->|                |          |
   |          |             |        |  (decode, load user)     |                |          |
   |          |             |        |--validate_event_payload->|                |          |
   |          |             |        |           |--IP format   |                |          |
   |          |             |        |           |--port range  |                |          |
   |          |             |        |           |--protocol    |                |          |
   |          |             |        |           |--numeric     |                |          |
   |          |             |        |<--cleaned-|              |                |          |
   |          |             |        |                          |                |          |
   |          |             |        |--persist_analysis(cleaned, user)--------->|          |
   |          |             |        |           |              |                |          |
   |          |             |        |           |     resolve_asset(src, dst)   |          |
   |          |             |        |           |              |--SELECT asset WHERE ip IN>|
   |          |             |        |           |              |<--asset or None-----------|
   |          |             |        |           |              |                |          |
   |          |             |        |           |     INSERT SecurityEvent      |          |
   |          |             |        |           |              |--flush() (get id)-------->|
   |          |             |        |           |              |                |          |
   |          |             |        |           |              |--detect(payload)->|       |
   |          |             |        |           |              |                |          |
   |          |             |        |           |     +--------------------------------+   |
   |          |             |        |           |     | 1. extract_features -> 18 vals |   |
   |          |             |        |           |     | 2. evaluate_rules   -> cat,    |   |
   |          |             |        |           |     |    score, reasons              |   |
   |          |             |        |           |     | 3. baseline.score   -> anomaly |   |
   |          |             |        |           |     | 4. _ml_score        -> ml      |   |
   |          |             |        |           |     |    (skipped if no artefacts)   |   |
   |          |             |        |           |     | 5. fuse:                       |   |
   |          |             |        |           |     |    weighted = .58r+.18a+.24m   |   |
   |          |             |        |           |     |    risk = max(weighted,        |   |
   |          |             |        |           |     |            0.85*rule)*sens     |   |
   |          |             |        |           |     | 6. severity band               |   |
   |          |             |        |           |     | 7. confidence                  |   |
   |          |             |        |           |     | 8. assemble reasons + action   |   |
   |          |             |        |           |     +--------------------------------+   |
   |          |             |        |           |              |<--verdict------|          |
   |          |             |        |           |              |                |          |
   |          |             |        |           |     INSERT DetectionResult    |--INSERT->|
   |          |             |        |           |     event.processed = True    |          |
   |          |             |        |           |              |                |          |
   |          |             |        |   [is_threat]            |                |          |
   |          |             |        |           |     INSERT Threat             |--INSERT->|
   |          |             |        |           |              |                |          |
   |          |             |        |   [risk >= 26]           |                |          |
   |          |             |        |           |     next_code("ALT") ->       |          |
   |          |             |        |           |     INSERT Alert (status NEW) |--INSERT->|
   |          |             |        |           |              |                |          |
   |          |             |        |   [risk >= 76]           |                |          |
   |          |             |        |           |     next_code("INC") ->       |          |
   |          |             |        |           |     INSERT Incident (NEW)     |--INSERT->|
   |          |             |        |           |     alert.incident_id = inc.id|          |
   |          |             |        |           |              |                |          |
   |          |             |        |           |     _update_asset_risk(asset) |--UPDATE->|
   |          |             |        |           |              |                |          |
   |          |             |        |           |     audit("EVENT_ANALYSED")   |--INSERT->|
   |          |             |        |           |     COMMIT (single txn)       |--COMMIT->|
   |          |             |        |<--bundle--|              |                |          |
   |          |             |        |                                                      |
   |          |             |        |--analysis_to_response(bundle)                        |
   |          |             |<--200--|                                                      |
   |          |<--verdict---|                                                               |
   |          |                                                                             |
   |          |--render ScoreRing(risk, severity)                                           |
   |          |--render reasons list                                                        |
   |          |--render sub-score bars (rule / statistical / ML)                            |
   |          |--render recommended action                                                  |
   |          |--render links to the created alert and incident                             |
   |<--result-|                                                                             |
   | + toast  |                                                                             |

  ALTERNATE FLOW  [validation fails]
   |          |             |        |<--ValidationError(field)-|                |          |
   |          |             |<--422--|  {"error":"VALIDATION_ERROR",                        |
   |          |             |        |   "details":{"field":"source_ip"}}                   |
   |          |<--ApiError--|                                                               |
   |<--field--|  the offending input is highlighted and every problem listed                |
   |  error   |                                                                             |

  ALTERNATE FLOW  [persist=false, dry run]
   |          |             |        |--analyze_only(cleaned)-->|--detect()----->|          |
   |          |             |        |<--verdict (nothing written to the database)          |
   |          |<--{persisted:false}--|                                                      |
```

---

## Sequence 3 - CSV Log Upload (FR-10, UC-05)

```
Analyst  LogAnalyzer  api.js  events.py  csv_parser  detection_service  ThreatDetector  DB
   |         |          |        |           |              |                |           |
   |--drop-->|          |        |           |              |                |           |
   | file    |          |        |           |              |                |           |
   |         |--check extension + size (client-side guard)  |                |           |
   |--click->|          |        |           |              |                |           |
   | Analyze |          |        |           |              |                |           |
   |         |--uploadLogs(file, onProgress)  |             |                |           |
   |         |          |--POST->|           |              |                |           |
   |         |          | multipart          |              |                |           |
   |         |<--progress events (10%..100%) |              |                |           |
   |         |          |        |--validate_upload()------>|                |           |
   |         |          |        |           | extension in {.csv,.txt,.log}?|           |
   |         |          |        |--decode_file()---------->|                |           |
   |         |          |        |           | utf-8-sig -> utf-8 -> latin-1 |           |
   |         |          |        |--parse_csv(text, max=5000)|               |           |
   |         |          |        |           |                               |           |
   |         |          |        |           |  sniff delimiter              |           |
   |         |          |        |           |  normalise header aliases     |           |
   |         |          |        |           |  require source_ip            |           |
   |         |          |        |           |                               |           |
   |         |          |        |           |  loop over rows:              |           |
   |         |          |        |           |    try validate_event_payload |           |
   |         |          |        |           |      -> valid_rows.append()   |           |
   |         |          |        |           |    except ValidationError     |           |
   |         |          |        |           |      -> row_errors.append(    |           |
   |         |          |        |           |           {row, reason})      |           |
   |         |          |        |           |         and CONTINUE          |           |
   |         |          |        |<--(valid_rows, row_errors)                |           |
   |         |          |        |                                           |           |
   |         |          |        |--analyze_batch(valid_rows, user, "csv")-->|           |
   |         |          |        |           |              |                |           |
   |         |          |        |           |   loop over valid_rows:       |           |
   |         |          |        |           |     persist_analysis(row,     |           |
   |         |          |        |           |        commit=False)          |           |
   |         |          |        |           |              |--detect()----->|           |
   |         |          |        |           |              |<--verdict------|           |
   |         |          |        |           |              |--INSERT event + result----->|
   |         |          |        |           |              |--INSERT threat/alert/inc--->|
   |         |          |        |           |              |  (per thresholds)           |
   |         |          |        |           |              |  tally severity counters    |
   |         |          |        |           |              |                |           |
   |         |          |        |           |   audit("LOG_UPLOAD_ANALYSED")|           |
   |         |          |        |           |   COMMIT  <-- ONE transaction for the      |
   |         |          |        |           |               entire file                  |
   |         |          |        |<--summary-|              |                |           |
   |         |          |<--201--|                                                       |
   |         |<--summary|                                                                |
   |         |                                                                           |
   |         |--render 5 KPI tiles (total / normal / suspicious / high / critical)       |
   |         |--render severity band breakdown                                           |
   |         |--render category + top-source charts                                      |
   |         |--render rejected rows with line numbers and reasons                       |
   |         |--render filterable per-record results table                               |
   |<--result|                                                                           |
   | + toast |                                                                           |

  NOTE: a malformed row is reported, never fatal. A 4-row file with 2 bad rows
        returns HTTP 201 with total_records=2 and rejected_rows=2.
```

---

## Sequence 4 - Threat Detection Internals (FR-05, UC-06)

```
detection_service   ThreatDetector   features   rules   StatisticalBaseline   joblib models
        |                  |            |         |             |                   |
        |--detect(event)-->|            |         |             |                   |
        |                  |            |         |             |                   |
        |                  |--extract_features(event)->|        |                   |
        |                  |            |  11 raw -> 18 features|                   |
        |                  |<--features-|         |             |                   |
        |                  |                      |             |                   |
        |                  |--evaluate_rules(features, event)-->|                   |
        |                  |            |         |             |                   |
        |                  |            |    R1 brute force  -> (score, reasons)     |
        |                  |            |    R2 DoS          -> (score, reasons)     |
        |                  |            |    R3 data transfer-> (score, reasons)     |
        |                  |            |    R4 port scan    -> (score, reasons)     |
        |                  |            |    R5 cred abuse   -> (score, reasons)     |
        |                  |            |    R6 susp. login  -> (score, reasons)     |
        |                  |            |    R7 net anomaly  -> (score, reasons)     |
        |                  |            |                                            |
        |                  |            |    sort by score desc                      |
        |                  |            |    winner = triggered[0]                   |
        |                  |            |    others -> "Secondary indicator - ..."   |
        |                  |<--{category, score, reasons, triggered}-----------------|
        |                  |                      |             |                   |
        |                  |--score(features)------------------>|                   |
        |                  |            |         |     z = (x - mean) / std         |
        |                  |            |         |     keep z > 2.0                 |
        |                  |            |         |     c = 1.0*z1 + .45*z2 + .25*z3 |
        |                  |            |         |     score = 100*(1 - e^(-c/9))   |
        |                  |<--(anomaly_score, reasons)---------|                   |
        |                  |                      |             |                   |
        |                  |--_load_models() (once, under lock)------------------->  |
        |                  |            |         |             |                   |
        |                  |  [artefacts present]               |                   |
        |                  |--_ml_score(features)-------------------------------->  |
        |                  |            |         |     scaler.transform(vector)     |
        |                  |            |         |     clf.predict_proba -> p*100   |
        |                  |            |         |     iforest.decision_function    |
        |                  |            |         |        -> outlier score          |
        |                  |<--(max(scores), reasons, True)---------------------->   |
        |                  |                                                        |
        |                  |  [artefacts missing OR load raised]                     |
        |                  |<--(0.0, [], False)   -> engine continues in             |
        |                  |                         "hybrid-rules" mode             |
        |                  |                                                        |
        |                  |  FUSE                                                  |
        |                  |    ml_used  : weighted = .58r + .18a + .24m             |
        |                  |    else     : weighted = .74r + .26a                    |
        |                  |    risk = clamp(max(weighted, 0.85*rule) * sensitivity) |
        |                  |                                                        |
        |                  |  SEVERITY                                              |
        |                  |    0-25 LOW | 26-50 MEDIUM | 51-75 HIGH | 76-100 CRIT   |
        |                  |    if category == Normal and risk >= 26:                |
        |                  |        category = "Network Anomaly"                     |
        |                  |    is_threat = risk >= 26 and category != Normal        |
        |                  |                                                        |
        |                  |  CONFIDENCE                                            |
        |                  |    agreement = 1 - (max-min)/100 across active scores   |
        |                  |    threat : .55 + .32*(risk/100) + .13*agreement        |
        |                  |    benign : .60 + .35*(1 - risk/100)                    |
        |                  |    clamp to [0.50, 0.99]                                |
        |                  |                                                        |
        |                  |  EXPLAIN                                               |
        |                  |    reasons = winner + secondary + statistical + ML      |
        |                  |    de-duplicate, cap at 8                               |
        |                  |    + recommended_action(category)                       |
        |                  |    + mitre_tactic(category)                             |
        |                  |    + analysis_time_ms                                   |
        |<--verdict--------|                                                        |
```

---

## Sequence 5 - Alert Investigation (FR-06, UC-07)

```
Analyst   Alerts.jsx   api.js   alerts.py   alert_service   Alert   AuditLog   DB
   |          |          |         |             |            |         |       |
   |--open--->|          |         |             |            |         |       |
   | Alerts   |          |         |             |            |         |       |
   |          |--listAlerts(params)|             |            |         |       |
   |          |          |--GET--->|             |            |         |       |
   |          |          |         |--build_query(args)------>|         |       |
   |          |          |         |   severity / status / type / date / search  |
   |          |          |         |   sort + offset/limit    |         |       |
   |          |          |         |             |--SELECT ... WHERE ... LIMIT-->|
   |          |          |         |<--rows + total-----------|         |       |
   |          |          |<--200---|  {data, pagination, filters}       |       |
   |          |<--queue--|         |             |            |         |       |
   |<--table--|          |         |             |            |         |       |
   |          |          |         |             |            |         |       |
   |--click-->|          |         |             |            |         |       |
   | alert    |--getAlert(id)----->|             |            |         |       |
   |          |          |--GET--->|--get_alert()|            |         |       |
   |          |          |         |             |--SELECT with event + incident->|
   |          |          |<--200---|             |            |         |       |
   |          |<--detail-|         |             |            |         |       |
   |<--modal--|  severity, risk bar, reasons, telemetry, recommended action      |
   |          |          |         |             |            |         |       |
   |--choose->|          |         |             |            |         |       |
   | action + |          |         |             |            |         |       |
   | note     |--updateAlert(id, {action, note}) |            |         |       |
   |          |          |--PUT--->|             |            |         |       |
   |          |          |         |  map action -> status    |         |       |
   |          |          |         |--update_status(a,s,n,u)->|         |       |
   |          |          |         |             |            |         |       |
   |          |          |         |   status in ALERT_STATUSES?  else 422       |
   |          |          |         |   can_transition(cur, new)?  else 409       |
   |          |          |         |             |            |         |       |
   |          |          |         |   alert.status = new     |         |       |
   |          |          |         |   append "[ts] Analyst: note"      |       |
   |          |          |         |   if terminal: resolved_at = now   |       |
   |          |          |         |--audit("ALERT_STATUS_CHANGED")---->|       |
   |          |          |         |--commit()--------------------------------->|
   |          |          |<--200---|             |            |         |       |
   |          |<--updated|         |             |            |         |       |
   |          |--refresh queue (quiet)           |            |         |       |
   |<--toast--|          |         |             |            |         |       |

  ESCALATION PATH
   |--click Escalate---->|--escalateAlert(id)--->|            |         |       |
   |          |          |--POST-->|--escalate_to_incident()->|         |       |
   |          |          |         |             |            |         |       |
   |          |          |         |  [alert.incident_id set] |         |       |
   |          |          |         |     -> return the EXISTING incident (idempotent)
   |          |          |         |  [else]                  |         |       |
   |          |          |         |     -> INSERT Incident (status INVESTIGATING)
   |          |          |         |        alert.incident_id = inc.id  |       |
   |          |          |         |        alert.status = INVESTIGATING|       |
   |          |          |         |--audit("ALERT_ESCALATED")--------->|       |
   |          |          |<--201---|             |            |         |       |
   |          |--navigate(/incidents/:id)        |            |         |       |
   |<--incident details---|         |             |            |         |       |
```

---

## Sequence 6 - Incident Resolution (FR-07, UC-09)

```
Analyst  IncidentDetails  api.js  incidents.py  incident_service  Incident  Alert  DB
   |          |             |         |              |               |        |     |
   |--open--->|             |         |              |               |        |     |
   |          |--getIncident(id)----->|              |               |        |     |
   |          |             |--GET--->|--get_incident()               |        |     |
   |          |             |         |--related_events()             |        |     |
   |          |             |         |  state_machine = {            |        |     |
   |          |             |         |    current: status,           |        |     |
   |          |             |         |    allowed: allowed_transitions(status)|     |
   |          |             |         |  }            |               |        |     |
   |          |             |<--200---|              |               |        |     |
   |          |<--incident--|         |              |               |        |     |
   |          |                                                                     |
   |          |--render LifecycleTracker(current)                                   |
   |          |--render ONLY the buttons in state_machine.allowed                   |
   |<--page---|  (the UI cannot offer an illegal transition)                        |
   |          |                                                                     |
   |--click-->|             |         |              |               |        |     |
   | Contain  |--open TransitionModal (note + resolution summary if terminal)       |
   |--confirm>|             |         |              |               |        |     |
   |          |--updateIncident(id, {status, note})  |               |        |     |
   |          |             |--PUT--->|              |               |        |     |
   |          |             |         |--transition(i, "CONTAINED", note, user)->   |
   |          |             |         |              |               |        |     |
   |          |             |         |   status in INCIDENT_STATUSES?   else 422   |
   |          |             |         |   can_transition(cur, new)?      else 409   |
   |          |             |         |              |               |        |     |
   |          |             |         |   incident.status = CONTAINED |        |     |
   |          |             |         |   incident.contained_at = now |        |     |
   |          |             |         |   append_history(from,to,actor,note)   |     |
   |          |             |         |--audit("INCIDENT_STATUS_CHANGED")----------->|
   |          |             |         |--commit()----------------------------------->|
   |          |             |<--200---|              |               |        |     |
   |          |<--updated---|         |              |               |        |     |
   |<--tracker advances-----|         |              |               |        |     |
   |          |                                                                     |
   |--click-->|             |         |              |               |        |     |
   | Resolve  |--confirm with resolution summary     |               |        |     |
   |          |--updateIncident(id, {status:"RESOLVED", resolution_summary})        |
   |          |             |--PUT--->|--transition(i, "RESOLVED", ...)->            |
   |          |             |         |              |               |        |     |
   |          |             |         |   can_transition(CONTAINED, RESOLVED) = true |
   |          |             |         |   incident.resolved_at = now  |        |     |
   |          |             |         |   incident.resolution_summary = ...    |     |
   |          |             |         |   append_history(...)         |        |     |
   |          |             |         |                               |        |     |
   |          |             |         |   CASCADE: for each linked alert:      |     |
   |          |             |         |      if not already terminal: |        |     |
   |          |             |         |         alert.status = RESOLVED------->|     |
   |          |             |         |         alert.resolved_at = now        |     |
   |          |             |         |--audit("INCIDENT_STATUS_CHANGED")----------->|
   |          |             |         |--commit()----------------------------------->|
   |          |             |<--200---|              |               |        |     |
   |          |<--resolved--|         |              |               |        |     |
   |          |                                                                     |
   |          |--LifecycleTracker shows the path complete                           |
   |          |--history timeline gains a fourth entry                              |
   |          |--the resolved alerts now feed the detection-precision figure        |
   |<--done---|  on the dashboard                                                   |
   | + toast  |                                                                     |

  ALTERNATE FLOW  [illegal transition attempted, e.g. NEW -> RESOLVED]
   |          |             |<--409---|  {"error":"CONFLICT",                       |
   |          |             |         |   "message":"Invalid lifecycle transition:  |
   |          |             |         |      NEW -> RESOLVED. Allowed from NEW:     |
   |          |             |         |      FALSE_POSITIVE, INVESTIGATING, OPEN.", |
   |          |             |         |   "details":{current, requested, allowed}}  |
   |<--toast--|  In practice this is unreachable from the UI, because the page only |
   |  error   |  renders the allowed buttons. The guard exists because the API is   |
   |          |  the authority, not the UI.                                         |
```

---

## Sequence 7 - Report Generation (FR-11, UC-12)

```
Analyst  Reports.jsx  api.js  reports.py  report_service  analytics_service  ReportLab  DB
   |         |          |         |            |                |               |       |
   |--choose>|          |         |            |                |               |       |
   | period, |          |         |            |                |               |       |
   | type    |          |         |            |                |               |       |
   |--click->|          |         |            |                |               |       |
   | Generate|--generateReport({days, type, title})             |               |       |
   |         |          |--POST-->|            |                |               |       |
   |         |          |         |--generate_report(days, type, title, user)-> |       |
   |         |          |         |            |                |               |       |
   |         |          |         |   validate days in 1..365   |               |       |
   |         |          |         |   validate type in REPORT_TYPES             |       |
   |         |          |         |            |                |               |       |
   |         |          |         |            |--build_report_content(days)--->|       |
   |         |          |         |            |                |               |       |
   |         |          |         |            |   count events / threats / alerts /    |
   |         |          |         |            |   incidents in the period     |--SELECT>|
   |         |          |         |            |--severity_distribution()----->|--SELECT>|
   |         |          |         |            |--category_distribution()----->|--SELECT>|
   |         |          |         |            |--detection_quality()--------->|--SELECT>|
   |         |          |         |            |--events_by_source()---------->|--SELECT>|
   |         |          |         |            |   at-risk assets              |--SELECT>|
   |         |          |         |            |--threat_level()-------------->|--SELECT>|
   |         |          |         |            |<--content------|               |       |
   |         |          |         |            |                                        |
   |         |          |         |            |--_recommendations(content)             |
   |         |          |         |            |   CONDITIONAL on measured values:      |
   |         |          |         |            |     critical > 0      -> review each   |
   |         |          |         |            |     brute force > 0   -> MFA + lockout |
   |         |          |         |            |     port scan > 0     -> firewall audit|
   |         |          |         |            |     exfiltration > 0  -> egress limits |
   |         |          |         |            |     open incidents>0  -> assign owners |
   |         |          |         |            |     FP > resolved     -> lower         |
   |         |          |         |            |                          sensitivity   |
   |         |          |         |            |     none of the above -> "no elevated  |
   |         |          |         |            |                          activity"     |
   |         |          |         |            |   + always: academic-prototype caveat  |
   |         |          |         |            |                                        |
   |         |          |         |   next_code("RPT") -> RPT-000001                    |
   |         |          |         |   INSERT Report (content stored as JSON)---------->|
   |         |          |         |   audit("REPORT_GENERATED")---------------------->|
   |         |          |         |   commit()--------------------------------------->|
   |         |          |<--201---|            |                                       |
   |         |<--report-|         |            |                                       |
   |<--modal-|  full report rendered inline with charts                                |
   |         |                                                                         |
   |--click->|          |         |            |                                       |
   | PDF     |--downloadReport(id, "pdf")      |                                       |
   |         |          |--GET--->|            |                                       |
   |         |          | ?format=pdf          |                                       |
   |         |          |         |--audit("REPORT_DOWNLOADED")-------------------->   |
   |         |          |         |--to_pdf(report)------------>|                      |
   |         |          |         |            |                |--SimpleDocTemplate--> |
   |         |          |         |            |                |  7 sections, styled   |
   |         |          |         |            |                |  tables, A4           |
   |         |          |         |            |<--PDF bytes----|                      |
   |         |          |<--200---|  Content-Disposition: attachment                   |
   |         |          |  application/pdf                                             |
   |         |<--blob---|                                                              |
   |         |--saveBlob() -> browser download                                         |
   |<--file--|                                                                         |

  ALTERNATE FLOW  [ReportLab not installed]
   |         |          |         |--to_pdf() raises ImportError                       |
   |         |          |<--501---|  {"message":"PDF export needs ReportLab. Install   |
   |         |          |         |    it with 'pip install reportlab', or download    |
   |         |          |         |    the CSV/JSON version instead.",                 |
   |         |          |         |   "data":{"available_formats":["json","csv"]}}     |
   |<--toast-|  CSV and JSON downloads continue to work                                |
```

---

## 8. Cross-cutting interaction: authentication on every protected call

```
   any page      api.js (interceptor)      Flask route      security.py
      |                  |                      |                |
      |--api.method()--->|                      |                |
      |                  |--attach header:      |                |
      |                  |  Authorization:      |                |
      |                  |  Bearer <token>      |                |
      |                  |--------------------->|                |
      |                  |                      |--token_required()->|
      |                  |                      |                |--_extract_token()
      |                  |                      |                |--decode_token()
      |                  |                      |                |  (signature + expiry)
      |                  |                      |                |--User.query.get(uid)
      |                  |                      |                |--check is_active
      |                  |                      |<--g.current_user|
      |                  |                      |                |
      |                  |                      |-- route body runs --
      |                  |<--200----------------|                |
      |<--data-----------|                      |                |

   TOKEN EXPIRED OR FORGED
      |                  |<--401 TOKEN_EXPIRED / TOKEN_INVALID   |
      |                  |--onUnauthorized() -> tokenStore.clear()
      |                  |                   -> setUser(null)
      |<--redirected to /login ------------------------------------
```
