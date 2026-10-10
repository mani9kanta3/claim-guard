from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db
from app.services.ml_scorer import is_model_loaded

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "down"

    status_code = 200 if database == "ok" else 503
    return jsonify(
        {
            "status": "ok" if database == "ok" else "error",
            "database": database,
            "model_loaded": is_model_loaded(),
        }
    ), status_code
