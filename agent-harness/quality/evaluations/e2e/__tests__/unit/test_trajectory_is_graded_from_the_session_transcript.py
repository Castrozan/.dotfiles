import json

import e2e_session_transcript
from e2e_assertions_skills_tools import check_bash_command_not_contains_assertion
from e2e_session_transcript import (
    claude_project_directory_for_workspace,
    tool_calls_from_session_transcript,
)
from e2e_trace import build_terminal_session_trace

SCRAPE_SHOWING_ONLY_GREP = "⏺ Grep(pattern: **/*.py)\n⏺ There are 5 Python files.\n"


def write_transcript(project_directory, tool_uses, filename="session.jsonl"):
    project_directory.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "message": {
                    "content": [{"type": "tool_use", "name": name, "input": tool_input}]
                }
            }
        )
        for name, tool_input in tool_uses
    ]
    (project_directory / filename).write_text("\n".join(lines) + "\n")


def workspace_with_transcript(tmp_path, monkeypatch, tool_uses):
    monkeypatch.setattr(
        e2e_session_transcript, "SESSION_TRANSCRIPT_ROOT", tmp_path / "projects"
    )
    workspace = tmp_path / "repo" / ".e2e-tests" / "e2e-glob-abc123"
    workspace.mkdir(parents=True)
    write_transcript(claude_project_directory_for_workspace(workspace), tool_uses)
    return workspace


def test_the_project_slug_dashes_every_non_alphanumeric_character(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        e2e_session_transcript, "SESSION_TRANSCRIPT_ROOT", tmp_path / "projects"
    )
    resolved = claude_project_directory_for_workspace(tmp_path / "a.b" / "c-d")

    assert "." not in resolved.name and "/" not in resolved.name
    assert resolved.name.endswith("a-b-c-d")


def test_a_bash_call_is_recovered_with_its_full_command(tmp_path, monkeypatch):
    workspace = workspace_with_transcript(
        tmp_path,
        monkeypatch,
        [("Bash", {"command": 'find . -name "*.py" | sort'})],
    )

    calls = tool_calls_from_session_transcript(workspace)

    assert [call.tool_name for call in calls] == ["Bash"]
    assert calls[0].tool_arguments_text == 'find . -name "*.py" | sort'


def test_a_workspace_with_no_transcript_yields_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        e2e_session_transcript, "SESSION_TRANSCRIPT_ROOT", tmp_path / "projects"
    )

    assert tool_calls_from_session_transcript(tmp_path / "never-ran") == []


def test_the_transcript_beats_a_terminal_scrape_that_missed_the_command(
    tmp_path, monkeypatch
):
    workspace = workspace_with_transcript(
        tmp_path,
        monkeypatch,
        [("Bash", {"command": 'find . -name "*.py" | sort'})],
    )

    trace = build_terminal_session_trace(
        SCRAPE_SHOWING_ONLY_GREP,
        duration_seconds=1.0,
        timed_out=False,
        workspace=workspace,
    )
    result = check_bash_command_not_contains_assertion(trace, "find ")

    assert not result.passed, (
        "the terminal showed only Grep while the session transcript records the "
        "forbidden find, and grading the screen instead of the record reports a "
        "violating run as green"
    )
    assert "find ." in result.detail


def test_the_terminal_scrape_still_grades_a_run_with_no_transcript(tmp_path):
    trace = build_terminal_session_trace(
        "⏺ Bash(git add -A)\n",
        duration_seconds=1.0,
        timed_out=False,
        workspace=tmp_path / "never-ran",
    )

    assert not check_bash_command_not_contains_assertion(trace, "git add -A").passed
