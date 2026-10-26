"""Authentication endpoints: /api/auth/*"""
from flask import Blueprint, request

from ..services import auth_service
from ..utils.responses import success
from ..utils.security import current_user, token_required
from ..utils.validators import require_dict

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    """POST /api/auth/login - exchange credentials for a signed session token."""
    payload = require_dict(request.get_json(silent=True) or {})
    result = auth_service.login(payload.get("email"), payload.get("password"))
    return success(result, message="Signed in successfully.")


@bp.post("/logout")
@token_required
def logout():
    """POST /api/auth/logout - record the sign-out in the audit trail."""
    auth_service.logout(current_user())
    return success(message="Signed out successfully.")


@bp.get("/me")
@token_required
def me():
    """GET /api/auth/me - the profile behind the supplied token."""
    return success(current_user().to_dict(include_preferences=True))


@bp.put("/profile")
@token_required
def update_profile():
    """PUT /api/auth/profile - update name, department or email."""
    payload = require_dict(request.get_json(silent=True) or {})
    user = auth_service.update_profile(current_user(), payload)
    return success(user.to_dict(include_preferences=True), message="Profile updated.")


@bp.put("/preferences")
@token_required
def update_preferences():
    """PUT /api/auth/preferences - notification, theme and sensitivity settings."""
    payload = require_dict(request.get_json(silent=True) or {})
    user = auth_service.update_preferences(current_user(), payload)
    return success(user.to_dict(include_preferences=True), message="Preferences saved.")


@bp.put("/password")
@token_required
def change_password():
    """PUT /api/auth/password - change the signed-in user's password."""
    payload = require_dict(request.get_json(silent=True) or {})
    auth_service.change_password(
        current_user(), payload.get("current_password"), payload.get("new_password")
    )
    return success(message="Password changed successfully.")
