"""
routes/sentiment.py
Sentiment analysis API endpoints.

  GET /api/analyze-brand   — full multi-source analysis
  GET /api/top-comments    — filtered top comments from cache
  GET /api/history         — recent search keywords from DB

Query params for /api/analyze-brand:
  keyword         (required)
  source          (optional) youtube | reddit | both   [default: youtube]
  max_videos      (optional, 1-20,  default 5)
  max_comments    (optional, 1-100, default 20)
  include_reddit_comments  (optional, true|false, default true)
"""

import os
import logging
from flask import Blueprint, jsonify, request
from services.youtube_service   import fetch_comments_for_keyword
from services.reddit_service    import fetch_reddit_posts, fetch_posts_with_comments
from services.sentiment_service import (
    analyse_comments,
    analyse_reddit_posts,
    analyse_reddit_with_comments,
    merge_analyses,
)
from services.cache_service     import (
    make_cache_key, get_cached_analysis, store_analysis, log_search
)
from utils.validators import validate_keyword, clamp

logger       = logging.getLogger(__name__)
sentiment_bp = Blueprint("sentiment", __name__)

_DEFAULT_MAX_VIDEOS   = int(os.getenv("MAX_VIDEOS", 5))
_DEFAULT_MAX_COMMENTS = int(os.getenv("MAX_COMMENTS_PER_VIDEO", 20))
_CACHE_TTL            = int(os.getenv("CACHE_TIMEOUT", 600))

_VALID_SOURCES = {"youtube", "reddit", "both"}


