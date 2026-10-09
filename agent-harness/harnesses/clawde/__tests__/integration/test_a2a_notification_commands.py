import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_notify_inbox_and_acknowledgement_use_the_stable_pane(owned_fleet):
    script_directory = (
        Path(__file__).resolve().parents[4]
        / "agent-to-agent-communication"
        / "client"
        / "scripts"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(script_directory)

    def invoke(*arguments):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "a2a_cli",
                "--daemon",
                owned_fleet.endpoint,
                *arguments,
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    notification = invoke(
        "notify", "owned-pane", "clearance\nEnter C-c", "--sender", "Semiramis"
    )
    assert invoke("inbox", "owned-pane")["messages"] == [notification]
    assert invoke("inbox", "owned-pane")["messages"] == [notification]
    assert invoke("ack", "owned-pane", notification["id"])["acknowledged"] is True
    assert invoke("ack", "owned-pane", notification["id"])["acknowledged"] is True
    assert invoke("inbox", "owned-pane")["messages"] == []
    assert owned_fleet.target.commands == []
