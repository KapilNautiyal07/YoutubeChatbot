from app.services.rag.pipeline import _BROAD_RE, _parse_json
from app.services.rag.prompts import format_timestamp
from app.services.retrieval.retriever import _keyword_query


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(75.9) == "01:15"
    assert format_timestamp(3725) == "1:02:05"


def test_keyword_query_strips_stopwords_and_symbols():
    assert _keyword_query("What does the speaker say about gradient descent?") == "gradient | descent"
    assert _keyword_query("what is it?") is None
    assert "'" not in (_keyword_query("Bob's model & (weights)") or "")


def test_broad_detection():
    for q in ["Summarize this video", "What are the key takeaways?", "give me a tl;dr", "What is this video about?"]:
        assert _BROAD_RE.search(q), q
    for q in ["What is backpropagation?", "When does he mention Python?"]:
        assert not _BROAD_RE.search(q), q


def test_parse_json_tolerates_code_fences():
    assert _parse_json('```json\n{"query": "x", "scope": "broad"}\n```') == {"query": "x", "scope": "broad"}
