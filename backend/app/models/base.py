"""Shared model helpers."""
from datetime import datetime


def utcnow() -> datetime:
    """Naive UTC timestamp - SQLite stores no timezone information."""
    return datetime.utcnow()


def iso(value) -> str | None:
    """Serialise a datetime to ISO-8601, tolerating ``None``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


class SerializerMixin:
    """Gives every model a predictable ``to_dict`` contract."""

    def to_dict(self) -> dict:  # pragma: no cover - overridden by each model
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"
