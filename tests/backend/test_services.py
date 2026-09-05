import pytest
from backend.services.duplicate_service import remove_duplicates
from backend.services.text_cleaner_service import clean_entries
from backend.services.chart_service import inspect_chart
from backend.services.chunking_service import chunk_text

def test_cleaner_removes_filler_and_duplicates():
    assert clean_entries(["hello", "The deadline is Friday.", "the deadline is Friday."]) == ["The deadline is Friday."]

def test_chart_observation_never_invents_values():
    result = inspect_chart("Quarterly revenue chart")
    assert result["chart_type"] == "unknown_chart"
    assert result["parsed_values"] == []

def test_chunking_respects_limit():
    assert all(len(chunk) <= 20 for chunk in chunk_text("one\ntwo\nthree\nfour", 20))

def test_similarity_deduplication():
    assert remove_duplicates(["Ship the release", "Ship the release", "A different point"]) == ["Ship the release", "A different point"]
