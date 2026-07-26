import itertools

import e2e_herdr_io

PANE = "wX:p1"


def drive_completion(monkeypatch, first_capture, next_capture, timeout_seconds=30):
    monkeypatch.setattr(e2e_herdr_io.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        e2e_herdr_io, "capture_full_terminal_output", lambda _pane: next_capture()
    )
    return e2e_herdr_io.wait_for_response_completion(
        PANE, first_capture, timeout_seconds=timeout_seconds
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
