# 16 - Deployment Diagram

**Project:** CyberGuard AI
**Lab experiment:** 8 - OO design: Package, component and deployment models

---

## 1. Development / demonstration deployment (the configuration this project ships)

Everything runs on one Windows 11 machine. This is the configuration used for the
lab demonstration and the one the README sets up.

```
+==============================================================================+
|  <<device>>  Student Workstation  -  Windows 11, 8 GB RAM, Python 3.10+,     |
|                                      Node.js 18+                             |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |  <<execution environment>>  Web Browser  (Chrome / Edge / Firefox)      |  |
|  |                                                                        |  |
|  |     +--------------------------------------------------------------+   |  |
|  |     |  <<artifact>>  CyberGuard AI SPA                             |   |  |
|  |     |    index.html + bundled JS/CSS                               |   |  |
|  |     |    React 18 - Router - Recharts - Tailwind                   |   |  |
|  |     |    localStorage: session token, user profile                 |   |  |
|  |     +--------------------------------------------------------------+   |  |
|  +------------------------------------------------------------------------+  |
|                                  |                                           |
|                                  |  <<HTTP>>  http://localhost:5173          |
|                                  v                                           |
|  +------------------------------------------------------------------------+  |
|  |  <<execution environment>>  Node.js 18+  /  Vite Dev Server  (:5173)    |  |
|  |                                                                        |  |
|  |     +--------------------------------------------------------------+   |  |
|  |     |  <<artifact>>  Vite dev server                               |   |  |
|  |     |    - serves the SPA with hot module replacement               |   |  |
|  |     |    - PROXIES /api  ->  http://127.0.0.1:5000                  |   |  |
|  |     |      (so the browser sees a single origin and CORS is         |   |  |
|  |     |       never exercised during development)                     |   |  |
|  |     +--------------------------------------------------------------+   |  |
|  +------------------------------------------------------------------------+  |
|                                  |                                           |
|                                  |  <<HTTP / JSON>>  Bearer token            |
|                                  |  127.0.0.1:5000                           |
|                                  v                                           |
|  +------------------------------------------------------------------------+  |
|  |  <<execution environment>>  Python 3.10+ venv  /  Flask Dev Server      |  |
|  |                                            (:5000)                      |  |
|  |     +--------------------------------------------------------------+   |  |
|  |     |  <<artifact>>  run.py -> create_app()                        |   |  |
|  |     |                                                              |   |  |
|  |     |   +------------------+  +---------------------------------+  |   |  |
|  |     |   | Flask REST API   |  |  AI Detection Engine            |  |   |  |
|  |     |   | 11 blueprints    |  |  in-process, singleton per app  |  |   |  |
|  |     |   | ~40 routes       |  |  models cached after first load |  |   |  |
|  |     |   +------------------+  +---------------------------------+  |   |  |
|  |     |   +------------------+  +---------------------------------+  |   |  |
|  |     |   | Service layer    |  |  SQLAlchemy ORM + session       |  |   |  |
|  |     |   | 7 services       |  |                                 |  |   |  |
|  |     |   +------------------+  +---------------------------------+  |   |  |
|  |     +--------------------------------------------------------------+   |  |
|  |                        |                        |                      |  |
|  |                        | file I/O               | file I/O             |  |
|  |                        v                        v                      |  |
|  |     +----------------------------+   +-------------------------------+ |  |
|  |     | <<artifact>> ml_model/     |   | <<artifact>> logs/            | |  |
|  |     |   threat_classifier.joblib |   |   cyberguard.log              | |  |
|  |     |   isolation_forest.joblib  |   |   (rotating, 1 MB x 3)        | |  |
|  |     |   feature_scaler.joblib    |   +-------------------------------+ |  |
|  |     |   baseline.json            |                                     |  |
|  |     |   metadata.json            |                                     |  |
|  |     +----------------------------+                                     |  |
|  +------------------------------------------------------------------------+  |
|                                  |                                           |
|                                  |  <<DB-API / file I/O>>                    |
|                                  v                                           |
|  +------------------------------------------------------------------------+  |
|  |  <<database>>  SQLite  -  database/cyberguard.db                        |  |
|  |     10 tables, embedded, single file, no service to install             |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |  <<artifact>>  sample_data/                                             |  |
|  |     sample_logs_mixed.csv       (120 rows, realistic mix)               |  |
|  |     sample_logs_normal.csv      (80 rows, benign only)                  |  |
|  |     sample_logs_suspicious.csv  (60 rows, suspicious only)              |  |
|  |     sample_logs_invalid.csv     (5 rows, 4 deliberately malformed)      |  |
|  +------------------------------------------------------------------------+  |
+==============================================================================+
```

