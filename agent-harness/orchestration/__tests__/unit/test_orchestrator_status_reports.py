import json

import pytest
from orchestration_test_support import run_orchestrator


def report_document(**overrides):
    document = {
        "goal": "drop the codex status line patch",
        "state": "working",
        "done_check": "rebuild uses the binary cache for codex",
        "progress": "patch removed from the overlay",
        "next_step": "run rebuild",
        "verified": [
            {"claim": "overlay no longer patches codex", "evidence": "a1b2c3d"}
        ],
        "unverified": ["the binary cache already has this codex version"],
        "open_decisions": ["D-20261107-869b52"],
    }
    document.update(overrides)
    return document


def file_report(monkeypatch, directory, capsys, sender="Edmond Dantès", **overrides):
    exit_code = run_orchestrator(
        monkeypatch,
        directory,
        "file",
        "--to",
        "orchestrator-session",
        "--sender",
        sender,
        stdin_text=json.dumps(report_document(**overrides)),
        command="report",
    )
    return exit_code, capsys.readouterr().out.strip()


def test_working_updates_are_silent_and_turning_blocked_or_done_notifies_once(
    monkeypatch, tmp_path, capsys, notifications
):
    assert file_report(monkeypatch, tmp_path, capsys) == (
        0,
        "Edmond-Dantes-worker-pane",
    )
    assert notifications == []
    file_report(monkeypatch, tmp_path, capsys, state="blocked", next_step="decide D-1")
    file_report(monkeypatch, tmp_path, capsys, state="blocked", next_step="decide D-1")
    file_report(monkeypatch, tmp_path, capsys, state="done", next_step="nothing")
    assert [content for _, _, content in notifications] == [
        "Edmond Dantès is blocked: decide D-1 Read it: orchestrator report show Edmond-Dantes-worker-pane",
        "Edmond Dantès is done: nothing Read it: orchestrator report show Edmond-Dantes-worker-pane",
    ]


def test_list_keeps_one_current_row_per_peer_and_show_separates_verified_claims(
    monkeypatch, tmp_path, capsys, notifications
):
    file_report(monkeypatch, tmp_path, capsys)
    file_report(monkeypatch, tmp_path, capsys, progress="rebuilt")
    file_report(monkeypatch, tmp_path, capsys, sender="Angra")
    run_orchestrator(monkeypatch, tmp_path, "list", command="report")
    rows = capsys.readouterr().out.strip().splitlines()
    assert sorted(row.split("\t")[1] for row in rows) == ["Angra", "Edmond Dantès"]
    run_orchestrator(
        monkeypatch, tmp_path, "show", "Edmond-Dantes-worker-pane", command="report"
    )
    rendered = capsys.readouterr().out
    assert "**Progress**: rebuilt" in rendered
    assert "- overlay no longer patches codex (a1b2c3d)" in rendered
    assert "**Not verified**" in rendered


@pytest.mark.parametrize(
    "overrides",
    [
        {"state": "paused"},
        {"goal": ""},
        {"verified": [{"claim": "no evidence"}]},
        {"verified": "all of it"},
    ],
)
def test_incomplete_reports_are_refused_and_nothing_is_saved(
    monkeypatch, tmp_path, capsys, notifications, overrides
):
    assert file_report(monkeypatch, tmp_path, capsys, **overrides)[0] == 1
    assert list(tmp_path.glob("*.json")) == []


def test_two_sessions_sharing_a_servant_name_keep_separate_reports(
    monkeypatch, tmp_path, capsys, notifications
):
    file_report(monkeypatch, tmp_path, capsys, sender="Medea")
    monkeypatch.setenv("HERDR_PANE_ID", "other-pane")
    file_report(monkeypatch, tmp_path, capsys, sender="Medea")
    assert sorted(path.stem for path in tmp_path.glob("*.json")) == [
        "Medea-other-pane",
        "Medea-worker-pane",
    ]
