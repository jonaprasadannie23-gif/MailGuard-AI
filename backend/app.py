"""
ProbMail Backend Application Entry Point.
Flask REST API with CORS, SQLite persistence, and ML Pipeline.
Serves production frontend build when available.
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SECRET_KEY
from services.db import init_db
from ml.train import ensure_trained_model
from services.dataset_service import dataset_service
from routes.health import health_bp
from routes.dashboard import dashboard_bp
from routes.dataset import dataset_bp
from routes.analytics import analytics_bp
from routes.model import model_bp
from routes.predict import predict_bp
from routes.predictions import predictions_bp
from routes.auth import auth_bp
from routes.mailbox import mailbox_bp


def create_app() -> Flask:
    frontend_dist = Path(__file__).resolve().parent.parent / "dist"
    if not frontend_dist.exists():
        frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    static_folder = str(frontend_dist) if frontend_dist.exists() else None

    app = Flask(__name__, static_folder=static_folder)
    app.config["SECRET_KEY"] = SECRET_KEY

    # Enable CORS for all origins on API routes with exposed headers for file downloads
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        expose_headers=["Content-Disposition", "Content-Type", "Content-Length"],
        allow_headers=["Content-Type", "Authorization", "X-ProbMail-Token", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Initialize database schema
    try:
        from services.db import log_db_diagnostics
        log_db_diagnostics()
        init_db()
    except Exception as e:
        print(f"[ProbMail Startup] Database initialization warning: {e}", file=sys.stderr)

    # Automatically ensure primary model is trained and ready
    try:
        ensure_trained_model()
    except Exception as e:
        print(f"[ProbMail Startup] Note: Background model check: {e}", file=sys.stderr)

    # Register API Blueprints under /api prefix
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(dataset_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(model_bp, url_prefix="/api")
    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(predictions_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(mailbox_bp, url_prefix="/api")

    # Serve built frontend assets if present
    if frontend_dist.exists():
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path.startswith("api/"):
                return jsonify({"error": f"API endpoint '/{path}' not found."}), 404
            if path and (frontend_dist / path).exists():
                return send_from_directory(str(frontend_dist), path)
            return send_from_directory(str(frontend_dist), "index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"ProbMail Security Platform running at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
