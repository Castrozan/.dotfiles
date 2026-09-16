import json
import os
import subprocess
import sys

import pytest
from authoring_router_test_support import assert_allowed, assert_blocked
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path


def dispatch(event, payload):
    dispatcher = find_hook_module_path(
        "post-tool-use-dispatcher"
        if event == "PostToolUse"
        else "pre-tool-use-dispatcher"
    )
    return subprocess.run(
        [sys.executable, str(dispatcher), "--surface=codex"],
        input=json.dumps({"hook_event_name": event, **payload}),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )


@pytest.fixture
def skill_read_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(
        "AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path / "markers")
    )
    monkeypatch.setenv("CLAUDE_CODE_WORKSPACE_STATE_FILE", os.devnull)
    for skill in ("instructions", "docs"):
        path = tmp_path / ".codex" / "skills" / skill / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"---\nname: {skill}\n---\nApply the {skill} standards.\n")
    return tmp_path


def edit_payload(skill, session="authoring-session"):
    target = "AGENTS.md" if skill == "instructions" else "README.md"
    return {
        "session_id": session,
        "tool_name": "apply_patch",
        "tool_input": (
            f"*** Begin Patch\n*** Update File: {target}\n@@\n-old\n+new\n*** End Patch"
        ),
    }


def read_payload(home, skill="instructions", session="authoring-session"):
    path = home / ".codex" / "skills" / skill / "SKILL.md"
    return {
        "session_id": session,
        "cwd": str(home),
        "tool_name": "Bash",
        "tool_input": {"command": f"cat {path}"},
        "tool_response": path.read_text(),
    }


@pytest.mark.parametrize("skill", ["instructions", "docs"])
def test_codex_skill_read_opens_only_its_session_and_skill_gate(
    skill_read_environment, skill
):
    assert_blocked(dispatch("PreToolUse", edit_payload(skill)))
    result = dispatch("PostToolUse", read_payload(skill_read_environment, skill))
    assert result.returncode == 0
    assert result.stdout == ""
    assert_allowed(dispatch("PreToolUse", edit_payload(skill)))
    assert_blocked(dispatch("PreToolUse", edit_payload(skill, "another-session")))
    other_skill = "docs" if skill == "instructions" else "instructions"
    assert_blocked(dispatch("PreToolUse", edit_payload(other_skill)))


@pytest.mark.parametrize(
    "command_template,response",
    [
        ("echo {path}", "complete"),
        ("cat {path} > /dev/null", "complete"),
        ("head -n 2 {path}", "---\nname: instructions\n"),
        ("false && cat {path}", "complete"),
        ("cat {path}", "cat: permission denied"),
        ("cat {path}", "---\nname: instructions\n... truncated ..."),
        ("cat {path}", {}),
        ("cat {path}", None),
    ],
)
def test_codex_unproven_skill_read_keeps_gate_closed(
    skill_read_environment, command_template, response
):
    payload = read_payload(skill_read_environment)
    path = skill_read_environment / ".codex/skills/instructions/SKILL.md"
    payload["tool_input"]["command"] = command_template.format(path=path)
    if response != "complete":
        payload["tool_response"] = response
    dispatch("PostToolUse", payload)
    assert_blocked(dispatch("PreToolUse", edit_payload("instructions")))


def test_codex_reads_deployed_symlink_targets_with_quoted_paths(skill_read_environment):
    path = skill_read_environment / ".codex/skills/instructions/SKILL.md"
    payload = read_payload(skill_read_environment)
    source = skill_read_environment / "nix store source"
    source.mkdir()
    path.rename(source / "SKILL.md")
    path.parent.rmdir()
    path.parent.symlink_to(source, target_is_directory=True)
    payload["tool_input"]["command"] = f'cat "{source}/SKILL.md"'
    dispatch("PostToolUse", payload)
    assert_allowed(dispatch("PreToolUse", edit_payload("instructions")))


def test_codex_reads_both_authoring_skills_in_one_command(skill_read_environment):
    payload = read_payload(skill_read_environment)
    docs = read_payload(skill_read_environment, "docs")
    payload["tool_input"]["command"] = (
        "cat -- ~/.codex/skills/instructions/SKILL.md .codex/skills/docs/SKILL.md"
    )
    payload["tool_response"] += docs["tool_response"]
    dispatch("PostToolUse", payload)
    for skill in ("instructions", "docs"):
        assert_allowed(dispatch("PreToolUse", edit_payload(skill)))


def test_codex_rejects_an_unrelated_copy_of_the_skill(skill_read_environment):
    payload = read_payload(skill_read_environment)
    copy = skill_read_environment / "untrusted/skills/instructions/SKILL.md"
    copy.parent.mkdir(parents=True)
    copy.write_text(payload["tool_response"])
    payload["tool_input"]["command"] = f"cat {copy}"
    dispatch("PostToolUse", payload)
    assert_blocked(dispatch("PreToolUse", edit_payload("instructions")))


@pytest.mark.parametrize("session", [None, "", " ", 42])
def test_codex_does_not_record_reads_without_a_session(skill_read_environment, session):
    payload = read_payload(skill_read_environment, session=session)
    dispatch("PostToolUse", payload)
    assert not (skill_read_environment / "markers").exists()


def test_codex_denial_explains_the_supported_load_command(skill_read_environment):
    for skill in ("instructions", "docs"):
        result = dispatch("PreToolUse", edit_payload(skill))
        assert_blocked(result)
        assert f"cat ~/.codex/skills/{skill}/SKILL.md" in result.stdout
