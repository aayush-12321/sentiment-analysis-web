"""
services/cache_service.py
PostgreSQL-backed persistent analysis cache.

Flow:
  1. Check in-memory Flask-Cache (fast, < 1ms)
  2. Check PostgreSQL AnalysisCache table (survives restarts / workers)
  3. On miss: run analysis, persist to both layers
"""

import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from app import cache, db
from models import AnalysisCache, SearchHistory

logger = logging.getLogger(__name__)


def make_cache_key(keyword: str, max_videos: int, max_comments: int, source: str = "youtube") -> str:
    """Stable, URL-safe cache key for a (keyword, params, source) quadruple."""
    raw = f"{keyword.lower().strip()}:v{max_videos}:c{max_comments}:s{source}"
    return "analysis:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_cached_analysis(cache_key: str) -> dict | None:
    """
    Look up a cached result. Returns the result dict or None.
    Checks memory cache first, then PostgreSQL.
    """
    # 1. Memory cache
    mem = cache.get(cache_key)
    if mem:
        logger.debug("Memory cache hit: %s", cache_key)
        return mem

    # 2. PostgreSQL
    try:
        row = AnalysisCache.query.filter_by(cache_key=cache_key).first()
        if row and not row.is_expired():
            result = row.result          # parsed from JSON column
            cache.set(cache_key, result) # backfill memory cache
            logger.info("DB cache hit: %s", cache_key)
            return result
        if row and row.is_expired():
            db.session.delete(row)
            db.session.commit()
    except Exception as exc:
        logger.warning("DB cache read failed: %s", exc)

    return None


def store_analysis(
    cache_key: str,
    keyword: str,
    result: dict,
    # ttl_seconds: int = 600,
    ttl_seconds: int = 6000,

) -> None:
    """
    Persist analysis result to memory cache and PostgreSQL.
    """
    # Memory cache
    cache.set(cache_key, result, timeout=ttl_seconds)

    # PostgreSQL
    expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    summary = result.get("summary", {})

    try:
        existing = AnalysisCache.query.filter_by(cache_key=cache_key).first()
        if existing:
            existing.result_json     = json.dumps(result)
            existing.expires_at      = expires
            existing.total_comments  = summary.get("total", 0)
            existing.positive_count  = summary.get("positive", 0)
            existing.negative_count  = summary.get("negative", 0)
            existing.neutral_count   = summary.get("neutral", 0)
            existing.avg_score       = summary.get("avg_score", 0.0)
        else:
            row = AnalysisCache(
                cache_key       = cache_key,
                keyword         = keyword,
                result_json     = json.dumps(result),
                expires_at      = expires,
                total_comments  = summary.get("total", 0),
                positive_count  = summary.get("positive", 0),
                negative_count  = summary.get("negative", 0),
                neutral_count   = summary.get("neutral", 0),
                avg_score       = summary.get("avg_score", 0.0),
            )
            db.session.add(row)
        db.session.commit()
        logger.info("Stored analysis for %r in DB (ttl=%ds)", keyword, ttl_seconds)
    except Exception as exc:
        logger.error("Failed to store analysis in DB: %s", exc)
        db.session.rollback()


def log_search(keyword: str, ip: str, cache_hit: bool, result_count: int) -> None:
    """Append a row to the search_history audit table (non-critical)."""
    import hashlib
    print(f"ip: {ip}")
    try:
        row = SearchHistory(
            keyword      = keyword,
            ip_hash      = hashlib.sha256(ip.encode()).hexdigest()[:16],
            cache_hit    = cache_hit,
            result_count = result_count,
        )
        db.session.add(row)
        db.session.commit()
    except Exception as exc:
        logger.warning("Could not log search history: %s", exc)
        db.session.rollback()
