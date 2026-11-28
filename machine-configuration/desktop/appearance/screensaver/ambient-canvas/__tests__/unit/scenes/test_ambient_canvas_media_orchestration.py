import ensure_ambient_canvas_screensaver as ensure
from recording.recorded_loop_capture_target import RecordedLoopCaptureTarget

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
        ensure, "restart_player_service", lambda: observed_calls.append("restart")
    )

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
        30,
        30,
    )
    return result, observed_calls


def test_fresh_loop_only_discards_render_leftovers_and_leaves_the_player_alone(
    monkeypatch,
):
    result, calls = _run_ensure(monkeypatch, fresh=True, render_result=None)
    assert result == 0
    assert calls == [("discard", "source")]


def test_stale_render_failure_without_existing_loop_exits_nonzero(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=False, render_result=None, loop_exists=False
    )
    assert result == 1
    assert calls == ["render"]


def test_stale_render_failure_preserves_the_playing_loop(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=False, render_result=None, loop_exists=True
    )
    assert result == 0
    assert calls == ["render"]


def test_stale_loop_skips_render_while_a_record_pass_is_running(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=False, render_result=None, record_pass_running=True
    )
    assert result == 0
    assert calls == []


def test_a_render_that_makes_the_loop_current_restarts_the_player_on_it(monkeypatch):
    observed_calls = _install_orchestration_stubs(
        monkeypatch, fresh=False, render_result="loop.segments.json"
    )
    freshness_answers = iter([False, True])
    monkeypatch.setattr(
        ensure, "recorded_loop_is_fresh", lambda *ignored: next(freshness_answers)
    )
    result = ensure.ensure_screensaver("index", LAPTOP_CAPTURE_TARGET, "source", 30, 30)
    assert result == 0
    assert observed_calls == ["render", ("discard", "source"), "restart"]


def test_freshness_is_judged_against_the_capture_geometry(monkeypatch):
    observed_calls = _install_orchestration_stubs(
        monkeypatch, fresh=True, render_result=None
    )
    checked_identifiers = []
    monkeypatch.setattr(
        ensure,
        "recorded_loop_is_fresh",
        lambda loop_directory, identifier: (
            checked_identifiers.append(identifier) or True
        ),
    )
    ensure.ensure_screensaver("index", LAPTOP_CAPTURE_TARGET, "source", 30, 30)
    assert set(checked_identifiers) == {"source capture=1660x1080"}
    assert observed_calls == [("discard", "source")]
