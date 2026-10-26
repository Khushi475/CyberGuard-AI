"""Input validation helpers.

The prototype validates every request payload before it reaches the detection
engine or the database.  This satisfies NFR-02 (Security) and prevents malformed
CSV rows from corrupting analytics.
"""
import ipaddress
import re
from datetime import datetime

from .errors import ValidationError

VALID_PROTOCOLS = {"TCP", "UDP", "ICMP", "HTTP", "HTTPS", "SSH", "FTP", "DNS", "SMTP", "RDP"}

VALID_EVENT_TYPES = {
    "authentication",
    "network_traffic",
    "file_access",
    "process_execution",
    "dns_query",
    "web_request",
    "firewall",
    "vpn_session",
    "database_query",
    "email_gateway",
}

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ALERT_STATUSES = ["NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"]
INCIDENT_STATUSES = ["NEW", "OPEN", "INVESTIGATING", "CONTAINED", "RESOLVED", "FALSE_POSITIVE"]
ASSET_STATUSES = ["ONLINE", "OFFLINE", "MAINTENANCE", "QUARANTINED"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def require_dict(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")
    return payload


def validate_email(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        raise ValidationError("Email is required.", details={"field": "email"})
    if not EMAIL_RE.match(value):
        raise ValidationError("Email address format is invalid.", details={"field": "email"})
    return value


def validate_password(value: str, field: str = "password") -> str:
    if not value or not isinstance(value, str):
        raise ValidationError("Password is required.", details={"field": field})
    if len(value) < 6:
        raise ValidationError(
            "Password must be at least 6 characters long.", details={"field": field}
        )
    return value


def validate_ip(value, field: str = "ip_address", required: bool = True):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return None
    text = str(value).strip()
    try:
        ipaddress.ip_address(text)
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be a valid IPv4/IPv6 address (received '{text}').",
            details={"field": field},
        ) from exc
    return text


def validate_port(value, field: str = "port", required: bool = False):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return None
    try:
        port = int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be an integer.", details={"field": field}) from exc
    if not 0 <= port <= 65535:
        raise ValidationError(f"{field} must be between 0 and 65535.", details={"field": field})
    return port


def validate_number(value, field: str, minimum=0, maximum=None, default=0, required: bool = False):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be numeric.", details={"field": field}) from exc
    if number != number:  # NaN guard
        raise ValidationError(f"{field} must be numeric.", details={"field": field})
    if minimum is not None and number < minimum:
        raise ValidationError(
            f"{field} must be greater than or equal to {minimum}.", details={"field": field}
        )
    if maximum is not None and number > maximum:
        raise ValidationError(
            f"{field} must be less than or equal to {maximum}.", details={"field": field}
        )
    return number


def validate_choice(value, options, field: str, required: bool = True, default=None):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return default
    text = str(value).strip()
    upper_options = {str(option).upper(): option for option in options}
    if text.upper() in upper_options:
        return upper_options[text.upper()]
    raise ValidationError(
        f"{field} must be one of: {', '.join(str(o) for o in options)}.",
        details={"field": field, "allowed": list(options)},
    )


def validate_protocol(value, required: bool = False, default: str = "TCP") -> str:
    if value in (None, ""):
        if required:
            raise ValidationError("protocol is required.", details={"field": "protocol"})
        return default
    return validate_choice(value, sorted(VALID_PROTOCOLS), "protocol")


def validate_event_type(value, required: bool = False, default: str = "network_traffic") -> str:
    if value in (None, ""):
        if required:
            raise ValidationError("event_type is required.", details={"field": "event_type"})
        return default
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if text not in VALID_EVENT_TYPES:
        raise ValidationError(
            f"event_type must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}.",
            details={"field": "event_type", "allowed": sorted(VALID_EVENT_TYPES)},
        )
    return text


def validate_timestamp(value, field: str = "timestamp", required: bool = False):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    for pattern in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:26] if "." in text else text, pattern)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).replace(tzinfo=None)
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be an ISO-8601 date/time value.", details={"field": field}
        ) from exc


def validate_string(value, field: str, max_length: int = 255, required: bool = True, default=None):
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.", details={"field": field})
        return default
    text = str(value).strip()
    if not text and required:
        raise ValidationError(f"{field} cannot be empty.", details={"field": field})
    if len(text) > max_length:
        text = text[:max_length]
    return text


def validate_event_payload(payload: dict, partial: bool = False) -> dict:
    """Validate and normalise a single security-event payload.

    Used by POST /api/events, POST /api/events/analyze and by every row of an
    uploaded CSV file so that all three paths share identical rules.
    """
    payload = require_dict(payload)
    cleaned = {
        "source_ip": validate_ip(payload.get("source_ip"), "source_ip", required=not partial),
        "destination_ip": validate_ip(
            payload.get("destination_ip"), "destination_ip", required=False
        ),
        "source_port": validate_port(payload.get("source_port"), "source_port"),
        "destination_port": validate_port(payload.get("destination_port"), "destination_port"),
        "protocol": validate_protocol(payload.get("protocol")),
        "event_type": validate_event_type(payload.get("event_type")),
        "request_count": int(
            validate_number(payload.get("request_count"), "request_count", 0, 10000000)
        ),
        "failed_login_attempts": int(
            validate_number(payload.get("failed_login_attempts"), "failed_login_attempts", 0, 100000)
        ),
        "packet_count": int(
            validate_number(payload.get("packet_count"), "packet_count", 0, 100000000)
        ),
        "bytes_transferred": float(
            validate_number(payload.get("bytes_transferred"), "bytes_transferred", 0, 1e12)
        ),
        "connection_duration": float(
            validate_number(payload.get("connection_duration"), "connection_duration", 0, 1e6)
        ),
        "timestamp": validate_timestamp(payload.get("timestamp")),
        "user_agent": validate_string(
            payload.get("user_agent"), "user_agent", 255, required=False
        ),
        "raw_log": validate_string(payload.get("raw_log"), "raw_log", 4000, required=False),
    }
    if payload.get("asset_id") not in (None, ""):
        cleaned["asset_id"] = int(validate_number(payload.get("asset_id"), "asset_id", 1))
    return cleaned


def parse_pagination(args, default_per_page: int = 20, max_per_page: int = 200):
    try:
        page = max(1, int(args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = max(1, min(per_page, max_per_page))
    return page, per_page
