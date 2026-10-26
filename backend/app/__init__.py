"""CyberGuard AI - Flask application factory.

    from app import create_app
    app = create_app()

The factory wires configuration, extensions, logging, the detection engine, all
blueprints and the global error handlers.  Using a factory (rather than a module
level ``app``) is what lets the pytest suite build an isolated in-memory instance
for every test module.
"""
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from .config import get_config
from .extensions import cors, db
from .ml.detector import ThreatDetector
from .routes import register_blueprints
from .utils.errors import ApiError
from .utils.logger import configure_logging

__version__ = "1.0.0"


def create_app(config_name: str | None = None, **overrides) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    app.config.update(overrides)

    configure_logging(app)

    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Auth-Token"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # One detection engine per application instance, created eagerly so that a
    # missing model file is reported at start-up rather than on the first request.
    app.extensions["cyberguard_detector"] = ThreatDetector(
        model_dir=app.config["ML_MODEL_DIR"],
        sensitivity=app.config.get("DETECTION_SENSITIVITY", 1.0),
    )

    register_blueprints(app)
    register_error_handlers(app)
    register_cli(app)

    with app.app_context():
        db.create_all()

    engine_info = app.extensions["cyberguard_detector"].model_info()
    app.logger.info(
        "CyberGuard AI %s ready | env=%s | detection=%s | db=%s",
        __version__,
        app.config.get("ENV"),
        engine_info["mode"],
        app.config["SQLALCHEMY_DATABASE_URI"],
    )
    return app


def register_error_handlers(app: Flask) -> None:
    """Translate every failure into the same JSON envelope."""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        if error.status_code >= 500:
            app.logger.exception("API error on %s: %s", request.path, error.message)
        else:
            app.logger.warning("%s on %s: %s", error.error_code, request.path, error.message)
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(error):
        limit_mb = app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "FILE_TOO_LARGE",
                    "message": f"The uploaded file exceeds the {limit_mb:.0f} MB limit.",
                }
            ),
            413,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "NOT_FOUND",
                    "message": f"No API route matches {request.method} {request.path}. "
                               "See GET /api for the endpoint index.",
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "METHOD_NOT_ALLOWED",
                    "message": f"{request.method} is not supported on {request.path}.",
                }
            ),
            405,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return (
            jsonify(
                {
                    "success": False,
                    "error": error.name.upper().replace(" ", "_"),
                    "message": error.description,
                }
            ),
            error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        db.session.rollback()
        app.logger.exception("Unhandled error on %s", request.path)
        message = (
            str(error)
            if app.config.get("DEBUG") or app.config.get("TESTING")
            else "An internal server error occurred. Check the backend logs for details."
        )
        return (
            jsonify({"success": False, "error": "INTERNAL_SERVER_ERROR", "message": message}),
            500,
        )


def register_cli(app: Flask) -> None:
    """Small maintenance commands: ``flask init-db`` and ``flask seed-db``."""

    @app.cli.command("init-db")
    def init_db():  # pragma: no cover - developer convenience
        """Create every table defined by the ORM models."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db():  # pragma: no cover - developer convenience
        """Populate the database with the synthetic demonstration dataset."""
        from seed_database import seed

        seed()
