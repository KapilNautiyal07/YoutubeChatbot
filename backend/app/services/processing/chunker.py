"""Split timestamped transcript segments into overlapping, sentence-aware chunks.

Caption segments are the atomic units, so every chunk maps back to exact
start/end timestamps. Within a size window, the chunker prefers to break after a
segment that ends a sentence; auto-generated captions without punctuation fall
back to size-based breaks on segment boundaries.
"""

from dataclasses import dataclass

from app.services.youtube.transcript import Segment

_SENTENCE_END = (".", "?", "!", "。", "？", "！", "…", '."', '?"', '!"')


@dataclass
class Chunk:
    index: int
    content: str
    start_time: float
    end_time: float


def _ends_sentence(text: str) -> bool:
    return text.rstrip().endswith(_SENTENCE_END)


def _make_chunk(index: int, units: list[Segment]) -> Chunk:
    return Chunk(
        index=index,
        content=" ".join(u.text for u in units),
        start_time=round(units[0].start, 2),
        end_time=round(max(u.end for u in units), 2),
    )


def chunk_segments(segments: list[Segment], chunk_size: int = 1000, chunk_overlap: int = 150) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
    soft_limit = int(chunk_size * 0.7)

    chunks: list[Chunk] = []
    current: list[Segment] = []
    length = 0
    # Number of leading units in `current` that are overlap carried from the previous chunk.
    carried = 0

    def flush() -> None:
        nonlocal current, length, carried
        chunks.append(_make_chunk(len(chunks), current))
        overlap: list[Segment] = []
        overlap_len = 0
        for unit in reversed(current):
            if overlap_len >= chunk_overlap or len(overlap) + 1 >= len(current):
                break
            overlap.insert(0, unit)
            overlap_len += len(unit.text) + 1
        current, length, carried = overlap, overlap_len, len(overlap)

    for segment in segments:
        seg_len = len(segment.text) + 1
        if current and len(current) > carried and length + seg_len > chunk_size:
            flush()
        current.append(segment)
        length += seg_len
        if length >= soft_limit and _ends_sentence(segment.text):
            flush()

    if len(current) > carried:
        chunks.append(_make_chunk(len(chunks), current))

    return chunks
