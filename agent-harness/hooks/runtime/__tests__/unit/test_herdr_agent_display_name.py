import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from herdr_socket_double import (
    RecordingHerdrSocketServer,
    explain_result_carrying,
    tab_result_labelled,
)
from hook_module_loader import import_hyphenated_hook_module

herdr_agent_display_name_handler = import_hyphenated_hook_module(
    "herdr_agent_display_name_handler"
)

HERDR_PANE_ID = "wS:p31"
HERDR_TAB_ID = "wS:t7"
WORKING_TITLE = "◐ Agent session naming and tracking strategy"
TURN_END = {"hook_event_name": "Stop", "cwd": "/Users/someone/.dotfiles"}


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
    monkeypatch.setenv("HERDR_TAB_ID", HERDR_TAB_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_socket_server.socket_path))
    monkeypatch.setattr(sys, "argv", ["stop-dispatcher.py"])
    herdr_socket_server.answer("agent.explain", explain_result_carrying(WORKING_TITLE))
    herdr_socket_server.answer("tab.get", tab_result_labelled(HERDR_TAB_ID, "4"))
    return herdr_socket_server


def test_reports_the_title_the_harness_wrote_as_the_pane_title(herdr_pane_environment):
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    reported = herdr_pane_environment.requests_for("pane.report_metadata")[0]["params"]
    assert reported["pane_id"] == HERDR_PANE_ID
    assert reported["source"] == "herdr:claude"
    assert reported["agent"] == "claude"
    assert reported["title"] == "Agent session naming and tracking strategy"


def test_names_an_unnamed_single_pane_tab_with_a_shortened_title(
    herdr_pane_environment,
):
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    renamed = herdr_pane_environment.requests_for("tab.rename")[0]["params"]
    assert renamed["tab_id"] == HERDR_TAB_ID
    assert renamed["label"] == "Agent session naming"


def test_leaves_a_tab_a_human_already_named_alone(herdr_pane_environment):
    herdr_pane_environment.answer(
        "tab.get", tab_result_labelled(HERDR_TAB_ID, "release cut")
    )
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    assert herdr_pane_environment.requests_for("tab.rename") == []


def test_leaves_a_tab_holding_other_panes_alone(herdr_pane_environment):
    herdr_pane_environment.answer(
        "tab.get", tab_result_labelled(HERDR_TAB_ID, "4", pane_count=2)
    )
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    assert herdr_pane_environment.requests_for("tab.rename") == []


def test_falls_back_to_the_working_directory_when_the_harness_wrote_no_title(
    herdr_pane_environment,
):
    herdr_pane_environment.answer("agent.explain", explain_result_carrying(""))
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    reported = herdr_pane_environment.requests_for("pane.report_metadata")[0]["params"]
    assert reported["title"] == ".dotfiles"
    assert herdr_pane_environment.requests_for("tab.rename") == []


def test_drops_the_ellipsis_herdr_truncates_a_long_title_with(herdr_pane_environment):
    herdr_pane_environment.answer(
        "agent.explain", explain_result_carrying("scaffolding | feature/CAFE-694-pr...")
    )
    herdr_agent_display_name_handler.handle(TURN_END)
    herdr_pane_environment.close()
    reported = herdr_pane_environment.requests_for("pane.report_metadata")[0]["params"]
    assert reported["title"] == "scaffolding | feature/CAFE-694-pr"


def test_reports_nothing_for_an_agent_the_clawde_supervisor_owns(
    herdr_pane_environment, monkeypatch
):
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "jenny")
    herdr_agent_display_name_handler.handle(TURN_END)
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_for_a_subagent_stop(herdr_pane_environment):
    herdr_agent_display_name_handler.handle(
        {**TURN_END, "hook_event_name": "SubagentStop"}
    )
    assert herdr_pane_environment.received_requests == []


def test_reports_nothing_outside_a_herdr_pane(monkeypatch, herdr_socket_server):
    monkeypatch.delenv("HERDR_ENV", raising=False)
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(herdr_socket_server.socket_path))
    herdr_agent_display_name_handler.handle(TURN_END)
    assert herdr_socket_server.received_requests == []


def test_survives_a_missing_herdr_socket(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_PANE_ID", HERDR_PANE_ID)
    monkeypatch.setenv("HERDR_TAB_ID", HERDR_TAB_ID)
    monkeypatch.setenv("HERDR_SOCKET_PATH", str(tmp_path / "absent.sock"))
    monkeypatch.setattr(sys, "argv", ["stop-dispatcher.py"])
    assert herdr_agent_display_name_handler.handle(TURN_END) is None