### 1.1 Why this topology

| Decision | Reason |
|----------|--------|
| SQLite rather than PostgreSQL/MySQL | No service to install, no credentials to configure, no port conflicts. The whole database is one file that can be deleted and re-seeded in a single command. This matters because the lab machine (WBS item 3.1.5) may not permit installing a database service. |
| Vite dev-server proxy rather than direct cross-origin calls | The browser only ever talks to `localhost:5173`, so no CORS preflight is involved during development. CORS is still configured on the backend for the case where the frontend is served separately. |
| Detection engine in-process, not a separate service | Avoids a second process to start and a network hop per event. For the prototype's volumes, an in-process call takes well under a millisecond. |
| Two terminals, not a container | A student on Windows 11 can run `python run.py` and `npm run dev` without installing Docker. |

---

## 2. Process and port allocation

| Process | Command | Port | Started from |
|---------|---------|------|--------------|
| Flask backend | `python run.py` | 5000 | `backend/` |
| Vite dev server | `npm run dev` | 5173 | `frontend/` |
| Vite preview (production build) | `npm run preview` | 4173 | `frontend/` |

Both ports are configurable: `HOST`/`PORT` in `backend/.env`, and `server.port`
in `frontend/vite.config.js`.

---

## 3. Deployment sequence

```
   1. cd backend
      python -m venv venv
      venv\Scripts\activate
      pip install -r requirements.txt
                 |
                 v
   2. python -m app.ml.train_model      [OPTIONAL]
      -> writes ml_model/*.joblib, baseline.json, metadata.json
      -> if skipped, the engine runs in hybrid-rules mode
                 |
                 v
   3. python seed_database.py
      -> creates database/cyberguard.db (10 tables)
      -> seeds 3 users, 12 assets, 15 indicators
      -> analyses 320 synthetic events through the real pipeline
      -> regenerates sample_data/*.csv
                 |
                 v
   4. python run.py                     [TERMINAL 1 - keep running]
      -> Flask on http://127.0.0.1:5000
                 |
                 v
   5. cd frontend
      npm install
      npm run dev                       [TERMINAL 2 - keep running]
      -> Vite on http://localhost:5173
                 |
                 v
   6. Open http://localhost:5173
      Sign in as admin@cyberguard.ai / admin123
```

---

## 4. Production build deployment (optional)

For a deployment where the frontend is served as static files rather than by the
Vite dev server.

```
+==============================================================================+
|  <<device>>  Host machine                                                    |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |  <<execution environment>>  Static file server (nginx / Vite preview)   |  |
|  |     <<artifact>>  frontend/dist/                                        |  |
|  |        index.html + hashed JS/CSS bundles                               |  |
|  |        (produced by `npm run build`)                                    |  |
|  +------------------------------------------------------------------------+  |
|                              |                                               |
|                              |  <<HTTPS / CORS>>                             |
|                              |  Origin must be listed in CORS_ORIGINS        |
|                              v                                               |
|  +------------------------------------------------------------------------+  |
|  |  <<execution environment>>  WSGI server (waitress / gunicorn)           |  |
|  |     <<artifact>>  create_app()                                          |  |
|  |     FLASK_ENV=production, DEBUG off, real SECRET_KEY                    |  |
|  +------------------------------------------------------------------------+  |
|                              |                                               |
|                              v                                               |
|  +------------------------------------------------------------------------+  |
|  |  <<database>>  SQLite file, or PostgreSQL via DATABASE_URL              |  |
|  +------------------------------------------------------------------------+  |
+==============================================================================+
```

