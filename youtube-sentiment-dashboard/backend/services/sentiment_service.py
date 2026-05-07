"""
services/sentiment_service.py
Orchestrates filtering, sentiment classification, and result aggregation.

Supports three data sources:
  youtube  — YouTube comments via youtube_service
  reddit   — Reddit posts via reddit_service
  both     — Both sources merged with weighted aggregation

Analyzers:
  vader   — VADER (3-class: positive / negative / neutral) [default]
  roberta — Twitter-RoBERTa (2-class: positive / negative)
"""

import logging
from collections import defaultdict

from services.analyzer_factory import get_analyzer
from services.comment_utils import filter_comments

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def classify_comment(text: str) -> dict:
    """Classify a single text using the configured analyzer."""
    return get_analyzer().classify_comment(text)


def analyse_comments(raw_comments: list[dict], brand: str = "") -> dict:
    """
    Filter, clean, deduplicate, then run sentiment analysis over YouTube comments.

    Returns:
        { comments, summary, trend, topByLabel }
    """
    if not raw_comments:
        return _empty_result()

    comments = filter_comments(raw_comments=raw_comments, brand=brand)

    if not comments:
        logger.info("All %d comments filtered out.", len(raw_comments))
        return _empty_result()

    analyzer = get_analyzer()
    logger.info(
        "Analysing %d YouTube comments (%d filtered) using '%s'.",
        len(comments), len(raw_comments) - len(comments), analyzer.name,
    )

    return _run_analysis(comments, text_key="cleaned_text", analyzer=analyzer)


def analyse_reddit_posts(posts: list[dict], brand: str = "") -> dict:
    """
    Run sentiment analysis on Reddit posts (pre-filtered by reddit_service).

    Returns:
        { posts, summary, trend, topByLabel }
    """
    if not posts:
        return _empty_reddit_result()

    analyzer = get_analyzer()
    logger.info("Analysing %d Reddit posts using '%s'.", len(posts), analyzer.name)

    result = _run_analysis(posts, text_key="text", analyzer=analyzer)
    # Rename 'comments' key to 'posts' for Reddit
    result["posts"] = result.pop("comments")
    return result


