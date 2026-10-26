"""TC-05: the detection engine itself, tested without the web layer."""
import pytest

from app.ml.detector import ThreatDetector, severity_for
from app.ml.features import FEATURE_NAMES, extract_features, features_to_vector
from app.ml.generate_dataset import generate_events
from app.ml.rules import evaluate_rules, recommended_action

NORMAL = {
    "source_ip": "10.0.1.42",
    "destination_ip": "10.0.3.10",
    "destination_port": 443,
    "protocol": "HTTPS",
    "event_type": "web_request",
    "request_count": 12,
    "failed_login_attempts": 0,
    "packet_count": 180,
    "bytes_transferred": 210000,
    "connection_duration": 45,
}

BRUTE_FORCE = {
    "source_ip": "203.0.113.66",
    "destination_ip": "10.0.1.20",
    "destination_port": 22,
    "protocol": "SSH",
    "event_type": "authentication",
    "request_count": 68,
    "failed_login_attempts": 62,
    "packet_count": 340,
    "bytes_transferred": 41000,
    "connection_duration": 95,
}

PORT_SCAN = {
    "source_ip": "198.51.100.23",
    "destination_ip": "10.0.2.15",
    "destination_port": 41234,
    "protocol": "TCP",
    "event_type": "firewall",
    "request_count": 420,
    "failed_login_attempts": 0,
    "packet_count": 480,
    "bytes_transferred": 29000,
    "connection_duration": 9,
}

EXFILTRATION = {
    "source_ip": "10.0.2.31",
    "destination_ip": "192.0.2.90",
    "destination_port": 443,
    "protocol": "HTTPS",
    "event_type": "file_access",
    "request_count": 6,
    "failed_login_attempts": 0,
    "packet_count": 900000,
    "bytes_transferred": 1288490188,
    "connection_duration": 5400,
    "timestamp": "2026-01-15T02:40:00",
}

DOS = {
    "source_ip": "192.0.2.150",
    "destination_ip": "10.0.3.10",
    "destination_port": 80,
    "protocol": "HTTP",
    "event_type": "web_request",
    "request_count": 48000,
    "failed_login_attempts": 0,
    "packet_count": 96000,
    "bytes_transferred": 8600000,
    "connection_duration": 42,
}


@pytest.fixture(scope="module")
def detector():
    """A detector with no model directory: exercises the rules-only fallback."""
    return ThreatDetector(model_dir=None)


def test_engine_works_without_any_trained_model(detector):
    info = detector.model_info()

    assert info["ml_available"] is False
    assert info["mode"] == "hybrid-rules"
    result = detector.detect(NORMAL)
    assert result["classification"] == "Normal Activity"


def test_normal_traffic_is_low_risk(detector):
    result = detector.detect(NORMAL)

    assert result["classification"] == "Normal Activity"
    assert result["is_threat"] is False
    assert result["severity"] == "LOW"
    assert result["risk_score"] < 26


def test_brute_force_is_classified_and_escalated(detector):
    result = detector.detect(BRUTE_FORCE)

    assert result["classification"] == "Brute Force Attempt"
    assert result["is_threat"] is True
    assert result["severity"] in ("HIGH", "CRITICAL")
    assert result["risk_score"] >= 51
    assert any("failed authentication" in reason.lower() for reason in result["reasons"])


def test_port_scan_is_classified(detector):
    result = detector.detect(PORT_SCAN)
    assert result["classification"] == "Port Scanning Pattern"
    assert result["is_threat"] is True


def test_data_exfiltration_is_classified(detector):
    result = detector.detect(EXFILTRATION)
    assert result["classification"] == "Data Transfer Anomaly"
    assert result["severity"] == "CRITICAL"


def test_denial_of_service_is_classified(detector):
    result = detector.detect(DOS)
    assert result["classification"] == "Denial-of-Service Pattern"
    assert result["is_threat"] is True


