"""CyberGuard AI detection engine package.

Modules
-------
features.py          feature engineering shared by training and inference
rules.py             explainable behavioural rule bank
anomaly.py           statistical baseline / z-score novelty scoring
detector.py          hybrid fusion engine (the public entry point)
generate_dataset.py  synthetic, safe security-event generator
train_model.py       optional scikit-learn training script
predict.py           command line inference utility
"""
from .detector import ENGINE_VERSION, ThreatDetector, get_detector, reset_detector, severity_for
from .features import FEATURE_NAMES, extract_features

__all__ = [
    "ENGINE_VERSION",
    "FEATURE_NAMES",
    "ThreatDetector",
    "extract_features",
    "get_detector",
    "reset_detector",
    "severity_for",
]
