"""Incident entity and its lifecycle state machine.

The transition table below is the executable version of the State Transition
Diagram in ``documentation/09_State_Transition_Diagram.md``.  The API refuses any
transition that is not listed here, so the diagram and the code cannot drift.
"""
import json

from ..extensions import db
from .base import SerializerMixin, iso, utcnow

INCIDENT_STATE_TRANSITIONS = {
    "NEW": {"OPEN", "INVESTIGATING", "FALSE_POSITIVE"},
    "OPEN": {"INVESTIGATING", "CONTAINED", "FALSE_POSITIVE"},
    "INVESTIGATING": {"CONTAINED", "RESOLVED", "FALSE_POSITIVE"},
    "CONTAINED": {"RESOLVED", "INVESTIGATING"},
    "RESOLVED": {"INVESTIGATING"},
    "FALSE_POSITIVE": {"INVESTIGATING"},
}

TERMINAL_STATES = {"RESOLVED", "FALSE_POSITIVE"}


class Incident(db.Model, SerializerMixin):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    incident_code = db.Column(db.String(24), unique=True, nullable=False, index=True)

    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=True)
    threat_type = db.Column(db.String(60), nullable=False, default="Network Anomaly", index=True)
    severity = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    priority = db.Column(db.String(20), nullable=False, default="P3")
    status = db.Column(db.String(20), nullable=False, default="NEW", index=True)

    risk_score = db.Column(db.Integer, nullable=False, default=0)
    source_ip = db.Column(db.String(45), nullable=True, index=True)

    detected_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    contained_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    resolution_summary = db.Column(db.Text, nullable=True)
    history_json = db.Column(db.Text, nullable=False, default="[]")

    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    analyst = db.relationship("User", back_populates="incidents", foreign_keys=[assigned_to])

    alerts = db.relationship("Alert", back_populates="incident")

    @property
    def history(self) -> list:
        try:
            return json.loads(self.history_json or "[]")
        except (ValueError, TypeError):
            return []

    @history.setter
    def history(self, values) -> None:
        self.history_json = json.dumps(list(values or []), default=str)

    def append_history(self, from_status, to_status, actor: str, note: str = "") -> None:
        entries = self.history
        entries.append(
            {
                "from": from_status,
                "to": to_status,
                "actor": actor,
                "note": note,
                "at": utcnow().isoformat(timespec="seconds"),
            }
        )
        self.history = entries

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        if current == target:
            return True
        return target in INCIDENT_STATE_TRANSITIONS.get(current, set())

    @staticmethod
    def allowed_transitions(current: str) -> list:
        return sorted(INCIDENT_STATE_TRANSITIONS.get(current, set()))

    def to_dict(self, include_alerts: bool = False) -> dict:
        data = {
            "id": self.id,
            "incident_code": self.incident_code,
            "title": self.title,
            "description": self.description,
            "threat_type": self.threat_type,
            "severity": self.severity,
            "priority": self.priority,
            "status": self.status,
            "risk_score": self.risk_score,
            "source_ip": self.source_ip,
            "assigned_to": self.assigned_to,
            "assigned_analyst": self.analyst.full_name if self.analyst else "Unassigned",
            "detected_at": iso(self.detected_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "contained_at": iso(self.contained_at),
            "resolved_at": iso(self.resolved_at),
            "resolution_summary": self.resolution_summary,
            "alert_count": len(self.alerts),
            "allowed_transitions": self.allowed_transitions(self.status),
        }
        if include_alerts:
            data["history"] = self.history
            data["alerts"] = [alert.to_dict() for alert in self.alerts]
        return data
