"""Audit trail service (FR-12).

Every state-changing operation calls :func:`record` so the Settings page and the
``/api/audit-logs`` endpoint can show who did what and when.
"""
from flask import has_request_context, request

from ..extensions import db
from ..models import AuditLog
from ..utils.logger import get_logger

logger = get_logger("cyberguard.audit")


def record(action: str, description: str = "", entity_type: str | None = None,
           entity_id: int | None = None, user=None, status: str = "SUCCESS",
           commit: bool = False) -> AuditLog:
    """Append one entry to the audit trail.

    ``commit=False`` is the default because callers normally commit the audit row
    together with the business change, keeping the two atomic.
    """
    ip_address = None
    if has_request_context():
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

    entry = AuditLog(
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        ip_address=ip_address,
        user_id=getattr(user, "id", None),
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    logger.info("AUDIT %s %s#%s by %s - %s", action, entity_type, entity_id,
                getattr(user, "email", "system"), description)
    return entry


def recent(limit: int = 50, user_id: int | None = None, action: str | None = None):
    query = AuditLog.query
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).all()
