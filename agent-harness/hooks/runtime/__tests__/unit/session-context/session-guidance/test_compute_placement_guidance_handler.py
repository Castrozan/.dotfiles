import stat

import pytest
from hook_module_loader import import_hyphenated_hook_module

compute_placement_guidance_handler = import_hyphenated_hook_module(
    "compute_placement_guidance_handler"
)

GUIDANCE_LINE = (
    "Compute placement is kira: submit long or heavy commands as agent-api "
    "compute jobs so they run on kira."
)


@pytest.fixture
def stand_in_agent_api(tmp_path, monkeypatch):
    def install(script_body):
        executable = tmp_path / "agent-api"
        executable.write_text(f"#!/bin/sh\n{script_body}\n")
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv("PATH", str(tmp_path))

    return install


def _handle():
    return compute_placement_guidance_handler.handle(
        {"hook_event_name": "SessionStart"}
    )


def test_the_guidance_the_command_prints_reaches_the_session(stand_in_agent_api):
    stand_in_agent_api(f'[ "$*" = "directives --guidance" ] && echo "{GUIDANCE_LINE}"')

    assert _handle().additional_context == GUIDANCE_LINE


def test_a_failing_command_leaves_the_session_silent(stand_in_agent_api):
    stand_in_agent_api(f'echo "{GUIDANCE_LINE}"; exit 1')

    assert _handle() is None
