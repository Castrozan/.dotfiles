import json

import pytest
from orchestration_test_support import heartbeat_text, run_orchestrator
from orchestrator_cli.heartbeats.session_index import entries_of, index_directory

ORCHESTRATOR = "orchestrator-session"


def file_heartbeat(
    monkeypatch, directory, capsys, sender="Edmond Dantès", text=None, **overrides
):
    exit_code = run_orchestrator(
        monkeypatch,
        directory,
        "file",
        "--to",
        ORCHESTRATOR,
        "--sender",
        sender,
        stdin_text=text if text is not None else heartbeat_text(**overrides),
        command="heartbeat",
    )
    return exit_code, capsys.readouterr().out.strip()


def test_working_updates_are_silent_and_turning_blocked_or_done_notifies_once(
    monkeypatch, tmp_path, capsys, notifications
):
    assert file_heartbeat(monkeypatch, tmp_path, capsys) == (
        0,
        "Edmond-Dantes-worker-pane",
    )
    assert notifications == []
    blocked = dict(state="blocked", next="decide D-1", open_decisions=["D-1"])
    file_heartbeat(monkeypatch, tmp_path, capsys, **blocked)
    file_heartbeat(monkeypatch, tmp_path, capsys, **blocked)
    file_heartbeat(monkeypatch, tmp_path, capsys, state="done", next="nothing")
    assert [content for _, _, content in notifications] == [
        "Edmond Dantès is blocked: decide D-1 Read it: orchestrator heartbeat show Edmond-Dantes-worker-pane",
        "Edmond Dantès is done: nothing Read it: orchestrator heartbeat show Edmond-Dantes-worker-pane",
    ]


def test_show_renders_the_published_file_in_the_template_it_arrived_in(
    monkeypatch, tmp_path, capsys, notifications
):
    file_heartbeat(monkeypatch, tmp_path, capsys, doing="rebuilding")
    run_orchestrator(
        monkeypatch, tmp_path, "show", "Edmond-Dantes-worker-pane", command="heartbeat"
    )
    published, _, rendered = capsys.readouterr().out.strip().partition("\n\n")
    assert published.startswith("Published ") and published.endswith("Edmond Dantès")
    assert rendered == heartbeat_text(doing="rebuilding")


def test_a_first_heartbeat_registers_its_session_in_the_index_once(
    monkeypatch, tmp_path, capsys, notifications
):
    file_heartbeat(monkeypatch, tmp_path, capsys)
    file_heartbeat(monkeypatch, tmp_path, capsys, doing="still at it")
    (entry,) = entries_of(ORCHESTRATOR)
    assert entry["pane"] == "worker-pane" and entry["brief"] is None
    assert entry["heartbeat"] == str(tmp_path / "Edmond-Dantes-worker-pane.json")
    assert entry["goal"] == "drop the codex status line patch"


@pytest.mark.parametrize(
    "text",
    [
        heartbeat_text(state="paused"),
        heartbeat_text(state="blocked"),
        heartbeat_text().replace("Goal:", "Objective:"),
        heartbeat_text().replace(" (evidence: a1b2c3d)", ""),
        json.dumps({"goal": "the old JSON report"}),
    ],
)
def test_a_heartbeat_off_the_template_is_refused_and_nothing_is_saved(
    monkeypatch, tmp_path, capsys, notifications, text
):
    assert file_heartbeat(monkeypatch, tmp_path, capsys, text=text)[0] == 1
    assert list(tmp_path.glob("*.json")) == []
    assert not index_directory().exists()


def test_two_sessions_sharing_a_servant_name_keep_separate_heartbeats(
    monkeypatch, tmp_path, capsys, notifications
):
    file_heartbeat(monkeypatch, tmp_path, capsys, sender="Medea")
    monkeypatch.setenv("HERDR_PANE_ID", "other-pane")
    file_heartbeat(monkeypatch, tmp_path, capsys, sender="Medea")
    assert sorted(path.stem for path in tmp_path.glob("*.json")) == [
        "Medea-other-pane",
        "Medea-worker-pane",
    ]
    assert len(entries_of(ORCHESTRATOR)) == 2


def test_check_validates_without_publishing(monkeypatch, tmp_path, capsys):
    arguments = dict(command="heartbeat", stdin_text=heartbeat_text())
    assert run_orchestrator(monkeypatch, tmp_path, "check", **arguments) == 0
    arguments["stdin_text"] = heartbeat_text(next="x" * 51)
    assert run_orchestrator(monkeypatch, tmp_path, "check", **arguments) == 1
    assert "over its limit of 50" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
