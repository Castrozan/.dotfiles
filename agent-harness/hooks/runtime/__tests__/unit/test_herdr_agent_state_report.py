import json
import shutil
import socket
import sys
import tempfile
import threading
from pathlib import Path

import pytest
from hook_module_loader import (
    HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    import_hyphenated_hook_module,
)

herdr_agent_state_report_handler = import_hyphenated_hook_module(
    "herdr_agent_state_report_handler"
)

HERDR_PANE_ID = "wS:p31"


class RecordingHerdrSocketServer:
    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.received_requests = []
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(socket_path))
        self.listener.listen(1)
        self.accepting_thread = threading.Thread(
            target=self.accept_one_request, daemon=True
        )
        self.accepting_thread.start()

    def accept_one_request(self):
        try:
            connection, _ = self.listener.accept()
        except OSError:
            return
        with connection:
            received_bytes = connection.recv(65536).decode()
            if received_bytes.strip():
                self.received_requests.append(json.loads(received_bytes))
            try:
                connection.sendall(b"{}\n")
            except OSError:
                pass

    def close(self):
        self.accepting_thread.join(timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS)
        self.listener.close()


@pytest.fixture
def herdr_socket_server():
    short_temporary_directory = Path(tempfile.mkdtemp())
    server = RecordingHerdrSocketServer(short_temporary_directory / "h.sock")
    yield server
    server.close()
    shutil.rmtree(short_temporary_directory, ignore_errors=True)


@pytest.fixture
def herdr_pane_environment(monkeypatch, herdr_socket_server):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_socket_server.socket_path))
    monkeypatch.setattr(sys, "argv", ["stop-dispatcher.py"])
    return herdr_socket_server


def sent_parameters(herdr_pane_environment):
    herdr_pane_environment.close()
    request = herdr_pane_environment.received_requests[0]
    assert request["method"] == "pane.report_agent"
    return request["params"]


def test_a_submitted_prompt_reports_the_agent_as_working(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "UserPromptSubmit", "session_id": "abc-123"}
    )
    parameters = sent_parameters(herdr_pane_environment)
    assert parameters["state"] == "working"
    assert parameters["pane_id"] == HERDR_PANE_ID
    assert parameters["agent"] == "claude"
    assert parameters["source"] == "herdr:claude"
    assert parameters["agent_session_id"] == "abc-123"


def test_the_end_of_a_turn_reports_the_agent_as_idle(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "Stop", "session_id": "abc-123"}
    )
    assert sent_parameters(herdr_pane_environment)["state"] == "idle"


def test_a_session_start_reports_the_agent_as_idle(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "SessionStart", "session_id": "abc-123"}
    )
    assert sent_parameters(herdr_pane_environment)["state"] == "idle"


def test_a_clawde_supervised_agent_still_reports_its_state(
    herdr_pane_environment, monkeypatch
):
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "steward")
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "UserPromptSubmit", "session_id": "abc-123"}
    )
    assert sent_parameters(herdr_pane_environment)["state"] == "working", (
        "the heartbeat driver gates on this state before typing into a supervised "
        "agent's pane, so a supervised agent is exactly the one that has to report"
    )


def test_reports_the_codex_agent_on_the_codex_surface(
    herdr_pane_environment, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["stop-dispatcher.py", "--surface=codex"])
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "Stop", "session_id": "abc-123"}
    )
    parameters = sent_parameters(herdr_pane_environment)
    assert parameters["agent"] == "codex"
    assert parameters["source"] == "herdr:codex"


def test_reports_a_state_even_without_a_session_id(herdr_pane_environment):
    herdr_agent_state_report_handler.handle({"hook_event_name": "Stop"})
    parameters = sent_parameters(herdr_pane_environment)
    assert parameters["state"] == "idle"
    assert "agent_session_id" not in parameters


def test_reports_nothing_for_a_subagent_stop(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "SubagentStop", "session_id": "abc-123"}
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_for_a_subagent_prompt(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "abc-123",
            "agent_id": "subagent-1",
        }
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_for_an_event_that_maps_to_no_state(herdr_pane_environment):
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "PreToolUse", "session_id": "abc-123"}
    )
    assert herdr_pane_environment.received_requests == [], (
        "PreToolUse fires on every tool call, and the working state a prompt "
        "submission latches already covers the whole turn, so reporting here would "
        "buy nothing and charge a socket round trip to the hot path"
    )


def test_reports_nothing_outside_a_herdr_pane(monkeypatch, herdr_socket_server):
    monkeypatch.delenv("HERDR_ENV", raising=False)
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_socket_server.socket_path))
    herdr_agent_state_report_handler.handle(
        {"hook_event_name": "Stop", "session_id": "abc-123"}
    )
    assert herdr_socket_server.received_requests == []


def test_survives_a_missing_herdr_socket(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "absent.sock"))
    monkeypatch.setattr(sys, "argv", ["stop-dispatcher.py"])
    assert (
        herdr_agent_state_report_handler.handle(
            {"hook_event_name": "Stop", "session_id": "abc-123"}
        )
        is None
    )
