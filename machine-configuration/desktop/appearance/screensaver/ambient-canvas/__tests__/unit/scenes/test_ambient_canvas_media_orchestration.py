import pytest

import ensure_ambient_canvas_screensaver as ensure
from recording.recorded_loop_capture_target import RecordedLoopCaptureTarget

PLAYER_BINARY_PATH = "/home/user/.local/bin/player"
LAPTOP_CAPTURE_TARGET = RecordedLoopCaptureTarget(
    loop_directory="/state/loops/1660x1080",
    scene_video_directory="/state/videos",
    playback_dwell_override_path="/state/playback-dwell-seconds",
    screen_dimensions=(1470, 956),
    capture_pixel_dimensions=(1660, 1080),
    capture_signature="1660x1080",
)


def _install_orchestration_stubs(
    monkeypatch,
    *,
    fresh,
    render_result,
    display_running,
    loop_exists=True,
    record_pass_running=False,
):
    observed_calls = []
    monkeypatch.setattr(ensure, "recorded_loop_is_fresh", lambda *ignored: fresh)
    monkeypatch.setattr(ensure, "recorded_loop_exists", lambda *ignored: loop_exists)

    def fake_render(*ignored):
        observed_calls.append("render")
        return render_result

    monkeypatch.setattr(ensure, "render_recorded_loop", fake_render)
    monkeypatch.setattr(ensure, "a_record_pass_is_running", lambda: record_pass_running)
    monkeypatch.setattr(
        ensure, "is_display_running_for_loop", lambda *ignored: display_running
    )
    monkeypatch.setattr(
        ensure, "stop_every_display", lambda *ignored: observed_calls.append("stop")
    )
    monkeypatch.setattr(
        ensure,
        "wait_for_every_display_to_exit",
        lambda *ignored: observed_calls.append("wait"),
    )

    def fake_launch(*ignored):
        observed_calls.append("launch")
        return 0

    monkeypatch.setattr(ensure, "launch_display", fake_launch)

    def fake_discard(capture_target, rendering_source_identifier):
        observed_calls.append(("discard", rendering_source_identifier))
        return []

    monkeypatch.setattr(ensure, "discard_rendering_leftovers", fake_discard)
    return observed_calls


def _run_ensure(monkeypatch, **stub_arguments):
    observed_calls = _install_orchestration_stubs(monkeypatch, **stub_arguments)
    result = ensure.ensure_screensaver(
        "index",
        LAPTOP_CAPTURE_TARGET,
        "source",
        "#241010",
        PLAYER_BINARY_PATH,
        30,
        30,
    )
    return result, observed_calls


def test_fresh_loop_with_running_display_only_discards_render_leftovers(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=True
    )
    assert result == 0
    assert calls == [("discard", "source")]


def test_fresh_loop_with_stopped_display_relaunches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=False
    )
    assert result == 0
    assert calls == [("discard", "source"), "stop", "wait", "launch"]


def test_a_cached_display_swap_repoints_the_player_without_recording(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=False
    )
    assert result == 0
    assert "render" not in calls
    assert calls[-1] == "launch"


@pytest.mark.parametrize("display_running", [True, False])
def test_stale_render_success_relaunches(monkeypatch, display_running):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result="loop.segments.json",
        display_running=display_running,
    )
    assert result == 0
    assert calls == ["render", "stop", "wait", "launch"]


def test_stale_render_failure_without_existing_loop_exits_nonzero(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result=None,
        display_running=False,
        loop_exists=False,
    )
    assert result == 1
    assert calls == ["render"]


@pytest.mark.parametrize(
    ("display_running", "expected_calls"),
    [(False, ["render", "stop", "wait", "launch"]), (True, ["render"])],
)
def test_stale_render_failure_preserves_existing_loop(
    monkeypatch, display_running, expected_calls
):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result=None,
        display_running=display_running,
        loop_exists=True,
    )
    assert result == 0
    assert calls == expected_calls


def test_stale_loop_skips_render_while_a_record_pass_is_running(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result=None,
        display_running=False,
        record_pass_running=True,
    )
    assert result == 0
    assert calls == []


def test_a_render_that_makes_the_loop_current_discards_leftovers_before_launch(
    monkeypatch,
):
    observed_calls = _install_orchestration_stubs(
        monkeypatch,
        fresh=False,
        render_result="loop.segments.json",
        display_running=False,
    )
    freshness_answers = iter([False, True])
    monkeypatch.setattr(
        ensure, "recorded_loop_is_fresh", lambda *ignored: next(freshness_answers)
    )
    result = ensure.ensure_screensaver(
        "index", LAPTOP_CAPTURE_TARGET, "source", "#241010", PLAYER_BINARY_PATH, 30, 30
    )
    assert result == 0
    assert observed_calls == [
        "render",
        ("discard", "source"),
        "stop",
        "wait",
        "launch",
    ]


def test_freshness_is_judged_against_the_capture_geometry(monkeypatch):
    observed_calls = _install_orchestration_stubs(
        monkeypatch, fresh=True, render_result=None, display_running=True
    )
    checked_identifiers = []
    monkeypatch.setattr(
        ensure,
        "recorded_loop_is_fresh",
        lambda loop_directory, identifier: (
            checked_identifiers.append(identifier) or True
        ),
    )
    ensure.ensure_screensaver(
        "index", LAPTOP_CAPTURE_TARGET, "source", "#241010", PLAYER_BINARY_PATH, 30, 30
    )
    assert set(checked_identifiers) == {"source capture=1660x1080"}
    assert observed_calls == [("discard", "source")]
