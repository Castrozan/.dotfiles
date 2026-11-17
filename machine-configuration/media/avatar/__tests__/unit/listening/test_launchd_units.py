from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import launchd_units
import listener_runtime
import pytest
import user_units

LISTENER = "avatar-listener.service"
RUNNING = "gui/503/agent = {\n\tactive count = 1\n\tstate = running\n}\n"
LOADED = "gui/503/agent = {\n\tactive count = 0\n\tstate = not running\n}\n"
ENDPOINT_ONLY = "gui/503/agent = {\n\tendpoints = {\n\t\tstate = running\n\t}\n}\n"


def launchctl_printing(monkeypatch, *outputs):
    answers = [SimpleNamespace(stdout=output, returncode=0) for output in outputs]
    run = Mock(side_effect=answers)
    monkeypatch.setattr(launchd_units.subprocess, "run", run)
    return run


@pytest.mark.parametrize(
    ("printed", "active"),
    [(RUNNING, True), (LOADED, False), (ENDPOINT_ONLY, False), ("", False)],
)
def test_an_agent_is_active_only_while_launchd_reports_it_running(
    monkeypatch, printed, active
):
    launchctl_printing(monkeypatch, printed)
    assert launchd_units.unit_active(LISTENER) is active


def test_a_unit_no_agent_stands_for_is_inactive_without_asking(monkeypatch):
    run = launchctl_printing(monkeypatch)
    assert launchd_units.unit_active("avatar-live.service") is False
    assert not run.called


def test_stopping_waits_until_the_agent_has_ended(monkeypatch):
    monkeypatch.setattr(launchd_units.time, "sleep", Mock())
    run = launchctl_printing(monkeypatch, "", RUNNING, RUNNING, LOADED)
    launchd_units.stop(LISTENER)
    assert run.call_args_list[0].args[0][1:3] == ["kill", "TERM"]
    assert run.call_count == 4


def test_an_agent_that_never_ends_is_reported(monkeypatch):
    monkeypatch.setattr(launchd_units, "STOP_WAIT_SECONDS", -1)
    launchctl_printing(monkeypatch, "", RUNNING)
    with pytest.raises(TimeoutError, match=launchd_units.CONVERSATION_AGENT):
        launchd_units.stop(LISTENER)


def test_every_launchctl_call_is_bounded(monkeypatch):
    run = launchctl_printing(monkeypatch, "")
    launchd_units.start(LISTENER)
    assert run.call_args.kwargs["timeout"] == launchd_units.COMMAND_TIMEOUT_SECONDS
    assert run.call_args.kwargs["check"] is True


def test_on_a_mac_units_are_launchd_agents_and_records_live_in_the_home(monkeypatch):
    monkeypatch.setattr(user_units.sys, "platform", "darwin")
    launchctl_printing(monkeypatch, RUNNING)
    assert user_units.unit_active(LISTENER) is True
    expected = Path.home() / listener_runtime.MAC_RUNTIME_DIRECTORY
    assert listener_runtime.runtime_directory() == expected
