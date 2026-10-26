"""Security report generation and export (FR-11).

A report is first stored as structured JSON in the ``reports`` table, then the
same content can be exported as JSON, CSV or PDF.  PDF export uses ReportLab when
it is installed; if it is not, the API returns a clear message and the CSV/JSON
routes still work.
"""
import csv
import io
from datetime import datetime, timedelta

from ..extensions import db
from ..models import Alert, Asset, Incident, Report, SecurityEvent, Threat
from ..utils.errors import ValidationError
from . import analytics_service as analytics
from .audit_service import record as audit
from .detection_service import next_code

REPORT_TYPES = ("SUMMARY", "THREAT", "INCIDENT", "COMPLIANCE")


def _recommendations(content: dict) -> list:
    """Derive concrete, defensive recommendations from the measured figures."""
    recommendations = []
    severity = {row["severity"]: row["count"] for row in content["severity_breakdown"]}
    categories = {row["category"]: row["count"] for row in content["threat_categories"]}
    stats = content["detection_statistics"]
    incidents = content["incident_statistics"]

    if severity.get("CRITICAL", 0) > 0:
        recommendations.append(
            f"{severity['CRITICAL']} critical detection(s) were recorded in this period. "
            "Review each one against the asset owner's change calendar and confirm containment."
        )
    if categories.get("Brute Force Attempt", 0) > 0:
        recommendations.append(
            "Brute-force patterns were observed. Enforce account lockout thresholds and "
            "multi-factor authentication on externally reachable services."
        )
    if categories.get("Port Scanning Pattern", 0) > 0:
        recommendations.append(
            "Scanning behaviour was detected. Re-verify the perimeter firewall rule set and "
            "close any service that does not need external exposure."
        )
    if categories.get("Data Transfer Anomaly", 0) > 0:
        recommendations.append(
            "Unusually large transfers were seen. Confirm whether scheduled backups explain "
            "them and apply egress limits where they do not."
        )
    if categories.get("Denial-of-Service Pattern", 0) > 0:
        recommendations.append(
            "Volumetric traffic was recorded. Validate rate-limiting and upstream filtering "
            "for the affected services."
        )
    if incidents["open"] > 0:
        recommendations.append(
            f"{incidents['open']} incident(s) remain open. Assign an owner to each so the "
            "lifecycle can progress to CONTAINED or RESOLVED."
        )
    if stats["false_positive_alerts"] > stats["resolved_alerts"] and stats["triaged_alerts"] >= 5:
        recommendations.append(
            "False positives currently outnumber confirmed findings. Lower the detection "
            "sensitivity on the Settings page and re-baseline the affected assets."
        )
    if not recommendations:
        recommendations.append(
            "No elevated activity was recorded in this reporting period. Continue routine "
            "monitoring and keep the detection baseline under review."
        )
    recommendations.append(
        "This report is produced by an academic prototype using simulated telemetry; it is "
        "not a substitute for a production security assessment."
    )
    return recommendations


