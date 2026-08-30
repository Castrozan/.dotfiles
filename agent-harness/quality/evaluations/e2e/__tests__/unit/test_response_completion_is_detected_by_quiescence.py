import itertools

import e2e_herdr_io

PANE = "wX:p1"


def drive_completion(monkeypatch, first_capture, next_capture, timeout_seconds=30):
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io, "capture_visible_screen", lambda _pane: next_capture()
    )
    return e2e_herdr_io.wait_for_response_completion(
        PANE, first_capture, timeout_seconds=timeout_seconds
    )


def drive_startup_settle(monkeypatch, next_capture, timeout_seconds=30):
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io, "capture_visible_screen", lambda _pane: next_capture()
    )
    return e2e_herdr_io.wait_for_startup_output_to_settle(
        PANE, timeout_seconds=timeout_seconds
    )


def replaying(captures):
    remaining = iter(captures)
    last = [captures[-1]]

    def next_capture():
        return next(remaining, last[0])

    return next_capture


def test_a_turn_that_renders_then_stops_is_reported_complete(monkeypatch):
    captures = ["thinking 1s", "thinking 2s", "answer"]
    captures += ["answer"] * e2e_herdr_io.RESPONSE_QUIESCENCE_SAMPLES

    assert drive_completion(monkeypatch, "prompt typed", replaying(captures)) is True


def test_a_pane_that_never_changes_is_never_reported_complete(monkeypatch):
    assert (
        drive_completion(
            monkeypatch,
            "prompt typed",
            lambda: "prompt typed",
            timeout_seconds=3,
        )
        is False
    ), (
        "a prompt that never reached the agent leaves the pane frozen, and reporting "
        "that as a completed turn grades the pre-prompt scrollback as the answer"
    )


def test_a_pane_still_rendering_at_the_deadline_is_reported_incomplete(monkeypatch):
    streamed_tokens = itertools.count()

    assert (
        drive_completion(
            monkeypatch,
            "prompt typed",
            lambda: f"streaming token {next(streamed_tokens)}",
            timeout_seconds=3,
        )
        is False
    )


def test_a_pause_shorter_than_the_quiescence_window_does_not_end_the_turn(monkeypatch):
    pause_length = e2e_herdr_io.RESPONSE_QUIESCENCE_SAMPLES - 1
    captures = ["tool call"] * pause_length + ["tool result", "answer"]
    captures += ["answer"] * e2e_herdr_io.RESPONSE_QUIESCENCE_SAMPLES
    replay = replaying(captures)
    consumed = []

    def counting_capture():
        consumed.append(replay())
        return consumed[-1]

    assert drive_completion(monkeypatch, "prompt typed", counting_capture) is True
    assert "answer" in consumed[: len(consumed) - 1], (
        "the turn ended during the mid-turn pause, before the answer ever rendered, "
        "so a tool call that pauses rendering would truncate the graded trace"
    )
    assert len(consumed) == len(captures), (
        f"expected the full {len(captures)} captures to be consumed before the turn "
        f"was called complete, got {len(consumed)}"
    )


def test_a_harness_still_painting_its_startup_is_not_ready_for_a_prompt(monkeypatch):
    starting_seconds = itertools.count()

    assert (
        drive_startup_settle(
            monkeypatch,
            lambda: f"Starting MCP servers (4/5): example-core ({next(starting_seconds)}s)",
            timeout_seconds=3,
        )
        is False
    ), (
        "a harness that reports idle while its startup output still moves will take "
        "the first scenario prompt into a composer it never submits"
    )


def test_a_harness_that_stops_painting_its_startup_is_ready_for_a_prompt(monkeypatch):
    captures = ["Starting MCP servers (4/5)", "Ask Codex to do anything"]
    captures += ["Ask Codex to do anything"] * e2e_herdr_io.RESPONSE_QUIESCENCE_SAMPLES

    assert drive_startup_settle(monkeypatch, replaying(captures)) is True


def test_a_harness_whose_startup_never_moves_is_ready_rather_than_stuck(monkeypatch):
    assert (
        drive_startup_settle(monkeypatch, lambda: "Ask Claude to do anything") is True
    ), (
        "readiness must not require the pane to change first, or a harness that "
        "finished painting before the first capture would never be called ready"
    )


def test_quiescence_samples_the_visible_screen_not_the_recent_scrollback(monkeypatch):
    requested_sources = []
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io,
        "read_pane",
        lambda _pane, source: requested_sources.append(source) or "settled screen",
    )

    assert e2e_herdr_io.wait_for_startup_output_to_settle(PANE, timeout_seconds=30)
    assert set(requested_sources) == {"visible"}, (
        "recent-unwrapped returns nothing once a resting TUI stops emitting, so "
        "sampling it makes every idle harness look quiescent immediately"
    )


def test_a_frozen_busy_indicator_does_not_end_the_turn(monkeypatch):
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_visible_screen",
        lambda _pane: "Working (0s - esc to interrupt)",
    )

    assert (
        e2e_herdr_io.wait_for_response_completion(
            PANE,
            "prompt typed",
            timeout_seconds=3,
            busy_marker="esc to interrupt",
        )
        is False
    ), (
        "codex holds its elapsed counter still while it works, so a screen that stops "
        "changing while the busy marker is up is a turn in flight, not a finished one"
    )


def test_a_turn_ends_once_the_busy_indicator_clears(monkeypatch):
    captures = ["Working (0s - esc to interrupt)"] * 3 + ["Context compacted"]
    captures += ["Context compacted"] * e2e_herdr_io.RESPONSE_QUIESCENCE_SAMPLES
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    replay = replaying(captures)
    monkeypatch.setattr(e2e_herdr_io, "capture_visible_screen", lambda _pane: replay())

    assert (
        e2e_herdr_io.wait_for_response_completion(
            PANE,
            "prompt typed",
            timeout_seconds=30,
            busy_marker="esc to interrupt",
        )
        is True
    )


def test_a_harness_still_starting_is_not_ready_while_its_busy_marker_is_up(monkeypatch):
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io,
        "capture_visible_screen",
        lambda _pane: "Starting MCP servers (4/5): example-core (38s - esc to interrupt)",
    )

    assert (
        e2e_herdr_io.wait_for_startup_output_to_settle(
            PANE, busy_marker="esc to interrupt", timeout_seconds=3
        )
        is False
    )
