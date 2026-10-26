"""Typed API exceptions.

Every route raises one of these instead of returning ad-hoc dictionaries, so a
single error handler in the application factory can produce a consistent JSON
envelope and the correct HTTP status code.
"""


class ApiError(Exception):
    """Base class for all handled API failures."""

    status_code = 400
    error_code = "BAD_REQUEST"

    def __init__(self, message: str, status_code: int | None = None,
                 error_code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {
            "success": False,
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ValidationError(ApiError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class AuthError(ApiError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(ApiError):
    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(ApiError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(ApiError):
    status_code = 409
    error_code = "CONFLICT"


class DatabaseError(ApiError):
    status_code = 500
    error_code = "DATABASE_ERROR"
