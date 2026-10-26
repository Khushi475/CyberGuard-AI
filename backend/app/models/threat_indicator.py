"""ThreatIndicator entity: simulated defensive threat-intelligence records.

IMPORTANT: every indicator stored by this project is synthetic.  IP addresses come
from RFC 5737 / RFC 1918 documentation ranges and domains use the reserved
``.invalid`` and ``example`` namespaces, so nothing here points at real
infrastructure.
"""
from ..extensions import db
from .base import SerializerMixin, iso, utcnow

INDICATOR_TYPES = (
    "Suspicious IP",
    "Suspicious Domain",
    "Suspicious User Activity",
    "Anomalous Network Activity",
)


class ThreatIndicator(db.Model, SerializerMixin):
    __tablename__ = "threat_indicators"

    id = db.Column(db.Integer, primary_key=True)
    indicator = db.Column(db.String(180), nullable=False, index=True)
    indicator_type = db.Column(db.String(60), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=True)
    risk_level = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    confidence = db.Column(db.Float, nullable=False, default=0.5)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    description = db.Column(db.Text, nullable=True)
    source_feed = db.Column(db.String(80), nullable=False, default="CyberGuard Simulated Feed")
    hit_count = db.Column(db.Integer, nullable=False, default=0)
    is_simulated = db.Column(db.Boolean, nullable=False, default=True)

    first_seen = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_seen = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "indicator": self.indicator,
            "indicator_type": self.indicator_type,
            "category": self.category,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 2),
            "status": self.status,
            "description": self.description,
            "source_feed": self.source_feed,
            "hit_count": self.hit_count,
            "is_simulated": self.is_simulated,
            "first_seen": iso(self.first_seen),
            "last_seen": iso(self.last_seen),
        }
