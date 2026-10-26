"""Analytics and dashboard aggregation (FR-02).

Every number returned here is computed from the SQLite database with SQLAlchemy
aggregates - nothing is hard-coded, so the dashboard changes as soon as new
events are analysed.
"""
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app
from sqlalchemy import func

from ..extensions import db
from ..models import (Alert, Asset, AuditLog, DetectionResult, Incident, SecurityEvent,
                      Threat, ThreatIndicator)

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ACTIVE_INCIDENT_STATES = ("NEW", "OPEN", "INVESTIGATING", "CONTAINED")
OPEN_ALERT_STATES = ("NEW", "ACKNOWLEDGED", "INVESTIGATING")


def _date_series(days: int):
    today = datetime.utcnow().date()
    return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def _count(model, *filters) -> int:
    query = db.session.query(func.count(model.id))
    for condition in filters:
        query = query.filter(condition)
    return int(query.scalar() or 0)


def threat_level() -> dict:
    """Overall posture derived from unresolved alerts in the last 24 hours."""
    since = datetime.utcnow() - timedelta(hours=24)
    rows = (
        db.session.query(Alert.severity, func.count(Alert.id))
        .filter(Alert.created_at >= since, Alert.status.in_(OPEN_ALERT_STATES))
        .group_by(Alert.severity)
        .all()
    )
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    for severity, total in rows:
        if severity in counts:
            counts[severity] = int(total)

    if counts["CRITICAL"] >= 1:
        level, score = "CRITICAL", 92
    elif counts["HIGH"] >= 3:
        level, score = "HIGH", 74
    elif counts["HIGH"] >= 1 or counts["MEDIUM"] >= 5:
        level, score = "MEDIUM", 48
    else:
        level, score = "LOW", 18

    return {
        "level": level,
        "score": score,
        "window_hours": 24,
        "open_by_severity": counts,
        "basis": "Unresolved alerts raised in the last 24 hours.",
    }


def detection_quality() -> dict:
    """Detection accuracy measured from analyst triage decisions.

    We never invent a number.  Precision is only reported once analysts have
    actually closed alerts; until then the endpoint says so explicitly and falls
    back to the model's synthetic hold-out score (clearly labelled).
    """
    resolved = _count(Alert, Alert.status == "RESOLVED")
    false_positive = _count(Alert, Alert.status == "FALSE_POSITIVE")
    triaged = resolved + false_positive

    payload = {
        "triaged_alerts": triaged,
        "confirmed_true_positive": resolved,
        "confirmed_false_positive": false_positive,
    }

    if triaged >= 5:
        precision = resolved / triaged
        payload.update(
            {
                "accuracy": round(precision * 100, 1),
                "source": "analyst_triage",
                "label": "Analyst-confirmed precision",
                "note": f"Measured from {triaged} alerts closed by analysts.",
            }
        )
        return payload

    metadata_path = Path(current_app.config["ML_MODEL_DIR"]) / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                metadata = json.load(handle)
            payload.update(
                {
                    "accuracy": round(float(metadata.get("holdout_accuracy", 0)) * 100, 1),
                    "source": "model_holdout",
                    "label": "Model hold-out accuracy (synthetic data)",
                    "note": "Measured on the synthetic hold-out split created during training, "
                            "not on real-world traffic.",
                }
            )
            return payload
        except (ValueError, OSError):
            pass

    mean_confidence = db.session.query(func.avg(DetectionResult.confidence)).scalar()
    payload.update(
        {
            "accuracy": round(float(mean_confidence or 0) * 100, 1),
            "source": "engine_confidence",
            "label": "Mean engine confidence",
            "note": "No analyst-triaged alerts and no trained model yet, so the mean engine "
                    "confidence is shown instead of a measured accuracy.",
        }
    )
    return payload


def system_health() -> dict:
    """A lightweight self-check used by the dashboard health widget."""
    checks = []
    try:
        db.session.execute(db.text("SELECT 1"))
        checks.append({"component": "Database", "status": "OPERATIONAL",
                       "detail": "SQLite connection responding."})
    except Exception as exc:  # pragma: no cover - only on a broken database
        checks.append({"component": "Database", "status": "DEGRADED", "detail": str(exc)})

    from .detection_service import get_engine

    info = get_engine().model_info()
    checks.append(
        {
            "component": "Detection Engine",
            "status": "OPERATIONAL",
            "detail": f"Running in {info['mode']} mode with {info['feature_count']} features.",
        }
    )
    checks.append(
        {
            "component": "ML Models",
            "status": "OPERATIONAL" if info["ml_available"] else "FALLBACK",
            "detail": "Trained models loaded." if info["ml_available"]
            else "No trained model found - using rules plus statistical baseline.",
        }
    )
    unprocessed = _count(SecurityEvent, SecurityEvent.processed.is_(False))
    checks.append(
        {
            "component": "Event Pipeline",
            "status": "OPERATIONAL" if unprocessed == 0 else "BACKLOG",
            "detail": f"{unprocessed} event(s) awaiting analysis.",
        }
    )

    degraded = [c for c in checks if c["status"] not in ("OPERATIONAL", "FALLBACK")]
    overall = "OPERATIONAL" if not degraded else "DEGRADED"
    score = 100 - (len(degraded) * 25) - (0 if info["ml_available"] else 5)
    return {"overall": overall, "score": max(0, score), "checks": checks}


