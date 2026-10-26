"""Explainable rule bank - the deterministic half of the hybrid detector.

Every rule is a small pure function that receives the engineered features plus
the original event and returns ``(score, reasons)`` where ``score`` is a 0-100
contribution and ``reasons`` is a list of plain-English explanations.

Scoring design
--------------
The magnitude terms grow **logarithmically** rather than linearly.  A linear
score would mean that any brute-force attempt above roughly twenty tries is
indistinguishable from one with a thousand, and the whole alert queue would
collapse into a single CRITICAL band.  A logarithmic curve keeps the ordering
intact across several orders of magnitude while still separating a mild probe
from a sustained campaign.  Each rule then adds bounded, additive bonuses for
corroborating context (off-hours, sensitive port, tiny payloads, ...).

All classifications are *behavioural* descriptions of supplied telemetry.  The
engine never executes, probes or attacks anything - it only reads numbers that
were handed to it.
"""
from math import log10

from .features import SENSITIVE_PORTS

# Category -> recommended defensive response shown to the analyst.
RECOMMENDED_ACTIONS = {
    "Normal Activity": (
        "No action required. Continue passive monitoring of this source."
    ),
    "Brute Force Attempt": (
        "Temporarily rate-limit or lock the targeted account, enforce MFA, and review "
        "authentication logs for the source address."
    ),
    "Port Scanning Pattern": (
        "Review firewall rules for the destination segment, confirm exposed services are "
        "intentional, and add the source to a monitoring watch-list."
    ),
    "Suspicious Login Activity": (
        "Verify the sign-in with the account owner, require a password reset, and check "
        "for follow-up successful logins from the same address."
    ),
    "Network Anomaly": (
        "Correlate with the asset owner's expected baseline and capture a longer traffic "
        "sample before escalating."
    ),
    "Data Transfer Anomaly": (
        "Confirm whether a sanctioned backup or migration explains the volume; if not, "
        "restrict egress for the asset and preserve logs for review."
    ),
    "Denial-of-Service Pattern": (
        "Enable rate limiting at the gateway, scale or shed load on the target service, "
        "and notify the network operations team."
    ),
    "Credential Abuse Pattern": (
        "Suspend the affected session, force re-authentication, and audit recent privileged "
        "operations performed by the account."
    ),
}

MITRE_TACTICS = {
    "Brute Force Attempt": "Credential Access (TA0006)",
    "Port Scanning Pattern": "Discovery (TA0007)",
    "Suspicious Login Activity": "Initial Access (TA0001)",
    "Data Transfer Anomaly": "Exfiltration (TA0010)",
    "Denial-of-Service Pattern": "Impact (TA0040)",
    "Credential Abuse Pattern": "Privilege Escalation (TA0004)",
    "Network Anomaly": "Discovery (TA0007)",
    "Normal Activity": None,
}

def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _magnitude(value: float, pivot: float, base: float, slope: float) -> float:
    """Logarithmic magnitude term: ``base`` at ``value == pivot``, +``slope`` per decade."""
    if value <= 0 or pivot <= 0:
        return base
    return base + slope * log10(max(value / pivot, 0.1))


def rule_brute_force(f: dict, event: dict):
    """Many failed authentications from one source in a single observation window."""
    failed = f["failed_login_attempts"]
    if failed < 5:
        return 0.0, []

    score = _magnitude(failed, pivot=4.0, base=38.0, slope=30.0)
    reasons = [f"{int(failed)} failed authentication attempts recorded for this source."]

    if f["is_auth_event"]:
        score += 8
        reasons.append("The event originates from an authentication service.")
    if f["requests_per_second"] > 5:
        score += 6
        reasons.append(
            f"Authentication attempts arrived rapidly "
            f"({f['requests_per_second']:.1f} requests/second)."
        )
    if int(f["destination_port"]) in SENSITIVE_PORTS:
        score += 5
        reasons.append(
            f"The targeted port {int(f['destination_port'])} hosts a remote-access or "
            "database service."
        )
    return _clamp(score), reasons


