import pytest

from app.core.errors import InvalidURLError
from app.services.youtube.url import extract_video_id

VID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://youtube.com/watch?v={VID}&t=42s&list=PL123",
        f"http://m.youtube.com/watch?feature=share&v={VID}",
        f"https://youtu.be/{VID}?si=abc",
        f"youtu.be/{VID}",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/embed/{VID}?start=10",
        f"https://www.youtube.com/live/{VID}",
        f"https://music.youtube.com/watch?v={VID}",
        f"https://www.youtube-nocookie.com/embed/{VID}",
        f"  {VID}  ",
    ],
)
def test_extracts_video_id(url):
    assert extract_video_id(url) == VID


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://vimeo.com/123456",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/channel/UC123",
        "https://evil.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ",
        "javascript:alert(1)",
        "ftp://youtube.com/watch?v=dQw4w9WgXcQ",
    ],
)
def test_rejects_invalid_urls(url):
    with pytest.raises(InvalidURLError):
        extract_video_id(url)