def dashboard_stats(days: int = 14) -> dict:
    now = datetime.utcnow()
    since = now - timedelta(days=days)

    total_events = _count(SecurityEvent)
    total_threats = _count(Threat)
    critical_alerts = _count(Alert, Alert.severity == "CRITICAL")
    open_alerts = _count(Alert, Alert.status.in_(OPEN_ALERT_STATES))
    active_incidents = _count(Incident, Incident.status.in_(ACTIVE_INCIDENT_STATES))
    resolved_incidents = _count(Incident, Incident.status == "RESOLVED")
    monitored_assets = _count(Asset)
    at_risk_assets = _count(Asset, Asset.risk_level.in_(("HIGH", "CRITICAL")))
    indicators = _count(ThreatIndicator, ThreatIndicator.status == "ACTIVE")

    events_24h = _count(SecurityEvent, SecurityEvent.timestamp >= now - timedelta(hours=24))
    threats_24h = _count(Threat, Threat.detected_at >= now - timedelta(hours=24))

    return {
        "totals": {
            "total_events": total_events,
            "threats_detected": total_threats,
            "critical_alerts": critical_alerts,
            "open_alerts": open_alerts,
            "active_incidents": active_incidents,
            "resolved_incidents": resolved_incidents,
            "monitored_assets": monitored_assets,
            "assets_at_risk": at_risk_assets,
            "active_indicators": indicators,
            "events_last_24h": events_24h,
            "threats_last_24h": threats_24h,
        },
        "threat_level": threat_level(),
        "detection_quality": detection_quality(),
        "system_health": system_health(),
        "charts": {
            "threats_over_time": threats_over_time(days),
            "severity_distribution": severity_distribution(),
            "category_distribution": category_distribution(),
            "events_by_source": events_by_source(),
            "detection_trend": detection_trend(days),
            "protocol_distribution": protocol_distribution(),
        },
        "recent_alerts": [alert.to_dict() for alert in recent_alerts(6)],
        "activity_feed": activity_feed(12),
        "window_days": days,
        "generated_at": now.isoformat(timespec="seconds"),
    }


def threats_over_time(days: int = 14) -> list:
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.session.query(
            func.date(Threat.detected_at).label("day"),
            Threat.severity,
            func.count(Threat.id),
        )
        .filter(Threat.detected_at >= since)
        .group_by("day", Threat.severity)
        .all()
    )
    buckets = OrderedDict(
        (day.isoformat(), {"date": day.isoformat(), "LOW": 0, "MEDIUM": 0,
                           "HIGH": 0, "CRITICAL": 0, "total": 0})
        for day in _date_series(days)
    )
    for day, severity, total in rows:
        key = str(day)[:10]
        if key in buckets and severity in SEVERITY_ORDER:
            buckets[key][severity] = int(total)
            buckets[key]["total"] += int(total)
    return list(buckets.values())


def detection_trend(days: int = 14) -> list:
    since = datetime.utcnow() - timedelta(days=days)
    event_rows = dict(
        db.session.query(func.date(SecurityEvent.timestamp), func.count(SecurityEvent.id))
        .filter(SecurityEvent.timestamp >= since)
        .group_by(func.date(SecurityEvent.timestamp))
        .all()
    )
    threat_rows = dict(
        db.session.query(func.date(Threat.detected_at), func.count(Threat.id))
        .filter(Threat.detected_at >= since)
        .group_by(func.date(Threat.detected_at))
        .all()
    )
    series = []
    for day in _date_series(days):
        key = day.isoformat()
        events = int(event_rows.get(key, 0))
        threats = int(threat_rows.get(key, 0))
        series.append(
            {
                "date": key,
                "events": events,
                "threats": threats,
                "detection_rate": round((threats / events) * 100, 1) if events else 0.0,
            }
        )
    return series


def severity_distribution() -> list:
    rows = (
        db.session.query(DetectionResult.severity, func.count(DetectionResult.id))
        .group_by(DetectionResult.severity)
        .all()
    )
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    for severity, total in rows:
        if severity in counts:
            counts[severity] = int(total)
    return [{"severity": severity, "count": counts[severity]} for severity in SEVERITY_ORDER]


def category_distribution(limit: int = 8) -> list:
    rows = (
        db.session.query(Threat.category, func.count(Threat.id))
        .group_by(Threat.category)
        .order_by(func.count(Threat.id).desc())
        .limit(limit)
        .all()
    )
    return [{"category": category, "count": int(total)} for category, total in rows]


def events_by_source(limit: int = 8) -> list:
    rows = (
        db.session.query(SecurityEvent.source_ip, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.source_ip)
        .order_by(func.count(SecurityEvent.id).desc())
        .limit(limit)
        .all()
    )
    return [{"source_ip": ip, "count": int(total)} for ip, total in rows]


