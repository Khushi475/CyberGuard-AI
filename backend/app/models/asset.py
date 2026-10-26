"""Asset entity: the monitored hosts, servers and network devices."""
from ..extensions import db
from .base import SerializerMixin, iso, utcnow

ASSET_TYPES = (
    "Web Server",
    "Database Server",
    "Application Server",
    "Network Gateway",
    "Workstation",
    "Laptop",
    "Firewall",
    "Domain Controller",
    "Mail Server",
    "IoT Device",
)


class Asset(db.Model, SerializerMixin):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    asset_type = db.Column(db.String(60), nullable=False, default="Workstation")
    operating_system = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(80), nullable=True)
    owner = db.Column(db.String(120), nullable=True)
    criticality = db.Column(db.String(20), nullable=False, default="MEDIUM")
    status = db.Column(db.String(20), nullable=False, default="ONLINE")
    risk_level = db.Column(db.String(20), nullable=False, default="LOW")
    risk_score = db.Column(db.Integer, nullable=False, default=0)
    last_seen = db.Column(db.DateTime, nullable=True, default=utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    events = db.relationship("SecurityEvent", back_populates="asset")

    def to_dict(self, include_counts: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "ip_address": self.ip_address,
            "asset_type": self.asset_type,
            "operating_system": self.operating_system,
            "location": self.location,
            "owner": self.owner,
            "criticality": self.criticality,
            "status": self.status,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "last_seen": iso(self.last_seen),
            "created_at": iso(self.created_at),
        }
        if include_counts:
            data["event_count"] = len(self.events)
        return data
