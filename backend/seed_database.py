"""Populate the CyberGuard AI database with a realistic demonstration dataset.

    python seed_database.py                 # ~320 events (default)
    python seed_database.py --events 500    # more history
    python seed_database.py --keep          # add to the existing data
    python seed_database.py --no-csv        # skip regenerating sample_data/*.csv

Everything created here is synthetic.  Running the script twice is safe: by
default it drops and recreates every table first.
"""
import argparse
import csv
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.ml.generate_dataset import CSV_COLUMNS, generate_events, to_csv_rows  # noqa: E402
from app.models import Asset, AuditLog, ThreatIndicator, User  # noqa: E402
from app.services import detection_service, incident_service  # noqa: E402

SAMPLE_DATA_DIR = BACKEND_DIR.parent / "sample_data"

DEMO_USERS = [
    {
        "full_name": "Priya Administrator",
        "email": os.getenv("DEMO_ADMIN_EMAIL", "admin@cyberguard.ai"),
        "password": os.getenv("DEMO_ADMIN_PASSWORD", "admin123"),
        "role": "ADMIN",
        "department": "Security Operations Centre",
    },
    {
        "full_name": "Arjun Analyst",
        "email": "analyst@cyberguard.ai",
        "password": "analyst123",
        "role": "ANALYST",
        "department": "Threat Detection",
    },
    {
        "full_name": "Meera Viewer",
        "email": "viewer@cyberguard.ai",
        "password": "viewer123",
        "role": "VIEWER",
        "department": "IT Governance",
    },
]

DEMO_ASSETS = [
    ("Primary Web Server", "10.0.3.10", "Web Server", "Ubuntu Server 22.04 LTS",
     "Data Centre A", "Platform Team", "CRITICAL"),
    ("Customer Database Server", "10.0.3.20", "Database Server", "Debian 12",
     "Data Centre A", "Data Team", "CRITICAL"),
    ("Billing Application Server", "10.0.3.30", "Application Server", "Red Hat Enterprise Linux 9",
     "Data Centre B", "Finance IT", "HIGH"),
    ("Perimeter Network Gateway", "10.0.1.1", "Network Gateway", "pfSense 2.7",
     "Data Centre A", "Network Team", "CRITICAL"),
    ("Employee Laptop - Finance", "10.0.1.42", "Laptop", "Windows 11 Pro",
     "Head Office", "Finance", "MEDIUM"),
    ("Employee Laptop - Engineering", "10.0.1.55", "Laptop", "macOS 14 Sonoma",
     "Head Office", "Engineering", "MEDIUM"),
    ("HR Workstation", "10.0.2.15", "Workstation", "Windows 11 Pro",
     "Head Office", "Human Resources", "MEDIUM"),
    ("Engineering Workstation", "10.0.2.31", "Workstation", "Ubuntu Desktop 24.04",
     "Head Office", "Engineering", "MEDIUM"),
    ("Corporate Mail Server", "10.0.3.40", "Mail Server", "Ubuntu Server 22.04 LTS",
     "Data Centre B", "IT Services", "HIGH"),
    ("Active Directory Controller", "10.0.1.20", "Domain Controller", "Windows Server 2022",
     "Data Centre A", "IT Services", "CRITICAL"),
    ("Branch Office Firewall", "192.168.10.1", "Firewall", "FortiOS 7.4",
     "Branch Office", "Network Team", "HIGH"),
    ("Warehouse Sensor Hub", "172.16.5.12", "IoT Device", "Embedded Linux",
     "Warehouse", "Facilities", "LOW"),
]

