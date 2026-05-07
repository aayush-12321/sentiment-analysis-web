"""
routes/health.py
Health-check endpoint — used by Docker, Nginx, and load balancers.
"""

import os
from flask import Blueprint, jsonify
from app import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Returns 200 with service status info."""
    db_ok = True
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db_ok = False

    return jsonify({
        "status":              "ok",
        "service":             "YouTube Brand Sentiment API",
        "version":             "1.0.0",
        "database":            "connected" if db_ok else "unavailable",
        "youtube_key_present": bool(os.getenv("YOUTUBE_API_KEY", "").strip()),
    }), 200
