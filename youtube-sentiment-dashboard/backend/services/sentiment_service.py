"""
services/sentiment_service.py
Orchestrates comment filtering, sentiment classification, and result aggregation.

The actual classification is delegated to whichever analyzer is selected via
the SENTIMENT_MODEL environment variable (see services/analyzer_factory.py).

Supported analyzers
-------------------
  vader   — VADER (3-class: positive / negative / neutral)  [default]
  roberta — Twitter-RoBERTa (2-class: positive / negative)

When using RoBERTa, the 'neutral' bucket in every result will always be 0.
The response structure is identical regardless of the analyzer chosen so the
frontend does not need to change.

Brand filtering
---------------
The `brand` parameter propagates through the pipeline so that
``filter_comments()`` can call ``is_comment_relevant(brand, text)``
and discard comments that are clearly unrelated to the searched brand.
"""

import logging
from collections import defaultdict

from services.analyzer_factory import get_analyzer
from services.comment_utils import filter_comments

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def classify_comment(text: str) -> dict:
    """
    Classify a single piece of text using the configured analyzer.

    Returns:
        {
            "label":  "positive" | "negative" | "neutral",
            "score":  float,   # scalar in [-1.0, +1.0]
            "scores": dict,    # model-specific raw scores
        }

    Note: When SENTIMENT_MODEL=roberta the label will never be "neutral"
          because that model was trained on only 2 classes.
    """
    analyzer = get_analyzer()
    return analyzer.classify_comment(text)


def analyse_comments(raw_comments: list[dict], brand: str = "") -> dict:
    """
    Filter, clean, deduplicate, then run sentiment analysis over a list of
    comment dicts returned by youtube_service.fetch_comments_for_keyword().

    Pipeline:
        1. filter_comments(brand) — removes junk, strips URLs, deduplicates
                                     per-author, converts hashtags to words,
                                     checks brand relevance, adds "cleaned_text".
        2. classify_comment()     — delegates to the active analyzer (VADER or RoBERTa).
        3. Each passing comment is mutated in-place to add a "sentiment" key.
           The original "text" field is preserved for the frontend.

    Parameters
    ----------
    raw_comments : list[dict]
        Comments as returned by fetch_comments_for_keyword().
    brand : str, optional
        Brand name entered by the user.  Passed to filter_comments() so
        that brand-irrelevant comments are dropped before classification.

    Returns:
    {
      "comments": [ ...enriched comment dicts... ],
      "summary": {
          total, positive, negative, neutral, avg_score,
          positivePercent, negativePercent, neutralPercent,
          mostPositiveComment, mostNegativeComment
      },
      "trend": [
          { "date": "YYYY-MM-DD", "positive": int, "negative": int, "neutral": int },
          ...sorted by date...
      ],
      "topByLabel": {
          "positive": [...top 5 by likeCount],
          "negative": [...top 5 by likeCount],
          "neutral":  [...top 5 by likeCount],   # always [] when using RoBERTa
      }
    }
    """
    if not raw_comments:
        return _empty_result()

    # filter_comments() returns only comments worth analysing,
    # each with a "cleaned_text" key. Raw "text" is left untouched for the frontend.
    # Passing brand= enables the brand-relevance comment filter.
    comments = filter_comments(raw_comments=raw_comments, brand=brand)

    if not comments:
        logger.info(
            "All %d comments were filtered out before analysis.",
            len(raw_comments),
        )
        return _empty_result()

    analyzer = get_analyzer()
    logger.info(
        "Analysing %d comments (%d filtered out of %d raw) using '%s'.",
        len(comments),
        len(raw_comments) - len(comments),
        len(raw_comments),
        analyzer.name,
    )

    counts    = defaultdict(int)
    score_sum = 0.0
    date_map: dict[str, dict] = {}
    by_label: dict[str, list] = {"positive": [], "negative": [], "neutral": []}

    most_positive = {"score": -999.0, "comment": None}
    most_negative = {"score":  999.0, "comment": None}

    for comment in comments:
        cleaned_text     = comment.get("cleaned_text", "")
        result           = analyzer.classify_comment(cleaned_text)
        comment["sentiment"] = result

        label    = result["label"]
        compound = result["score"]

        counts[label] += 1
        score_sum      += compound

        # Track sentiment extremes
        if compound > most_positive["score"]:
            most_positive = {"score": compound, "comment": comment}
        if compound < most_negative["score"]:
            most_negative = {"score": compound, "comment": comment}

        # Group by publication date for the trend chart
        date_key = (comment.get("publishedAt") or "")[:10] or "unknown"
        if date_key not in date_map:
            date_map[date_key] = {
                "date": date_key, "positive": 0, "negative": 0, "neutral": 0
            }
        date_map[date_key][label] += 1

        by_label[label].append(comment)

    total     = len(comments)
    avg_score = round(score_sum / total, 4) if total else 0.0

    # Sort each label bucket by likeCount for top-comment selection
    for lbl in by_label:
        by_label[lbl].sort(key=lambda c: c.get("likeCount", 0), reverse=True)

    summary = {
        "total":               total,
        "positive":            counts["positive"],
        "negative":            counts["negative"],
        "neutral":             counts["neutral"],    # 0 when using RoBERTa
        "avg_score":           avg_score,
        "positivePercent":     _pct(counts["positive"], total),
        "negativePercent":     _pct(counts["negative"], total),
        "neutralPercent":      _pct(counts["neutral"],  total),  # 0.0 for RoBERTa
        "mostPositiveComment": most_positive["comment"],
        "mostNegativeComment": most_negative["comment"],
        # Expose which model produced this analysis (useful for the frontend)
        "analyzer":            analyzer.name,
        "supportsNeutral":     analyzer.supports_neutral,
    }

    trend = sorted(
        [v for k, v in date_map.items() if k != "unknown"],
        key=lambda x: x["date"],
    )

    # Full list sorted by most-liked first
    comments_sorted = sorted(
        comments, key=lambda c: c.get("likeCount", 0), reverse=True
    )

    return {
        "comments":   comments_sorted,
        "summary":    summary,
        "trend":      trend,
        "topByLabel": {lbl: by_label[lbl][:5] for lbl in by_label},
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total else 0.0


def _empty_result() -> dict:
    analyzer = get_analyzer()
    return {
        "comments": [],
        "summary": {
            "total": 0, "positive": 0, "negative": 0, "neutral": 0,
            "avg_score": 0.0,
            "positivePercent": 0.0, "negativePercent": 0.0, "neutralPercent": 0.0,
            "mostPositiveComment": None, "mostNegativeComment": None,
            "analyzer":        analyzer.name,
            "supportsNeutral": analyzer.supports_neutral,
        },
        "trend": [],
        "topByLabel": {"positive": [], "negative": [], "neutral": []},
    }
