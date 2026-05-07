"""
services/sentiment_service.py
Sentiment analysis using VADER (Valence Aware Dictionary and sEntiment Reasoner).

Why VADER?
   Purpose-built for social-media / short-form text
   Handles emoji, slang, ALL-CAPS, punctuation emphasis
   Zero external API calls - fully offline
   Sub-millisecond per comment - scales to thousands easily
"""

import logging
from collections import defaultdict
from typing import Literal
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from services.comment_utils import filter_comments

logger = logging.getLogger(__name__)

#  Singleton analyser (expensive to construct, safe to reuse across threads) 
_analyser = SentimentIntensityAnalyzer()

SentimentLabel = Literal["positive", "negative", "neutral"]

# VADER compound score thresholds (from the original paper)
_POS_THRESHOLD =  0.05
_NEG_THRESHOLD = -0.05


#  Public API 

def classify_comment(text: str) -> dict:
    """
    Analyse a single piece of text.

    Returns:
        {
          "label":   "positive" | "negative" | "neutral",
          "score":   float,   # compound score -1.0 … +1.0
          "scores":  { "neg": float, "neu": float, "pos": float, "compound": float }
        }
    """
    if not text or not text.strip():
        return {"label": "neutral", "score": 0.0, "scores": {}}

    scores   = _analyser.polarity_scores(text)
    compound = scores["compound"]

    if compound >= _POS_THRESHOLD:
        label: SentimentLabel = "positive"
    elif compound <= _NEG_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label":  label,
        "score":  round(compound, 4),
        "scores": {k: round(v, 4) for k, v in scores.items()},
    }


# def clean_comment(text: str) -> str:
#     """Clean and normalize raw comment text."""
#     import re
#     if not text:
#         return ''
#     text = text.stripe()
#     text = re.sub(r'http\S+', '', text)  # remove urls
#     text = re.sub(r'@\S+|#\S+', '', text)  # remove mentions/hashtags
#     text = re.sub(r'[!]{2,}', '!', text)  # normalize repeated punctuation
#     text = re.sub(r'[\s]+', '', text)   # collapse whitespaces
#     return text




def analyse_comments(raw_comments: list[dict]) -> dict:
    """
    Filter, clean, deduplicate, then run sentiment analysis over a list of
    comment dicts returned by youtube_service.fetch_comments_for_keyword().
 
    Pipeline:

    1. filter_comments()  — removes junk, strips URLs, deduplicates per-author,
                            converts hashtags to words, adds "cleaned_text" key
    2. classify_comment() — runs VADER on cleaned_text (NOT raw text)
    3. Each passing comment is mutated in-place to add a "sentiment" key.
       The original "text" field is preserved untouched for the frontend.

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
          "neutral":  [...top 5 by likeCount],
      }
    }
    """
    if not raw_comments:
        return _empty_result()

    # filter_comments() returns only comments worth analyzing, each with a "cleaned_text" key. Raw "text" is left untouched for frontend display.

    comments = filter_comments(raw_comments=raw_comments)

    if not comments:
        logger.info("All %d comments were filtered out before analysis.", len(raw_comments))
        return _empty_result()
    
    logger.info(
        "Analysing %d comments (%d filtered out of %d raw).",
        len(comments),
        len(raw_comments) - len(comments),
        len(raw_comments)
    )

    counts    = defaultdict(int)
    score_sum = 0.0
    date_map: dict[str, dict] = {}
    by_label: dict[str, list] = {"positive": [], "negative": [], "neutral": []}

    most_positive = {"score": -999, "comment": None}
    most_negative = {"score":  999, "comment": None}

    for comment in comments:
        cleaned_text   = comment.get("cleaned_text", "")
        result = classify_comment(cleaned_text)
        comment["sentiment"] = result

        label    = result["label"]
        compound = result["score"]

        counts[label] += 1
        score_sum      += compound

        # Track extremes
        if compound > most_positive["score"]:
            most_positive = {"score": compound, "comment": comment}
        if compound < most_negative["score"]:
            most_negative = {"score": compound, "comment": comment}

        # Group by date for trend chart
        date_key = (comment.get("publishedAt") or "")[:10] or "unknown"
        if date_key not in date_map:
            date_map[date_key] = {"date": date_key, "positive": 0, "negative": 0, "neutral": 0}
        date_map[date_key][label] += 1

        by_label[label].append(comment)

    total     = len(comments)
    avg_score = round(score_sum / total, 4) if total else 0.0

    # Sort by likeCount descending for top-comments per label
    for lbl in by_label:
        by_label[lbl].sort(key=lambda c: c.get("likeCount", 0), reverse=True)

    summary = {
        "total":              total,
        "positive":           counts["positive"],
        "negative":           counts["negative"],
        "neutral":            counts["neutral"],
        "avg_score":          avg_score,
        "positivePercent":    _pct(counts["positive"], total),
        "negativePercent":    _pct(counts["negative"], total),
        "neutralPercent":     _pct(counts["neutral"],  total),
        "mostPositiveComment": most_positive["comment"],
        "mostNegativeComment": most_negative["comment"],
    }

    trend = sorted(
        [v for k, v in date_map.items() if k != "unknown"],
        key=lambda x: x["date"],
    )

    # Sort full list: most-liked first
    comments_sorted = sorted(comments, key=lambda c: c.get("likeCount", 0), reverse=True)

    return {
        "comments":   comments_sorted,
        "summary":    summary,
        "trend":      trend,
        "topByLabel": {lbl: by_label[lbl][:5] for lbl in by_label},
    }


#  Helpers 

# percentage
def _pct(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total else 0.0


def _empty_result() -> dict:
    return {
        "comments": [],
        "summary": {
            "total": 0, "positive": 0, "negative": 0, "neutral": 0,
            "avg_score": 0.0,
            "positivePercent": 0.0, "negativePercent": 0.0, "neutralPercent": 0.0,
            "mostPositiveComment": None, "mostNegativeComment": None,
        },
        "trend": [],
        "topByLabel": {"positive": [], "negative": [], "neutral": []},
    }
