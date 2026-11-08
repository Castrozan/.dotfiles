import json

import pytest
from orchestration_test_support import file_card, run_orchestrator, valid_card_document

USER_MODEL_TEXT = """# USER

- U-001 · active · 2026-11-08 · scope: local build patches · Never keep a cosmetic local patch · source: D-20261101-aaaaaa
- U-002 · superseded by U-001 · 2026-11-01 · scope: local build patches · Always keep local patches · source: stated
"""


@pytest.fixture
def user_model(tmp_path):
    path = tmp_path / "USER.md"
    path.write_text(USER_MODEL_TEXT)
    return path


def answer(monkeypatch, directory, identifier, by, *extra):
    return run_orchestrator(
        monkeypatch,
        directory,
        "answer",
        identifier,
        "--choice",
        "drop",
        "--rationale",
        "U-001 covers cosmetic local patches",
        "--by",
        by,
        "--sender",
        "Medea",
        *extra,
    )


def stored_card(directory, identifier):
    return json.loads((directory / f"{identifier}.json").read_text())


def test_the_orchestrator_decides_only_by_citing_an_active_directive(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    cards = tmp_path / "cards"
    _, identifier = file_card(monkeypatch, cards, capsys)
    model = ["--user-model", str(user_model)]
    assert answer(monkeypatch, cards, identifier, "orchestrator", *model) == 1
    assert (
        answer(
            monkeypatch,
            cards,
            identifier,
            "orchestrator",
            *model,
            "--directive",
            "U-002",
        )
        == 1
    )
    assert (
        answer(
            monkeypatch,
            cards,
            identifier,
            "orchestrator",
            *model,
            "--directive",
            "U-001",
        )
        == 0
    )
    assert stored_card(cards, identifier)["answer"]["directive"] == "U-001"


@pytest.mark.parametrize(
    "overrides",
    [
        {"reversible": False},
        {"human_only": ["secret"]},
        {"human_only": ["ril-verdict"]},
    ],
)
def test_a_human_only_card_refuses_the_orchestrator_even_under_a_directive(
    monkeypatch, tmp_path, capsys, notifications, user_model, overrides
):
    _, identifier = file_card(
        monkeypatch, tmp_path, capsys, valid_card_document(**overrides)
    )
    cited = ["--user-model", str(user_model), "--directive", "U-001"]
    assert answer(monkeypatch, tmp_path, identifier, "orchestrator", *cited) == 1
    assert "is the human's" in capsys.readouterr().err
    assert answer(monkeypatch, tmp_path, identifier, "human") == 0


def test_an_escalated_card_is_kept_with_its_reason_and_only_the_human_closes_it(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    escalate = ["escalate", identifier, "--reason", "no-directive"]
    assert (
        run_orchestrator(monkeypatch, tmp_path, *escalate, "--missing", "no patch rule")
        == 0
    )
    assert "escalated it (no-directive): no patch rule." in capsys.readouterr().out
    cited = ["--user-model", str(user_model), "--directive", "U-001"]
    assert answer(monkeypatch, tmp_path, identifier, "orchestrator", *cited) == 1
    assert answer(monkeypatch, tmp_path, identifier, "human") == 0
    card = stored_card(tmp_path, identifier)
    assert (card["state"], card["escalation"]["reason"]) == ("answered", "no-directive")


def test_an_override_reopens_the_work_by_notifying_the_requester(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    _, identifier = file_card(monkeypatch, tmp_path, capsys)
    cited = ["--user-model", str(user_model), "--directive", "U-001"]
    answer(monkeypatch, tmp_path, identifier, "orchestrator", *cited)
    override = ["override", identifier, "--choice", "keep", "--rationale", "keep it"]
    assert run_orchestrator(monkeypatch, tmp_path, *override, "--sender", "Medea") == 0
    assert stored_card(tmp_path, identifier)["state"] == "overridden"
    assert notifications[-1][0] == "worker-pane"
    assert "overridden by the human: keep" in notifications[-1][2]


def test_the_audit_query_lists_only_recent_orchestrator_decisions(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    cards = tmp_path / "cards"
    _, recent = file_card(monkeypatch, cards, capsys)
    _, old = file_card(monkeypatch, cards, capsys)
    _, by_human = file_card(monkeypatch, cards, capsys)
    cited = ["--user-model", str(user_model), "--directive", "U-001"]
    answer(monkeypatch, cards, recent, "orchestrator", *cited)
    answer(monkeypatch, cards, old, "orchestrator", *cited)
    answer(monkeypatch, cards, by_human, "human")
    old_card = stored_card(cards, old)
    old_card["answer"]["decided_at"] = "2000-01-01T00:00:00+00:00"
    (cards / f"{old}.json").write_text(json.dumps(old_card))
    capsys.readouterr()
    audit = ["list", "--state", "answered", "--decided-by", "orchestrator"]
    run_orchestrator(monkeypatch, cards, *audit, "--since-hours", "12")
    rows = capsys.readouterr().out.splitlines()
    assert [row.split("\t")[0] for row in rows] == [recent]
