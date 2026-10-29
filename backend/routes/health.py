import os
from datetime import datetime, timezone
from flask import Blueprint, jsonify
from ml.train import load_trained_pipeline
from services.db import _is_postgres_active

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    pipeline, metadata = load_trained_pipeline()
    db_engine = "postgresql" if _is_postgres_active() else "sqlite"
    return jsonify({
        "status": "healthy",
        "service": "ProbMail AI Email Security Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_loaded": pipeline is not None,
        "database": db_engine,
        "last_trained_at": metadata.get("trained_at") if metadata else None
    })
