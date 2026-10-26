# 22 - Project Report

**Project title:** CyberGuard AI - Intelligent Cyber Threat Detection System
**Course:** BCSE301P - Software Engineering Lab
**Deliverable:** Full-stack working application with a complete Software Engineering artefact set

---

## 1. Abstract

CyberGuard AI is a working, web-based Security Operations Centre platform that
ingests security telemetry, classifies it with an explainable hybrid detection
engine, raises alerts, drives an incident lifecycle, and reports on the outcome.

It was built specifically to demonstrate the Software Engineering Lab syllabus in
a way where the diagrams and the running code are the same thing: the incident
state machine in the design document *is* the transition table the API enforces;
the ER diagram *is* the SQLAlchemy schema; the severity bands in the DFD *are*
the constants the engine uses.

The system is a defensive academic prototype. It analyses simulated telemetry and
performs no scanning, probing or exploitation of any kind.

**Delivered:** 48 backend Python modules, 22 frontend modules, 10 database
entities, ~40 REST endpoints, 12 screens, 117 automated tests (all passing), and
23 documentation artefacts.

---

## 2. Problem statement and objectives

Security teams face more telemetry than they can review by hand, and many
detection tools give a verdict without a reason, which an analyst cannot act on
or defend. The objectives were therefore:

| # | Objective | Met by |
|---|-----------|--------|
| O1 | Classify security telemetry into actionable categories | An 8-category hybrid detection engine |
| O2 | Make every verdict explainable | Each detection carries reasons, per-detector sub-scores, and a recommended defensive action |
| O3 | Support the full analyst workflow, not just detection | Alert triage plus a guarded incident lifecycle |
| O4 | Work without cloud services or paid infrastructure | Runs entirely locally on SQLite; ML is optional |
| O5 | Demonstrate every syllabus experiment against real code | 23 documents, each traced to the implementation |
| O6 | Remain strictly defensive | No outbound network capability anywhere in the system |

---

## 3. System overview

### 3.1 Architecture

```
  Browser (React 18 + Vite + Tailwind + Recharts)
      |  REST / JSON, Bearer token
      v
  Flask application factory
      |
      +-- routes/     11 blueprints, ~40 endpoints, uniform JSON envelope
      +-- services/   7 services: detection, alert, incident, analytics,
      |               report, auth, audit
      +-- ml/         detection engine (no Flask, no database dependency)
      |                 features.py  18 engineered features
      |                 rules.py     7 explainable behavioural rules
      |                 anomaly.py   statistical baseline
      |                 detector.py  fusion, severity, confidence, explanation
      +-- models/     10 SQLAlchemy entities
      +-- utils/      validation, security, errors, CSV, logging
      |
      v
  SQLite (database/cyberguard.db)
```

The dependency rule is strict and one-directional:
`routes -> services -> models -> extensions`, with `ml` depending on nothing
inside the application at all.

### 3.2 The detection engine

Three independent detectors vote on every event:

| Detector | Nature | Contribution |
|----------|--------|--------------|
| Rule bank | Deterministic, fully explainable | 7 behavioural rules with logarithmic magnitude terms |
| Statistical baseline | Unsupervised | Robust z-scores against learned normals, mapped through a saturating curve |
| Machine learning | Optional | RandomForest classifier + IsolationForest novelty detector |

Fusion:

```
  with ML:     weighted = 0.58*rule + 0.18*anomaly + 0.24*ml
  without ML:  weighted = 0.74*rule + 0.26*anomaly

  risk = clamp( max(weighted, 0.85 * rule_score) * sensitivity , 0, 100 )
```

The rule score acts as a **floor**. The statistical and ML detectors contribute
only through the weighted term, so on their own they can raise an event to MEDIUM
for review but never to CRITICAL. This keeps unexplained outliers from flooding
the queue with unactionable "critical" noise.

**Severity bands:** LOW 0-25, MEDIUM 26-50, HIGH 51-75, CRITICAL 76-100.
An alert is raised at 26; an incident opens automatically at 76.

