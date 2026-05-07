"""
comment_utils.py

YouTube Brand Sentiment Dashboard - Comment Cleaning & Keyword Validation


Provides two public functions for use in sentiment_service.py and
routes/sentiment.py:

    clean_comment_for_analysis(text)  ->  Optional[str]
    validate_keyword(keyword)         ->  Optional[str]

Plus one convenience helper:

    filter_comments(raw_comments)     ->  List[dict]
        Accepts a list of raw comment dicts (must have a "text" key) and
        returns only those that pass all filters, each enriched with a
        "cleaned_text" key ready for the sentiment model.

Design principles

• Original text is NEVER mutated - the frontend always shows the raw comment.
• clean_comment_for_analysis returns None to signal "skip this comment entirely"
  (e.g. URL-only comments, gibberish, too short after cleaning).
• All regex patterns are pre-compiled at module level for performance.
• Every decision is logged at DEBUG level so it is easy to trace in production.

Author : (your name / team)
Version: 1.0.0
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata
from typing import Any, Optional

#  Logger 

logger = logging.getLogger(__name__)

#  Pre-compiled regex patterns 

# Full URLs (http/https/ftp, bare www., and common shorteners)
_URL_PATTERN = re.compile(
    r"(?:"
    r"https?://[^\s]+"                    # http:// or https://
    r"|ftp://[^\s]+"                      # ftp://
    r"|www\.[^\s]+"                       # www. (no scheme)
    r"|(?:bit\.ly|t\.co|goo\.gl|tinyurl\.com|youtu\.be|ow\.ly)/[^\s]*"  # shorteners
    r")",
    re.IGNORECASE,
)

# @mentions and #hashtags
_MENTION_PATTERN = re.compile(r"@\w+")
_HASHTAG_PATTERN = re.compile(r"#\w+")

# Repeated punctuation / filler characters (e.g. "!!!!!!", "......", "lolololol")
_REPEATED_PUNCT_PATTERN = re.compile(r"([!?.,;:\-_*~`^])\1{3,}")
_REPEATED_CHAR_PATTERN = re.compile(r"(\w)\1{4,}")      # aaaaa → aaa (keep 3)

# Excessive caps: more than 80% uppercase words → likely spam
_WORD_SPLIT_PATTERN = re.compile(r"\s+")

# HTML entities and invisible / zero-width characters
_ZWS_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060]"
)

# Minimum meaningful token length after cleaning
_MIN_CLEANED_LENGTH = 3

# Maximum fraction of uppercase words before we flag the comment as ALL-CAPS spam
_MAX_CAPS_FRACTION = 0.85


#  Public API 
def clean_comment_for_analysis(text: str) -> Optional[str]:
    """
    Clean a YouTube comment and return a version suitable for sentiment analysis.

    Parameters
    ----------
    text : str
        Raw comment text as returned by the YouTube Data API.

    Returns
    -------
    str
        Cleaned text ready to be passed to the sentiment model.
    None
        If the comment should be skipped entirely (URL present, too short,
        gibberish, all-caps spam, etc.).

    Notes
    -----
    • The *original* ``text`` is never modified - this function only produces
      a cleaned copy.
    • Returning ``None`` means "do not analyze this comment at all".
    • Returning a non-empty string means "analyze this string, display the
      original ``text`` in the frontend".
    """
    if not isinstance(text, str):
        logger.debug("Skipping non-string comment: %r", text)
        return None

    #  Step 1: Decode HTML entities (YouTube API sometimes encodes & → &amp;)
    cleaned = html.unescape(text)

    #  Step 2: Remove zero-width / invisible characters
    cleaned = _ZWS_PATTERN.sub("", cleaned)

    #  Step 3: Reject comments that contain ANY URL
    #    Rationale: URL-only or URL-heavy comments carry no brand sentiment signal.
    if _URL_PATTERN.search(cleaned):
        logger.debug("Skipping comment with URL: %.60r…", text)
        return None

    #  Step 4: Remove @mentions and #hashtags from cleaned copy
    cleaned = _MENTION_PATTERN.sub("", cleaned)
    cleaned = _HASHTAG_PATTERN.sub("", cleaned)

    #  Step 5: Normalize Unicode to NFC (handles é vs e + combining accent)
    cleaned = unicodedata.normalize("NFC", cleaned)

    #  Step 6: Collapse repeated filler punctuation and characters
    #    "amazing!!!!!!" → "amazing!!!"   |   "yessssss" → "yesss"
    cleaned = _REPEATED_PUNCT_PATTERN.sub(r"\1\1\1", cleaned)
    cleaned = _REPEATED_CHAR_PATTERN.sub(r"\1\1\1", cleaned)

    #  Step 7: Normalize whitespace (collapse, strip)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)   # collapse horizontal whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned) # max two consecutive newlines
    cleaned = cleaned.strip()

    #  Step 8: Skip if too short after cleaning
    if len(cleaned) < _MIN_CLEANED_LENGTH:
        logger.debug("Skipping too-short comment after cleaning: %r", cleaned)
        return None

    #  Step 9: Detect all-caps spam heuristic
    words = _WORD_SPLIT_PATTERN.split(cleaned)
    alpha_words = [w for w in words if re.search(r"[A-Za-z]{2,}", w)]
    if len(alpha_words) >= 4:
        caps_count = sum(1 for w in alpha_words if w.isupper())
        caps_fraction = caps_count / len(alpha_words)
        if caps_fraction >= _MAX_CAPS_FRACTION:
            logger.debug(
                "Skipping all-caps comment (%.0f%% uppercase words): %.60r…",
                caps_fraction * 100,
                text,
            )
            return None

    #  Step 10: Detect gibberish - a single token with no vowels and length > 5
    #    Catches keyboard mashing like "asdfghjkl", "qwerty123xyz"
    cleaned_lower = cleaned.lower()
    tokens = _WORD_SPLIT_PATTERN.split(cleaned_lower)
    alpha_tokens = [t for t in tokens if t.isalpha() and len(t) > 7]
    if alpha_tokens and all(not re.search(r"[aeiouáéíóúàèìòùäëïöü]", t) for t in alpha_tokens):
        logger.debug("Skipping likely gibberish comment: %.60r…", text)
        return None

    logger.debug("Cleaned comment: %r → %r", text[:60], cleaned[:60])
    return cleaned


def validate_keyword(keyword: str) -> Optional[str]:
    """
    Validate a brand/keyword string before using it as a YouTube search query.

    Parameters
    ----------
    keyword : str
        The search term provided by the user (or API consumer).

    Returns
    -------
    None
        The keyword is valid and safe to use.
    str
        A human-readable error message describing why the keyword is invalid.
        This string can be returned directly in a JSON error response:
        ``{"error": validate_keyword(kw)}``.

    Validation rules (in order)
    
    1. Must be a non-empty string.
    2. Must not be whitespace-only.
    3. Must be at least 3 characters long (after stripping).
    4. Must contain at least one letter or digit (rejects pure symbols).
    5. Must not exceed 100 characters (YouTube API query length guard).
    6. Must not contain shell-injection or SQLi-style characters (production guard).
    7. Must not consist entirely of repeated single characters ("aaaaaaa").
    """
    #  Rule 1: type and emptiness
    if not isinstance(keyword, str) or not keyword:
        return "Keyword must be a non-empty string."

    stripped = keyword.strip()

    #  Rule 2: whitespace-only
    if not stripped:
        return "Keyword cannot be whitespace only."

    #  Rule 3: minimum length
    if len(stripped) < 3:
        return f"Keyword is too short ({len(stripped)} chars). Please use at least 3 characters."

    #  Rule 4: must contain at least one alphanumeric character
    if not re.search(r"[A-Za-z0-9]", stripped):
        return "Keyword must contain at least one letter or number."

    #  Rule 5: maximum length guard (YouTube search query limit is ~100 chars)
    if len(stripped) > 100:
        return (
            f"Keyword is too long ({len(stripped)} chars). "
            "Please keep it under 100 characters."
        )

    #  Rule 6: basic injection / abuse guard
    #    Rejects keywords containing shell-control chars, SQL comment sequences,
    #    or excessive special symbols that have no place in a brand name search.
    dangerous_pattern = re.compile(r"[;<>|`$\\]|--|\bDROP\b|\bSELECT\b|\bINSERT\b", re.IGNORECASE)
    if dangerous_pattern.search(stripped):
        return "Keyword contains invalid or potentially unsafe characters."

    #  Rule 7: repeated-character gibberish ("aaaaaaa", "111111")
    if re.fullmatch(r"(.)\1+", stripped):
        return "Keyword appears to be gibberish (single repeated character)."

    return None  # keyword is valid


def filter_comments(raw_comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convenience helper for the sentiment service.

    Accepts a list of raw comment dicts (each must have a ``"text"`` key as
    returned by the YouTube Data API) and returns only the comments that pass
    all filters.  Each passing dict is enriched with a ``"cleaned_text"`` key
    containing the analysis-ready string.

    Parameters
    ----------
    raw_comments : list[dict]
        e.g. [{"comment_id": "xyz", "text": "Great product!", "author": "..."}, …]

    Returns
    -------
    list[dict]
        Subset of input dicts that are safe/meaningful to analyze, each with
        an added ``"cleaned_text"`` field.

    Example
    -------
    >>> comments = [{"text": "Love this brand!"}, {"text": "http://spam.com"}]
    >>> filter_comments(comments)
    [{'text': 'Love this brand!', 'cleaned_text': 'Love this brand!'}]
    """
    results: list[dict[str, Any]] = []
    skipped = 0

    for item in raw_comments:
        raw_text = item.get("text", "")
        cleaned = clean_comment_for_analysis(raw_text)
        if cleaned is None:
            skipped += 1
            continue
        results.append({**item, "cleaned_text": cleaned})

    logger.info(
        "filter_comments: %d accepted, %d skipped out of %d total.",
        len(results),
        skipped,
        len(raw_comments),
    )
    return results


