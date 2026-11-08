import io
import json
import sys

import pytest
from orchestrator_cli import __main__ as orchestrator_main
from orchestrator_cli import peer_messenger

PANE_SENDER_NAME = "worker-session"


def valid_card_document(**overrides):
    document = {
        "goal": "drop the codex status line patch",
        "progress": "found the patch and measured the compile cost",
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

    def fake_a2a(command, *arguments):
        if command == "whoami":
            return arguments[1] if arguments else PANE_SENDER_NAME
        target, text, _, sender = arguments
        sent.append((target, sender, text))
        return ""

    monkeypatch.setattr(peer_messenger, "run_a2a", fake_a2a)
    monkeypatch.setenv("HERDR_PANE_ID", "worker-pane")
    return sent


def run_orchestrator(
    monkeypatch,
    state_location,
    *arguments,
    stdin_text="",
    command="decision",
    location_flag="--dir",
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["orchestrator", command, location_flag, str(state_location), *arguments],
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    try:
        return orchestrator_main.main()
    except SystemExit as exit_request:
        return exit_request.code


def file_card(monkeypatch, decision_directory, capsys, document=None):
    exit_code = run_orchestrator(
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
