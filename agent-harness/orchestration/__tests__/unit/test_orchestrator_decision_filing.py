import json

import pytest
from orchestrator_cli import peer_messenger
from orchestration_test_support import file_card, run_orchestrator, valid_card_document


def test_filing_saves_an_open_card_and_notifies_the_orchestrator_with_how_to_read_it(
    monkeypatch, tmp_path, capsys, notifications
):
    exit_code, identifier = file_card(monkeypatch, tmp_path, capsys)
    card = json.loads((tmp_path / f"{identifier}.json").read_text())
    assert exit_code == 0
    assert card["state"] == "open"
    assert card["requester"] == "Angra"
    assert card["requester_pane"] == "worker-pane"
    assert card["orchestrator"] == "orchestrator-session"
    assert notifications == [
        (
            "orchestrator-session",
            "Angra",
            f"decision {identifier} for you from Angra: {card['question']} "
            f"Read it: orchestrator decision show {identifier}",
        )
    ]


@pytest.mark.parametrize(
    "overrides",
    [
        {"recommendation": "something else"},
        {"options": [{"label": "only", "consequence": "one choice is no choice"}]},
        {
            "options": [
                {"label": "same", "consequence": "a"},
                {"label": "same", "consequence": "b"},
            ]
        },
        {"evidence": []},
        {"evidence": ["  "]},
        {"reversible": "yes"},
        {"question": ""},
        {"progress": ""},
        {"unverified_assumptions": "not a list"},
    ],
)
def test_incomplete_cards_are_refused_and_nothing_is_saved_or_sent(
    monkeypatch, tmp_path, capsys, notifications, overrides
):
    exit_code, _ = file_card(
        monkeypatch, tmp_path, capsys, valid_card_document(**overrides)
    )
    assert exit_code == 1
    assert list(tmp_path.glob("D-*.json")) == []
    assert notifications == []


def test_a_failed_notification_keeps_the_card_and_reports_where_it_is(
    monkeypatch, tmp_path, capsys, notifications
):
    def refuse(target, sender, text):
        raise peer_messenger.PeerMessageFailure("peer refused the notification")

    monkeypatch.setattr(peer_messenger, "notify_peer", refuse)
    exit_code, identifier = file_card(monkeypatch, tmp_path, capsys)
    assert exit_code == 1
    assert (tmp_path / f"{identifier}.json").is_file()


def test_an_identifier_cannot_reach_outside_the_decision_directory(
    monkeypatch, tmp_path, capsys
):
    assert run_orchestrator(monkeypatch, tmp_path, "show", "../secrets") == 1
