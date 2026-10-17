import json
import subprocess

import pytest
from e2e.sessions import e2e_herdr


@pytest.mark.parametrize(
    ("processes", "expected"),
    [
        ([{"name": "bash", "pid": 12}], False),
        ([], False),
        ([{"name": "claude", "pid": 34}], True),
        ([{"argv0": "/nix/store/package/bin/claude", "pid": 34}], True),
        ([{"name": "bash", "argv0": None}], False),
    ],
)
def test_a_historical_agent_registration_is_not_a_live_session(
    monkeypatch, processes, expected
):
    def run_command(arguments):
        payload = (
            {"agent": {"agent": "claude"}}
            if arguments[0] == "agent"
            else {"process_info": {"foreground_processes": processes}}
        )
        return subprocess.CompletedProcess(
            arguments, 0, json.dumps({"result": payload}), ""
        )

    monkeypatch.setattr(e2e_herdr, "run_herdr_command", run_command)

    assert e2e_herdr.pane_hosts_a_live_agent("pane") is expected


def test_failed_process_lookup_is_not_a_live_agent(monkeypatch):
    def run_command(arguments):
        if arguments[0] == "agent":
            return subprocess.CompletedProcess(
                arguments, 0, json.dumps({"result": {"agent": {"agent": "claude"}}}), ""
            )
        return subprocess.CompletedProcess(arguments, 1, "", "unavailable")

    monkeypatch.setattr(e2e_herdr, "run_herdr_command", run_command)

    assert not e2e_herdr.pane_hosts_a_live_agent("pane")
