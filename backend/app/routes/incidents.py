"""Incident endpoints: /api/incidents/*"""
from flask import Blueprint, request

from ..models import Incident, User
from ..services import incident_service
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import INCIDENT_STATUSES, parse_pagination, require_dict

bp = Blueprint("incidents", __name__, url_prefix="/api/incidents")

ACTION_TO_STATUS = {
    "investigate": "INVESTIGATING",
    "open": "OPEN",
    "contain": "CONTAINED",
    "resolve": "RESOLVED",
    "false_positive": "FALSE_POSITIVE",
    "reopen": "INVESTIGATING",
}


@bp.get("")
@token_required
def list_incidents():
    """GET /api/incidents - filtered, paginated incident list."""
    page, per_page = parse_pagination(request.args)
    query = incident_service.build_query(request.args)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    analysts = [
        {"id": user.id, "full_name": user.full_name, "role": user.role}
        for user in User.query.filter(User.is_active.is_(True)).all()
    ]
    return paginated(
        [incident.to_dict() for incident in rows],
        total,
        page,
        per_page,
        filters={"statuses": INCIDENT_STATUSES, "analysts": analysts},
    )


@bp.get("/<int:incident_id>")
@token_required
def get_incident(incident_id: int):
    """GET /api/incidents/<id> - full detail, history, alerts and related events."""
    incident = incident_service.get_incident(incident_id)
    data = incident.to_dict(include_alerts=True)
    data["related_events"] = incident_service.related_events(incident)
    data["state_machine"] = {
        "current": incident.status,
        "allowed": Incident.allowed_transitions(incident.status),
        "all_states": INCIDENT_STATUSES,
    }
    return success(data)


@bp.post("")
@token_required
def create_incident():
    """POST /api/incidents - raise an incident manually."""
    payload = require_dict(request.get_json(silent=True) or {})
    incident = incident_service.create_incident(payload, current_user())
    return success(
        incident.to_dict(include_alerts=True),
        message=f"Incident {incident.incident_code} created.",
        status_code=201,
    )


@bp.put("/<int:incident_id>")
@token_required
def update_incident(incident_id: int):
    """PUT /api/incidents/<id> - drive the lifecycle state machine."""
    payload = require_dict(request.get_json(silent=True) or {})
    incident = incident_service.get_incident(incident_id)

    if "assigned_to" in payload and "status" not in payload and "action" not in payload:
        updated = incident_service.assign(incident, payload.get("assigned_to"), current_user())
        return success(updated.to_dict(include_alerts=True), message="Incident reassigned.")

    action = (payload.get("action") or "").strip().lower()
    status = payload.get("status") or ACTION_TO_STATUS.get(action)

    updated = incident_service.transition(
        incident,
        status,
        payload.get("note"),
        current_user(),
        resolution_summary=payload.get("resolution_summary"),
    )
    if payload.get("assigned_to") is not None:
        updated = incident_service.assign(updated, payload.get("assigned_to"), current_user())

    return success(
        updated.to_dict(include_alerts=True),
        message=f"Incident {updated.incident_code} is now "
                f"{updated.status.replace('_', ' ').title()}.",
    )
