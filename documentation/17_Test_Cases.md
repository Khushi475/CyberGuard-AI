# 17 - Test Case Design

**Project:** CyberGuard AI
**Lab experiment:** 9 - Design and demonstration of test cases

---

## 1. Test strategy

| Level | Scope | Technique | Where |
|-------|-------|-----------|-------|
| Unit | Detection engine in isolation (no database, no HTTP) | Equivalence partitioning, boundary value analysis, property testing | `tests/test_detection_engine.py` |
| Integration | API endpoint through service, model and database | Black-box API testing against the documented contract | `tests/test_events.py`, `test_alerts_incidents.py`, `test_assets_dashboard.py` |
| Security | Authentication, authorisation, input validation | Negative testing, error-path testing | `tests/test_auth.py`, validation cases throughout |
| System | End-to-end workflows through the running stack | Scenario walkthrough | Document 18 |
| Non-functional | Performance, reliability, usability, maintainability | Measurement and procedure | Document 19 |

**Test design techniques applied**

- **Equivalence partitioning** - inputs split into valid and invalid classes
  (valid IP / malformed IP; port in range / out of range; known protocol /
  unknown protocol).
- **Boundary value analysis** - the severity bands are tested exactly at 0, 25,
  26, 50, 51, 75, 76 and 100.
- **State transition testing** - every legal incident transition is exercised,
  and representative illegal ones are confirmed to be refused.
- **Error guessing** - empty file, header-only file, wrong extension, forged
  token, duplicate IP address.
- **Property-based assertions** - monotonicity of risk with attack intensity,
  score always within 0-100, every verdict carries a reason.

---

## 2. Test case catalogue

Format: **TC-nn** groups map to the twelve areas required by the lab brief.
"Automated by" names the executing test function.

---

### TC-01 - Login (FR-01)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-01.1 | Valid credentials | `admin@test.local` / `admin123` | 200; token returned; user profile without any password field | `test_login_with_valid_credentials_returns_token` |
| TC-01.2 | Wrong password | valid email, wrong password | 401 `INVALID_CREDENTIALS` | `test_login_with_wrong_password_is_rejected` |
| TC-01.3 | Unknown account | `nobody@test.local` | 401 with a message **identical** to TC-01.2 | `test_login_with_unknown_email_gives_the_same_message` |
| TC-01.4 | Malformed email | `not-an-email` | 422 `VALIDATION_ERROR` | `test_login_with_malformed_email_is_a_validation_error` |
| TC-01.5 | Missing password | email only | 422 naming the password field | `test_login_requires_a_password` |
| TC-01.6 | Deactivated account | `disabled@test.local` | 401 `ACCOUNT_DISABLED` | `test_disabled_account_cannot_sign_in` |
| TC-01.7 | Successful login is audited | valid login | `LOGIN_SUCCESS` entry exists | `test_logout_is_recorded` |
| TC-01.8 | Failed login is audited | wrong password | `LOGIN_FAILED` entry with status FAILURE | `test_failed_login_is_audited` |
| TC-01.9 | Profile retrieval | valid token | 200 with profile and preferences | `test_me_returns_the_signed_in_profile` |
| TC-01.10 | Password change round-trip | correct current password + new password | 200, and the new password then authenticates | `test_password_change_succeeds_and_the_new_password_works` |
| TC-01.11 | Password change with wrong current | wrong current password | 401 | `test_password_change_requires_the_current_password` |
| TC-01.12 | Out-of-range sensitivity | `detection_sensitivity = 9.0` | 422 | `test_preferences_reject_an_out_of_range_sensitivity` |

---

