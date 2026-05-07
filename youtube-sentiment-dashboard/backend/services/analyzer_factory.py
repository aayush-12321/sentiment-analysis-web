"""
services/analyzer_factory.py
Returns the configured sentiment analyzer singleton.

Switch analyzers by setting SENTIMENT_MODEL in your .env:

    SENTIMENT_MODEL=vader     # default — fast, 3-class (pos/neg/neutral)
    SENTIMENT_MODEL=roberta   # local Twitter-RoBERTa, 2-class (pos/neg)

The singleton is built once on first call and reused for the lifetime
of the process (thread-safe for reads after initialisation).
"""

import logging
import os

from services.analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)

_SUPPORTED_MODELS = ("vader", "roberta")

# Process-level singleton
_analyzer_instance: BaseAnalyzer | None = None


def get_analyzer() -> BaseAnalyzer:
    """
    Return the active sentiment analyzer.

    The analyzer is built lazily on the first call and cached.
    Subsequent calls return the same instance — no re-initialisation cost.
    """
    global _analyzer_instance

    if _analyzer_instance is not None:
        return _analyzer_instance

    model_name = os.getenv("SENTIMENT_MODEL", "vader").strip().lower()

    if model_name not in _SUPPORTED_MODELS:
        logger.warning(
            "Unknown SENTIMENT_MODEL=%r — falling back to 'vader'. "
            "Supported values: %s",
            model_name,
            ", ".join(_SUPPORTED_MODELS),
        )
        model_name = "vader"

    # Explicit print for testing as requested
    print(f"\n{'='*50}\n[SENTIMENT SYSTEM] Loading model: {model_name.upper()}\n{'='*50}\n")
    logger.info("Initialising sentiment analyzer: %s", model_name)

    if model_name == "roberta":
        from services.analyzers.roberta_analyzer import RobertaAnalyzer
        _analyzer_instance = RobertaAnalyzer()
    else:
        from services.analyzers.vader_analyzer import VaderAnalyzer
        _analyzer_instance = VaderAnalyzer()

    logger.info(
        "Analyzer '%s' ready (supports_neutral=%s).",
        _analyzer_instance.name,
        _analyzer_instance.supports_neutral,
    )
    return _analyzer_instance
