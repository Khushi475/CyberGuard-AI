"""DetectionResult entity: the explainable output of the detection engine."""
import json

from ..extensions import db
from .base import SerializerMixin, iso, utcnow


class DetectionResult(db.Model, SerializerMixin):
    __tablename__ = "detection_results"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("security_events.id"), nullable=False, unique=True, index=True
    )

    classification = db.Column(db.String(60), nullable=False, default="Normal Activity")
    risk_score = db.Column(db.Integer, nullable=False, default=0)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    severity = db.Column(db.String(20), nullable=False, default="LOW", index=True)
    is_threat = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # Individual scores kept separately so the viva can show how the hybrid
    # engine combines its three sub-detectors.
    rule_score = db.Column(db.Float, nullable=False, default=0.0)
    anomaly_score = db.Column(db.Float, nullable=False, default=0.0)
    ml_score = db.Column(db.Float, nullable=False, default=0.0)
    engine_version = db.Column(db.String(20), nullable=False, default="1.0")
    model_used = db.Column(db.String(40), nullable=False, default="hybrid-rules")

    reasons_json = db.Column(db.Text, nullable=False, default="[]")
    features_json = db.Column(db.Text, nullable=False, default="{}")
    recommended_action = db.Column(db.Text, nullable=True)
    analysis_time_ms = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    event = db.relationship("SecurityEvent", back_populates="detection_result")

    @property
    def reasons(self) -> list:
        try:
            return json.loads(self.reasons_json or "[]")
        except (ValueError, TypeError):
            return []

    @reasons.setter
    def reasons(self, values) -> None:
        self.reasons_json = json.dumps(list(values or []))

    @property
    def features(self) -> dict:
        try:
            return json.loads(self.features_json or "{}")
        except (ValueError, TypeError):
            return {}

    @features.setter
    def features(self, values) -> None:
        self.features_json = json.dumps(values or {}, default=str)

    def to_dict(self, include_features: bool = False) -> dict:
        data = {
            "id": self.id,
            "event_id": self.event_id,
            "classification": self.classification,
            "risk_score": self.risk_score,
            "confidence": round(self.confidence, 3),
            "severity": self.severity,
            "is_threat": self.is_threat,
            "reasons": self.reasons,
            "recommended_action": self.recommended_action,
            "scores": {
                "rule": round(self.rule_score, 2),
                "anomaly": round(self.anomaly_score, 2),
                "ml": round(self.ml_score, 2),
            },
            "model_used": self.model_used,
            "engine_version": self.engine_version,
            "analysis_time_ms": round(self.analysis_time_ms, 2),
            "created_at": iso(self.created_at),
        }
        if include_features:
            data["features"] = self.features
        return data