### TC-02 - Dashboard API (FR-02)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-02.1 | All sections present | `GET /api/dashboard/stats` | 200 with totals, threat_level, detection_quality, system_health, charts, recent_alerts, activity_feed | `test_dashboard_stats_returns_every_section` |
| TC-02.2 | Totals reconcile with list endpoints | dashboard vs `/events` and `/assets` | totals match exactly - proving nothing is hard-coded | `test_dashboard_totals_are_computed_from_the_database` |
| TC-02.3 | All six chart series present | dashboard charts | each series exists and is a list; severity chart has all four bands | `test_dashboard_charts_have_the_expected_series` |
| TC-02.4 | Threat level is valid | `GET /api/dashboard/threat-level` | level in {LOW, MEDIUM, HIGH, CRITICAL}; score 0-100; basis stated | `test_threat_level_is_one_of_the_four_bands` |
| TC-02.5 | Accuracy figure is qualified | detection_quality | `source`, `label` and `note` always present | `test_detection_quality_states_where_the_number_came_from` |
| TC-02.6 | Activity feed ordering | `GET /api/dashboard/activity` | strictly newest-first | `test_activity_feed_is_newest_first` |
| TC-02.7 | Analytics aggregates | `GET /api/analytics?days=30` | averages, distributions, 24 hourly buckets | `test_analytics_endpoint_returns_aggregates` |
| TC-02.8 | Requires authentication | no token | 401 | `test_dashboard_requires_authentication` |

---

### TC-03 - Event Creation (FR-03)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-03.1 | Valid event stored and analysed | normal HTTPS event | 201; `processed = true`; classification returned | `test_create_event_stores_and_analyses_it` |
| TC-03.2 | Event linked to its asset | event whose destination IP is a known asset | `asset_id` set, `asset_name` populated | `test_event_is_linked_to_a_monitored_asset` |
| TC-03.3 | Event listing paginates | `?per_page=2` | at most 2 rows; pagination metadata correct | `test_list_events_is_paginated` |
| TC-03.4 | Event deletion cascades | delete an event | 200, then 404 on re-fetch | `test_event_can_be_deleted` |
| TC-03.5 | Unknown event | `GET /api/events/999999` | 404 `NOT_FOUND` | `test_unknown_event_returns_404` |

---

### TC-04 - Event Analysis (FR-04)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-04.1 | Full explainable verdict | brute-force payload | 200 with classification, severity, risk 0-100, reasons, recommended action | `test_analyze_returns_a_full_explainable_verdict` |
| TC-04.2 | Alert raised for a threat | brute-force payload | alert created; alert count increases by exactly 1 | `test_analyze_raises_an_alert_for_a_threat` |
| TC-04.3 | No alert for benign traffic | normal payload | `alert` is null; alert count unchanged | `test_analyze_does_not_raise_an_alert_for_normal_traffic` |
| TC-04.4 | Critical detection opens an incident | 400 failed logins | severity CRITICAL; incident created in NEW | `test_critical_detection_opens_an_incident` |
| TC-04.5 | Dry run stores nothing | `?persist=false` | `persisted: false`; event count unchanged | `test_dry_run_analysis_stores_nothing` |
| TC-04.6 | Sample payloads available | `GET /api/events/sample` | at least 5 scenarios, each with payload and expected class | `test_sample_payloads_are_available` |
| TC-04.7 | Requires authentication | no token | 401 | `test_analysis_requires_authentication` |

---