def test_every_detection_is_explainable(detector):
    for event in (NORMAL, BRUTE_FORCE, PORT_SCAN, EXFILTRATION, DOS):
        result = detector.detect(event)

        assert result["reasons"], "every verdict must state at least one reason"
        assert result["recommended_action"]
        assert 0 <= result["risk_score"] <= 100
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_risk_score_is_always_within_bounds(detector):
    extreme = dict(BRUTE_FORCE, failed_login_attempts=99999, request_count=9999999,
                   packet_count=99999999, bytes_transferred=1e11)
    result = detector.detect(extreme)

    assert 0 <= result["risk_score"] <= 100
    assert result["severity"] == "CRITICAL"


def test_severity_bands_match_the_specification():
    assert severity_for(0) == "LOW"
    assert severity_for(25) == "LOW"
    assert severity_for(26) == "MEDIUM"
    assert severity_for(50) == "MEDIUM"
    assert severity_for(51) == "HIGH"
    assert severity_for(75) == "HIGH"
    assert severity_for(76) == "CRITICAL"
    assert severity_for(100) == "CRITICAL"


def test_sensitivity_scales_the_risk_score(detector):
    mild = {**NORMAL, "failed_login_attempts": 6, "event_type": "authentication",
            "destination_port": 22}
    relaxed = detector.detect(mild, sensitivity=0.5)
    aggressive = detector.detect(mild, sensitivity=1.5)

    assert aggressive["risk_score"] > relaxed["risk_score"]


def test_risk_grows_with_attack_intensity(detector):
    scores = [
        detector.detect({**BRUTE_FORCE, "failed_login_attempts": attempts})["risk_score"]
        for attempts in (6, 20, 80, 200)
    ]
    assert scores == sorted(scores), f"risk should be monotonic with intensity, got {scores}"


def test_missing_optional_fields_are_handled(detector):
    result = detector.detect({"source_ip": "10.0.1.1"})

    assert result["classification"] == "Normal Activity"
    assert result["risk_score"] >= 0


def test_feature_extraction_is_stable_and_ordered():
    features = extract_features(BRUTE_FORCE)
    vector = features_to_vector(features)

    assert len(vector) == len(FEATURE_NAMES)
    assert all(isinstance(value, float) for value in vector)
    assert features["failed_login_attempts"] == 62
    assert features["is_auth_event"] == 1.0


def test_off_hours_flag_is_derived_from_the_timestamp():
    night = extract_features({**NORMAL, "timestamp": "2026-01-15T03:00:00"})
    day = extract_features({**NORMAL, "timestamp": "2026-01-15T14:00:00"})

    assert night["is_off_hours"] == 1.0
    assert day["is_off_hours"] == 0.0


def test_rule_bank_returns_a_recommended_action_for_every_category():
    outcome = evaluate_rules(extract_features(BRUTE_FORCE), BRUTE_FORCE)

    assert outcome["category"] == "Brute Force Attempt"
    assert recommended_action(outcome["category"])
    assert outcome["triggered"]


def test_generated_dataset_covers_every_severity_band(detector):
    """The synthetic generator must not collapse into a single severity."""
    events = generate_events(count=400, seed=11, days_back=14)
    severities = {detector.detect(event)["severity"] for event in events}

    assert {"LOW", "MEDIUM", "HIGH", "CRITICAL"}.issubset(severities)


def test_generated_normal_events_are_mostly_benign(detector):
    events = [e for e in generate_events(count=400, seed=3) if e["profile"] == "normal"]
    threats = sum(1 for event in events if detector.detect(event)["is_threat"])

    # A small false-positive rate is expected and realistic; a large one is a bug.
    assert threats / len(events) < 0.15


def test_detect_batch_matches_individual_detection(detector):
    events = [NORMAL, BRUTE_FORCE, PORT_SCAN]
    batch = detector.detect_batch(events)

    assert len(batch) == 3
    assert [item["classification"] for item in batch] == [
        detector.detect(event)["classification"] for event in events
    ]
