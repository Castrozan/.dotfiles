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

herdr_agent_session_report_handler = import_hyphenated_hook_module(
    "herdr_agent_session_report_handler"
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
    monkeypatch.setattr(sys, "argv", ["session-start-dispatcher.py"])
    return herdr_socket_server


def test_reports_the_session_id_to_herdr_when_running_inside_a_pane(
    herdr_pane_environment,
):
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SessionStart", "source": "resume", "session_id": "abc-123"}
    )
    herdr_pane_environment.close()
    request = herdr_pane_environment.received_requests[0]
    assert request["method"] == "pane.report_agent_session"
    assert request["params"]["pane_id"] == HERDR_PANE_ID
    assert request["params"]["agent"] == "claude"
    assert request["params"]["source"] == "herdr:claude"
    assert request["params"]["agent_session_id"] == "abc-123"
    assert request["params"]["session_start_source"] == "resume"


def test_includes_the_transcript_path_when_the_payload_carries_one(
    herdr_pane_environment,
):
    herdr_agent_session_report_handler.handle(
        {
            "hook_event_name": "SessionStart",
            "session_id": "abc-123",
            "transcript_path": "/tmp/transcript.jsonl",
        }
    )
    herdr_pane_environment.close()
    request = herdr_pane_environment.received_requests[0]
    assert request["params"]["agent_session_path"] == "/tmp/transcript.jsonl"


def test_reports_the_codex_agent_on_the_codex_surface(
    herdr_pane_environment, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["session-start-dispatcher.py", "--surface=codex"])
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SessionStart", "session_id": "abc-123"}
    )
    herdr_pane_environment.close()
    request = herdr_pane_environment.received_requests[0]
    assert request["params"]["agent"] == "codex"
    assert request["params"]["source"] == "herdr:codex"


def test_reports_the_session_id_at_the_end_of_every_turn(herdr_pane_environment):
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "Stop", "session_id": "abc-123"}
    )
    herdr_pane_environment.close()
    request = herdr_pane_environment.received_requests[0]
    assert request["params"]["agent_session_id"] == "abc-123"


def test_reports_nothing_for_an_agent_the_clawde_supervisor_owns(
    herdr_pane_environment, monkeypatch
):
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "jenny")
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SessionStart", "session_id": "abc-123"}
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_for_a_subagent_stop(herdr_pane_environment):
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SubagentStop", "session_id": "abc-123"}
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_for_a_subagent_session(herdr_pane_environment):
    herdr_agent_session_report_handler.handle(
        {
            "hook_event_name": "SessionStart",
            "session_id": "abc-123",
            "agent_id": "subagent-1",
        }
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_without_a_session_id(herdr_pane_environment):
    herdr_agent_session_report_handler.handle({"hook_event_name": "SessionStart"})
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_outside_a_herdr_pane(monkeypatch, herdr_socket_server):
    monkeypatch.delenv("HERDR_ENV", raising=False)
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_socket_server.socket_path))
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SessionStart", "session_id": "abc-123"}
    )
    assert herdr_socket_server.received_requests == []


def test_survives_a_missing_herdr_socket(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "absent.sock"))
    monkeypatch.setattr(sys, "argv", ["session-start-dispatcher.py"])
    assert (
        herdr_agent_session_report_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "abc-123"}
        )
        is None
    )