### TC-05 - Threat Detection Engine (FR-05)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-05.1 | Works with no trained model | `ThreatDetector(model_dir=None)` | `ml_available = false`; mode `hybrid-rules`; still classifies | `test_engine_works_without_any_trained_model` |
| TC-05.2 | Normal traffic is LOW | benign HTTPS browsing | Normal Activity, LOW, `is_threat` false, risk < 26 | `test_normal_traffic_is_low_risk` |
| TC-05.3 | Brute force classified | 62 failed SSH logins | Brute Force Attempt; HIGH or CRITICAL; reason mentions failed authentication | `test_brute_force_is_classified_and_escalated` |
| TC-05.4 | Port scan classified | 420 tiny connections in 9 s | Port Scanning Pattern | `test_port_scan_is_classified` |
| TC-05.5 | Data exfiltration classified | 1.2 GB off-hours upload | Data Transfer Anomaly; CRITICAL | `test_data_exfiltration_is_classified` |
| TC-05.6 | DoS classified | 48000 requests in 42 s | Denial-of-Service Pattern | `test_denial_of_service_is_classified` |
| TC-05.7 | Every verdict is explainable | all five scenarios | non-empty reasons, recommended action, valid ranges | `test_every_detection_is_explainable` |
| TC-05.8 | Score bounded under extremes | absurd values (1e11 bytes etc.) | risk stays 0-100; CRITICAL | `test_risk_score_is_always_within_bounds` |
| TC-05.9 | **Boundary:** severity bands | 0, 25, 26, 50, 51, 75, 76, 100 | LOW, LOW, MEDIUM, MEDIUM, HIGH, HIGH, CRITICAL, CRITICAL | `test_severity_bands_match_the_specification` |
| TC-05.10 | Sensitivity scales the score | same event at 0.5 and 1.5 | aggressive > relaxed | `test_sensitivity_scales_the_risk_score` |
| TC-05.11 | **Property:** risk is monotonic with intensity | 6, 20, 80, 200 failed logins | scores strictly non-decreasing | `test_risk_grows_with_attack_intensity` |
| TC-05.12 | Missing optional fields tolerated | `{source_ip}` only | Normal Activity; no exception | `test_missing_optional_fields_are_handled` |
| TC-05.13 | Feature vector is stable and ordered | brute-force event | 18 float features in `FEATURE_NAMES` order | `test_feature_extraction_is_stable_and_ordered` |
| TC-05.14 | Off-hours flag derived correctly | 03:00 vs 14:00 | 1.0 vs 0.0 | `test_off_hours_flag_is_derived_from_the_timestamp` |
| TC-05.15 | Every category has a recommended action | rule evaluation | action string returned | `test_rule_bank_returns_a_recommended_action_for_every_category` |
| TC-05.16 | **Regression:** all four bands populated | 400 generated events | {LOW, MEDIUM, HIGH, CRITICAL} all present | `test_generated_dataset_covers_every_severity_band` |
| TC-05.17 | **Regression:** low false-positive rate | benign generated events | fewer than 15% flagged as threats | `test_generated_normal_events_are_mostly_benign` |
| TC-05.18 | Batch matches individual | 3 events | identical classifications | `test_detect_batch_matches_individual_detection` |

> TC-05.16 and TC-05.17 exist because of the defect described in document 01
> section 5.1: the first calibration put every attack in the CRITICAL band and
> left HIGH empty. These two cases make that regression impossible to reintroduce
> silently.

---

### TC-06 - Alert Retrieval and Triage (FR-06)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-06.1 | Listing includes filter metadata | `GET /api/alerts` | pagination plus severities and statuses | `test_alerts_are_listed_with_filter_metadata` |
| TC-06.2 | Filter by severity | `?severity=CRITICAL` | every row is CRITICAL | `test_alerts_can_be_filtered_by_severity` |
| TC-06.3 | Search by source IP | `?search=<ip>` | every row matches | `test_alerts_can_be_searched_by_source_ip` |
| TC-06.4 | Sort by risk | `?sort=risk` | risk scores descending | `test_alerts_can_be_sorted_by_risk` |
| TC-06.5 | Detail includes the event | `GET /api/alerts/<id>` | event and reasons embedded | `test_single_alert_includes_its_event` |
| TC-06.6 | Move to investigating | `{action: investigate, note}` | status INVESTIGATING; note recorded with attribution | `test_alert_can_be_moved_to_investigating` |
| TC-06.7 | Resolve | `{action: resolve}` | status RESOLVED; `resolved_at` set | `test_alert_can_be_resolved` |
| TC-06.8 | Mark false positive | `{action: false_positive}` | status FALSE_POSITIVE | `test_alert_can_be_marked_false_positive` |
| TC-06.9 | Invalid status rejected | `{status: BANANA}` | 422 | `test_invalid_alert_status_is_rejected` |
| TC-06.10 | Status change is audited | resolve an alert | `ALERT_STATUS_CHANGED` entry exists | `test_alert_status_change_is_audited` |
| TC-06.11 | Escalate to incident | `POST .../escalate` | 201; incident created; alert linked | `test_alert_can_be_escalated_to_an_incident` |
| TC-06.12 | Escalation is idempotent | escalate an already-linked alert | the **existing** incident is returned, not a duplicate | `test_escalating_an_already_linked_alert_returns_the_same_incident` |
| TC-06.13 | Unknown alert | id 999999 | 404 | `test_unknown_alert_returns_404` |

