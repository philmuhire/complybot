"""Unit tests for API request/response schemas."""

from schemas_api import AnalyzeBody


def test_analyze_body_defaults_jurisdiction_to_eu_when_missing():
    body = AnalyzeBody(raw_input="x" * 15, jurisdictions=[])
    assert body.jurisdictions == ["EU"]


def test_analyze_body_dedupes_jurisdictions():
    body = AnalyzeBody(
        raw_input="incident narrative " * 2,
        jurisdictions=["eu", "EU", "US"],
    )
    assert body.jurisdictions == ["eu", "US"]


def test_analyze_body_falls_back_to_jurisdiction_hint():
    body = AnalyzeBody(
        raw_input="something long enough",
        jurisdictions=[],
        jurisdiction_hint="GDPR, GDPR",
    )
    assert "GDPR" in body.jurisdictions
