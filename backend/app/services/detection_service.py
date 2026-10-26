"""Detection orchestration - the bridge between the ML engine and the database.

Pipeline implemented here (mirrors DFD Level 1, process 2.0 "Analyse Event"):

    validated event -> persist SecurityEvent
                    -> ThreatDetector.detect()
                    -> persist DetectionResult
                    -> if suspicious: persist Threat + Alert
                    -> if critical:   open an Incident and link the Alert
                    -> update the owning Asset's risk posture
"""
from datetime import datetime

from flask import current_app
from sqlalchemy import func

from ..extensions import db
from ..ml.detector import ThreatDetector, severity_for
from ..models import Alert, Asset, DetectionResult, Incident, SecurityEvent, Threat
from ..utils.logger import get_logger
from .audit_service import record as audit

logger = get_logger("cyberguard.detection")

SEVERITY_TO_PRIORITY = {"LOW": "P4", "MEDIUM": "P3", "HIGH": "P2", "CRITICAL": "P1"}

_ENGINE_KEY = "cyberguard_detector"


def get_engine() -> ThreatDetector:
    """Return the detector attached to the current Flask application."""
    engine = current_app.extensions.get(_ENGINE_KEY)
    if engine is None:
        engine = ThreatDetector(
            model_dir=current_app.config["ML_MODEL_DIR"],
            sensitivity=current_app.config.get("DETECTION_SENSITIVITY", 1.0),
        )
        current_app.extensions[_ENGINE_KEY] = engine
    return engine


def analyze_only(payload: dict, sensitivity: float | None = None) -> dict:
    """Run the engine without touching the database (used for dry-run previews)."""
    return get_engine().detect(payload, sensitivity=sensitivity)


def next_code(prefix: str, model, column) -> str:
    """Generate a human-friendly sequential code such as ``ALT-000042``."""
    highest = db.session.query(func.max(model.id)).scalar() or 0
    return f"{prefix}-{highest + 1:06d}"


def resolve_asset(source_ip: str, destination_ip: str | None) -> Asset | None:
    """Attach an event to a monitored asset by matching either endpoint IP."""
    candidates = [ip for ip in (destination_ip, source_ip) if ip]
    if not candidates:
        return None
    return Asset.query.filter(Asset.ip_address.in_(candidates)).first()


def _update_asset_risk(asset: Asset | None, risk_score: int, seen_at: datetime) -> None:
    if asset is None:
        return
    asset.last_seen = max(asset.last_seen or seen_at, seen_at)
    if risk_score > asset.risk_score:
        asset.risk_score = int(risk_score)
        asset.risk_level = severity_for(risk_score)


def _build_description(result: dict, event: SecurityEvent) -> str:
    target = f"{event.destination_ip}:{event.destination_port}" if event.destination_ip else "the monitored network"
    return (
        f"{result['classification']} observed from {event.source_ip} towards {target} "
        f"over {event.protocol}. Risk score {result['risk_score']}/100 "
        f"({result['severity']}), engine confidence {result['confidence'] * 100:.0f}%."
    )


def persist_analysis(cleaned: dict, user=None, channel: str = "manual",
                     sensitivity: float | None = None, commit: bool = True,
                     auto_incident: bool = True) -> dict:
    """Persist an event, analyse it and create every downstream artefact."""
    config = current_app.config
    timestamp = cleaned.get("timestamp") or datetime.utcnow()

    asset = None
    if cleaned.get("asset_id"):
        asset = Asset.query.get(cleaned["asset_id"])
    if asset is None:
        asset = resolve_asset(cleaned.get("source_ip"), cleaned.get("destination_ip"))

    event = SecurityEvent(
        timestamp=timestamp,
        source_ip=cleaned["source_ip"],
        destination_ip=cleaned.get("destination_ip"),
        source_port=cleaned.get("source_port"),
        destination_port=cleaned.get("destination_port"),
        protocol=cleaned.get("protocol") or "TCP",
        event_type=cleaned.get("event_type") or "network_traffic",
        request_count=cleaned.get("request_count") or 0,
        failed_login_attempts=cleaned.get("failed_login_attempts") or 0,
        packet_count=cleaned.get("packet_count") or 0,
        bytes_transferred=cleaned.get("bytes_transferred") or 0.0,
        connection_duration=cleaned.get("connection_duration") or 0.0,
        user_agent=cleaned.get("user_agent"),
        raw_log=cleaned.get("raw_log"),
        source_channel=channel,
        asset_id=asset.id if asset else None,
    )
    db.session.add(event)
    db.session.flush()  # assigns event.id without committing

    result = get_engine().detect(event.feature_payload(), sensitivity=sensitivity)

    detection = DetectionResult(
        event_id=event.id,
        classification=result["classification"],
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        severity=result["severity"],
        is_threat=result["is_threat"],
        rule_score=result["scores"]["rule"],
        anomaly_score=result["scores"]["anomaly"],
        ml_score=result["scores"]["ml"],
        engine_version=result["engine_version"],
        model_used=result["model_used"],
        recommended_action=result["recommended_action"],
        analysis_time_ms=result["analysis_time_ms"],
    )
    detection.reasons = result["reasons"]
    detection.features = result["feature_summary"]
    db.session.add(detection)

    event.processed = True

    threat = None
    alert = None
    incident = None

    if result["is_threat"]:
        threat = Threat(
            event_id=event.id,
            category=result["classification"],
            description=_build_description(result, event),
            severity=result["severity"],
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            source_ip=event.source_ip,
            destination_ip=event.destination_ip,
            mitre_tactic=result.get("mitre_tactic"),
            detected_at=timestamp,
        )
        threat.indicators = [
            {"type": "source_ip", "value": event.source_ip},
            {"type": "destination_port", "value": event.destination_port},
            {"type": "protocol", "value": event.protocol},
        ]
        db.session.add(threat)
        db.session.flush()

    if result["risk_score"] >= config["ALERT_RISK_THRESHOLD"] and threat is not None:
        alert = Alert(
            alert_code=next_code("ALT", Alert, Alert.id),
            event_id=event.id,
            threat_id=threat.id,
            title=f"{result['classification']} from {event.source_ip}",
            threat_type=result["classification"],
            source_ip=event.source_ip,
            destination_ip=event.destination_ip,
            severity=result["severity"],
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            status="NEW",
            description=threat.description,
            recommended_action=result["recommended_action"],
            created_at=timestamp,
            updated_at=datetime.utcnow(),
        )
        alert.reasons = result["reasons"]
        db.session.add(alert)
        db.session.flush()

    if (auto_incident and alert is not None
            and result["risk_score"] >= config["INCIDENT_RISK_THRESHOLD"]):
        incident = Incident(
            incident_code=next_code("INC", Incident, Incident.id),
            title=f"{result['classification']} targeting "
                  f"{event.destination_ip or 'internal network'}",
            description=threat.description,
            threat_type=result["classification"],
            severity=result["severity"],
            priority=SEVERITY_TO_PRIORITY.get(result["severity"], "P3"),
            status="NEW",
            risk_score=result["risk_score"],
            source_ip=event.source_ip,
            detected_at=timestamp,
            assigned_to=getattr(user, "id", None),
        )
        incident.append_history(
            None, "NEW", getattr(user, "full_name", "Detection Engine"),
            "Incident opened automatically because the risk score reached the critical band.",
        )
        db.session.add(incident)
        db.session.flush()
        alert.incident_id = incident.id

    _update_asset_risk(asset, result["risk_score"], timestamp)

    if commit:
        db.session.commit()

    logger.info(
        "Analysed event #%s from %s -> %s (%s, risk=%s)",
        event.id, event.source_ip, event.destination_ip,
        result["classification"], result["risk_score"],
    )

    return {
        "event": event,
        "detection": detection,
        "threat": threat,
        "alert": alert,
        "incident": incident,
        "result": result,
    }