# Simulated indicators: RFC 5737 documentation IPs and reserved domain names only.
DEMO_INDICATORS = [
    ("203.0.113.66", "Suspicious IP", "Brute Force Attempt", "HIGH", 0.91,
     "Repeated failed SSH authentication bursts against the domain controller."),
    ("198.51.100.23", "Suspicious IP", "Port Scanning Pattern", "MEDIUM", 0.78,
     "Sequential connection attempts across a wide port range."),
    ("192.0.2.150", "Suspicious IP", "Denial-of-Service Pattern", "CRITICAL", 0.95,
     "Sustained high-rate HTTP requests aimed at the public web server."),
    ("203.0.113.201", "Suspicious IP", "Credential Abuse Pattern", "HIGH", 0.84,
     "Authenticated sessions originating outside expected working hours."),
    ("198.51.100.77", "Suspicious IP", "Network Anomaly", "LOW", 0.55,
     "Occasional long-lived connections with unusual packet sizing."),
    ("suspicious-update-server.invalid", "Suspicious Domain", "Data Transfer Anomaly",
     "HIGH", 0.88, "Simulated domain used in exfiltration training scenarios."),
    ("login-verify-portal.example", "Suspicious Domain", "Suspicious Login Activity",
     "MEDIUM", 0.72, "Look-alike sign-in portal used in phishing awareness exercises."),
    ("cdn-assets-mirror.invalid", "Suspicious Domain", "Network Anomaly", "LOW", 0.48,
     "Unclassified content mirror observed in simulated DNS traffic."),
    ("svc_backup_temp", "Suspicious User Activity", "Credential Abuse Pattern", "HIGH", 0.86,
     "Service account performing interactive logons it has never used before."),
    ("contractor_j.doe", "Suspicious User Activity", "Suspicious Login Activity", "MEDIUM", 0.69,
     "Sign-ins from two distant network segments within a short interval."),
    ("finance_shared_01", "Suspicious User Activity", "Data Transfer Anomaly", "MEDIUM", 0.66,
     "Bulk file reads from the finance share outside month-end."),
    ("Outbound TLS burst - 10.0.2.31", "Anomalous Network Activity", "Data Transfer Anomaly",
     "CRITICAL", 0.93, "Multi-gigabyte encrypted upload recorded during the night window."),
    ("ICMP sweep - branch segment", "Anomalous Network Activity", "Port Scanning Pattern",
     "MEDIUM", 0.74, "Broad ICMP echo activity across the branch office subnet."),
    ("DNS volume spike - 10.0.1.55", "Anomalous Network Activity", "Network Anomaly",
     "LOW", 0.52, "DNS query volume three times the weekly average for this host."),
    ("RDP session anomaly - 10.0.3.30", "Anomalous Network Activity", "Credential Abuse Pattern",
     "HIGH", 0.81, "Remote desktop sessions established from an unusual internal host."),
]


def reset_database() -> None:
    db.drop_all()
    db.create_all()
    print("  Database schema recreated (10 tables).")


def seed_users() -> list:
    users = []
    for spec in DEMO_USERS:
        user = User(
            full_name=spec["full_name"],
            email=spec["email"],
            role=spec["role"],
            department=spec["department"],
            is_active=True,
        )
        user.set_password(spec["password"])
        db.session.add(user)
        users.append(user)
    db.session.commit()
    print(f"  Created {len(users)} demo users.")
    return users


def seed_assets() -> list:
    assets = []
    for name, ip, kind, os_name, location, owner, criticality in DEMO_ASSETS:
        asset = Asset(
            name=name,
            ip_address=ip,
            asset_type=kind,
            operating_system=os_name,
            location=location,
            owner=owner,
            criticality=criticality,
            status="ONLINE",
            risk_level="LOW",
            risk_score=0,
            last_seen=datetime.utcnow() - timedelta(minutes=random.randint(1, 120)),
        )
        db.session.add(asset)
        assets.append(asset)
    db.session.commit()
    print(f"  Registered {len(assets)} monitored assets.")
    return assets


def seed_indicators() -> int:
    now = datetime.utcnow()
    for indicator, kind, category, risk, confidence, description in DEMO_INDICATORS:
        first_seen = now - timedelta(days=random.randint(5, 90))
        db.session.add(
            ThreatIndicator(
                indicator=indicator,
                indicator_type=kind,
                category=category,
                risk_level=risk,
                confidence=confidence,
                status=random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "MONITORING"]),
                description=description,
                hit_count=random.randint(1, 45),
                is_simulated=True,
                first_seen=first_seen,
                last_seen=now - timedelta(hours=random.randint(1, 72)),
            )
        )
    db.session.commit()
    print(f"  Loaded {len(DEMO_INDICATORS)} simulated threat indicators.")
    return len(DEMO_INDICATORS)


