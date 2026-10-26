"""Synthetic security-event generator.

Everything CyberGuard AI learns from and demonstrates with is generated here.  No
real capture, no real infrastructure: internal hosts use RFC 1918 space and
"external" hosts use the RFC 5737 documentation ranges (192.0.2.0/24,
198.51.100.0/24, 203.0.113.0/24) which are reserved for examples.

The same generator feeds three consumers, which keeps them consistent:

* ``train_model.py``      - builds the training matrix.
* ``seed_database.py``    - populates the demo database.
* ``sample_data/*.csv``   - the files used to demonstrate the Log Analyzer.
"""
import random
from datetime import datetime, timedelta

INTERNAL_PREFIXES = ("10.0.1.", "10.0.2.", "10.0.3.", "192.168.10.", "172.16.5.")
EXTERNAL_PREFIXES = ("192.0.2.", "198.51.100.", "203.0.113.")

SERVICE_PORTS = [22, 25, 53, 80, 110, 143, 389, 443, 445, 587, 1433, 3306, 3389, 5432, 8080, 8443]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGuardDemo/1.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) CyberGuardDemo/1.0",
    "curl/8.4.0",
    "python-requests/2.31.0",
    "CyberGuard-Sensor/1.2",
    "OpenSSH_9.3",
]

# profile -> share of the generated population
PROFILE_WEIGHTS = {
    "normal": 0.56,
    "brute_force": 0.08,
    "port_scan": 0.08,
    "dos": 0.05,
    "data_exfiltration": 0.05,
    "suspicious_login": 0.12,
    "credential_abuse": 0.03,
    "network_anomaly": 0.03,
}

PROFILE_CATEGORY = {
    "normal": "Normal Activity",
    "brute_force": "Brute Force Attempt",
    "port_scan": "Port Scanning Pattern",
    "dos": "Denial-of-Service Pattern",
    "data_exfiltration": "Data Transfer Anomaly",
    "suspicious_login": "Suspicious Login Activity",
    "credential_abuse": "Credential Abuse Pattern",
    "network_anomaly": "Network Anomaly",
}


# --- attack intensity -------------------------------------------------------
# Real security telemetry is dominated by *mild* suspicious activity with only a
# small tail of extreme campaigns.  Generating every attack at full strength would
# push every detection into the CRITICAL band and make the dashboard meaningless,
# so each attack profile is scaled by an intensity factor t in [0, 1].
INTENSITY_TIERS = (
    ("low", 0.00, 0.30, 0.42),
    ("medium", 0.30, 0.62, 0.34),
    ("high", 0.62, 1.00, 0.24),
)


def _intensity(rng: random.Random) -> float:
    names = [tier[0] for tier in INTENSITY_TIERS]
    weights = [tier[3] for tier in INTENSITY_TIERS]
    chosen = rng.choices(names, weights=weights, k=1)[0]
    low, high = next((tier[1], tier[2]) for tier in INTENSITY_TIERS if tier[0] == chosen)
    return rng.uniform(low, high)


def _lerp(low: float, high: float, t: float, curve: float = 1.0) -> float:
    """Interpolate between ``low`` and ``high``; ``curve`` > 1 biases towards ``low``."""
    return low + (high - low) * (max(0.0, min(1.0, t)) ** curve)


def _internal_ip(rng: random.Random) -> str:
    return rng.choice(INTERNAL_PREFIXES) + str(rng.randint(2, 254))


def _external_ip(rng: random.Random) -> str:
    return rng.choice(EXTERNAL_PREFIXES) + str(rng.randint(2, 254))


def _business_hour(rng: random.Random) -> int:
    return rng.choices(
        population=list(range(24)),
        weights=[1, 1, 1, 1, 1, 2, 4, 8, 14, 18, 20, 20, 16, 18, 20, 20, 16, 12, 8, 5, 3, 2, 1, 1],
        k=1,
    )[0]


def _timestamp(rng: random.Random, days_back: int, off_hours: bool = False) -> datetime:
    now = datetime.utcnow()
    day_offset = rng.randint(0, max(days_back - 1, 0))
    hour = rng.choice([0, 1, 2, 3, 4, 23]) if off_hours else _business_hour(rng)
    return (now - timedelta(days=day_offset)).replace(
        hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59), microsecond=0
    )


