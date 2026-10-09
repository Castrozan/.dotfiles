import importlib.util
import json
from pathlib import Path
import sys

import pytest


SOURCE = (
    Path(__file__).resolve().parents[2] / "agent-session-codex-launcher-migration.py"
)
SPEC = importlib.util.spec_from_file_location(
    "codex_launcher_migration_transport", SOURCE
)
TRANSPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSPORT)


def test_fixture_command_records_status_and_bounded_output(tmp_path):
    commands = TRANSPORT.MigrationCommands(tmp_path)
    assert (
        commands.run("fixture", [sys.executable, "-c", "print('fixture output')"])
        == "fixture output\n"
    )
    record = json.loads((tmp_path / "command-0000-finished.json").read_text())
    assert record["status"] == 0 and record["stdout_bytes"] == 15
    assert (tmp_path / "command-0000-started.json").exists()


def test_fixture_output_overflow_stops_only_created_cli(tmp_path):
    commands = TRANSPORT.MigrationCommands(tmp_path)
    with pytest.raises(ValueError, match="bounded stdout"):
        commands.run(
            "fixture overflow",
            [sys.executable, "-c", "import os; os.write(1, b'x' * 300000)"],
        )
    record = json.loads((tmp_path / "command-0000-finished.json").read_text())
    assert record["status"] == "failed" and record["stdout_bytes"] <= 262144


def test_fixture_timeout_is_recorded_without_retry(tmp_path):
    commands = TRANSPORT.MigrationCommands(tmp_path)
    with pytest.raises(TimeoutError):
        commands.run(
            "fixture timeout",
            [sys.executable, "-c", "import time; time.sleep(2)"],
            0.05,
        )
    records = list(tmp_path.glob("command-*-finished.json"))
    assert len(records) == 1
    assert json.loads(records[0].read_text())["status"] == "failed"


@pytest.mark.parametrize(
    "records",
    [
        {},
        {"one": {"paneId": "fixture", "name": "one", "harness": "claude"}},
        {
            "one": {"paneId": "fixture", "name": "one", "harness": "codex"},
            "two": {"paneId": "fixture", "name": "two", "harness": "codex"},
        },
    ],
)
def test_continuation_refuses_missing_wrong_or_ambiguous_peer(
    tmp_path, monkeypatch, records
):
    commands = TRANSPORT.MigrationCommands(tmp_path)
    calls = []

    def run(label, arguments, timeout=5.0):
        calls.append(arguments)
        return json.dumps(records)

    monkeypatch.setattr(commands, "run", run)
    with pytest.raises(ValueError, match="unique Codex"):
        commands.send("fixture", "continuation")
    assert calls == [["a2a", "list", "--json"]]


def test_continuation_resolves_current_name_and_sends_once(tmp_path, monkeypatch):
    commands = TRANSPORT.MigrationCommands(tmp_path)
    calls = []

    def run(label, arguments, timeout=5.0):
        calls.append(arguments)
        if arguments == ["a2a", "list", "--json"]:
            return json.dumps(
                {
                    "changed-name": {
                        "paneId": "fixture",
                        "name": "changed-name",
                        "harness": "codex",
                    }
                }
            )
        return "acknowledged-task\n"

    monkeypatch.setattr(commands, "run", run)
    assert commands.send("fixture", "continuation") == {
        "target": "changed-name",
        "task_identifier": "acknowledged-task",
    }
    assert calls[-1] == ["a2a", "send", "changed-name", "continuation"]
    assert len(calls) == 2
