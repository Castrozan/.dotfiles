import ensure_ambient_canvas_screensaver as ensure


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
    monkeypatch.setattr(ensure, "is_display_running", lambda *ignored: display_running)
    monkeypatch.setattr(
        ensure, "stop_display", lambda *ignored: observed_calls.append("stop")
    )
    monkeypatch.setattr(
        ensure,
        "wait_for_display_to_exit",
        lambda *ignored: observed_calls.append("wait"),
    )

    def fake_launch(*ignored):
        observed_calls.append("launch")
        return 0

    monkeypatch.setattr(ensure, "launch_display", fake_launch)
    return observed_calls


def _run_ensure(monkeypatch, **stub_arguments):
    observed_calls = _install_orchestration_stubs(monkeypatch, **stub_arguments)
    result = ensure.ensure_screensaver("index", "out", "source", "profile", 30, 30)
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
    assert calls == ["launch"]


def test_stale_render_success_while_running_stops_waits_then_relaunches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=False, render_result="loop.mp4", display_running=True
    )
    assert result == 0
    assert calls == ["render", "stop", "wait", "launch"]


def test_stale_render_success_while_stopped_renders_then_launches(monkeypatch):
    result, calls = _run_ensure(
        monkeypatch, fresh=False, render_result="loop.mp4", display_running=False
    )
    assert result == 0
    assert calls == ["render", "launch"]


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
    assert calls == ["render", "launch"]
