# 08 - Data Flow Diagram - Level 2

**Project:** CyberGuard AI
**Lab experiment:** 4 - Requirement modelling using DFD

---

## 1. Purpose

Level 2 decomposes **Process 2.3 - Analyse Event**, the detection engine. This is
the deepest decomposition in the project because it is where the system's
distinctive logic lives; every other process is essentially validation,
persistence or aggregation.

A second Level 2 diagram decomposes **Process 2.2 - Parse and Validate CSV**,
because its per-row error isolation is a specific behaviour required by FR-10.

---

## 2. Process 2.3 - Analyse Event (full decomposition)

```
                          validated event
                                |
                                v
      +--------------------------------------------------------+
      |                        2.3.1                           |
      |                 EXTRACT FEATURES                       |
      |                                                        |
      |  From 11 observed fields, derive 18 numeric features:  |
      |                                                        |
      |  Direct:      failed_login_attempts, request_count,    |
      |               packet_count, bytes_transferred,         |
      |               connection_duration, source_port,        |
      |               destination_port                         |
      |                                                        |
      |  Derived:     bytes_per_packet = bytes / packets       |
      |               packets_per_second = packets / duration  |
      |               requests_per_second = requests / duration|
      |               bytes_per_request = bytes / requests     |
      |               log_bytes = ln(1 + bytes)                |
      |               log_requests = ln(1 + requests)          |
      |                                                        |
      |  Contextual:  hour_of_day                              |
      |               is_off_hours   (hour < 6 or hour >= 22)  |
      |               is_wellknown_dest_port                   |
      |               is_high_dest_port  (port >= 1024)        |
      |               is_auth_event                            |
      +--------------------------------------------------------+
                                |
                 feature vector (fixed order, 18 values)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
+------------------+  +------------------+  +---------------------------+
|      2.3.2       |  |      2.3.3       |  |          2.3.4            |
|   RULE BANK      |  |  STATISTICAL     |  |    MACHINE LEARNING       |
|   EVALUATION     |  |  BASELINE        |  |    (optional)             |
|                  |  |  SCORING         |  |                           |
| 7 rules, each    |  |                  |  | If ml_model/ artefacts    |
| returning        |  | z = (x - mean)   |  | are present:              |
| (score, reasons):|  |      / std       |  |                           |
|                  |  |                  |  |  - StandardScaler         |
| R1 Brute Force   |  | Keep only        |  |  - RandomForest           |
| R2 DoS Pattern   |  | z > 2.0          |  |    -> P(malicious) * 100  |
| R3 Data Transfer |  |                  |  |  - IsolationForest        |
| R4 Port Scanning |  | Combine the 3    |  |    -> outlier score       |
| R5 Cred. Abuse   |  | strongest with   |  |                           |
| R6 Susp. Login   |  | weights          |  | ml_score = max(the two)   |
| R7 Network Anom. |  | (1.0, 0.45, 0.25)|  |                           |
|                  |  |                  |  | Else: ml_used = false     |
| Magnitude terms  |  | score = 100 *    |  | and this branch is        |
| are LOGARITHMIC  |  |   (1 - e^(-c/9)) |  | skipped entirely          |
| so intensity is  |  |                  |  |                           |
| preserved across |  | (saturating, so  |  | Load failures are caught: |
| orders of        |  |  3-sigma and     |  | the engine degrades to    |
| magnitude        |  |  30-sigma differ)|  | rules rather than failing |
+------------------+  +------------------+  +---------------------------+
        |                       |                       |
   rule_score (0-100)    anomaly_score (0-100)     ml_score (0-100)
   + category            + reasons                 + reasons
   + reasons                    |                       |
        |                       |                       |
        +-----------------------+-----------------------+
                                |
                                v
      +--------------------------------------------------------+
      |                        2.3.5                           |
      |                    FUSE SCORES                         |
      |                                                        |
      |  With ML:     weighted = 0.58*rule + 0.18*anomaly      |
      |                        + 0.24*ml                       |
      |  Without ML:  weighted = 0.74*rule + 0.26*anomaly      |
      |                                                        |
      |  risk = clamp( max(weighted, 0.85 * rule_score)        |
      |                * sensitivity , 0, 100 )                |
      |                                                        |
      |  The rule score acts as a FLOOR. The statistical and   |
      |  ML detectors contribute only through the weighted     |
      |  term, so on their own they can raise an event to      |
      |  MEDIUM for review but never to CRITICAL. This stops   |
      |  unexplained outliers from flooding the queue with     |
      |  unactionable "critical" noise.                        |
      |                                                        |
      |  sensitivity comes from the analyst's Settings page    |
      |  and is clamped to [0.5, 1.5].                         |
      +--------------------------------------------------------+
                                |
                          risk_score (0-100)
                                |
                                v
      +--------------------------------------------------------+
      |                        2.3.6                           |
      |               MAP SEVERITY AND VERDICT                 |
      |                                                        |
      |     0 - 25   -> LOW            26 - 50  -> MEDIUM      |
      |    51 - 75   -> HIGH           76 - 100 -> CRITICAL    |
      |                                                        |
      |  classification = winning rule category                |
      |  If the winner is "Normal Activity" but risk >= 26,    |
      |  reclassify as "Network Anomaly" - something objected  |
      |  statistically even though no rule matched.            |
      |                                                        |
      |  is_threat = (risk >= 26) AND                          |
      |              (classification != Normal Activity)       |
      +--------------------------------------------------------+
                                |
                                v
      +--------------------------------------------------------+
      |                        2.3.7                           |
      |               COMPUTE CONFIDENCE                       |
      |                                                        |
      |  agreement = 1 - (max(active) - min(active)) / 100     |
      |              over the detectors that fired             |
      |                                                        |
      |  If threat:  0.55 + 0.32*(risk/100) + 0.13*agreement   |
      |  If benign:  0.60 + 0.35*(1 - risk/100)                |
      |                                                        |
      |  clamped to [0.50, 0.99] - the engine never claims     |
      |  certainty                                             |
      +--------------------------------------------------------+
                                |
                                v
      +--------------------------------------------------------+
      |                        2.3.8                           |
      |              ASSEMBLE EXPLANATION                      |
      |                                                        |
      |  - reasons from the winning rule (in order)            |
      |  - one line per secondary rule that also fired         |
      |  - statistical reasons ("x is N sigma above baseline") |
      |  - ML reasons (classifier probability, outlier flag)   |
      |  - de-duplicate, preserve order, cap at 8              |
      |  - attach the recommended defensive action for the     |
      |    winning category                                    |
      |  - attach the MITRE ATT&CK tactic reference            |
      |  - record analysis_time_ms                             |
      +--------------------------------------------------------+
                                |
                                v
                +-------------------------------+
                |        DETECTION VERDICT      |
                |                               |
                | classification                |
                | risk_score      0-100         |
                | confidence      0.50-0.99     |
                | severity        LOW..CRITICAL |
                | is_threat       boolean       |
                | reasons         list          |
                | recommended_action            |
                | mitre_tactic                  |
                | scores {rule, anomaly, ml}    |
                | triggered_rules               |
                | feature_summary               |
                | model_used      hybrid-*      |
                | analysis_time_ms              |
                +-------------------------------+
                                |
                                v
                      to Process 2.4 (persist)
```

