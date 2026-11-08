import json
import subprocess

import pytest
from orchestration_test_support import file_card, run_orchestrator

USER_MODEL_TEXT = (
    "- U-001 · active · 2026-11-08 · scope: patches · "
    "Never keep a cosmetic patch · source: stated\n"
)


@pytest.fixture
def user_model(tmp_path):
    path = tmp_path / "USER.md"
    path.write_text(USER_MODEL_TEXT)
    return path


def git(repository, *arguments):
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return completed.stdout.strip()


ISOLATED_COMMIT = [
    "-c",
    "user.name=t",
    "-c",
    "user.email=t@t",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "commit.gpgsign=false",
]


def commit_file(repository, name, content):
    (repository / name).write_text(content)
    git(repository, "add", name)
    git(repository, *ISOLATED_COMMIT, "commit", "-qm", name)
    return git(repository, "rev-parse", "HEAD")


def learn(monkeypatch, cards, *arguments):
    return run_orchestrator(monkeypatch, cards, *arguments, command="learn")


def decided_by_orchestrator(monkeypatch, cards, capsys, user_model):
    _, identifier = file_card(monkeypatch, cards, capsys)
    run_orchestrator(
        monkeypatch,
        cards,
        "answer",
        identifier,
        "--choice",
        "drop",
        "--rationale",
        "U-001",
        "--by",
        "orchestrator",
        "--directive",
        "U-001",
        "--user-model",
        str(user_model),
        "--sender",
        "Medea",
    )
    return identifier


def pending(monkeypatch, cards, capsys):
    capsys.readouterr()
    learn(monkeypatch, cards, "pending")
    return [line.split("\t")[:2] for line in capsys.readouterr().out.splitlines()]


def test_a_later_unlinked_change_to_decided_work_becomes_a_deviation_to_learn(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    cards, repository = tmp_path / "cards", tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-q")
    decided_commit = commit_file(repository, "overlay.nix", "patch removed\n")
    identifier = decided_by_orchestrator(monkeypatch, cards, capsys, user_model)
    link = ["link", identifier, "--repository", str(repository), decided_commit]
    assert run_orchestrator(monkeypatch, cards, *link) == 0
    commit_file(repository, "unrelated.nix", "untouched\n")
    learn(monkeypatch, cards, "scan")
    assert pending(monkeypatch, cards, capsys) == []
    human_commit = commit_file(repository, "overlay.nix", "patch restored\n")
    learn(monkeypatch, cards, "scan")
    learn(monkeypatch, cards, "scan")
    card = json.loads((cards / f"{identifier}.json").read_text())
    assert [deviation["commit"] for deviation in card["deviations"]] == [human_commit]
    assert pending(monkeypatch, cards, capsys) == [[identifier, "deviation"]]


def test_overrides_and_human_answers_to_escalations_stay_pending_until_resolved(
    monkeypatch, tmp_path, capsys, notifications, user_model
):
    overridden = decided_by_orchestrator(monkeypatch, tmp_path, capsys, user_model)
    run_orchestrator(
        monkeypatch,
        tmp_path,
        "override",
        overridden,
        "--choice",
        "keep",
        "--rationale",
        "keep it",
        "--sender",
        "Medea",
    )
    _, escalated = file_card(monkeypatch, tmp_path, capsys)
    run_orchestrator(
        monkeypatch,
        tmp_path,
        "escalate",
        escalated,
        "--reason",
        "no-directive",
        "--missing",
        "nothing on patches that matter",
    )
    run_orchestrator(
        monkeypatch,
        tmp_path,
        "answer",
        escalated,
        "--choice",
        "drop",
        "--rationale",
        "cosmetic",
        "--by",
        "human",
        "--sender",
        "Medea",
    )
    assert sorted(pending(monkeypatch, tmp_path, capsys)) == sorted(
        [[overridden, "override"], [escalated, "escalation"]]
    )
    assert (
        learn(
            monkeypatch,
            tmp_path,
            "resolve",
            overridden,
            "--outcome",
            "no-change",
            "--directive",
            "U-002",
            "--reason",
            "x",
        )
        == 1
    )
    resolve_superseded = [
        "resolve",
        overridden,
        "--outcome",
        "superseded",
        "--directive",
        "U-002",
        "--reason",
        "Lucas keeps patches that change behavior",
        "--user-model",
        str(user_model),
    ]
    assert learn(monkeypatch, tmp_path, *resolve_superseded) == 1
    user_model.write_text(
        USER_MODEL_TEXT
        + "- U-002 · active · 2026-11-08 · scope: patches · "
        + f"Never drop a patch that changes behavior · source: {overridden}\n"
    )
    assert learn(monkeypatch, tmp_path, *resolve_superseded) == 0
    assert pending(monkeypatch, tmp_path, capsys) == [[escalated, "escalation"]]
    capsys.readouterr()
    learn(monkeypatch, tmp_path, "stats")
    statistics = json.loads(capsys.readouterr().out)
    assert statistics["escalated"] == {"no-directive": 1}
    assert (statistics["overridden"], statistics["pending_learning"]) == (1, 1)
