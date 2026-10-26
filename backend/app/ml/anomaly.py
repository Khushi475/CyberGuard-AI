"""Statistical anomaly scoring.

The baseline holds the mean and standard deviation of each numeric feature for
*benign* traffic.  A robust z-score is computed per feature and the largest few
are combined into a 0-100 anomaly score.

The default baseline below was computed from the synthetic benign population
produced by ``generate_dataset.py``; running ``train_model.py`` overwrites it
with a freshly measured baseline saved to ``ml_model/baseline.json``.
"""
import json
import os
from math import exp
from pathlib import Path

from .features import FEATURE_NAMES

BASELINE_FILENAME = "baseline.json"

# Feature -> (mean, standard deviation) for normal enterprise traffic.
DEFAULT_BASELINE = {
    "failed_login_attempts": (0.18, 0.55),
    "request_count": (14.0, 12.0),
    "packet_count": (120.0, 110.0),
    "bytes_transferred": (180000.0, 240000.0),
    "connection_duration": (46.0, 60.0),
    "bytes_per_packet": (900.0, 420.0),
    "packets_per_second": (4.0, 5.0),
    "requests_per_second": (0.7, 1.1),
    "bytes_per_request": (16000.0, 18000.0),
    "log_bytes": (11.4, 1.6),
    "log_requests": (2.5, 0.9),
}

# Features that are categorical / cyclical are excluded from z-scoring.
SCORED_FEATURES = list(DEFAULT_BASELINE.keys())


class StatisticalBaseline:
    """Holds per-feature statistics and converts an event into an anomaly score."""

    def __init__(self, stats: dict | None = None, source: str = "default"):
        self.stats = {key: tuple(value) for key, value in (stats or DEFAULT_BASELINE).items()}
        self.source = source

    # -- persistence -----------------------------------------------------
    @classmethod
    def load(cls, model_dir: str | os.PathLike):
        path = Path(model_dir) / BASELINE_FILENAME
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                stats = payload.get("stats") or payload
                if isinstance(stats, dict) and stats:
                    return cls(stats, source=str(path))
            except (ValueError, OSError):
                pass
        return cls(source="default")

    def save(self, model_dir: str | os.PathLike) -> Path:
        path = Path(model_dir) / BASELINE_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"stats": {k: list(v) for k, v in self.stats.items()}}, handle, indent=2)
        return path

    # -- scoring ---------------------------------------------------------
    def z_scores(self, features: dict) -> dict:
        scores = {}
        for name in SCORED_FEATURES:
            mean, std = self.stats.get(name, DEFAULT_BASELINE.get(name, (0.0, 1.0)))
            std = max(float(std), 1e-6)
            value = float(features.get(name, 0.0))
            scores[name] = (value - float(mean)) / std
        return scores

    def score(self, features: dict):
        """Return ``(anomaly_score_0_100, reasons)`` for one event."""
        zs = self.z_scores(features)
        # Only positive deviations matter: unusually *low* traffic is not a threat.
        positives = sorted(
            ((name, z) for name, z in zs.items() if z > 2.0),
            key=lambda item: item[1],
            reverse=True,
        )
        if not positives:
            top = max(zs.values()) if zs else 0.0
            return max(0.0, min(20.0, top * 6.0)), []

        # Combine the three strongest deviations with diminishing weight, then map
        # the total through a saturating curve.  A linear mapping would push every
        # attack-shaped event straight to 100 and erase the difference between a
        # mildly unusual event and an extreme one.
        weights = (1.0, 0.45, 0.25)
        combined = sum(z * w for (_, z), w in zip(positives[:3], weights))
        score = 100.0 * (1.0 - exp(-combined / 9.0))

        reasons = [
            f"'{_pretty(name)}' is {z:.1f} standard deviations above the learned normal "
            f"baseline."
            for name, z in positives[:3]
        ]
        return score, reasons

    def as_dict(self) -> dict:
        return {"source": self.source, "features": len(self.stats), "stats": self.stats}


def _pretty(name: str) -> str:
    return name.replace("_", " ")


def fit_baseline(rows) -> StatisticalBaseline:
    """Compute mean/std from an iterable of benign feature dictionaries."""
    import numpy as np

    matrix = {name: [] for name in SCORED_FEATURES}
    for row in rows:
        for name in SCORED_FEATURES:
            matrix[name].append(float(row.get(name, 0.0)))

    stats = {}
    for name, values in matrix.items():
        if not values:
            stats[name] = DEFAULT_BASELINE[name]
            continue
        array = np.asarray(values, dtype=float)
        stats[name] = (float(array.mean()), float(max(array.std(), 1e-6)))
    return StatisticalBaseline(stats, source="fitted")


__all__ = ["StatisticalBaseline", "fit_baseline", "DEFAULT_BASELINE", "FEATURE_NAMES"]
