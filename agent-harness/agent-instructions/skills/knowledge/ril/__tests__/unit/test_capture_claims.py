from datetime import datetime, timedelta
from pathlib import Path

import captures
from claims import claim_capture, record_capture_verdict, release_capture

FIXED_NOW = datetime(2026, 7, 25, 21, 0, 0)


def state_of(capture_path: Path, now: datetime = FIXED_NOW) -> str:
    return captures.capture_state(captures.read_capture_body(capture_path), 60, now)


def test_claiming_a_free_capture_stamps_the_owner_and_the_claim_time(
    tmp_path, write_capture
):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")

    claim_outcome = claim_capture(capture_path, "chise", 60, FIXED_NOW)

    capture_body = capture_path.read_text(encoding="utf-8")
    assert claim_outcome == "claimed"
    assert "status:: working" in capture_body
    assert "claimed_by:: chise" in capture_body
    assert "claimed_at:: 2026-07-25T21:00:00" in capture_body
    assert state_of(capture_path) == "working"


def test_a_live_claim_refuses_a_second_claimant(tmp_path, write_capture):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    claim_capture(capture_path, "chise", 60, FIXED_NOW)

    claim_outcome = claim_capture(
        capture_path, "kira", 60, FIXED_NOW + timedelta(minutes=5)
    )

    assert claim_outcome == "held"
    assert "claimed_by:: chise" in capture_path.read_text(encoding="utf-8")


def test_a_live_claim_yields_to_an_explicit_takeover(tmp_path, write_capture):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    claim_capture(capture_path, "chise", 60, FIXED_NOW)

    claim_outcome = claim_capture(
        capture_path, "kira", 60, FIXED_NOW + timedelta(minutes=5), force=True
    )

    assert claim_outcome == "reclaimed"
    assert "claimed_by:: kira" in capture_path.read_text(encoding="utf-8")


def test_an_expired_claim_is_reclaimable_without_a_takeover_flag(
    tmp_path, write_capture
):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    claim_capture(capture_path, "chise", 60, FIXED_NOW)

    claim_outcome = claim_capture(
        capture_path, "kira", 60, FIXED_NOW + timedelta(minutes=61)
    )

    capture_body = capture_path.read_text(encoding="utf-8")
    assert claim_outcome == "reclaimed"
    assert capture_body.count("status:: working") == 1
    assert "claimed_by:: kira" in capture_body


def test_a_done_capture_cannot_be_claimed(tmp_path, write_capture):
    capture_path = write_capture(
        tmp_path, "Article 2026-07-01 10-00-00.md", "body\n\n#agent-work-done\n"
    )

    assert claim_capture(capture_path, "chise", 60, FIXED_NOW) == "already-done"


def test_releasing_a_claim_returns_the_capture_unworked(tmp_path, write_capture):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    claim_capture(capture_path, "chise", 60, FIXED_NOW)

    release_outcome = release_capture(capture_path, 60, FIXED_NOW)

    assert release_outcome == "released"
    assert capture_path.read_text(encoding="utf-8") == "body\n"
    assert state_of(capture_path) == "unworked"


def test_releasing_an_unclaimed_capture_changes_nothing(tmp_path, write_capture):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body\n")

    release_outcome = release_capture(capture_path, 60, FIXED_NOW)

    assert release_outcome == "not-claimed"
    assert capture_path.read_text(encoding="utf-8") == "body\n"


def test_recording_a_verdict_clears_the_claim_and_closes_the_capture(
    tmp_path, write_capture
):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    claim_capture(capture_path, "chise", 60, FIXED_NOW)

    recording_outcome = record_capture_verdict(
        capture_path, "adopt", "chise advertises an exit node", "Tailscale exit nodes"
    )

    capture_body = capture_path.read_text(encoding="utf-8")
    assert recording_outcome == "recorded"
    assert "status:: working" not in capture_body
    assert "claimed_by::" not in capture_body
    assert "#agent-work-done" in capture_body
    assert "verdict:: adopt" in capture_body
    assert "outcome:: chise advertises an exit node" in capture_body
    assert "entry:: [[Tailscale exit nodes]]" in capture_body
    assert state_of(capture_path) == "done"


def test_recording_a_verdict_twice_leaves_the_first_one_standing(
    tmp_path, write_capture
):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")
    record_capture_verdict(capture_path, "adopt", "first outcome", None)

    recording_outcome = record_capture_verdict(
        capture_path, "drop", "second outcome", None
    )

    capture_body = capture_path.read_text(encoding="utf-8")
    assert recording_outcome == "already-recorded"
    assert "first outcome" in capture_body
    assert "second outcome" not in capture_body


def test_an_entry_link_already_wrapped_in_brackets_is_not_double_wrapped(
    tmp_path, write_capture
):
    capture_path = write_capture(tmp_path, "Article 2026-07-01 10-00-00.md", "body")

    record_capture_verdict(capture_path, "learn", "read it", "[[Exit nodes]]")

    assert "entry:: [[Exit nodes]]" in capture_path.read_text(encoding="utf-8")
