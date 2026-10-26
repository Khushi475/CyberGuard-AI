# Database

This folder holds the SQLite database file for CyberGuard AI.

`cyberguard.db` is **generated**, not committed - it is listed in `.gitignore`.

## Creating it

```powershell
cd backend
venv\Scripts\activate
python seed_database.py
```

That creates all ten tables and populates a realistic demonstration dataset:
3 users, 12 monitored assets, 15 simulated threat indicators, and 320 synthetic
security events pushed through the real detection pipeline.

## Schema

Ten tables, described in detail in `documentation/04_ER_Diagram.md`:

| Table | Purpose |
|-------|---------|
| `users` | Analysts and administrators |
| `assets` | Monitored hosts and devices |
| `security_events` | Observed telemetry (the central fact table) |
| `detection_results` | The engine's verdict, one per event |
| `threats` | Classified malicious-looking findings |
| `alerts` | Analyst-facing notifications |
| `incidents` | Investigation cases with a lifecycle |
| `threat_indicators` | Simulated threat-intelligence records |
| `reports` | Generated security reports |
| `audit_logs` | Append-only trail of state-changing actions |

## Resetting

```powershell
python seed_database.py          # drops and recreates everything
python seed_database.py --keep   # adds to the existing data instead
```

## Inspecting it

```powershell
python -c "import sqlite3;c=sqlite3.connect('database/cyberguard.db');print([r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')])"
```

Or use any SQLite browser. Live row counts are also available from the running
application at `GET /api/system/status`.