def seed_events(count: int, seed_value: int, user) -> dict:
    """Push generated events through the real detection pipeline."""
    events = generate_events(count=count, seed=seed_value, days_back=21)
    payloads = []
    for event in events:
        payload = {key: value for key, value in event.items()
                   if key not in ("profile", "expected_category", "label")}
        payloads.append(payload)

    summary = detection_service.analyze_batch(payloads, user=user, channel="seed")
    print(f"  Analysed {summary['total_records']} synthetic security events:")
    print(f"      normal     : {summary['normal_events']}")
    print(f"      suspicious : {summary['suspicious_events']}")
    print(f"      severity   : LOW={summary['low']} MEDIUM={summary['medium']} "
          f"HIGH={summary['high']} CRITICAL={summary['critical']}")
    print(f"      alerts     : {summary['alerts_created']}")
    print(f"      incidents  : {summary['incidents_created']}")
    return summary


def advance_incident_lifecycle(users) -> None:
    """Move a few incidents through the state machine so history is non-empty."""
    from app.models import Incident

    incidents = Incident.query.order_by(Incident.id.asc()).all()
    if not incidents:
        return

    analyst = next((u for u in users if u.role == "ANALYST"), users[0])
    admin = next((u for u in users if u.role == "ADMIN"), users[0])

    plan = [
        ("INVESTIGATING", "Triage started; correlating with asset owner's change calendar."),
        ("CONTAINED", "Source address blocked at the perimeter gateway."),
        ("RESOLVED", "Containment verified and monitoring returned to baseline."),
        ("FALSE_POSITIVE", "Confirmed as a scheduled vulnerability scan by the IT team."),
        ("INVESTIGATING", "Escalated to tier-2 for packet capture review."),
    ]

    for index, incident in enumerate(incidents[: len(plan) * 2]):
        target, note = plan[index % len(plan)]
        actor = analyst if index % 2 == 0 else admin
        try:
            if target in ("CONTAINED", "RESOLVED") and incident.status == "NEW":
                incident_service.transition(incident, "INVESTIGATING", "Initial triage.", actor)
            if target == "RESOLVED" and incident.status == "INVESTIGATING":
                incident_service.transition(
                    incident, "CONTAINED", "Temporary containment applied.", actor
                )
            incident_service.transition(
                incident, target, note, actor,
                resolution_summary=note if target in ("RESOLVED", "FALSE_POSITIVE") else None,
            )
        except Exception as exc:  # pragma: no cover - defensive during seeding
            print(f"      (skipped incident {incident.incident_code}: {exc})")

    print(f"  Advanced {min(len(incidents), len(plan) * 2)} incidents through the lifecycle.")


def triage_some_alerts(users) -> None:
    """Close a handful of alerts so detection precision becomes measurable."""
    from app.models import Alert
    from app.services import alert_service

    analyst = next((u for u in users if u.role == "ANALYST"), users[0])
    open_alerts = (
        Alert.query.filter(Alert.status == "NEW").order_by(Alert.id.asc()).limit(14).all()
    )
    resolved = false_positive = 0
    for index, alert in enumerate(open_alerts):
        try:
            if index % 5 == 4:
                alert_service.update_status(
                    alert, "FALSE_POSITIVE",
                    "Verified as authorised internal testing activity.", analyst,
                )
                false_positive += 1
            elif index % 3 == 0:
                alert_service.update_status(
                    alert, "RESOLVED", "Source blocked and activity confirmed stopped.", analyst
                )
                resolved += 1
            elif index % 3 == 1:
                alert_service.update_status(
                    alert, "INVESTIGATING", "Assigned for deeper packet review.", analyst
                )
        except Exception as exc:  # pragma: no cover
            print(f"      (skipped alert {alert.alert_code}: {exc})")
    print(f"  Triaged alerts: {resolved} resolved, {false_positive} marked false positive.")


