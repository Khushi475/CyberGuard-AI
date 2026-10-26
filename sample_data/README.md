# Sample data

CSV log files used to demonstrate the Log Analyzer (FR-10).

**All of this data is synthetic.** It is produced by
`backend/app/ml/generate_dataset.py` and regenerated every time you run
`python seed_database.py`. Internal hosts use RFC 1918 private ranges and
"external" hosts use the RFC 5737 documentation ranges (192.0.2.0/24,
198.51.100.0/24, 203.0.113.0/24), which are reserved for examples. Nothing here
refers to real infrastructure.

| File | Rows | Contents |
|------|------|----------|
| `sample_logs_mixed.csv` | 120 | A realistic mix of normal and suspicious traffic - **use this one for the main demonstration** |
| `sample_logs_normal.csv` | 80 | Benign baseline traffic only |
| `sample_logs_suspicious.csv` | 60 | Suspicious activity only |
| `sample_logs_invalid.csv` | 5 | 4 rows deliberately malformed, to demonstrate per-row validation |

## Columns

Only `source_ip` is mandatory. Everything else defaults to zero if absent.

```
timestamp, source_ip, destination_ip, source_port, destination_port,
protocol, bytes, packets, failed_logins, request_count, duration, event_type
```

These aliases are also accepted: `bytes` -> `bytes_transferred`,
`packets` -> `packet_count`, `failed_logins` -> `failed_login_attempts`,
`duration` -> `connection_duration`, `src_ip`/`dst_ip`, `src_port`/`dst_port`.

## Using them

Sign in, open **Log Analyzer**, and drop a file onto the upload area.

`sample_logs_invalid.csv` is the interesting one: it returns HTTP 201 with
1 row analysed and 4 rejected, each reported with its line number and the
specific reason. A malformed row never aborts the file.

## Regenerating

```powershell
cd backend
venv\Scripts\activate
python seed_database.py
```
