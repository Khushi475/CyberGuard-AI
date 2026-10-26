"""Service layer.

Routes stay thin: they validate input and shape responses, while every business
rule (detection pipeline, lifecycle transitions, aggregation, reporting, audit)
lives in this package.  That separation is what the Package Diagram documents.
"""
from . import (alert_service, analytics_service, audit_service, auth_service,
               detection_service, incident_service, report_service)

__all__ = [
    "alert_service",
    "analytics_service",
    "audit_service",
    "auth_service",
    "detection_service",
    "incident_service",
    "report_service",
]
