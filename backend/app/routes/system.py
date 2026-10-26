"""System endpoints: health check, settings, audit log and API index."""
import json
from pathlib import Path

from flask import Blueprint, current_app, request

from ..extensions import db
from ..models import (Alert, Asset, AuditLog, DetectionResult, Incident, Report,
                      SecurityEvent, Threat, ThreatIndicator, User)
from ..services import analytics_service, audit_service, detection_service
from ..utils.responses import success
from ..utils.security import current_user, token_required

bp = Blueprint("system", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    """GET /api/health - public liveness probe (no token required)."""
    database_ok = True
    detail = "connected"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        database_ok = False
        detail = str(exc)

    engine = detection_service.get_engine().model_info()
    return success(
        {
            "status": "healthy" if database_ok else "degraded",
            "service": "CyberGuard AI API",
            "version": "1.0.0",
            "environment": current_app.config.get("ENV", "development"),
            "database": {"connected": database_ok, "detail": detail},
            "detection_engine": {
                "mode": engine["mode"],
                "ml_available": engine["ml_available"],
                "engine_version": engine["engine_version"],
                "baseline_source": engine["baseline_source"],
            },
        },
        message="CyberGuard AI API is running.",
    )


@bp.get("/system/status")
@token_required
def system_status():
    """GET /api/system/status - detailed status for the Settings page."""
    engine = detection_service.get_engine().model_info()
    metadata_path = Path(current_app.config["ML_MODEL_DIR"]) / "metadata.json"
    metadata = None
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except (ValueError, OSError):
            metadata = None

    return success(
        {
            "api": {
                "status": "OPERATIONAL",
                "version": "1.0.0",
                "environment": current_app.config.get("ENV", "development"),
                "cors_origins": current_app.config.get("CORS_ORIGINS", []),
                "endpoints": len([r for r in current_app.url_map.iter_rules()
                                  if str(r).startswith("/api")]),
            },
            "database": {
                "status": "OPERATIONAL",
                "engine": "SQLite via SQLAlchemy",
                "uri": current_app.config["SQLALCHEMY_DATABASE_URI"].split("///")[-1],
                "tables": {
                    "users": User.query.count(),
                    "assets": Asset.query.count(),
                    "security_events": SecurityEvent.query.count(),
                    "detection_results": DetectionResult.query.count(),
                    "threats": Threat.query.count(),
                    "alerts": Alert.query.count(),
                    "incidents": Incident.query.count(),
                    "threat_indicators": ThreatIndicator.query.count(),
                    "reports": Report.query.count(),
                    "audit_logs": AuditLog.query.count(),
                },
            },
            "detection_engine": engine,
            "model_metadata": metadata,
            "health": analytics_service.system_health(),
            "thresholds": {
                "alert_risk_threshold": current_app.config["ALERT_RISK_THRESHOLD"],
                "incident_risk_threshold": current_app.config["INCIDENT_RISK_THRESHOLD"],
                "severity_bands": {
                    "LOW": "0-25", "MEDIUM": "26-50", "HIGH": "51-75", "CRITICAL": "76-100"
                },
                "max_csv_rows": current_app.config["MAX_CSV_ROWS"],
                "max_upload_bytes": current_app.config["MAX_CONTENT_LENGTH"],
            },
        }
    )


@bp.post("/system/reload-model")
@token_required
def reload_model():
    """POST /api/system/reload-model - re-read ML artefacts from disk."""
    info = detection_service.get_engine().reload()
    audit_service.record(
        "MODEL_RELOADED",
        f"Detection engine reloaded in {info['mode']} mode.",
        entity_type="System",
        user=current_user(),
        commit=True,
    )
    return success(info, message=f"Detection engine reloaded ({info['mode']}).")


@bp.get("/audit-logs")
@token_required
def audit_logs():
    """GET /api/audit-logs - the audit trail (FR-12)."""
    try:
        limit = int(request.args.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100
    entries = audit_service.recent(
        limit=max(1, min(limit, 500)), action=request.args.get("action")
    )
    return success([entry.to_dict() for entry in entries])


@bp.get("")
def api_index():
    """GET /api - a machine-readable index of every available endpoint."""
    routes = []
    for rule in current_app.url_map.iter_rules():
        path = str(rule)
        if not path.startswith("/api"):
            continue
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        view = current_app.view_functions.get(rule.endpoint)
        summary = (view.__doc__ or "").strip().split("\n")[0] if view else ""
        routes.append({"path": path, "methods": methods, "summary": summary})
    routes.sort(key=lambda item: item["path"])
    return success(
        {
            "service": "CyberGuard AI API",
            "version": "1.0.0",
            "documentation": "documentation/API_Documentation.md",
            "endpoint_count": len(routes),
            "endpoints": routes,
        },
        message="CyberGuard AI REST API index.",
    )