**Categories:** Normal Activity, Brute Force Attempt, Port Scanning Pattern,
Suspicious Login Activity, Network Anomaly, Data Transfer Anomaly,
Denial-of-Service Pattern, Credential Abuse Pattern.

---

## 4. Module specifications for the viva

For every major module: purpose, input, processing, output, and the SE concept it
demonstrates.

### 4.1 Authentication module

| | |
|---|---|
| **Purpose** | Verify identity and protect every other endpoint |
| **Input** | Email, password; thereafter a Bearer token |
| **Processing** | Email format validation, account lookup, PBKDF2 hash verification, active-account check, signed token issue with expiry, audit write |
| **Output** | Session token and user profile, or a non-disclosing 401 |
| **SE concept** | **Decorator pattern** (`@token_required`), **cross-cutting concerns**, security-by-design |
| **Viva point** | An unknown email and a wrong password return a byte-identical message, so the API cannot be used to enumerate accounts. |

### 4.2 Detection engine

| | |
|---|---|
| **Purpose** | Turn raw telemetry into an explainable verdict |
| **Input** | 11 observed fields |
| **Processing** | 18 engineered features -> 7 rules + statistical baseline + optional ML -> weighted fusion with a rule floor -> severity band -> confidence -> explanation assembly |
| **Output** | Classification, risk 0-100, confidence 0.5-0.99, severity, reasons, recommended action, MITRE tactic, sub-scores |
| **SE concept** | **Strategy pattern** (interchangeable rule functions), **Facade** (`detect()` hides eight stages), **dependency isolation** (no Flask, no DB) |
| **Viva point** | Because `ml/` imports nothing from the application, its 18 tests run with no database and no HTTP layer. That isolation is a design decision, not an accident. |

### 4.3 Detection service (orchestration)

| | |
|---|---|
| **Purpose** | Persist a verdict and everything that follows from it |
| **Input** | A validated event plus the acting user |
| **Processing** | Resolve the owning asset -> store the event -> run the engine -> store the result -> conditionally create Threat, Alert and Incident -> update asset risk -> audit -> commit once |
| **Output** | A bundle containing the event, verdict and every created artefact |
| **SE concept** | **Transaction boundary**, **service layer**, **DTO** |
| **Viva point** | A CSV upload calls this with `commit=False` per row and commits once at the end, so a file either lands completely or not at all. |

### 4.4 Incident management

| | |
|---|---|
| **Purpose** | Drive an investigation to a recorded outcome |
| **Input** | A target state, a note, optionally a resolution summary |
| **Processing** | Validate against `INCIDENT_STATE_TRANSITIONS` -> apply -> stamp timestamps -> append attributed history -> cascade alert closure on terminal states -> audit |
| **Output** | The incident plus the transitions that are currently legal |
| **SE concept** | **State pattern**, **behavioural modelling**, **single source of truth** |
| **Viva point** | The API returns `allowed_transitions`, and the UI renders a button only for each. The UI cannot offer an illegal move, and the API would refuse it anyway. |

### 4.5 CSV log analyzer

| | |
|---|---|
| **Purpose** | Analyse many events at once from a real-world export |
| **Input** | A `.csv`/`.txt`/`.log` file, up to 8 MB and 5000 rows |
| **Processing** | Decode with encoding fallbacks -> sniff the delimiter -> normalise header aliases -> validate each row **independently** -> analyse valid rows -> commit once |
| **Output** | Severity counts, distributions, per-record results, and per-row rejection reasons |
| **SE concept** | **Error isolation**, defensive parsing, batch transaction management |
| **Viva point** | A four-row file with two bad rows returns HTTP 201 with one record analysed and two rejections reported by line number. One bad row never kills the upload. |

### 4.6 Analytics engine

