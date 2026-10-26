"""Feature engineering for the CyberGuard AI detection engine.

A raw security event carries eleven observable fields.  ``extract_features``
turns them into the eighteen numeric features consumed by the rule bank, the
statistical baseline and (when available) the trained scikit-learn models.

Keeping this in one module guarantees that training and inference always see an
identical feature ordering - a classic source of bugs in ML systems.
"""
from datetime import datetime
from math import log1p

# Canonical ordering: the trained models depend on this list, so append only.
FEATURE_NAMES = [
    "failed_login_attempts",
    "request_count",
    "packet_count",
    "bytes_transferred",
    "connection_duration",
    "source_port",
    "destination_port",
    "bytes_per_packet",
    "packets_per_second",
    "requests_per_second",
    "bytes_per_request",
    "log_bytes",
    "log_requests",
    "hour_of_day",
    "is_off_hours",
    "is_wellknown_dest_port",
    "is_high_dest_port",
    "is_auth_event",
]

# Ports a normal enterprise workload is expected to talk to.
COMMON_SERVICE_PORTS = {20, 21, 22, 25, 53, 80, 110, 123, 143, 389, 443, 445,
                        587, 993, 995, 1433, 3306, 3389, 5432, 8080, 8443}

# Ports that are legitimate but frequently abused - used by the rule bank.
SENSITIVE_PORTS = {22, 23, 445, 1433, 3306, 3389, 5432, 5900}

AUTH_EVENT_TYPES = {"authentication", "vpn_session", "database_query"}


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        number = float(value)
        return default if number != number else number
    except (TypeError, ValueError):
        return default


def _hour_of(timestamp) -> int:
    if isinstance(timestamp, datetime):
        return timestamp.hour
    if isinstance(timestamp, str) and timestamp:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
        except ValueError:
            return datetime.utcnow().hour
    return datetime.utcnow().hour


def extract_features(event: dict) -> dict:
    """Build the full feature dictionary for a single event."""
    failed_logins = _to_float(event.get("failed_login_attempts"))
    request_count = _to_float(event.get("request_count"))
    packet_count = _to_float(event.get("packet_count"))
    bytes_transferred = _to_float(event.get("bytes_transferred"))
    duration = _to_float(event.get("connection_duration"))
    source_port = _to_float(event.get("source_port"))
    dest_port = _to_float(event.get("destination_port"))

    safe_duration = max(duration, 1.0)
    safe_packets = max(packet_count, 1.0)
    safe_requests = max(request_count, 1.0)

    hour = _hour_of(event.get("timestamp"))
    event_type = str(event.get("event_type") or "network_traffic").lower()

    return {
        "failed_login_attempts": failed_logins,
        "request_count": request_count,
        "packet_count": packet_count,
        "bytes_transferred": bytes_transferred,
        "connection_duration": duration,
        "source_port": source_port,
        "destination_port": dest_port,
        "bytes_per_packet": bytes_transferred / safe_packets,
        "packets_per_second": packet_count / safe_duration,
        "requests_per_second": request_count / safe_duration,
        "bytes_per_request": bytes_transferred / safe_requests,
        "log_bytes": log1p(max(bytes_transferred, 0.0)),
        "log_requests": log1p(max(request_count, 0.0)),
        "hour_of_day": float(hour),
        "is_off_hours": 1.0 if (hour < 6 or hour >= 22) else 0.0,
        "is_wellknown_dest_port": 1.0 if int(dest_port) in COMMON_SERVICE_PORTS else 0.0,
        "is_high_dest_port": 1.0 if dest_port >= 1024 else 0.0,
        "is_auth_event": 1.0 if event_type in AUTH_EVENT_TYPES else 0.0,
    }


def features_to_vector(features: dict) -> list:
    """Flatten a feature dict into the fixed-order vector the models expect."""
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]


def describe_features(features: dict) -> dict:
    """Human-readable feature summary shown on the Threat Detection page."""
    return {
        "Failed logins": int(features.get("failed_login_attempts", 0)),
        "Requests": int(features.get("request_count", 0)),
        "Packets": int(features.get("packet_count", 0)),
        "Bytes transferred": int(features.get("bytes_transferred", 0)),
        "Duration (s)": round(features.get("connection_duration", 0.0), 2),
        "Requests/sec": round(features.get("requests_per_second", 0.0), 2),
        "Bytes/packet": round(features.get("bytes_per_packet", 0.0), 2),
        "Hour of day": int(features.get("hour_of_day", 0)),
        "Off hours": bool(features.get("is_off_hours", 0.0)),
    }
