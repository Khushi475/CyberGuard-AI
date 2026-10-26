"""Threat entity: a confirmed, classified malicious-looking finding."""
import json

from ..extensions import db
from .base import SerializerMixin, iso, utcnow

THREAT_CATEGORIES = (
    "Normal Activity",
    "Brute Force Attempt",
    "Port Scanning Pattern",
    "Suspicious Login Activity",
    "Network Anomaly",
    "Data Transfer Anomaly",
    "Denial-of-Service Pattern",
    "Credential Abuse Pattern",
)


class Threat(db.Model, SerializerMixin):
    __tablename__ = "threats"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("security_events.id"), nullable=False, index=True
    )

    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    risk_score = db.Column(db.Integer, nullable=False, default=0)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    destination_ip = db.Column(db.String(45), nullable=True)
    mitre_tactic = db.Column(db.String(60), nullable=True)
    indicators_json = db.Column(db.Text, nullable=False, default="[]")
    detected_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    event = db.relationship("SecurityEvent", back_populates="threats")
    alerts = db.relationship("Alert", back_populates="threat")

    @property
    def indicators(self) -> list:
        try:
            return json.loads(self.indicators_json or "[]")
        except (ValueError, TypeError):
            return []

    @indicators.setter
    def indicators(self, values) -> None:
        self.indicators_json = json.dumps(list(values or []))

    def to_dict(self, include_event: bool = False) -> dict:
        data = {
            "id": self.id,
            "event_id": self.event_id,
            "category": self.category,
            "description": self.description,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "confidence": round(self.confidence, 3),
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "mitre_tactic": self.mitre_tactic,
            "indicators": self.indicators,
            "detected_at": iso(self.detected_at),
            "alert_count": len(self.alerts),
        }
        if include_event and self.event is not None:
            data["event"] = self.event.to_dict(include_detection=True)
        return data
