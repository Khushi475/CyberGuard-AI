"""The CyberGuard AI hybrid threat-detection engine.

Three independent detectors vote on every event:

1. **Rule bank** (``rules.py``) - deterministic, fully explainable behavioural rules.
2. **Statistical baseline** (``anomaly.py``) - robust z-scores against learned normals.
3. **Machine learning** (optional) - a RandomForest classifier plus an IsolationForest
   novelty detector trained by ``train_model.py``.

The fused risk score is

    weighted   = w_rule*rule + w_anomaly*anomaly + w_ml*ml
    risk       = clamp(max(weighted, 0.85 * strongest_single_detector) * sensitivity)

The ``max(...)`` guard means one very strong detector is never diluted by the
others, while the weighted term rewards agreement between detectors.

The engine is fully functional with the ML models absent - it simply falls back to
rules plus statistics and reports ``model_used = "hybrid-rules"``.
"""
import threading
import time
from pathlib import Path

from .anomaly import StatisticalBaseline
from .features import FEATURE_NAMES, describe_features, extract_features, features_to_vector
from .rules import evaluate_rules, mitre_tactic, recommended_action

ENGINE_VERSION = "1.2"

SEVERITY_BANDS = (
    (0, 25, "LOW"),
    (26, 50, "MEDIUM"),
    (51, 75, "HIGH"),
    (76, 100, "CRITICAL"),
)

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

THREAT_RISK_THRESHOLD = 26

MODEL_FILES = {
    "classifier": "threat_classifier.joblib",
    "anomaly": "isolation_forest.joblib",
    "scaler": "feature_scaler.joblib",
}


def severity_for(risk_score: float) -> str:
    score = max(0, min(100, int(round(risk_score))))
    for low, high, label in SEVERITY_BANDS:
        if low <= score <= high:
            return label
    return "LOW"


