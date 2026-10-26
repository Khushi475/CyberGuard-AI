"""Alert entity: the analyst-facing notification raised for a threat."""
import json

from ..extensions import db
from .base import SerializerMixin, iso, utcnow

ALERT_STATUS_TRANSITIONS = {
    "NEW": {"ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"},
    "ACKNOWLEDGED": {"INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"},
    "INVESTIGATING": {"RESOLVED", "FALSE_POSITIVE", "ACKNOWLEDGED"},
    "RESOLVED": {"INVESTIGATING"},
    "FALSE_POSITIVE": {"INVESTIGATING"},
}


class Alert(db.Model, SerializerMixin):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    alert_code = db.Column(db.String(24), unique=True, nullable=False, index=True)

    event_id = db.Column(db.Integer, db.ForeignKey("security_events.id"), nullable=True, index=True)
    threat_id = db.Column(db.Integer, db.ForeignKey("threats.id"), nullable=True, index=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=True, index=True)

    title = db.Column(db.String(160), nullable=False)
    threat_type = db.Column(db.String(60), nullable=False, index=True)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    destination_ip = db.Column(db.String(45), nullable=True)
    severity = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    risk_score = db.Column(db.Integer, nullable=False, default=0)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default="NEW", index=True)

    description = db.Column(db.Text, nullable=True)
    reasons_json = db.Column(db.Text, nullable=False, default="[]")
    recommended_action = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    event = db.relationship("SecurityEvent", back_populates="alerts")
    threat = db.relationship("Threat", back_populates="alerts")
    incident = db.relationship("Incident", back_populates="alerts")

    @property
    def reasons(self) -> list:
        try:
            return json.loads(self.reasons_json or "[]")
        except (ValueError, TypeError):
            return []

    @reasons.setter
    def reasons(self, values) -> None:
        self.reasons_json = json.dumps(list(values or []))

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        if current == target:
            return True
        return target in ALERT_STATUS_TRANSITIONS.get(current, set())

    def to_dict(self, include_event: bool = False) -> dict:
        data = {
            "id": self.id,
            "alert_code": self.alert_code,
            "title": self.title,
            "threat_type": self.threat_type,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "confidence": round(self.confidence, 3),
            "status": self.status,
            "description": self.description,
            "reasons": self.reasons,
            "recommended_action": self.recommended_action,
            "notes": self.notes,
            "event_id": self.event_id,
            "threat_id": self.threat_id,
            "incident_id": self.incident_id,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "resolved_at": iso(self.resolved_at),
        }
        if include_event:
            data["event"] = self.event.to_dict(include_detection=True) if self.event else None
            data["incident"] = self.incident.to_dict() if self.incident else None
        return data
