"""
models.py — SQLAlchemy ORM models
Stores analysis results in PostgreSQL so results survive server restarts
and are queryable across workers.
"""

import json
from datetime import datetime, timezone
from app import db


class AnalysisCache(db.Model):
    """
    Persists a full sentiment-analysis result keyed by (keyword, params).
    Acts as a durable cache that survives process restarts, unlike SimpleCache.
    """

    __tablename__ = "analysis_cache"

    id         = db.Column(db.Integer, primary_key=True)
    cache_key  = db.Column(db.String(255), unique=True, nullable=False, index=True)
    keyword    = db.Column(db.String(100), nullable=False, index=True)
    result_json = db.Column(db.Text, nullable=False)   # full JSON blob
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    #  Summary columns for quick aggregation queries 
    total_comments   = db.Column(db.Integer, default=0)
    positive_count   = db.Column(db.Integer, default=0)
    negative_count   = db.Column(db.Integer, default=0)
    neutral_count    = db.Column(db.Integer, default=0)
    avg_score        = db.Column(db.Float,   default=0.0)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    @property
    def result(self) -> dict:
        return json.loads(self.result_json)

    def __repr__(self) -> str:
        return f"<AnalysisCache keyword={self.keyword!r} total={self.total_comments}>"


class SearchHistory(db.Model):
    """
    Lightweight audit log of every search request.
    Useful for analytics: which brands get searched most often?
    """

    __tablename__ = "search_history"

    id         = db.Column(db.Integer, primary_key=True)
    keyword    = db.Column(db.String(100), nullable=False, index=True)
    ip_hash    = db.Column(db.String(64))   # hashed for privacy
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cache_hit  = db.Column(db.Boolean, default=False)
    result_count = db.Column(db.Integer, default=0)

    def __repr__(self) -> str:
        return f"<SearchHistory keyword={self.keyword!r} hit={self.cache_hit}>"
