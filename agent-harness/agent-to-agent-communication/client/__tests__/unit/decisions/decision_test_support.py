import io
import json
import sys

import pytest
from a2a_cli import __main__ as a2a_main
from a2a_cli.decisions import cli as decision_cli

AGENT_DIRECTORY = {
    "orchestrator-session": {
        "paneId": "orchestrator-pane",
        "endpoint": "http://daemon/agents/orchestrator-session",
    },
    "worker-session": {
        "paneId": "worker-pane",
        "endpoint": "http://daemon/agents/worker-session",
    },
}


def valid_card_document(**overrides):
    document = {
        "goal": "drop the codex status line patch",
        "question": "Drop the local codex patch or keep compiling from source?",
        "blocked_work": "the rebuild waits on this; nothing else is blocked",
        "options": [
            {
                "label": "drop",
                "consequence": "binary cache build, status line loses two fields",
            },
            {
                "label": "keep",
                "consequence": "every rebuild compiles codex for ~9 minutes",
            },
        ],
        "recommendation": "drop",
        "reasoning": "the two fields are cosmetic and the compile dominates rebuild time",
        "evidence": [
            "agent-harness/harnesses/codex/package.nix:12",
            "rebuild log: 9m12s",
        ],
        "unverified_assumptions": ["upstream has not merged the same fields"],
        "reversible": True,
        "blast_radius": "codex on every host",
    }
    document.update(overrides)
    return document


@pytest.fixture
def notifications(monkeypatch):
    sent = []

    def record(endpoint, sender, content):
        sent.append((endpoint, sender, content))
        return {"id": "notification"}

    monkeypatch.setattr(
        decision_cli, "read_agent_directory", lambda daemon: AGENT_DIRECTORY
    )
    monkeypatch.setattr(decision_cli, "notify_peer", record)
    monkeypatch.setenv("HERDR_PANE_ID", "worker-pane")
    return sent


def run_a2a(monkeypatch, decision_directory, *arguments, stdin_text=""):
    monkeypatch.setattr(
        sys, "argv", ["a2a", "decision", "--dir", str(decision_directory), *arguments]
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    return a2a_main.main()


def file_card(monkeypatch, decision_directory, capsys, document=None):
    exit_code = run_a2a(
        monkeypatch,
        decision_directory,
        "file",
        "--to",
        "orchestrator-session",
        "--sender",
        "Angra",
        stdin_text=json.dumps(document or valid_card_document()),
    )
    return exit_code, capsys.readouterr().out.strip()