def _normal(rng: random.Random, days_back: int) -> dict:
    duration = round(rng.uniform(0.4, 220.0), 2)
    requests = rng.randint(1, 45)
    packets = rng.randint(6, 520)
    return {
        "source_ip": _internal_ip(rng),
        "destination_ip": rng.choice([_internal_ip(rng), _external_ip(rng)]),
        "source_port": rng.randint(20000, 65000),
        "destination_port": rng.choice([80, 443, 443, 443, 53, 3306, 5432, 8080]),
        "protocol": rng.choice(["TCP", "HTTPS", "HTTP", "TCP", "DNS", "UDP"]),
        "event_type": rng.choice(
            ["network_traffic", "web_request", "dns_query", "file_access", "database_query"]
        ),
        "request_count": requests,
        "failed_login_attempts": 0 if rng.random() > 0.08 else 1,
        "packet_count": packets,
        "bytes_transferred": round(packets * rng.uniform(300, 1500), 2),
        "connection_duration": duration,
        "timestamp": _timestamp(rng, days_back),
        "user_agent": rng.choice(USER_AGENTS),
    }


def _brute_force(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    attempts = int(_lerp(5, 150, t, curve=2.0))
    duration = round(_lerp(20, 260, t), 2)
    return {
        "source_ip": _external_ip(rng),
        "destination_ip": _internal_ip(rng),
        "source_port": rng.randint(30000, 65000),
        "destination_port": rng.choice([22, 3389, 445, 1433, 3306]),
        "protocol": rng.choice(["SSH", "TCP", "RDP"]),
        "event_type": "authentication",
        "request_count": attempts + rng.randint(0, 10),
        "failed_login_attempts": attempts,
        "packet_count": attempts * rng.randint(3, 8),
        "bytes_transferred": round(attempts * rng.uniform(180, 700), 2),
        "connection_duration": duration,
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.3 + 0.4 * t),
        "user_agent": "OpenSSH_9.3",
    }


def _port_scan(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    probes = int(_lerp(28, 900, t, curve=2.0))
    duration = round(_lerp(42, 3, t), 2)
    packets = int(probes * rng.uniform(1.0, 1.8))
    return {
        "source_ip": _external_ip(rng),
        "destination_ip": _internal_ip(rng),
        "source_port": rng.randint(40000, 65000),
        "destination_port": rng.choice([rng.randint(1024, 65000), rng.choice(SERVICE_PORTS)]),
        "protocol": rng.choice(["TCP", "UDP"]),
        "event_type": rng.choice(["network_traffic", "firewall"]),
        "request_count": probes,
        "failed_login_attempts": 0,
        "packet_count": packets,
        "bytes_transferred": round(packets * rng.uniform(40, 110), 2),
        "connection_duration": duration,
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.2 + 0.3 * t),
        "user_agent": None,
    }


