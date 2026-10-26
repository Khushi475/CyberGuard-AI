"""Shared pytest fixtures.

Each test module gets a brand-new application backed by an in-memory SQLite
database, seeded with a small deterministic dataset.  Nothing here touches the
demonstration database in ``database/cyberguard.db``.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import Asset, ThreatIndicator, User  # noqa: E402
from app.services import detection_service  # noqa: E402

ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "admin123"
ANALYST_EMAIL = "analyst@test.local"
ANALYST_PASSWORD = "analyst123"


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.drop_all()
        _db.create_all()
        _seed(application)
        yield application
        _db.session.remove()
        _db.drop_all()


def _seed(application):
    admin = User(full_name="Test Administrator", email=ADMIN_EMAIL, role="ADMIN",
                 department="SOC", is_active=True)
    admin.set_password(ADMIN_PASSWORD)

    analyst = User(full_name="Test Analyst", email=ANALYST_EMAIL, role="ANALYST",
                   department="Detection", is_active=True)
    analyst.set_password(ANALYST_PASSWORD)

    disabled = User(full_name="Disabled User", email="disabled@test.local", role="VIEWER",
                    is_active=False)
    disabled.set_password("disabled123")

    _db.session.add_all([admin, analyst, disabled])

    _db.session.add_all(
        [
            Asset(name="Test Web Server", ip_address="10.0.3.10", asset_type="Web Server",
                  operating_system="Ubuntu 22.04", status="ONLINE", criticality="CRITICAL"),
            Asset(name="Test Domain Controller", ip_address="10.0.1.20",
                  asset_type="Domain Controller", operating_system="Windows Server 2022",
                  status="ONLINE", criticality="CRITICAL"),
        ]
    )

    now = datetime.utcnow()
    _db.session.add(
        ThreatIndicator(
            indicator="203.0.113.66",
            indicator_type="Suspicious IP",
            category="Brute Force Attempt",
            risk_level="HIGH",
            confidence=0.9,
            status="ACTIVE",
            description="Simulated indicator used by the test-suite.",
            first_seen=now - timedelta(days=5),
            last_seen=now,
        )
    )
    _db.session.commit()

    # A few analysed events so list/aggregate endpoints have data to return.
    with application.test_request_context():
        for payload in (
            {"source_ip": "10.0.1.42", "destination_ip": "10.0.3.10", "destination_port": 443,
             "protocol": "HTTPS", "event_type": "web_request", "request_count": 10,
             "packet_count": 150, "bytes_transferred": 180000, "connection_duration": 40},
            {"source_ip": "203.0.113.66", "destination_ip": "10.0.1.20", "destination_port": 22,
             "protocol": "SSH", "event_type": "authentication", "failed_login_attempts": 55,
             "request_count": 60, "packet_count": 320, "bytes_transferred": 40000,
             "connection_duration": 90},
            {"source_ip": "198.51.100.23", "destination_ip": "10.0.3.10",
             "destination_port": 41234, "protocol": "TCP", "event_type": "firewall",
             "request_count": 380, "packet_count": 420, "bytes_transferred": 26000,
             "connection_duration": 8},
        ):
            detection_service.persist_analysis(payload, user=admin, channel="seed")


@pytest.fixture()
def client(app):
    return app.test_client()


def _token(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]["token"]


@pytest.fixture()
def auth_headers(client):
    """Authorization header for the administrator account."""
    return {"Authorization": f"Bearer {_token(client, ADMIN_EMAIL, ADMIN_PASSWORD)}"}


@pytest.fixture()
def analyst_headers(client):
    return {"Authorization": f"Bearer {_token(client, ANALYST_EMAIL, ANALYST_PASSWORD)}"}


@pytest.fixture()
def sample_csv():
    """A small in-memory CSV used by the upload tests."""
    return (
        "timestamp,source_ip,destination_ip,source_port,destination_port,protocol,"
        "bytes,packets,failed_logins,request_count,duration,event_type\n"
        "2026-02-01 10:00:00,10.0.1.42,10.0.3.10,51200,443,HTTPS,180000,150,0,10,40,web_request\n"
        "2026-02-01 02:15:00,203.0.113.66,10.0.1.20,44122,22,SSH,41000,320,64,68,92,authentication\n"
        "2026-02-01 11:30:00,198.51.100.23,10.0.3.10,60211,41234,TCP,26000,420,0,380,8,firewall\n"
        "2026-02-01 12:00:00,10.0.1.55,10.0.3.20,51322,3306,TCP,95000,210,0,18,55,database_query\n"
    )


@pytest.fixture()
def invalid_csv():
    return (
        "timestamp,source_ip,destination_ip,destination_port,protocol,bytes,packets,"
        "failed_logins,request_count,duration,event_type\n"
        "2026-02-01 10:00:00,10.0.1.42,10.0.3.10,443,HTTPS,180000,150,0,10,40,web_request\n"
        "2026-02-01 10:05:00,NOT_AN_IP,10.0.3.10,443,HTTPS,90000,120,0,8,25,web_request\n"
        "2026-02-01 10:10:00,10.0.1.43,10.0.3.10,99999,HTTPS,80000,100,0,7,20,web_request\n"
    )
