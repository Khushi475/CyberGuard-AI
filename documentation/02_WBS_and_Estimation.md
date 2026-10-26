# 02 - Work Breakdown Structure and Estimation

**Project:** CyberGuard AI - Intelligent Cyber Threat Detection System
**Lab experiment:** 2 - Work Breakdown Structure (process, product, geographic, role based) and estimations

---

> **Important statement about the numbers in this document.**
> Every duration and effort figure below is a **planning estimate** produced
> before or during development using expert judgement and analogy with similar
> student projects. They are **not** measured timesheet data and must not be
> read as recorded project history. Where a figure was revised after building
> the component, this is stated explicitly in Section 7.

---

## 1. Process-Based WBS

Decomposes the work by **software engineering process phase**.

```
1.0 CyberGuard AI (Process-Based)
|
+-- 1.1 Requirements Engineering
|    +-- 1.1.1 Stakeholder and actor identification
|    +-- 1.1.2 Functional requirements elicitation (FR-01..FR-12)
|    +-- 1.1.3 Non-functional requirements (NFR-01..NFR-07)
|    +-- 1.1.4 Scope and safety boundary definition (defensive-only rule)
|    +-- 1.1.5 Requirements review and sign-off
|
+-- 1.2 Analysis and Modelling
|    +-- 1.2.1 Structural modelling (ER diagram)
|    +-- 1.2.2 Functional modelling (Context diagram, DFD 0/1/2)
|    +-- 1.2.3 Behavioural modelling (State transition diagram)
|    +-- 1.2.4 Object-oriented modelling (Use case, Class)
|    +-- 1.2.5 Interaction modelling (Sequence, Communication)
|
+-- 1.3 Design
|    +-- 1.3.1 Layered architecture definition
|    +-- 1.3.2 Database schema design
|    +-- 1.3.3 REST API contract design
|    +-- 1.3.4 Detection engine algorithm design
|    +-- 1.3.5 UI/UX design and storyboarding
|    +-- 1.3.6 Package, component and deployment design
|
+-- 1.4 Implementation
|    +-- 1.4.1 Database layer (models, migrations, seeding)
|    +-- 1.4.2 Detection engine (features, rules, anomaly, ML, fusion)
|    +-- 1.4.3 Service layer (detection, alert, incident, analytics, report, audit)
|    +-- 1.4.4 REST API layer (11 blueprints, error handling, auth)
|    +-- 1.4.5 Frontend foundation (routing, auth, API client, design system)
|    +-- 1.4.6 Frontend pages (11 screens)
|    +-- 1.4.7 Integration and wiring
|
+-- 1.5 Testing
|    +-- 1.5.1 Test case design
|    +-- 1.5.2 Unit testing (detection engine)
|    +-- 1.5.3 Integration testing (API endpoints)
|    +-- 1.5.4 Functional testing (end-to-end workflows)
|    +-- 1.5.5 Non-functional test procedures
|    +-- 1.5.6 Defect fixing and regression
|
+-- 1.6 Documentation
|    +-- 1.6.1 SE lab artefacts (22 documents)
|    +-- 1.6.2 API documentation
|    +-- 1.6.3 README and setup guide
|
+-- 1.7 Deployment and Demonstration
     +-- 1.7.1 Local environment setup scripts
     +-- 1.7.2 Seed data preparation
     +-- 1.7.3 Final consistency audit
     +-- 1.7.4 Viva demonstration rehearsal
```

### 1.1 Estimation table (process-based)

