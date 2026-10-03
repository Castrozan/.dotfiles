from pathlib import Path

from e2e.sessions import e2e_scenario_results
from e2e.sessions.e2e_models import E2eAssertionResult, TerminalSessionTrace


def test_failed_result_builds_trace_before_debug_capture_and_skips_minimum(monkeypatch):
    calls = []
    monkeypatch.setattr(
        e2e_scenario_results, "capture_full_terminal_output", lambda pane: "output"
    )
    monkeypatch.setattr(e2e_scenario_results.time, "time", lambda: 8)
    monkeypatch.setattr(
        e2e_scenario_results,
        "build_terminal_session_trace",
        lambda *args, **kwargs: calls.append("trace") or TerminalSessionTrace(),
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "save_debug_capture",
        lambda *args: calls.append("debug"),
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "run_e2e_assertions",
        lambda *args: calls.append("assertions") or [],
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "calculate_e2e_experience_score",
        lambda *args: calls.append("score") or 71,
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "check_minimum_e2e_experience_score",
        lambda *args: calls.append("minimum"),
    )

    result = e2e_scenario_results.failed_e2e_scenario_result(
        {"minimum_experience_score": 90},
        "scenario",
        "pane",
        Path("workspace"),
        5,
        "step failed",
        True,
    )

    assert calls == ["trace", "debug", "assertions", "score"]
    assert result.passed is False
    assert result.duration_seconds == 3
    assert result.error == "step failed"
    assert result.experience_score == 71


def test_successful_result_saves_debug_before_trace_and_checks_minimum(monkeypatch):
    calls = []
    monkeypatch.setattr(
        e2e_scenario_results, "capture_full_terminal_output", lambda pane: "output"
    )
    monkeypatch.setattr(e2e_scenario_results.time, "time", lambda: 8)
    monkeypatch.setattr(
        e2e_scenario_results,
        "save_debug_capture",
        lambda *args: calls.append("debug"),
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "build_terminal_session_trace",
        lambda *args, **kwargs: calls.append("trace") or TerminalSessionTrace(),
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "run_e2e_assertions",
        lambda *args: calls.append("assertions")
        or [E2eAssertionResult("existing", True, "passed")],
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "calculate_e2e_experience_score",
        lambda *args: calls.append("score") or 71,
    )
    monkeypatch.setattr(
        e2e_scenario_results,
        "check_minimum_e2e_experience_score",
        lambda *args: calls.append("minimum")
        or E2eAssertionResult("minimum", False, "found 71"),
    )

    result = e2e_scenario_results.successful_e2e_scenario_result(
        {"minimum_experience_score": 90},
        "scenario",
        "pane",
        Path("workspace"),
        5,
        True,
    )

    assert calls == ["debug", "trace", "assertions", "score", "minimum"]
    assert result.passed is False
    assert result.duration_seconds == 3
    assert [assertion.name for assertion in result.assertion_results] == [
        "existing",
        "minimum",
    ]
