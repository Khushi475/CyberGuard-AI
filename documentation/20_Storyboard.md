# 20 - Storyboard

**Project:** CyberGuard AI
**Lab experiment:** 10 - Story boarding

---

## 1. Purpose and narrative

A storyboard walks through the system as a user actually experiences it, frame by
frame. This one follows a single continuous narrative so the frames connect
rather than sitting as isolated screenshots:

> **Arjun, a security analyst, starts his shift. The overnight detection engine
> has flagged repeated failed logins against the domain controller. He
> investigates, contains the source, resolves the case, and produces a report for
> the morning handover.**

Each frame records the **user action**, the **system response** and the
**expected result**.

---

## Frame 1 - Login

```
+==============================================================================+
|  +---------------------------------+  +-----------------------------------+  |
|  |                                 |  |                                   |  |
|  |   [shield]  CyberGuard AI       |  |   Sign in                         |  |
|  |   INTELLIGENT CYBER THREAT      |  |   Use a demo account below to     |  |
|  |   DETECTION SYSTEM              |  |   enter the console.              |  |
|  |                                 |  |                                   |  |
|  |   Detect, investigate and       |  |   EMAIL ADDRESS                   |  |
|  |   resolve security events from  |  |   [envelope] admin@cyberguard.ai  |  |
|  |   a single console.             |  |                                   |  |
|  |                                 |  |   PASSWORD                        |  |
|  |   * Hybrid rule, statistical    |  |   [lock] ............     [eye]   |  |
|  |     and ML threat detection     |  |                                   |  |
|  |   * Explainable 0-100 risk      |  |   [x] Remember me on this device  |  |
|  |     scoring with stated reasons |  |                                   |  |
|  |   * Alert triage and full       |  |   +---------------------------+   |  |
|  |     incident lifecycle          |  |   |   Sign in to console      |   |  |
|  |   * CSV log analysis with       |  |   +---------------------------+   |  |
|  |     per-row validation          |  |                                   |  |
|  |                                 |  |   DEMO ACCOUNTS                   |  |
|  |   (faint grid background)       |  |   +-----------------------------+ |  |
|  |                                 |  |   | Administrator         Use   | |  |
|  |   Academic prototype. Analyses  |  |   | admin@cyberguard.ai/admin123| |  |
|  |   simulated, defensive          |  |   +-----------------------------+ |  |
|  |   telemetry only.               |  |   | Security Analyst      Use   | |  |
|  |                                 |  |   | Viewer                Use   | |  |
|  +---------------------------------+  +-----------------------------------+  |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun clicks the "Security Analyst" demo card, then "Sign in to console". |
| **System response** | Client-side format validation, then `POST /api/auth/login`. The backend verifies the PBKDF2 hash, writes a `LOGIN_SUCCESS` audit entry, updates `last_login` and returns a signed token. |
| **Expected result** | Token stored, success toast "Welcome back, Arjun.", navigation to the dashboard. |
| **Error path** | Wrong credentials -> inline red banner "Invalid email address or password." and no navigation. Backend down -> "Cannot reach the CyberGuard AI backend" with the exact start command. |

---

## Frame 2 - Dashboard: the morning picture

```
+==============================================================================+
| [=] [search pages, IPs, alert codes.....]      [API online] [bell 7] [AA v]   |
+==========+===================================================================+
| SHIELD   |  Security Overview                    Updated 2m ago  [Refresh]   |
| CyberGuard|  Live posture of the monitored estate.                            |
|          |                                                                   |
| >Dashboard| +----------+ +----------+ +----------+ +----------+               |
|  Threat  | | Total    | | Threats  | | Critical | | Active   |               |
|  Detection| | Events   | | Detected | | Alerts   | | Incidents|               |
|  Alerts  | |   320    | |   143    | |    64    | |    60    |               |
|  Incidents| | 12 in 24h| | 9 in 24h | | 79 open  | | 4 resolved|              |
|  Threat  | +----------+ +----------+ +----------+ +----------+               |
|  Intel   |                                                                   |
|  Log     | +----------+ +----------+ +----------+ +----------+               |
|  Analyzer| | Monitored| | Detection| | Active   | | System   |               |
|  Assets  | | Assets 12| | Accuracy | |Indicators| | Health   |               |
|  Reports | | 5 at risk| |   66.7%  | |    15    | |  95/100  |               |
|  Settings| |          | |(analyst- | |          | |OPERATIONAL|              |
|          | |          | | confirmed)| |          | |          |              |
| Engine:  | +----------+ +----------+ +----------+ +----------+               |
| hybrid-ml|                                                                   |
|          | +----------------+ +--------------------------------------------+ |
| Academic | | CURRENT THREAT | | Threats over time                          | |
| prototype| | LEVEL          | | Detections per day, stacked by severity     | |
|          | |                | |                                            | |
|          | |   CRITICAL     | |  40|         ###                           | |
|          | | Immediate      | |    |       #######    ##                    | |
|          | | response       | |  20|    #################                   | |
|          | | [=========  ]  | |    |  ######################                | |
|          | |                | |   0+--------------------------------        | |
|          | | 0   6   0  12  | |     01Feb   05Feb   09Feb   13Feb          | |
|          | | LOW MED HIGH CR| |   [] LOW [] MEDIUM [] HIGH [] CRITICAL     | |
|          | +----------------+ +--------------------------------------------+ |
|          |                                                                   |
|          | +-------------+ +---------------+ +---------------------------+   |
|          | | Severity    | | Threat        | | Protocol mix              |   |
|          | | distribution| | categories    | |                           |   |
|          | |   (donut)   | |  (bar chart)  | |         (donut)           |   |
|          | +-------------+ +---------------+ +---------------------------+   |
|          |                                                                   |
|          | +-------------------------+ +-----------------------------------+ |
|          | | Detection trend         | | Most active sources               | |
|          | | events vs threats/day   | | top source IPs by event count     | |
|          | +-------------------------+ +-----------------------------------+ |
|          |                                                                   |
|          | +----------------------------------------+ +-------------------+  |
|          | | Recent alerts                 View all | | System health     |  |
|          | | ALERT   TYPE        SRC    SEV  RISK   | |  66.7%            |  |
|          | | ALT-143 Brute Force 203..  CRIT [===]  | |  Analyst-confirmed|  |
|          | | ALT-142 Port Scan   198..  HIGH [==]   | |  precision        |  |
|          | | ALT-141 Data Xfer   10.0.. CRIT [===]  | |                   |  |
|          | +----------------------------------------+ | [ok] Database     |  |
|          |                                            | [ok] Engine       |  |
|          | +----------------------------------------+ | [ok] ML Models    |  |
|          | | Activity feed                          | | [ok] Pipeline     |  |
|          | | [!] Alert ALT-000143 raised... 2m ago  | +-------------------+  |
|          | | [i] Incident INC-000064 ...    8m ago  |                       |
|          | +----------------------------------------+                       |
+==========+===================================================================+
```

| | |
|---|---|
| **User action** | Arjun reads the overnight picture. The bell shows 7 unacknowledged alerts. |
| **System response** | `GET /api/dashboard/stats` returns totals, six chart series, the threat level, the detection-quality figure **with its source labelled**, the health self-check and a merged activity feed. The page auto-refreshes every 45 seconds. |
| **Expected result** | Every figure comes from the database. Analysing a new event and returning here increases the totals. |
| **Design note** | The accuracy tile always states where its number came from - "Analyst-confirmed precision" here, or "Model hold-out accuracy (synthetic data)" before enough alerts have been triaged. A bare percentage is never shown. |

---

## Frame 3 - Threat Detection: reproducing the finding

```
+==============================================================================+
|  Threat Detection                                          [Reset form]      |
|  Submit a security event for analysis. The hybrid engine returns a           |
|  classification, a 0-100 risk score, a confidence value and its reasons.     |
|                                                                              |
| +--------------------------+ +---------------------------------------------+ |
| | Security event           | |  [!] Brute Force Attempt      [CRITICAL]    | |
| |                          | |                                             | |
| | SOURCE IP *  DEST IP     | |        .-----.      Risk score  92/100       | |
| | [203.0.113.66][10.0.1.20]| |      /   92   \     Severity    CRITICAL     | |
| |                          | |     |  RISK   |     Confidence  97.0%        | |
| | SRC PORT     DEST PORT   | |      \  /100 /      Verdict     Threat       | |
| | [44122]      [22]        | |        '-----'                              | |
| |                          | |                                             | |
| | PROTOCOL     EVENT TYPE  | |  Mapped tactic: Credential Access (TA0006)  | |
| | [SSH    v]   [auth...v]  | +---------------------------------------------+ |
| |                          | |                                             | |
| | REQUEST COUNT            | | Why the engine reached this verdict         | |
| | [68]                     | |  * 62 failed authentication attempts        | |
| | FAILED LOGIN ATTEMPTS    | |    recorded for this source.                | |
| | [62]                     | |  * The event originates from an             | |
| | PACKET COUNT             | |    authentication service.                  | |
| | [340]                    | |  * The targeted port 22 hosts a remote-     | |
| | BYTES TRANSFERRED        | |    access or database service.              | |
| | [41000]                  | |  * 'failed login attempts' is 112.4 standard| |
| | CONNECTION DURATION (s)  | |    deviations above the learned baseline.   | |
| | [95]                     | |  * The trained classifier assigns a 99%     | |
| |                          | |    probability that this event is malicious.| |
| | DERIVED FROM YOUR INPUT  | |                                             | |
| | Volume   Duration  Req/s | | +---------+ +-----------+ +---------------+ | |
| | 40.0 KB  1m 35s    0.72  | | |Rule bank| |Statistical| |Machine learning| | |
| |                          | | |  86.7   | |   100.0   | |     99.0      | | |
| | [x] Store this event in  | | | [=====] | |  [=====]  | |   [=====]     | | |
| |     the database         | | +---------+ +-----------+ +---------------+ | |
| |                          | +---------------------------------------------+ |
| | +----------------------+ | |                                             | |
| | |  [zap] Analyze Threat| | | Recommended defensive action                | |
| | +----------------------+ | | Temporarily rate-limit or lock the targeted | |
| |                          | | account, enforce MFA, and review            | |
| | SAMPLE SCENARIOS         | | authentication logs for the source address. | |
| | > Normal HTTPS browsing  | |                                             | |
| | > Repeated failed SSH    | | [!] Alert ALT-000144 raised  ->             | |
| |   logins                 | | [i] Incident INC-000065 opened ->           | |
| | > Rapid small connections| +---------------------------------------------+ |
| | > Large off-hours upload | | Feature summary                             | |
| | > High-volume flood      | | Failed logins 62 | Requests 68 | Packets 340| |
| +--------------------------+ +---------------------------------------------+ |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun loads the "Repeated failed SSH logins" sample to reproduce the overnight finding, then clicks "Analyze Threat". |
| **System response** | `POST /api/events/analyze` -> validation -> asset resolution -> `SecurityEvent` stored -> engine runs 8 stages -> `DetectionResult`, `Threat`, `Alert` and `Incident` created -> asset risk updated -> audit entry -> single commit. |
| **Expected result** | Score ring animates to 92, the classification and severity appear, five plain-English reasons are listed, the three detector sub-scores are shown separately, and the alert and incident that were created are linked. |
| **Design note** | The three sub-score bars exist so the analyst can see *which* detector drove the verdict. When the rule bar is high the finding is deterministic and explainable; when only the statistical bar is high it is an unexplained outlier that warrants a closer look. |
| **Error path** | An invalid IP highlights the field in red with "source_ip must be a valid IPv4/IPv6 address", and a summary box lists every problem. Nothing is stored. |

