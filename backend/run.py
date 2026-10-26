"""Development entry point for the CyberGuard AI backend.

    python run.py

Reads HOST / PORT / FLASK_DEBUG from ``.env`` (or the environment) and prints a
short banner so the demonstration clearly shows which URL to open.
"""
import os

from app import __version__, create_app

app = create_app()


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") not in ("0", "false", "False")

    engine = app.extensions["cyberguard_detector"].model_info()

    print("=" * 66)
    print(f"  CyberGuard AI - Intelligent Cyber Threat Detection System v{__version__}")
    print("  Academic prototype - defensive, simulated telemetry only")
    print("=" * 66)
    print(f"  API root        : http://{host}:{port}/api")
    print(f"  Health check    : http://{host}:{port}/api/health")
    print(f"  Detection engine: {engine['mode']} (ml_available={engine['ml_available']})")
    print(f"  Database        : {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"  Allowed origins : {', '.join(app.config['CORS_ORIGINS'][:2])} ...")
    print("=" * 66)
    print("  Start the frontend in another terminal with:  cd frontend && npm run dev")
    print("=" * 66)

    app.run(host=host, port=port, debug=debug, use_reloader=debug)


if __name__ == "__main__":
    main()
