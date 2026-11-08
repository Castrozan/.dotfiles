import json

from orchestrator_cli import peer_messenger
from orchestration_test_support import file_card, run_orchestrator


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
    assert run_orchestrator(monkeypatch, tmp_path, *answer) == 0
    card = json.loads((tmp_path / f"{identifier}.json").read_text())
    assert card["state"] == "answered"
    assert card["answer"]["decided_by"] == "human"
    assert notifications[-1][0] == "worker-pane"
    assert notifications[-1][2].startswith(
        f"decision {identifier} answered by human: drop."
    )
    assert run_orchestrator(monkeypatch, tmp_path, *answer) == 1
    assert len(notifications) == 2


def test_withdrawal_closes_the_card_and_tells_the_orchestrator(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    assert (
        run_orchestrator(
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
    assert notifications[-1][0] == "orchestrator-session"


def test_list_filters_by_state_and_show_renders_the_whole_card(
    monkeypatch, tmp_path, capsys, notifications
):
    _, open_identifier = file_card(monkeypatch, tmp_path, capsys)
    _, answered_identifier = file_card(monkeypatch, tmp_path, capsys)
    run_orchestrator(
        monkeypatch,
        tmp_path,
        "answer",
        answered_identifier,
        "--choice",
        "keep",
        "--rationale",
        "r",
        "--by",
        "human",
        "--sender",
        "Medea",
    )
    capsys.readouterr()
    run_orchestrator(monkeypatch, tmp_path, "list")
    rows = capsys.readouterr().out.strip().splitlines()
    assert [row.split("\t")[0] for row in rows] == [open_identifier]
    run_orchestrator(monkeypatch, tmp_path, "show", answered_identifier)
    rendered = capsys.readouterr().out
    paragraph, *labels = rendered.strip().split("\n\n")[1:]
    paragraph = " ".join(paragraph.split())
    assert "It recommends drop because" in paragraph
    assert "Not verified: upstream has not merged the same fields." in paragraph
    assert "Decided by human: keep" in paragraph
    assert labels == [
        "**What is this session about?:** drop the codex status line patch.",
        "**Done:** found the patch and measured the compile cost.",
        "**Next:** the rebuild waits on this; nothing else is blocked.",
    ]


def test_an_answer_is_recorded_even_when_the_daemon_cannot_deliver_it(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)

    def unreachable(command, *arguments):
        raise peer_messenger.PeerMessageFailure("the a2a daemon is unreachable")

    monkeypatch.setattr(peer_messenger, "run_a2a", unreachable)
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
    assert run_orchestrator(monkeypatch, tmp_path, *answer) == 1
    assert (
        json.loads((tmp_path / f"{identifier}.json").read_text())["state"] == "answered"
    )
    assert "is saved but" in capsys.readouterr().err