def protocol_distribution() -> list:
    rows = (
        db.session.query(SecurityEvent.protocol, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.protocol)
        .order_by(func.count(SecurityEvent.id).desc())
        .all()
    )
    return [{"protocol": protocol, "count": int(total)} for protocol, total in rows]


def event_type_distribution() -> list:
    rows = (
        db.session.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.event_type)
        .order_by(func.count(SecurityEvent.id).desc())
        .all()
    )
    return [{"event_type": event_type, "count": int(total)} for event_type, total in rows]


def hourly_distribution() -> list:
    rows = (
        db.session.query(
            func.strftime("%H", SecurityEvent.timestamp), func.count(SecurityEvent.id)
        )
        .group_by(func.strftime("%H", SecurityEvent.timestamp))
        .all()
    )
    counts = {f"{hour:02d}": 0 for hour in range(24)}
    for hour, total in rows:
        if hour in counts:
            counts[hour] = int(total)
    return [{"hour": hour, "count": count} for hour, count in counts.items()]


def recent_alerts(limit: int = 6):
    return (
        Alert.query.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit).all()
    )


def activity_feed(limit: int = 12) -> list:
    """Merged, newest-first stream of detections, alerts, incidents and audit rows."""
    feed = []

    for alert in Alert.query.order_by(Alert.created_at.desc()).limit(limit).all():
        feed.append(
            {
                "type": "alert",
                "severity": alert.severity,
                "title": alert.title,
                "message": f"Alert {alert.alert_code} raised with risk score "
                           f"{alert.risk_score}/100.",
                "timestamp": alert.created_at.isoformat(timespec="seconds"),
                "reference": alert.alert_code,
                "entity_id": alert.id,
            }
        )

    for incident in Incident.query.order_by(Incident.updated_at.desc()).limit(limit).all():
        feed.append(
            {
                "type": "incident",
                "severity": incident.severity,
                "title": incident.title,
                "message": f"Incident {incident.incident_code} is currently "
                           f"{incident.status.replace('_', ' ').title()}.",
                "timestamp": incident.updated_at.isoformat(timespec="seconds"),
                "reference": incident.incident_code,
                "entity_id": incident.id,
            }
        )

    for log in AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all():
        feed.append(
            {
                "type": "audit",
                "severity": "LOW",
                "title": log.action.replace("_", " ").title(),
                "message": log.description or log.action,
                "timestamp": log.created_at.isoformat(timespec="seconds"),
                "reference": log.action,
                "entity_id": log.id,
            }
        )

    feed.sort(key=lambda item: item["timestamp"], reverse=True)
    return feed[:limit]


def analytics_overview(days: int = 30) -> dict:
    """Payload for the dedicated /api/analytics endpoint."""
    since = datetime.utcnow() - timedelta(days=days)

    avg_risk = db.session.query(func.avg(DetectionResult.risk_score)).scalar()
    avg_confidence = db.session.query(func.avg(DetectionResult.confidence)).scalar()
    avg_latency = db.session.query(func.avg(DetectionResult.analysis_time_ms)).scalar()
    max_latency = db.session.query(func.max(DetectionResult.analysis_time_ms)).scalar()

    mttr_rows = (
        db.session.query(Incident.detected_at, Incident.resolved_at)
        .filter(Incident.resolved_at.isnot(None))
        .all()
    )
    mttr_hours = None
    if mttr_rows:
        deltas = [
            (resolved - detected).total_seconds() / 3600.0
            for detected, resolved in mttr_rows
            if detected and resolved
        ]
        if deltas:
            mttr_hours = round(sum(deltas) / len(deltas), 2)

    channel_rows = (
        db.session.query(SecurityEvent.source_channel, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.source_channel)
        .all()
    )

    return {
        "window_days": days,
        "events_in_window": _count(SecurityEvent, SecurityEvent.timestamp >= since),
        "threats_in_window": _count(Threat, Threat.detected_at >= since),
        "averages": {
            "risk_score": round(float(avg_risk or 0), 2),
            "confidence": round(float(avg_confidence or 0), 3),
            "analysis_time_ms": round(float(avg_latency or 0), 3),
            "max_analysis_time_ms": round(float(max_latency or 0), 3),
        },
        "mean_time_to_resolve_hours": mttr_hours,
        "severity_distribution": severity_distribution(),
        "category_distribution": category_distribution(12),
        "detection_trend": detection_trend(days),
        "threats_over_time": threats_over_time(days),
        "events_by_source": events_by_source(10),
        "protocol_distribution": protocol_distribution(),
        "event_type_distribution": event_type_distribution(),
        "hourly_distribution": hourly_distribution(),
        "ingestion_channels": [
            {"channel": channel, "count": int(total)} for channel, total in channel_rows
        ],
        "detection_quality": detection_quality(),
        "alert_status_breakdown": [
            {"status": status, "count": _count(Alert, Alert.status == status)}
            for status in ("NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE")
        ],
        "incident_status_breakdown": [
            {"status": status, "count": _count(Incident, Incident.status == status)}
            for status in ("NEW", "OPEN", "INVESTIGATING", "CONTAINED", "RESOLVED",
                           "FALSE_POSITIVE")
        ],
    }
