"""Incident lifecycle service (FR-07).

The transition guard here is the runtime enforcement of the State Transition
Diagram: an illegal move returns HTTP 409 rather than silently corrupting the
lifecycle.
"""
from datetime import datetime

from sqlalchemy import or_

from ..extensions import db
from ..models import Alert, Incident, User
from ..utils.errors import ConflictError, NotFoundError, ValidationError
from ..utils.validators import INCIDENT_STATUSES, SEVERITIES, validate_string
from .audit_service import record as audit
from .detection_service import SEVERITY_TO_PRIORITY, next_code


def build_query(args):
    query = Incident.query

    status = args.get("status")
    if status and status.upper() != "ALL":
        query = query.filter(Incident.status == status.upper())

    severity = args.get("severity")
    if severity and severity.upper() != "ALL":
        query = query.filter(Incident.severity == severity.upper())

    assigned_to = args.get("assigned_to")
    if assigned_to and str(assigned_to).lower() not in ("all", ""):
        if str(assigned_to).lower() == "unassigned":
            query = query.filter(Incident.assigned_to.is_(None))
        else:
            try:
                query = query.filter(Incident.assigned_to == int(assigned_to))
            except ValueError as exc:
                raise ValidationError(
                    "assigned_to must be a user id or 'unassigned'.",
                    details={"field": "assigned_to"},
                ) from exc

    search = (args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Incident.incident_code.ilike(pattern),
                Incident.title.ilike(pattern),
                Incident.source_ip.ilike(pattern),
                Incident.threat_type.ilike(pattern),
            )
        )

    sort = (args.get("sort") or "newest").lower()
    if sort == "risk":
        query = query.order_by(Incident.risk_score.desc(), Incident.id.desc())
    elif sort == "oldest":
        query = query.order_by(Incident.detected_at.asc(), Incident.id.asc())
    else:
        query = query.order_by(Incident.detected_at.desc(), Incident.id.desc())
    return query


def get_incident(incident_id: int) -> Incident:
    incident = Incident.query.get(incident_id)
    if incident is None:
        raise NotFoundError(f"Incident #{incident_id} was not found.")
    return incident


def create_incident(payload: dict, user) -> Incident:
    title = validate_string(payload.get("title"), "title", 180)
    severity = (payload.get("severity") or "MEDIUM").upper()
    if severity not in SEVERITIES:
        raise ValidationError(
            f"severity must be one of: {', '.join(SEVERITIES)}.",
            details={"field": "severity", "allowed": SEVERITIES},
        )

    risk_score = payload.get("risk_score")
    try:
        risk_score = int(risk_score) if risk_score not in (None, "") else {
            "LOW": 15, "MEDIUM": 40, "HIGH": 65, "CRITICAL": 88
        }[severity]
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "risk_score must be an integer between 0 and 100.",
            details={"field": "risk_score"},
        ) from exc
    risk_score = max(0, min(100, risk_score))

    assigned_to = payload.get("assigned_to") or getattr(user, "id", None)
    if assigned_to and User.query.get(assigned_to) is None:
        raise ValidationError(
            f"No analyst exists with id {assigned_to}.", details={"field": "assigned_to"}
        )

    incident = Incident(
        incident_code=next_code("INC", Incident, Incident.id),
        title=title,
        description=validate_string(
            payload.get("description"), "description", 4000, required=False
        ),
        threat_type=validate_string(
            payload.get("threat_type"), "threat_type", 60, required=False,
            default="Network Anomaly",
        ),
        severity=severity,
        priority=payload.get("priority") or SEVERITY_TO_PRIORITY.get(severity, "P3"),
        status="NEW",
        risk_score=risk_score,
        source_ip=validate_string(payload.get("source_ip"), "source_ip", 45, required=False),
        detected_at=datetime.utcnow(),
        assigned_to=assigned_to,
    )
    incident.append_history(
        None, "NEW", getattr(user, "full_name", "Analyst"), "Incident created manually."
    )
    db.session.add(incident)
    db.session.flush()

    alert_ids = payload.get("alert_ids") or []
    if isinstance(alert_ids, list) and alert_ids:
        linked = Alert.query.filter(Alert.id.in_([int(a) for a in alert_ids])).all()
        for alert in linked:
            alert.incident_id = incident.id

    audit(
        "INCIDENT_CREATED",
        f"Incident {incident.incident_code} created: {incident.title}.",
        entity_type="Incident",
        entity_id=incident.id,
        user=user,
    )
    db.session.commit()
    return incident