def analysis_to_response(bundle: dict, include_features: bool = True) -> dict:
    """Shape a persisted analysis for the Threat Detection page."""
    result = bundle["result"]
    event = bundle["event"]
    alert = bundle["alert"]
    incident = bundle["incident"]
    return {
        "event_id": event.id,
        "event": event.to_dict(),
        "classification": result["classification"],
        "risk_score": result["risk_score"],
        "confidence": result["confidence"],
        "severity": result["severity"],
        "is_threat": result["is_threat"],
        "reasons": result["reasons"],
        "recommended_action": result["recommended_action"],
        "mitre_tactic": result.get("mitre_tactic"),
        "scores": result["scores"],
        "triggered_rules": result["triggered_rules"],
        "feature_summary": result["feature_summary"] if include_features else None,
        "model_used": result["model_used"],
        "engine_version": result["engine_version"],
        "analysis_time_ms": result["analysis_time_ms"],
        "alert": alert.to_dict() if alert else None,
        "incident": incident.to_dict() if incident else None,
        "threat_id": bundle["threat"].id if bundle["threat"] else None,
    }


def analyze_batch(rows, user=None, channel: str = "csv", sensitivity: float | None = None) -> dict:
    """Analyse many events (CSV upload) inside a single transaction."""
    summary = {
        "total_records": len(rows),
        "normal_events": 0,
        "suspicious_events": 0,
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
        "alerts_created": 0,
        "incidents_created": 0,
        "categories": {},
        "records": [],
        "top_sources": {},
    }

    for row in rows:
        bundle = persist_analysis(
            row, user=user, channel=channel, sensitivity=sensitivity, commit=False,
        )
        result = bundle["result"]
        severity = result["severity"]
        summary[severity.lower()] += 1
        if result["is_threat"]:
            summary["suspicious_events"] += 1
        else:
            summary["normal_events"] += 1
        if bundle["alert"] is not None:
            summary["alerts_created"] += 1
        if bundle["incident"] is not None:
            summary["incidents_created"] += 1

        category = result["classification"]
        summary["categories"][category] = summary["categories"].get(category, 0) + 1
        source = bundle["event"].source_ip
        summary["top_sources"][source] = summary["top_sources"].get(source, 0) + 1

        summary["records"].append(
            {
                "event_id": bundle["event"].id,
                "timestamp": bundle["event"].timestamp.isoformat(timespec="seconds"),
                "source_ip": bundle["event"].source_ip,
                "destination_ip": bundle["event"].destination_ip,
                "destination_port": bundle["event"].destination_port,
                "protocol": bundle["event"].protocol,
                "event_type": bundle["event"].event_type,
                "classification": result["classification"],
                "risk_score": result["risk_score"],
                "severity": severity,
                "confidence": result["confidence"],
                "reason": result["reasons"][0] if result["reasons"] else "",
            }
        )

    db.session.commit()

    summary["high_risk_events"] = summary["high"] + summary["critical"]
    summary["top_sources"] = sorted(
        ({"source_ip": ip, "count": count} for ip, count in summary["top_sources"].items()),
        key=lambda item: item["count"],
        reverse=True,
    )[:10]
    summary["categories"] = sorted(
        ({"category": name, "count": count} for name, count in summary["categories"].items()),
        key=lambda item: item["count"],
        reverse=True,
    )

    audit(
        "LOG_UPLOAD_ANALYSED",
        f"Analysed {summary['total_records']} records from an uploaded log file: "
        f"{summary['suspicious_events']} suspicious, {summary['alerts_created']} alerts raised.",
        entity_type="SecurityEvent",
        user=user,
        commit=True,
    )
    return summary
