"""Dashboard and analytics endpoints."""
from flask import Blueprint, request

from ..services import analytics_service
from ..utils.responses import success
from ..utils.security import token_required

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _days(default: int, maximum: int = 365) -> int:
    try:
        days = int(request.args.get("days", default))
    except (TypeError, ValueError):
        days = default
    return max(1, min(days, maximum))


@bp.get("/stats")
@token_required
def stats():
    """GET /api/dashboard/stats - every figure and chart series the dashboard needs."""
    return success(analytics_service.dashboard_stats(days=_days(14, 90)))


@bp.get("/activity")
@token_required
def activity():
    """GET /api/dashboard/activity - the live-looking activity feed."""
    try:
        limit = int(request.args.get("limit", 15))
    except (TypeError, ValueError):
        limit = 15
    return success(analytics_service.activity_feed(max(1, min(limit, 50))))


@bp.get("/threat-level")
@token_required
def threat_level():
    """GET /api/dashboard/threat-level - the LOW/MEDIUM/HIGH/CRITICAL posture."""
    return success(analytics_service.threat_level())


@analytics_bp.get("")
@token_required
def analytics_overview():
    """GET /api/analytics - the deeper analytics payload used by Reports/Settings."""
    return success(analytics_service.analytics_overview(days=_days(30)))
