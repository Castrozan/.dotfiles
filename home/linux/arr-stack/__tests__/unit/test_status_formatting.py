import sys
from pathlib import Path

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))

import status_formatting
from status_assembly import MediaStatusLine


def make_line(**overrides):
    defaults = {
        "title": "Slime",
        "year": "2018",
        "media_type": "tv",
        "requested_by": "lucas",
        "stage": "partial",
        "progress": None,
        "arr_reachable": True,
    }
    defaults.update(overrides)
    return MediaStatusLine(**defaults)


def test_format_includes_year_when_present():
    assert status_formatting.format_status_line(make_line()).startswith("Slime (2018)")


def test_format_omits_year_when_absent():
    line = make_line(year=None)
    assert status_formatting.format_status_line(line).startswith("Slime\t")


def test_format_appends_download_progress_and_eta():
    line = make_line(progress={"percent": 33, "time_left": "00:09:58"})
    assert "partial | downloading 33% ETA 00:09:58" in (
        status_formatting.format_status_line(line)
    )


def test_format_download_progress_without_eta():
    line = make_line(progress={"percent": 33, "time_left": None})
    text = status_formatting.format_status_line(line)
    assert "downloading 33%" in text
    assert "ETA" not in text


def test_format_marks_chain_idle_for_processing_when_unreachable():
    line = make_line(stage="processing", progress=None, arr_reachable=False)
    assert "processing (download chain idle)" in (
        status_formatting.format_status_line(line)
    )


def test_format_does_not_mark_idle_for_available():
    line = make_line(stage="available", progress=None, arr_reachable=False)
    assert status_formatting.stage_text(line) == "available"


def test_filter_by_title_is_case_insensitive_substring():
    lines = [make_line(title="Slime"), make_line(title="Frieren")]
    filtered = status_formatting.filter_by_title(lines, "iere")
    assert [line.title for line in filtered] == ["Frieren"]


def test_filter_by_title_returns_all_when_query_empty():
    lines = [make_line(title="Slime"), make_line(title="Frieren")]
    assert status_formatting.filter_by_title(lines, None) == lines