| | |
|---|---|
| **Purpose** | Turn the database into the dashboard |
| **Input** | A time window |
| **Processing** | SQL aggregates for totals and six chart series; threat level from unresolved 24-hour alerts; detection quality by source priority; subsystem self-check |
| **Output** | The complete dashboard payload |
| **SE concept** | **Read-only service**, separation of query from command |
| **Viva point** | `detection_quality` never returns a bare number. It returns `source`, `label` and `note` - analyst-confirmed precision when enough alerts have been triaged, otherwise the model's synthetic hold-out score, clearly marked. |

### 4.7 Report module

| | |
|---|---|
| **Purpose** | Produce a shareable summary |
| **Input** | Period, type, optional title, export format |
| **Processing** | Aggregate the period -> derive recommendations **from those figures** -> store as JSON -> render PDF/CSV/JSON on demand |
| **Output** | A stored report and a downloadable file |
| **SE concept** | **Separation of content from presentation**, graceful optional-dependency handling |
| **Viva point** | The recommendations are conditional on the data. A period with no elevated activity produces a different list from one with brute-force findings. |

---

## 5. How CyberGuard AI satisfies the Software Engineering Lab syllabus

| # | Syllabus experiment | Project artefact | Document | Where it lives in the code |
|---|---------------------|------------------|----------|----------------------------|
| 1 | Analysis and identification of suitable process models | Incremental/Agile model selected after comparing Waterfall, Prototyping and Spiral; nine executed increments; risk register | `01_Process_Model.md` | Evidenced by the increment-I7 re-calibration of `ml/rules.py`, `ml/anomaly.py`, `ml/detector.py` |
| 2 | Work Breakdown Structure and estimations | All four WBS views (process, product, geographic, role) with duration, effort, dependencies and responsible role; 445-hour baseline cross-checked against a size-based estimate | `02_WBS_and_Estimation.md` | - |
| 3 | Requirement modelling: Entity Relationship Diagram | 10 entities, 9 relationships with cardinality, keys, indexes, normalisation analysis with documented denormalisation | `04_ER_Diagram.md` | `backend/app/models/` (10 files) |
| 4 | Requirement modelling: Context flow diagram and DFD | Context diagram; Level 0 (7 processes, 8 stores); Level 1 (full decomposition); Level 2 (detection engine and CSV parser); balancing checks at each level | `05`, `06`, `07`, `08` | `routes/`, `services/`, `ml/`, `utils/csv_parser.py` |
| 5 | Requirement modelling: State Transition Diagram | Incident lifecycle (6 states), alert lifecycle (5 states), event processing, asset risk, session state; legal and forbidden transitions | `09_State_Transition_Diagram.md` | `models/incident.py::INCIDENT_STATE_TRANSITIONS` |
| 6 | OO design: Use case and class models | 3 actors, 17 use cases with include/extend relationships, 5 detailed specifications with extensions; class diagrams for entity, control and service classes with multiplicity | `10`, `11` | Whole code base |
| 7 | OO design: Interaction models | 7 sequence diagrams with alternate flows; 6 communication diagrams with Dewey-numbered messages | `12`, `13` | Whole code base |
| 8 | OO design: Package, component and deployment models | Package diagram with a stated dependency rule; component diagram with provided/required interfaces and a degradation matrix; deployment diagram for development and production topologies | `14`, `15`, `16` | Package layout of `backend/app/` and `frontend/src/` |
| 9 | Test case design; functional and non-functional testing | 117 automated cases across 12 TC groups using equivalence partitioning, boundary values, state-transition and property testing; 11 manual scenarios; measured non-functional results | `17`, `18`, `19` | `backend/tests/` (5 files) |
| 10 | Storyboarding and UI design modelling | A 9-frame narrative storyboard following one analyst through a complete shift; full UI design specification with colour system, components and accessibility | `20`, `21` | `frontend/src/` |

### 5.1 The mapping the brief asked for, stated directly

