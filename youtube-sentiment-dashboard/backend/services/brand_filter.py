"""
services/brand_filter.py

Lightweight brand-relevance filtering for the YouTube sentiment pipeline.

Provides three public helpers:

    build_search_query(brand)           -> str
        Constructs a smarter YouTube search query.
        Appends disambiguation context for well-known ambiguous brand names
        (Apple, Meta, X, Amazon, …) to avoid unrelated results.

    is_video_relevant(brand, video)     -> bool
        Returns True when a YouTube video's title/description is likely about
        the requested brand.  For ambiguous brands, at least one domain-
        specific context keyword must also appear in the title/description.

    is_comment_relevant(brand, text)    -> bool
        Light relevance check on a single comment string.
        Returns False only for comments that are clearly unrelated to the brand
        (emoji-only, very short with no brand mention, or — for ambiguous brands
        — short with neither a brand name nor a context keyword).
        Intentionally permissive: video-level filtering carries most of the
        relevance signal; comment filtering only removes obvious noise.

Design principles
-----------------
* Zero extra dependencies — pure Python string / re operations.
* Works for any brand the user types; the ambiguous-brand dictionary is a
  bonus for the most common edge-cases.
* Every decision is logged at DEBUG level for easy tracing.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ambiguous brand definitions
# ---------------------------------------------------------------------------
# Each entry maps a normalised brand name (lower-case, stripped) to:
#   query_suffix      — appended to the raw brand name in the YouTube query
#   context_keywords  — at least one must appear in a video title/description
#                       before we accept it as a brand-related video.
#                       A hit on any keyword also auto-approves a comment.

_AMBIGUOUS_BRANDS: dict[str, dict] = {
    "apple": {
        "query_suffix": "company iPhone Mac tech review",
        "context_keywords": {
            "iphone", "ipad", "mac", "macbook", "ios", "apple inc",
            "tim cook", "airpods", "apple watch", "app store", "wwdc",
            "apple tv", "m1", "m2", "m3", "apple intelligence", "silicon",
        },
    },
    "meta": {
        "query_suffix": "Facebook Instagram company review",
        "context_keywords": {
            "facebook", "instagram", "whatsapp", "zuckerberg", "oculus",
            "vr", "virtual reality", "meta platforms", "reels", "threads",
            "ray-ban", "quest", "horizon",
        },
    },
    "amazon": {
        "query_suffix": "ecommerce AWS shopping company review",
        "context_keywords": {
            "aws", "prime", "alexa", "kindle", "bezos", "ecommerce",
            "amazon prime", "amazon web", "echo", "fire tv", "ring",
            "fulfillment", "marketplace", "prime video",
        },
    },
    "x": {
        "query_suffix": "Twitter social media platform Elon Musk",
        "context_keywords": {
            "twitter", "tweet", "elon", "musk", "x.com", "retweet",
            "social media", "grok", "xai", "blue tick", "verified",
            "timeline", "trending",
        },
    },
    "tesla": {
        "query_suffix": "electric car EV company review",
        "context_keywords": {
            "elon", "musk", "ev", "electric", "model s", "model 3",
            "model y", "cybertruck", "autopilot", "full self-driving",
            "fsd", "supercharger", "gigafactory", "electric vehicle",
        },
    },
    "google": {
        "query_suffix": "company tech search engine review",
        "context_keywords": {
            "search engine", "android", "gmail", "chrome", "alphabet",
            "pixel", "google cloud", "gemini", "bard", "google maps",
            "google drive", "workspace", "search", "youtube",
        },
    },
    "microsoft": {
        "query_suffix": "company software Windows review",
        "context_keywords": {
            "windows", "office", "azure", "xbox", "satya nadella",
            "teams", "outlook", "surface", "copilot", "bing", "365",
            "visual studio", "github",
        },
    },
    "samsung": {
        "query_suffix": "electronics Galaxy phone review",
        "context_keywords": {
            "galaxy", "android", "fold", "flip", "semiconductor",
            "amoled", "exynos", "one ui", "s24", "s25", "galaxy watch",
        },
    },
    "nike": {
        "query_suffix": "brand shoes sportswear review",
        "context_keywords": {
            "shoe", "shoes", "sneaker", "sportswear", "jordan",
            "just do it", "swoosh", "air max", "running", "athlete",
            "jersey", "apparel",
        },
    },
    "target": {
        "query_suffix": "retail store company shopping",
        "context_keywords": {
            "store", "retail", "shopping", "bullseye", "merchandise",
            "discount", "clearance", "grocery", "department store",
        },
    },
    "uber": {
        "query_suffix": "ride sharing app company review",
        "context_keywords": {
            "ride", "driver", "taxi", "uber eats", "delivery",
            "ride sharing", "rideshare", "lyft",
        },
    },
    "snap": {
        "query_suffix": "Snapchat social media app review",
        "context_keywords": {
            "snapchat", "story", "streaks", "spectacles", "filter",
            "snap map", "augmented reality", "ar lens",
        },
    },
    "oracle": {
        "query_suffix": "database cloud software company review",
        "context_keywords": {
            "database", "java", "cloud", "erp", "saas", "sql",
            "ellison", "netsuite", "fusion", "jdbc",
        },
    },
    "dove": {
        "query_suffix": "beauty personal care brand review",
        "context_keywords": {
            "soap", "shampoo", "skin care", "moisturizer", "body wash",
            "beauty", "unilever", "personal care",
        },
    },
    "mars": {
        "query_suffix": "candy chocolate company brand",
        "context_keywords": {
            "chocolate", "candy", "snickers", "m&m", "milky way",
            "twix", "skittles", "confectionery", "sweets",
        },
    },
    "spring": {
        "query_suffix": "software framework Java backend",
        "context_keywords": {
            "java", "framework", "boot", "spring boot", "dependency",
            "backend", "microservice", "rest api", "hibernate",
        },
    },
}

# ---------------------------------------------------------------------------
# Pre-compiled helpers
# ---------------------------------------------------------------------------

# Matches strings that consist entirely of emoji + whitespace (no real words)
_EMOJI_ONLY_PATTERN = re.compile(
    r"^[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF"
    r"\u231A-\u231B\u23E9-\u23F3\u25AA-\u25FE\u2614-\u2615"
    r"\s]+$",
    re.UNICODE,
)

# Minimum character count for a comment to be checked for brand relevance.
# Comments shorter than this are rarely meaningful brand sentiment.
_MIN_COMMENT_LENGTH = 15

# Length at which we accept an ambiguous-brand comment even without a keyword.
# Long comments are almost always substantive discussion about the video topic.
_LONG_COMMENT_LENGTH = 40


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_search_query(brand: str) -> str:
    """
    Return a smarter YouTube search query for the given brand name.

    For ambiguous brand names (Apple, Meta, X, Amazon, …), a disambiguation
    suffix is appended so YouTube returns brand-related videos rather than
    videos about the homonym (fruit, element, letter, …).

    For all other brands, a generic "brand review" suffix is added to attract
    opinion-heavy videos with richer sentiment signal.

    Parameters
    ----------
    brand : str
        Raw brand name as entered by the user.

    Returns
    -------
    str
        Optimised query string ready to pass to the YouTube search API.
    """
    brand_stripped = brand.strip()
    brand_lower    = brand_stripped.lower()

    entry = _AMBIGUOUS_BRANDS.get(brand_lower)
    if entry:
        query = f"{brand_stripped} {entry['query_suffix']}"
        logger.debug(
            "Ambiguous brand %r → enriched query: %r", brand_stripped, query
        )
    else:
        query = f"{brand_stripped} brand review"
        logger.debug(
            "Standard brand %r → generic query: %r", brand_stripped, query
        )

    return query


def is_video_relevant(brand: str, video: dict) -> bool:
    """
    Return True when the video is likely about the brand being searched.

    Strategy
    --------
    1. The brand name (normalised) must appear somewhere in the title +
       description combined text.
    2. For *ambiguous* brands (e.g. Apple) an additional check requires at
       least one context keyword (e.g. "iphone", "mac") to appear in the
       combined text — otherwise the video is probably about the homonym.

    Parameters
    ----------
    brand : str
        Raw brand name.
    video : dict
        Video dict as returned by ``youtube_service.search_videos()``
        (expected keys: ``"videoId"``, ``"title"``, ``"description"``).

    Returns
    -------
    bool
    """
    brand_lower = brand.strip().lower()
    title       = (video.get("title",       "") or "").lower()
    description = (video.get("description", "") or "").lower()
    combined    = f"{title} {description}"

    # Rule 1: brand name must appear in title or description
    brand_pattern = re.compile(r"\b" + re.escape(brand_lower) + r"\b")
    if not brand_pattern.search(combined):
        logger.debug(
            "Video %r rejected — brand %r not in title/description.",
            video.get("videoId", "?"), brand_lower,
        )
        return False

    # Rule 2: ambiguous brand → require at least one context keyword
    entry = _AMBIGUOUS_BRANDS.get(brand_lower)
    if entry:
        context_keywords = entry["context_keywords"]
        if not any(kw in combined for kw in context_keywords):
            logger.debug(
                "Video %r rejected — ambiguous brand %r: no context keyword "
                "in title/description. (checked: %s, …)",
                video.get("videoId", "?"), brand_lower,
                ", ".join(list(context_keywords)[:5]),
            )
            return False

    logger.debug(
        "Video %r accepted for brand %r.", video.get("videoId", "?"), brand_lower
    )
    return True


def is_comment_relevant(brand: str, text: str) -> bool:
    """
    Light relevance check: return False only when the comment is clearly
    unrelated to the brand.

    This is intentionally permissive.  Most comments on a brand-relevant
    video *are* about that brand even when the brand name is not typed out
    (e.g. "It overheats badly" on an iPhone review video).  Aggressive
    filtering here removes valid sentiment signal.

    Rules (in priority order)
    -------------------------
    1. Empty text                          → reject.
    2. Emoji-only comment                  → reject (no textual sentiment).
    3. Short (<_MIN_COMMENT_LENGTH chars) AND brand not mentioned → reject.
    4. Brand name present in text          → accept immediately.
    5. Ambiguous brand + context keyword   → accept.
    6. Non-ambiguous brand                 → accept (video filter sufficient).
    7. Ambiguous brand, long comment       → accept (likely topical).
    8. Ambiguous brand, short, no keyword  → reject.

    Parameters
    ----------
    brand : str
        Raw brand name.
    text  : str
        Cleaned comment text (after comment_utils processing).

    Returns
    -------
    bool
    """
    if not text:
        return False

    text_lower  = text.lower()
    brand_lower = brand.strip().lower()

    # Rule 2: emoji-only → no textual sentiment
    if _EMOJI_ONLY_PATTERN.match(text):
        logger.debug("Rejecting emoji-only comment: %.40r", text)
        return False

    # Rule 3: very short comment without explicit brand mention → skip
    if len(text) < _MIN_COMMENT_LENGTH:
        brand_pattern = re.compile(r"\b" + re.escape(brand_lower) + r"\b")
        if not brand_pattern.search(text_lower):
            logger.debug(
                "Rejecting short comment with no brand mention (len=%d): %.40r",
                len(text), text,
            )
            return False

    # Rule 4: brand name present → always accept
    brand_pattern = re.compile(r"\b" + re.escape(brand_lower) + r"\b")
    if brand_pattern.search(text_lower):
        return True

    entry = _AMBIGUOUS_BRANDS.get(brand_lower)

    # Rules 5-8: ambiguous brand handling
    if entry:
        context_keywords = entry["context_keywords"]

        # Rule 5: context keyword hit → accept
        if any(kw in text_lower for kw in context_keywords):
            return True

        # Rule 7: long enough to be substantive topical discussion → accept
        if len(text) >= _LONG_COMMENT_LENGTH:
            return True

        # Rule 8: short, no keyword → reject for ambiguous brands
        logger.debug(
            "Rejecting short comment for ambiguous brand %r — no context "
            "keyword found: %.40r",
            brand_lower, text,
        )
        return False

    # Rule 6: non-ambiguous brand → video filter already ensures relevance
    return True


def get_brand_keywords(brand: str) -> set[str]:
    """
    Return all context keywords associated with a brand (empty set if unknown).
    Useful for enriching API responses or debugging.
    """
    entry = _AMBIGUOUS_BRANDS.get(brand.strip().lower())
    return set(entry["context_keywords"]) if entry else set()
