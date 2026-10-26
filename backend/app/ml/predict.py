"""Standalone inference script.

Lets an examiner run the detection engine from the command line without starting
the web application:

    python -m app.ml.predict --failed-logins 24 --source-ip 203.0.113.44 \
        --dest-port 22 --event-type authentication

    python -m app.ml.predict --json "{\"source_ip\": \"10.0.1.5\", \"bytes_transferred\": 900000000}"

    python -m app.ml.predict --csv ../sample_data/sample_logs_mixed.csv
"""
import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.detector import ThreatDetector  # noqa: E402

MODEL_DIR = BACKEND_DIR / "ml_model"


def analyse_one(detector: ThreatDetector, event: dict) -> dict:
    result = detector.detect(event)
    print(f"\n  Source        : {event.get('source_ip', 'n/a')} -> "
          f"{event.get('destination_ip', 'n/a')}:{event.get('destination_port', 'n/a')}")
    print(f"  Classification: {result['classification']}")
    print(f"  Risk score    : {result['risk_score']}/100")
    print(f"  Severity      : {result['severity']}")
    print(f"  Confidence    : {result['confidence'] * 100:.1f}%")
    print(f"  Engine        : {result['model_used']} v{result['engine_version']}")
    print("  Reasons:")
    for reason in result["reasons"]:
        print(f"    - {reason}")
    print(f"  Recommended   : {result['recommended_action']}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CyberGuard AI detection from the CLI.")
    parser.add_argument("--json", type=str, help="a JSON event object")
    parser.add_argument("--csv", type=str, help="path to a CSV log file")
    parser.add_argument("--source-ip", type=str, default="203.0.113.10")
    parser.add_argument("--dest-ip", type=str, default="10.0.1.20")
    parser.add_argument("--dest-port", type=int, default=443)
    parser.add_argument("--source-port", type=int, default=51514)
    parser.add_argument("--protocol", type=str, default="TCP")
    parser.add_argument("--event-type", type=str, default="network_traffic")
    parser.add_argument("--failed-logins", type=int, default=0)
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--packets", type=int, default=120)
    parser.add_argument("--bytes", type=float, default=90000.0)
    parser.add_argument("--duration", type=float, default=30.0)
    args = parser.parse_args()

    detector = ThreatDetector(model_dir=MODEL_DIR)
    info = detector.model_info()
    print("CyberGuard AI detection engine")
    print(f"  mode={info['mode']}  ml_available={info['ml_available']}  "
          f"baseline={info['baseline_source']}")

    if args.csv:
        from app.utils.csv_parser import parse_csv

        text = Path(args.csv).read_text(encoding="utf-8-sig")
        rows, errors = parse_csv(text)
        print(f"\nParsed {len(rows)} rows ({len(errors)} rejected) from {args.csv}")
        tally = {}
        for row in rows:
            result = detector.detect(row)
            tally[result["severity"]] = tally.get(result["severity"], 0) + 1
        print("Severity distribution:")
        for severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            print(f"  {severity:<9} {tally.get(severity, 0)}")
        return

    if args.json:
        event = json.loads(args.json)
    else:
        event = {
            "source_ip": args.source_ip,
            "destination_ip": args.dest_ip,
            "source_port": args.source_port,
            "destination_port": args.dest_port,
            "protocol": args.protocol,
            "event_type": args.event_type,
            "failed_login_attempts": args.failed_logins,
            "request_count": args.requests,
            "packet_count": args.packets,
            "bytes_transferred": args.bytes,
            "connection_duration": args.duration,
        }

    analyse_one(detector, event)


if __name__ == "__main__":
    main()
