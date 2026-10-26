"""Asset endpoints: /api/assets/*"""
from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import func, or_

from ..extensions import db
from ..models import Asset, SecurityEvent
from ..models.asset import ASSET_TYPES
from ..services.audit_service import record as audit
from ..utils.errors import NotFoundError, ValidationError
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import (ASSET_STATUSES, SEVERITIES, parse_pagination, require_dict,
                                validate_choice, validate_ip, validate_string)

bp = Blueprint("assets", __name__, url_prefix="/api/assets")


def _get_asset(asset_id: int) -> Asset:
    asset = Asset.query.get(asset_id)
    if asset is None:
        raise NotFoundError(f"Asset #{asset_id} was not found.")
    return asset


@bp.get("")
@token_required
def list_assets():
    """GET /api/assets - the monitored inventory with live event counts."""
    page, per_page = parse_pagination(request.args, default_per_page=50)
    query = Asset.query

    status = request.args.get("status")
    if status and status.upper() != "ALL":
        query = query.filter(Asset.status == status.upper())

    risk = request.args.get("risk_level")
    if risk and risk.upper() != "ALL":
        query = query.filter(Asset.risk_level == risk.upper())

    asset_type = request.args.get("asset_type")
    if asset_type and asset_type.lower() != "all":
        query = query.filter(Asset.asset_type == asset_type)

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Asset.name.ilike(pattern), Asset.ip_address.ilike(pattern),
                Asset.operating_system.ilike(pattern))
        )

    total = query.count()
    rows = query.order_by(Asset.risk_score.desc(), Asset.name.asc()) \
        .offset((page - 1) * per_page).limit(per_page).all()

    counts = dict(
        db.session.query(SecurityEvent.asset_id, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.asset_id)
        .all()
    )
    payload = []
    for asset in rows:
        data = asset.to_dict()
        data["event_count"] = int(counts.get(asset.id, 0))
        payload.append(data)

    return paginated(
        payload, total, page, per_page,
        filters={"types": list(ASSET_TYPES), "statuses": ASSET_STATUSES,
                 "risk_levels": SEVERITIES},
    )


@bp.get("/<int:asset_id>")
@token_required
def get_asset(asset_id: int):
    """GET /api/assets/<id> - one asset plus its most recent events."""
    asset = _get_asset(asset_id)
    data = asset.to_dict()
    recent = (
        SecurityEvent.query.filter(SecurityEvent.asset_id == asset.id)
        .order_by(SecurityEvent.timestamp.desc())
        .limit(20)
        .all()
    )
    data["recent_events"] = [event.to_dict(include_detection=True) for event in recent]
    data["event_count"] = SecurityEvent.query.filter(SecurityEvent.asset_id == asset.id).count()
    return success(data)


@bp.post("")
@token_required
def create_asset():
    """POST /api/assets - register a new monitored asset."""
    payload = require_dict(request.get_json(silent=True) or {})

    ip_address = validate_ip(payload.get("ip_address"), "ip_address")
    if Asset.query.filter(Asset.ip_address == ip_address).first() is not None:
        raise ValidationError(
            f"An asset with IP address {ip_address} is already registered.",
            details={"field": "ip_address"},
        )

    asset = Asset(
        name=validate_string(payload.get("name"), "name", 120),
        ip_address=ip_address,
        asset_type=validate_string(
            payload.get("asset_type"), "asset_type", 60, required=False, default="Workstation"
        ),
        operating_system=validate_string(
            payload.get("operating_system"), "operating_system", 80, required=False
        ),
        location=validate_string(payload.get("location"), "location", 80, required=False),
        owner=validate_string(payload.get("owner"), "owner", 120, required=False),
        criticality=validate_choice(
            payload.get("criticality"), SEVERITIES, "criticality", required=False, default="MEDIUM"
        ),
        status=validate_choice(
            payload.get("status"), ASSET_STATUSES, "status", required=False, default="ONLINE"
        ),
        risk_level="LOW",
        risk_score=0,
        last_seen=datetime.utcnow(),
    )
    db.session.add(asset)
    db.session.flush()
    audit(
        "ASSET_CREATED",
        f"Asset '{asset.name}' ({asset.ip_address}) registered for monitoring.",
        entity_type="Asset",
        entity_id=asset.id,
        user=current_user(),
    )
    db.session.commit()
    return success(asset.to_dict(), message=f"Asset '{asset.name}' created.", status_code=201)


@bp.put("/<int:asset_id>")
@token_required
def update_asset(asset_id: int):
    """PUT /api/assets/<id> - update inventory details or operational status."""
    payload = require_dict(request.get_json(silent=True) or {})
    asset = _get_asset(asset_id)

    if "name" in payload:
        asset.name = validate_string(payload.get("name"), "name", 120)
    if "ip_address" in payload:
        new_ip = validate_ip(payload.get("ip_address"), "ip_address")
        clash = Asset.query.filter(Asset.ip_address == new_ip, Asset.id != asset.id).first()
        if clash is not None:
            raise ValidationError(
                f"Asset '{clash.name}' already uses IP address {new_ip}.",
                details={"field": "ip_address"},
            )
        asset.ip_address = new_ip
    if "asset_type" in payload:
        asset.asset_type = validate_string(payload.get("asset_type"), "asset_type", 60)
    if "operating_system" in payload:
        asset.operating_system = validate_string(
            payload.get("operating_system"), "operating_system", 80, required=False
        )
    if "location" in payload:
        asset.location = validate_string(payload.get("location"), "location", 80, required=False)
    if "owner" in payload:
        asset.owner = validate_string(payload.get("owner"), "owner", 120, required=False)
    if "criticality" in payload:
        asset.criticality = validate_choice(payload.get("criticality"), SEVERITIES, "criticality")
    if "status" in payload:
        asset.status = validate_choice(payload.get("status"), ASSET_STATUSES, "status")
    if "risk_level" in payload:
        asset.risk_level = validate_choice(payload.get("risk_level"), SEVERITIES, "risk_level")

    audit(
        "ASSET_UPDATED",
        f"Asset '{asset.name}' ({asset.ip_address}) updated.",
        entity_type="Asset",
        entity_id=asset.id,
        user=current_user(),
    )
    db.session.commit()
    return success(asset.to_dict(), message=f"Asset '{asset.name}' updated.")


@bp.delete("/<int:asset_id>")
@token_required
def delete_asset(asset_id: int):
    """DELETE /api/assets/<id> - retire an asset (its events are kept)."""
    asset = _get_asset(asset_id)
    name = asset.name
    SecurityEvent.query.filter(SecurityEvent.asset_id == asset.id).update(
        {"asset_id": None}, synchronize_session=False
    )
    db.session.delete(asset)
    audit(
        "ASSET_DELETED",
        f"Asset '{name}' removed from monitoring.",
        entity_type="Asset",
        entity_id=asset_id,
        user=current_user(),
    )
    db.session.commit()
    return success(message=f"Asset '{name}' deleted.")