| WBS ID | Task | Duration (days) | Effort (person-hours) | Dependencies | Responsible role |
|--------|------|-----------------|------------------------|--------------|------------------|
| 1.1.1 | Actor identification | 0.5 | 3 | - | Business Analyst |
| 1.1.2 | Functional requirements | 1.5 | 10 | 1.1.1 | Business Analyst |
| 1.1.3 | Non-functional requirements | 1.0 | 6 | 1.1.2 | Business Analyst |
| 1.1.4 | Scope / safety boundary | 0.5 | 3 | 1.1.2 | Project Lead |
| 1.1.5 | Requirements review | 0.5 | 4 | 1.1.3, 1.1.4 | All |
| 1.2.1 | ER diagram | 1.0 | 7 | 1.1.5 | Database Designer |
| 1.2.2 | Context diagram + DFD 0/1/2 | 2.0 | 13 | 1.1.5 | System Analyst |
| 1.2.3 | State transition diagram | 0.5 | 4 | 1.1.5 | System Analyst |
| 1.2.4 | Use case + class model | 1.5 | 10 | 1.1.5 | System Analyst |
| 1.2.5 | Sequence + communication diagrams | 1.5 | 10 | 1.2.4 | System Analyst |
| 1.3.1 | Architecture definition | 1.0 | 7 | 1.2.* | Software Architect |
| 1.3.2 | Database schema | 1.0 | 7 | 1.2.1 | Database Designer |
| 1.3.3 | REST API contract | 1.0 | 7 | 1.3.1 | Backend Developer |
| 1.3.4 | Detection algorithm design | 2.0 | 14 | 1.3.1 | ML Engineer |
| 1.3.5 | UI/UX design + storyboard | 2.0 | 13 | 1.2.4 | UI/UX Designer |
| 1.3.6 | Package/component/deployment design | 1.0 | 6 | 1.3.1 | Software Architect |
| 1.4.1 | Database layer | 2.0 | 14 | 1.3.2 | Backend Developer |
| 1.4.2 | Detection engine | 4.0 | 30 | 1.3.4, 1.4.1 | ML Engineer |
| 1.4.3 | Service layer | 3.0 | 22 | 1.4.1, 1.4.2 | Backend Developer |
| 1.4.4 | REST API layer | 3.0 | 22 | 1.4.3 | Backend Developer |
| 1.4.5 | Frontend foundation | 2.5 | 18 | 1.3.5 | Frontend Developer |
| 1.4.6 | Frontend pages | 5.0 | 38 | 1.4.5, 1.4.4 | Frontend Developer |
| 1.4.7 | Integration and wiring | 2.0 | 15 | 1.4.4, 1.4.6 | Full-stack Developer |
| 1.5.1 | Test case design | 1.0 | 7 | 1.1.5 | QA Engineer |
| 1.5.2 | Unit testing | 1.5 | 11 | 1.4.2 | QA Engineer |
| 1.5.3 | Integration testing | 2.0 | 15 | 1.4.4 | QA Engineer |
| 1.5.4 | Functional testing | 1.5 | 11 | 1.4.7 | QA Engineer |
| 1.5.5 | Non-functional test procedures | 1.0 | 7 | 1.4.7 | QA Engineer |
| 1.5.6 | Defect fixing and regression | 2.0 | 15 | 1.5.2-1.5.5 | All developers |
| 1.6.1 | SE lab documentation | 3.5 | 26 | all design tasks | Documentation Lead |
| 1.6.2 | API documentation | 1.0 | 7 | 1.4.4 | Backend Developer |
| 1.6.3 | README and setup guide | 1.0 | 7 | 1.7.1 | Documentation Lead |
| 1.7.1 | Environment setup scripts | 0.5 | 4 | 1.4.* | DevOps / Full-stack |
| 1.7.2 | Seed data preparation | 1.0 | 7 | 1.4.1, 1.4.2 | Backend Developer |
| 1.7.3 | Final consistency audit | 1.5 | 11 | everything | Project Lead + QA |
| 1.7.4 | Demonstration rehearsal | 0.5 | 4 | 1.7.3 | All |
| | **TOTAL** | **~57 working days (elapsed, with parallelism ~40)** | **~415 person-hours** | | |

---

## 2. Product-Based WBS

Decomposes the work by **deliverable component** rather than by phase.