| Concept | CyberGuard AI realisation |
|---------|---------------------------|
| Process Model | Incremental/Agile development with a documentation-inclusive Definition of Done |
| WBS | CyberGuard project task decomposition in four views |
| ERD | The CyberGuard database structure - 10 entities implemented as SQLAlchemy models |
| DFD | Security event processing, decomposed to the detection engine's eight stages |
| State Diagram | The incident lifecycle, enforced by the API |
| Use Case | Analyst and administrator interactions with the console |
| Class Diagram | The object-oriented architecture of entities, services and the engine |
| Sequence Diagram | The threat-detection interaction, end to end |
| Component Diagram | The system architecture with its degradation paths |
| Deployment Diagram | The two-process local deployment on Windows 11 |
| Testing | 117 backend test cases plus manual frontend scenarios |
| Storyboard | The analyst's shift, from login to handover report |
| UI Design | The Security Operations Centre dashboard |

---

## 6. Results

### 6.1 Delivered scope

| Metric | Value |
|--------|-------|
| Backend Python modules | 48 (plus 6 test modules) |
| Frontend modules | 22 |
| Database entities | 10 |
| REST endpoints | ~40 across 11 blueprints |
| Frontend screens | 12 |
| Reusable UI primitives | ~20 |
| Chart components | 7 |
| Detection categories | 8 |
| Engineered features | 18 |
| Behavioural rules | 7 |
| Automated tests | 117 (100% passing) |
| Documentation artefacts | 23 |
| Seeded demonstration events | 320 |

### 6.2 Measured performance

All figures measured on Windows 11 / Python 3.10.0; procedures in document 19.

| Measurement | Result |
|-------------|--------|
| Detection latency, `hybrid-ml` (n=2000) | mean 7.083 ms, p95 9.890 ms, p99 13.672 ms |
| Detection latency, `hybrid-rules` (n=2000) | mean 0.033 ms, p95 0.069 ms |
| Throughput, rules mode | ~29 900 events/second |
| Heaviest API endpoint (`/api/analytics`) | mean 14.0 ms |
| Dashboard aggregation | mean 13.4 ms |
| CSV upload, 120 rows | 1475 ms total, 12.3 ms per row |
| Frontend bundle | 824 kB raw, 231 kB gzipped |
| Test suite | 117 passed in 51.16 s |

### 6.3 Detection behaviour on the synthetic population

Measured over 1000 generated events:

| Severity | Share |
|----------|-------|
| LOW | 57.7% |
| MEDIUM | 9.8% |
| HIGH | 15.5% |
| CRITICAL | 17.0% |

A realistic pyramid with all four bands populated - which, as section 7 records,
was **not** true of the first implementation.

---

## 7. Engineering problems encountered and how they were solved

This section is deliberately honest about what went wrong. It is the most useful
part of the report for a viva.

### 7.1 Severity saturation (the significant one)

**Symptom.** After the first end-to-end build, the seeded dashboard showed
`LOW=177, MEDIUM=21, HIGH=0, CRITICAL=140`. Every simulated attack landed in the
top band and the HIGH band was completely empty, so the severity chart and the
alert queue conveyed no prioritisation at all.

**Diagnosis.** Three compounding causes:

1. The rule bank used **linear** magnitude terms, so 20 failed logins and 2000
   failed logins both hit the 100 ceiling.
2. The statistical scorer mapped the combined z-score linearly, so any
   attack-shaped event saturated at 100.
3. The fusion floor was `0.85 * max(rule, anomaly, ml)`, which let the
   statistical detector alone drive an event to CRITICAL.
4. The data generator produced every attack at full intensity, which is not how
   real telemetry is distributed.

**Fix.**

| Change | File |
|--------|------|
| Logarithmic magnitude terms, e.g. `38 + 30*log10(failed/4)` | `ml/rules.py` |
| Saturating exponential mapping `100 * (1 - e^(-c/9))` | `ml/anomaly.py` |
| Floor changed to `0.85 * rule_score` only, so statistics and ML cannot alone reach CRITICAL | `ml/detector.py` |
| Low/medium/high intensity tiers, weighted towards mild | `ml/generate_dataset.py` |

