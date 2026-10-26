"""Blueprint registry.

Each feature area owns one blueprint module, which keeps the API modular instead
of a single oversized Flask file (see the Component Diagram).
"""
from .alerts import bp as alerts_bp
from .assets import bp as assets_bp
from .auth import bp as auth_bp
from .dashboard import analytics_bp, bp as dashboard_bp
from .events import bp as events_bp
from .incidents import bp as incidents_bp
from .reports import bp as reports_bp
from .system import bp as system_bp
from .threats import bp as threats_bp, intel_bp as threat_intel_bp

ALL_BLUEPRINTS = (
    auth_bp,
    dashboard_bp,
    analytics_bp,
    events_bp,
    threats_bp,
    threat_intel_bp,
    alerts_bp,
    incidents_bp,
    assets_bp,
    reports_bp,
    system_bp,
)


def register_blueprints(app):
    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)
    return app


__all__ = ["ALL_BLUEPRINTS", "register_blueprints"]