def rule_suspicious_login(f: dict, event: dict):
    """A smaller burst of failures, or failures at an unusual hour."""
    failed = f["failed_login_attempts"]
    if failed == 0 or failed >= 5:
        return 0.0, []

    score = 15 + failed * 7
    reasons = [f"{int(failed)} failed login attempt(s) detected from this source."]

    if f["is_off_hours"]:
        score += 16
        reasons.append(
            f"The attempts occurred outside business hours (around {int(f['hour_of_day'])}:00)."
        )
    if f["is_auth_event"]:
        score += 7
        reasons.append("Authentication subsystem reported the anomaly.")
    if int(f["destination_port"]) in SENSITIVE_PORTS:
        score += 6
        reasons.append(
            f"The attempts targeted port {int(f['destination_port'])}, a remote-access service."
        )
    return _clamp(score), reasons


def rule_port_scanning(f: dict, event: dict):
    """Many tiny, short-lived connections - the signature of a sweep."""
    if f["request_count"] < 25 or f["bytes_per_packet"] > 220:
        return 0.0, []

    score = 0.0
    reasons = []

    if f["connection_duration"] <= 45:
        score += _magnitude(f["request_count"], pivot=20.0, base=18.0, slope=26.0)
        reasons.append(
            f"{int(f['request_count'])} connection attempts compressed into "
            f"{f['connection_duration']:.1f} seconds."
        )
    if f["bytes_per_packet"] < 120:
        score += 18
        reasons.append(
            f"Payloads are unusually small ({f['bytes_per_packet']:.0f} bytes per packet), "
            "which is typical of probe traffic rather than data exchange."
        )
    if f["packet_count"] <= max(f["request_count"] * 2, 4):
        score += 12
        reasons.append("Each connection carried only a handful of packets.")
    if f["is_high_dest_port"] and not f["is_wellknown_dest_port"]:
        score += 8
        reasons.append(
            f"Traffic targeted the uncommon high port {int(f['destination_port'])}."
        )

    if not reasons:
        return 0.0, []
    return _clamp(score), reasons


def rule_dos_pattern(f: dict, event: dict):
    """Volumetric flooding against a single destination."""
    if f["request_count"] < 400 and f["packets_per_second"] < 400:
        return 0.0, []

    score = 0.0
    reasons = []
    rps = f["requests_per_second"]

    if f["request_count"] >= 400:
        score += _magnitude(f["request_count"], pivot=300.0, base=20.0, slope=30.0)
        reasons.append(f"{int(f['request_count'])} requests observed in one window.")
    if rps >= 20:
        score += min(20.0, 8.0 + 6.0 * log10(max(rps / 20.0, 1.0) + 1.0) * 3.0)
        reasons.append(f"Sustained request rate of {rps:.0f} per second.")
    if f["packets_per_second"] >= 400:
        score += 14
        reasons.append(f"Packet rate reached {f['packets_per_second']:.0f} packets/second.")
    if f["bytes_per_request"] < 200 and f["request_count"] >= 400:
        score += 8
        reasons.append("Requests carry almost no payload, consistent with flood traffic.")

    if not reasons:
        return 0.0, []
    return _clamp(score), reasons


def rule_data_transfer_anomaly(f: dict, event: dict):
    """Large or oddly shaped outbound transfers."""
    megabytes = f["bytes_transferred"] / (1024 * 1024)
    if megabytes < 45:
        return 0.0, []

    score = _magnitude(megabytes, pivot=40.0, base=18.0, slope=30.0)
    reasons = [f"{megabytes:.1f} MB transferred in a single session."]

    if f["is_off_hours"]:
        score += 16
        reasons.append(
            f"The transfer took place outside business hours (around {int(f['hour_of_day'])}:00)."
        )
    if f["connection_duration"] > 600:
        score += 8
        reasons.append(
            f"The connection stayed open for {f['connection_duration'] / 60:.0f} minutes."
        )
    if f["bytes_per_packet"] > 1400:
        score += 6
        reasons.append("Packets are consistently at maximum size, indicating bulk transfer.")
    return _clamp(score), reasons


