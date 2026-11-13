import conversation_addressee
import floor_cli
import listener_runtime
import pytest
import remote_agent
import speaking_floor
from conversation_addressee import Addressee
from remote_agent import AgentPane


def run_floor_cli(monkeypatch, tmp_path, *arguments):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    monkeypatch.setattr(floor_cli.sys, "argv", ["avatar-claim-floor", *arguments])
    try:
        floor_cli.main()
    except SystemExit as finished:
        return finished.code
    return 0


def test_an_agent_with_a_servant_is_handed_the_floor_with_its_host(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 0
    assert conversation_addressee.current(tmp_path) == Addressee(
        "wW:pPZ", "Voyager", 0, "kira"
    )


def test_an_agent_pane_without_a_servant_fails_and_leaves_the_floor(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: None)
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 1
    assert floor_cli.NO_SERVANT_MESSAGE in capsys.readouterr().err
    assert conversation_addressee.current(tmp_path) is None


def test_an_unreadable_remote_session_fails_with_its_reason(
    monkeypatch, tmp_path, capsys
):
    def unreachable(agent):
        raise OSError("ssh is missing")

    monkeypatch.setattr(remote_agent, "servant_at", unreachable)
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 1
    assert "ssh is missing" in capsys.readouterr().err


@pytest.mark.parametrize("agent", ["kira", ":wW:pPZ", "kira:"])
def test_an_agent_that_is_not_host_and_pane_is_refused(monkeypatch, tmp_path, agent):
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", agent) == 2


def test_the_shared_hand_over_names_the_servant_and_reports_whether_it_exists(
    monkeypatch, tmp_path
):
    agent = AgentPane("kira", "wW:pPZ")
    monkeypatch.setattr(remote_agent, "servant_at", lambda pane: None)
    assert speaking_floor.hand_to_remote_agent(tmp_path, agent) is False
    monkeypatch.setattr(remote_agent, "servant_at", lambda pane: "Voyager")
    assert speaking_floor.hand_to_remote_agent(tmp_path, agent) is True
    assert conversation_addressee.current(tmp_path).host == "kira"


def test_without_an_agent_a_pane_outside_herdr_claims_nothing(monkeypatch, tmp_path):
    monkeypatch.delenv(floor_cli.PANE_ENVIRONMENT_VARIABLE, raising=False)
    assert run_floor_cli(monkeypatch, tmp_path) == 0
    assert conversation_addressee.current(tmp_path) is None