```
2.0 CyberGuard AI (Product-Based)
|
+-- 2.1 Backend Application
|    +-- 2.1.1 Application factory and configuration
|    +-- 2.1.2 Data model package (10 entities)
|    +-- 2.1.3 Detection engine package
|    |     +-- 2.1.3.1 Feature extraction (18 features)
|    |     +-- 2.1.3.2 Rule bank (7 behavioural rules)
|    |     +-- 2.1.3.3 Statistical baseline
|    |     +-- 2.1.3.4 ML models (RandomForest + IsolationForest)
|    |     +-- 2.1.3.5 Fusion and severity mapping
|    |     +-- 2.1.3.6 Synthetic data generator
|    +-- 2.1.4 Service package
|    +-- 2.1.5 REST API package (11 blueprints)
|    +-- 2.1.6 Utility package (validation, errors, CSV, security, logging)
|
+-- 2.2 Frontend Application
|    +-- 2.2.1 Design system (Tailwind theme, component primitives)
|    +-- 2.2.2 Application shell (sidebar, top bar, routing, guards)
|    +-- 2.2.3 State and services (auth context, toast context, API client, hooks)
|    +-- 2.2.4 Chart library wrappers
|    +-- 2.2.5 Pages
|          +-- 2.2.5.1 Login          +-- 2.2.5.7 Log Analyzer
|          +-- 2.2.5.2 Dashboard      +-- 2.2.5.8 Assets
|          +-- 2.2.5.3 Threat Detection +-- 2.2.5.9 Reports
|          +-- 2.2.5.4 Alerts         +-- 2.2.5.10 Settings
|          +-- 2.2.5.5 Incidents      +-- 2.2.5.11 Not Found
|          +-- 2.2.5.6 Incident Details / Threat Intelligence
|
+-- 2.3 Database
|    +-- 2.3.1 SQLite schema (10 tables)
|    +-- 2.3.2 Relationships and indexes
|    +-- 2.3.3 Seed script
|
+-- 2.4 Data Assets
|    +-- 2.4.1 Synthetic event generator
|    +-- 2.4.2 Sample CSV log files (4 files)
|    +-- 2.4.3 Trained model artefacts
|
+-- 2.5 Test Suite
|    +-- 2.5.1 Fixtures and harness
|    +-- 2.5.2 Authentication tests
|    +-- 2.5.3 Detection engine tests
|    +-- 2.5.4 Event / upload tests
|    +-- 2.5.5 Alert / incident tests
|    +-- 2.5.6 Dashboard / asset / report tests
|
+-- 2.6 Documentation Set
     +-- 2.6.1 Requirements and process documents
     +-- 2.6.2 Analysis and design diagrams
     +-- 2.6.3 Testing documents
     +-- 2.6.4 README, API reference, project report
```

### 2.1 Estimation table (product-based)

| WBS ID | Deliverable | Size indicator | Duration (days) | Effort (hours) | Dependencies | Responsible role |
|--------|-------------|----------------|-----------------|----------------|--------------|------------------|
| 2.1.1 | App factory + config | 3 modules | 0.5 | 4 | - | Backend Developer |
| 2.1.2 | Data models | 10 entities | 2.0 | 14 | 2.1.1 | Database Designer |
| 2.1.3 | Detection engine | 7 modules | 4.0 | 30 | 2.1.2 | ML Engineer |
| 2.1.4 | Service layer | 7 services | 3.0 | 22 | 2.1.3 | Backend Developer |
| 2.1.5 | REST API | 11 blueprints, 40+ routes | 3.0 | 22 | 2.1.4 | Backend Developer |
| 2.1.6 | Utilities | 6 modules | 1.5 | 11 | 2.1.1 | Backend Developer |
| 2.2.1 | Design system | theme + ~20 primitives | 1.5 | 11 | - | UI/UX Designer |
| 2.2.2 | Application shell | layout + routing | 1.0 | 8 | 2.2.1 | Frontend Developer |
| 2.2.3 | State and services | 2 contexts, 3 hooks, API client | 1.0 | 8 | 2.2.2 | Frontend Developer |
| 2.2.4 | Chart wrappers | 7 chart types | 1.0 | 8 | 2.2.1 | Frontend Developer |
| 2.2.5 | Pages | 12 screens | 5.0 | 38 | 2.2.3, 2.1.5 | Frontend Developer |
| 2.3.1-3 | Database + seed | 10 tables, seeder | 1.5 | 11 | 2.1.2 | Database Designer |
| 2.4.1-3 | Data assets | generator, 4 CSVs, models | 1.5 | 11 | 2.1.3 | ML Engineer |
| 2.5.1-6 | Test suite | 117 test cases | 4.0 | 30 | 2.1.5, 2.2.5 | QA Engineer |
| 2.6.1-4 | Documentation | 22 documents | 5.0 | 38 | all | Documentation Lead |
| | **TOTAL** | | **~36 days** | **~266 hours** | | |

> The product-based total is lower than the process-based total because the
> process-based WBS also charges the analysis, review, audit and rehearsal
> activities that do not map onto a single shippable component. Both views are
> retained because the lab asks for both, and the difference (~150 hours) is
> itself a useful illustration: roughly 35% of the effort on this project is
> engineering process rather than artefact construction.

---

## 3. Geographic-Based WBS

Decomposes the work by **location where it is performed**. For an academic
project the "sites" are the physical and virtual places the team works.