def rule_credential_abuse(f: dict, event: dict):
    """Authenticated session behaving unlike a normal user session."""
    if not f["is_auth_event"]:
        return 0.0, []

    score = 0.0
    reasons = []

    if f["failed_login_attempts"] >= 3 and f["request_count"] >= 30:
        score += min(45.0, _magnitude(f["request_count"], pivot=25.0, base=22.0, slope=18.0))
        reasons.append(
            "Repeated authentication failures were followed by a high volume of "
            "session activity."
        )
    if f["is_off_hours"] and f["request_count"] >= 20:
        score += 22
        reasons.append("Heavy account activity recorded outside normal working hours.")
    if int(f["destination_port"]) in SENSITIVE_PORTS and f["failed_login_attempts"] >= 2:
        score += 16
        reasons.append(
            f"Failures target port {int(f['destination_port'])}, a privileged administrative "
            "service."
        )

    if not reasons:
        return 0.0, []
    return _clamp(score), reasons


def rule_network_anomaly(f: dict, event: dict):
    """Catch-all for traffic shapes that do not match any specific pattern."""
    score = 0.0
    reasons = []

    if f["connection_duration"] > 3600:
        score += min(26.0, 12.0 + 14.0 * log10(f["connection_duration"] / 3600.0 + 1.0))
        reasons.append(
            f"Connection held open for {f['connection_duration'] / 3600:.1f} hours."
        )
    if f["bytes_per_packet"] > 4000:
        score += 20
        reasons.append(
            f"Average packet size of {f['bytes_per_packet']:.0f} bytes exceeds the expected MTU."
        )
    if f["is_off_hours"] and f["bytes_transferred"] > 5 * 1024 * 1024:
        score += 18
        reasons.append("Sizeable transfer recorded during off-hours.")
    if f["source_port"] and f["source_port"] < 1024 and f["is_high_dest_port"]:
        score += 12
        reasons.append(
            f"Traffic originates from privileged port {int(f['source_port'])} towards a "
            "high ephemeral port."
        )

    if not reasons:
        return 0.0, []
    return _clamp(score), reasons


# Ordered by specificity: the first highest-scoring rule wins the classification.
RULE_BANK = (
    ("Brute Force Attempt", rule_brute_force),
    ("Denial-of-Service Pattern", rule_dos_pattern),
    ("Data Transfer Anomaly", rule_data_transfer_anomaly),
    ("Port Scanning Pattern", rule_port_scanning),
    ("Credential Abuse Pattern", rule_credential_abuse),
    ("Suspicious Login Activity", rule_suspicious_login),
    ("Network Anomaly", rule_network_anomaly),
)


def evaluate_rules(features: dict, event: dict) -> dict:
    """Run every rule and return the winning category plus all triggered reasons."""
    triggered = []
    for category, rule in RULE_BANK:
        score, reasons = rule(features, event)
        if score > 0 and reasons:
            triggered.append({"category": category, "score": round(score, 2), "reasons": reasons})

    if not triggered:
        return {
            "category": "Normal Activity",
            "score": 0.0,
            "reasons": ["No rule in the detection bank matched this event's behaviour."],
            "triggered": [],
        }

    triggered.sort(key=lambda item: item["score"], reverse=True)
    winner = triggered[0]

    reasons = list(winner["reasons"])
    for other in triggered[1:]:
        reasons.append(
            f"Secondary indicator - {other['category']}: {other['reasons'][0]}"
        )

    return {
        "category": winner["category"],
        "score": winner["score"],
        "reasons": reasons[:6],
        "triggered": triggered,
    }


def recommended_action(category: str) -> str:
    return RECOMMENDED_ACTIONS.get(category, RECOMMENDED_ACTIONS["Network Anomaly"])


def mitre_tactic(category: str):
    return MITRE_TACTICS.get(category)
