from app.services.processing.chunker import chunk_segments
from app.services.youtube.transcript import Segment, clean_text


def _segments(n: int, text: str = "word " * 10, punctuate_every: int = 0) -> list[Segment]:
    segs = []
    for i in range(n):
        t = text.strip() + (f" sentence {i}." if punctuate_every and i % punctuate_every == 0 else f" part {i}")
        segs.append(Segment(text=t, start=i * 3.0, duration=3.5))
    return segs


def test_preserves_order_and_timestamps():
    segs = _segments(200)
    chunks = chunk_segments(segs, chunk_size=500, chunk_overlap=80)
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert chunks[0].start_time == 0.0
    assert chunks[-1].end_time == round(segs[-1].start + segs[-1].duration, 2)
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.start_time >= prev.start_time
        assert nxt.start_time <= prev.end_time  # overlap keeps continuity


def test_all_text_is_covered():
    segs = _segments(120)
    chunks = chunk_segments(segs, chunk_size=400, chunk_overlap=60)
    joined = " ".join(c.content for c in chunks)
    for s in segs:
        assert s.text in joined


def test_respects_size_limit():
    segs = _segments(300)
    longest_segment = max(len(s.text) for s in segs)
    chunks = chunk_segments(segs, chunk_size=600, chunk_overlap=100)
    assert all(len(c.content) <= 600 + longest_segment for c in chunks)


def test_prefers_sentence_boundaries():
    segs = _segments(200, punctuate_every=4)
    chunks = chunk_segments(segs, chunk_size=800, chunk_overlap=0)
    sentence_endings = sum(c.content.endswith(".") for c in chunks[:-1])
    assert sentence_endings >= len(chunks[:-1]) * 0.8


def test_single_short_transcript():
    chunks = chunk_segments([Segment("Hello there.", 1.0, 2.0)], chunk_size=1000, chunk_overlap=100)
    assert len(chunks) == 1
    assert (chunks[0].start_time, chunks[0].end_time) == (1.0, 3.0)


def test_no_duplicate_tail_chunk_from_overlap():
    segs = _segments(30)
    chunks = chunk_segments(segs, chunk_size=300, chunk_overlap=100)
    assert chunks[-1].content.endswith(segs[-1].text)
    assert chunks[-2].content != chunks[-1].content


def test_clean_text():
    assert clean_text("[Music] hello &amp; welcome\n>> to   the show [Applause]") == "hello & welcome to the show"
