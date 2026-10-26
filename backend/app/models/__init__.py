"""SQLAlchemy ORM models for CyberGuard AI.

The ten entities below are the physical realisation of the Entity Relationship
Diagram in ``documentation/04_ER_Diagram.md``.  Every relationship documented
there exists here as a real foreign key.
"""
from .user import User
from .asset import Asset
from .security_event import SecurityEvent
from .detection_result import DetectionResult
from .threat import Threat
from .alert import Alert
from .incident import Incident
from .threat_indicator import ThreatIndicator
from .report import Report
from .audit_log import AuditLog

__all__ = [
    "User",
    "Asset",
    "SecurityEvent",
    "DetectionResult",
    "Threat",
    "Alert",
    "Incident",
    "ThreatIndicator",
    "Report",
    "AuditLog",
]
