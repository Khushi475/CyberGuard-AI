"""Application logging configuration.

Logs go to the console and to ``backend/logs/cyberguard.log`` so that the viva
demonstration can show real request/detection traces (NFR-04 Reliability).
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"


def configure_logging(app):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    handlers = [stream_handler]

    if not app.config.get("TESTING"):
        file_handler = RotatingFileHandler(
            LOG_DIR / "cyberguard.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)

    app.logger.handlers.clear()
    for handler in handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(level)
    app.logger.propagate = False

    detection_logger = logging.getLogger("cyberguard.detection")
    detection_logger.handlers.clear()
    for handler in handlers:
        detection_logger.addHandler(handler)
    detection_logger.setLevel(level)
    detection_logger.propagate = False

    app.logger.info("Logging initialised (level=%s, dir=%s)", logging.getLevelName(level), LOG_DIR)
    return app.logger


def get_logger(name: str = "cyberguard") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    return logger


os.environ.setdefault("PYTHONUNBUFFERED", "1")
