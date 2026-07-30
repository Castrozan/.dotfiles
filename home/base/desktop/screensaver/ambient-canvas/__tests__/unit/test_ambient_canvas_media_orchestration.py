import ensure_ambient_canvas_screensaver as ensure
from recorded_loop_capture_target import RecordedLoopCaptureTarget

PLAYER_BINARY_PATH = "/home/user/.local/bin/player"
LAPTOP_CAPTURE_TARGET = RecordedLoopCaptureTarget(
    loop_directory="/state/loops/1660x1080",
    scene_video_directory="/state/videos",
    screen_dimensions=(1470, 956),
    capture_pixel_dimensions=(1660, 1080),
    capture_signature="1660x1080",
)


def _install_orchestration_stubs(
    monkeypatch, *, fresh, render_result, display_running, loop_exists=True
):
    observed_calls = []
    monkeypatch.setattr(ensure, "recorded_loop_is_fresh", lambda *ignored: fresh)
    monkeypatch.setattr(ensure, "recorded_loop_exists", lambda *ignored: loop_exists)

    def fake_render(*ignored):
        observed_calls.append("render")
        return render_result

    monkeypatch.setattr(ensure, "render_recorded_loop", fake_render)
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
    return observed_calls


def _run_ensure(monkeypatch, **stub_arguments):
    observed_calls = _install_orchestration_stubs(monkeypatch, **stub_arguments)
    result = ensure.ensure_screensaver(
        "index", LAPTOP_CAPTURE_TARGET, "source", PLAYER_BINARY_PATH, 30, 30
    )
    return result, observed_calls


def test_fresh_loop_with_running_display_does_nothing(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=True
    )
    assert result == 0
    assert calls == []


def test_fresh_loop_with_stopped_display_relaunches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=False
    )
    assert result == 0
    assert calls == ["stop", "wait", "launch"]


def test_a_cached_display_swap_repoints_the_player_without_recording(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=True, render_result=None, display_running=False
    )
    assert result == 0
    assert "render" not in calls
    assert calls[-1] == "launch"


def test_stale_render_success_while_running_stops_waits_then_relaunches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result="loop.segments.json",
        display_running=True,
    )
    assert result == 0
    assert calls == ["render", "stop", "wait", "launch"]


def test_stale_render_success_while_stopped_renders_then_launches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result="loop.segments.json",
        display_running=False,
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


def test_stale_render_failure_falls_back_to_existing_loop(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch,
        fresh=False,
        render_result=None,
        display_running=False,
        loop_exists=True,
    )
    assert result == 0
    assert calls == ["render", "stop", "wait", "launch"]


def test_the_running_display_is_matched_by_the_manifest_it_was_launched_with():
    assert (
        ensure.resolve_loop_display_process_marker(
            PLAYER_BINARY_PATH, "/state/loops/1660x1080"
        )
        == "/home/user/.local/bin/player /state/loops/1660x1080/loop.segments.json"
    )


def test_two_capture_geometries_produce_two_distinct_display_markers():
    assert ensure.resolve_loop_display_process_marker(
        PLAYER_BINARY_PATH, "/state/loops/1660x1080"
    ) != ensure.resolve_loop_display_process_marker(
        PLAYER_BINARY_PATH, "/state/loops/1920x1080"
    )


def test_stopping_the_display_matches_a_process_name_the_agent_cannot_carry():
    assert ensure.resolve_display_process_name(PLAYER_BINARY_PATH) == "player"