**Result.** `LOW 57.7% / MEDIUM 9.8% / HIGH 15.5% / CRITICAL 17.0%`.

**Prevention.** Two regression tests now make this impossible to reintroduce
silently: `test_generated_dataset_covers_every_severity_band` asserts all four
bands are populated, and `test_risk_grows_with_attack_intensity` asserts the
score is monotonic in attack intensity.

### 7.2 ML inference 1800x slower than necessary

**Symptom.** Performance measurement showed `hybrid-ml` mode averaging
**45.353 ms** per event against 0.025 ms for rules mode.

**Diagnosis.** Timing the sub-calls isolated it to
`RandomForest.predict_proba` at 43 ms for a **single** sample. The models were
trained and saved with `n_jobs=-1`. That is correct for fitting, but at inference
the engine scores one event at a time, and joblib spent far longer dispatching to
a thread pool than doing the work.

**Fix.** Force `n_jobs = 1` on the models at load time in
`ThreatDetector._load_models()`; training still uses all cores.

**Result.** 45.353 ms -> **7.083 ms** mean, a 6.4x improvement. The test suite
also dropped from 78 s to 51 s as a side effect.

### 7.3 Wrong HTTP status for a wrong password

**Symptom.** A wrong password shorter than six characters returned HTTP 422
(validation error) instead of 401.

**Diagnosis.** The registration password-strength rule was being applied at
sign-in. Besides being the wrong status code, it leaked information: a 422 told
an attacker the password they tried was too short to be the real one.

**Fix.** Login now checks only that a password was supplied; the strength rule
applies to password *changes*.

### 7.4 A failing test that was itself wrong

**Symptom.** `test_resolving_an_incident_closes_its_alerts` failed, asserting an
alert was still `NEW` after its incident was resolved.

**Diagnosis.** The test escalated a CRITICAL alert that **already had an
auto-created incident in NEW**, then tried to move it straight to CONTAINED. The
API correctly refused with 409, because NEW -> CONTAINED is not a legal
transition.

**Resolution.** The code was right and the test encoded a wrong assumption. The
test was corrected to investigate first, and a new test was added for the
property that had been misunderstood -
`test_escalating_an_already_linked_alert_returns_the_same_incident`.

This is worth stating plainly: the first instinct on a red test is to change the
code, and here that would have introduced a real defect.

### 7.5 Build failure on an invalid Tailwind opacity

`border-white/12` is not on Tailwind's default opacity scale, so `npm run build`
failed. Replaced with `/15` throughout.

---

## 8. Known limitations

Stated plainly rather than buried.

### 8.1 Security

- Tokens cannot be revoked before expiry; there is no server-side session store.
- No rate limiting on login, so repeated attempts are not throttled.
- No HTTPS in the shipped topology.
- Role checks are coarse: any authenticated user reaches most endpoints.
- No penetration testing or dependency vulnerability scanning was performed.
- Demo credentials are intentionally published for the demonstration.

### 8.2 Data and detection

- **All telemetry is synthetic.** The system has never seen a real network
  capture, and the reported model accuracy is measured on synthetic hold-out data
  whose classes are well separated by construction.
- The rule thresholds are calibrated against that synthetic population, not
  against production traffic.
- There is no cross-event correlation: each event is scored in isolation, so a
  slow distributed scan spread across many events would not be detected.
- Indicators are simulated and are not matched automatically against events.

### 8.3 Scale and operations

- SQLite allows one writer at a time - the first real ceiling.
- CSV uploads hold parsed rows in memory, hence the 5000-row cap.
- Single-process development server with no clustering or failover.
- No concurrent-load testing was performed.

### 8.4 Testing

- No automated frontend tests; React is verified manually and by the build.
- No cross-browser matrix, no real-device testing.
- No automated accessibility audit or screen-reader testing.

---

