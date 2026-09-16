import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from integration.comparisons import ab_test_claude_session as sessions


def test_stream_parser_ignores_noise_and_preserves_tools_and_text():
    events = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    None,
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "a.py"},
                    },
                    {"type": "text", "text": "answer"},
                    {"type": "text", "text": " "},
                ]
            },
        },
        {"type": "assistant", "content": "invalid"},
        {"type": "result", "result": "complete"},
        {"type": "result", "result": None},
        {"type": "system"},
    ]
    trace = sessions.parse_stream_json_output(
        "noise\n\n" + "\n".join(map(json.dumps, events))
    )
    assert [(event.tool_name, event.tool_input) for event in trace.tool_calls] == [
        ("Read", {"file_path": "a.py"})
    ]
    assert trace.assistant_messages == ["answer", "complete"]


@pytest.mark.parametrize("with_system_prompt", [False, True])
def test_session_transport_preserves_exit_and_isolates_environment(
    monkeypatch, tmp_path, with_system_prompt
):
    monkeypatch.setattr(
        sessions, "resolve_subject_claude_binary", lambda: "/test/claude"
    )
    monkeypatch.setenv("CLAUDECODE", "parent")
    monkeypatch.setenv("TEST_RETAINED", "present")
    run = Mock(
        return_value=SimpleNamespace(
            stdout='{"type":"result","result":"done"}', returncode=7
        )
    )
    monkeypatch.setattr(sessions.subprocess, "run", run)
    function = (
        sessions.run_claude_session_with_system_prompt
        if with_system_prompt
        else sessions.run_claude_session_without_system_prompt
    )
    options = {"system_prompt": "policy"} if with_system_prompt else {}
    result = function(
        "prompt", tmp_path, timeout_seconds=9, model="test-model", **options
    )
    assert result.exit_code == 7 and result.assistant_messages == ["done"]
    arguments = run.call_args.args[0]
    assert arguments[:2] == ["/test/claude", "-p"] and arguments[-1] == "prompt"
    assert ("--system-prompt" in arguments) == with_system_prompt
    assert run.call_args.kwargs["timeout"] == 9
    assert "CLAUDECODE" not in run.call_args.kwargs["env"]
    assert run.call_args.kwargs["env"]["TEST_RETAINED"] == "present"
    run.side_effect = subprocess.TimeoutExpired(arguments, 9)
    timed_out = function("prompt", tmp_path, **options)
    assert timed_out.exit_code == 124 and timed_out.tool_calls == []
