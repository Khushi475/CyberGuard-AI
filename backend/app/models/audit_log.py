"""AuditLog entity: an append-only trail of every state-changing action (FR-12)."""
from ..extensions import db
from .base import SerializerMixin, iso, utcnow


class AuditLog(db.Model, SerializerMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(60), nullable=False, index=True)
    entity_type = db.Column(db.String(40), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="SUCCESS")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    user = db.relationship("User", back_populates="audit_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "ip_address": self.ip_address,
            "status": self.status,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else "System",
            "created_at": iso(self.created_at),
        }