In this mode the browser calls the backend across origins, so `FRONTEND_URL` must
be set in `backend/.env` (it is added to the CORS allow-list), or
`VITE_API_BASE_URL` must be set at build time to point the SPA at the API.

> **This project is an academic prototype.** The production topology is documented
> because the design supports it, not because the prototype is production-ready.
> Section 7 lists what would have to change first.

---

## 5. Node and artifact summary

| Node | Type | Software | Artifacts deployed |
|------|------|----------|--------------------|
| Student Workstation | Device | Windows 11 | everything below |
| Web Browser | Execution environment | Chrome / Edge / Firefox | SPA bundle, localStorage session |
| Vite Dev Server | Execution environment | Node.js 18+ | `frontend/src/`, dev middleware, `/api` proxy |
| Flask Dev Server | Execution environment | Python 3.10+ venv | `run.py`, `app/` package, blueprints, services, engine |
| ml_model store | Artifact directory | filesystem | 3 joblib files, baseline.json, metadata.json |
| logs | Artifact directory | filesystem | rotating `cyberguard.log` |
| SQLite | Database | embedded | `database/cyberguard.db` |
| sample_data | Artifact directory | filesystem | 4 CSV files |

---

## 6. Communication paths

| # | From | To | Protocol | Notes |
|---|------|----|----------|-------|
| 1 | Browser | Vite dev server | HTTP | Serves the SPA; HMR over a websocket |
| 2 | Vite dev server | Flask | HTTP (proxy) | `/api/*` forwarded to `127.0.0.1:5000` |
| 3 | Browser | Flask | HTTP + CORS | Only in the production-build topology |
| 4 | Flask | SQLite | DB-API / file I/O | Single-writer, WAL not enabled |
| 5 | Flask | ml_model/ | file I/O | Read once on first detection, then cached in memory |
| 6 | Flask | logs/ | file I/O | Rotating handler, 1 MB x 3 |

All communication in the shipped topology is loopback-only. **No component makes
an outbound connection to any external host**, which is the deployment-level
expression of the defensive-only scope rule.

---

## 7. Deployment constraints and what production would require

### 7.1 Current constraints

| Constraint | Consequence |
|------------|-------------|
| Flask development server | Single-threaded by default; suitable for one demonstrator, not for concurrent users. |
| SQLite single-writer | Concurrent writes serialise. Fine at the prototype's volumes; the first real ceiling if scaled. |
| In-process detection engine | Model memory is per worker; with multiple workers each loads its own copy. |
| Tokens are not revocable | A signed token remains valid until it expires; there is no server-side session store. |
| No HTTPS | Everything is plaintext over loopback. |
| No rate limiting | Nothing throttles repeated login attempts. |

### 7.2 What would have to change before any real deployment

1. Replace the development server with a WSGI server (waitress on Windows,
   gunicorn on Linux) behind a reverse proxy.
2. Terminate TLS at the proxy and set `Secure`/`HttpOnly` cookie handling, or move
   tokens out of `localStorage`.
3. Move to PostgreSQL (`DATABASE_URL` change only) for concurrent writes.
4. Add a server-side session or token-revocation store so sign-out is immediate.
5. Add rate limiting on `/api/auth/login` and on the upload endpoint.
6. Generate a strong `SECRET_KEY` per environment and keep it out of the
   repository (the `.env.example` already models this).
7. Add structured log shipping and a real monitoring probe against `/api/health`.

These are listed as known limitations in the README rather than presented as
completed work.
