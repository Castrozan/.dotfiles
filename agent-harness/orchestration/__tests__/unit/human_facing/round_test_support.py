import json
from datetime import datetime, timezone

from orchestration_test_support import run_orchestrator

ORCHESTRATOR = "orchestrator-session"


def report_document(**overrides):
    return {
        "goal": "retire hey-bot into the avatar",
        "state": "blocked",
        "done_check": "hey-bot is gone from the repo and chise",
        "progress": "inventory filed as a card",
        "next_step": "wait for the scope decision",
        **overrides,
    }


def file_report(monkeypatch, reports, sender, document):
    return run_orchestrator(
        monkeypatch,
        reports,
        "file",
        "--to",
        ORCHESTRATOR,
        "--sender",
        sender,
        stdin_text=json.dumps(document),
        command="report",
    )


def escalate(monkeypatch, cards, identifier):
    escalation = ["escalate", identifier, "--reason", "no-directive"]
    run_orchestrator(monkeypatch, cards, *escalation, "--missing", "no scope rule")


def run_round(monkeypatch, cards, reports, capsys):
    capsys.readouterr()
    exit_code = run_orchestrator(
        monkeypatch,
        cards,
        "--for",
        ORCHESTRATOR,
        "--reports-dir",
        str(reports),
        command="round",
    )
    assert exit_code == 0
    return capsys.readouterr().out


def record_open_ask(state_home, identifier, words, owner="orchestrator"):
    ledger = state_home / "orchestrator-ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    ask = {
        "id": identifier,
        "kind": "ask",
        "words": words,
        "owner": owner,
        "orchestrator": ORCHESTRATOR,
        "state": "open",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (ledger / f"{identifier}.json").write_text(json.dumps(ask))
