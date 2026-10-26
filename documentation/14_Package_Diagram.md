# 14 - Package Diagram

**Project:** CyberGuard AI
**Lab experiment:** 8 - OO design: Package, component and deployment models

---

## 1. Package diagram

```
+=============================================================================+
|                          CyberGuard-AI  (system)                            |
+=============================================================================+
                    |                                |
                    v                                v
+===================================+    +===================================+
|          <<subsystem>>            |    |          <<subsystem>>            |
|            frontend               |    |            backend                |
+===================================+    +===================================+
                                                        |
    +-------------------+                               |
    |   frontend.pages  |                               v
    |-------------------|              +=========================================+
    | Login             |              |            backend.app                  |
    | Dashboard         |              +=========================================+
    | ThreatDetection   |                  |        |        |       |       |
    | Alerts            |                  v        v        v       v       v
    | Incidents         |        +----------+ +----------+ +-------+ +-----+ +-------+
    | IncidentDetails   |        | .routes  | |.services | | .ml   | |.mod-| |.utils |
    | ThreatIntelligence|        |          | |          | |       | | els | |       |
    | LogAnalyzer       |        +----------+ +----------+ +-------+ +-----+ +-------+
    | Assets            |             |            |          |        |        |
    | Reports           |             |            |          |        |        |
    | Settings          |             |            |          |        |        |
    | NotFound          |             |            |          |        |        |
    +-------------------+             |            |          |        |        |
         |      |    |                |            |          |        |        |
         |      |    | <<import>>     |            |          |        |        |
         v      |    v                |            |          |        |        |
  +-----------+ | +--------------+    |            |          |        |        |
  |.components| | |  .layouts    |    |            |          |        |        |
  |-----------| | |--------------|    |            |          |        |        |
  | ui.jsx    | | | DashboardLay-|    |            |          |        |        |
  | charts/   | | | out.jsx      |    |            |          |        |        |
  +-----------+ | +--------------+    |            |          |        |        |
         |      |        |            |            |          |        |        |
         |      v        |            |            |          |        |        |
         | +-----------+ |            |            |          |        |        |
         | | .context  | |            |            |          |        |        |
         | |-----------| |            |            |          |        |        |
         | | Auth      | |            |            |          |        |        |
         | | Toast     | |            |            |          |        |        |
         | +-----------+ |            |            |          |        |        |
         |      |        |            |            |          |        |        |
         v      v        v            |            |          |        |        |
       +-------------------+          |            |          |        |        |
       |    .services      |          |            |          |        |        |
       |-------------------|          |            |          |        |        |
       |     api.js        |          |            |          |        |        |
       +-------------------+          |            |          |        |        |
                |                     |            |          |        |        |
                |  HTTP / JSON        |            |          |        |        |
                +-------------------->+            |          |        |        |
                                                   |          |        |        |
       +-------------------+                       |          |        |        |
       |     .hooks        |                       |          |        |        |
       |-------------------|                       |          |        |        |
       | useApi            |                       |          |        |        |
       | useDebounced      |                       |          |        |        |
       | usePersistentState|                       |          |        |        |
       +-------------------+                       |          |        |        |
                                                   |          |        |        |
       +-------------------+                       |          |        |        |
       |     .utils        |                       |          |        |        |
       |-------------------|                       |          |        |        |
       | format.js         |                       |          |        |        |
       +-------------------+                       |          |        |        |
                                                   |          |        |        |
                                                   v          v        v        v
                                          (see the backend detail below)
```

---

## 2. Backend package detail and dependency direction

