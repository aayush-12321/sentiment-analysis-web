"""
services/reddit_service.py
Fetch Reddit posts via RSS + fetch comments via public JSON endpoint.

No API key required — uses:
  • https://www.reddit.com/search.rss   — for post discovery
  • https://reddit.com/<post_url>.json  — for comment fetching

Public-domain approach: no OAuth, no Reddit API credentials needed.
"""

import logging
import re
import time
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
_REQUEST_TIMEOUT  = 20   # seconds
_COMMENT_TIMEOUT  = 15   # seconds per post
_MAX_COMMENTS_PER_POST = 20
_MIN_COMMENT_LEN  = 15   # ignore very short comments
_COMMENT_DELAY    = 0.5  # polite delay between JSON fetches (seconds)


# ── Public API ────────────────────────────────────────────────────────────────

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


def fetch_reddit_comments(post_url: str, max_comments: int = _MAX_COMMENTS_PER_POST) -> list[dict]:
    """
    Fetch comments from a single Reddit post using the public .json endpoint.

    Args:
        post_url: The Reddit post URL (e.g. https://www.reddit.com/r/sub/comments/abc/title/)
        max_comments: Maximum number of raw comments to return

    Returns:
        List of comment dicts: { commentId, body, author, score, publishedAt }
    """
    json_url = _build_json_url(post_url)
    if not json_url:
        logger.warning("Could not build JSON URL for: %s", post_url)
        return []

    logger.info("Fetching Reddit comments: %s", json_url)
    try:
        resp = requests.get(json_url, headers=_HEADERS, timeout=_COMMENT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.warning("Comment fetch timed out for %s", post_url)
        return []
    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code
        if code == 429:
            logger.warning("Rate limited fetching comments for %s", post_url)
        else:
            logger.warning("HTTP %d fetching comments for %s", code, post_url)
        return []
    except Exception as exc:
        logger.warning("Comment fetch failed for %s: %s", post_url, exc)
        return []

    return _extract_comments(data, max_comments)


def filter_relevant_comments(
    comments: list[dict],
    brand: str,
    max_comments: int = _MAX_COMMENTS_PER_POST,
) -> list[dict]:
    """
    Filter comments to keep only those relevant to the brand.

    Keeps comments that:
      • Are not deleted/removed
      • Meet minimum length threshold
      • Contain the brand keyword OR are from a brand-related subreddit context

    Args:
        comments: Raw comment dicts from fetch_reddit_comments()
        brand: Brand keyword to filter by
        max_comments: Maximum comments to return after filtering

    Returns:
        Filtered list of comment dicts ready for sentiment analysis.
    """
    brand_lower = brand.strip().lower()
    brand_tokens = set(brand_lower.split())
    filtered = []

    for c in comments:
        body = (c.get("body") or "").strip()

        # Skip deleted/removed
        if body in ("[deleted]", "[removed]", ""):
            continue

        # Skip too short
        if len(body) < _MIN_COMMENT_LEN:
            continue

        body_lower = body.lower()

        # Keep if brand keyword mentioned OR any brand token found
        brand_mentioned = brand_lower in body_lower or any(
            tok in body_lower for tok in brand_tokens if len(tok) > 3
        )

        if brand_mentioned:
            c["text"]         = body
            c["likeCount"]    = c.get("score", 0)
            c["publishedAt"]  = c.get("publishedAt", "")
            c["source"]       = "reddit_comment"
            filtered.append(c)

        if len(filtered) >= max_comments:
            break

    return filtered


def fetch_posts_with_comments(
    brand: str,
    max_posts: int = 10,
    max_comments_per_post: int = _MAX_COMMENTS_PER_POST,
) -> tuple[list[dict], list[dict]]:
    """
    Fetch Reddit posts AND their comments in a single call.

    Returns:
        (posts, all_comments)
        - posts: list of post dicts (same as fetch_reddit_posts)
        - all_comments: list of filtered comment dicts across all posts
    """
    posts = fetch_reddit_posts(brand, max_posts=max_posts)
    if not posts:
        return posts, []

    all_comments: list[dict] = []

    for i, post in enumerate(posts):
        post_url = post.get("url", "")
        if not post_url:
            continue

        # Polite delay between requests (skip on first)
        if i > 0:
            time.sleep(_COMMENT_DELAY)

        raw_comments = fetch_reddit_comments(post_url, max_comments=max_comments_per_post * 2)
        relevant     = filter_relevant_comments(raw_comments, brand, max_comments=max_comments_per_post)

        # Tag each comment with its parent post
        for c in relevant:
            c["postId"]    = post.get("postId", "")
            c["subreddit"] = post.get("subreddit", "")

        all_comments.extend(relevant)
        logger.info(
            "Post %d/%d (%s): %d raw → %d relevant comments",
            i + 1, len(posts), post.get("subreddit", "?"),
            len(raw_comments), len(relevant),
        )

    logger.info(
        "Total Reddit: %d posts, %d relevant comments for brand %r",
        len(posts), len(all_comments), brand,
    )
    return posts, all_comments


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_json_url(post_url: str) -> str | None:
    """
    Convert a Reddit post URL to its .json equivalent.

    Example:
      https://www.reddit.com/r/netflix/comments/abc123/title/
      → https://www.reddit.com/r/netflix/comments/abc123/title/.json
    """
    if not post_url or "reddit.com" not in post_url:
        return None
    # Ensure we have a clean URL without query params
    clean = post_url.split("?")[0].rstrip("/")
    return clean + "/.json?limit=50&depth=2"


def _extract_comments(data: list | dict, max_comments: int) -> list[dict]:
    """
    Walk the Reddit JSON response and extract comment bodies.

    Reddit JSON structure:
      data[0] = post listing
      data[1] = comments listing (nested)
    """
    if not isinstance(data, list) or len(data) < 2:
        return []

    comments_listing = data[1]
    if not isinstance(comments_listing, dict):
        return []

    children = (
        comments_listing
        .get("data", {})
        .get("children", [])
    )

    extracted: list[dict] = []
    _walk_comments(children, extracted, max_comments)
    return extracted


def _walk_comments(children: list, out: list, max_count: int, depth: int = 0) -> None:
    """Recursively walk Reddit comment tree."""
    if depth > 3:   # don't go too deep
        return

    for child in children:
        if len(out) >= max_count:
            return

        kind = child.get("kind", "")
        if kind == "more":
            continue   # skip "load more" stubs

        item = child.get("data", {})
        body = (item.get("body") or "").strip()

        # Only keep actual text comments
        if body and body not in ("[deleted]", "[removed]"):
            published = ""
            created_utc = item.get("created_utc")
            if created_utc:
                import datetime
                published = datetime.datetime.utcfromtimestamp(
                    float(created_utc)
                ).strftime("%Y-%m-%d")

            out.append({
                "commentId":   item.get("id", ""),
                "body":        body,
                "author":      item.get("author", "Anonymous"),
                "score":       item.get("score", 0),
                "publishedAt": published,
            })

        # Recurse into replies
        replies = item.get("replies", {})
        if isinstance(replies, dict):
            reply_children = replies.get("data", {}).get("children", [])
            if reply_children:
                _walk_comments(reply_children, out, max_count, depth + 1)


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
