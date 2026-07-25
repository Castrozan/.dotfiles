import importlib.util
import json
import os
import time
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "scripts"
    / "list-unprocessed-captures.py"
)
module_specification = importlib.util.spec_from_file_location(
    "list_unprocessed_captures", SCRIPT_PATH
)
loaded_capture_listing_module = importlib.util.module_from_spec(module_specification)
assert module_specification.loader is not None
module_specification.loader.exec_module(loaded_capture_listing_module)


def write_capture(capture_inbox_directory: Path, name: str, body: str) -> Path:
    capture_inbox_directory.mkdir(parents=True, exist_ok=True)
    capture_path = capture_inbox_directory / name
    capture_path.write_text(body, encoding="utf-8")
    return capture_path


def test_captures_carrying_the_done_marker_are_excluded(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-03-01 10-00-00).md", "unworked body")
    write_capture(
        tmp_path,
        "Tweet from B (2026-03-02 10-00-00).md",
        "worked body\n\n#agent-work-done\nverdict:: drop\n",
    )

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )

    assert [capture["name"] for capture in unprocessed_captures] == [
        "Tweet from A (2026-03-01 10-00-00).md"
    ]


def test_captures_are_ordered_newest_first_by_the_filename_timestamp(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-01-05 09-00-00).md", "body")
    write_capture(tmp_path, "Article 2026-06-13 20-37-11.md", "body")
    write_capture(tmp_path, "Tweet from C (2026-03-20 22-55-15).md", "body")

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )

    assert [capture["name"] for capture in unprocessed_captures] == [
        "Article 2026-06-13 20-37-11.md",
        "Tweet from C (2026-03-20 22-55-15).md",
        "Tweet from A (2026-01-05 09-00-00).md",
    ]


def test_the_filename_timestamp_outranks_a_recently_rewritten_modification_time(
    tmp_path,
):
    old_capture = write_capture(
        tmp_path, "Tweet from Old (2026-01-05 09-00-00).md", "body"
    )
    write_capture(tmp_path, "Tweet from New (2026-05-31 11-01-45).md", "body")
    os.utime(old_capture, (time.time() + 10_000, time.time() + 10_000))

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )

    assert unprocessed_captures[0]["name"] == "Tweet from New (2026-05-31 11-01-45).md"
    assert unprocessed_captures[0]["captured_from"] == "filename"


def test_an_undated_capture_falls_back_to_its_modification_time(tmp_path):
    undated_capture = write_capture(tmp_path, "Youtube - homebrew router.md", "body")
    write_capture(tmp_path, "Tweet from Dated (2026-05-31 11-01-45).md", "body")
    os.utime(undated_capture, (time.time() + 10_000, time.time() + 10_000))

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )

    assert unprocessed_captures[0]["name"] == "Youtube - homebrew router.md"
    assert unprocessed_captures[0]["captured_from"] == "modification-time"


def test_a_missing_inbox_directory_yields_no_captures(tmp_path):
    assert (
        loaded_capture_listing_module.collect_unprocessed_captures(tmp_path / "absent")
        == []
    )


def test_the_rendered_text_reports_the_total_alongside_a_truncated_view(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-01-05 09-00-00).md", "body")
    write_capture(tmp_path, "Tweet from B (2026-02-05 09-00-00).md", "body")

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )
    rendered_text = loaded_capture_listing_module.render_unprocessed_captures_as_text(
        unprocessed_captures[:1], len(unprocessed_captures)
    )

    assert rendered_text.splitlines()[0] == (
        "2 unprocessed captures, newest first, showing 1"
    )
    assert "Tweet from B (2026-02-05 09-00-00).md" in rendered_text


def test_the_json_payload_carries_the_resolved_capture_path(tmp_path):
    capture_path = write_capture(
        tmp_path, "Tweet from A (2026-01-05 09-00-00).md", "body"
    )

    unprocessed_captures = loaded_capture_listing_module.collect_unprocessed_captures(
        tmp_path
    )
    parsed_payload = json.loads(json.dumps(unprocessed_captures))

    assert parsed_payload[0]["path"] == str(capture_path)
    assert parsed_payload[0]["captured"] == "2026-01-05 09:00:00"