---

## 3. Sub-process specification for 2.3

| ID | Sub-process | Input | Output | Code |
|----|-------------|-------|--------|------|
| 2.3.1 | Extract Features | Validated event (11 fields) | 18-feature dictionary + fixed-order vector | `ml/features.py::extract_features` |
| 2.3.2 | Rule Bank Evaluation | Features + event | Winning category, rule score, reasons, all triggered rules | `ml/rules.py::evaluate_rules` |
| 2.3.3 | Statistical Baseline Scoring | Features | Anomaly score 0-100 + reasons | `ml/anomaly.py::StatisticalBaseline.score` |
| 2.3.4 | Machine Learning Scoring | Feature vector | ML score 0-100 + reasons + `ml_used` flag | `ml/detector.py::_ml_score` |
| 2.3.5 | Fuse Scores | Three sub-scores + sensitivity | Fused risk score | `ml/detector.py::detect` |
| 2.3.6 | Map Severity and Verdict | Risk score + category | Severity band, classification, threat flag | `ml/detector.py::severity_for` |
| 2.3.7 | Compute Confidence | Sub-scores, risk, threat flag | Confidence 0.50-0.99 | `ml/detector.py::_confidence` |
| 2.3.8 | Assemble Explanation | All of the above | Reason list, recommended action, MITRE tactic | `ml/detector.py::detect`, `ml/rules.py` |

