# 01 - Software Process Model Analysis and Selection

**Project:** CyberGuard AI - Intelligent Cyber Threat Detection System
**Lab experiment:** 1 - Analysis and identification of the suitable process models

---

## 1. Purpose

This document analyses the candidate software process models for CyberGuard AI,
justifies the model chosen, and shows how the chosen model was actually applied
to build the system.

---

## 2. Project characteristics that drive the choice

| # | Characteristic | Observation for CyberGuard AI |
|---|----------------|-------------------------------|
| C1 | Requirement stability | Core requirements (detect, alert, investigate, report) were clear, but detection rules and the UI evolved substantially during development. |
| C2 | Team size | Small team (1-4 students), co-located, high communication bandwidth. |
| C3 | Duration | Short - one academic semester, roughly 8 weeks of active development. |
| C4 | Technical risk | Medium-high. The detection engine's scoring behaviour could not be fully specified in advance; it had to be tuned against generated data. |
| C5 | Feedback need | High. The dashboard and detection quality could only be judged by running the system and looking at the output. |
| C6 | Deliverable | A demonstrable, working product plus a complete documentation set. |
| C7 | User availability | The "customer" (lab examiner) reviews the product at fixed checkpoints, not continuously. |

---

## 3. Candidate models evaluated

### 3.1 Waterfall

Sequential: Requirements -> Design -> Implementation -> Testing -> Maintenance.

| Aspect | Assessment |
|--------|------------|
| Strength | Produces exactly the documentation set this lab requires; every phase has a clear artefact. |
| Strength | Easy to plan and to report progress against. |
| Weakness | Assumes requirements are frozen after phase 1. **This failed in practice**: the risk-fusion formula and the severity distribution had to be re-tuned after we saw the first seeded dashboard. |
| Weakness | Testing happens only at the end, so defects in the detection engine would surface too late. |
| **Verdict** | **Rejected** as the primary model - it cannot absorb C1 and C4. |

### 3.2 Prototyping model

Build a throw-away or evolutionary prototype, get feedback, refine.

| Aspect | Assessment |
|--------|------------|
| Strength | Excellent fit for the dashboard and for calibrating the detection engine. |
| Weakness | On its own it produces weak documentation and risks an unstructured code base. |
| **Verdict** | **Adopted as a technique inside the chosen model**, not as the overall model. |

### 3.3 Spiral model

Risk-driven iterations, each with risk analysis, engineering and evaluation.

| Aspect | Assessment |
|--------|------------|
| Strength | Explicit risk management, which suits the uncertain detection logic (C4). |
| Weakness | Heavyweight. The formal risk-analysis phase per cycle is disproportionate for an 8-week student project. |
| **Verdict** | **Rejected** - correct instincts, too much ceremony for C2/C3. |

### 3.4 Incremental / Agile (Scrum-style iterations)

Deliver the system in working increments; each increment is analysed, designed,
built and tested.

| Aspect | Assessment |
|--------|------------|
| Strength | Directly addresses C1, C4 and C5 - each increment is runnable and can be evaluated. |
| Strength | Fits a small co-located team (C2) and a short timeline (C3). |
| Strength | Working software exists from increment 2 onwards, which de-risks the final demonstration (C6). |
| Weakness | Agile de-emphasises documentation, but this lab *requires* documentation. |
| Mitigation | Each increment ends with a documentation task; the documents are versioned with the code rather than written at the end. |
| **Verdict** | **SELECTED** |

---

## 4. Decision

> **CyberGuard AI follows an Incremental (Agile-style) process model, with
> evolutionary prototyping used inside each increment for the user interface and
> the detection engine, and a documentation deliverable attached to every
> increment so that the artefacts required by the lab are produced continuously
> rather than retrospectively.**

### 4.1 Why not pure Agile

Pure Agile would leave the lab's diagram set unwritten. The adaptation is: a
**Definition of Done** for every increment that includes "the affected
documentation is updated". This is why, for example, the incident state machine
in `documentation/09_State_Transition_Diagram.md` and the transition table in
`backend/app/models/incident.py` cannot drift apart - updating one without the
other fails the increment's Definition of Done.

---

## 5. Increments actually executed

