import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from herdr_socket_double import RecordingHerdrSocketServer
from hook_module_loader import import_hyphenated_hook_module

herdr_agent_session_report_handler = import_hyphenated_hook_module(
    "herdr_agent_session_report_handler"
)

HERDR_PANE_ID = "wS:p31"


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
    request = herdr_pane_environment.received_requests[0]
    assert request["params"]["agent_session_path"] == "/tmp/transcript.jsonl"


@pytest.mark.parametrize("surface", ["codex", "opencode"])
def test_reports_the_agent_name_the_surface_carries(
    herdr_pane_environment, monkeypatch, surface
):
    monkeypatch.setattr(
        sys, "argv", ["session-start-dispatcher.py", f"--surface={surface}"]
    )
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "SessionStart", "session_id": "abc-123"}
    )
    request = herdr_pane_environment.received_requests[0]
    assert request["params"]["agent"] == surface
    assert request["params"]["source"] == f"herdr:{surface}"


def test_reports_the_session_id_at_the_end_of_every_turn(herdr_pane_environment):
    herdr_agent_session_report_handler.handle(
        {"hook_event_name": "Stop", "session_id": "abc-123"}
    )
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