def build_report_content(days: int = 30, report_type: str = "SUMMARY") -> dict:
    now = datetime.utcnow()
    since = now - timedelta(days=days)

    events_in_period = SecurityEvent.query.filter(SecurityEvent.timestamp >= since).count()
    threats_in_period = Threat.query.filter(Threat.detected_at >= since).count()
    alerts_in_period = Alert.query.filter(Alert.created_at >= since).count()
    incidents_in_period = Incident.query.filter(Incident.detected_at >= since).count()

    severity_rows = analytics.severity_distribution()
    category_rows = analytics.category_distribution(12)
    quality = analytics.detection_quality()

    resolved_alerts = Alert.query.filter(Alert.status == "RESOLVED").count()
    false_positive_alerts = Alert.query.filter(Alert.status == "FALSE_POSITIVE").count()
    open_alerts = Alert.query.filter(
        Alert.status.in_(("NEW", "ACKNOWLEDGED", "INVESTIGATING"))
    ).count()

    incident_open = Incident.query.filter(
        Incident.status.in_(("NEW", "OPEN", "INVESTIGATING", "CONTAINED"))
    ).count()
    incident_resolved = Incident.query.filter(Incident.status == "RESOLVED").count()
    incident_false_positive = Incident.query.filter(
        Incident.status == "FALSE_POSITIVE"
    ).count()

    top_sources = analytics.events_by_source(10)
    risky_assets = (
        Asset.query.filter(Asset.risk_level.in_(("HIGH", "CRITICAL")))
        .order_by(Asset.risk_score.desc())
        .limit(10)
        .all()
    )

    content = {
        "title": f"CyberGuard AI {report_type.title()} Security Report",
        "report_type": report_type,
        "generated_at": now.isoformat(timespec="seconds"),
        "period": {
            "days": days,
            "start": since.isoformat(timespec="seconds"),
            "end": now.isoformat(timespec="seconds"),
        },
        "summary": {
            "total_events": events_in_period,
            "threats_detected": threats_in_period,
            "alerts_raised": alerts_in_period,
            "incidents_opened": incidents_in_period,
            "events_all_time": SecurityEvent.query.count(),
            "monitored_assets": Asset.query.count(),
        },
        "severity_breakdown": severity_rows,
        "threat_categories": category_rows,
        "detection_statistics": {
            "accuracy": quality.get("accuracy"),
            "accuracy_label": quality.get("label"),
            "accuracy_note": quality.get("note"),
            "triaged_alerts": quality.get("triaged_alerts", 0),
            "resolved_alerts": resolved_alerts,
            "false_positive_alerts": false_positive_alerts,
            "open_alerts": open_alerts,
            "engine_mode": analytics.system_health()["checks"][1]["detail"],
        },
        "incident_statistics": {
            "open": incident_open,
            "resolved": incident_resolved,
            "false_positive": incident_false_positive,
            "mean_time_to_resolve_hours": analytics.analytics_overview(days).get(
                "mean_time_to_resolve_hours"
            ),
        },
        "top_sources": top_sources,
        "at_risk_assets": [
            {
                "name": asset.name,
                "ip_address": asset.ip_address,
                "risk_level": asset.risk_level,
                "risk_score": asset.risk_score,
            }
            for asset in risky_assets
        ],
        "threat_level": analytics.threat_level(),
    }
    content["recommendations"] = _recommendations(content)
    return content


def generate_report(days: int = 30, report_type: str = "SUMMARY", title: str | None = None,
                    user=None) -> Report:
    report_type = (report_type or "SUMMARY").upper()
    if report_type not in REPORT_TYPES:
        raise ValidationError(
            f"report_type must be one of: {', '.join(REPORT_TYPES)}.",
            details={"field": "report_type", "allowed": list(REPORT_TYPES)},
        )
    try:
        days = int(days)
    except (TypeError, ValueError) as exc:
        raise ValidationError("days must be an integer.", details={"field": "days"}) from exc
    if not 1 <= days <= 365:
        raise ValidationError(
            "days must be between 1 and 365.", details={"field": "days"}
        )

    content = build_report_content(days=days, report_type=report_type)
    if title:
        content["title"] = title

    report = Report(
        report_code=next_code("RPT", Report, Report.id),
        title=content["title"],
        report_type=report_type,
        period_days=days,
        period_start=datetime.fromisoformat(content["period"]["start"]),
        period_end=datetime.fromisoformat(content["period"]["end"]),
        total_events=content["summary"]["total_events"],
        total_threats=content["summary"]["threats_detected"],
        total_alerts=content["summary"]["alerts_raised"],
        total_incidents=content["summary"]["incidents_opened"],
        generated_by=getattr(user, "id", None),
    )
    report.content = content
    db.session.add(report)
    db.session.flush()

    audit(
        "REPORT_GENERATED",
        f"Report {report.report_code} generated covering the last {days} day(s).",
        entity_type="Report",
        entity_id=report.id,
        user=user,
    )
    db.session.commit()
    return report


