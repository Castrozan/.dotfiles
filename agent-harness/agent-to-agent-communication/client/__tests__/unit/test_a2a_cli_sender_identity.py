import json
import subprocess

import pytest
from a2a_cli import sender_identity
from a2a_cli.peer_transport import PeerRequestFailure
from catalog import select_servant_for_session

SENDER_DIRECTORY = {
    "sender-session": {"name": "sender-session", "paneId": "w1:p2"},
    "other-session": {"name": "other-session", "paneId": "w1:p3"},
}


@pytest.fixture(autouse=True)
def isolated_sender_environment(monkeypatch, tmp_path):
    for variable in (
        "CODEX_THREAD_ID",
        "HERDR_PANE_ID",
        "CLAWDE_AGENT_NAME",
        "CLAWDE_AGENTS_DIRECTORY",
        "OPENCLAW_GATEWAY_PORT",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.chdir(tmp_path)


def test_codex_uses_its_native_thread_identity_without_a_pane_request(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "native-codex-thread")

    def reject_request(*arguments, **options):
        pytest.fail("a native session identifier needs no pane request")

    monkeypatch.setattr(sender_identity.subprocess, "run", reject_request)

    assert (
        sender_identity.resolve_sender_name({})
        == select_servant_for_session("native-codex-thread")["name"]
    )


@pytest.mark.parametrize("harness", ["claude", "opencode", "pi", "hermes"])
def test_other_harnesses_use_the_session_reported_for_the_sending_pane(
    harness, monkeypatch
):
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")

    def read_pane(arguments, **options):
        assert arguments == ["herdr", "pane", "get", "w1:p2"]
        assert options["timeout"] == 1.0
        return subprocess.CompletedProcess(
            arguments,
            0,
            json.dumps(
                {
                    "result": {
                        "pane": {
                            "agent_session": {
                                "agent": harness,
                                "kind": "id",
                                "value": "reported-session",
                            }
                        }
                    }
                }
            ),
        )

    monkeypatch.setattr(sender_identity.subprocess, "run", read_pane)

    assert (
        sender_identity.resolve_sender_name(SENDER_DIRECTORY)
        == select_servant_for_session("reported-session")["name"]
    )


def test_a_background_agent_keeps_its_name_despite_an_inherited_thread(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "parent-thread")
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "steward")

    assert sender_identity.resolve_sender_name({}) == "steward"


@pytest.mark.parametrize("marker", ["OPENCLAW_GATEWAY_PORT", "CLAWDE_AGENT_NAME"])
def test_agents_without_a_servant_use_their_own_directory_name(marker, monkeypatch):
    monkeypatch.setenv(marker, "1234" if marker == "OPENCLAW_GATEWAY_PORT" else "")
    monkeypatch.setenv("CODEX_THREAD_ID", "parent-thread")
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")

    assert sender_identity.resolve_sender_name(SENDER_DIRECTORY) == "sender-session"


def test_a_clawde_workspace_has_no_servant_without_an_environment_marker(
    monkeypatch, tmp_path
):
    workspace = tmp_path / "fleet" / "steward"
    workspace.mkdir(parents=True)
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(workspace.parent))
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")
    monkeypatch.setenv("CODEX_THREAD_ID", "parent-thread")
    monkeypatch.chdir(workspace)

    assert sender_identity.resolve_sender_name(SENDER_DIRECTORY) == "sender-session"


@pytest.mark.parametrize(
    "response_text",
    [
        "invalid json",
        "null",
        "[]",
        "{}",
        '{"result": {"pane": {"agent_session": null}}}',
        '{"result": {"pane": {"agent_session": {"kind": "path", "value": "file"}}}}',
        '{"result": {"pane": {"agent_session": {"kind": "id", "value": ""}}}}',
        '{"result": {"pane": {"agent_session": {"kind": "id", "value": 12}}}}',
    ],
)
def test_unusable_pane_identity_falls_back_to_the_sending_session_name(
    response_text, monkeypatch
):
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")
    monkeypatch.setattr(
        sender_identity.subprocess,
        "run",
        lambda *arguments, **options: subprocess.CompletedProcess(
            arguments, 0, response_text
        ),
    )

    assert sender_identity.resolve_sender_name(SENDER_DIRECTORY) == "sender-session"


@pytest.mark.parametrize(
    "failure", [FileNotFoundError(), subprocess.TimeoutExpired("herdr", 1)]
)
def test_pane_transport_failure_can_use_the_directory_name(failure, monkeypatch):
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p2")

    def fail(*arguments, **options):
        raise failure

    monkeypatch.setattr(sender_identity.subprocess, "run", fail)

    assert sender_identity.resolve_sender_name(SENDER_DIRECTORY) == "sender-session"


def test_an_unknown_sender_requires_an_explicit_name():
    with pytest.raises(PeerRequestFailure, match="use --sender"):
        sender_identity.signed_input_text("inspect the result", None, SENDER_DIRECTORY)


def test_remote_identity_needs_no_local_session():
    assert (
        sender_identity.signed_input_text("inspect the result", "Cú Chulainn", {})
        == "inspect the result — Cú Chulainn"
    )


@pytest.mark.parametrize("sender_name", ["", "  ", "first\nsecond", "first\rsecond"])
def test_invalid_sender_names_are_rejected(sender_name):
    with pytest.raises(PeerRequestFailure, match="single-line"):
        sender_identity.signed_input_text("inspect the result", sender_name, {})


@pytest.mark.parametrize("input_text", ["", "  "])
def test_empty_tasks_cannot_become_a_signature_only(input_text):
    with pytest.raises(PeerRequestFailure, match="task text must not be empty"):
        sender_identity.signed_input_text(input_text, "Sasaki Kojirou", {})