| Increment | Goal | Key outputs | Documentation produced |
|-----------|------|-------------|------------------------|
| **I0 - Inception** | Scope, feasibility, process model | Requirement list, architecture sketch | 01, 02, 03 |
| **I1 - Data foundation** | Domain model and persistence | 10 SQLAlchemy models, `create_all`, seed skeleton | 04 (ERD) |
| **I2 - Detection engine** | Explainable risk scoring | `features.py`, `rules.py`, `anomaly.py`, `detector.py` | 05-08 (DFDs) |
| **I3 - REST API** | Expose the engine and the data | 11 blueprints, error handlers, auth | 10, 11 (Use case, Class) |
| **I4 - Frontend shell** | Navigation, auth, layout | Login, layout, routing, API client | 20, 21 (Storyboard, UI) |
| **I5 - SOC pages** | Dashboard, alerts, incidents, assets | All 11 pages wired to real endpoints | 12, 13 (Sequence, Communication) |
| **I6 - Analysis features** | Log analyzer, reports, intelligence | CSV pipeline, PDF/CSV/JSON export | 14-16 (Package, Component, Deployment) |
| **I7 - Hardening** | Tests, tuning, validation | 117 pytest cases, engine re-calibration | 17, 18, 19 (Test cases, testing) |
| **I8 - Consolidation** | Consistency audit, README | Final audit, setup guide | 22 (Project report) |

### 5.1 Evidence that the iterative model was genuinely used

The most important example is **increment I7**. After I2 the engine was
"finished" by a Waterfall definition: it classified every attack type correctly.
But when the seeded dashboard was first rendered, the severity distribution was
`LOW=177, MEDIUM=21, HIGH=0, CRITICAL=140` - every attack saturated the top band
and the HIGH band was empty, making the charts meaningless.

The iteration that followed changed three things:

1. **`anomaly.py`** - replaced the linear z-score mapping with a saturating
   exponential curve, so a 3-sigma deviation and a 30-sigma deviation no longer
   score the same.
2. **`detector.py`** - made the rule score the floor of the fused score, so the
   statistical and ML detectors can raise an event to MEDIUM for review but
   cannot single-handedly drive it to CRITICAL.
3. **`generate_dataset.py`** - added low/medium/high intensity tiers so that
   most simulated attacks are mild, as in real telemetry.

The resulting distribution is `LOW 58%, MEDIUM 10%, HIGH 15%, CRITICAL 17%`.
A Waterfall process would not have surfaced this defect until after the
documentation was already written.

---

## 6. Process model applied to the phases

```
        +-------------------------------------------------+
        |              INCREMENT n                        |
        |                                                 |
        |  Requirements  ->  Design  ->  Build  ->  Test   |
        |       ^                                    |     |
        |       |          Evaluate / demo           |     |
        |       +------------------------------------+     |
        |                                                 |
        |  Definition of Done:                            |
        |    - feature works end to end (UI -> API -> DB)  |
        |    - pytest suite green                         |
        |    - affected documentation updated             |
        +-------------------------------------------------+
                              |
                              v
                       INCREMENT n+1
```

---

## 7. Risk register maintained across increments

| ID | Risk | Likelihood | Impact | Mitigation actually applied |
|----|------|-----------|--------|------------------------------|
| R1 | Detection engine produces unrealistic or saturated scores | High | High | Increment I7 re-calibration; regression test `test_risk_grows_with_attack_intensity` and `test_generated_dataset_covers_every_severity_band` lock the behaviour in. |
| R2 | scikit-learn unavailable or model not trained on the demo machine | Medium | High | Engine degrades to `hybrid-rules` mode; `test_engine_works_without_any_trained_model` proves the system still functions. |
| R3 | Frontend and backend contracts drift | Medium | Medium | Single API client module (`services/api.js`); `GET /api` returns a live endpoint index used in the final consistency audit. |
| R4 | Documentation diverges from the implementation | High | High | Definition of Done ties them together; the state machine, severity bands and ER relationships exist once in code and are described from there. |
| R5 | Scope creep into offensive security features | Low | Very High | Explicit scope rule: the system only reads numbers supplied to it. No scanning, probing or exploitation code exists anywhere in the repository. |
| R6 | Demonstration fails because the database is empty | Medium | Medium | `seed_database.py` produces a full, realistic dataset in one command. |

---

## 8. Traceability

| Lab requirement | Where satisfied |
|-----------------|-----------------|
| Identify suitable process model | Sections 3 and 4 of this document |
| Justify the selection | Section 3 comparison table, Section 4.1 |
| Show the model in use | Section 5 increments, Section 5.1 evidence |
| Risk handling | Section 7 |
