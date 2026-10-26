"""Authentication service (FR-01).

Academic-demo authentication: passwords are stored as salted PBKDF2 hashes
(Werkzeug) and sessions are signed, expiring tokens.  It is intentionally simple
and is not a production identity solution.
"""
from datetime import datetime

from ..extensions import db
from ..models import User
from ..utils.errors import AuthError, ValidationError
from ..utils.security import generate_token
from ..utils.validators import validate_email, validate_password, validate_string
from .audit_service import record as audit


def login(email: str, password: str) -> dict:
    email = validate_email(email)
    # Only presence is checked here. Applying the registration strength rule at
    # sign-in would return a validation error for a short *wrong* password, which
    # both confuses the user and leaks information about the stored credential.
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required.", details={"field": "password"})

    user = User.query.filter(User.email == email).first()
    if user is None or not user.check_password(password):
        # The same message for both cases avoids leaking which accounts exist.
        audit(
            "LOGIN_FAILED",
            f"Failed sign-in attempt for {email}.",
            entity_type="User",
            status="FAILURE",
            commit=True,
        )
        raise AuthError("Invalid email address or password.", error_code="INVALID_CREDENTIALS")

    if not user.is_active:
        raise AuthError("This account has been deactivated.", error_code="ACCOUNT_DISABLED")

    user.last_login = datetime.utcnow()
    token = generate_token(user)

    audit(
        "LOGIN_SUCCESS",
        f"{user.full_name} signed in.",
        entity_type="User",
        entity_id=user.id,
        user=user,
    )
    db.session.commit()

    return {"token": token, "user": user.to_dict(include_preferences=True)}


def logout(user) -> None:
    audit(
        "LOGOUT",
        f"{getattr(user, 'full_name', 'A user')} signed out.",
        entity_type="User",
        entity_id=getattr(user, "id", None),
        user=user,
        commit=True,
    )


def update_profile(user, payload: dict) -> User:
    if "full_name" in payload:
        user.full_name = validate_string(payload.get("full_name"), "full_name", 120)
    if "department" in payload:
        user.department = validate_string(
            payload.get("department"), "department", 80, required=False
        )
    if "email" in payload and payload["email"]:
        new_email = validate_email(payload["email"])
        existing = User.query.filter(User.email == new_email, User.id != user.id).first()
        if existing is not None:
            raise ValidationError(
                "Another account already uses that email address.",
                details={"field": "email"},
            )
        user.email = new_email

    audit(
        "PROFILE_UPDATED",
        f"{user.full_name} updated their profile.",
        entity_type="User",
        entity_id=user.id,
        user=user,
    )
    db.session.commit()
    return user


def update_preferences(user, payload: dict) -> User:
    if "notify_email" in payload:
        user.notify_email = bool(payload["notify_email"])
    if "notify_critical_only" in payload:
        user.notify_critical_only = bool(payload["notify_critical_only"])
    if "theme" in payload:
        theme = str(payload["theme"]).lower()
        if theme not in ("dark", "light"):
            raise ValidationError(
                "theme must be either 'dark' or 'light'.", details={"field": "theme"}
            )
        user.theme = theme
    if "detection_sensitivity" in payload:
        try:
            sensitivity = float(payload["detection_sensitivity"])
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "detection_sensitivity must be a number between 0.5 and 1.5.",
                details={"field": "detection_sensitivity"},
            ) from exc
        if not 0.5 <= sensitivity <= 1.5:
            raise ValidationError(
                "detection_sensitivity must be between 0.5 and 1.5.",
                details={"field": "detection_sensitivity"},
            )
        user.detection_sensitivity = round(sensitivity, 2)

    audit(
        "PREFERENCES_UPDATED",
        f"{user.full_name} updated their system preferences.",
        entity_type="User",
        entity_id=user.id,
        user=user,
    )
    db.session.commit()
    return user


def change_password(user, current_password: str, new_password: str) -> User:
    if not user.check_password(current_password or ""):
        raise AuthError("The current password is incorrect.", error_code="INVALID_CREDENTIALS")
    new_password = validate_password(new_password, field="new_password")
    if new_password == current_password:
        raise ValidationError(
            "The new password must differ from the current one.",
            details={"field": "new_password"},
        )
    user.set_password(new_password)
    audit(
        "PASSWORD_CHANGED",
        f"{user.full_name} changed their password.",
        entity_type="User",
        entity_id=user.id,
        user=user,
    )
    db.session.commit()
    return user
