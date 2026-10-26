"""SecurityEvent entity: one observed network / authentication record.

This is the central fact table of the system - every detection, threat and alert
ultimately references a security event.
"""
from ..extensions import db
from .base import SerializerMixin, iso, utcnow


class SecurityEvent(db.Model, SerializerMixin):
    __tablename__ = "security_events"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    source_ip = db.Column(db.String(45), nullable=False, index=True)
    destination_ip = db.Column(db.String(45), nullable=True)
    source_port = db.Column(db.Integer, nullable=True)
    destination_port = db.Column(db.Integer, nullable=True, index=True)
    protocol = db.Column(db.String(10), nullable=False, default="TCP")
    event_type = db.Column(db.String(40), nullable=False, default="network_traffic", index=True)

    request_count = db.Column(db.Integer, nullable=False, default=0)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    packet_count = db.Column(db.Integer, nullable=False, default=0)
    bytes_transferred = db.Column(db.Float, nullable=False, default=0.0)
    connection_duration = db.Column(db.Float, nullable=False, default=0.0)

    user_agent = db.Column(db.String(255), nullable=True)
    raw_log = db.Column(db.Text, nullable=True)
    source_channel = db.Column(db.String(30), nullable=False, default="manual")  # manual|csv|seed

    processed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=True, index=True)
    asset = db.relationship("Asset", back_populates="events")

    detection_result = db.relationship(
        "DetectionResult",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )
    threats = db.relationship("Threat", back_populates="event", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", back_populates="event", cascade="all, delete-orphan")

    def feature_payload(self) -> dict:
        """Dictionary consumed by the detection engine."""
        return {
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "event_type": self.event_type,
            "request_count": self.request_count,
            "failed_login_attempts": self.failed_login_attempts,
            "packet_count": self.packet_count,
            "bytes_transferred": self.bytes_transferred,
            "connection_duration": self.connection_duration,
            "timestamp": self.timestamp,
        }

    def to_dict(self, include_detection: bool = False) -> dict:
        data = {
            "id": self.id,
            "timestamp": iso(self.timestamp),
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "event_type": self.event_type,
            "request_count": self.request_count,
            "failed_login_attempts": self.failed_login_attempts,
            "packet_count": self.packet_count,
            "bytes_transferred": self.bytes_transferred,
            "connection_duration": self.connection_duration,
            "user_agent": self.user_agent,
            "source_channel": self.source_channel,
            "processed": self.processed,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else None,
            "created_at": iso(self.created_at),
        }
        if include_detection:
            data["detection"] = (
                self.detection_result.to_dict() if self.detection_result else None
            )
        return data