---

### TC-07 - Incident Management (FR-07)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-07.1 | Manual creation | title, severity HIGH, source IP | 201; `INC-` code; status NEW; priority P2; one history entry | `test_incident_can_be_created_manually` |
| TC-07.2 | Title is mandatory | no title | 422 naming the title field | `test_incident_creation_requires_a_title` |
| TC-07.3 | Unknown severity rejected | `severity: URGENT` | 422 | `test_incident_creation_rejects_an_unknown_severity` |
| TC-07.4 | **State:** only legal transitions offered | read an incident in NEW | allowed = {OPEN, INVESTIGATING, FALSE_POSITIVE}; RESOLVED absent | `test_incident_exposes_only_legal_transitions` |
| TC-07.5 | **State:** illegal transition refused | NEW -> RESOLVED | 409 CONFLICT with current, requested and allowed | `test_illegal_transition_is_refused` |
| TC-07.6 | **State:** full lifecycle | NEW -> INVESTIGATING -> CONTAINED -> RESOLVED | each step 200; `contained_at` and `resolved_at` set; 4 history entries | `test_full_lifecycle_new_to_resolved` |
| TC-07.7 | **State:** dismissal path | NEW -> FALSE_POSITIVE with summary | status and resolution summary stored | `test_incident_can_be_closed_as_false_positive` |
| TC-07.8 | Closure cascades to alerts | resolve an incident with a linked alert | the alert becomes RESOLVED | `test_resolving_an_incident_closes_its_alerts` |
| TC-07.9 | Reassignment | `{assigned_to: id}` | 200; assignee updated | `test_incident_can_be_reassigned` |
| TC-07.10 | Filter by status | `?status=NEW` | every row is NEW | `test_incidents_can_be_filtered_by_status` |
| TC-07.11 | Unknown incident | id 999999 | 404 | `test_unknown_incident_returns_404` |
| TC-07.12 | Requires authentication | no token | 401 on GET and POST | `test_incident_endpoints_require_authentication` |

---

### TC-08 - Asset Management (FR-08)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-08.1 | Listing includes event counts | `GET /api/assets` | every asset carries `event_count` | `test_assets_are_listed_with_event_counts` |
| TC-08.2 | Creation | name, IP, type, OS | 201; risk starts LOW | `test_asset_can_be_created` |
| TC-08.3 | Duplicate IP rejected | existing IP | 422 naming `ip_address` | `test_duplicate_asset_ip_is_rejected` |
| TC-08.4 | Invalid IP rejected | `10.0.0` | 422 | `test_asset_requires_a_valid_ip` |
| TC-08.5 | Name is mandatory | IP only | 422 naming `name` | `test_asset_requires_a_name` |
| TC-08.6 | Update | `{status: QUARANTINED}` | 200; status changed | `test_asset_can_be_updated` |
| TC-08.7 | Risk rises after a critical detection | attack against a known asset IP | asset risk score increases; level becomes CRITICAL | `test_asset_risk_rises_after_a_critical_detection` |
| TC-08.8 | Deletion preserves history | delete an asset | 200; event count unchanged | `test_asset_can_be_deleted_and_events_survive` |
| TC-08.9 | Requires authentication | no token | 401 on GET and POST | `test_asset_endpoints_require_authentication` |

---

