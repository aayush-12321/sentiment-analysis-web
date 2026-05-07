"""
routes/sentiment.py
Sentiment analysis API endpoints.

  GET /api/analyze-brand   - full analysis for a keyword
  GET /api/top-comments    - filtered top comments from cache
  GET /api/history         - recent search keywords from DB
"""

import os
import logging
from flask import Blueprint, jsonify, request
from services.youtube_service   import fetch_comments_for_keyword
from services.sentiment_service import analyse_comments
from services.cache_service     import (
    make_cache_key, get_cached_analysis, store_analysis, log_search
)
from services.comment_utils import validate_keyword
from utils.validators import validate_keyword, clamp

logger        = logging.getLogger(__name__)
sentiment_bp  = Blueprint("sentiment", __name__)

_DEFAULT_MAX_VIDEOS   = int(os.getenv("MAX_VIDEOS", 5))
_DEFAULT_MAX_COMMENTS = int(os.getenv("MAX_COMMENTS_PER_VIDEO", 20))
_CACHE_TTL            = int(os.getenv("CACHE_TIMEOUT", 600))


@sentiment_bp.route("/analyze-brand", methods=["GET"])
def analyze_brand():
    """
    Fetch YouTube comments for *keyword* and return a full sentiment analysis.

    Query params:
        keyword      (required) - brand name or search term
        max_videos   (optional, 1-20, default 5)
        max_comments (optional, 1-100, default 20 per video)

    Success 200:
        {
          "keyword":    str,
          "cached":     bool,
          "comments":   [...],
          "summary":    { total, positive, negative, neutral,
                          avg_score, *Percent fields,
                          mostPositiveComment, mostNegativeComment },
          "trend":      [{ date, positive, negative, neutral }],
          "topByLabel": { positive: [...], negative: [...], neutral: [...] }
        }

    Errors:
        400 - bad keyword / params
        403 - YouTube API key invalid / quota exceeded
        404 - no comments found
        502 - YouTube upstream error
        500 - unexpected server error
    """
    keyword      = request.args.get("keyword", "").strip()
    max_videos   = clamp(request.args.get("max_videos"),   1, 20,  _DEFAULT_MAX_VIDEOS)
    max_comments = clamp(request.args.get("max_comments"), 1, 100, _DEFAULT_MAX_COMMENTS)

    err = validate_keyword(keyword)
    if err:
        return jsonify({"error": err}), 400
    
    

    cache_key = make_cache_key(keyword, max_videos, max_comments)

    #    Cache lookup 
    cached = get_cached_analysis(cache_key)
    if cached:
        log_search(keyword, _client_ip(), cache_hit=True, result_count=cached["summary"]["total"])
        return jsonify({"keyword": keyword, "cached": True, **cached}), 200

    #    Fetch from YouTube    
    try:
        comments = fetch_comments_for_keyword(
            keyword,
            max_videos=max_videos,
            max_comments_per_video=max_comments,
        )
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        logger.error("YouTube fetch error: %s", exc)
        return jsonify({"error": "Failed to reach YouTube. Please try again."}), 502
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        return jsonify({"error": "An unexpected server error occurred."}), 500

    if not comments:
        return jsonify({
            "error": (
                f"No comments found for '{keyword}'. "
                "Try a broader keyword or check your YouTube API quota."
            ) 
        }), 404

    #    Analyse     
    analysis = analyse_comments(comments)
    store_analysis(cache_key, keyword, analysis, ttl_seconds=_CACHE_TTL)
    log_search(keyword, _client_ip(), cache_hit=False, result_count=analysis["summary"]["total"])

    return jsonify({"keyword": keyword, "cached": False, **analysis}), 200


@sentiment_bp.route("/top-comments", methods=["GET"])
def top_comments():
    """
    Return top comments filtered by sentiment label.
    Requires a prior /analyze-brand call to warm the cache.

    Query params:
        keyword   (required)
        sentiment (optional) - positive | negative | neutral | all  (default: all)
        limit     (optional, 1-50, default: 10)
    """
    keyword   = request.args.get("keyword", "").strip()
    sentiment = request.args.get("sentiment", "all").lower()
    limit     = clamp(request.args.get("limit"), 1, 50, 10)

    err = validate_keyword(keyword)
    if err:
        return jsonify({"error": err}), 400

    if sentiment not in ("positive", "negative", "neutral", "all"):
        return jsonify({"error": "sentiment must be positive, negative, neutral, or all"}), 400

    cache_key = make_cache_key(keyword, _DEFAULT_MAX_VIDEOS, _DEFAULT_MAX_COMMENTS)
    cached = get_cached_analysis(cache_key)
    if not cached:
        return jsonify({
            "error": "No cached analysis found. Call /api/analyze-brand first."
        }), 404

    if sentiment == "all":
        comments = cached.get("comments", [])
    else:
        comments = cached.get("topByLabel", {}).get(sentiment, [])

    return jsonify({
        "keyword":   keyword,
        "sentiment": sentiment,
        "total":     len(comments),
        "comments":  comments[:limit],
    }), 200


@sentiment_bp.route("/history", methods=["GET"])
def search_history():
    """Return the 20 most recently searched unique keywords."""
    try:
        from models import SearchHistory
        from app import db
        rows = (
            db.session.query(SearchHistory.keyword)
            .order_by(SearchHistory.created_at.desc())
            .limit(100)
            .all()
        )
        # Deduplicate while preserving order
        seen, keywords = set(), []
        for (kw,) in rows:
            if kw not in seen:
                seen.add(kw)
                keywords.append(kw)
                if len(keywords) >= 20:
                    break
        return jsonify({"keywords": keywords}), 200
    except Exception as exc:
        logger.warning("History query failed: %s", exc)
        return jsonify({"keywords": []}), 200


#    Helpers       

def _client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0]
