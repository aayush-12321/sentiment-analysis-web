"""
app.py - Flask application factory
YouTube Brand Sentiment Dashboard
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

#     Shared extension instances            
cache = Cache()
db    = SQLAlchemy()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    #     Config                 
    app.config["SECRET_KEY"]          = os.getenv("FLASK_SECRET_KEY", "dev-insecure-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///sentiment_cache.db"   # SQLite fallback for local dev
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]       = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Cache: SimpleCache in dev; swap to RedisCache for multi-worker prod
    app.config["CACHE_TYPE"]            = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_TIMEOUT", 600))

    #     Extensions
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": [o.strip() for o in allowed_origins]}})

    cache.init_app(app)
    db.init_app(app)


    #     Blueprints
    from routes.sentiment import sentiment_bp
    from routes.health    import health_bp

    app.register_blueprint(sentiment_bp, url_prefix="/api")
    app.register_blueprint(health_bp,    url_prefix="/api")

    #     Create DB tables on first run              
    with app.app_context():
        from models import AnalysisCache  # noqa: F401 - registers with SQLAlchemy
        db.create_all()

    #     Eagerly initialise the sentiment analyzer                    ─
    # Triggers the console print immediately on startup so you can confirm
    # which model is active (VADER or RoBERTa) before any request arrives.
    from services.analyzer_factory import get_analyzer
    get_analyzer()

    return app