```
3.0 CyberGuard AI (Geographic-Based)
|
+-- 3.1 On-Campus Laboratory (VIT lab, supervised sessions)
|    +-- 3.1.1 Requirements workshops with the faculty guide
|    +-- 3.1.2 Design reviews and diagram walkthroughs
|    +-- 3.1.3 Mid-term demonstration
|    +-- 3.1.4 Final viva demonstration
|    +-- 3.1.5 Lab-machine installation validation (Windows 11)
|
+-- 3.2 Home / Hostel Development Environment
|    +-- 3.2.1 Backend implementation
|    +-- 3.2.2 Frontend implementation
|    +-- 3.2.3 Detection engine development and tuning
|    +-- 3.2.4 Unit and integration test authoring
|    +-- 3.2.5 Documentation writing
|
+-- 3.3 Shared Online Workspace (repository and issue tracker)
|    +-- 3.3.1 Source control and branching
|    +-- 3.3.2 Code review
|    +-- 3.3.3 Issue and defect tracking
|    +-- 3.3.4 Document versioning
|
+-- 3.4 Local Runtime Environment (each developer's machine)
     +-- 3.4.1 Python virtual environment
     +-- 3.4.2 Node.js toolchain
     +-- 3.4.3 SQLite database instance
     +-- 3.4.4 Local model training runs
```

### 3.1 Estimation table (geographic-based)

| WBS ID | Location | Activities | Duration (days) | Effort (hours) | Constraint | Responsible role |
|--------|----------|-----------|-----------------|----------------|------------|------------------|
| 3.1.1 | Campus lab | Requirements workshops | 1.0 | 8 (team) | Only during scheduled lab hours | All + Faculty Guide |
| 3.1.2 | Campus lab | Design reviews | 1.0 | 8 (team) | Requires guide availability | All + Faculty Guide |
| 3.1.3 | Campus lab | Mid-term demo | 0.5 | 4 (team) | Fixed calendar date | All |
| 3.1.4 | Campus lab | Final viva | 0.5 | 4 (team) | Fixed calendar date | All |
| 3.1.5 | Campus lab | Install validation on lab PC | 0.5 | 4 | Lab machines may lack admin rights | DevOps / Full-stack |
| 3.2.1 | Home | Backend build | 7.0 | 52 | Individual working hours | Backend Developer |
| 3.2.2 | Home | Frontend build | 7.0 | 54 | Individual working hours | Frontend Developer |
| 3.2.3 | Home | Engine build and tuning | 4.0 | 30 | Needs local CPU for training | ML Engineer |
| 3.2.4 | Home | Test authoring | 4.0 | 30 | - | QA Engineer |
| 3.2.5 | Home | Documentation | 5.0 | 38 | - | Documentation Lead |
| 3.3.1 | Online | Source control | continuous | 6 | Network dependency | All |
| 3.3.2 | Online | Code review | continuous | 14 | Reviewer availability | All |
| 3.3.3 | Online | Defect tracking | continuous | 6 | - | QA Engineer |
| 3.3.4 | Online | Document versioning | continuous | 4 | - | Documentation Lead |
| 3.4.1-4 | Local machines | Environment setup and training runs | 1.5 | 12 | Windows 11, Python 3.10+, Node 18+ | All |
| | **TOTAL** | | **~33 days elapsed** | **~274 hours** | | |

### 3.2 Why a geographic WBS matters here

The distinction is not decorative. Two real constraints follow from it:

1. **Anything that requires the faculty guide (3.1.1-3.1.4) is calendar-locked.**
   These tasks cannot be compressed by adding effort, so they became fixed
   milestones that the increments in document 01 were planned around.
2. **The lab machine (3.1.5) is a different environment from the development
   machines (3.4).** This drove two concrete design decisions: SQLite instead of
   a server database (no service to install), and the rules-only fallback in the
   detection engine (so the system still runs if scikit-learn cannot be
   installed on a restricted lab account).

---

## 4. Role-Based WBS

Decomposes the work by **who performs it**. In a small student team one person
holds several roles; the roles are still separated because the responsibilities
and the review relationships differ.