def merge_analyses(
    yt_result: dict | None,
    reddit_result: dict | None,
    yt_weight: float = 0.5,
    reddit_weight: float = 0.5,
) -> dict:
    """
    Merge YouTube and Reddit analysis results into a single combined result.

    Returns the merged dict with an additional 'agreementScore' field.
    """
    yt  = yt_result     or _empty_result()
    rd  = reddit_result or _empty_reddit_result()

    yt_s = yt.get("summary", {})
    rd_s = rd.get("summary", {})

    yt_total = yt_s.get("total", 0)
    rd_total = rd_s.get("total", 0)
    total    = yt_total + rd_total

    # Weighted percentage aggregation
    def _wp(yt_val, rd_val):
        return round(yt_val * yt_weight + rd_val * reddit_weight, 1)

    pos_pct = _wp(yt_s.get("positivePercent", 0.0), rd_s.get("positivePercent", 0.0))
    neg_pct = _wp(yt_s.get("negativePercent", 0.0), rd_s.get("negativePercent", 0.0))
    neu_pct = _wp(yt_s.get("neutralPercent",  0.0), rd_s.get("neutralPercent",  0.0))
    avg_sc  = round(
        yt_s.get("avg_score", 0.0) * yt_weight +
        rd_s.get("avg_score", 0.0) * reddit_weight, 4
    )

    # Agreement: overlap between the two distributions (0–100)
    agreement = round(
        min(yt_s.get("positivePercent", 0.0), rd_s.get("positivePercent", 0.0)) +
        min(yt_s.get("negativePercent", 0.0), rd_s.get("negativePercent", 0.0)) +
        min(yt_s.get("neutralPercent",  0.0), rd_s.get("neutralPercent",  0.0)),
        1,
    )

    # Derive counts from percentages
    pos_count = round(total * pos_pct / 100) if total else 0
    neg_count = round(total * neg_pct / 100) if total else 0
    neu_count = max(0, total - pos_count - neg_count)

    dominant = max(
        {"positive": pos_pct, "negative": neg_pct, "neutral": neu_pct},
        key=lambda k: {"positive": pos_pct, "negative": neg_pct, "neutral": neu_pct}[k],
    )

    merged_summary = {
        "total":               total,
        "positive":            pos_count,
        "negative":            neg_count,
        "neutral":             neu_count,
        "avg_score":           avg_sc,
        "positivePercent":     pos_pct,
        "negativePercent":     neg_pct,
        "neutralPercent":      neu_pct,
        "dominantSentiment":   dominant,
        "mostPositiveComment": yt_s.get("mostPositiveComment") or rd_s.get("mostPositiveComment"),
        "mostNegativeComment": yt_s.get("mostNegativeComment") or rd_s.get("mostNegativeComment"),
        "analyzer":            yt_s.get("analyzer", ""),
        "supportsNeutral":     yt_s.get("supportsNeutral", True),
        "youtubeWeight":       yt_weight,
        "redditWeight":        reddit_weight,
        "youtubeSummary":      yt_s,
        "redditSummary":       rd_s,
    }

    # Tag each item with source and merge
    yt_comments = yt.get("comments", [])
    rd_posts    = rd.get("posts", [])
    for c in yt_comments: c.setdefault("source", "youtube")
    for p in rd_posts:    p.setdefault("source", "reddit")

    merged_comments = sorted(
        yt_comments + rd_posts,
        key=lambda x: x.get("likeCount", 0), reverse=True,
    )

    # Merge topByLabel
    yt_top = yt.get("topByLabel", {})
    rd_top = rd.get("topByLabel", {})
    merged_top = {
        lbl: sorted(
            (yt_top.get(lbl, []) + rd_top.get(lbl, []))[:10],
            key=lambda x: x.get("likeCount", 0), reverse=True,
        )[:5]
        for lbl in ("positive", "negative", "neutral")
    }

    # Merge trend
    trend_map: dict[str, dict] = {}
    for entry in yt.get("trend", []) + rd.get("trend", []):
        d = entry["date"]
        if d not in trend_map:
            trend_map[d] = {"date": d, "positive": 0, "negative": 0, "neutral": 0}
        for lbl in ("positive", "negative", "neutral"):
            trend_map[d][lbl] += entry.get(lbl, 0)
    merged_trend = sorted(trend_map.values(), key=lambda x: x["date"])

    return {
        "summary":        merged_summary,
        "comments":       merged_comments,
        "trend":          merged_trend,
        "topByLabel":     merged_top,
        "agreementScore": agreement,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_analysis(items: list[dict], text_key: str, analyzer) -> dict:
    """Core analysis loop shared by YouTube and Reddit pipelines."""
    counts    = defaultdict(int)
    score_sum = 0.0
    date_map: dict[str, dict] = {}
    by_label: dict[str, list] = {"positive": [], "negative": [], "neutral": []}
    most_positive = {"score": -999.0, "item": None}
    most_negative = {"score":  999.0, "item": None}

    for item in items:
        text   = item.get(text_key, "") or item.get("text", "") or item.get("title", "")
        result = analyzer.classify_comment(text)
        item["sentiment"] = result

        label    = result["label"]
        compound = result["score"]

        counts[label] += 1
        score_sum      += compound

        if compound > most_positive["score"]:
            most_positive = {"score": compound, "item": item}
        if compound < most_negative["score"]:
            most_negative = {"score": compound, "item": item}

        date_key = (item.get("publishedAt") or "")[:10] or "unknown"
        if date_key not in date_map:
            date_map[date_key] = {"date": date_key, "positive": 0, "negative": 0, "neutral": 0}
        date_map[date_key][label] += 1

        by_label[label].append(item)

    total     = len(items)
    avg_score = round(score_sum / total, 4) if total else 0.0

    for lbl in by_label:
        by_label[lbl].sort(key=lambda c: c.get("likeCount", 0), reverse=True)

    summary = {
        "total":               total,
        "positive":            counts["positive"],
        "negative":            counts["negative"],
        "neutral":             counts["neutral"],
        "avg_score":           avg_score,
        "positivePercent":     _pct(counts["positive"], total),
        "negativePercent":     _pct(counts["negative"], total),
        "neutralPercent":      _pct(counts["neutral"],  total),
        "mostPositiveComment": most_positive["item"],
        "mostNegativeComment": most_negative["item"],
        "analyzer":            analyzer.name,
        "supportsNeutral":     analyzer.supports_neutral,
    }

    trend = sorted(
        [v for k, v in date_map.items() if k != "unknown"],
        key=lambda x: x["date"],
    )

    comments_sorted = sorted(items, key=lambda c: c.get("likeCount", 0), reverse=True)

    return {
        "comments":   comments_sorted,
        "summary":    summary,
        "trend":      trend,
        "topByLabel": {lbl: by_label[lbl][:5] for lbl in by_label},
    }


def _pct(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total else 0.0


def _empty_result() -> dict:
    analyzer = get_analyzer()
    base_summary = {
        "total": 0, "positive": 0, "negative": 0, "neutral": 0,
        "avg_score": 0.0,
        "positivePercent": 0.0, "negativePercent": 0.0, "neutralPercent": 0.0,
        "mostPositiveComment": None, "mostNegativeComment": None,
        "analyzer": analyzer.name, "supportsNeutral": analyzer.supports_neutral,
    }
    return {
        "comments": [], "summary": base_summary,
        "trend": [], "topByLabel": {"positive": [], "negative": [], "neutral": []},
    }


def _empty_reddit_result() -> dict:
    base = _empty_result()
    base["posts"] = base.pop("comments")
    return base
