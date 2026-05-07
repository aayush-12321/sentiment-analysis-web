"""
services/youtube_service.py
All YouTube Data API v3 interactions.

Responsibilities:
  - Build authenticated API client from env key
  - Search videos by keyword
  - Fetch top-level comments for a video
  - Aggregate comments across multiple videos for a keyword
  - Convert raw API errors into friendly Python exceptions
"""
 
import os
import logging
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.brand_filter import build_search_query, is_video_relevant

logger = logging.getLogger(__name__)

_YT_MAX_PAGE_SIZE = 100   # YouTube API hard limit per page


#  Client factory 

def _get_client():
    """Return an authenticated YouTube API v3 client."""
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "YOUTUBE_API_KEY is missing. Add it to your .env file.\n"
            "Get a key at https://console.developers.google.com/"
        )
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


#  Public API 

def search_videos(keyword: str, max_results: int = 10) -> list[dict]:
    """
    Search YouTube for videos matching *keyword*.

    Returns a list of:
        {
          videoId, title, channelTitle, publishedAt, thumbnailUrl,
          description
        }

    Raises:
        PermissionError   - quota exceeded / invalid API key
        ValueError        - bad request
        RuntimeError      - other HTTP error
        EnvironmentError  - missing API key
    """
    youtube = _get_client()
    max_results = min(max(1, max_results), 50)

    # Build a smarter, disambiguation-aware query before hitting the API
    smart_query = build_search_query(keyword)
    logger.info("YouTube search query: %r (original keyword: %r)", smart_query, keyword)

    try:
        resp = (
            youtube.search()
            .list(
                q=smart_query,
                part="snippet",
                type="video",
                maxResults=max_results,
                order="relevance",
                relevanceLanguage="en",
            )
            .execute()
        )
    except HttpError as exc:
        _handle_http_error(exc)

    videos = []
    for item in resp.get("items", []):
        snippet = item.get("snippet", {})
        thumbs  = snippet.get("thumbnails", {})
        videos.append(
            {
                "videoId":      item["id"]["videoId"],
                "title":        snippet.get("title", ""),
                "channelTitle": snippet.get("channelTitle", ""),
                "publishedAt":  snippet.get("publishedAt", ""),
                "description":  snippet.get("description", "")[:200],
                "thumbnailUrl": (
                    thumbs.get("medium") or thumbs.get("default") or {}
                ).get("url", ""),
            }
        )
    return videos


def fetch_comments(video_id: str, max_comments: int = 20) -> list[dict]:
    """
    Fetch top-level comments for *video_id*.

    Returns a list of:
        {
          commentId, text, author, likeCount, publishedAt
        }

    Raises:
        ValueError       - comments disabled on this video
        PermissionError  - quota / key issue
        RuntimeError     - other HTTP error
    """
    youtube = _get_client()
    max_comments = min(max(1, max_comments), _YT_MAX_PAGE_SIZE)

    try:
        resp = (
            youtube.commentThreads()
            .list(
                videoId=video_id,
                part="snippet",
                maxResults=max_comments,
                order="relevance",
                textFormat="plainText",
            )
            .execute()
        )
    except HttpError as exc:
        if _extract_reason(exc) == "commentsDisabled":
            raise ValueError(f"Comments are disabled for video {video_id}.")
        _handle_http_error(exc)

    comments = []
    for item in resp.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]

        comment_id = item['id']

        comments.append(
            {
                "commentId":   comment_id,
                "text":        top.get("textDisplay", "").strip(),
                "author":      top.get("authorDisplayName", "Anonymous"),
                "likeCount":   top.get("likeCount", 0),
                "publishedAt": top.get("publishedAt", ""),

                "commentUrl": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"
            }
        )
    return comments


def fetch_comments_for_keyword(
    keyword: str,
    max_videos: int = 5,
    max_comments_per_video: int = 20,
) -> list[dict]:
    """
    High-level helper: search videos then aggregate comments.

    Each comment dict is enriched with videoId and videoTitle.
    Videos whose comments are disabled or cause transient errors are skipped.
    """
    videos = search_videos(keyword, max_results=max_videos)
    if not videos:
        logger.warning("No videos found for keyword %r", keyword)
        return []

    # Filter out videos whose title/description are not about the brand.
    # This removes unrelated content (e.g. "Apple" fruit videos) before
    # we spend API quota fetching their comments.
    relevant_videos = [v for v in videos if is_video_relevant(keyword, v)]
    logger.info(
        "Video relevance filter: %d/%d videos accepted for brand %r.",
        len(relevant_videos), len(videos), keyword,
    )

    # If all videos were filtered out, fall back to the full list so the
    # user still gets *some* result (with a warning in the logs).
    if not relevant_videos:
        logger.warning(
            "All %d videos were rejected by relevance filter for brand %r — "
            "falling back to unfiltered list.",
            len(videos), keyword,
        )
        relevant_videos = videos

    all_comments: list[dict] = []
    for video in relevant_videos:
        try:
            comments = fetch_comments(video["videoId"], max_comments=max_comments_per_video)
            for c in comments:
                c["videoId"]       = video["videoId"]
                c["videoTitle"]    = video["title"]
                c["videoThumbnail"] = video["thumbnailUrl"]
            all_comments.extend(comments)
            logger.info("Fetched %d comments from %r", len(comments), video["title"])
        except (ValueError, HttpError, RuntimeError) as exc:
            logger.warning("Skipping video %s — %s", video["videoId"], exc)

    return all_comments


#  Error helpers 

def _extract_reason(exc: HttpError) -> str:
    try:
        return (exc.error_details or [{}])[0].get("reason", "")
    except Exception:
        return ""


def _handle_http_error(exc: HttpError) -> None:
    """Re-raise HttpError as a typed Python exception."""
    status = exc.resp.status
    reason = _extract_reason(exc)
    logger.error("YouTube API HTTP %s (reason=%r): %s", status, reason, exc)

    if status == 403:
        raise PermissionError(
            "YouTube API quota exceeded or API key is invalid. "
            "Check your Google Cloud Console quota dashboard."
        )
    if status == 400:
        raise ValueError(f"Invalid request to YouTube API: {exc}")
    if status == 429:
        raise PermissionError("YouTube API rate limit hit. Try again in a few minutes.")
    raise RuntimeError(f"YouTube API error (HTTP {status}): {exc}")
