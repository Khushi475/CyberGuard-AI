"""Alert endpoints: /api/alerts/*"""
from flask import Blueprint, request

from ..services import alert_service
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import parse_pagination, require_dict

bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")

ACTION_TO_STATUS = {
    "investigate": "INVESTIGATING",
    "acknowledge": "ACKNOWLEDGED",
    "resolve": "RESOLVED",
    "false_positive": "FALSE_POSITIVE",
    "reopen": "INVESTIGATING",
}


@bp.get("")
@token_required
def list_alerts():
    """GET /api/alerts - filtered, paginated alert queue."""
    page, per_page = parse_pagination(request.args)
    query = alert_service.build_query(request.args)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated(
        [alert.to_dict() for alert in rows],
        total,
        page,
        per_page,
        filters=alert_service.alert_filter_options(),
    )


@bp.get("/<int:alert_id>")
@token_required
def get_alert(alert_id: int):
    """GET /api/alerts/<id> - full alert detail for the incident-details view."""
    alert = alert_service.get_alert(alert_id)
    return success(alert.to_dict(include_event=True))


@bp.put("/<int:alert_id>")
@token_required
def update_alert(alert_id: int):
    """PUT /api/alerts/<id> - change status via ``status`` or ``action``."""
    payload = require_dict(request.get_json(silent=True) or {})
    alert = alert_service.get_alert(alert_id)

    action = (payload.get("action") or "").strip().lower()
    status = payload.get("status") or ACTION_TO_STATUS.get(action)

    updated = alert_service.update_status(alert, status, payload.get("note"), current_user())
    return success(
        updated.to_dict(include_event=True),
        message=f"Alert {updated.alert_code} is now {updated.status.replace('_', ' ').title()}.",
    )


@bp.post("/<int:alert_id>/escalate")
@token_required
def escalate_alert(alert_id: int):
    """POST /api/alerts/<id>/escalate - open an incident from this alert."""
    payload = require_dict(request.get_json(silent=True) or {})
    alert = alert_service.get_alert(alert_id)
    incident = alert_service.escalate_to_incident(alert, current_user(), payload.get("title"))
    return success(
        {"incident": incident.to_dict(), "alert": alert.to_dict()},
        message=f"Incident {incident.incident_code} opened from alert {alert.alert_code}.",
        status_code=201,
    )


@bp.get("/filters")
@token_required
def filters():
    """GET /api/alerts/filters - dropdown values for the Alerts page."""
    return success(alert_service.alert_filter_options())