```
                     +----------------------------------+
                     |         backend.app              |
                     |     (application factory)        |
                     +----------------------------------+
                              |          |
             registers        |          |  initialises
                              v          v
                   +------------------+  +-----------------------+
                   |  app.routes      |  |   app.extensions      |
                   |------------------|  |-----------------------|
                   | auth.py          |  | db  (SQLAlchemy)      |
                   | dashboard.py     |  | cors (Flask-CORS)     |
                   | events.py        |  +-----------------------+
                   | threats.py       |            ^
                   | alerts.py        |            |
                   | incidents.py     |            |
                   | assets.py        |            |
                   | reports.py       |            |
                   | system.py        |            |
                   +------------------+            |
                       |          |                |
           <<import>>  |          | <<import>>     |
                       v          v                |
      +---------------------+  +--------------------+
      |   app.services      |  |    app.utils       |
      |---------------------|  |--------------------|
      | auth_service        |  | validators.py      |
      | detection_service   |  | security.py        |
      | alert_service       |  | errors.py          |
      | incident_service    |  | responses.py       |
      | analytics_service   |  | csv_parser.py      |
      | report_service      |  | logger.py          |
      | audit_service       |  +--------------------+
      +---------------------+            |
           |            |                |
           | <<import>> | <<import>>     |
           v            v                |
   +-------------+  +--------------+     |
   |  app.ml     |  |  app.models  |<----+
   |-------------|  |--------------|
   | detector.py |  | user.py      |
   | features.py |  | asset.py     |
   | rules.py    |  | security_    |
   | anomaly.py  |  |   event.py   |
   | generate_   |  | detection_   |
   |  dataset.py |  |   result.py  |
   | train_      |  | threat.py    |
   |  model.py   |  | alert.py     |
   | predict.py  |  | incident.py  |
   +-------------+  | threat_      |
         |          |  indicator.py|
         |          | report.py    |
         | uses     | audit_log.py |
         v          | base.py      |
   +-------------+  +--------------+
   | scikit-learn|         |
   | numpy       |         | uses
   | joblib      |         v
   | (optional)  |  +--------------+
   +-------------+  | app.extensions|
                    |    (db)      |
                    +--------------+
```

### 2.1 The dependency rule

```
   routes  --->  services  --->  models  --->  extensions
      |             |
      |             +--->  ml
      |
      +--->  utils  (used by every layer)
```

**Dependencies point strictly inward and never back out.**

| Package | May import | Must never import |
|---------|-----------|-------------------|
| `app.routes` | services, utils, models (for read queries) | nothing imports routes |
| `app.services` | models, ml, utils, extensions | routes |
| `app.ml` | **nothing from the application** - only the standard library, NumPy and (optionally) scikit-learn | models, services, routes, Flask, the database |
| `app.models` | extensions, utils | services, routes, ml |
| `app.utils` | models (only inside a function body, to avoid a cycle) | services, routes |

### 2.2 Why `app.ml` is fully isolated

The detection engine imports nothing from Flask, from SQLAlchemy or from the rest
of the application. This is deliberate and has three concrete benefits:

1. **It is testable in isolation.** `tests/test_detection_engine.py` builds a
   `ThreatDetector` directly and runs 18 test cases with no application context,
   no database and no HTTP layer.
2. **It is reusable.** `app/ml/predict.py` runs the same engine from the command
   line, and `app/ml/train_model.py` trains against the same feature code.
3. **It can be replaced.** Swapping the engine for a different implementation
   requires only that `detect()` keeps its contract; nothing else changes.

The one place the boundary is crossed is `security.py`, which imports `User`
inside the function body rather than at module level. This is documented in the
code with the reason: a module-level import would create a cycle
(`models` -> `utils` -> `models`).

---

## 3. Frontend package detail

```
                      +--------------------+
                      |       main.jsx     |
                      +--------------------+
                                |
                                v
                      +--------------------+
                      |       App.jsx      |
                      |  routes + guards   |
                      +--------------------+
                          |            |
             +------------+            +-------------+
             v                                       v
   +-------------------+                   +--------------------+
   |    .context       |                   |     .layouts       |
   |-------------------|                   |--------------------|
   | AuthContext       |<------------------| DashboardLayout    |
   | ToastContext      |<---+              +--------------------+
   +-------------------+    |                        |
             |              |                        | renders <Outlet/>
             |              |                        v
             |              |              +--------------------+
             |              +--------------|      .pages        |
             |                             |--------------------|
             |                             | 12 page components |
             |                             +--------------------+
             |                                  |          |
             |                      <<import>>  |          | <<import>>
             |                                  v          v
             |                        +-------------+  +------------------+
             |                        | .components |  |     .hooks       |
             |                        |-------------|  |------------------|
             |                        | ui.jsx      |  | useApi           |
             |                        | charts/     |  | useDebounced     |
             |                        |  Charts.jsx |  | usePersistent... |
             |                        +-------------+  +------------------+
             |                                  |              |
             |                                  | <<import>>   |
             |                                  v              v
             |                        +-------------------------------+
             +----------------------->|         .services             |
                                      |-------------------------------|
                                      |          api.js               |
                                      | (the ONLY module that knows   |
                                      |  the backend exists)          |
                                      +-------------------------------+
                                                   |
                                      +-------------------------------+
                                      |          .utils               |
                                      |-------------------------------|
                                      | format.js  (severity colours, |
                                      | date/byte formatting, badges) |
                                      +-------------------------------+
```

