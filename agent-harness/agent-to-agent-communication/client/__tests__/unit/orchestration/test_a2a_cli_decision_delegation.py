import json

import pytest
from orchestration_test_support import file_card, run_a2a, valid_card_document


def answer(monkeypatch, directory, identifier, by):
    return run_a2a(
        monkeypatch,
        directory,
        "answer",
        identifier,
        "--choice",
        "drop",
        "--rationale",
        "standing order: drop cosmetic local patches",
        "--by",
        by,
        "--sender",
        "Medea",
    )


def stored_card(directory, identifier):
    return json.loads((directory / f"{identifier}.json").read_text())


def test_the_orchestrator_may_decide_a_reversible_card_nobody_reserved(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    assert answer(monkeypatch, tmp_path, identifier, "orchestrator") == 0
    assert stored_card(tmp_path, identifier)["answer"]["decided_by"] == "orchestrator"


@pytest.mark.parametrize(
    "overrides",
    [
        {"reversible": False},
        {"human_only": ["secret"]},
        {"human_only": ["ril-verdict"]},
    ],
)
def test_the_orchestrator_cannot_decide_a_human_only_card_and_the_human_still_can(
    monkeypatch, tmp_path, capsys, notifications, overrides
):
    _, identifier = file_card(
        monkeypatch, tmp_path, capsys, valid_card_document(**overrides)
    )
    assert answer(monkeypatch, tmp_path, identifier, "orchestrator") == 1
    assert "is the human's" in capsys.readouterr().err
    assert stored_card(tmp_path, identifier)["state"] == "open"
    assert answer(monkeypatch, tmp_path, identifier, "human") == 0


def test_the_card_names_the_human_as_sole_decider_when_it_is_reserved(
    monkeypatch, tmp_path, capsys, notifications
):
    _, identifier = file_card(
        monkeypatch,
        tmp_path,
        capsys,
        valid_card_document(reversible=False, human_only=["money"]),
    )
    run_a2a(monkeypatch, tmp_path, "show", identifier)
    assert (
        "**Decider**: the human only (money, irreversible)" in capsys.readouterr().out
    )


def test_an_unknown_human_only_reason_is_refused_when_filed(
    monkeypatch, tmp_path, capsys, notifications
):
    document = valid_card_document(human_only=["mood"])
    assert file_card(monkeypatch, tmp_path, capsys, document)[0] == 1


def test_the_audit_query_lists_only_recent_orchestrator_decisions(
    monkeypatch, tmp_path, capsys, notifications
):
    _, recent = file_card(monkeypatch, tmp_path, capsys)
    _, old = file_card(monkeypatch, tmp_path, capsys)
    _, by_human = file_card(monkeypatch, tmp_path, capsys)
    answer(monkeypatch, tmp_path, recent, "orchestrator")
    answer(monkeypatch, tmp_path, old, "orchestrator")
    answer(monkeypatch, tmp_path, by_human, "human")
    old_card = stored_card(tmp_path, old)
    old_card["answer"]["decided_at"] = "2000-01-01T00:00:00+00:00"
    (tmp_path / f"{old}.json").write_text(json.dumps(old_card))
    capsys.readouterr()
    audit = ["list", "--state", "answered", "--decided-by", "orchestrator"]
    run_a2a(monkeypatch, tmp_path, *audit, "--since-hours", "12")
    rows = capsys.readouterr().out.splitlines()
    assert [row.split("\t")[0] for row in rows] == [recent]
