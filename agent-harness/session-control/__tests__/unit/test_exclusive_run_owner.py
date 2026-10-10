import json
import subprocess
from types import SimpleNamespace

import pytest

import exclusive_run_owner


def test_a_non_agent_owner_is_not_given_an_agent_identity(monkeypatch):
    monkeypatch.setattr(exclusive_run_owner, "find_agent_session", lambda _: None)
    owner = exclusive_run_owner.resolve_run_owner({}, 123)
    assert owner["owner_type"] == "non-agent"
    assert owner["owner_user"]
    assert not owner["agent_name"]
    assert not owner["agent_harness"]
    assert not owner["agent_session"]


@pytest.mark.parametrize(
    "variable,harness",
    [
        ("CODEX_THREAD_ID", "codex"),
        ("CLAUDE_CODE_SESSION_ID", "claude"),
        ("OPENCODE_SESSION_ID", "opencode"),
    ],
)
def test_an_interactive_owner_uses_the_existing_servant_command(
    monkeypatch, variable, harness
):
    def select_servant(arguments, **options):
        assert arguments == ["servant-name", "fixture-session"]
        assert options["timeout"] == 1
        return SimpleNamespace(returncode=0, stdout="fixture-servant\n")

    monkeypatch.setattr(subprocess, "run", select_servant)
    owner = exclusive_run_owner.resolve_run_owner({variable: "fixture-session"}, 123)
    assert owner["owner_type"] == "agent"
    assert owner["agent_name"] == "fixture-servant"
    assert owner["agent_harness"] == harness
    assert owner["agent_session"] == "fixture-session"


def test_process_ancestry_identifies_an_agent_without_session_environment(monkeypatch):
    monkeypatch.setattr(
        exclusive_run_owner,
        "find_agent_session",
        lambda _: (456, "claude", "claude --resume fixture-session"),
    )
    monkeypatch.setattr(
        exclusive_run_owner, "servant_name", lambda _: "fixture-servant"
    )
    owner = exclusive_run_owner.resolve_run_owner({}, 123)
    assert owner["agent_harness"] == "claude"
    assert owner["agent_session"] == "fixture-session"


@pytest.mark.parametrize(
    "variable,harness",
    [("PI_UNWRAPPED_BINARY", "pi"), ("HERMES_AGENT_BINARY", "hermes")],
)
def test_other_deployed_harnesses_are_identified_without_inventing_a_session(
    variable, harness
):
    owner = exclusive_run_owner.resolve_run_owner({variable: "/fixture/agent"}, 123)
    assert owner["owner_type"] == "agent"
    assert owner["agent_harness"] == harness
    assert not owner["agent_session"]


def test_captured_owner_survives_privilege_handoff_without_agent_environment(
    monkeypatch,
):
    captured = {
        "owner_type": "agent",
        "owner_user": "fixture-user",
        "agent_name": "fixture-agent",
        "agent_session": "fixture-session",
    }
    monkeypatch.setattr(
        exclusive_run_owner,
        "find_agent_session",
        lambda _: pytest.fail("captured identity must not be rediscovered after sudo"),
    )
    owner = exclusive_run_owner.resolve_run_owner(
        {"DOTFILES_EXCLUSIVE_RUN_OWNER": json.dumps(captured)}, 123
    )
    assert all(owner[name] == value for name, value in captured.items())


@pytest.mark.parametrize("captured", ["invalid", "[]", "{}", "x" * 4097])
def test_invalid_captured_metadata_falls_back_to_observation(monkeypatch, captured):
    monkeypatch.setattr(exclusive_run_owner, "find_agent_session", lambda _: None)
    owner = exclusive_run_owner.resolve_run_owner(
        {"DOTFILES_EXCLUSIVE_RUN_OWNER": captured}, 123
    )
    assert owner["owner_type"] == "non-agent"


def test_control_characters_cannot_add_fields_or_terminal_escapes():
    value = "fixture\nowner_type=non-agent\r\x1b[31m"
    sanitized = exclusive_run_owner.single_line(value)
    assert not any(character in sanitized for character in "\n\r\x1b")
    assert len(exclusive_run_owner.single_line("x" * 1000)) == 256


def test_missing_process_information_is_reported_as_unknown(monkeypatch):
    def unavailable(_):
        raise FileNotFoundError("ps is unavailable")

    monkeypatch.setattr(exclusive_run_owner, "find_agent_session", unavailable)
    assert exclusive_run_owner.resolve_run_owner({}, 123)["owner_type"] == "unknown"


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError("unavailable"), subprocess.TimeoutExpired("servant-name", 1)],
)
def test_unavailable_name_lookup_preserves_the_identifiable_agent_session(
    monkeypatch, failure
):
    def unavailable(*arguments, **options):
        raise failure

    monkeypatch.setattr(subprocess, "run", unavailable)
    owner = exclusive_run_owner.resolve_run_owner(
        {"CODEX_THREAD_ID": "fixture-session"}, 123
    )
    assert owner["owner_type"] == "agent"
    assert owner["agent_session"] == "fixture-session"
    assert not owner["agent_name"]
