import json

from a2a_cli.decisions import cli as decision_cli
from a2a_cli.peer_transport import PeerRequestFailure
from decision_test_support import file_card, run_a2a


def test_answering_records_the_decider_and_notifies_the_requesting_pane_once(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    answer = [
        "answer",
        identifier,
        "--choice",
        "drop",
        "--rationale",
        "cosmetic",
        "--by",
        "human",
        "--sender",
        "Medea",
    ]
    assert run_a2a(monkeypatch, tmp_path, *answer) == 0
    card = json.loads((tmp_path / f"{identifier}.json").read_text())
    assert card["state"] == "answered"
    assert card["answer"]["decided_by"] == "human"
    assert notifications[-1][0] == "http://daemon/agents/worker-session"
    assert notifications[-1][2].startswith(
        f"decision {identifier} answered by human: drop."
    )
    assert run_a2a(monkeypatch, tmp_path, *answer) == 1
    assert len(notifications) == 2


def test_withdrawal_closes_the_card_and_tells_the_orchestrator(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    assert (
        run_a2a(
            monkeypatch,
            tmp_path,
            "withdraw",
            identifier,
            "--reason",
            "resolved by CI",
            "--sender",
            "Angra",
        )
        == 0
    )
    assert (
        json.loads((tmp_path / f"{identifier}.json").read_text())["state"]
        == "withdrawn"
    )
    assert notifications[-1][0] == "http://daemon/agents/orchestrator-session"


def test_list_filters_by_state_and_show_renders_the_whole_card(
    monkeypatch, tmp_path, capsys, notifications
):
    _, open_identifier = file_card(monkeypatch, tmp_path, capsys)
    _, answered_identifier = file_card(monkeypatch, tmp_path, capsys)
    run_a2a(
        monkeypatch,
        tmp_path,
        "answer",
        answered_identifier,
        "--choice",
        "keep",
        "--rationale",
        "r",
        "--by",
        "orchestrator",
        "--sender",
        "Medea",
    )
    capsys.readouterr()
    run_a2a(monkeypatch, tmp_path, "list")
    rows = capsys.readouterr().out.strip().splitlines()
    assert [row.split("\t")[0] for row in rows] == [open_identifier]
    run_a2a(monkeypatch, tmp_path, "show", answered_identifier)
    rendered = capsys.readouterr().out
    assert "**drop** (recommended)" in rendered
    assert "**Unverified assumptions**" in rendered
    assert "**Answer** (orchestrator" in rendered


def test_an_answer_is_recorded_even_when_the_daemon_cannot_deliver_it(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)

    def unreachable(daemon):
        raise PeerRequestFailure("http://127.0.0.1:7000/agents is unreachable")

    monkeypatch.setattr(decision_cli, "read_agent_directory", unreachable)
    answer = [
        "answer",
        identifier,
        "--choice",
        "drop",
        "--rationale",
        "r",
        "--by",
        "human",
    ]
    assert run_a2a(monkeypatch, tmp_path, *answer) == 1
    assert (
        json.loads((tmp_path / f"{identifier}.json").read_text())["state"] == "answered"
    )
    assert "is saved at" in capsys.readouterr().err
