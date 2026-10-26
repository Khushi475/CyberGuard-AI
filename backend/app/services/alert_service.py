"""Alert querying and lifecycle management (FR-06)."""
from datetime import datetime

from sqlalchemy import or_

from ..extensions import db
from ..models import Alert, Incident
from ..utils.errors import ConflictError, NotFoundError, ValidationError
from ..utils.validators import ALERT_STATUSES, SEVERITIES
from .audit_service import record as audit
from .detection_service import SEVERITY_TO_PRIORITY, next_code


def build_query(args):
    """Apply the Alerts page filters to a SQLAlchemy query."""
    query = Alert.query

    severity = args.get("severity")
    if severity and severity.upper() != "ALL":
        query = query.filter(Alert.severity == severity.upper())

    status = args.get("status")
    if status and status.upper() != "ALL":
        query = query.filter(Alert.status == status.upper())

    threat_type = args.get("threat_type")
    if threat_type and threat_type.lower() != "all":
        query = query.filter(Alert.threat_type == threat_type)

    search = (args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Alert.alert_code.ilike(pattern),
                Alert.source_ip.ilike(pattern),
                Alert.title.ilike(pattern),
                Alert.threat_type.ilike(pattern),
            )
        )

    date_from = args.get("date_from")
    if date_from:
        try:
            query = query.filter(Alert.created_at >= datetime.fromisoformat(date_from))
        except ValueError as exc:
            raise ValidationError(
                "date_from must be an ISO date (YYYY-MM-DD).", details={"field": "date_from"}
            ) from exc

    date_to = args.get("date_to")
    if date_to:
        try:
            end = datetime.fromisoformat(date_to)
            end = end.replace(hour=23, minute=59, second=59) if end.hour == 0 else end
            query = query.filter(Alert.created_at <= end)
        except ValueError as exc:
            raise ValidationError(
                "date_to must be an ISO date (YYYY-MM-DD).", details={"field": "date_to"}
            ) from exc

    min_risk = args.get("min_risk")
    if min_risk:
        try:
            query = query.filter(Alert.risk_score >= int(min_risk))
        except ValueError as exc:
            raise ValidationError(
                "min_risk must be an integer.", details={"field": "min_risk"}
            ) from exc

    sort = (args.get("sort") or "newest").lower()
    if sort == "risk":
        query = query.order_by(Alert.risk_score.desc(), Alert.id.desc())
    elif sort == "oldest":
        query = query.order_by(Alert.created_at.asc(), Alert.id.asc())
    else:
        query = query.order_by(Alert.created_at.desc(), Alert.id.desc())
    return query


def get_alert(alert_id: int) -> Alert:
    alert = Alert.query.get(alert_id)
    if alert is None:
        raise NotFoundError(f"Alert #{alert_id} was not found.")
    return alert


def update_status(alert: Alert, new_status: str, note: str | None, user) -> Alert:
    """Apply a status change, honouring the alert state machine."""
    new_status = (new_status or "").strip().upper()
    if new_status not in ALERT_STATUSES:
        raise ValidationError(
            f"status must be one of: {', '.join(ALERT_STATUSES)}.",
            details={"field": "status", "allowed": ALERT_STATUSES},
        )
    if not Alert.can_transition(alert.status, new_status):
        raise ConflictError(
            f"An alert in state {alert.status} cannot move directly to {new_status}.",
            details={"current": alert.status, "requested": new_status},
        )

    previous = alert.status
    alert.status = new_status
    alert.updated_at = datetime.utcnow()
    if note:
        stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        author = getattr(user, "full_name", "Analyst")
        alert.notes = f"{alert.notes}\n" if alert.notes else ""
        alert.notes += f"[{stamp}] {author}: {note}"
    if new_status in ("RESOLVED", "FALSE_POSITIVE"):
        alert.resolved_at = datetime.utcnow()
    else:
        alert.resolved_at = None

    audit(
        "ALERT_STATUS_CHANGED",
        f"Alert {alert.alert_code} moved from {previous} to {new_status}.",
        entity_type="Alert",
        entity_id=alert.id,
        user=user,
    )
    db.session.commit()
    return alert


def escalate_to_incident(alert: Alert, user, title: str | None = None) -> Incident:
    """Create (or return) the incident that tracks this alert."""
    if alert.incident_id:
        existing = Incident.query.get(alert.incident_id)
        if existing is not None:
            return existing

    incident = Incident(
        incident_code=next_code("INC", Incident, Incident.id),
        title=title or f"Investigation: {alert.title}",
        description=alert.description,
        threat_type=alert.threat_type,
        severity=alert.severity,
        priority=SEVERITY_TO_PRIORITY.get(alert.severity, "P3"),
        status="INVESTIGATING",
        risk_score=alert.risk_score,
        source_ip=alert.source_ip,
        detected_at=alert.created_at,
        assigned_to=getattr(user, "id", None),
    )
    incident.append_history(
        None, "INVESTIGATING", getattr(user, "full_name", "Analyst"),
        f"Incident raised from alert {alert.alert_code}.",
    )
    db.session.add(incident)
    db.session.flush()

    alert.incident_id = incident.id
    if alert.status in ("NEW", "ACKNOWLEDGED"):
        alert.status = "INVESTIGATING"
    alert.updated_at = datetime.utcnow()

    audit(
        "ALERT_ESCALATED",
        f"Alert {alert.alert_code} escalated to incident {incident.incident_code}.",
        entity_type="Incident",
        entity_id=incident.id,
        user=user,
    )
    db.session.commit()
    return incident


def alert_filter_options() -> dict:
    """Values the Alerts page uses to populate its filter dropdowns."""
    threat_types = [row[0] for row in db.session.query(Alert.threat_type).distinct().all() if row[0]]
    return {
        "severities": SEVERITIES,
        "statuses": ALERT_STATUSES,
        "threat_types": sorted(threat_types),
    }
