"""YouTube URL validation and video ID extraction."""

import re
from urllib.parse import parse_qs, urlparse

from app.core.errors import InvalidURLError

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
_PATH_PREFIXES = ("/embed/", "/shorts/", "/live/", "/v/", "/e/")


def extract_video_id(url: str) -> str:
    """Return the 11-character video ID for any common YouTube URL form, or raise InvalidURLError."""
    candidate = (url or "").strip()
    if not candidate:
        raise InvalidURLError("Please paste a YouTube link.")
    if len(candidate) > 2048:
        raise InvalidURLError("That link is too long to be a YouTube URL.")

    # Allow a bare video ID.
    if VIDEO_ID_RE.match(candidate):
        return candidate

    if not re.match(r"^https?://", candidate, re.IGNORECASE):
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() not in {"http", "https"} or host not in _ALLOWED_HOSTS:
        raise InvalidURLError("That doesn't look like a YouTube link. Try a youtube.com or youtu.be URL.")

    video_id: str | None = None
    if host.endswith("youtu.be"):
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif parsed.path == "/watch":
        video_id = (parse_qs(parsed.query).get("v") or [None])[0]
    else:
        for prefix in _PATH_PREFIXES:
            if parsed.path.startswith(prefix):
                video_id = parsed.path[len(prefix):].split("/")[0]
                break

    if not video_id or not VIDEO_ID_RE.match(video_id):
        raise InvalidURLError("We couldn't find a video ID in that link. Please check the URL.")
    return video_id