### TC-09 - CSV Upload (FR-10)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-09.1 | Valid file analysed | 4-row CSV | 201; all 4 analysed; normal + suspicious = 4; no rejects | `test_csv_upload_analyses_every_row` |
| TC-09.2 | Alerts created from the file | 4-row CSV with a brute-force row | alert count rises by `alerts_created` | `test_csv_upload_creates_alerts` |
| TC-09.3 | **Partial failure isolated** | 3-row CSV, 2 rows invalid | 201; 1 analysed; 2 rejected with reasons | `test_csv_upload_reports_invalid_rows_without_failing` |
| TC-09.4 | Empty file | zero bytes | 422 "empty" | `test_empty_file_upload_is_rejected` |
| TC-09.5 | Header only | header, no data rows | 422 "no data rows" | `test_header_only_csv_is_rejected` |
| TC-09.6 | Missing mandatory column | CSV without `source_ip` | 422 naming `source_ip` | `test_csv_without_source_ip_column_is_rejected` |
| TC-09.7 | Wrong extension | `payload.exe` | 422 listing accepted extensions | `test_wrong_file_extension_is_rejected` |
| TC-09.8 | No file part | empty multipart body | 422 | `test_upload_without_a_file_part_is_rejected` |
| TC-09.9 | Requires authentication | no token | 401 | `test_upload_requires_authentication` |

---

### TC-10 - Input Validation (NFR-02)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-10.1 | Invalid IP | `999.999.1.1` | 422; `details.field = source_ip` | `test_invalid_source_ip_is_rejected` |
| TC-10.2 | Missing required field | no `source_ip` | 422 naming it | `test_missing_source_ip_is_rejected` |
| TC-10.3 | **Boundary:** port out of range | 70000 | 422; `details.field = destination_port` | `test_out_of_range_port_is_rejected` |
| TC-10.4 | Unknown protocol | `TELEPATHY` | 422 listing valid protocols | `test_unknown_protocol_is_rejected` |
| TC-10.5 | **Boundary:** negative number | `failed_login_attempts = -5` | 422 | `test_negative_numeric_value_is_rejected` |
| TC-10.6 | Non-numeric where numeric expected | `bytes_transferred = "not-a-number"` | 422 | `test_non_numeric_value_is_rejected` |
| TC-10.7 | Invalid report period | `days = 9999` | 422 | `test_report_rejects_an_invalid_period` |
| TC-10.8 | Unknown report type | `MAGIC` | 422 | `test_report_rejects_an_unknown_type` |

---

### TC-11 - Unauthorised Access (NFR-02)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-11.1 | No token | `GET /api/alerts` | 401 `NO_TOKEN` | `test_protected_route_rejects_a_missing_token` |
| TC-11.2 | Forged token | `Bearer not.a.real.token` | 401 `TOKEN_INVALID` | `test_protected_route_rejects_a_forged_token` |
| TC-11.3 | Protected endpoints across the API | dashboard, events, alerts, incidents, assets, upload | all 401 without a token | `test_dashboard_requires_authentication`, `test_analysis_requires_authentication`, `test_upload_requires_authentication`, `test_incident_endpoints_require_authentication`, `test_asset_endpoints_require_authentication` |

---

### TC-12 - Health, Reports and System (NFR-07, FR-11)

