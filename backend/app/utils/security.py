"""Token issuing / verification and route protection decorators.

This is deliberately simple, signed-token authentication suited to an academic
prototype.  Tokens are created with ``itsdangerous`` (already a Flask
dependency), signed with ``SECRET_KEY`` and carry an expiry.  They are *not* a
substitute for a production identity provider - see the limitations section of
the README.
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .errors import AuthError, ForbiddenError


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="cyberguard-auth")


def generate_token(user) -> str:
    """Create a signed session token for an authenticated user."""
    return _serializer().dumps({"uid": user.id, "email": user.email, "role": user.role})


def decode_token(token: str) -> dict:
    max_age = current_app.config.get("TOKEN_MAX_AGE_SECONDS", 86400)
    try:
        return _serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise AuthError("Session expired. Please sign in again.", error_code="TOKEN_EXPIRED") from exc
    except BadSignature as exc:
        raise AuthError("Invalid authentication token.", error_code="TOKEN_INVALID") from exc


def _extract_token() -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    if header:
        return header.strip()
    token = request.headers.get("X-Auth-Token") or request.args.get("token")
    if token:
        return token.strip()
    raise AuthError("Authentication required. Provide a Bearer token.", error_code="NO_TOKEN")


def load_current_user():
    """Resolve the request token into a ``User`` instance and cache it on ``g``."""
    from ..models import User  # local import avoids a circular dependency

    if getattr(g, "current_user", None) is not None:
        return g.current_user
    payload = decode_token(_extract_token())
    user = User.query.get(payload.get("uid"))
    if user is None:
        raise AuthError("The account linked to this token no longer exists.")
    if not user.is_active:
        raise ForbiddenError("This account has been deactivated.")
    g.current_user = user
    return user


def token_required(view):
    """Protect a route: a valid Bearer token must be supplied."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        load_current_user()
        return view(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """Protect a route and additionally require one of the given roles."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = load_current_user()
            if roles and user.role not in roles:
                raise ForbiddenError(
                    f"This action requires one of the following roles: {', '.join(roles)}."
                )
            return view(*args, **kwargs)

        return wrapper

    return decorator


def current_user():
    """Return the authenticated user for the active request (or ``None``)."""
    return getattr(g, "current_user", None)