def transition(incident: Incident, new_status: str, note: str | None, user,
               resolution_summary: str | None = None) -> Incident:
    new_status = (new_status or "").strip().upper()
    if new_status not in INCIDENT_STATUSES:
        raise ValidationError(
            f"status must be one of: {', '.join(INCIDENT_STATUSES)}.",
            details={"field": "status", "allowed": INCIDENT_STATUSES},
        )
    if not Incident.can_transition(incident.status, new_status):
        raise ConflictError(
            f"Invalid lifecycle transition: {incident.status} -> {new_status}. "
            f"Allowed from {incident.status}: "
            f"{', '.join(Incident.allowed_transitions(incident.status)) or 'none'}.",
            details={
                "current": incident.status,
                "requested": new_status,
                "allowed": Incident.allowed_transitions(incident.status),
            },
        )

    previous = incident.status
    incident.status = new_status
    incident.updated_at = datetime.utcnow()

    if new_status == "CONTAINED":
        incident.contained_at = datetime.utcnow()
    if new_status in ("RESOLVED", "FALSE_POSITIVE"):
        incident.resolved_at = datetime.utcnow()
        if resolution_summary:
            incident.resolution_summary = resolution_summary
        # Closing an incident closes the alerts that belong to it.
        target_alert_status = "RESOLVED" if new_status == "RESOLVED" else "FALSE_POSITIVE"
        for alert in incident.alerts:
            if alert.status not in ("RESOLVED", "FALSE_POSITIVE"):
                alert.status = target_alert_status
                alert.resolved_at = datetime.utcnow()
                alert.updated_at = datetime.utcnow()
    else:
        incident.resolved_at = None

    incident.append_history(
        previous, new_status, getattr(user, "full_name", "Analyst"), note or ""
    )

    audit(
        "INCIDENT_STATUS_CHANGED",
        f"Incident {incident.incident_code} moved from {previous} to {new_status}.",
        entity_type="Incident",
        entity_id=incident.id,
        user=user,
    )
    db.session.commit()
    return incident


def assign(incident: Incident, user_id, actor) -> Incident:
    analyst = User.query.get(user_id) if user_id else None
    if user_id and analyst is None:
        raise ValidationError(
            f"No analyst exists with id {user_id}.", details={"field": "assigned_to"}
        )
    incident.assigned_to = analyst.id if analyst else None
    incident.updated_at = datetime.utcnow()
    incident.append_history(
        incident.status, incident.status, getattr(actor, "full_name", "Analyst"),
        f"Assigned to {analyst.full_name if analyst else 'nobody'}.",
    )
    audit(
        "INCIDENT_ASSIGNED",
        f"Incident {incident.incident_code} assigned to "
        f"{analyst.full_name if analyst else 'nobody'}.",
        entity_type="Incident",
        entity_id=incident.id,
        user=actor,
    )
    db.session.commit()
    return incident


def related_events(incident: Incident, limit: int = 20) -> list:
    """Events tied to the incident through its alerts, plus same-source activity."""
    from ..models import SecurityEvent

    event_ids = [alert.event_id for alert in incident.alerts if alert.event_id]
    events = []
    if event_ids:
        events = (
            SecurityEvent.query.filter(SecurityEvent.id.in_(event_ids))
            .order_by(SecurityEvent.timestamp.desc())
            .all()
        )
    if incident.source_ip and len(events) < limit:
        extra = (
            SecurityEvent.query.filter(
                SecurityEvent.source_ip == incident.source_ip,
                ~SecurityEvent.id.in_(event_ids or [-1]),
            )
            .order_by(SecurityEvent.timestamp.desc())
            .limit(limit - len(events))
            .all()
        )
        events.extend(extra)
    return [event.to_dict(include_detection=True) for event in events[:limit]]
