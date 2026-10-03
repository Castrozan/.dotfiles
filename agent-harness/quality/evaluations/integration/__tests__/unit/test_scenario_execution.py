import importlib.util
import json
from pathlib import Path

import integration_scenario_execution
import pytest
from integration_assertions_output import run_assertions
from integration_models import AssertionResult, SessionTrace, ToolCallEvent
from integration_session import parse_stream_json_output


def _load_runner():
    runner_path = Path(__file__).resolve().parents[2] / "run-integration-tests.py"
    spec = importlib.util.spec_from_file_location("run_integration_tests", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def _load_ab_runner():
    runner_path = (
        Path(__file__).resolve().parents[2] / "run-instruction-loading-ab-test.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_instruction_loading_ab_test", runner_path
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_missing_prompt_returns_error_and_cleans_workspace(monkeypatch, tmp_path):
    runner = _load_runner()
    removed_paths = []
    monkeypatch.setattr(runner, "load_scenario", lambda _: {"name": "scenario"})
    monkeypatch.setattr(runner.tempfile, "mkdtemp", lambda **_: str(tmp_path))
    monkeypatch.setattr(runner, "setup_scenario_workspace", lambda *_: None)
    monkeypatch.setattr(
        runner.shutil,
        "rmtree",
        lambda path, ignore_errors: removed_paths.append((path, ignore_errors)),
    )

    result = runner.run_scenario(Path("scenario.yaml"))

    assert result.passed is False
    assert result.error == "Scenario missing 'prompt' field"
    assert result.workspace_directory == tmp_path
    assert removed_paths == [(tmp_path, True)]


def test_ab_runner_filters_scenarios_and_reports_missing_names(capsys):
    runner = _load_ab_runner()
    first_scenario_name = runner.UNPROMPTED_SCENARIOS[0]["name"]

    assert runner._scenarios_to_run(None) is runner.UNPROMPTED_SCENARIOS
    assert [
        scenario["name"] for scenario in runner._scenarios_to_run(first_scenario_name)
    ] == [first_scenario_name]
    with pytest.raises(SystemExit) as exit_error:
        runner._scenarios_to_run("missing")

    assert exit_error.value.code == 1
    assert capsys.readouterr().out == "Scenario 'missing' not found\n"


def test_live_scenario_preserves_timeout_and_nonzero_failure_results(monkeypatch):
    for exit_code, expected_error in (
        (124, "Session timed out after 17s"),
        (3, "Claude session exited with code 3"),
    ):
        trace = SessionTrace(duration_seconds=4, exit_code=exit_code)
        monkeypatch.setattr(
            integration_scenario_execution, "run_claude_session", lambda **_: trace
        )
        monkeypatch.setattr(
            integration_scenario_execution,
            "run_assertions",
            lambda *_args, **_kwargs: pytest.fail("failure results skip assertions"),
        )

        result = integration_scenario_execution.run_live_scenario(
            {}, "scenario", "prompt", Path("workspace"), 17, "sonnet"
        )

        assert result.passed is False
        assert result.assertion_results == []
        assert result.error == expected_error
        assert result.duration_seconds == 4


def test_live_scenario_scores_and_checks_minimum_after_assertions(monkeypatch):
    calls = []
    trace = SessionTrace(duration_seconds=4)
    assertion = AssertionResult("output", True, "passed")
    monkeypatch.setattr(
        integration_scenario_execution,
        "run_claude_session",
        lambda **_: trace,
    )
    monkeypatch.setattr(
        integration_scenario_execution,
        "run_assertions",
        lambda *_args, **_kwargs: calls.append("assertions") or [assertion],
    )
    monkeypatch.setattr(
        integration_scenario_execution,
        "calculate_experience_score",
        lambda *_args: calls.append("score") or 68,
    )
    check_minimum = integration_scenario_execution.check_minimum_experience_score
    monkeypatch.setattr(
        integration_scenario_execution,
        "check_minimum_experience_score",
        lambda *args: calls.append("minimum") or check_minimum(*args),
    )

    result = integration_scenario_execution.run_live_scenario(
        {"minimum_experience_score": 70},
        "scenario",
        "prompt",
        Path("workspace"),
        17,
        "sonnet",
    )

    assert calls == ["assertions", "score", "minimum"]
    assert result.passed is False
    assert result.experience_score == 68
    assert [item.name for item in result.assertion_results] == [
        "output",
        "experience score is at least 70",
    ]


def test_stream_parser_collects_assistant_text_tools_and_result_in_order():
    raw_output = "\n".join(
        [
            "ignored prose",
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": "first"},
                            {"type": "tool_use", "name": "Read", "input": {}},
                            {"type": "text", "text": "second"},
                            {"type": "text", "text": "  "},
                        ]
                    },
                }
            ),
            json.dumps({"type": "result", "result": "done"}),
        ]
    )

    trace = parse_stream_json_output(raw_output)

    assert trace.assistant_messages == ["first second", "done"]
    assert [call.tool_name for call in trace.tool_calls] == ["Read"]


def test_run_assertions_preserves_category_order():
    trace = SessionTrace(
        tool_calls=[
            ToolCallEvent("Read", {}, 0),
            ToolCallEvent("Edit", {"new_string": "safe"}, 0),
            ToolCallEvent("Bash", {"command": "ls"}, 0),
        ],
        assistant_messages=["done"],
    )

    results = run_assertions(
        trace,
        {
            "tool_order": [{"tool": "Read", "before": "Edit"}],
            "tool_presence": ["Edit"],
            "tool_absence": ["Write"],
            "output_contains": ["done"],
            "output_not_contains": ["failure"],
            "output_maximum_words": 1,
            "written_code_not_contains": ["forbidden"],
            "read_to_edit_ratio": 1,
            "minimum_tool_count": [{"tool": "Bash", "count": 1}],
        },
    )

    assert [result.name for result in results] == [
        "Read before Edit",
        "uses Edit",
        "does not use Write",
        "output contains 'done'",
        "output does not contain 'failure'",
        "final output uses at most 1 words",
        "written code does not contain 'forbidden'",
        "read-to-edit ratio >= 1",
        "Bash called >= 1 times",
    ]
    assert all(result.passed for result in results)
