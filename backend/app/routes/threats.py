"""Threat and threat-intelligence endpoints."""
from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import or_

from ..extensions import db
from ..models import Threat, ThreatIndicator
from ..models.threat import THREAT_CATEGORIES
from ..models.threat_indicator import INDICATOR_TYPES
from ..services.audit_service import record as audit
from ..utils.errors import NotFoundError
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import SEVERITIES, parse_pagination, require_dict

bp = Blueprint("threats", __name__, url_prefix="/api/threats")
intel_bp = Blueprint("threat_intelligence", __name__, url_prefix="/api/threat-intelligence")


@bp.get("")
@token_required
def list_threats():
    """GET /api/threats - the classified threat history."""
    page, per_page = parse_pagination(request.args)
    query = Threat.query

    severity = request.args.get("severity")
    if severity and severity.upper() != "ALL":
        query = query.filter(Threat.severity == severity.upper())

    category = request.args.get("category")
    if category and category.lower() != "all":
        query = query.filter(Threat.category == category)

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Threat.source_ip.ilike(pattern), Threat.category.ilike(pattern),
                Threat.description.ilike(pattern))
        )

    total = query.count()
    rows = (
        query.order_by(Threat.detected_at.desc(), Threat.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return paginated(
        [threat.to_dict() for threat in rows],
        total,
        page,
        per_page,
        filters={"categories": list(THREAT_CATEGORIES), "severities": SEVERITIES},
    )


@bp.get("/<int:threat_id>")
@token_required
def get_threat(threat_id: int):
    """GET /api/threats/<id> - one threat with its originating event."""
    threat = Threat.query.get(threat_id)
    if threat is None:
        raise NotFoundError(f"Threat #{threat_id} was not found.")
    return success(threat.to_dict(include_event=True))


@intel_bp.get("")
@token_required
def list_indicators():
    """GET /api/threat-intelligence - simulated defensive indicator feed."""
    page, per_page = parse_pagination(request.args, default_per_page=50)
    query = ThreatIndicator.query

    indicator_type = request.args.get("indicator_type")
    if indicator_type and indicator_type.lower() != "all":
        query = query.filter(ThreatIndicator.indicator_type == indicator_type)

    risk = request.args.get("risk_level")
    if risk and risk.upper() != "ALL":
        query = query.filter(ThreatIndicator.risk_level == risk.upper())

    status = request.args.get("status")
    if status and status.upper() != "ALL":
        query = query.filter(ThreatIndicator.status == status.upper())

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(ThreatIndicator.indicator.ilike(pattern),
                ThreatIndicator.description.ilike(pattern))
        )

    total = query.count()
    rows = (
        query.order_by(ThreatIndicator.last_seen.desc(), ThreatIndicator.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return paginated(
        [indicator.to_dict() for indicator in rows],
        total,
        page,
        per_page,
        filters={
            "types": list(INDICATOR_TYPES),
            "risk_levels": SEVERITIES,
            "statuses": ["ACTIVE", "MONITORING", "RETIRED"],
        },
        notice="All indicators in this feed are simulated for academic demonstration. "
               "They use RFC 5737 documentation addresses and reserved domain names.",
    )


@intel_bp.put("/<int:indicator_id>")
@token_required
def update_indicator(indicator_id: int):
    """PUT /api/threat-intelligence/<id> - change an indicator's watch status."""
    payload = require_dict(request.get_json(silent=True) or {})
    indicator = ThreatIndicator.query.get(indicator_id)
    if indicator is None:
        raise NotFoundError(f"Threat indicator #{indicator_id} was not found.")

    status = (payload.get("status") or "").strip().upper()
    if status in ("ACTIVE", "MONITORING", "RETIRED"):
        indicator.status = status
    indicator.last_seen = datetime.utcnow()

    audit(
        "INDICATOR_UPDATED",
        f"Indicator '{indicator.indicator}' set to {indicator.status}.",
        entity_type="ThreatIndicator",
        entity_id=indicator.id,
        user=current_user(),
    )
    db.session.commit()
    return success(indicator.to_dict(), message="Indicator updated.")