### 3.1 Frontend layering rules

| Package | Responsibility | Rule |
|---------|----------------|------|
| `.services` | The single HTTP boundary | **No other module may call `axios` or `fetch`.** Every network call goes through `api.js`. |
| `.context` | Cross-cutting state (session, toasts) | Provides; never consumes pages. |
| `.hooks` | Reusable data-fetching and timing behaviour | May use `.services`; never renders. |
| `.components` | Presentation primitives | Pure presentation; no direct API calls. |
| `.pages` | Screen composition and page-level state | Composes components, calls hooks and services. |
| `.layouts` | Navigation shell | Renders `<Outlet/>`; owns the sidebar and top bar. |
| `.utils` | Pure functions | No React, no network. |

**Why the single API module matters.** The base URL, the auth header, the error
translation and the 401 handling exist in exactly one file. When the backend
returns a new error shape, one file changes. This is the frontend counterpart of
the backend's service layer, and the concrete basis for the maintainability claim
in NFR-05.

---

## 4. External package dependencies

### 4.1 Backend

| Package | Version | Used by | Required at runtime? |
|---------|---------|---------|----------------------|
| Flask | 3.0.3 | `app`, `app.routes` | Yes |
| Flask-Cors | 4.0.1 | `app.extensions` | Yes |
| Flask-SQLAlchemy | 3.1.1 | `app.extensions`, `app.models` | Yes |
| SQLAlchemy | 2.0.31 | `app.models`, `app.services` | Yes |
| Werkzeug | 3.0.3 | `app.models.user` (PBKDF2 hashing) | Yes |
| itsdangerous | 2.2.0 | `app.utils.security` (token signing) | Yes |
| python-dotenv | 1.0.1 | `app.config` | Yes |
| NumPy | 1.26.4 | `app.ml.anomaly` (baseline fitting) | Only for training |
| pandas | 2.2.2 | data preparation | Only for training |
| scikit-learn | 1.5.1 | `app.ml.train_model`, `app.ml.detector` | **No - optional** |
| joblib | 1.4.2 | `app.ml.detector` (model loading) | **No - optional** |
| reportlab | 4.2.2 | `app.services.report_service` | **No - optional** |
| pytest | 8.3.2 | `tests` | Development only |

### 4.2 Frontend

| Package | Version | Used by |
|---------|---------|---------|
| react / react-dom | 18.3.1 | everything |
| react-router-dom | 6.26.2 | `App.jsx`, `.layouts`, `.pages` |
| axios | 1.7.7 | `.services/api.js` only |
| recharts | 2.12.7 | `.components/charts` only |
| lucide-react | 0.446.0 | icons across `.pages`, `.components` |
| tailwindcss | 3.4.13 | build-time styling |
| vite | 5.4.8 | build-time tooling |

### 4.3 Optional dependency isolation

The three optional backend packages are each isolated behind a guard:

| Package | Guard | Behaviour when absent |
|---------|-------|-----------------------|
| scikit-learn / joblib | `try/except` inside `ThreatDetector._load_models()` | The engine reports `hybrid-rules` mode and continues with rules plus statistics. |
| reportlab | `try/except ImportError` in `routes/reports.py` | HTTP 501 with a message naming the install command; CSV and JSON exports still work. |

This is what makes the claim "the application must still work even if the ML
model has not been trained" structurally true rather than aspirational, and it is
verified by `test_engine_works_without_any_trained_model`.

---

## 5. Package metrics

| Package | Modules | Primary responsibility | Stability |
|---------|---------|------------------------|-----------|
| `app.routes` | 10 | HTTP contract | Unstable (depends on much, depended on by nothing) |
| `app.services` | 8 | Business rules | Balanced |
| `app.ml` | 8 | Detection algorithm | **Stable** (depends on nothing internal) |
| `app.models` | 12 | Persistence | Stable |
| `app.utils` | 7 | Cross-cutting helpers | Stable |
| `frontend.pages` | 12 | Screens | Unstable |
| `frontend.components` | 2 | Presentation primitives | Stable |
| `frontend.services` | 1 | HTTP boundary | Stable |

Following the Stable Dependencies Principle, the volatile packages (`routes`,
`pages`) depend on the stable ones (`ml`, `models`, `components`, `services`) and
never the reverse. A change to a route cannot break the detection engine.
