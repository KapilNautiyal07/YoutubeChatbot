"""Fetch public video metadata without requiring a YouTube Data API key.

Title/channel/thumbnail come from the oEmbed endpoint; duration is parsed from the
watch page when available (falls back to the transcript end time later on).
"""

import html
import logging
import re
from dataclasses import dataclass

import httpx

from app.core.errors import VideoUnavailableError

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class VideoMetadata:
    title: str | None
    channel_name: str | None
    thumbnail_url: str
    duration: int | None


def _thumbnail(video_id: str) -> str:
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return html.unescape(match.group(1)) if match else None


async def fetch_metadata(video_id: str) -> VideoMetadata:
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    title = channel = None
    duration: int | None = None

    async with httpx.AsyncClient(timeout=15, headers=_HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get(
                "https://www.youtube.com/oembed", params={"url": watch_url, "format": "json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                title, channel = data.get("title"), data.get("author_name")
            elif resp.status_code in (400, 404):
                raise VideoUnavailableError("This video doesn't exist or has been removed.")
            # 401/403 means embedding is disabled or the video is private; fall through to the page.
        except httpx.HTTPError as exc:
            logger.warning("oEmbed request failed for %s: %s", video_id, exc)

        try:
            page = await client.get(watch_url)
            if page.status_code == 200:
                text = page.text
                length = _search(r'"lengthSeconds":"(\d+)"', text)
                duration = int(length) if length else None
                title = title or _search(r'<meta name="title" content="([^"]*)"', text)
                channel = channel or _search(r'"ownerChannelName":"([^"]*)"', text)
                status = _search(r'"playabilityStatus":\{"status":"([A-Z_]+)"', text)
                if status in {"ERROR"} and not title:
                    raise VideoUnavailableError("This video is unavailable.")
                if status == "LOGIN_REQUIRED" and not title:
                    raise VideoUnavailableError("This video is private or age-restricted.")
        except httpx.HTTPError as exc:
            logger.warning("Watch page request failed for %s: %s", video_id, exc)

    return VideoMetadata(title=title, channel_name=channel, thumbnail_url=_thumbnail(video_id), duration=duration)