```
4.0 CyberGuard AI (Role-Based)
|
+-- 4.1 Project Lead
|    +-- 4.1.1 Process model selection and increment planning
|    +-- 4.1.2 Risk register maintenance
|    +-- 4.1.3 Scope and safety boundary enforcement
|    +-- 4.1.4 Final consistency audit
|
+-- 4.2 Business / System Analyst
|    +-- 4.2.1 Requirements elicitation and specification
|    +-- 4.2.2 Use case and actor modelling
|    +-- 4.2.3 DFD and context modelling
|    +-- 4.2.4 State transition modelling
|    +-- 4.2.5 Traceability matrix upkeep
|
+-- 4.3 Software Architect
|    +-- 4.3.1 Layered architecture definition
|    +-- 4.3.2 Package, component, deployment models
|    +-- 4.3.3 Technology selection
|    +-- 4.3.4 Cross-cutting concerns (errors, logging, auth)
|
+-- 4.4 Database Designer
|    +-- 4.4.1 ER modelling
|    +-- 4.4.2 Schema and relationship implementation
|    +-- 4.4.3 Seed data design
|
+-- 4.5 ML / Detection Engineer
|    +-- 4.5.1 Feature engineering
|    +-- 4.5.2 Rule bank design and calibration
|    +-- 4.5.3 Statistical baseline
|    +-- 4.5.4 Model training pipeline
|    +-- 4.5.5 Fusion logic and explainability
|    +-- 4.5.6 Synthetic data generation
|
+-- 4.6 Backend Developer
|    +-- 4.6.1 Models and persistence
|    +-- 4.6.2 Service layer
|    +-- 4.6.3 REST endpoints
|    +-- 4.6.4 Validation and error handling
|    +-- 4.6.5 API documentation
|
+-- 4.7 Frontend Developer
|    +-- 4.7.1 Design system implementation
|    +-- 4.7.2 Application shell and routing
|    +-- 4.7.3 Page implementation
|    +-- 4.7.4 API integration and state handling
|    +-- 4.7.5 Loading / empty / error states
|
+-- 4.8 UI/UX Designer
|    +-- 4.8.1 Storyboarding
|    +-- 4.8.2 Visual language and colour semantics
|    +-- 4.8.3 Layout and responsive rules
|    +-- 4.8.4 Accessibility review
|
+-- 4.9 QA Engineer
|    +-- 4.9.1 Test case design
|    +-- 4.9.2 Automated test implementation
|    +-- 4.9.3 Functional test execution
|    +-- 4.9.4 Non-functional test procedures
|    +-- 4.9.5 Defect reporting and verification
|
+-- 4.10 Documentation Lead
     +-- 4.10.1 SE lab artefact authoring
     +-- 4.10.2 README and setup guide
     +-- 4.10.3 Project report compilation
     +-- 4.10.4 Syllabus traceability mapping
```

### 4.1 Estimation table (role-based)

| Role | Primary WBS items | Effort (hours) | % of total | Peak increment |
|------|-------------------|----------------|-----------|----------------|
| 4.1 Project Lead | 4.1.1-4.1.4 | 24 | 6% | I0, I8 |
| 4.2 Business / System Analyst | 4.2.1-4.2.5 | 42 | 10% | I0, I2 |
| 4.3 Software Architect | 4.3.1-4.3.4 | 26 | 6% | I0, I3 |
| 4.4 Database Designer | 4.4.1-4.4.3 | 32 | 8% | I1 |
| 4.5 ML / Detection Engineer | 4.5.1-4.5.6 | 58 | 14% | I2, I7 |
| 4.6 Backend Developer | 4.6.1-4.6.5 | 70 | 17% | I1, I3 |
| 4.7 Frontend Developer | 4.7.1-4.7.5 | 76 | 18% | I4, I5 |
| 4.8 UI/UX Designer | 4.8.1-4.8.4 | 26 | 6% | I4 |
| 4.9 QA Engineer | 4.9.1-4.9.5 | 46 | 11% | I7 |
| 4.10 Documentation Lead | 4.10.1-4.10.4 | 45 | 11% | continuous |
| | **TOTAL** | **445** | **100%** | |

### 4.2 Responsibility assignment (RACI) for key deliverables

**R** = Responsible, **A** = Accountable, **C** = Consulted, **I** = Informed

| Deliverable | Lead | Analyst | Architect | DB | ML | BE | FE | UX | QA | Docs |
|-------------|------|---------|-----------|----|----|----|----|----|----|------|
| Requirements spec | A | R | C | I | C | C | I | C | C | R |
| ER diagram / schema | I | C | C | **A/R** | I | R | I | I | I | C |
| Detection engine | I | C | C | I | **A/R** | C | I | I | C | C |
| REST API | I | C | **A** | C | C | **R** | C | I | C | R |
| Frontend pages | I | I | C | I | I | C | **A/R** | **R** | C | I |
| Test suite | A | C | I | I | C | C | C | I | **R** | I |
| Documentation set | **A** | R | C | C | C | C | C | C | C | **R** |
| Final audit | **A/R** | C | C | C | C | C | C | I | **R** | C |

---

## 5. Aggregate estimation

### 5.1 Effort summary across the four views

