"""Report entity: a generated security summary document."""
import json

from ..extensions import db
from .base import SerializerMixin, iso, utcnow

REPORT_TYPES = ("SUMMARY", "THREAT", "INCIDENT", "COMPLIANCE")


class Report(db.Model, SerializerMixin):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    report_code = db.Column(db.String(24), unique=True, nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    report_type = db.Column(db.String(30), nullable=False, default="SUMMARY", index=True)
    period_days = db.Column(db.Integer, nullable=False, default=30)
    period_start = db.Column(db.DateTime, nullable=True)
    period_end = db.Column(db.DateTime, nullable=True)

    total_events = db.Column(db.Integer, nullable=False, default=0)
    total_threats = db.Column(db.Integer, nullable=False, default=0)
    total_alerts = db.Column(db.Integer, nullable=False, default=0)
    total_incidents = db.Column(db.Integer, nullable=False, default=0)

    content_json = db.Column(db.Text, nullable=False, default="{}")
    generated_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author = db.relationship("User", back_populates="reports")

    @property
    def content(self) -> dict:
        try:
            return json.loads(self.content_json or "{}")
        except (ValueError, TypeError):
            return {}

    @content.setter
    def content(self, value) -> None:
        self.content_json = json.dumps(value or {}, default=str)

    def to_dict(self, include_content: bool = False) -> dict:
        data = {
            "id": self.id,
            "report_code": self.report_code,
            "title": self.title,
            "report_type": self.report_type,
            "period_days": self.period_days,
            "period_start": iso(self.period_start),
            "period_end": iso(self.period_end),
            "total_events": self.total_events,
            "total_threats": self.total_threats,
            "total_alerts": self.total_alerts,
            "total_incidents": self.total_incidents,
            "generated_at": iso(self.generated_at),
            "generated_by": self.author.full_name if self.author else "System",
        }
        if include_content:
            data["content"] = self.content
        return data
