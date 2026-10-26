"""Training script for the optional machine-learning half of the detector.

Run it from the ``backend`` folder:

    python -m app.ml.train_model              # 6000 synthetic samples
    python -m app.ml.train_model --samples 12000 --seed 7

It writes four artefacts into ``backend/ml_model/``:

    threat_classifier.joblib   RandomForest (supervised: benign vs. suspicious)
    isolation_forest.joblib    IsolationForest (unsupervised novelty detection)
    feature_scaler.joblib      StandardScaler fitted on the training matrix
    baseline.json              per-feature mean/std of the benign population
    metadata.json              accuracy, feature order, training parameters

The application deliberately does NOT require these files: without them the
detector runs in ``hybrid-rules`` mode using the rule bank plus the default
statistical baseline.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.anomaly import fit_baseline  # noqa: E402
from app.ml.features import FEATURE_NAMES, extract_features, features_to_vector  # noqa: E402
from app.ml.generate_dataset import generate_events  # noqa: E402

MODEL_DIR = BACKEND_DIR / "ml_model"


def build_matrix(samples: int, seed: int):
    events = generate_events(count=samples, seed=seed, days_back=90)
    feature_rows = [extract_features(event) for event in events]
    x = [features_to_vector(row) for row in feature_rows]
    y = [event["label"] for event in events]
    benign_rows = [row for row, event in zip(feature_rows, events) if event["label"] == 0]
    return x, y, benign_rows, events


def train(samples: int = 6000, seed: int = 42, output_dir: Path = MODEL_DIR) -> dict:
    try:
        import joblib
        import numpy as np
        from sklearn.ensemble import IsolationForest, RandomForestClassifier
        from sklearn.metrics import accuracy_score, classification_report, f1_score
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise SystemExit(
            "scikit-learn / joblib are required for training. Install them with:\n"
            "    pip install -r requirements.txt\n"
            f"(original error: {exc})"
        ) from exc

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {samples} synthetic security events (seed={seed}) ...")
    x, y, benign_rows, events = build_matrix(samples, seed)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=int)
    print(f"  feature matrix: {x.shape[0]} rows x {x.shape[1]} features")
    print(f"  class balance : benign={int((y == 0).sum())}, suspicious={int((y == 1).sum())}")

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=seed, stratify=y
    )

    scaler = StandardScaler().fit(x_train)
    x_train_scaled = scaler.transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    print("Training RandomForestClassifier ...")
    classifier = RandomForestClassifier(
        n_estimators=220,
        max_depth=14,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    ).fit(x_train_scaled, y_train)

    predictions = classifier.predict(x_test_scaled)
    accuracy = float(accuracy_score(y_test, predictions))
    f1 = float(f1_score(y_test, predictions))
    print(f"  hold-out accuracy: {accuracy:.4f}")
    print(f"  hold-out F1      : {f1:.4f}")
    print(classification_report(y_test, predictions, target_names=["benign", "suspicious"]))

    print("Training IsolationForest on the benign population ...")
    benign_matrix = scaler.transform(x_train[y_train == 0])
    iforest = IsolationForest(
        n_estimators=180, contamination=0.06, random_state=seed, n_jobs=-1
    ).fit(benign_matrix)

    print("Fitting the statistical baseline ...")
    baseline = fit_baseline(benign_rows)
    baseline.save(output_dir)

    joblib.dump(classifier, output_dir / "threat_classifier.joblib")
    joblib.dump(iforest, output_dir / "isolation_forest.joblib")
    joblib.dump(scaler, output_dir / "feature_scaler.joblib")

    importances = sorted(
        zip(FEATURE_NAMES, (float(v) for v in classifier.feature_importances_)),
        key=lambda item: item[1],
        reverse=True,
    )

    metadata = {
        "trained_at": datetime.utcnow().isoformat(timespec="seconds"),
        "samples": int(samples),
        "seed": int(seed),
        "feature_names": FEATURE_NAMES,
        "holdout_accuracy": round(accuracy, 4),
        "holdout_f1": round(f1, 4),
        "top_features": [{"feature": name, "importance": round(value, 4)}
                         for name, value in importances[:8]],
        "classifier": "RandomForestClassifier(n_estimators=220, max_depth=14)",
        "anomaly_model": "IsolationForest(n_estimators=180, contamination=0.06)",
        "note": "Metrics are measured on synthetic hold-out data generated by "
                "app/ml/generate_dataset.py, not on real-world network captures. The generator "
                "produces well-separated behaviour profiles, so a near-perfect score reflects "
                "that separability rather than real-world detection performance.",
    }
    with open(output_dir / "metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print("\nArtefacts written to", output_dir)
    for name in ("threat_classifier.joblib", "isolation_forest.joblib",
                 "feature_scaler.joblib", "baseline.json", "metadata.json"):
        print("  -", name)
    print("\nTop features:")
    for name, value in importances[:8]:
        print(f"  {name:<26} {value:.4f}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the CyberGuard AI detection models.")
    parser.add_argument("--samples", type=int, default=6000, help="number of synthetic samples")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--output", type=str, default=str(MODEL_DIR), help="artefact directory")
    args = parser.parse_args()
    train(samples=args.samples, seed=args.seed, output_dir=Path(args.output))


if __name__ == "__main__":
    main()
