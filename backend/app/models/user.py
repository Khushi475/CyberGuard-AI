"""User entity: analysts and administrators of the platform."""
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from .base import SerializerMixin, iso, utcnow

ROLES = ("ADMIN", "ANALYST", "VIEWER")


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="ANALYST")
    department = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    # Preferences edited from the Settings page.
    notify_email = db.Column(db.Boolean, nullable=False, default=True)
    notify_critical_only = db.Column(db.Boolean, nullable=False, default=False)
    detection_sensitivity = db.Column(db.Float, nullable=False, default=1.0)
    theme = db.Column(db.String(20), nullable=False, default="dark")

    incidents = db.relationship(
        "Incident", back_populates="analyst", foreign_keys="Incident.assigned_to"
    )
    audit_logs = db.relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="author")

    def set_password(self, raw_password: str) -> None:
        """Store only a salted PBKDF2 hash - never the plaintext password."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password or "")

    def to_dict(self, include_preferences: bool = False) -> dict:
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "department": self.department,
            "is_active": self.is_active,
            "last_login": iso(self.last_login),
            "created_at": iso(self.created_at),
        }
        if include_preferences:
            data["preferences"] = {
                "notify_email": self.notify_email,
                "notify_critical_only": self.notify_critical_only,
                "detection_sensitivity": self.detection_sensitivity,
                "theme": self.theme,
            }
        return data
