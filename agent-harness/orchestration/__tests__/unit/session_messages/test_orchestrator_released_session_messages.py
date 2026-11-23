import pytest
from orchestration_test_support import run_orchestrator
from orchestrator_cli.record_store import save_record
from orchestrator_cli.releases import released_sessions
from session_message_test_support import brief

RELEASED_PANE = "wW:p3"
LOCAL_BRIEF = brief().replace("ssh chise ", "").replace(" --reply-host kira", "")


@pytest.fixture
def released_voyager(monkeypatch):
    release = {
        "name": "wW-p3",
        "pane": RELEASED_PANE,
        "panes": [RELEASED_PANE],
        "session_identifier": None,
        "session": "Voyager",
        "orchestrator": "Medea",
        "released_at": "2026-11-17T12:00:00+00:00",
    }
    save_record(released_sessions.release_directory(), release["name"], release)
    directory = {"Voyager": RELEASED_PANE, "Mozart": "wW:p4"}
    monkeypatch.setattr(released_sessions, "peer_pane", directory.get)


def dispatch(monkeypatch, tmp_path, target):
    path = tmp_path / "brief.md"
    path.write_text(LOCAL_BRIEF)
    arguments = dict(command="dispatch", location_flag="--brief")
    return run_orchestrator(monkeypatch, path, target, **arguments)


def relay(monkeypatch, tmp_path, target):
    arguments = [target, "--fact", "the cache is warm"]
    return run_orchestrator(
        monkeypatch,
        tmp_path / "reports",
        *arguments,
        command="relay",
        location_flag="--heartbeats-dir",
    )


@pytest.mark.parametrize("target", [RELEASED_PANE, "Voyager"])
def test_a_released_session_gets_no_relay_and_no_brief(
    monkeypatch, tmp_path, capsys, notifications, released_voyager, target
):
    assert relay(monkeypatch, tmp_path, target) == 1
    assert dispatch(monkeypatch, tmp_path, target) == 1
    assert notifications == []
    refusals = capsys.readouterr().err
    assert refusals.count("Medea released Voyager to Lucas") == 2
    assert refusals.count(f"orchestrator handover {RELEASED_PANE} --take-back") == 2


def test_other_sessions_are_still_reached_while_a_release_stands(
    monkeypatch, tmp_path, notifications, released_voyager
):
    assert relay(monkeypatch, tmp_path, "Mozart") == 0
    assert dispatch(monkeypatch, tmp_path, "Mozart") == 0
    assert [target for target, _, _ in notifications] == ["Mozart", "Mozart"]