@sentiment_bp.route("/analyze-brand", methods=["GET"])
def analyze_brand():
    """
    Multi-source brand sentiment analysis.

    Success 200:
        {
          keyword, source, cached,
          summary, comments, trend, topByLabel,
          # when source=reddit or both:
          reddit: {
            summary, posts, comments, trend, topByLabel,
            post_sentiment, comment_sentiment
          },
          # when source=both:
          youtube: { summary, comments, trend, topByLabel },
          agreementScore: float
        }
    """
    keyword      = request.args.get("keyword", "").strip()
    max_videos   = clamp(request.args.get("max_videos"),   1, 20,  _DEFAULT_MAX_VIDEOS)
    max_comments = clamp(request.args.get("max_comments"), 1, 100, _DEFAULT_MAX_COMMENTS)
    source       = request.args.get("source", "youtube").lower().strip()
    include_reddit_comments = request.args.get(
        "include_reddit_comments", "true"
    ).lower() != "false"

    if source not in _VALID_SOURCES:
        source = "youtube"

    err = validate_keyword(keyword)
    if err:
        return jsonify({"error": err}), 400

    cache_key = make_cache_key(keyword, max_videos, max_comments, source)

    # ── Cache lookup ───────────────────────────────────────────────────────────
    cached = get_cached_analysis(cache_key)
    if cached:
        log_search(keyword, _client_ip(), cache_hit=True,
                   result_count=cached.get("summary", {}).get("total", 0))
        return jsonify({"keyword": keyword, "source": source, "cached": True, **cached}), 200

    # ── Fetch YouTube ──────────────────────────────────────────────────────────
    yt_result = None
    if source in ("youtube", "both"):
        try:
            comments = fetch_comments_for_keyword(
                keyword,
                max_videos=max_videos,
                max_comments_per_video=max_comments,
            )
            if comments:
                yt_result = analyse_comments(comments, brand=keyword)
            elif source == "youtube":
                return jsonify({
                    "error": (
                        f"No comments found for '{keyword}'. "
                        "Try a broader keyword or check your YouTube API quota."
                    )
                }), 404
        except PermissionError as exc:
            if source == "youtube":
                return jsonify({"error": str(exc)}), 403
            logger.warning("YouTube permission error in 'both' mode: %s", exc)
        except (ValueError, RuntimeError) as exc:
            if source == "youtube":
                return jsonify({"error": str(exc)}), 502
            logger.warning("YouTube fetch failed in 'both' mode: %s", exc)
        except Exception as exc:
            logger.exception("Unexpected YouTube error: %s", exc)
            if source == "youtube":
                return jsonify({"error": "An unexpected server error occurred."}), 500

    # ── Fetch Reddit ───────────────────────────────────────────────────────────
    reddit_result = None
    if source in ("reddit", "both"):
        try:
            if include_reddit_comments:
                # Fetch posts + comments together
                posts, reddit_comments = fetch_posts_with_comments(
                    keyword,
                    max_posts=max_videos,
                    max_comments_per_post=min(max_comments, 20),
                )
                if posts or reddit_comments:
                    reddit_result = analyse_reddit_with_comments(
                        posts, reddit_comments, brand=keyword
                    )
                elif source == "reddit":
                    return jsonify({
                        "error": f"No Reddit posts found for '{keyword}'. Try a different brand name."
                    }), 404
            else:
                # Posts only (fast mode)
                posts = fetch_reddit_posts(keyword, max_posts=max_videos)
                if posts:
                    reddit_result = analyse_reddit_posts(posts, brand=keyword)
                elif source == "reddit":
                    return jsonify({
                        "error": f"No Reddit posts found for '{keyword}'. Try a different brand name."
                    }), 404

        except RuntimeError as exc:
            if source == "reddit":
                return jsonify({"error": str(exc)}), 502
            logger.warning("Reddit fetch failed in 'both' mode: %s", exc)
        except Exception as exc:
            logger.exception("Unexpected Reddit error: %s", exc)
            if source == "reddit":
                return jsonify({"error": "Reddit fetch failed unexpectedly."}), 500

    # ── Build response ─────────────────────────────────────────────────────────
    if source == "youtube":
        if not yt_result:
            return jsonify({"error": f"No data found for '{keyword}'."}), 404
        payload = yt_result
        extra   = {}

    elif source == "reddit":
        if not reddit_result:
            return jsonify({"error": f"No data found for '{keyword}'."}), 404

        # For reddit-only: use all_items (posts+comments) as main comments list
        all_reddit_items = reddit_result.get("all_items", reddit_result.get("posts", []))
        payload = {
            "comments":   all_reddit_items,
            "summary":    reddit_result["summary"],
            "trend":      reddit_result["trend"],
            "topByLabel": reddit_result["topByLabel"],
        }
        extra = {"reddit": reddit_result}

    else:  # both
        if not yt_result and not reddit_result:
            return jsonify({"error": f"No data found for '{keyword}' from any source."}), 404

        merged = merge_analyses(yt_result, reddit_result)
        payload = {
            "comments":   merged["comments"],
            "summary":    merged["summary"],
            "trend":      merged["trend"],
            "topByLabel": merged["topByLabel"],
        }
        extra = {
            "youtube":        yt_result     or {},
            "reddit":         reddit_result or {},
            "agreementScore": merged["agreementScore"],
        }

    full_result = {**payload, **extra}
    store_analysis(cache_key, keyword, full_result, ttl_seconds=_CACHE_TTL)
    log_search(keyword, _client_ip(), cache_hit=False,
               result_count=payload["summary"]["total"])

    return jsonify({
        "keyword": keyword,
        "source":  source,
        "cached":  False,
        **full_result,
    }), 200


@sentiment_bp.route("/top-comments", methods=["GET"])
def top_comments():
    """Return top comments/posts filtered by sentiment label."""
    keyword   = request.args.get("keyword", "").strip()
    sentiment = request.args.get("sentiment", "all").lower()
    limit     = clamp(request.args.get("limit"), 1, 50, 10)
    source    = request.args.get("source", "youtube").lower().strip()
    if source not in _VALID_SOURCES:
        source = "youtube"

    err = validate_keyword(keyword)
    if err:
        return jsonify({"error": err}), 400

    if sentiment not in ("positive", "negative", "neutral", "all"):
        return jsonify({"error": "sentiment must be positive, negative, neutral, or all"}), 400

    cache_key = make_cache_key(keyword, _DEFAULT_MAX_VIDEOS, _DEFAULT_MAX_COMMENTS, source)
    cached    = get_cached_analysis(cache_key)
    if not cached:
        return jsonify({
            "error": "No cached analysis found. Call /api/analyze-brand first."
        }), 404

    if sentiment == "all":
        items = cached.get("comments", [])
    else:
        items = cached.get("topByLabel", {}).get(sentiment, [])

    return jsonify({
        "keyword":   keyword,
        "sentiment": sentiment,
        "total":     len(items),
        "comments":  items[:limit],
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _client_ip() -> str:
    return request.headers.get(
        "X-Forwarded-For", request.remote_addr or "unknown"
    ).split(",")[0]
