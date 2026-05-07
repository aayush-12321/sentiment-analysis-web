"""
services/analyzers/base.py
Abstract base class that every sentiment analyzer must implement.

All analyzers must return a consistent dict shape from classify_comment():
    {
        "label":  "positive" | "negative" | "neutral",
        "score":  float,   # normalised confidence/polarity in [-1.0, +1.0]
        "scores": dict,    # raw model-specific scores
    }

NOTE: RoBERTa only has 2 labels (positive / negative).
      VADER produces all 3 (positive / negative / neutral).
      Callers (sentiment_service.py) must handle neutral counts being 0
      when using a 2-class model — the summary structure is identical,
      neutral will just always be 0.
"""

from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    """Interface every sentiment analyzer must satisfy."""

    @abstractmethod
    def classify_comment(self, text: str) -> dict:
        """
        Analyse a single piece of text and return a sentiment result.

        Args:
            text: Raw or pre-cleaned comment text.

        Returns:
            {
                "label":  str,   # "positive" | "negative" | "neutral"
                "score":  float, # scalar in [-1.0, 1.0]
                "scores": dict,  # model-specific breakdown
            }
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def supports_neutral(self) -> bool:
        """True if the model can produce a 'neutral' label."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name used in logs and health checks."""
        raise NotImplementedError
