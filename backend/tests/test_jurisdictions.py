"""Unit tests for jurisdiction label helpers."""

from compliance_core.jurisdictions import (
    MAX_JURISDICTION_CSV,
    merge_jurisdiction_labels,
    row_matches_jurisdictions,
    split_jurisdiction_csv,
    wanted_jurisdiction_list,
)


def test_merge_dedupes_case_insensitive_preserves_first_casing():
    assert merge_jurisdiction_labels("EU, eu, US") == "EU,US"


def test_merge_splits_comma_in_both_args():
    assert merge_jurisdiction_labels(jurisdiction="A, B", jurisdictions=["b", "C"]) == "A,B,C"


def test_merge_truncates_joined_csv_to_max_length():
    parts = ["x" * 200, "y" * 200]
    out = merge_jurisdiction_labels(jurisdictions=parts)
    assert out is not None
    assert len(out) == MAX_JURISDICTION_CSV


def test_merge_returns_none_when_empty():
    assert merge_jurisdiction_labels(jurisdiction="", jurisdictions=[]) is None


def test_split_csv_normalizes_case():
    assert split_jurisdiction_csv("EU, US, eu") == {"eu", "us"}


def test_wanted_jurisdiction_list_none_when_no_labels():
    assert wanted_jurisdiction_list() is None


def test_row_matches_global_row_when_filter_active():
    assert row_matches_jurisdictions(None, ["EU"]) is True


def test_row_matches_when_tags_overlap():
    assert row_matches_jurisdictions("EU,CH", ["eu"]) is True


def test_row_matches_false_when_disjoint():
    assert row_matches_jurisdictions("US", ["EU"]) is False


def test_row_matches_no_filter_always_true():
    assert row_matches_jurisdictions("anything", None) is True