| ID | Test case | Input | Expected result | Automated by |
|----|-----------|-------|-----------------|--------------|
| TC-12.1 | Health check is public | `GET /api/health` without a token | 200; status healthy; database connected; engine mode reported | `test_health_check_is_public` |
| TC-12.2 | System status reports table counts and thresholds | `GET /api/system/status` | user count correct; thresholds 26 and 76 | `test_system_status_reports_table_counts` |
| TC-12.3 | API index lists endpoints | `GET /api` | more than 20 endpoints; key paths present | `test_api_index_lists_endpoints` |
| TC-12.4 | Unknown route | `GET /api/does-not-exist` | JSON 404, not an HTML page | `test_unknown_route_returns_a_json_404` |
| TC-12.5 | Wrong method | `DELETE /api/health` | 405 `METHOD_NOT_ALLOWED` | `test_wrong_method_returns_405` |
| TC-12.6 | Report generation | 30-day summary | 201; `RPT-` code; content with recommendations | `test_report_can_be_generated` |
| TC-12.7 | Export in all three formats | JSON, CSV, PDF | JSON and CSV 200; PDF 200 with `%PDF` header, or 501 with a clear message | `test_report_downloads_in_every_format` |
| TC-12.8 | Preview stores nothing | `GET /api/reports/preview` | 200; report count unchanged | `test_report_preview_does_not_store_anything` |
| TC-12.9 | Threat intelligence marked simulated | `GET /api/threat-intelligence` | every indicator `is_simulated`; notice present | `test_threat_intelligence_is_marked_simulated` |
| TC-12.10 | Indicator status change | `PUT .../<id>` | 200; status MONITORING | `test_indicator_status_can_be_changed` |
| TC-12.11 | Audit trail captures changes | create an asset | `ASSET_CREATED` and `LOGIN_SUCCESS` present | `test_audit_log_records_every_state_change` |
| TC-12.12 | Threats listed with filters | `GET /api/threats` | categories filter metadata present | `test_threats_are_listed` |
| TC-12.13 | Threat detail includes its event | `GET /api/threats/<id>` | event embedded | `test_single_threat_includes_its_event` |

---

## 3. Coverage summary

| Test file | Cases | Area |
|-----------|-------|------|
| `test_auth.py` | 15 | TC-01, TC-11 |
| `test_detection_engine.py` | 18 | TC-05 |
| `test_events.py` | 27 | TC-03, TC-04, TC-09, TC-10 |
| `test_alerts_incidents.py` | 25 | TC-06, TC-07 |
| `test_assets_dashboard.py` | 32 | TC-02, TC-08, TC-12 |
| **Total** | **117** | |

### 3.1 Requirement coverage

| Requirement | Covered by | Cases |
|-------------|-----------|-------|
| FR-01 Login | TC-01, TC-11 | 15 |
| FR-02 Dashboard | TC-02 | 8 |
| FR-03 Event submission | TC-03 | 5 |
| FR-04 Event analysis | TC-04 | 7 |
| FR-05 Threat detection | TC-05 | 18 |
| FR-06 Alert management | TC-06 | 13 |
| FR-07 Incident management | TC-07 | 12 |
| FR-08 Asset management | TC-08 | 9 |
| FR-09 Threat intelligence | TC-12.9, TC-12.10 | 2 |
| FR-10 Log analysis | TC-09 | 9 |
| FR-11 Report generation | TC-12.6 - TC-12.8 | 3 |
| FR-12 Audit logging | TC-01.7, TC-01.8, TC-06.10, TC-12.11 | 4 |
| NFR-02 Security | TC-10, TC-11 | 11 |
| NFR-04 Reliability | TC-05.1, TC-09.3, TC-12.7 | 3 |
| NFR-07 Availability | TC-12.1 - TC-12.3 | 3 |

**Every functional requirement has at least two automated test cases, and every
requirement has at least one negative (error-path) case.**

---

## 4. How to run

```bash
cd backend
venv\Scripts\activate
python -m pytest                    # full suite, verbose
python -m pytest -q                 # quiet summary
python -m pytest tests/test_detection_engine.py -v
python -m pytest -k "incident"      # by keyword
python -m pytest -k "boundary or severity"
```

### 4.1 Latest recorded run

```
tests\test_alerts_incidents.py .........................                 [ 21%]
tests\test_assets_dashboard.py ................................         [ 48%]
tests\test_auth.py ...............                                       [ 61%]
tests\test_detection_engine.py ..................                        [ 76%]
tests\test_events.py ...........................                         [100%]

============================ 117 passed in 51.16s =============================
```

Environment: Windows 11, Python 3.10.0, pytest 8.3.2, detection engine in
`hybrid-ml` mode.

### 4.2 Test isolation

Every test module builds a fresh application through `create_app("testing")`
backed by an **in-memory SQLite database**, seeded with three users, two assets,
one indicator and three analysed events. Tests therefore:

- never touch `database/cyberguard.db`;
- cannot affect one another through shared state;
- can run in any order.
