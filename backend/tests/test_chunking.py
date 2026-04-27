"""Unit tests for text chunking."""

from compliance_core.chunking import chunk_text


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_single_short_block():
    assert chunk_text("One paragraph only.") == ["One paragraph only."]


def test_chunk_text_blank_lines_then_merges_small_blocks():
    # Paragraphs are split on blank lines, then merged until max_chars (default 2400).
    out = chunk_text("A\n\nB\n\nC")
    assert out == ["A\n\nB\n\nC"]


def test_chunk_text_merges_small_paragraphs_under_max():
    # Default max_chars is 2400; two tiny paragraphs merge with \n\n
    out = chunk_text("x\n\ny")
    assert len(out) == 1
    assert out[0] == "x\n\ny"


def test_chunk_text_respects_max_chars():
    long_word = "w" * 50
    body = "\n\n".join([long_word] * 100)
    chunks = chunk_text(body, max_chars=120)
    for c in chunks:
        assert len(c) <= 120
