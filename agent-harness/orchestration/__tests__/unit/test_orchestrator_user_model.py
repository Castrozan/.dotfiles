import pytest
from orchestration_test_support import run_orchestrator

HEADER = "# USER\n\nFree prose the parser ignores.\n\n"
EXISTING = (
    "- U-001 · active · 2026-11-08 · scope: merge requests · "
    "Never merge without review · source: stated\n"
)


@pytest.fixture
def user_model(tmp_path):
    path = tmp_path / "USER.md"
    path.write_text(HEADER + EXISTING)
    return path


def run_user(monkeypatch, user_model, *arguments):
    return run_orchestrator(
        monkeypatch, user_model, *arguments, command="user", location_flag="--file"
    )


def directive(kind, scope, rule, source):
    return ["--kind", kind, "--scope", scope, "--rule", rule, "--source", source]


def test_add_appends_the_next_identifier_and_keeps_the_prose(
    monkeypatch, user_model, capsys
):
    new = directive("Prefer", "status", "a table per round", "D-20261108-aaaaaa")
    assert run_user(monkeypatch, user_model, "add", *new) == 0
    assert capsys.readouterr().out.strip() == "U-002"
    text = user_model.read_text()
    assert text.startswith(HEADER + EXISTING)
    assert text.endswith(
        " · scope: status · Prefer a table per round · source: D-20261108-aaaaaa\n"
    )


def test_supersede_keeps_history_and_lists_only_the_active_directive(
    monkeypatch, user_model, capsys
):
    new = directive("Never", "merge requests", "merge before QA", "override D-1")
    assert run_user(monkeypatch, user_model, "supersede", "U-001", *new) == 0
    capsys.readouterr()
    run_user(monkeypatch, user_model, "list")
    active = capsys.readouterr().out.strip().splitlines()
    assert len(active) == 1 and active[0].startswith("- U-002 · active")
    run_user(monkeypatch, user_model, "list", "--all")
    assert "U-001 · superseded by U-002" in capsys.readouterr().out
    assert run_user(monkeypatch, user_model, "supersede", "U-001", *new) == 1


@pytest.mark.parametrize(
    "fields",
    [
        directive("Maybe", "s", "r", "x"),
        directive("Always", "a · b", "r", "x"),
        directive("Always", "s", " ", "x"),
    ],
)
def test_malformed_directives_are_refused_and_the_file_is_unchanged(
    monkeypatch, user_model, fields
):
    before = user_model.read_text()
    assert run_user(monkeypatch, user_model, "add", *fields) != 0
    assert user_model.read_text() == before