---

## 4. The seven rules of process 2.3.2

Each rule is a pure function `(features, event) -> (score, reasons)`. A rule that
does not fire returns `(0, [])`. The highest-scoring rule determines the
classification; every other rule that fired is recorded as a secondary indicator.

| Rule | Fires when | Magnitude term | Additive bonuses |
|------|-----------|----------------|------------------|
| **R1 Brute Force Attempt** | `failed_logins >= 5` | `38 + 30*log10(failed/4)` | +8 authentication service, +6 high request rate, +5 sensitive destination port |
| **R2 Denial-of-Service Pattern** | `requests >= 400` or `packets/sec >= 400` | `20 + 30*log10(requests/300)` | +up to 20 sustained rate, +14 high packet rate, +8 near-empty payloads |
| **R3 Data Transfer Anomaly** | `bytes >= 45 MB` | `18 + 30*log10(MB/40)` | +16 off-hours, +8 very long session, +6 packets at MTU |
| **R4 Port Scanning Pattern** | `requests >= 25` and `bytes_per_packet <= 220` | `18 + 26*log10(requests/20)` | +18 tiny payloads, +12 few packets per connection, +8 uncommon high port |
| **R5 Credential Abuse Pattern** | authentication event with `failed >= 3` and `requests >= 30` | `22 + 18*log10(requests/25)`, capped at 45 | +22 off-hours heavy activity, +16 privileged port |
| **R6 Suspicious Login Activity** | `1 <= failed_logins <= 4` | `15 + 7*failed` | +16 off-hours, +7 authentication service, +6 remote-access port |
| **R7 Network Anomaly** | catch-all traffic-shape rule | duration, packet-size and off-hours terms | - |

### 4.1 Why the magnitude terms are logarithmic

This was the single most important correction made during development. With a
linear term, a brute-force attempt with 20 failed logins and one with 2000 both
saturated at 100, so the entire alert queue collapsed into one severity band and
the dashboard charts conveyed nothing.

With `38 + 30*log10(failed/4)`:

| Failed logins | Rule score (before bonuses) | Typical final severity |
|---------------|------------------------------|------------------------|
| 5 | 41 | HIGH |
| 10 | 50 | HIGH |
| 20 | 59 | HIGH |
| 50 | 71 | CRITICAL |
| 150 | 85 | CRITICAL |
| 1000 | 100 | CRITICAL |

The ordering is preserved across three orders of magnitude, which is exactly what
an analyst needs in order to prioritise. The regression test
`test_risk_grows_with_attack_intensity` locks this property in.

---

## 5. Process 2.2 - Parse and Validate CSV (decomposition)

