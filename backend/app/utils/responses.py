"""Uniform JSON response envelopes used by every blueprint."""
from flask import jsonify


def success(data=None, message: str = "OK", status_code: int = 200, **extra):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload), status_code


def error_response(message: str, status_code: int = 400,
                   error_code: str = "BAD_REQUEST", details: dict | None = None):
    payload = {"success": False, "error": error_code, "message": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


def paginated(items, total: int, page: int, per_page: int, message: str = "OK", **extra):
    pages = (total + per_page - 1) // per_page if per_page else 0
    payload = {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }
    payload.update(extra)
    return jsonify(payload), 200
