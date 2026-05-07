"""
services/analyzers/roberta_analyzer.py
Twitter-RoBERTa-based sentiment analyzer.

The locally trained model has exactly 2 output classes:
    0 → negative
    1 → positive

A synthetic 'neutral' class is derived from the model's confidence:
    score = p_positive - p_negative  ∈ [-1.0, +1.0]

    |score| >= ROBERTA_NEUTRAL_THRESHOLD → positive or negative
    |score| <  ROBERTA_NEUTRAL_THRESHOLD → neutral  (model is uncertain)

Default threshold: 0.2 (configurable via ROBERTA_NEUTRAL_THRESHOLD in .env)

Model files are loaded from ROBERTA_MODEL_PATH (env var).
The model is loaded lazily on first use and cached as a singleton to
avoid reloading on every request.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from services.analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)

# ── Module-level singletons (loaded once per process) 
_tokenizer = None
_model     = None
_label_map: dict[str, str] = {}   # e.g. {"0": "negative", "1": "positive"}


def _get_model_path() -> Path:
    """Resolve model directory from env var, with a sensible default."""
    raw = os.getenv("ROBERTA_MODEL_PATH", "")
    if raw:
        p = Path(raw)
        if p.is_absolute():
            return p
        # Relative path: resolve from backend directory (location of this file's parent chain)
        backend_dir = Path(__file__).resolve().parent.parent.parent
        return (backend_dir / p).resolve()

    # Default: look for a 'models' directory at the root (d:/sentimentscope/models)
    backend_dir = Path(__file__).resolve().parent.parent.parent
    # backend_dir is .../youtube-sentiment-dashboard/backend
    # .parent is .../youtube-sentiment-dashboard
    # .parent.parent is .../sentimentscope
    return (backend_dir.parent.parent / "models").resolve()


def _load_artifacts() -> None:
    """Load tokenizer, model, and label map from disk (called once)."""
    global _tokenizer, _model, _label_map

    if _model is not None:
        return  # already loaded

    try:
        # Import heavy deps here so the server starts even if transformers
        # is not installed (VADER will be used instead).
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch  # noqa: F401 — imported to confirm availability
    except ImportError as exc:
        raise ImportError(
            "transformers and torch are required for the RoBERTa analyzer. "
            "Install them with: pip install transformers torch"
        ) from exc

    model_path = _get_model_path()
    logger.info("Loading RoBERTa model from: %s", model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model directory not found: {model_path}. "
            "Set ROBERTA_MODEL_PATH in your .env to the correct path."
        )

    # Load label map
    label_map_path = model_path / "label_map.json"
    if label_map_path.exists():
        with open(label_map_path, "r", encoding="utf-8") as f:
            _label_map = json.load(f)
        logger.info("Label map loaded: %s", _label_map)
    else:
        # Fallback: assume {0: negative, 1: positive}
        _label_map = {"0": "negative", "1": "positive"}
        logger.warning(
            "label_map.json not found at %s — using default {0: negative, 1: positive}",
            label_map_path,
        )

    _tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    _model     = AutoModelForSequenceClassification.from_pretrained(str(model_path))
    _model.eval()

    logger.info(
        "RoBERTa model loaded successfully. Classes: %s",
        list(_label_map.values()),
    )


class RobertaAnalyzer(BaseAnalyzer):
    """
    Sentiment analyzer backed by a locally fine-tuned Twitter-RoBERTa model.

    - 2 output classes: negative (0), positive (1)
    - Neutral is derived from low-confidence predictions (|score| < ROBERTA_NEUTRAL_THRESHOLD)
    - Uses softmax probabilities; score = p_positive - p_negative ∈ [-1.0, +1.0]
    - Model is loaded once and cached for the lifetime of the process
    """

    def __init__(self) -> None:
        _load_artifacts()   # idempotent — only runs on first instantiation
        logger.info("RobertaAnalyzer ready.")

    # ── BaseAnalyzer interface 

    @property
    def name(self) -> str:
        return "roberta"

    @property
    def supports_neutral(self) -> bool:
        # We derive a neutral label from low-confidence predictions
        return True

    @property
    def _neutral_threshold(self) -> float:
        """Minimum |score| required to call a result positive/negative.
        If |score| is below this, the comment is labelled neutral.
        Configurable via ROBERTA_NEUTRAL_THRESHOLD in .env (default: 0.2).
        """
        try:
            return float(os.getenv("ROBERTA_NEUTRAL_THRESHOLD", "0.2"))
        except ValueError:
            return 0.2

    def classify_comment(self, text: str) -> dict:
        """
        Analyse a single piece of text with the RoBERTa model.

        Label assignment:
            |score| >= ROBERTA_NEUTRAL_THRESHOLD → "positive" or "negative"
            |score| <  ROBERTA_NEUTRAL_THRESHOLD → "neutral"  (low confidence)

        Returns:
            {
                "label":  "positive" | "negative" | "neutral",
                "score":  float,   # p_positive - p_negative ∈ [-1.0, +1.0]
                "scores": { "negative": float, "positive": float }
            }
        """
        import torch
        import torch.nn.functional as F

        if not text or not text.strip():
            return {"label": "neutral", "score": 0.0, "scores": {}}

        # Truncate to model's max token length
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        with torch.no_grad():
            logits = _model(**inputs).logits          # shape: (1, num_classes)

        probs = F.softmax(logits, dim=-1).squeeze()  # shape: (num_classes,)

        # Map each index to its label name
        raw_scores: dict[str, float] = {}
        for idx, prob in enumerate(probs.tolist()):
            label_name = _label_map.get(str(idx), str(idx))
            raw_scores[label_name] = round(prob, 4)

        # Scalar score: positive probability minus negative probability
        p_pos = raw_scores.get("positive", 0.0)
        p_neg = raw_scores.get("negative", 0.0)
        score = round(p_pos - p_neg, 4)   # ∈ [-1.0, +1.0]

        # Apply neutral zone: if confidence difference is below threshold,
        # the model is uncertain — label it neutral instead of forcing binary.
        threshold = self._neutral_threshold
        if abs(score) < threshold:
            label = "neutral"
        elif score >= threshold:
            label = "positive"
        else:
            label = "negative"

        return {
            "label":  label,
            "score":  score,
            "scores": raw_scores,
        }