---

## Frame 4 - Alerts: the triage queue

```
+==============================================================================+
|  Alerts                                        [Filters 2] [Refresh]         |
|  Every detection at MEDIUM severity or above raises an alert for triage.     |
|                                                                              |
| +--------------------------------------------------------------------------+ |
| | [search alert code, source IP, threat type...]        [Highest risk  v]   | |
| |                                                                          | |
| | SEVERITY      STATUS        THREAT TYPE     FROM DATE    TO DATE         | |
| | [CRITICAL v]  [New      v]  [All types  v]  [        ]   [        ]      | |
| |                                                                          | |
| | [x] Clear all filters                                                    | |
| +--------------------------------------------------------------------------+ |
| | ALERT ID   TIMESTAMP     THREAT TYPE      SOURCE       SEV   RISK        | |
| |            CONFIDENCE    STATUS           ACTIONS                        | |
| |--------------------------------------------------------------------------| |
| | ALT-000144 22 Sep, 03:14 Brute Force      203.0.113.66 CRIT  [=======] 92| |
| |            97%           [New]            [eye][search][check][shield]   | |
| |--------------------------------------------------------------------------| |
| | ALT-000143 22 Sep, 02:51 Port Scanning    198.51.100.23 CRIT [======] 90 | |
| |            95%           [New]            [eye][search][check][shield]   | |
| |--------------------------------------------------------------------------| |
| | ALT-000141 22 Sep, 01:07 Data Transfer    10.0.2.31    CRIT  [=======]100| |
| |            99%           [Investigating]  [eye][search][check][shield]   | |
| +--------------------------------------------------------------------------+ |
| | Showing 1-15 of 79                          [<] [1] [2] [3] [4] [5] [>]  | |
| +--------------------------------------------------------------------------+ |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun filters to CRITICAL + New, sorts by highest risk, and opens ALT-000144. |
| **System response** | `GET /api/alerts` with the filter parameters. All filtering, sorting and pagination happen in SQL, not in the browser. |
| **Expected result** | The queue narrows to critical unacknowledged alerts, ordered by risk. |
| **Design note** | The four row actions map to the four decisions an analyst can make: view, investigate, resolve, mark false positive. Resolve and false-positive both open a confirmation dialog, because both feed the detection-precision figure on the dashboard. |

---

## Frame 5 - Alert detail: deciding what to do

```
+==============================================================================+
|                                                                    [x]       |
|  ALT-000144 - Brute Force Attempt                                            |
|  22 Sep 2026, 03:14                                                          |
|------------------------------------------------------------------------------|
|  [CRITICAL]  [New]  confidence 97%   [Linked incident #65]                   |
|                                                                              |
|  SUMMARY                                                                     |
|  Brute Force Attempt observed from 203.0.113.66 towards 10.0.1.20:22 over    |
|  SSH. Risk score 92/100 (CRITICAL), engine confidence 97%.                   |
|                                                                              |
|  RISK SCORE                                                                  |
|  [==========================================              ]  92              |
|                                                                              |
|  +------------------------------+  +------------------------------+          |
|  | SOURCE INFORMATION           |  | EVENT TELEMETRY              |          |
|  | Source IP      203.0.113.66  |  | Protocol           SSH       |          |
|  | Destination IP 10.0.1.20     |  | Dest. port         22        |          |
|  | Event ID       441           |  | Failed logins      62        |          |
|  | Raised         22 Sep, 03:14 |  | Requests           68        |          |
|  +------------------------------+  +------------------------------+          |
|                                                                              |
|  DETECTION REASONS                                                           |
|   * 62 failed authentication attempts recorded for this source.              |
|   * The event originates from an authentication service.                     |
|   * The targeted port 22 hosts a remote-access or database service.          |
|                                                                              |
|  RECOMMENDED RESPONSE                                                        |
|  +------------------------------------------------------------------------+ |
|  | Temporarily rate-limit or lock the targeted account, enforce MFA, and   | |
|  | review authentication logs for the source address.                     | |
|  +------------------------------------------------------------------------+ |
|                                                                              |
|  ADD A NOTE WITH YOUR NEXT ACTION                                            |
|  +------------------------------------------------------------------------+ |
|  | Source blocked at the perimeter gateway, monitoring for recurrence.    | |
|  +------------------------------------------------------------------------+ |
|------------------------------------------------------------------------------|
|  [Investigate]  [Escalate to incident]  [False positive]  [Resolve]          |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun reads the reasons, types a note, and clicks "Escalate to incident". |
| **System response** | `POST /api/alerts/144/escalate`. Because this alert already has an auto-created incident (it was CRITICAL), the **existing** incident is returned rather than a duplicate being created. The alert moves to INVESTIGATING and an `ALERT_ESCALATED` audit entry is written. |
| **Expected result** | Navigation to the incident details page. |

---

## Frame 6 - Incident investigation

```
+==============================================================================+
|  < Back to incidents                                                         |
|                                                                              |
|  Brute Force Attempt targeting 10.0.1.20                      [Refresh]      |
|  INC-000065 - detected 22 Sep 2026, 03:14                                    |
|                                                                              |
|  [CRITICAL] [New] [Priority P1] [Brute Force Attempt]                        |
|                                                                              |
| +-------------------------------------------+ +----------------------------+ |
| | Incident lifecycle                        | | Details                    | |
| |                                           | | Incident ID   INC-000065   | |
| |  (1)----(2)----(3)----(4)----(5)          | | Threat type   Brute Force  | |
| |  New    Open   Invest  Contained Resolved | | Severity      CRITICAL     | |
| |  [*]                                      | | Priority      P1           | |
| |                                           | | Source IP     203.0.113.66 | |
| | AVAILABLE TRANSITIONS                     | | Detected      22 Sep 03:14 | |
| | [Investigate] [Reopen as open]            | +----------------------------+ |
| | [False positive]                          |                              | |
| |                                           | +----------------------------+ |
| | Only transitions allowed by the backend   | | Assignment                 | |
| | state machine are offered. Attempting any | | [person] Arjun Analyst     | |
| | other move returns HTTP 409.              | | REASSIGN TO                | |
| +-------------------------------------------+ | [Arjun Analyst        v]   | |
|                                               +----------------------------+ |
| +-------------------------------------------+                              | |
| | Incident summary                          | +----------------------------+ |
| | Brute Force Attempt observed from         | | Status history             | |
| | 203.0.113.66 towards 10.0.1.20:22 over    | |                            | |
| | SSH. Risk score 92/100 (CRITICAL).        | | o [New]                    | |
| |                                           | |   Detection Engine         | |
| | RISK SCORE                                | |   Incident opened          | |
| | [=====================================] 92| |   automatically because    | |
| +-------------------------------------------+ |   the risk score reached   | |
|                                               |   the critical band.       | |
| +-------------------------------------------+ |   22 Sep 2026, 03:14      | |
| | Linked alerts                    1 alert  | +----------------------------+ |
| | ALT-000144 Brute Force 203.0.113.66 CRIT  |                              | |
| +-------------------------------------------+ +----------------------------+ |
|                                               | Response checklist         | |
| +-------------------------------------------+ | [] Confirm with the asset  | |
| | Related events                            | |    owner                   | |
| | TIMESTAMP   SOURCE      DEST     CLASS    | | [] Preserve the events     | |
| | 22 Sep 03:14 203.0.113. 10.0.1.. Brute F. | | [] Apply containment       | |
| | 22 Sep 02:58 203.0.113. 10.0.1.. Brute F. | | [] Verify it stopped       | |
| +-------------------------------------------+ | [] Record a resolution     | |
|                                               +----------------------------+ |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun reviews the linked alert and the related events from the same source, then clicks "Investigate". |
| **System response** | `GET /api/incidents/65` returned the incident **plus the list of currently legal transitions**. The page rendered a button only for each of those. `PUT /api/incidents/65` validates the transition server-side before applying it. |
| **Expected result** | The tracker advances to stage 3; a history entry is appended with Arjun's name, the note and a timestamp. |
| **Design note** | "Contain" and "Resolve" are deliberately **absent** at this stage. The state machine does not permit NEW -> CONTAINED, so the UI cannot offer it. This is the visible consequence of the state transition diagram in document 09. |

---

## Frame 7 - Containment and resolution

```
+==============================================================================+
|                                                                    [x]       |
|  Resolve incident                                                            |
|  The incident will move to Resolved. This change is written to the audit     |
|  trail.                                                                      |
|------------------------------------------------------------------------------|
|                                                                              |
|  NOTE FOR THE STATUS HISTORY                                                 |
|  +------------------------------------------------------------------------+ |
|  | Source address blocked at the perimeter gateway; no further attempts   | |
|  | observed in 4 hours.                                                   | |
|  +------------------------------------------------------------------------+ |
|                                                                              |
|  RESOLUTION SUMMARY                                                          |
|  +------------------------------------------------------------------------+ |
|  | Account lockout threshold lowered to 5 attempts and MFA enforced for   | |
|  | remote SSH. Containment verified.                                      | |
|  +------------------------------------------------------------------------+ |
|  Closing the incident also closes every alert linked to it.                  |
|                                                                              |
|------------------------------------------------------------------------------|
|                                             [Cancel]  [Confirm]              |
+==============================================================================+

                                   |  after confirmation
                                   v

  Incident lifecycle
   (1)----(2)----(3)----(4)----(5)
   New    Open   Invest  Contained Resolved
                                   [*]
  Lifecycle complete. The incident can be reopened for investigation if the
  activity recurs.

  Status history
   o [Contained] to [Resolved]   Arjun Analyst
     Source address blocked at the perimeter gateway...     22 Sep, 09:12
   o [Investigating] to [Contained]   Arjun Analyst
     Temporary containment applied.                         22 Sep, 08:40
   o [New] to [Investigating]   Arjun Analyst
     Triage started.                                        22 Sep, 08:15
   o [New]   Detection Engine
     Incident opened automatically...                       22 Sep, 03:14
```

| | |
|---|---|
| **User action** | Arjun moves the incident to CONTAINED, then to RESOLVED with a resolution summary. |
| **System response** | Each transition is re-validated server-side. `contained_at` and `resolved_at` are stamped. On resolution, **every alert linked to the incident is closed as RESOLVED**. Each change is audited. |
| **Expected result** | The tracker completes, the history shows four attributed entries newest-first, and ALT-000144 now shows as Resolved on the Alerts page. |
| **Downstream effect** | The resolved alert now counts towards the analyst-confirmed precision figure on the dashboard - closing the loop between triage and reported detection accuracy. |

---

## Frame 8 - Log Analyzer: the bulk check

```
+==============================================================================+
|  Log Analyzer                          [Export results] [Clear]              |
|  Upload a CSV log export. Every row is validated, scored and stored.         |
|                                                                              |
| +------------------------+ +-----------------------------------------------+ |
| | Upload log file        | | +-------+ +-------+ +-------+ +-------+ +----+| |
| | CSV/TXT/LOG, max 8 MB  | | |Total  | |Normal | |Suspic-| |High   | |Crit|| |
| |                        | | |records| |events | |ious   | |risk   | |ical|| |
| | +--------------------+ | | |  120  | |  61   | |  59   | |  53   | | 27 || |
| | |    [upload icon]   | | | +-------+ +-------+ +-------+ +-------+ +----+| |
| | |                    | | |                                               | |
| | | sample_logs_mixed  | | | Ingestion summary                             | |
| | |      .csv          | | | sample_logs_mixed.csv - 59 alerts and 12      | |
| | |     14.2 KB        | | | incidents created                             | |
| | +--------------------+ | | +------+ +--------+ +------+ +----------+     | |
| |                        | | | LOW  | | MEDIUM | | HIGH | | CRITICAL |     | |
| | [====== 100% ]         | | |  61  | |   6    | |  26  | |    27    |     | |
| |                        | | +------+ +--------+ +------+ +----------+     | |
| | +--------------------+ | |                                               | |
| | | Analyze log file   | | | [View the 59 new alerts]                      | |
| | +--------------------+ | +-----------------------------------------------+ |
| |                        | +-------------------+ +-------------------------+ |
| | EXPECTED COLUMNS       | | Classifications   | | Most active sources     | |
| | [source_ip] [timestamp]| |   (bar chart)     | |    (bar chart)          | |
| | [protocol] [bytes] ... | +-------------------+ +-------------------------+ |
| |                        | +-----------------------------------------------+ |
| | Only source_ip is      | | Per-record results   [filter] [All severities]| |
| | mandatory. Aliases     | | TIME   SOURCE   DEST    CLASS     RISK  SEV   | |
| | accepted: bytes,       | | 03:14  203.0..  10.0..  Brute F.  [==] CRIT   | |
| | packets, failed_logins | | 03:02  10.0.1.. 10.0..  Normal    [ ]  LOW    | |
| |                        | | 02:51  198.51.. 10.0..  Port Scan [==] CRIT   | |
| | SAMPLE FILES           | +-----------------------------------------------+ |
| | sample_logs_mixed.csv  |                                                   |
| | sample_logs_normal.csv |                                                   |
| | ..._suspicious.csv     |                                                   |
| | ..._invalid.csv        |                                                   |
| +------------------------+                                                   |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun drops the overnight export onto the drop zone and clicks "Analyze log file". |
| **System response** | The file is decoded, the delimiter sniffed, header aliases normalised, each row validated independently, then every valid row is scored through the same engine path as a manual submission and committed as one transaction. |
| **Expected result** | Five KPI tiles, a severity breakdown, two charts and a filterable per-record table. |
| **Error path** | Uploading `sample_logs_invalid.csv` returns HTTP 201 with 1 row analysed and 4 rejected, each listed with its line number and the specific reason. **A malformed row never aborts the file.** |

---

## Frame 9 - Report generation and handover

```
+==============================================================================+
|  Security Reports                                          [Refresh]         |
|                                                                              |
| +--------------------------+ +---------------------------------------------+ |
| | Generate a report        | | Generated reports                           | |
| |                          | | REPORT     TYPE    PERIOD EVENTS  EXPORT    | |
| | REPORTING PERIOD         | | RPT-000001 Summary 30 days 440   [P][C][J]  | |
| | [Last 30 days        v]  | | Morning handover                            | |
| |                          | +---------------------------------------------+ |
| | REPORT TYPE              |                                                 |
| | (o) Summary report       | +---------------------------------------------+ |
| |     Overall posture...   | | CyberGuard AI Summary Security Report       | |
| | ( ) Threat report        | | Generated 22 Sep 2026 - last 30 days        | |
| | ( ) Incident report      | |                                             | |
| | ( ) Compliance report    | | Total Events 440 | Threats 143 | Alerts 79  | |
| |                          | |                                             | |
| | CUSTOM TITLE             | | +------------+  +------------------------+  | |
| | [Morning handover      ] | | | Severity   |  | Threat categories      |  | |
| |                          | | | (donut)    |  | (bars)                 |  | |
| | +----------------------+ | | +------------+  +------------------------+  | |
| | |  + Generate Report   | | |                                             | |
| | +----------------------+ | | RECOMMENDATIONS                             | |
| |                          | | (1) 27 critical detection(s) were recorded  | |
| | LIVE PREVIEW             | |     in this period. Review each one against | |
| | Total Events      440    | |     the asset owner's change calendar.      | |
| | Threats Detected  143    | | (2) Brute-force patterns were observed.     | |
| | Alerts Raised      79    | |     Enforce account lockout thresholds and  | |
| | Incidents Opened   64    | |     multi-factor authentication.            | |
| | Monitored Assets   12    | | (3) Scanning behaviour was detected...      | |
| +--------------------------+ | (4) 60 incident(s) remain open...           | |
|                              | (5) This report is produced by an academic  | |
|                              |     prototype using simulated telemetry.    | |
|                              +---------------------------------------------+ |
+==============================================================================+
```

| | |
|---|---|
| **User action** | Arjun generates a 30-day summary titled "Morning handover" and downloads the PDF. |
| **System response** | Figures are aggregated live, recommendations are **derived from those figures** (not a fixed list), the report is stored with an `RPT-` code, and ReportLab renders a seven-section A4 PDF. Both the generation and the download are audited. |
| **Expected result** | A PDF downloads and opens correctly; the report remains in the list for re-download as CSV or JSON. |

---

## 2. Storyboard flow summary

```
   Frame 1          Frame 2           Frame 3            Frame 4
   LOGIN     ---->  DASHBOARD  ---->  THREAT      ---->  ALERTS
   authenticate     see the           DETECTION          triage queue
                    overnight         reproduce and      filter to
                    picture           explain the        critical + new
                                      finding
                                                            |
                                                            v
   Frame 9          Frame 8           Frame 7            Frame 5/6
   REPORTS   <----  LOG         <---- RESOLUTION   <----  ALERT DETAIL
   handover         ANALYZER          contain and         + INCIDENT
   document         bulk check        resolve; alerts     read reasons,
                    the rest of       close with the      escalate
                    the export        incident
```

Each frame leads into the next, and the loop closes: the resolution in frame 7
changes the detection-accuracy figure that frame 2 displays on the next shift.

---

## 3. Storyboard to requirement mapping

| Frame | Screen | Requirement | Use case |
|-------|--------|-------------|----------|
| 1 | Login | FR-01 | UC-01 |
| 2 | Dashboard | FR-02 | UC-02, UC-14 |
| 3 | Threat Detection | FR-03, FR-04, FR-05 | UC-03, UC-04, UC-06 |
| 4 | Alerts list | FR-06 | UC-07 |
| 5 | Alert detail | FR-06, FR-12 | UC-07 |
| 6 | Incident investigation | FR-07 | UC-08, UC-09 |
| 7 | Incident resolution | FR-07, FR-12 | UC-09 |
| 8 | Log Analyzer | FR-10 | UC-05 |
| 9 | Reports | FR-11 | UC-12 |
| (not storyboarded in the narrative) | Threat Intelligence | FR-09 | UC-11 |
| (not storyboarded in the narrative) | Assets | FR-08 | UC-10 |
| (not storyboarded in the narrative) | Settings | FR-12, NFR-07 | UC-13, UC-15 |
