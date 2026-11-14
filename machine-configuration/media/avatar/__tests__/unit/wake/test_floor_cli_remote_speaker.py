import tempfile
from pathlib import Path

import conversation_addressee
import floor_cli
import remote_agent
from conversation_addressee import Addressee
from floor_runner import run_floor_cli
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

HOSTS = st.sampled_from(["kira", "mika"])
PANES = st.sampled_from(["wW:pPA", "wW:pPB", "wX:pPA"])
REPEATED_SETUP_IS_IDEMPOTENT = settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)


@REPEATED_SETUP_IS_IDEMPOTENT
@given(
    holder_host=HOSTS,
    holder_pane=PANES,
    speaker_host=HOSTS,
    speaker_pane=PANES,
)
def test_only_the_holder_pane_on_its_own_host_may_speak_from_another_machine(
    monkeypatch, holder_host, holder_pane, speaker_host, speaker_pane
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    shown = []
    monkeypatch.setattr(
        floor_cli.servant_character, "show_for", lambda servant: shown.append(servant)
    )
    with tempfile.TemporaryDirectory() as directory:
        holder = Addressee(holder_pane, "Circe", 2, holder_host)
        conversation_addressee.hand_to(Path(directory), holder)
        code = run_floor_cli(
            monkeypatch, Path(directory), "--speaker", f"{speaker_host}:{speaker_pane}"
        )
        assert conversation_addressee.current(Path(directory)) == holder
    is_holder = (holder_host, holder_pane) == (speaker_host, speaker_pane)
    assert code == (0 if is_holder else 1)
    assert shown == (["Voyager"] if is_holder else [])


def test_a_remote_speaker_without_a_holder_shows_its_character_and_claims_nothing(
    shown, monkeypatch, tmp_path
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    assert run_floor_cli(monkeypatch, tmp_path, "--speaker", "kira:wW:pPZ") == 0
    assert shown == ["Voyager"]
    assert conversation_addressee.current(tmp_path) is None


def test_a_refused_remote_speaker_hears_who_holds_the_floor(
    shown, monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    conversation_addressee.hand_to(tmp_path, Addressee("wW:pPA", "Circe", 0))
    assert run_floor_cli(monkeypatch, tmp_path, "--speaker", "kira:wW:pPZ") == 1
    assert "Circe holds the avatar's floor" in capsys.readouterr().err


def test_a_remote_speaker_pane_without_a_servant_changes_nothing(
    shown, monkeypatch, tmp_path
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: None)
    assert run_floor_cli(monkeypatch, tmp_path, "--speaker", "kira:wW:pPZ") == 0
    assert shown == []


def test_an_unreadable_remote_speaker_session_fails_with_its_reason(
    shown, monkeypatch, tmp_path, capsys
):
    def unreachable(agent):
        raise OSError("ssh is missing")

    monkeypatch.setattr(remote_agent, "servant_at", unreachable)
    assert run_floor_cli(monkeypatch, tmp_path, "--speaker", "kira:wW:pPZ") == 1
    assert "ssh is missing" in capsys.readouterr().err
    assert shown == []