#  Quick self-test (python comment_utils.py) 

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    test_comments = [
        "This product is absolutely amazing!!!",
        "Check out this deal: https://bit.ly/3xSpam",
        "LOVE IT SO MUCH BEST BRAND EVER BUY NOW",
        "@JohnDoe great video #sponsored",
        "lol",
        "asdfjkl;qweruiopzxcv",
        "Terrible quality, never buying again 😤",
        "  ",
        "<b>Bold claim</b> &amp; great taste",
        "aaaaaaaaaaaaa",
        "Not bad for the price. Would recommend to friends.",
    ]

    print(" clean_comment_for_analysis ")
    for c in test_comments:
        result = clean_comment_for_analysis(c)
        status = "✅" if result else "⛔ SKIP"
        print(f"  {status}  {c[:55]!r:58s} → {result!r}")

    print()
    print(" validate_keyword ")
    test_keywords = [
        "Nike",
        "  ",
        "ab",
        "!!!",
        "SELECT * FROM users",
        "aaaaaaa",
        "Apple iPhone 15 review",
        "A" * 101,
        "Coca-Cola",
        "B",
        "",
        "テスラ",
    ]
    for kw in test_keywords:
        err = validate_keyword(kw)
        status = "✅ valid" if err is None else f"❌ {err}"
        print(f"  {kw!r:35s} → {status}")