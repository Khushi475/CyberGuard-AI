"""Report endpoints: /api/reports/*"""
import json

from flask import Blueprint, Response, request

from ..extensions import db
from ..models import Report
from ..services import report_service
from ..services.audit_service import record as audit
from ..utils.errors import NotFoundError
from ..utils.responses import paginated, success
from ..utils.security import current_user, token_required
from ..utils.validators import parse_pagination, require_dict

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _get_report(report_id: int) -> Report:
    report = Report.query.get(report_id)
    if report is None:
        raise NotFoundError(f"Report #{report_id} was not found.")
    return report


@bp.get("")
@token_required
def list_reports():
    """GET /api/reports - previously generated reports, newest first."""
    page, per_page = parse_pagination(request.args, default_per_page=20)
    query = Report.query.order_by(Report.generated_at.desc(), Report.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated([report.to_dict() for report in rows], total, page, per_page)


@bp.get("/preview")
@token_required
def preview():
    """GET /api/reports/preview - build report content without storing it."""
    try:
        days = int(request.args.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 365))
    report_type = (request.args.get("report_type") or "SUMMARY").upper()
    return success(report_service.build_report_content(days=days, report_type=report_type))


@bp.get("/<int:report_id>")
@token_required
def get_report(report_id: int):
    """GET /api/reports/<id> - a stored report including its full content."""
    return success(_get_report(report_id).to_dict(include_content=True))


@bp.post("/generate")
@token_required
def generate():
    """POST /api/reports/generate - build and store a new security report."""
    payload = require_dict(request.get_json(silent=True) or {})
    report = report_service.generate_report(
        days=payload.get("days", 30),
        report_type=payload.get("report_type", "SUMMARY"),
        title=payload.get("title"),
        user=current_user(),
    )
    return success(
        report.to_dict(include_content=True),
        message=f"Report {report.report_code} generated.",
        status_code=201,
    )


@bp.get("/<int:report_id>/download")
@token_required
def download(report_id: int):
    """GET /api/reports/<id>/download?format=pdf|csv|json - export a report."""
    report = _get_report(report_id)
    fmt = (request.args.get("format") or "json").lower()
    base_name = f"{report.report_code}_cyberguard_report"

    audit(
        "REPORT_DOWNLOADED",
        f"Report {report.report_code} exported as {fmt.upper()}.",
        entity_type="Report",
        entity_id=report.id,
        user=current_user(),
        commit=True,
    )

    if fmt == "csv":
        return Response(
            report_service.to_csv(report),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.csv"'},
        )

    if fmt == "pdf":
        try:
            pdf_bytes = report_service.to_pdf(report)
        except ImportError:
            return success(
                {"available_formats": ["json", "csv"]},
                message="PDF export needs ReportLab. Install it with 'pip install reportlab', "
                        "or download the CSV/JSON version instead.",
                status_code=501,
            )
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.pdf"'},
        )

    return Response(
        json.dumps(report.to_dict(include_content=True), indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{base_name}.json"'},
    )


@bp.delete("/<int:report_id>")
@token_required
def delete_report(report_id: int):
    """DELETE /api/reports/<id> - remove a stored report."""
    report = _get_report(report_id)
    code = report.report_code
    db.session.delete(report)
    audit(
        "REPORT_DELETED",
        f"Report {code} deleted.",
        entity_type="Report",
        entity_id=report_id,
        user=current_user(),
    )
    db.session.commit()
    return success(message=f"Report {code} deleted.")