```
                        uploaded file
                              |
                              v
      +--------------------------------------------------+
      |                     2.2.1                        |
      |              GUARD THE UPLOAD                    |
      |  - file part present?                            |
      |  - extension in {.csv, .txt, .log}?              |
      |  - size <= 8 MB (enforced by MAX_CONTENT_LENGTH) |
      +--------------------------------------------------+
                              | pass
                              v
      +--------------------------------------------------+
      |                     2.2.2                        |
      |                 DECODE BYTES                     |
      |  Try utf-8-sig, then utf-8, then latin-1.        |
      |  All fail -> 422 "could not be decoded as text". |
      |  Empty     -> 422 "the uploaded file is empty".  |
      +--------------------------------------------------+
                              |
                              v
      +--------------------------------------------------+
      |                     2.2.3                        |
      |          SNIFF DIALECT AND READ HEADER           |
      |  csv.Sniffer over the first 4 KB; delimiters     |
      |  , ; tab | are all accepted. Fall back to the    |
      |  excel dialect if sniffing fails.                |
      +--------------------------------------------------+
                              |
                              v
      +--------------------------------------------------+
      |                     2.2.4                        |
      |            NORMALISE COLUMN NAMES                |
      |  lower-case, spaces/hyphens -> underscore, then  |
      |  map aliases:                                    |
      |     bytes          -> bytes_transferred          |
      |     packets        -> packet_count               |
      |     failed_logins  -> failed_login_attempts      |
      |     duration       -> connection_duration        |
      |     src_ip/dst_ip  -> source_ip/destination_ip   |
      |     requests       -> request_count              |
      +--------------------------------------------------+
                              |
                              v
      +--------------------------------------------------+
      |                     2.2.5                        |
      |         CHECK MANDATORY COLUMN                   |
      |  source_ip missing -> 422 naming the required    |
      |  column and listing the columns actually found   |
      +--------------------------------------------------+
                              |
                              v
      +--------------------------------------------------+
      |                     2.2.6                        |
      |            VALIDATE EACH ROW  (loop)             |
      |                                                  |
      |  for each data row:                              |
      |      skip if entirely blank                      |
      |      stop if the 5000-row cap is reached         |
      |      try   -> validate via process 2.1           |
      |              -> append to valid_rows             |
      |      except -> append {row number, reason}       |
      |                to row_errors and CONTINUE        |
      |                                                  |
      |  One bad row NEVER aborts the upload.            |
      +--------------------------------------------------+
                              |
              +---------------+---------------+
              |                               |
         valid_rows                      row_errors
              |                               |
              v                               v
        to process 2.3                  to the analyst
     (analysed one by one,        (row number + human-readable
      committed as one            reason for each rejection)
      transaction)
```

### 5.1 Why per-row isolation matters

A real log export frequently contains a handful of malformed lines. Rejecting
the whole file would make the feature unusable. The design therefore isolates
failures at row granularity and reports them, which is tested directly by
`test_csv_upload_reports_invalid_rows_without_failing`: a four-row file with
two bad rows yields one analysed record, two reported errors and HTTP 201.

The repository ships `sample_data/sample_logs_invalid.csv` specifically so this
behaviour can be demonstrated live.

---

## 6. Worked example through Level 2

Input event (the "Repeated failed SSH logins" sample):

```json
{
  "source_ip": "203.0.113.66", "destination_ip": "10.0.1.20",
  "source_port": 44122, "destination_port": 22,
  "protocol": "SSH", "event_type": "authentication",
  "request_count": 68, "failed_login_attempts": 62,
  "packet_count": 340, "bytes_transferred": 41000,
  "connection_duration": 95
}
```

| Stage | Result |
|-------|--------|
| 2.3.1 Features | `failed=62`, `requests/sec=0.72`, `bytes/packet=120.6`, `is_auth_event=1`, `is_high_dest_port=0`, ... |
| 2.3.2 Rules | R1 Brute Force fires: `38 + 30*log10(62/4) = 73.7`, +8 auth, +5 port 22 -> **86.7**. R6 does not fire (failed >= 5). Winner: **Brute Force Attempt** |
| 2.3.3 Statistical | `failed_login_attempts` is ~112 sigma above baseline -> combined saturates -> **~100** |
| 2.3.4 ML | Classifier probability ~0.99 -> **~99** |
| 2.3.5 Fusion | `weighted = 0.58*86.7 + 0.18*100 + 0.24*99 = 92.2`; floor `0.85*86.7 = 73.7`; `risk = 92` |
| 2.3.6 Severity | 92 -> **CRITICAL**, `is_threat = true` |
| 2.3.7 Confidence | High agreement between all three detectors -> **~0.97** |
| 2.3.8 Explanation | "62 failed authentication attempts recorded for this source." / "The event originates from an authentication service." / "The targeted port 22 hosts a remote-access or database service." / statistical and ML reasons |

Downstream, process 2.5 creates a Threat, 2.6 raises an alert (risk >= 26), and
2.7 opens an incident (risk >= 76).

---

## 7. Balancing check against Level 1

| Level 1 process | Level 2 sub-processes | Input preserved | Output preserved |
|-----------------|------------------------|-----------------|------------------|
| 2.2 Parse and Validate CSV | 2.2.1 - 2.2.6 | Uploaded file | Valid rows + row errors |
| 2.3 Analyse Event | 2.3.1 - 2.3.8 | Validated event | Detection verdict |

**Result: balanced.** The inputs and outputs at the boundary of processes 2.2 and
2.3 are unchanged by the decomposition; only the internal steps are revealed.
