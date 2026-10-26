"""Application configuration objects for CyberGuard AI.

Configuration is environment driven so that the same code base can run as a
development prototype, inside the automated test-suite, or on a demo machine
without any source changes.  Secrets are never hard-coded here.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATABASE_DIR = PROJECT_ROOT / "database"
ML_MODEL_DIR = BACKEND_DIR / "ml_model"
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"

load_dotenv(BACKEND_DIR / ".env")

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _normalise_database_url(raw_url: str) -> str:
    """Resolve a relative sqlite URL against the shared ``database/`` folder."""
    if raw_url.startswith("sqlite:///") and not raw_url.startswith("sqlite:////"):
        filename = raw_url.replace("sqlite:///", "", 1)
        candidate = Path(filename)
        if not candidate.is_absolute():
            candidate = DATABASE_DIR / filename
        return f"sqlite:///{candidate.as_posix()}"
    return raw_url


class BaseConfig:
    """Settings shared by every runtime profile."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change_this_for_local_development")
    SQLALCHEMY_DATABASE_URI = _normalise_database_url(
        os.getenv("DATABASE_URL", "sqlite:///cyberguard.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = [
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

    TOKEN_MAX_AGE_SECONDS = int(os.getenv("TOKEN_MAX_AGE_SECONDS", "86400"))
    DETECTION_SENSITIVITY = float(os.getenv("DETECTION_SENSITIVITY", "1.0"))

    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB upload ceiling
    MAX_CSV_ROWS = 5000

    ML_MODEL_DIR = str(ML_MODEL_DIR)
    SAMPLE_DATA_DIR = str(SAMPLE_DATA_DIR)
    PROJECT_ROOT = str(PROJECT_ROOT)

    # Alerts are raised from MEDIUM upwards; CRITICAL findings also open an incident.
    ALERT_RISK_THRESHOLD = 26
    INCIDENT_RISK_THRESHOLD = 76


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "testing-secret-key"


class ProductionConfig(BaseConfig):
    """Kept for completeness - this project is an academic prototype only."""

    DEBUG = False
    ENV = "production"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.getenv("FLASK_ENV") or "development").lower()
    return CONFIG_MAP.get(key, DevelopmentConfig)
