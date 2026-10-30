"""Transcript retrieval with language selection and translation fallback."""

import asyncio
import html
import logging
import re
from dataclasses import dataclass

from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    NotTranslatable,
    RequestBlocked,
    Transcript,
    TranscriptsDisabled,
    TranslationLanguageNotAvailable,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApi,
)

from app.core.errors import TranscriptError, VideoUnavailableError

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class TranscriptResult:
    segments: list[Segment]
    language: str
    language_code: str
    is_generated: bool
    is_translated: bool


_NOISE_RE = re.compile(r"\[(?:music|applause|laughter|laughs|inaudible|silence|noise|cheering)\]", re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = _NOISE_RE.sub(" ", text)
    text = text.replace(">>", " ").replace("♪", " ")
    return _SPACE_RE.sub(" ", text).strip()


def _select_transcript(transcripts, requested: str | None, preferred: list[str]) -> tuple[Transcript, bool]:
    """Pick the best transcript. Returns (transcript, will_translate)."""
    available = list(transcripts)
    if not available:
        raise NoTranscriptFound("", [], transcripts)

    if requested:
        try:
            return transcripts.find_transcript([requested]), False
        except NoTranscriptFound:
            for t in available:
                if t.is_translatable and any(lang.language_code == requested for lang in t.translation_languages):
                    return t.translate(requested), True
            raise TranscriptError(
                f"No transcript is available in '{requested}' for this video, and it can't be translated to it."
            ) from None

    try:
        return transcripts.find_transcript(preferred), False
    except NoTranscriptFound:
        pass

    # Fall back to the original-language transcript (manual captions first). Embeddings and
    # chat models are multilingual, so the original wording is kept for maximum accuracy.
    return available[0], False


def _fetch_sync(video_id: str, requested: str | None, preferred: list[str]) -> TranscriptResult:
    api = YouTubeTranscriptApi()
    try:
        transcripts = api.list(video_id)
        transcript, translated = _select_transcript(transcripts, requested, preferred)
        fetched = transcript.fetch()
    except TranscriptsDisabled:
        raise TranscriptError("Captions are turned off for this video, so there's no transcript to read.") from None
    except NoTranscriptFound:
        raise TranscriptError("This video doesn't have a transcript we can use.") from None
    except (NotTranslatable, TranslationLanguageNotAvailable):
        raise TranscriptError("The transcript can't be translated to the requested language.") from None
    except (VideoUnavailable, InvalidVideoId):
        raise VideoUnavailableError("This video is unavailable or has been removed.") from None
    except AgeRestricted:
        raise VideoUnavailableError("This video is age-restricted, so its transcript can't be accessed.") from None
    except VideoUnplayable:
        raise VideoUnavailableError("This video can't be played (it may be private or region-locked).") from None
    except (RequestBlocked, IpBlocked):
        raise TranscriptError(
            "YouTube is temporarily blocking transcript requests from this server. Please try again later.",
            code="youtube_blocked",
            status_code=503,
        ) from None
    except CouldNotRetrieveTranscript as exc:
        logger.warning("Transcript retrieval failed for %s: %s", video_id, type(exc).__name__)
        raise TranscriptError("We couldn't retrieve the transcript for this video.") from None

    segments = []
    for snippet in fetched:
        text = clean_text(snippet.text)
        if text:
            segments.append(Segment(text=text, start=float(snippet.start), duration=float(snippet.duration)))

    if not segments:
        raise TranscriptError("The transcript for this video is empty.", code="empty_transcript")

    return TranscriptResult(
        segments=segments,
        language=fetched.language,
        language_code=fetched.language_code,
        is_generated=fetched.is_generated,
        is_translated=translated,
    )


async def fetch_transcript(video_id: str, *, requested_language: str | None, preferred: list[str]) -> TranscriptResult:
    # The transcript client is synchronous; keep the event loop free.
    return await asyncio.to_thread(_fetch_sync, video_id, requested_language, preferred)