def to_csv(report: Report) -> str:
    """Flatten a report into a single downloadable CSV."""
    content = report.content
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    writer.writerow(["CyberGuard AI Security Report"])
    writer.writerow(["Report code", report.report_code])
    writer.writerow(["Title", content.get("title", report.title)])
    writer.writerow(["Generated at", content.get("generated_at")])
    writer.writerow(["Period (days)", content.get("period", {}).get("days")])
    writer.writerow([])

    writer.writerow(["Section", "Metric", "Value"])
    for key, value in content.get("summary", {}).items():
        writer.writerow(["Summary", key.replace("_", " ").title(), value])
    for row in content.get("severity_breakdown", []):
        writer.writerow(["Severity breakdown", row["severity"], row["count"]])
    for row in content.get("threat_categories", []):
        writer.writerow(["Threat categories", row["category"], row["count"]])
    for key, value in content.get("detection_statistics", {}).items():
        writer.writerow(["Detection statistics", key.replace("_", " ").title(), value])
    for key, value in content.get("incident_statistics", {}).items():
        writer.writerow(["Incident statistics", key.replace("_", " ").title(), value])
    for row in content.get("top_sources", []):
        writer.writerow(["Top sources", row["source_ip"], row["count"]])
    for row in content.get("at_risk_assets", []):
        writer.writerow(
            ["At-risk assets", f"{row['name']} ({row['ip_address']})",
             f"{row['risk_level']} / {row['risk_score']}"]
        )
    writer.writerow([])
    writer.writerow(["Recommendations"])
    for index, recommendation in enumerate(content.get("recommendations", []), start=1):
        writer.writerow([index, recommendation])

    return buffer.getvalue()


def to_pdf(report: Report) -> bytes:
    """Render the report as a PDF. Raises ImportError if ReportLab is missing."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)

    content = report.content
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title=report.title, author="CyberGuard AI",
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CGTitle", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#0f172a")
    )
    heading = ParagraphStyle(
        "CGHeading", parent=styles["Heading2"], fontSize=13,
        textColor=colors.HexColor("#0369a1"), spaceBefore=10, spaceAfter=6,
    )
    body = styles["BodyText"]

    story = [
        Paragraph(content.get("title", report.title), title_style),
        Paragraph(
            f"Report code <b>{report.report_code}</b> &nbsp;|&nbsp; generated "
            f"{content.get('generated_at')} &nbsp;|&nbsp; period: last "
            f"{content.get('period', {}).get('days')} day(s)",
            body,
        ),
        Paragraph(
            "<i>Academic prototype - generated from simulated security telemetry.</i>", body
        ),
        Spacer(1, 8),
    ]

    def make_table(rows, col_widths=None):
        table = Table(rows, colWidths=col_widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#f1f5f9")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    threat = content.get("threat_level", {})
    story.append(Paragraph("1. Executive summary", heading))
    story.append(
        Paragraph(
            f"The current posture is <b>{threat.get('level', 'LOW')}</b> "
            f"({threat.get('basis', '')})",
            body,
        )
    )
    summary_rows = [["Metric", "Value"]] + [
        [key.replace("_", " ").title(), str(value)]
        for key, value in content.get("summary", {}).items()
    ]
    story.append(Spacer(1, 6))
    story.append(make_table(summary_rows, [90 * mm, 70 * mm]))

    story.append(Paragraph("2. Severity breakdown", heading))
    story.append(
        make_table(
            [["Severity", "Detections"]]
            + [[row["severity"], str(row["count"])] for row in content.get("severity_breakdown", [])],
            [90 * mm, 70 * mm],
        )
    )

    story.append(Paragraph("3. Threat categories", heading))
    category_rows = content.get("threat_categories", []) or [{"category": "None", "count": 0}]
    story.append(
        make_table(
            [["Category", "Count"]] + [[row["category"], str(row["count"])] for row in category_rows],
            [110 * mm, 50 * mm],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("4. Detection statistics", heading))
    story.append(
        make_table(
            [["Metric", "Value"]]
            + [[key.replace("_", " ").title(), str(value)]
               for key, value in content.get("detection_statistics", {}).items()],
            [70 * mm, 90 * mm],
        )
    )

    story.append(Paragraph("5. Incident statistics", heading))
    story.append(
        make_table(
            [["Metric", "Value"]]
            + [[key.replace("_", " ").title(), str(value)]
               for key, value in content.get("incident_statistics", {}).items()],
            [90 * mm, 70 * mm],
        )
    )

    top_sources = content.get("top_sources", [])
    if top_sources:
        story.append(Paragraph("6. Most active sources", heading))
        story.append(
            make_table(
                [["Source IP", "Events"]]
                + [[row["source_ip"], str(row["count"])] for row in top_sources],
                [90 * mm, 70 * mm],
            )
        )

    story.append(Paragraph("7. Recommendations", heading))
    for index, recommendation in enumerate(content.get("recommendations", []), start=1):
        story.append(Paragraph(f"{index}. {recommendation}", body))
        story.append(Spacer(1, 3))

    doc.build(story)
    return buffer.getvalue()