def _dos(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    requests = int(_lerp(420, 90000, t, curve=2.4))
    duration = round(_lerp(110, 8, t), 2)
    packets = int(requests * rng.uniform(1.0, 2.6))
    return {
        "source_ip": _external_ip(rng),
        "destination_ip": _internal_ip(rng),
        "source_port": rng.randint(1024, 65000),
        "destination_port": rng.choice([80, 443, 53, 8080]),
        "protocol": rng.choice(["HTTP", "HTTPS", "UDP", "TCP"]),
        "event_type": rng.choice(["web_request", "network_traffic"]),
        "request_count": requests,
        "failed_login_attempts": 0,
        "packet_count": packets,
        "bytes_transferred": round(packets * rng.uniform(60, 150), 2),
        "connection_duration": duration,
        "timestamp": _timestamp(rng, days_back),
        "user_agent": rng.choice(["curl/8.4.0", "python-requests/2.31.0", None]),
    }


def _data_exfiltration(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    megabytes = _lerp(48, 6000, t, curve=2.4)
    total_bytes = megabytes * 1024 * 1024
    packets = int(total_bytes / rng.uniform(1300, 1500))
    duration = round(_lerp(180, 7200, t), 2)
    return {
        "source_ip": _internal_ip(rng),
        "destination_ip": _external_ip(rng),
        "source_port": rng.randint(20000, 65000),
        "destination_port": rng.choice([443, 22, 21, 8443, 9001]),
        "protocol": rng.choice(["HTTPS", "SSH", "FTP", "TCP"]),
        "event_type": rng.choice(["network_traffic", "file_access"]),
        "request_count": rng.randint(1, 30),
        "failed_login_attempts": 0,
        "packet_count": packets,
        "bytes_transferred": round(total_bytes, 2),
        "connection_duration": duration,
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.35 + 0.45 * t),
        "user_agent": rng.choice(["curl/8.4.0", None, "python-requests/2.31.0"]),
    }


def _suspicious_login(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    attempts = max(1, int(_lerp(1, 4, t)))
    return {
        "source_ip": rng.choice([_external_ip(rng), _internal_ip(rng)]),
        "destination_ip": _internal_ip(rng),
        "source_port": rng.randint(20000, 65000),
        "destination_port": rng.choice([22, 443, 3389, 389]),
        "protocol": rng.choice(["HTTPS", "SSH", "RDP"]),
        "event_type": rng.choice(["authentication", "vpn_session"]),
        "request_count": rng.randint(1, 20),
        "failed_login_attempts": attempts,
        "packet_count": rng.randint(10, 160),
        "bytes_transferred": round(rng.uniform(2000, 90000), 2),
        "connection_duration": round(rng.uniform(1, 90), 2),
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.18 + 0.45 * t),
        "user_agent": rng.choice(USER_AGENTS),
    }


def _credential_abuse(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    return {
        "source_ip": _internal_ip(rng),
        "destination_ip": _internal_ip(rng),
        "source_port": rng.randint(20000, 65000),
        "destination_port": rng.choice([3389, 1433, 3306, 5432, 22]),
        "protocol": rng.choice(["RDP", "TCP", "SSH"]),
        "event_type": rng.choice(["authentication", "database_query"]),
        "request_count": int(_lerp(32, 600, t, curve=2.0)),
        "failed_login_attempts": int(_lerp(3, 9, t)),
        "packet_count": int(_lerp(200, 4000, t, curve=1.8)),
        "bytes_transferred": round(_lerp(150000, 9000000, t, curve=2.0), 2),
        "connection_duration": round(_lerp(60, 2400, t), 2),
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.4 + 0.45 * t),
        "user_agent": rng.choice(USER_AGENTS),
    }


def _network_anomaly(rng: random.Random, days_back: int) -> dict:
    t = _intensity(rng)
    packets = rng.randint(50, 900)
    return {
        "source_ip": _internal_ip(rng),
        "destination_ip": _external_ip(rng),
        "source_port": rng.choice([53, 123, 443, 80]),
        "destination_port": rng.randint(20000, 65000),
        "protocol": rng.choice(["UDP", "TCP", "ICMP"]),
        "event_type": rng.choice(["network_traffic", "dns_query", "firewall"]),
        "request_count": rng.randint(5, 60),
        "failed_login_attempts": 0,
        "packet_count": packets,
        "bytes_transferred": round(packets * _lerp(3600, 9000, t), 2),
        "connection_duration": round(_lerp(3700, 40000, t, curve=1.8), 2),
        "timestamp": _timestamp(rng, days_back, off_hours=rng.random() < 0.3 + 0.35 * t),
        "user_agent": None,
    }


PROFILE_BUILDERS = {
    "normal": _normal,
    "brute_force": _brute_force,
    "port_scan": _port_scan,
    "dos": _dos,
    "data_exfiltration": _data_exfiltration,
    "suspicious_login": _suspicious_login,
    "credential_abuse": _credential_abuse,
    "network_anomaly": _network_anomaly,
}


def generate_event(profile: str, rng: random.Random, days_back: int = 30) -> dict:
    builder = PROFILE_BUILDERS.get(profile, _normal)
    event = builder(rng, days_back)
    event["profile"] = profile
    event["expected_category"] = PROFILE_CATEGORY[profile]
    event["label"] = 0 if profile == "normal" else 1
    return event


def generate_events(count: int = 300, seed: int | None = 42, days_back: int = 30) -> list:
    """Generate ``count`` events following the configured profile mix."""
    rng = random.Random(seed)
    profiles = list(PROFILE_WEIGHTS.keys())
    weights = list(PROFILE_WEIGHTS.values())
    chosen = rng.choices(profiles, weights=weights, k=count)
    events = [generate_event(profile, rng, days_back) for profile in chosen]
    events.sort(key=lambda item: item["timestamp"])
    return events


def to_csv_rows(events) -> list:
    """Convert generated events into Log-Analyzer compatible CSV rows."""
    rows = []
    for event in events:
        rows.append(
            {
                "timestamp": event["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "source_ip": event["source_ip"],
                "destination_ip": event["destination_ip"],
                "source_port": event["source_port"],
                "destination_port": event["destination_port"],
                "protocol": event["protocol"],
                "bytes": int(event["bytes_transferred"]),
                "packets": int(event["packet_count"]),
                "failed_logins": int(event["failed_login_attempts"]),
                "request_count": int(event["request_count"]),
                "duration": event["connection_duration"],
                "event_type": event["event_type"],
            }
        )
    return rows


CSV_COLUMNS = [
    "timestamp",
    "source_ip",
    "destination_ip",
    "source_port",
    "destination_port",
    "protocol",
    "bytes",
    "packets",
    "failed_logins",
    "request_count",
    "duration",
    "event_type",
]
