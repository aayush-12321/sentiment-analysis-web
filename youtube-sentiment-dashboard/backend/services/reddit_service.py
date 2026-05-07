"""
services/reddit_service.py
Fetch and parse the Reddit public search RSS feed for brand mentions.

Endpoint (no API key required):
  https://www.reddit.com/search.rss?q={brand}&sort=relevance&limit={n}

Posts are relevance-filtered: brand keyword must appear in title or summary.
"""

import logging
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_RSS_TEMPLATE = (
    "https://www.reddit.com/search.rss"
    "?q={query}&sort=relevance&limit={limit}&restrict_sr=false"
)
_HEADERS = {
    "User-Agent": "SentimentScope/1.0 (brand sentiment research tool)"
}
_REQUEST_TIMEOUT = 20  # seconds


#  Public API 

def fetch_reddit_posts(brand: str, max_posts: int = 10) -> list[dict]:
    """
    Fetch Reddit RSS posts for the given brand keyword.

    Returns a list of post dicts:
        { postId, title, text, summary, url, publishedAt,
          author, subreddit, likeCount (0), source="reddit" }

    Raises RuntimeError on network / parse failure.
    """
    max_posts   = min(max(1, max_posts), 50)
    fetch_limit = min(max_posts * 3, 100)   # over-fetch to survive filtering
    url = _RSS_TEMPLATE.format(query=quote_plus(brand), limit=fetch_limit)
    logger.info("Reddit RSS fetch: %s", url)

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Reddit RSS request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to Reddit. Check your connection.")
    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code
        if code == 429:
            raise RuntimeError("Reddit rate limit reached. Wait a moment and retry.")
        if code in (401, 403):
            raise RuntimeError("Reddit blocked the request. Try again later.")
        raise RuntimeError(f"Reddit RSS returned HTTP {code}.")

    posts = _parse_rss(resp.text, brand, max_posts)
    logger.info(
        "Reddit RSS: %d/%d relevant posts accepted for brand %r.",
        len(posts), fetch_limit, brand,
    )
    return posts


#  Internal helpers 

def _parse_rss(xml_text: str, brand: str, max_posts: int) -> list[dict]:
    """Parse Atom RSS from Reddit, apply brand filter, return post dicts."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RuntimeError(f"Failed to parse Reddit RSS XML: {exc}")

    ns          = {"atom": "http://www.w3.org/2005/Atom"}
    brand_lower = brand.strip().lower()
    posts       = []

    for entry in root.findall("atom:entry", ns):
        title       = (entry.findtext("atom:title",   "", ns) or "").strip()
        summary_raw = (entry.findtext("atom:summary", "", ns) or "").strip()

        # Strip HTML tags from summary
        summary = re.sub(r"<[^>]+>", " ", summary_raw)
        summary = re.sub(r"\s+",     " ", summary).strip()

        link_el   = entry.find("atom:link", ns)
        url       = link_el.get("href", "") if link_el is not None else ""
        published = (entry.findtext("atom:updated", "", ns) or "")[:10]
        author    = (
            entry.findtext("atom:author/atom:name", "Anonymous", ns) or "Anonymous"
        )
        post_id   = entry.findtext("atom:id", url, ns) or url
        subreddit = _extract_subreddit(url)

        # Relevance: brand must appear in title or summary
        if brand_lower not in f"{title} {summary}".lower():
            continue

        # Build analysis text: title + first 500 chars of summary
        full_text = f"{title}. {summary[:500]}" if summary else title

        posts.append({
            "postId":      post_id,
            "title":       title,
            "text":        full_text,
            "summary":     summary[:300],
            "url":         url,
            "publishedAt": published,
            "author":      author,
            "subreddit":   subreddit,
            "likeCount":   0,
            "source":      "reddit",
        })

        if len(posts) >= max_posts:
            break

    return posts


def _extract_subreddit(url: str) -> str:
    """Extract subreddit name from a Reddit URL."""
    match = re.search(r"/r/([^/?#]+)", url)
    return f"r/{match.group(1)}" if match else "r/all"
