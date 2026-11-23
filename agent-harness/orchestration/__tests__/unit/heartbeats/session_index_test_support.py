import json
from datetime import datetime, timedelta, timezone

from orchestration_test_support import heartbeat_text, run_orchestrator
from orchestrator_cli.heartbeats import status_cli
from orchestrator_cli.record_store import state_directory
from orchestrator_cli.session_messages import cli as session_message_cli

ORCHESTRATOR = "worker-session"
BRIEF = """# Brief: retire hey-bot

## Goal

Hey-bot is gone and the avatar answers its wake word.

## Context

Lucas's avatar on chise; results stay in the dotfiles repo.

## Done when

- The wake word reaches the avatar

## Constraints

- Leave the microphone settings alone.

## Workspace and worktree

chise, `~/.dotfiles/.worktrees/hey-bot`.

## Lucas's words

> kill hey-bot

## Contract

{contract}
"""
LOCAL_CONTRACT = "`orchestrator decision file --to Medea` and `orchestrator heartbeat file --to Medea`"
REMOTE_CONTRACT = (
    "`ssh chise orchestrator decision file --to Medea --reply-host kira < card.json` "
    "and `ssh chise orchestrator heartbeat file --to Medea --reply-host kira < HEARTBEAT.md`"
)


def heartbeats_directory():
    return state_directory("orchestrator-heartbeats")


def dispatch(monkeypatch, tmp_path, target, *arguments):
    path = tmp_path / "brief.md"
    contract = REMOTE_CONTRACT if arguments else LOCAL_CONTRACT
    path.write_text(BRIEF.format(contract=contract))
    monkeypatch.setattr(session_message_cli, "copy_file_to_host", lambda *_: None)
    options = dict(command="dispatch", location_flag="--brief")
    return run_orchestrator(monkeypatch, path, target, *arguments, **options)


def file_heartbeat(monkeypatch, *arguments, **overrides):
    filing = ["file", "--to", ORCHESTRATOR, *arguments]
    options = dict(command="heartbeat", stdin_text=heartbeat_text(**overrides))
    return run_orchestrator(monkeypatch, heartbeats_directory(), *filing, **options)


def age_heartbeat(name, minutes):
    path = heartbeats_directory() / f"{name}.json"
    record = json.loads(path.read_text())
    earlier = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    record["updated_at"] = earlier.isoformat(timespec="seconds")
    path.write_text(json.dumps(record))


def status_output(monkeypatch, capsys, pane_statuses):
    monkeypatch.setattr(status_cli, "pane_agent_status", pane_statuses.get)
    capsys.readouterr()
    assert (
        run_orchestrator(
            monkeypatch, "15", command="status", location_flag="--stale-minutes"
        )
        == 0
    )
    return capsys.readouterr().out


def open_row(output, name):
    return next(line for line in output.splitlines() if line.startswith(f"| {name} |"))


def close_session(monkeypatch, session):
    closing = [session, "--because", "wake word verified on chise"]
    options = dict(command="close", location_flag="--for")
    return run_orchestrator(monkeypatch, ORCHESTRATOR, *closing, **options)