| WBS view | Total effort (hours) | What it counts |
|----------|---------------------|----------------|
| Process-based | 415 | Every phase activity including reviews and audits |
| Product-based | 266 | Construction of shippable components only |
| Geographic-based | 274 | Work attributed to a location (excludes untracked async overhead) |
| Role-based | 445 | Every activity attributed to a role, including coordination |

The four totals differ because each view slices the same project along a
different axis and each therefore absorbs a different share of coordination and
review overhead. The **role-based figure (445 h)** is the most complete, because
every hour anyone spends belongs to some role. This is used as the planning
baseline.

### 5.2 Schedule

| Increment | Calendar weeks | Planned effort (h) |
|-----------|----------------|--------------------|
| I0 Inception | Week 1 | 35 |
| I1 Data foundation | Week 2 | 40 |
| I2 Detection engine | Weeks 2-3 | 60 |
| I3 REST API | Weeks 3-4 | 60 |
| I4 Frontend shell | Week 4 | 40 |
| I5 SOC pages | Weeks 5-6 | 80 |
| I6 Analysis features | Week 6 | 50 |
| I7 Hardening | Week 7 | 50 |
| I8 Consolidation | Week 8 | 30 |
| **Total** | **8 weeks** | **445** |

### 5.3 Sanity check against a size-based estimate

A rough cross-check using a function-point-style count:

| Component | Count | Hours each (est.) | Subtotal |
|-----------|-------|-------------------|----------|
| Database entities | 10 | 3.0 | 30 |
| REST endpoints | 40 | 2.0 | 80 |
| Frontend pages | 12 | 6.0 | 72 |
| Reusable UI components | 20 | 1.5 | 30 |
| Detection engine modules | 7 | 8.0 | 56 |
| Service modules | 7 | 4.0 | 28 |
| Test cases | 117 | 0.25 | 29 |
| Documents | 22 | 2.0 | 44 |
| | | **Construction subtotal** | **369** |
| | | + 20% integration/rework | 74 |
| | | **Cross-check total** | **443** |

The size-based cross-check (443 h) agrees closely with the role-based rollup
(445 h), which increases confidence that the estimate is internally consistent.
Note that agreement between two estimates is **not** evidence that either
matches the real effort - only that the assumptions are consistent.

---

## 6. Estimation technique and assumptions

**Techniques used**

1. **Expert judgement** - per-task estimates from prior coursework experience.
2. **Estimation by analogy** - comparison with previous full-stack lab projects.
3. **Decomposition** - estimating leaf tasks rather than whole phases, which
   reduces the tendency to underestimate.
4. **Bottom-up rollup with a cross-check** - Section 5.3.

**Assumptions**

| # | Assumption |
|---|------------|
| A1 | A 4-member team, each contributing roughly 14 productive hours per week. |
| A2 | All members are already familiar with Python; React is learned during the project (a 15% learning-curve allowance is folded into frontend tasks). |
| A3 | No paid infrastructure; everything runs locally. |
| A4 | Requirements are stable at the feature level; refinement happens inside features. |
| A5 | The 20% rework allowance in Section 5.3 covers ordinary defect fixing but not a fundamental redesign. |

---

## 7. Estimates that were revised during the project

Honest reporting of where the plan and reality diverged in structure (not in
measured hours, which were not recorded):

| Task | Original plan | Revision | Reason |
|------|---------------|----------|--------|
| 1.4.2 / 4.5.2 Detection engine | Estimated as a single 3-day build | Extended to 4 days and re-visited in increment I7 | The first calibration produced a saturated severity distribution and had to be redesigned (see document 01, Section 5.1). |
| 1.5.x Test suite | Planned at ~60 test cases | Delivered 117 test cases | Validation rules and lifecycle transitions each needed negative-path coverage, which doubled the count. |
| 2.2.5 Frontend pages | 10 pages planned | 12 pages delivered | Incident Details and a 404 page were separated out during storyboarding. |
| 1.6.1 Documentation | Planned as a single end-of-project task | Distributed across every increment | Required by the Definition of Done; also prevented the diagrams from drifting out of step with the code. |

---

## 8. Traceability

| Lab requirement | Where satisfied |
|-----------------|-----------------|
| Process-based WBS | Section 1 |
| Product-based WBS | Section 2 |
| Geographic-based WBS | Section 3 |
| Role-based WBS | Section 4 |
| Task / duration / effort / dependency / role | Estimation table in every section |
| Realistic academic estimates | Sections 5 and 6 |
| Statement that these are planning estimates | Header note and Section 7 |