def write_sample_csvs(seed_value: int) -> None:
    """Regenerate the CSV files used to demonstrate the Log Analyzer."""
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "sample_logs_mixed.csv": generate_events(count=120, seed=seed_value + 1, days_back=7),
        "sample_logs_normal.csv": [
            event for event in generate_events(count=400, seed=seed_value + 2, days_back=7)
            if event["profile"] == "normal"
        ][:80],
        "sample_logs_suspicious.csv": [
            event for event in generate_events(count=400, seed=seed_value + 3, days_back=7)
            if event["profile"] != "normal"
        ][:60],
    }

    for filename, events in files.items():
        rows = to_csv_rows(events)
        path = SAMPLE_DATA_DIR / filename
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Wrote {len(rows):>4} rows -> sample_data/{filename}")

    # A deliberately broken file so error handling can be demonstrated live.
    invalid_path = SAMPLE_DATA_DIR / "sample_logs_invalid.csv"
    with open(invalid_path, "w", newline="", encoding="utf-8") as handle:
        handle.write(",".join(CSV_COLUMNS) + "\n")
        handle.write("2026-02-01 10:00:00,10.0.1.42,10.0.3.10,51200,443,HTTPS,120000,150,0,10,30,web_request\n")
        handle.write("2026-02-01 10:05:00,NOT_AN_IP,10.0.3.10,51201,443,HTTPS,90000,120,0,8,25,web_request\n")
        handle.write("2026-02-01 10:10:00,10.0.1.43,10.0.3.10,51202,99999,HTTPS,80000,100,0,7,20,web_request\n")
        handle.write("2026-02-01 10:15:00,10.0.1.44,10.0.3.10,51203,443,TELEPATHY,70000,90,0,6,18,web_request\n")
        handle.write("2026-02-01 10:20:00,10.0.1.45,10.0.3.10,51204,443,HTTPS,abc,80,0,5,15,web_request\n")
    print("  Wrote    5 rows -> sample_data/sample_logs_invalid.csv (4 rows intentionally invalid)")


def seed(events: int = 320, seed_value: int = 42, reset: bool = True,
         write_csv: bool = True) -> dict:
    app = create_app()
    with app.app_context():
        print("\nSeeding the CyberGuard AI demonstration database")
        print("-" * 60)
        if reset:
            reset_database()
        else:
            db.create_all()

        users = User.query.all()
        if not users:
            users = seed_users()
        else:
            print(f"  Reusing {len(users)} existing users.")

        if Asset.query.count() == 0:
            seed_assets()
        else:
            print(f"  Reusing {Asset.query.count()} existing assets.")

        if ThreatIndicator.query.count() == 0:
            seed_indicators()

        admin = next((u for u in users if u.role == "ADMIN"), users[0])
        summary = seed_events(events, seed_value, admin)

        advance_incident_lifecycle(users)
        triage_some_alerts(users)

        db.session.add(
            AuditLog(
                action="DATABASE_SEEDED",
                entity_type="System",
                description=f"Database seeded with {events} synthetic security events.",
                user_id=admin.id,
                status="SUCCESS",
            )
        )
        db.session.commit()

        if write_csv:
            print("\nGenerating sample CSV log files")
            print("-" * 60)
            write_sample_csvs(seed_value)

        from app.models import Alert, Incident, SecurityEvent, Threat

        print("\nSeeding complete")
        print("-" * 60)
        print(f"  users            : {User.query.count()}")
        print(f"  assets           : {Asset.query.count()}")
        print(f"  security events  : {SecurityEvent.query.count()}")
        print(f"  threats          : {Threat.query.count()}")
        print(f"  alerts           : {Alert.query.count()}")
        print(f"  incidents        : {Incident.query.count()}")
        print(f"  indicators       : {ThreatIndicator.query.count()}")
        print(f"  audit log entries: {AuditLog.query.count()}")
        print(f"  database file    : {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("-" * 60)
        print("  Demo login       : admin@cyberguard.ai / admin123")
        print("  Analyst login    : analyst@cyberguard.ai / analyst123")
        print("  Viewer login     : viewer@cyberguard.ai / viewer123")
        print("-" * 60)
        print("  Next: python run.py      (then 'npm run dev' in ../frontend)\n")
        return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the CyberGuard AI database.")
    parser.add_argument("--events", type=int, default=320,
                        help="number of synthetic security events (default 320)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    parser.add_argument("--keep", action="store_true",
                        help="keep existing data instead of dropping the tables")
    parser.add_argument("--no-csv", action="store_true",
                        help="do not regenerate the sample_data CSV files")
    args = parser.parse_args()

    if args.events < 1 or args.events > 20000:
        raise SystemExit("--events must be between 1 and 20000")

    seed(events=args.events, seed_value=args.seed, reset=not args.keep,
         write_csv=not args.no_csv)


if __name__ == "__main__":
    main()