## 9. Future enhancements

| Priority | Enhancement | Rationale |
|----------|-------------|-----------|
| High | Cross-event correlation (group by source over a time window) | Would catch slow and distributed activity that per-event scoring misses - the most significant detection gap |
| High | Automatic indicator matching against incoming events | Makes the intelligence feed operational rather than informational |
| High | Frontend test suite (Vitest + React Testing Library) | Closes the largest gap in the test strategy |
| Medium | Server-side session store for immediate token revocation | Removes a stated security limitation |
| Medium | Rate limiting on authentication and upload | Removes a stated security limitation |
| Medium | Route-based code splitting | The 824 kB bundle is a single chunk |
| Medium | PostgreSQL support in the deployment guide | Lifts the single-writer ceiling; needs only a `DATABASE_URL` change plus one `strftime` query |
| Medium | Real packet-capture ingestion (PCAP or syslog) | Would allow calibration against genuine traffic |
| Low | Light theme | The preference is stored but only the dark theme ships |
| Low | Scheduled report delivery | Currently on-demand only |
| Low | WebSocket live feed instead of polling | The dashboard polls every 45 seconds |

---

## 10. Conclusion

CyberGuard AI delivers a complete, working full-stack security platform together
with the Software Engineering artefacts that describe it. Its distinguishing
characteristic is that the documentation and the implementation are the same
system viewed from two angles: the state transition diagram is the transition
table the API enforces, the ER diagram is the schema SQLAlchemy creates, and the
severity bands in the Level 2 DFD are the constants the engine applies.

The engineering value of the project lies as much in section 7 as in section 6.
The severity-saturation defect would not have been found by a process that wrote
the documentation after the code: it was only visible once a real dashboard was
rendered from real seeded data, and fixing it required changing the scoring
mathematics, the fusion rule and the data generator together. That is the
incremental process model doing what it was selected to do.

The system is explicitly a defensive academic prototype. It analyses simulated
telemetry, it makes no production security claims, and every figure it reports
states where it came from.

---

## Appendix A - Document index

| # | Document | Syllabus experiment |
|---|----------|---------------------|
| 01 | Process Model | 1 |
| 02 | WBS and Estimation | 2 |
| 03 | Requirements Specification | - |
| 04 | ER Diagram | 3 |
| 05 | Context Flow Diagram | 4 |
| 06 | DFD Level 0 | 4 |
| 07 | DFD Level 1 | 4 |
| 08 | DFD Level 2 | 4 |
| 09 | State Transition Diagram | 5 |
| 10 | Use Case Model | 6 |
| 11 | Class Model | 6 |
| 12 | Sequence Diagrams | 7 |
| 13 | Communication Diagrams | 7 |
| 14 | Package Diagram | 8 |
| 15 | Component Diagram | 8 |
| 16 | Deployment Diagram | 8 |
| 17 | Test Case Design | 9 |
| 18 | Functional Testing | 9 |
| 19 | Non-Functional Testing | 9 |
| 20 | Storyboard | 10 |
| 21 | UI Design Modelling | 10 |
| 22 | Project Report | - |
| - | API Documentation | - |

## Appendix B - Technology stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend framework | React | 18.3.1 |
| Build tool | Vite | 5.4.8 |
| Styling | Tailwind CSS | 3.4.13 |
| Charts | Recharts | 2.12.7 |
| Icons | Lucide React | 0.446.0 |
| Routing | React Router | 6.26.2 |
| HTTP client | Axios | 1.7.7 |
| Backend framework | Flask | 3.0.3 |
| ORM | SQLAlchemy | 2.0.31 |
| Database | SQLite | embedded |
| ML | scikit-learn | 1.5.1 (optional) |
| Numerics | NumPy / pandas | 1.26.4 / 2.2.2 |
| PDF | ReportLab | 4.2.2 (optional) |
| Testing | pytest | 8.3.2 |
| Runtime | Python / Node.js | 3.10+ / 18+ |
