"""
services/analyzers/vader_analyzer.py
VADER-based sentiment analyzer — wraps the existing VADER logic.

Produces 3 labels: positive / negative / neutral.
"""

import logging
from typing import Literal

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from services.analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)

# VADER compound score thresholds (from the original paper)
_POS_THRESHOLD =  0.05
_NEG_THRESHOLD = -0.05

SentimentLabel = Literal["positive", "negative", "neutral"]


class VaderAnalyzer(BaseAnalyzer):
    """
    Sentiment analyzer backed by VADER.

    VADER is purpose-built for social-media / short-form text:
      - Handles emoji, slang, ALL-CAPS, punctuation emphasis
      - Zero external API calls — fully offline
      - Sub-millisecond per comment — scales to thousands easily
    """

    def __init__(self) -> None:
        # SentimentIntensityAnalyzer is expensive to construct; build once.
        self._analyser = SentimentIntensityAnalyzer()
        logger.info("VaderAnalyzer initialised.")

    # ── BaseAnalyzer interface ────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "vader"

    @property
    def supports_neutral(self) -> bool:
        return True

    def classify_comment(self, text: str) -> dict:
        """
        Analyse a single piece of text with VADER.

        Returns:
            {
                "label":  "positive" | "negative" | "neutral",
                "score":  float,   # compound score in [-1.0, +1.0]
                "scores": { "neg": float, "neu": float,
                            "pos": float, "compound": float }
            }
        """
        if not text or not text.strip():
            return {"label": "neutral", "score": 0.0, "scores": {}}

        scores   = self._analyser.polarity_scores(text)
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
