"""Security event endpoints: /api/events/*"""
from flask import Blueprint, current_app, request
from sqlalchemy import or_

from ..extensions import db
from ..models import SecurityEvent
from ..services import detection_service
from ..services.audit_service import record as audit
from ..utils.csv_parser import decode_file, parse_csv, validate_upload
from ..utils.errors import NotFoundError, ValidationError
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import parse_pagination, require_dict, validate_event_payload

bp = Blueprint("events", __name__, url_prefix="/api/events")


def _sensitivity_for(user):
    """Per-analyst sensitivity from Settings, falling back to the app default."""
    return getattr(user, "detection_sensitivity", None) or current_app.config.get(
        "DETECTION_SENSITIVITY", 1.0
    )


@bp.get("")
@token_required
def list_events():
    """GET /api/events - paginated event history with filters."""
    page, per_page = parse_pagination(request.args)
    query = SecurityEvent.query

    severity = request.args.get("severity")
    if severity and severity.upper() != "ALL":
        from ..models import DetectionResult

        query = query.join(DetectionResult).filter(
            DetectionResult.severity == severity.upper()
        )

    event_type = request.args.get("event_type")
    if event_type and event_type.lower() != "all":
        query = query.filter(SecurityEvent.event_type == event_type)

    protocol = request.args.get("protocol")
    if protocol and protocol.upper() != "ALL":
        query = query.filter(SecurityEvent.protocol == protocol.upper())

    channel = request.args.get("channel")
    if channel and channel.lower() != "all":
        query = query.filter(SecurityEvent.source_channel == channel)

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                SecurityEvent.source_ip.ilike(pattern),
                SecurityEvent.destination_ip.ilike(pattern),
                SecurityEvent.event_type.ilike(pattern),
            )
        )

    total = query.count()
    rows = (
        query.order_by(SecurityEvent.timestamp.desc(), SecurityEvent.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return paginated(
        [event.to_dict(include_detection=True) for event in rows], total, page, per_page
    )


@bp.get("/<int:event_id>")
@token_required
def get_event(event_id: int):
    """GET /api/events/<id> - one event with its detection result."""
    event = SecurityEvent.query.get(event_id)
    if event is None:
        raise NotFoundError(f"Security event #{event_id} was not found.")
    return success(event.to_dict(include_detection=True))


@bp.post("")
@token_required
def create_event():
    """POST /api/events - submit an event; it is analysed and stored immediately."""
    payload = require_dict(request.get_json(silent=True) or {})
    cleaned = validate_event_payload(payload)
    user = current_user()
    bundle = detection_service.persist_analysis(
        cleaned, user=user, channel="manual", sensitivity=_sensitivity_for(user)
    )
    audit(
        "EVENT_SUBMITTED",
        f"Security event #{bundle['event'].id} submitted from {cleaned['source_ip']}.",
        entity_type="SecurityEvent",
        entity_id=bundle["event"].id,
        user=user,
        commit=True,
    )
    return success(
        detection_service.analysis_to_response(bundle),
        message="Event stored and analysed.",
        status_code=201,
    )


@bp.post("/analyze")
@token_required
def analyze_event():
    """POST /api/events/analyze - the Threat Detection page entry point.

    ``?persist=false`` runs the engine without writing to the database, which is
    useful for experimenting during a demonstration.
    """
    payload = require_dict(request.get_json(silent=True) or {})
    cleaned = validate_event_payload(payload)
    user = current_user()
    sensitivity = payload.get("sensitivity") or _sensitivity_for(user)

    persist = str(request.args.get("persist", "true")).lower() not in ("false", "0", "no")
    if not persist:
        result = detection_service.analyze_only(cleaned, sensitivity=sensitivity)
        return success(
            {
                "persisted": False,
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
                "feature_summary": result["feature_summary"],
                "model_used": result["model_used"],
                "engine_version": result["engine_version"],
                "analysis_time_ms": result["analysis_time_ms"],
            },
            message="Analysis complete (dry run - nothing was stored).",
        )

    bundle = detection_service.persist_analysis(
        cleaned, user=user, channel="manual", sensitivity=sensitivity
    )
    response = detection_service.analysis_to_response(bundle)
    response["persisted"] = True
    audit(
        "EVENT_ANALYSED",
        f"Event #{bundle['event'].id} classified as {response['classification']} "
        f"(risk {response['risk_score']}).",
        entity_type="SecurityEvent",
        entity_id=bundle["event"].id,
        user=user,
        commit=True,
    )
    return success(response, message="Analysis complete.")


@bp.post("/upload")
@token_required
def upload_events():
    """POST /api/events/upload - CSV log ingestion for the Log Analyzer."""
    if "file" not in request.files:
        raise ValidationError(
            "No file part in the request. Send the CSV as multipart/form-data under 'file'.",
            details={"field": "file"},
        )
    file_storage = validate_upload(request.files["file"])
    text = decode_file(file_storage)
    rows, row_errors = parse_csv(text, max_rows=current_app.config["MAX_CSV_ROWS"])

    if not rows:
        raise ValidationError(
            "No valid rows could be read from the file. "
            f"{len(row_errors)} row(s) failed validation.",
            details={"field": "file", "row_errors": row_errors[:20]},
        )

    user = current_user()
    summary = detection_service.analyze_batch(
        rows, user=user, channel="csv", sensitivity=_sensitivity_for(user)
    )
    summary["filename"] = file_storage.filename
    summary["rejected_rows"] = len(row_errors)
    summary["row_errors"] = row_errors[:25]
    return success(summary, message=f"Analysed {summary['total_records']} records.", status_code=201)


@bp.delete("/<int:event_id>")
@token_required
def delete_event(event_id: int):
    """DELETE /api/events/<id> - remove an event and its detection artefacts."""
    event = SecurityEvent.query.get(event_id)
    if event is None:
        raise NotFoundError(f"Security event #{event_id} was not found.")
    db.session.delete(event)
    audit(
        "EVENT_DELETED",
        f"Security event #{event_id} deleted.",
        entity_type="SecurityEvent",
        entity_id=event_id,
        user=current_user(),
    )
    db.session.commit()
    return success(message=f"Security event #{event_id} deleted.")


@bp.get("/sample")
@token_required
def sample_events():
    """GET /api/events/sample - ready-made payloads for the Threat Detection page."""
    return success(
        [
            {
                "label": "Normal HTTPS browsing",
                "expected": "Normal Activity",
                "payload": {
                    "source_ip": "10.0.1.42",
                    "destination_ip": "10.0.3.10",
                    "source_port": 51520,
                    "destination_port": 443,
                    "protocol": "HTTPS",
                    "event_type": "web_request",
                    "request_count": 12,
                    "failed_login_attempts": 0,
                    "packet_count": 180,
                    "bytes_transferred": 210000,
                    "connection_duration": 45,
                },
            },
            {
                "label": "Repeated failed SSH logins",
                "expected": "Brute Force Attempt",
                "payload": {
                    "source_ip": "203.0.113.66",
                    "destination_ip": "10.0.1.20",
                    "source_port": 44122,
                    "destination_port": 22,
                    "protocol": "SSH",
                    "event_type": "authentication",
                    "request_count": 68,
                    "failed_login_attempts": 62,
                    "packet_count": 340,
                    "bytes_transferred": 41000,
                    "connection_duration": 95,
                },
            },
            {
                "label": "Rapid small connections across ports",
                "expected": "Port Scanning Pattern",
                "payload": {
                    "source_ip": "198.51.100.23",
                    "destination_ip": "10.0.2.15",
                    "source_port": 60211,
                    "destination_port": 41234,
                    "protocol": "TCP",
                    "event_type": "firewall",
                    "request_count": 420,
                    "failed_login_attempts": 0,
                    "packet_count": 480,
                    "bytes_transferred": 29000,
                    "connection_duration": 9,
                },
            },
            {
                "label": "Large off-hours outbound transfer",
                "expected": "Data Transfer Anomaly",
                "payload": {
                    "source_ip": "10.0.2.31",
                    "destination_ip": "192.0.2.90",
                    "source_port": 52110,
                    "destination_port": 443,
                    "protocol": "HTTPS",
                    "event_type": "file_access",
                    "request_count": 6,
                    "failed_login_attempts": 0,
                    "packet_count": 900000,
                    "bytes_transferred": 1288490188,
                    "connection_duration": 5400,
                    "timestamp": "2026-01-15T02:40:00",
                },
            },
            {
                "label": "High-volume request flood",
                "expected": "Denial-of-Service Pattern",
                "payload": {
                    "source_ip": "192.0.2.150",
                    "destination_ip": "10.0.3.10",
                    "source_port": 40233,
                    "destination_port": 80,
                    "protocol": "HTTP",
                    "event_type": "web_request",
                    "request_count": 48000,
                    "failed_login_attempts": 0,
                    "packet_count": 96000,
                    "bytes_transferred": 8600000,
                    "connection_duration": 42,
                },
            },
        ]
    )
