import json
from types import SimpleNamespace

import pytest

from agent_session import herdr_session


def test_reads_the_current_herdr_panes_agent_session_identifier(monkeypatch):
    monkeypatch.setattr(
        herdr_session.subprocess,
        "run",
        lambda *_arguments, **_keywords: SimpleNamespace(
            returncode=0,
            stdout=(
                '{"result":{"agent":{"agent_session":{"agent":"codex",'
                '"kind":"id","source":"herdr:codex","value":"session-123"}}}}'
            ),
        ),
    )

    assert (
        herdr_session.herdr_pane_agent_session_identifier("pane-123", "codex")
        == "session-123"
    )


@pytest.mark.parametrize(
    "agent_session",
    [
        {"agent": "claude", "kind": "id", "value": "session-123"},
        {"agent": "codex", "kind": "path", "value": "/tmp/session.jsonl"},
        {"agent": "codex", "kind": "id", "value": ""},
        None,
    ],
)
def test_rejects_a_herdr_agent_session_that_cannot_resume_codex(
    monkeypatch, agent_session
):
    monkeypatch.setattr(
        herdr_session.subprocess,
        "run",
        lambda *_arguments, **_keywords: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"result": {"agent": {"agent_session": agent_session}}}),
        ),
    )

    assert (
        herdr_session.herdr_pane_agent_session_identifier("pane-123", "codex") is None
    )