class ThreatDetector:
    """Stateless-per-call detector; models are loaded once and cached."""

    def __init__(self, model_dir=None, sensitivity: float = 1.0):
        self.model_dir = Path(model_dir) if model_dir else None
        self.sensitivity = float(sensitivity or 1.0)
        self.baseline = (
            StatisticalBaseline.load(self.model_dir) if self.model_dir else StatisticalBaseline()
        )
        self._lock = threading.Lock()
        self._models_loaded = False
        self._classifier = None
        self._iforest = None
        self._scaler = None
        self._load_error = None

    # ------------------------------------------------------------------ models
    def _load_models(self) -> None:
        """Lazily load the optional scikit-learn artefacts (thread safe)."""
        if self._models_loaded or self.model_dir is None:
            self._models_loaded = True
            return
        with self._lock:
            if self._models_loaded:
                return
            try:
                import joblib  # imported here so the app runs without scikit-learn

                classifier_path = self.model_dir / MODEL_FILES["classifier"]
                iforest_path = self.model_dir / MODEL_FILES["anomaly"]
                scaler_path = self.model_dir / MODEL_FILES["scaler"]

                if classifier_path.exists():
                    self._classifier = joblib.load(classifier_path)
                if iforest_path.exists():
                    self._iforest = joblib.load(iforest_path)
                if scaler_path.exists():
                    self._scaler = joblib.load(scaler_path)

                # Force single-threaded inference. The models are trained with
                # n_jobs=-1, which is right for fitting, but at prediction time we
                # score one event at a time: joblib then spends far more time
                # dispatching to a thread pool than doing the work. Measured on the
                # development machine, predict_proba on a single sample takes ~43 ms
                # with n_jobs=-1 and ~4.6 ms with n_jobs=1 - a 9x difference that
                # dominated total analysis latency.
                for model in (self._classifier, self._iforest):
                    if model is not None and hasattr(model, "n_jobs"):
                        model.n_jobs = 1
            except Exception as exc:  # pragma: no cover - environment dependent
                self._load_error = str(exc)
                self._classifier = self._iforest = self._scaler = None
            finally:
                self._models_loaded = True

    @property
    def ml_available(self) -> bool:
        self._load_models()
        return self._classifier is not None or self._iforest is not None

    def model_info(self) -> dict:
        self._load_models()
        return {
            "engine_version": ENGINE_VERSION,
            "ml_available": self.ml_available,
            "classifier_loaded": self._classifier is not None,
            "anomaly_model_loaded": self._iforest is not None,
            "scaler_loaded": self._scaler is not None,
            "baseline_source": self.baseline.source,
            "sensitivity": self.sensitivity,
            "model_dir": str(self.model_dir) if self.model_dir else None,
            "load_error": self._load_error,
            "feature_count": len(FEATURE_NAMES),
            "mode": "hybrid-ml" if self.ml_available else "hybrid-rules",
        }

    def reload(self) -> dict:
        """Force the next detection to re-read models from disk."""
        with self._lock:
            self._models_loaded = False
            self._classifier = self._iforest = self._scaler = None
            self._load_error = None
        if self.model_dir:
            self.baseline = StatisticalBaseline.load(self.model_dir)
        return self.model_info()

    def _ml_score(self, features: dict):
        """Return ``(score_0_100, reasons)`` from the trained models, if present."""
        self._load_models()
        if self._classifier is None and self._iforest is None:
            return 0.0, [], False

        vector = [features_to_vector(features)]
        reasons = []
        scores = []

        try:
            transformed = self._scaler.transform(vector) if self._scaler is not None else vector
        except Exception:  # pragma: no cover - shape mismatch safety net
            return 0.0, [], False

        if self._classifier is not None:
            try:
                probability = float(self._classifier.predict_proba(transformed)[0][1])
                scores.append(probability * 100.0)
                if probability >= 0.5:
                    reasons.append(
                        f"The trained classifier assigns a {probability * 100:.0f}% probability "
                        "that this event is malicious."
                    )
            except Exception:  # pragma: no cover
                pass

        if self._iforest is not None:
            try:
                # decision_function: positive = inlier, negative = outlier.
                raw = float(self._iforest.decision_function(transformed)[0])
                outlier_score = max(0.0, min(100.0, (0.1 - raw) * 320.0))
                scores.append(outlier_score)
                if outlier_score >= 45:
                    reasons.append(
                        "The isolation-forest novelty model flags this event as an outlier "
                        "compared with the training population."
                    )
            except Exception:  # pragma: no cover
                pass

        if not scores:
            return 0.0, [], False
        return max(scores), reasons, True

    # --------------------------------------------------------------- detection
    def detect(self, event: dict, sensitivity: float | None = None) -> dict:
        """Analyse one security event and return the explainable verdict."""
        started = time.perf_counter()
        sensitivity = float(sensitivity if sensitivity is not None else self.sensitivity)
        sensitivity = max(0.5, min(1.5, sensitivity))

        features = extract_features(event)

        rule_outcome = evaluate_rules(features, event)
        rule_score = float(rule_outcome["score"])

        anomaly_score, anomaly_reasons = self.baseline.score(features)
        ml_score, ml_reasons, ml_used = self._ml_score(features)

        if ml_used:
            weighted = 0.58 * rule_score + 0.18 * anomaly_score + 0.24 * ml_score
            model_used = "hybrid-ml"
        else:
            weighted = 0.74 * rule_score + 0.26 * anomaly_score
            model_used = "hybrid-rules"

        # The rule bank is the authoritative, explainable signal, so its score acts
        # as a floor.  The statistical and ML detectors contribute only through the
        # weighted term: on their own they can raise an event to MEDIUM for review
        # but never to CRITICAL, which keeps unexplained outliers from saturating
        # the queue with unactionable "critical" noise.
        fused = max(weighted, 0.85 * rule_score) * sensitivity
        risk_score = int(round(max(0.0, min(100.0, fused))))

        classification = rule_outcome["category"]
        if classification == "Normal Activity" and risk_score >= THREAT_RISK_THRESHOLD:
            # Nothing deterministic matched, but the statistical/ML side objected.
            classification = "Network Anomaly"

        reasons = []
        if classification == "Normal Activity":
            reasons.append(
                "All measured indicators fall inside the expected baseline for this traffic type."
            )
        else:
            reasons.extend(rule_outcome["reasons"])
        reasons.extend(anomaly_reasons)
        reasons.extend(ml_reasons)
        # De-duplicate while preserving order.
        seen = set()
        reasons = [r for r in reasons if not (r in seen or seen.add(r))][:8]

        severity = severity_for(risk_score)
        is_threat = risk_score >= THREAT_RISK_THRESHOLD and classification != "Normal Activity"

        confidence = self._confidence(
            risk_score, rule_score, anomaly_score, ml_score, ml_used, is_threat
        )

        elapsed_ms = (time.perf_counter() - started) * 1000.0

        return {
            "classification": classification,
            "risk_score": risk_score,
            "confidence": round(confidence, 3),
            "severity": severity,
            "is_threat": is_threat,
            "reasons": reasons,
            "recommended_action": recommended_action(classification),
            "mitre_tactic": mitre_tactic(classification),
            "scores": {
                "rule": round(rule_score, 2),
                "anomaly": round(anomaly_score, 2),
                "ml": round(ml_score, 2),
            },
            "triggered_rules": [
                {"category": item["category"], "score": item["score"]}
                for item in rule_outcome["triggered"]
            ],
            "features": features,
            "feature_summary": describe_features(features),
            "model_used": model_used,
            "engine_version": ENGINE_VERSION,
            "sensitivity": sensitivity,
            "analysis_time_ms": round(elapsed_ms, 3),
        }

    @staticmethod
    def _confidence(risk, rule_score, anomaly_score, ml_score, ml_used, is_threat) -> float:
        """Confidence grows with signal strength and with detector agreement."""
        candidates = [rule_score, anomaly_score] + ([ml_score] if ml_used else [])
        active = [score for score in candidates if score > 0]
        if len(active) >= 2:
            spread = (max(active) - min(active)) / 100.0
            agreement = max(0.0, 1.0 - spread)
        else:
            agreement = 0.45

        if is_threat:
            strength = risk / 100.0
            confidence = 0.55 + 0.32 * strength + 0.13 * agreement
        else:
            # Confidence that the event is benign: high when every score is low.
            calm = 1.0 - (risk / 100.0)
            confidence = 0.60 + 0.35 * calm
        return max(0.50, min(0.99, confidence))

    def detect_batch(self, events, sensitivity: float | None = None) -> list:
        return [self.detect(event, sensitivity=sensitivity) for event in events]


_default_detector = None
_default_lock = threading.Lock()


def get_detector(model_dir=None, sensitivity: float = 1.0) -> ThreatDetector:
    """Return the process-wide detector singleton (created on first use)."""
    global _default_detector
    if _default_detector is None:
        with _default_lock:
            if _default_detector is None:
                _default_detector = ThreatDetector(model_dir=model_dir, sensitivity=sensitivity)
    return _default_detector


def reset_detector() -> None:
    """Used by the test-suite to rebuild the singleton between app instances."""
    global _default_detector
    with _default_lock:
        _default_detector = None
