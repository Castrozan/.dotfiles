import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import captures

FIXED_NOW = datetime(2026, 7, 25, 21, 0, 0)


def write_capture(capture_inbox_directory: Path, name: str, body: str) -> Path:
    capture_inbox_directory.mkdir(parents=True, exist_ok=True)
    capture_path = capture_inbox_directory / name
    capture_path.write_text(body, encoding="utf-8")
    return capture_path


def claim_block(claimed_at: datetime, claim_owner: str = "chise") -> str:
    return (
        f"\n\nstatus:: working\nclaimed_by:: {claim_owner}\n"
        f"claimed_at:: {claimed_at.isoformat(timespec='seconds')}\n"
    )


def test_captures_carrying_the_done_marker_leave_the_queue(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-03-01 10-00-00).md", "unworked body")
    write_capture(
        tmp_path,
        "Tweet from B (2026-03-02 10-00-00).md",
        "worked body\n\n#agent-work-done\nverdict:: drop\n",
    )

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)

    assert [capture["name"] for capture in pending_captures] == [
        "Tweet from A (2026-03-01 10-00-00).md"
    ]


def test_captures_are_ordered_newest_first_by_the_filename_timestamp(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-01-05 09-00-00).md", "body")
    write_capture(tmp_path, "Article 2026-06-13 20-37-11.md", "body")
    write_capture(tmp_path, "Tweet from C (2026-03-20 22-55-15).md", "body")

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)

    assert [capture["name"] for capture in pending_captures] == [
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

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)

    assert pending_captures[0]["name"] == "Tweet from New (2026-05-31 11-01-45).md"
    assert pending_captures[0]["captured_from"] == "filename"


def test_an_undated_capture_falls_back_to_its_modification_time(tmp_path):
    undated_capture = write_capture(tmp_path, "Youtube - homebrew router.md", "body")
    write_capture(tmp_path, "Tweet from Dated (2026-05-31 11-01-45).md", "body")
    os.utime(undated_capture, (time.time() + 10_000, time.time() + 10_000))

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)

    assert pending_captures[0]["name"] == "Youtube - homebrew router.md"
    assert pending_captures[0]["captured_from"] == "modification-time"


def test_a_missing_inbox_directory_yields_no_captures(tmp_path):
    assert captures.collect_pending_captures(tmp_path / "absent", 60, FIXED_NOW) == []


def test_a_fresh_claim_reads_as_working_and_a_stale_one_as_reclaimable(tmp_path):
    write_capture(
        tmp_path,
        "Tweet from Fresh (2026-07-01 10-00-00).md",
        "body" + claim_block(FIXED_NOW - timedelta(minutes=5)),
    )
    write_capture(
        tmp_path,
        "Tweet from Stale (2026-07-02 10-00-00).md",
        "body" + claim_block(FIXED_NOW - timedelta(minutes=180)),
    )

    states_by_name = {
        capture["name"]: capture["state"]
        for capture in captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    }

    assert states_by_name["Tweet from Fresh (2026-07-01 10-00-00).md"] == "working"
    assert states_by_name["Tweet from Stale (2026-07-02 10-00-00).md"] == "stale-claim"


def test_an_unparseable_claim_timestamp_is_treated_as_stale(tmp_path):
    write_capture(
        tmp_path,
        "Tweet from Broken (2026-07-01 10-00-00).md",
        "body\n\nstatus:: working\nclaimed_by:: chise\nclaimed_at:: yesterday\n",
    )

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)

    assert pending_captures[0]["state"] == "stale-claim"


def test_only_free_captures_are_claimable(tmp_path):
    write_capture(
        tmp_path,
        "Tweet from Held (2026-07-03 10-00-00).md",
        "body" + claim_block(FIXED_NOW - timedelta(minutes=5)),
    )
    write_capture(tmp_path, "Tweet from Free (2026-07-02 10-00-00).md", "body")

    pending_captures = captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    free_captures = captures.claimable_captures(pending_captures)

    assert [capture["name"] for capture in free_captures] == [
        "Tweet from Free (2026-07-02 10-00-00).md"
    ]


def test_the_probe_fingerprint_names_the_queue_head(tmp_path):
    write_capture(tmp_path, "Tweet from A (2026-07-02 10-00-00).md", "body")
    write_capture(tmp_path, "Tweet from B (2026-07-04 10-00-00).md", "body")

    fingerprint = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    assert fingerprint == "2026-07-04 10:00:00 Tweet from B (2026-07-04 10-00-00).md"


def test_the_probe_fingerprint_ignores_captures_worked_below_the_head(tmp_path):
    write_capture(tmp_path, "Tweet from Newest (2026-07-04 10-00-00).md", "body")
    write_capture(tmp_path, "Tweet from Older (2026-07-02 10-00-00).md", "body")
    fingerprint_before = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    (tmp_path / "Tweet from Older (2026-07-02 10-00-00).md").write_text(
        "body\n\n#agent-work-done\nverdict:: drop\n", encoding="utf-8"
    )
    fingerprint_after = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    assert fingerprint_after == fingerprint_before


def test_the_probe_fingerprint_holds_still_while_the_queue_head_is_claimed(tmp_path):
    write_capture(tmp_path, "Tweet from Head (2026-07-04 10-00-00).md", "body")
    write_capture(tmp_path, "Tweet from Next (2026-07-02 10-00-00).md", "body")
    fingerprint_before = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    (tmp_path / "Tweet from Head (2026-07-04 10-00-00).md").write_text(
        "body" + claim_block(FIXED_NOW - timedelta(minutes=5)), encoding="utf-8"
    )
    fingerprint_after = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    assert fingerprint_after == fingerprint_before


def test_the_probe_fingerprint_is_empty_when_every_capture_is_done(tmp_path):
    write_capture(
        tmp_path,
        "Tweet from Done (2026-07-03 10-00-00).md",
        "body\n\n#agent-work-done\nverdict:: drop\n",
    )

    fingerprint = captures.newest_pending_capture_fingerprint(
        captures.collect_pending_captures(tmp_path, 60, FIXED_NOW)
    )

    assert fingerprint == ""
