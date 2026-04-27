"""Unit tests for document text extraction."""

import pytest

from compliance_core.document_text import text_from_bytes


def test_text_from_txt_utf8():
    raw = "Hello, compliance.\nLine two.".encode("utf-8")
    assert text_from_bytes("policy.txt", raw) == "Hello, compliance.\nLine two."


def test_text_from_bytes_no_extension_treated_as_text():
    raw = b"plain body"
    assert text_from_bytes("README", raw) == "plain body"


def test_text_from_bytes_rejects_oversized_payload():
    huge = b"x" * (12 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="too large"):
        text_from_bytes("big.txt", huge)


def test_text_from_bytes_rejects_unknown_extension():
    with pytest.raises(ValueError, match="unsupported"):
        text_from_bytes("data.bin", b"abc")
